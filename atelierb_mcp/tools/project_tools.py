# Copyright (C) 2026 CLEARSY (https://www.clearsy.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of atelierb-mcp.
#
# atelierb-mcp is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# atelierb-mcp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with atelierb-mcp. If not, see <https://www.gnu.org/licenses/>.

"""Project-level MCP tools for Atelier B."""

import os
from pathlib import Path

from ..bbatch_wrapper import bbatch
from ..config import settings
from ..parsers import extract_error_message, parse_components_list, parse_project_info, parse_projects_list


async def atelierb_list_projects() -> dict:
    """List all available Atelier B projects.

    Returns:
        Dictionary with 'projects' list and 'success' status.
    """
    result = await bbatch.list_projects()

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or "Failed to list projects",
            "projects": [],
        }

    projects = parse_projects_list(result.output)
    return {
        "success": True,
        "projects": projects,
        "count": len(projects),
    }


async def atelierb_open_project(project_name: str) -> dict:
    """Open a project and verify it can be accessed.

    Args:
        project_name: Name of the project to open.

    Returns:
        Dictionary with project info and 'success' status.
    """
    # Try to get project info to verify it exists and can be opened
    result = await bbatch.infos_project(project_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to open project '{project_name}'",
        }

    info = parse_project_info(result.output)
    return {
        "success": True,
        "project": project_name,
        "info": {
            "name": info.name if info else project_name,
            "bdp_path": info.bdp_path if info else None,
            "lang_path": info.lang_path if info else None,
            "type": info.project_type if info else None,
        },
        "raw_output": result.output,
    }


async def atelierb_infos_project(project_name: str) -> dict:
    """Get detailed information about a project.

    Args:
        project_name: Name of the project.

    Returns:
        Dictionary with project information and 'success' status.
    """
    result = await bbatch.infos_project(project_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to get info for project '{project_name}'",
        }

    info = parse_project_info(result.output)
    return {
        "success": True,
        "project": project_name,
        "info": {
            "name": info.name if info else project_name,
            "bdp_path": info.bdp_path if info else None,
            "lang_path": info.lang_path if info else None,
            "type": info.project_type if info else None,
        },
        "raw_output": result.output,
    }


async def atelierb_list_components(project_name: str) -> dict:
    """List all components in a project.

    Args:
        project_name: Name of the project.

    Returns:
        Dictionary with 'components' list and 'success' status.
    """
    result = await bbatch.list_components(project_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to list components in project '{project_name}'",
            "components": [],
        }

    components = parse_components_list(result.output)
    return {
        "success": True,
        "project": project_name,
        "components": [{"name": c.name, "type": c.component_type} for c in components],
        "count": len(components),
        "raw_output": result.output,
    }


async def atelierb_create_project(
    project_name: str,
    project_type: str = "SYSTEM",
) -> dict:
    """Create a new Atelier B project in the workspace.

    This creates a new project with:
    - A bdp (project database) subdirectory for Atelier B metadata
    - A lang (translation) subdirectory for generated code (C, Rust, etc.)
    - A src subdirectory for B source files (.mch, .ref, .imp, .pmm, .def)

    Args:
        project_name: Name of the new project.
        project_type: Type of project (SYSTEM, SOFTWARE, or VALIDATION).
                     Defaults to SYSTEM.

    Returns:
        Dictionary with 'success' status and project information.
    """
    # Validate project type
    valid_types = ["SYSTEM", "SOFTWARE", "VALIDATION"]
    project_type = project_type.upper()
    if project_type not in valid_types:
        return {
            "success": False,
            "error": f"Invalid project type '{project_type}'. Must be one of: {', '.join(valid_types)}",
        }

    # Create project directories
    workspace = Path(settings.workspace)
    project_dir = workspace / project_name
    bdp_dir = project_dir / "bdp"
    lang_dir = project_dir / "lang"
    src_dir = project_dir / "src"

    # Check if project directory already exists
    if project_dir.exists():
        return {
            "success": False,
            "error": f"Project directory '{project_name}' already exists in workspace",
        }

    try:
        # Create the directories
        bdp_dir.mkdir(parents=True, exist_ok=False)
        lang_dir.mkdir(parents=True, exist_ok=False)
        src_dir.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        return {
            "success": False,
            "error": f"Failed to create project directories: {e}",
        }

    # Create the project using bbatch
    # crp <name> <pdb_dir> <lang_dir>: lang_dir is the translation path (generated code)
    result = await bbatch.create_project(
        project_name,
        str(bdp_dir),
        str(lang_dir),
        project_type,
    )

    if not result.success:
        error = extract_error_message(result.output) or result.error
        # Try to clean up directories on failure
        try:
            if src_dir.exists() and not any(src_dir.iterdir()):
                src_dir.rmdir()
            if lang_dir.exists() and not any(lang_dir.iterdir()):
                lang_dir.rmdir()
            if bdp_dir.exists() and not any(bdp_dir.iterdir()):
                bdp_dir.rmdir()
            if project_dir.exists() and not any(project_dir.iterdir()):
                project_dir.rmdir()
        except OSError:
            pass  # Ignore cleanup errors
        return {
            "success": False,
            "error": error or f"Failed to create project '{project_name}'",
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "type": project_type,
        "paths": {
            "project_dir": str(project_dir),
            "bdp_dir": str(bdp_dir),
            "lang_dir": str(lang_dir),
            "src_dir": str(src_dir),
        },
        "raw_output": result.output,
    }


