# Atelier B MCP Server - Deployment Guide

## Prerequisites

Before deploying the MCP server, ensure the following software is installed:

1. **Python 3.11 or higher**
   - Verify installation: `python --version`

2. **Atelier B Community Edition**
   - Default installation path: `C:\Program Files\Atelier B Community Edition 24.04.2 24.04.2`
   - Verify that `bbatch.exe` exists in the `bin` subdirectory

3. **Claude Desktop** (for using the MCP server)
   - Download from Anthropic's official website

---

## Step-by-Step Deployment Procedure

### Step 1: Extract the Deployment Archive

1. Extract `atelierb-mcp-deploy.zip` to a directory of your choice
   - Example: `C:\Tools\atelierb-mcp`

2. Verify the extracted structure:
   ```
   atelierb-mcp/
   ├── run_server.py
   ├── pyproject.toml
   ├── requirements.txt
   └── atelierb_mcp/
       ├── __init__.py
       ├── server.py
       ├── config.py
       ├── bbatch_wrapper.py
       ├── parsers.py
       └── tools/
           ├── __init__.py
           ├── project_tools.py
           ├── proof_tools.py
           ├── file_tools.py
           └── code_tools.py
   ```

### Step 2: Install Python Dependencies

1. Open a command prompt (cmd) or PowerShell

2. Navigate to the extracted directory:
   ```cmd
   cd C:\Tools\atelierb-mcp
   ```

3. Install the required dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

   Alternatively, install directly:
   ```cmd
   pip install mcp pydantic pydantic-settings
   ```

### Step 3: Verify Installation

1. Test that the server can start:
   ```cmd
   python run_server.py
   ```

   If successful, you should see:
   ```
   INFO:atelierb_mcp.server:Starting Atelier B MCP Server
   INFO:atelierb_mcp.server:  Atelier B path: ...
   INFO:atelierb_mcp.server:  Workspace: ...
   INFO:atelierb_mcp.server:  bbatch: ...
   ```

   Press `Ctrl+C` to stop the server.

### Step 4: Configure Claude Desktop

1. Locate the Claude Desktop configuration file:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

   Full path example: `C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json`

2. Create or edit the file with the following content:
   ```json
   {
     "mcpServers": {
       "atelierb": {
         "command": "python",
         "args": ["C:\\Tools\\atelierb-mcp\\run_server.py"],
         "env": {
           "ATELIERB_PATH": "C:\\Program Files\\Atelier B Community Edition 24.04.2 24.04.2",
           "ATELIERB_WORKSPACE": "C:\\Work\\B\\MyWorkspace"
         }
       }
     }
   }
   ```

3. **Important**: Customize the following values:
   - `args`: Update the path to match where you extracted the archive
   - `ATELIERB_PATH`: Update if Atelier B is installed in a different location
   - `ATELIERB_WORKSPACE`: Set to your B projects workspace directory

### Step 5: Restart Claude Desktop

1. Close Claude Desktop completely:
   - Right-click on the Claude icon in the system tray
   - Select "Quit" or "Exit"

2. Restart Claude Desktop

3. Verify the MCP server is connected:
   - In Claude Desktop, look for the MCP server indicator
   - The "atelierb" connector should appear as active

---

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATELIERB_PATH` | Path to Atelier B installation | `C:\Program Files\Atelier B Community Edition 24.04.2 24.04.2` |
| `ATELIERB_WORKSPACE` | Path to B projects workspace | `C:\Work\B\WK25.02` |
| `ATELIERB_BBATCH_CMD` | bbatch executable name | `bbatch.exe` |
| `ATELIERB_COMMAND_TIMEOUT` | Command timeout in seconds | `120` |

### Alternative: Using .env File

Instead of setting environment variables in `claude_desktop_config.json`, you can create a `.env` file in the server directory:

```env
ATELIERB_PATH=C:\Program Files\Atelier B Community Edition 24.04.2 24.04.2
ATELIERB_WORKSPACE=C:\Work\B\MyWorkspace
```

---

## Troubleshooting

### Server doesn't start

1. **Check Python path**: Ensure Python is in your system PATH
   ```cmd
   where python
   ```

2. **Check dependencies**: Verify all packages are installed
   ```cmd
   pip list | findstr mcp
   pip list | findstr pydantic
   ```

3. **Check Atelier B path**: Verify bbatch.exe exists
   ```cmd
   dir "C:\Program Files\Atelier B Community Edition 24.04.2 24.04.2\bin\bbatch.exe"
   ```

### MCP server not appearing in Claude Desktop

1. **Check configuration syntax**: Ensure `claude_desktop_config.json` is valid JSON
   - Use a JSON validator or editor with syntax highlighting

2. **Check paths**: Ensure all paths use double backslashes (`\\`) in JSON

3. **Check logs**: View MCP server logs at:
   ```
   %APPDATA%\Claude\logs\mcp-server-atelierb.log
   ```

### Commands timeout

Increase the timeout value in the configuration:
```json
"env": {
  "ATELIERB_COMMAND_TIMEOUT": "300"
}
```

---

## Verifying the Installation

After deployment, test the MCP server by asking Claude to:

1. **List projects**: "List all Atelier B projects in the workspace"

2. **Get project status**: "Show the proof status of the [ProjectName] project"

3. **Read a file**: "Show me the content of the main machine file in [ProjectName]"

4. **Typecheck a component**: "Typecheck the [ComponentName] in [ProjectName]"

5. **B0 check** (for implementations): "Run B0 check on [ImplementationName] in [ProjectName]"

6. **Generate C code**: "Generate C code for [ComponentName] in [ProjectName]"

If these commands work, the deployment is successful.

---

## Available Tools

The MCP server provides the following tools:

| Category | Tools |
|----------|-------|
| **Project Management** | `atelierb_list_projects`, `atelierb_infos_project`, `atelierb_list_components`, `atelierb_create_project`, `atelierb_remove_project`, `atelierb_add_component`, `atelierb_remove_component` |
| **Verification** | `atelierb_typecheck`, `atelierb_b0check`, `atelierb_pogenerate`, `atelierb_prove`, `atelierb_status` |
| **Code Generation** | `atelierb_generate_c`, `atelierb_generate_project_c` |
| **File Operations** | `atelierb_list_files`, `atelierb_read_file`, `atelierb_write_file`, `atelierb_list_project_structure` |

---

## Uninstallation

1. Remove the MCP server configuration from `claude_desktop_config.json`

2. Delete the extracted server directory

3. Optionally, remove installed packages:
   ```cmd
   pip uninstall mcp pydantic pydantic-settings
   ```
