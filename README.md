<!--
Copyright (C) 2026 CLEARSY (https://www.clearsy.com)
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Atelier B MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that connects [Claude AI](https://claude.ai) with [Atelier B](https://www.atelierb.eu), the formal methods IDE for the B-method.

This server enables Claude to directly interact with Atelier B projects: typechecking components, generating proof obligations, running the automatic prover, generating C code, and managing project files.

> **Works with Atelier B Community Edition 24.04.2** (`ATELIER B (Community Edition) version 24.04.2`, B Compiler `version/24.08`), which is the version every tool is developed and tested against. Other 24.x releases are expected to work, since the server drives `bbatch` through its documented command names, but they are not tested. Commands available only in the Professional edition, `vr` (`verify_rule`) among them, are deliberately not exposed; see [docs/coverage.md](docs/coverage.md).
>
> Also requires **Python 3.11+** and **mcp 2.0+**.

## History

Most recent first.

| Date | Change |
|------|--------|
| 2026-08-19 | **Phase 1 closed: fifteen bbatch commands added**, coverage 25 % to 54 %. Project check, archive and restore, make-all and remake, Rust generation, plus: what is left to prove (`us` / `ug`), component metadata (`ic`), prover timeout (`to`), unprove (`u`), the external SMT provers (`xtp`, `xtr`, `xce`) and the mechanism listings (`spm` / `sppm`) |
| 2026-08-19 | Projects created by the server now **appear in the workspace you browse**. Atelier B can hold several workspaces, each being a directory of `<project>.desc` descriptors; `crp` registers a new project in the default workspace only, so the server also writes the descriptor into the one `ATELIERB_WORKSPACE` points at |
| 2026-08-13 | **Ported to the mcp 2.0 protocol**, upper version bound lifted |
| 2026-08-06 | PMI proof files read through the sibling PO file, so proof state is attributed to the right proof obligation |
| 2026-08-06 | B sources moved to `src/`, out of the translation directory |

## Architecture

```
Claude Desktop (MCP Client)
    |  MCP Protocol (stdio, JSON-RPC 2.0)
    v
MCP Server (Python)
    |  subprocess (stdin/stdout)
    v
bbatch.exe (Atelier B CLI)
    |  filesystem
    v
B Projects (bdp/ + lang/ + src/ directories)
```

The server wraps Atelier B's `bbatch` command-line interface, translating MCP tool calls into bbatch commands and parsing the output back into structured responses. Files are returned exactly as they are on disk; when a PMI file is read, its per-PO entries are paired with the labels of the sibling PO file so they can be attributed to the right proof obligation (see [docs/PMI_PMM_ORDERING.md](docs/PMI_PMM_ORDERING.md)).

## Available Tools

| Category | Tools |
|----------|-------|
| **Project Management** | `atelierb_list_projects`, `atelierb_infos_project`, `atelierb_list_components`, `atelierb_create_project`, `atelierb_remove_project`, `atelierb_add_component`, `atelierb_remove_component` |
| **Verification** | `atelierb_typecheck`, `atelierb_b0check`, `atelierb_pogenerate`, `atelierb_prove`, `atelierb_status`, `atelierb_unproved_status`, `atelierb_infos_component`, `atelierb_proof_timeout`, `atelierb_unprove` |
| **External provers** (NG projects) | `atelierb_list_proof_mechanisms`, `atelierb_extprove`, `atelierb_extreplay`, `atelierb_counter_example` |
| **Code Generation** | `atelierb_generate_c`, `atelierb_generate_project_c`, `atelierb_generate_rust` |
| **Project Operations** | `atelierb_project_check`, `atelierb_make_all`, `atelierb_remake`, `atelierb_archive`, `atelierb_restore` |
| **Diagnostics** | `atelierb_version`, `atelierb_metrics` |
| **File Operations** | `atelierb_list_files`, `atelierb_read_file`, `atelierb_write_file`, `atelierb_list_project_structure` |

## Prerequisites

- **Python 3.11+**
- **Atelier B Community Edition 24.04.2** with `bbatch.exe` (the tested version; see the note at the top)
- **Claude Desktop** (or any MCP-compatible client)

## Installation

```bash
# Clone the repository
git clone https://github.com/CLEARSY/atelierb-mcp.git
cd atelierb-mcp
```

All remaining commands are run from this **repository root** (the directory that
contains `pyproject.toml`), not from the inner `atelierb_mcp/` package directory.

### Recommended: install into a virtual environment

On recent Linux distributions (and macOS with Homebrew Python), installing into
the system interpreter fails with `error: externally-managed-environment`
([PEP 668](https://peps.python.org/pep-0668/)). Use a virtual environment:

```bash
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows (PowerShell / cmd)

# Install dependencies (run from the repository root)
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

Re-activate the environment (`source .venv/bin/activate`) in any new shell before
running the server. When configuring an MCP client, point `command` at the
interpreter inside `.venv` (for example `.venv/bin/python`) so it uses the
installed dependencies.

## Configuration

Copy `.env.example` and adjust paths:

```bash
cp .env.example .env
```

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ATELIERB_PATH` | Path to Atelier B installation | `C:\Program Files\Atelier B Community Edition 24.04.2 24.04.2` |
| `ATELIERB_WORKSPACE` | Path to B projects workspace | *(none -- must be set)* |
| `ATELIERB_BBATCH_CMD` | bbatch executable name | `bbatch.exe` |
| `ATELIERB_COMMAND_TIMEOUT` | Command timeout in seconds | `120` |

**Important:** You must set `ATELIERB_PATH` and `ATELIERB_WORKSPACE` to match your local Atelier B installation and B projects directory.

## Claude Desktop Integration

Add to your Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "atelierb": {
      "command": "python",
      "args": ["-m", "atelierb_mcp.server"],
      "env": {
        "ATELIERB_PATH": "C:\\Program Files\\Atelier B Community Edition 24.04.2 24.04.2",
        "ATELIERB_WORKSPACE": "C:\\path\\to\\your\\B\\workspace"
      }
    }
  }
}
```

Adjust `ATELIERB_PATH` and `ATELIERB_WORKSPACE` to match your local setup, then restart Claude Desktop.

## Usage Examples

Once configured, you can ask Claude:

- *"List all Atelier B projects in the workspace"*
- *"Typecheck the Airlock machine in the SafetySystem project"*
- *"Run B0 check on the Airlock_i implementation"*
- *"Generate proof obligations and run the prover on Airlock"*
- *"Show the proof status of the SafetySystem project"*
- *"Generate C code for the Airlock component"*

## Development

```bash
# Run tests
pytest tests/ -v

# Run only unit tests (skip integration tests requiring bbatch)
pytest tests/ -v -m "not integration"

# Type checking
mypy atelierb_mcp/

# Linting
ruff check atelierb_mcp/

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m atelierb_mcp.server
```

## Project Structure

```
atelierb_mcp/
├── server.py              # MCP server entry point with tool definitions
├── bbatch_wrapper.py      # Async subprocess wrapper for bbatch CLI
├── parsers.py             # Output parsers for bbatch responses
├── config.py              # Pydantic settings management
└── tools/
    ├── project_tools.py   # Project management tools
    ├── proof_tools.py     # Verification tools (typecheck, prove, etc.)
    ├── file_tools.py      # File access tools
    └── code_tools.py      # C code generation tools

tests/
├── conftest.py            # pytest fixtures with mock bbatch
├── test_parsers.py        # Parser unit tests
└── test_bbatch_wrapper.py # Wrapper tests

docs/
├── ARCHITECTURE.md        # Detailed architecture documentation
├── DEPLOYMENT_GUIDE.md    # Step-by-step deployment instructions
└── bbatch_commands.md     # bbatch CLI command reference
```

## How This Project Was Built

This project was developed using [Claude Code](https://claude.ai/code) (Anthropic's CLI for Claude). The entire codebase -- server implementation, tools, parsers, tests, and documentation -- was written through interactive sessions with Claude Code, guided by a development plan and iterative refinement.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Step-by-step deployment instructions
- [bbatch Commands](docs/bbatch_commands.md) - Atelier B CLI reference

## License

Copyright (C) 2026 [CLEARSY](https://www.clearsy.com)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE.md](LICENSE.md) for the full license text.
