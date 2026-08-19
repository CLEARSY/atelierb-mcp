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
    atelierb_archive,
    atelierb_b0check,
    atelierb_counter_example,
    atelierb_extprove,
    atelierb_extreplay,
    atelierb_generate_rust,
    atelierb_make_all,
    atelierb_list_proof_mechanisms,
    atelierb_infos_component,
    atelierb_pogenerate,
    atelierb_proof_timeout,
    atelierb_project_check,
    atelierb_prove,
    atelierb_remake,
    atelierb_restore,
    atelierb_status,
    atelierb_typecheck,
    atelierb_unprove,
    atelierb_unproved_status,
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
    "atelierb_unproved_status",
    "atelierb_infos_component",
    "atelierb_proof_timeout",
    "atelierb_list_proof_mechanisms",
    "atelierb_unprove",
    "atelierb_extprove",
    "atelierb_extreplay",
    "atelierb_counter_example",
    "atelierb_project_check",
    "atelierb_archive",
    "atelierb_restore",
    "atelierb_make_all",
    "atelierb_remake",
    "atelierb_generate_rust",
    # Code generation tools
    "atelierb_generate_c",
    "atelierb_generate_project_c",
    # File tools
    "atelierb_list_files",
    "atelierb_read_file",
    "atelierb_write_file",
    "atelierb_list_project_structure",
]
