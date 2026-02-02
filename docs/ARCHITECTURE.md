<!--
Copyright (C) 2026 CLEARSY (https://www.clearsy.com)
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Atelier B MCP Server - Architecture Document

## Overview

The Atelier B MCP Server is a **Model Context Protocol (MCP)** server that enables Claude AI to interact with Atelier B, a formal methods IDE for the B-Method. The server acts as a bridge between Claude and Atelier B's command-line interface (`bbatch`).

```
┌─────────────────┐     MCP/JSON-RPC     ┌─────────────────┐     subprocess     ┌─────────────────┐
│  Claude Desktop │ ◄──────────────────► │  MCP Server     │ ◄────────────────► │  bbatch.exe     │
│  (MCP Client)   │       stdio          │  (Python)       │      stdin/stdout  │  (Atelier B)    │
└─────────────────┘                      └─────────────────┘                    └─────────────────┘
                                                │
                                                │ file I/O
                                                ▼
                                         ┌─────────────────┐
                                         │  B Workspace    │
                                         │  (.mch, .imp,   │
                                         │   .po, etc.)    │
                                         └─────────────────┘
```

---

## System Components

### 1. MCP Protocol Layer

**Protocol**: JSON-RPC 2.0 over stdio

The MCP protocol defines how Claude communicates with the server:
- **Tools**: Functions that Claude can invoke (e.g., list projects, run proofs)
- **Resources**: Read-only data sources (not currently used)
- **Prompts**: Pre-defined prompt templates (not currently used)

### 2. Server Core (`server.py`)

The main server module that:
- Registers available tools with their schemas
- Handles incoming tool calls from Claude
- Routes requests to appropriate tool handlers
- Returns JSON responses to Claude

```python
# Tool registration example
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="atelierb_list_projects",
            description="List all available Atelier B projects",
            inputSchema={...}
        ),
        ...
    ]
```

### 3. bbatch Wrapper (`bbatch_wrapper.py`)

An async wrapper around the Atelier B command-line tool:
- Spawns bbatch.exe as a subprocess
- Sends commands via stdin (with required newline termination)
- Captures stdout/stderr responses
- Handles timeouts and errors

```
Command flow:
1. Build command string (e.g., "open Airlock\nls\n")
2. Start bbatch subprocess
3. Write command to stdin
4. Read output from stdout
5. Parse and return result
```

### 4. Output Parsers (`parsers.py`)

Functions that parse bbatch text output into structured data:
- `parse_project_list()`: Extract project names from workspace listing
- `parse_project_info()`: Extract project details (paths, type)
- `parse_components_list()`: Extract machine/refinement/implementation list
- `parse_global_status()`: Parse the proof status table
- `parse_status()`: Parse individual component status

### 5. Tool Modules (`tools/`)

Organized by functionality:

#### Project Tools (`project_tools.py`)
- `atelierb_list_projects`: List all projects in workspace
- `atelierb_infos_project`: Get project details
- `atelierb_list_components`: List machines, refinements, implementations
- `atelierb_open_project`: Open a project (internal use)

#### Proof Tools (`proof_tools.py`)
- `atelierb_typecheck`: Verify syntax and types
- `atelierb_b0check`: B0 compliance check (required before C generation)
- `atelierb_pogenerate`: Generate proof obligations
- `atelierb_prove`: Run automatic prover
- `atelierb_status`: Get proof status

#### File Tools (`file_tools.py`)
- `atelierb_list_files`: List B source files with filtering
- `atelierb_read_file`: Read file content
- `atelierb_list_project_structure`: Get project directory tree

### 6. Configuration (`config.py`)

Uses Pydantic Settings for configuration management:
- Loads from environment variables (prefix: `ATELIERB_`)
- Optional `.env` file support
- Path validation on startup

---

## Directory Structure

```
atelierb-mcp/
├── run_server.py              # Entry point script
├── pyproject.toml             # Project metadata and dependencies
├── requirements.txt           # Pip requirements
├── .env.example               # Example environment configuration
│
├── atelierb_mcp/              # Main package
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   ├── config.py              # Configuration management
│   ├── bbatch_wrapper.py      # bbatch subprocess wrapper
│   ├── parsers.py             # Output parsing functions
│   │
│   ├── tools/                 # Tool implementations
│   │   ├── __init__.py
│   │   ├── project_tools.py   # Project management tools
│   │   ├── proof_tools.py     # Proof-related tools
│   │   └── file_tools.py      # File access tools
│   │
│   ├── resources/             # MCP resources (future)
│   │   └── __init__.py
│   │
│   └── prompts/               # MCP prompts (future)
│       └── __init__.py
│
├── tests/                     # Unit tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parsers.py
│   └── test_bbatch_wrapper.py
│
└── docs/                      # Documentation
    ├── DEPLOYMENT_GUIDE.md
    ├── ARCHITECTURE.md
    └── bbatch_commands.md
```

---

## Data Flow

### Tool Invocation Flow

```
1. User asks Claude: "List all projects"
   │
2. Claude determines tool to use: atelierb_list_projects
   │
3. Claude sends MCP request:
   │  {"method": "tools/call", "params": {"name": "atelierb_list_projects", "arguments": {}}}
   │
4. MCP Server receives request
   │  └── server.py: call_tool()
   │
5. Tool handler executes
   │  └── project_tools.py: atelierb_list_projects()
   │
6. bbatch wrapper called
   │  └── bbatch_wrapper.py: run_bbatch_command("ls")
   │
7. bbatch.exe executes and returns output
   │  └── "Project1\nProject2\nProject3\n"
   │
8. Parser extracts data
   │  └── parsers.py: parse_project_list()
   │
9. Tool returns structured result
   │  └── {"success": true, "projects": ["Project1", "Project2", "Project3"]}
   │
10. MCP Server sends JSON response to Claude
    │
11. Claude presents result to user
```

### File Access Flow

```
1. Tool: atelierb_read_file("Airlock/src/Airlock.mch")
   │
2. Security check: Is path within workspace?
   │  └── _is_safe_path() - prevents directory traversal
   │
3. Extension check: Is file type allowed?
   │  └── Whitelist: .mch, .ref, .imp, .erf, .po, .pmi, etc.
   │
4. Read file content
   │  └── UTF-8 encoding with error handling
   │
5. Return content with metadata
   └── {"success": true, "content": "MACHINE\n    Airlock\n..."}
```

---

## Security Considerations

### Path Traversal Protection
- All file paths are validated against the workspace root
- Uses `Path.is_relative_to()` to prevent `../` attacks
- Absolute paths outside workspace are rejected

### File Type Whitelist
- Only B-method related extensions are allowed
- Source: `.mch`, `.ref`, `.imp`, `.erf`, `.pmm`, `.rmf`, `.imf`
- Metadata: `.def`, `.bxml`, `.pmi`, `.nf`, `.po`

### Subprocess Security
- bbatch is executed with controlled input
- Commands are validated before execution
- Timeout prevents hanging processes

---

## Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `atelierb_list_projects` | List all projects in workspace | None |
| `atelierb_infos_project` | Get project details | `project_name` |
| `atelierb_list_components` | List project components | `project_name` |
| `atelierb_create_project` | Create a new project | `project_name`, `project_type?` |
| `atelierb_remove_project` | Remove a project | `project_name`, `delete_files?` |
| `atelierb_add_component` | Add machine/refinement/implementation | `project_name`, `component_name`, `component_type`, `content?` |
| `atelierb_remove_component` | Remove a component | `project_name`, `component_name`, `delete_file?` |
| `atelierb_typecheck` | Run type checker | `project_name`, `component_name` |
| `atelierb_b0check` | B0 compliance check (required before C generation) | `project_name`, `component_name` |
| `atelierb_pogenerate` | Generate proof obligations | `project_name`, `component_name`, `differential?` |
| `atelierb_prove` | Run automatic prover | `project_name`, `component_name`, `force?` |
| `atelierb_status` | Get proof status | `project_name`, `component_name?` |
| `atelierb_generate_c` | Generate C code for a component | `project_name`, `component_name`, `profile?` |
| `atelierb_generate_project_c` | Generate C code for entire project | `project_name`, `toplevel_component`, `profile?`, `generate_main?` |
| `atelierb_list_files` | List B source files | `project_name?`, `extension_filter?` |
| `atelierb_read_file` | Read file content | `file_path` |
| `atelierb_write_file` | Write/update file content | `file_path`, `content`, `create_backup?` |
| `atelierb_list_project_structure` | Get directory structure | `project_name` |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| MCP SDK | `mcp` package (Anthropic) |
| Configuration | Pydantic Settings |
| Async I/O | asyncio |
| Process Management | asyncio subprocess |
| Testing | pytest, pytest-asyncio |

---

## Extension Points

### Adding New Tools

1. Create tool function in appropriate module:
   ```python
   async def atelierb_new_tool(param1: str) -> dict:
       # Implementation
       return {"success": True, "result": ...}
   ```

2. Export in `tools/__init__.py`

3. Register in `server.py`:
   - Add to imports
   - Add Tool definition in `list_tools()`
   - Add handler in `call_tool()`

### Adding New File Types

Edit `file_tools.py`:
```python
ALLOWED_EXTENSIONS = {".mch", ".ref", ..., ".new_ext"}
```

### Adding bbatch Commands

The `bbatch_wrapper.py` supports any bbatch command. New tools can use existing wrapper:
```python
result = await run_bbatch_command(f"open {project}\nnewcommand {args}")
```

---

## Limitations

1. **Single Workspace**: The server operates on one workspace at a time
2. **B Source Files Only**: Write operations restricted to B source files (.mch, .ref, .imp, etc.)
3. **Windows Only**: bbatch.exe is Windows-specific
4. **Sequential Commands**: bbatch commands are executed sequentially

---

## Future Enhancements

- [ ] Support for multiple workspaces
- [ ] Proof script editing assistance
- [ ] Interactive prover integration
- [ ] Rust code generation (b2rust)
