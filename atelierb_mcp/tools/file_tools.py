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

"""File access tools for reading B source files from the workspace."""

import os
from pathlib import Path

from ..config import settings


# Allowed file extensions for B method files
B_SOURCE_EXTENSIONS = {".mch", ".ref", ".imp", ".erf", ".pmm", ".rmf", ".imf"}

# Additional extensions that may be needed (readable but not writable)
ADDITIONAL_EXTENSIONS = {".def", ".bxml", ".pmi", ".nf", ".po"}

# Generated code extensions (C code output) - readable and writable
GENERATED_CODE_EXTENSIONS = {".c", ".h"}

# Special filenames that are allowed (e.g., Makefile has no extension)
ALLOWED_FILENAMES = {"makefile", "makefile.mak"}

# All allowed extensions for reading
ALLOWED_EXTENSIONS = B_SOURCE_EXTENSIONS | ADDITIONAL_EXTENSIONS | GENERATED_CODE_EXTENSIONS

# All allowed extensions for writing (B source + generated C code)
WRITABLE_EXTENSIONS = B_SOURCE_EXTENSIONS | GENERATED_CODE_EXTENSIONS


def _is_safe_path(file_path: Path, base_path: Path) -> bool:
    """Check if file_path is safely within base_path (prevent directory traversal)."""
    try:
        # Resolve to absolute paths
        resolved_file = file_path.resolve()
        resolved_base = base_path.resolve()
        # Check if file is within base directory
        return resolved_file.is_relative_to(resolved_base)
    except (ValueError, OSError):
        return False


def _get_file_extension(file_path: Path) -> str:
    """Get the lowercase file extension."""
    return file_path.suffix.lower()


async def atelierb_list_files(
    project_name: str | None = None,
    extension_filter: str | None = None,
) -> dict:
    """
    List files in the workspace, optionally filtered by project and extension.

    Args:
        project_name: Optional project name to list files from a specific project
        extension_filter: Optional extension filter (e.g., ".mch", ".imp")

    Returns:
        Dictionary with success status and list of files
    """
    try:
        workspace = settings.workspace

        if not workspace.exists():
            return {
                "success": False,
                "error": f"Workspace not found: {workspace}",
            }

        # Determine search path
        if project_name:
            search_path = workspace / project_name
            if not search_path.exists():
                return {
                    "success": False,
                    "error": f"Project directory not found: {project_name}",
                }
        else:
            search_path = workspace

        # Collect files
        files = []
        for root, _, filenames in os.walk(search_path):
            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename
                ext = _get_file_extension(file_path)

                # Apply extension filter
                if extension_filter:
                    if ext != extension_filter.lower():
                        continue
                elif ext not in ALLOWED_EXTENSIONS:
                    continue

                # Get relative path from workspace
                rel_path = file_path.relative_to(workspace)
                files.append({
                    "path": str(rel_path),
                    "name": filename,
                    "extension": ext,
                    "size": file_path.stat().st_size,
                })

        # Sort by path
        files.sort(key=lambda x: x["path"])

        return {
            "success": True,
            "workspace": str(workspace),
            "project": project_name,
            "filter": extension_filter,
            "count": len(files),
            "files": files,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def atelierb_read_file(
    file_path: str,
) -> dict:
    """
    Read a B source file from the workspace.

    Args:
        file_path: Relative path from workspace root to the file

    Returns:
        Dictionary with success status and file content
    """
    try:
        workspace = settings.workspace

        # Construct full path
        full_path = workspace / file_path

        # Security check: ensure path is within workspace
        if not _is_safe_path(full_path, workspace):
            return {
                "success": False,
                "error": "Access denied: path is outside workspace directory",
            }

        # Check if file exists
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        if not full_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
            }

        # Check extension or special filename
        ext = _get_file_extension(full_path)
        filename_lower = full_path.name.lower()
        if ext not in ALLOWED_EXTENSIONS and filename_lower not in ALLOWED_FILENAMES:
            return {
                "success": False,
                "error": f"File type not allowed: {full_path.name}. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            }

        # Read file content
        content = full_path.read_text(encoding="utf-8", errors="replace")

        return {
            "success": True,
            "path": file_path,
            "full_path": str(full_path),
            "extension": ext,
            "size": len(content),
            "content": content,
        }

    except UnicodeDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to decode file (encoding issue): {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def atelierb_list_project_structure(
    project_name: str,
) -> dict:
    """
    Get the directory structure of a B project.

    Args:
        project_name: Name of the project

    Returns:
        Dictionary with success status and project structure
    """
    try:
        workspace = settings.workspace
        project_path = workspace / project_name

        if not project_path.exists():
            return {
                "success": False,
                "error": f"Project not found: {project_name}",
            }

        if not project_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {project_name}",
            }

        # Build directory structure
        structure = {
            "directories": [],
            "files": [],
        }

        for item in sorted(project_path.iterdir()):
            if item.is_dir():
                # Count files in subdirectory
                file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                structure["directories"].append({
                    "name": item.name,
                    "file_count": file_count,
                })
            elif item.is_file():
                ext = _get_file_extension(item)
                structure["files"].append({
                    "name": item.name,
                    "extension": ext,
                    "size": item.stat().st_size,
                    "is_b_source": ext in B_SOURCE_EXTENSIONS,
                })

        return {
            "success": True,
            "project": project_name,
            "path": str(project_path),
            "structure": structure,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def atelierb_write_file(
    file_path: str,
    content: str,
    create_backup: bool = True,
) -> dict:
    """
    Write or update the content of a B source file in the workspace.

    This tool allows modifying existing B component files (.mch, .ref, .imp, etc.)
    without needing to remove and re-add them to the project.

    Args:
        file_path: Relative path from workspace root to the file
        content: The new content to write to the file
        create_backup: If True (default), creates a .bak backup before overwriting

    Returns:
        Dictionary with success status and file information
    """
    try:
        workspace = settings.workspace

        # Construct full path
        full_path = workspace / file_path

        # Security check: ensure path is within workspace
        if not _is_safe_path(full_path, workspace):
            return {
                "success": False,
                "error": "Access denied: path is outside workspace directory",
            }

        # Check extension - allow B source files, C files, and special filenames
        ext = _get_file_extension(full_path)
        filename_lower = full_path.name.lower()
        if ext not in WRITABLE_EXTENSIONS and filename_lower not in ALLOWED_FILENAMES:
            return {
                "success": False,
                "error": f"File type not allowed for writing: {full_path.name}. Allowed extensions: {', '.join(sorted(WRITABLE_EXTENSIONS))}",
            }

        # Check if file exists (we're updating, not creating new files here)
        file_exists = full_path.exists()

        if file_exists and not full_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
            }

        # Create backup if requested and file exists
        backup_path = None
        if create_backup and file_exists:
            backup_path = full_path.with_suffix(full_path.suffix + ".bak")
            try:
                import shutil
                shutil.copy2(full_path, backup_path)
            except OSError as e:
                return {
                    "success": False,
                    "error": f"Failed to create backup: {e}",
                }

        # Write the new content
        try:
            full_path.write_text(content, encoding="utf-8")
        except OSError as e:
            # Try to restore from backup if write failed
            if backup_path and backup_path.exists():
                try:
                    import shutil
                    shutil.copy2(backup_path, full_path)
                except OSError:
                    pass
            return {
                "success": False,
                "error": f"Failed to write file: {e}",
            }

        return {
            "success": True,
            "path": file_path,
            "full_path": str(full_path),
            "extension": ext,
            "size": len(content),
            "created": not file_exists,
            "backup_created": backup_path is not None,
            "backup_path": str(backup_path) if backup_path else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
