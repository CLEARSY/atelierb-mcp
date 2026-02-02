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

"""Code generation tools for Atelier B."""

from pathlib import Path

from ..bbatch_wrapper import bbatch
from ..parsers import extract_error_message, parse_project_info


# Valid C translation profiles
C_PROFILES = ["C9X", "LIGHT", "PROJECT"]


async def atelierb_generate_c(
    project_name: str,
    component_name: str,
    profile: str = "C9X",
) -> dict:
    """Generate C code for a single B component.

    Translates an implementation or a basic machine (specification without
    implementation) to C code. The generated code is placed in the lang/c
    directory of the project.

    For basic machines (specifications), the generated C code serves as a
    skeleton for manual implementation.

    Args:
        project_name: Name of the project.
        component_name: Name of the component to translate (usually an
                       implementation, or a specification for basic machines).
        profile: C translation profile:
                - C9X: Standard C99 profile (default)
                - LIGHT: Lightweight profile
                - PROJECT: Project-specific profile

    Returns:
        Dictionary with 'success' status and generation information.
    """
    # Validate profile
    profile = profile.upper()
    if profile not in C_PROFILES:
        return {
            "success": False,
            "error": f"Invalid profile '{profile}'. Must be one of: {', '.join(C_PROFILES)}",
        }

    # Get project info to determine output directory
    info_result = await bbatch.infos_project(project_name)
    if not info_result.success:
        error = extract_error_message(info_result.output) or info_result.error
        return {
            "success": False,
            "error": error or f"Project '{project_name}' not found",
        }

    project_info = parse_project_info(info_result.output)
    c_output_dir = None
    if project_info and project_info.lang_path:
        c_output_dir = Path(project_info.lang_path) / "c"

    # Execute translation
    result = await bbatch.translate_to_c(project_name, component_name, profile)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to generate C code for '{component_name}'",
            "raw_output": result.output,
        }

    # Check for generated files
    generated_files = []
    if c_output_dir and c_output_dir.exists():
        # Look for files matching the component name
        for ext in [".c", ".h"]:
            file_path = c_output_dir / f"{component_name}{ext}"
            if file_path.exists():
                generated_files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                })

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "profile": profile,
        "output_directory": str(c_output_dir) if c_output_dir else None,
        "generated_files": generated_files,
        "raw_output": result.output,
    }


async def atelierb_generate_project_c(
    project_name: str,
    toplevel_component: str,
    profile: str = "C9X",
    generate_main: bool = False,
) -> dict:
    """Generate C code for a complete B project.

    Translates all components of a project to C code starting from a toplevel
    component. The generated code is placed in the lang/c directory.

    Args:
        project_name: Name of the project.
        toplevel_component: Name of the toplevel component (entry point).
        profile: C translation profile:
                - C9X: Standard C99 profile (default)
                - LIGHT: Lightweight profile
                - PROJECT: Project-specific profile
        generate_main: If True, generate a main() function for the toplevel.

    Returns:
        Dictionary with 'success' status and generation information.
    """
    # Validate profile
    profile = profile.upper()
    if profile not in C_PROFILES:
        return {
            "success": False,
            "error": f"Invalid profile '{profile}'. Must be one of: {', '.join(C_PROFILES)}",
        }

    # Get project info to determine output directory
    info_result = await bbatch.infos_project(project_name)
    if not info_result.success:
        error = extract_error_message(info_result.output) or info_result.error
        return {
            "success": False,
            "error": error or f"Project '{project_name}' not found",
        }

    project_info = parse_project_info(info_result.output)
    c_output_dir = None
    if project_info and project_info.lang_path:
        c_output_dir = Path(project_info.lang_path) / "c"

    # Execute project translation
    result = await bbatch.translate_project_to_c(
        project_name, toplevel_component, profile, generate_main
    )

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to generate C code for project '{project_name}'",
            "raw_output": result.output,
        }

    # List all generated files
    generated_files = []
    if c_output_dir and c_output_dir.exists():
        for file_path in c_output_dir.iterdir():
            if file_path.is_file() and file_path.suffix in [".c", ".h"]:
                generated_files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                })
        generated_files.sort(key=lambda x: x["name"])

    return {
        "success": True,
        "project": project_name,
        "toplevel": toplevel_component,
        "profile": profile,
        "main_generated": generate_main,
        "output_directory": str(c_output_dir) if c_output_dir else None,
        "generated_files": generated_files,
        "file_count": len(generated_files),
        "raw_output": result.output,
    }