async def atelierb_add_component(
    project_name: str,
    component_name: str,
    component_type: str,
    content: str | None = None,
) -> dict:
    """Add a new B component (machine, refinement, or implementation) to a project.

    Creates the component file in the project's src directory and registers it
    with Atelier B using the af (add_file) command.

    Args:
        project_name: Name of the project to add the component to.
        component_name: Name of the component (without extension).
        component_type: Type of component: 'machine', 'refinement', or 'implementation'.
        content: Optional initial content for the file. If not provided, a template
                will be generated based on the component type.

    Returns:
        Dictionary with 'success' status and component information.
    """
    # Validate component type and determine extension
    type_map = {
        "machine": (".mch", "MACHINE"),
        "refinement": (".ref", "REFINEMENT"),
        "implementation": (".imp", "IMPLEMENTATION"),
    }

    component_type_lower = component_type.lower()
    if component_type_lower not in type_map:
        return {
            "success": False,
            "error": f"Invalid component type '{component_type}'. Must be one of: machine, refinement, implementation",
        }

    extension, b_keyword = type_map[component_type_lower]

    # Get project info to find the src directory
    info_result = await bbatch.infos_project(project_name)
    if not info_result.success:
        error = extract_error_message(info_result.output) or info_result.error
        return {
            "success": False,
            "error": error or f"Project '{project_name}' not found",
        }

    project_info = parse_project_info(info_result.output)
    if not project_info or not project_info.bdp_path:
        return {
            "success": False,
            "error": f"Could not determine project paths for '{project_name}'",
        }

    # src/ is a sibling of bdp/ in the project directory
    project_dir = Path(project_info.bdp_path).parent
    src_dir = project_dir / "src"
    if not src_dir.exists():
        # Fallback: if src/ doesn't exist, try lang/ for backward compatibility
        if project_info.lang_path:
            lang_dir = Path(project_info.lang_path)
            if lang_dir.exists():
                src_dir = lang_dir
            else:
                return {
                    "success": False,
                    "error": f"Neither src/ nor lang/ directory exists for project '{project_name}'",
                }
        else:
            return {
                "success": False,
                "error": f"Source directory does not exist: {src_dir}",
            }

    # Create the file path
    file_name = f"{component_name}{extension}"
    file_path = src_dir / file_name

    if file_path.exists():
        return {
            "success": False,
            "error": f"Component file already exists: {file_path}",
        }

    # Generate default content if not provided
    if content is None:
        if component_type_lower == "machine":
            content = f"""{b_keyword}
    {component_name}

SETS

CONSTANTS

PROPERTIES

VARIABLES

INVARIANT

INITIALISATION

OPERATIONS

END
"""
        elif component_type_lower == "refinement":
            content = f"""{b_keyword}
    {component_name}

REFINES
    /* refines_component */

SETS

CONSTANTS

PROPERTIES

VARIABLES

INVARIANT

INITIALISATION

OPERATIONS

END
"""
        else:  # implementation
            content = f"""{b_keyword}
    {component_name}

REFINES
    /* refines_component */

IMPORTS

SEES

CONCRETE_VARIABLES

INVARIANT

INITIALISATION

OPERATIONS

END
"""

    # Write the file
    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as e:
        return {
            "success": False,
            "error": f"Failed to write component file: {e}",
        }

    # Add the file to the project using bbatch
    result = await bbatch.add_file(project_name, str(file_path))

    if not result.success:
        error = extract_error_message(result.output) or result.error
        # Try to clean up the file on failure
        try:
            file_path.unlink()
        except OSError:
            pass
        return {
            "success": False,
            "error": error or f"Failed to add component '{component_name}' to project",
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": {
            "name": component_name,
            "type": component_type_lower,
            "file": str(file_path),
        },
        "raw_output": result.output,
    }


