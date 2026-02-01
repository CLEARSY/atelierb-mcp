"""MCP Tools for Atelier B operations."""

from .code_tools import atelierb_generate_c, atelierb_generate_project_c
from .file_tools import (
    atelierb_list_files,
    atelierb_list_project_structure,
    atelierb_read_file,
    atelierb_write_file,
)
from .project_tools import (
    atelierb_add_component,
    atelierb_create_project,
    atelierb_infos_project,
    atelierb_list_components,
    atelierb_list_projects,
    atelierb_open_project,
    atelierb_remove_component,
    atelierb_remove_project,
)
from .proof_tools import (
    atelierb_b0check,
    atelierb_pogenerate,
    atelierb_prove,
    atelierb_status,
    atelierb_typecheck,
)

__all__ = [
    # Project tools
    "atelierb_list_projects",
    "atelierb_open_project",
    "atelierb_infos_project",
    "atelierb_list_components",
    "atelierb_create_project",
    "atelierb_add_component",
    "atelierb_remove_component",
    "atelierb_remove_project",
    # Proof tools
    "atelierb_typecheck",
    "atelierb_b0check",
    "atelierb_pogenerate",
    "atelierb_prove",
    "atelierb_status",
    # Code generation tools
    "atelierb_generate_c",
    "atelierb_generate_project_c",
    # File tools
    "atelierb_list_files",
    "atelierb_read_file",
    "atelierb_write_file",
    "atelierb_list_project_structure",
]