async def atelierb_remove_component(
    project_name: str,
    component_name: str,
    delete_file: bool = False,
) -> dict:
    """Remove a component from an Atelier B project.

    This unregisters the component from the project. Optionally, it can also
    delete the source file from disk.

    Args:
        project_name: Name of the project.
        component_name: Name of the component to remove.
        delete_file: If True, also delete the source file from disk.
                    Defaults to False (only unregister from project).

    Returns:
        Dictionary with 'success' status and removal information.
    """
    # Get project info to find the lang directory (needed if deleting file)
    info_result = await bbatch.infos_project(project_name)
    if not info_result.success:
        error = extract_error_message(info_result.output) or info_result.error
        return {
            "success": False,
            "error": error or f"Project '{project_name}' not found",
        }

    project_info = parse_project_info(info_result.output)

    # Remove the component from the project
    result = await bbatch.remove_component(project_name, component_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to remove component '{component_name}' from project",
            "raw_output": result.output,
        }

    deleted_file = None
    if delete_file and project_info and project_info.lang_path:
        lang_dir = Path(project_info.lang_path)
        # Try common extensions
        for ext in [".mch", ".ref", ".imp", ".erf"]:
            file_path = lang_dir / f"{component_name}{ext}"
            if file_path.exists():
                try:
                    file_path.unlink()
                    deleted_file = str(file_path)
                    break
                except OSError as e:
                    return {
                        "success": True,
                        "project": project_name,
                        "component": component_name,
                        "unregistered": True,
                        "file_deleted": False,
                        "warning": f"Component unregistered but failed to delete file: {e}",
                        "raw_output": result.output,
                    }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "unregistered": True,
        "file_deleted": deleted_file is not None,
        "deleted_file": deleted_file,
        "raw_output": result.output,
    }


async def atelierb_remove_project(
    project_name: str,
    delete_files: bool = False,
) -> dict:
    """Remove an Atelier B project.

    This removes the project from Atelier B's database. Optionally, it can also
    delete all project files from disk.

    WARNING: If delete_files is True, this will permanently delete the project
    directory and all its contents (source files, proof files, etc.).

    Args:
        project_name: Name of the project to remove.
        delete_files: If True, also delete project directory from disk.
                     Defaults to False (only unregister from Atelier B).

    Returns:
        Dictionary with 'success' status and removal information.
    """
    import shutil

    # Get project info before removing (to get paths for deletion)
    project_dir = None
    if delete_files:
        info_result = await bbatch.infos_project(project_name)
        if info_result.success:
            project_info = parse_project_info(info_result.output)
            if project_info and project_info.bdp_path:
                # Project dir is parent of bdp
                project_dir = Path(project_info.bdp_path).parent

    # Remove the project from Atelier B database
    result = await bbatch.remove_project(project_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to remove project '{project_name}'",
            "raw_output": result.output,
        }

    deleted_dir = None
    if delete_files and project_dir and project_dir.exists():
        try:
            shutil.rmtree(project_dir)
            deleted_dir = str(project_dir)
        except OSError as e:
            return {
                "success": True,
                "project": project_name,
                "unregistered": True,
                "files_deleted": False,
                "warning": f"Project unregistered but failed to delete directory: {e}",
                "raw_output": result.output,
            }

    return {
        "success": True,
        "project": project_name,
        "unregistered": True,
        "files_deleted": deleted_dir is not None,
        "deleted_directory": deleted_dir,
        "raw_output": result.output,
    }
