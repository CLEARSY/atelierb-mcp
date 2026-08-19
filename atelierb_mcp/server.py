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

"""MCP Server for Atelier B."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from .config import settings
from .tools import (
    atelierb_add_component,
    atelierb_archive,
    atelierb_b0check,
    atelierb_counter_example,
    atelierb_create_project,
    atelierb_extprove,
    atelierb_extreplay,
    atelierb_generate_c,
    atelierb_generate_project_c,
    atelierb_generate_rust,
    atelierb_infos_component,
    atelierb_infos_project,
    atelierb_list_components,
    atelierb_list_files,
    atelierb_list_proof_mechanisms,
    atelierb_list_project_structure,
    atelierb_list_projects,
    atelierb_make_all,
    atelierb_metrics,
    atelierb_pogenerate,
    atelierb_proof_timeout,
    atelierb_project_check,
    atelierb_prove,
    atelierb_read_file,
    atelierb_remake,
    atelierb_remove_component,
    atelierb_remove_project,
    atelierb_restore,
    atelierb_status,
    atelierb_typecheck,
    atelierb_version,
    atelierb_unprove,
    atelierb_unproved_status,
    atelierb_write_file,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_tools(ctx, params) -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(tools=[
        Tool(
            name="atelierb_list_projects",
            description="List all available Atelier B projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="atelierb_infos_project",
            description="Get detailed information about an Atelier B project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_list_components",
            description="List all components (machines, refinements, implementations) in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_typecheck",
            description="Typecheck a B component to verify syntax and type correctness",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component to typecheck",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_b0check",
            description="B0 check a B component to verify it is B0 compliant (required before C code generation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component to check (usually an implementation)",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_pogenerate",
            description="Generate proof obligations for a B component",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                    "differential": {
                        "type": "boolean",
                        "description": "If true, only generate new/changed POs",
                        "default": False,
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_prove",
            description="Run automatic prover on a B component. Force levels: 0-3 (auto), 10-13 (forced), -1 (fast), -2 (replay)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                    "force": {
                        "type": "integer",
                        "description": "Proof force level (0-3 auto, 10-13 forced, -1 fast, -2 replay)",
                        "default": 0,
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": (
                            "Per-proof-obligation time limit in seconds, 0 for none. "
                            "Omit to keep the configured default. Raise it on a hard "
                            "proof obligation, lower it to keep a broad sweep fast."
                        ),
                        "minimum": 0,
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_status",
            description="Get proof status of a component or entire project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component (optional, omit for global status)",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_unproved_status",
            description=(
                "Report what is left to prove, hiding everything already proved. "
                "With a component, lists the proof-obligation groups that still have "
                "unproved POs; without one, lists every component of the project that "
                "still has unproved POs. Use this rather than atelierb_status when the "
                "question is 'what remains?'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": (
                            "Name of the component (optional, omit to scan the whole project)"
                        ),
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_infos_component",
            description=(
                "Get the metadata of a component: its kind, the path of its source "
                "file, and its owner. Complements atelierb_status, which reports proof "
                "progress but not where the component lives."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_proof_timeout",
            description=(
                "Read the configured timeout of the automatic prover, in seconds, "
                "0 meaning no limit. Read-only: the timeout is scoped to a single "
                "bbatch session, so to actually bound a proof pass timeout_seconds to "
                "atelierb_prove instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="atelierb_list_proof_mechanisms",
            description=(
                "List the external proof mechanisms (SMT solvers and friends). Without "
                "a project name, lists what the Atelier B installation ships; with one, "
                "lists what that project has enabled, which is what atelierb_extprove "
                "will accept there. A mechanism can be installed yet not enabled on a "
                "given project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": (
                            "Project to inspect. Omit for the installation-wide list."
                        ),
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="atelierb_unprove",
            description=(
                "Discard the proof state of a component, sending every proof obligation "
                "back to unproved. DESTRUCTIVE and not undoable from here: automatic "
                "verdicts are lost, and on an NG project the verdicts written by external "
                "mechanisms are cleared too. Interactive proof scripts survive and can be "
                "replayed with atelierb_prove at force -2. Use it to redo a proof from "
                "scratch or to measure a prover on a whole component."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component to unprove",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_extprove",
            description=(
                "Submit a component's still-unproved proof obligations to an external "
                "prover such as an SMT solver. Natural follow-up to atelierb_prove, not a "
                "replacement: already-proved obligations are not resubmitted. Requires a "
                "project in NG mode with the mechanism enabled; the tool checks the "
                "mechanism against the project and lists the valid ones on error."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                    "mechanism": {
                        "type": "string",
                        "description": (
                            "Mechanism name, as reported by atelierb_list_proof_mechanisms "
                            "for this project (for example z3_pp)"
                        ),
                    },
                    "fast_only": {
                        "type": "boolean",
                        "description": (
                            "Use only the mechanism's fast drivers rather than all of "
                            "them. This selects drivers, not which proof obligations are "
                            "submitted."
                        ),
                        "default": False,
                    },
                },
                "required": ["project_name", "component_name", "mechanism"],
            },
        ),
        Tool(
            name="atelierb_extreplay",
            description=(
                "Replay the external proofs already recorded for a component, which is "
                "how an external verdict is checked again after the model changed. "
                "Requires a project in NG mode."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                    "mechanism": {
                        "type": "string",
                        "description": (
                            "Restrict the replay to one mechanism. Omit to replay all."
                        ),
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_counter_example",
            description=(
                "Ask an external mechanism for a counter-example on one proof obligation. "
                "When a proof obligation resists, this exhibits a valuation that satisfies "
                "the hypotheses and falsifies the goal, which usually points straight at a "
                "missing invariant or guard. Requires a project in NG mode with the "
                "mechanism enabled."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component",
                    },
                    "po": {
                        "type": "string",
                        "description": (
                            "The proof obligation, written Operation.index, for example "
                            "Operation_clear.5"
                        ),
                    },
                    "mechanism": {
                        "type": "string",
                        "description": "Mechanism name, as reported by atelierb_list_proof_mechanisms",
                    },
                    "driver": {
                        "type": "string",
                        "description": "Driver of that mechanism to run",
                    },
                },
                "required": [
                    "project_name",
                    "component_name",
                    "po",
                    "mechanism",
                    "driver",
                ],
            },
        ),
        Tool(
            name="atelierb_project_check",
            description=(
                "Check the structural integrity of a project's IMPORTS graph, from its "
                "main component. Catches what typecheck cannot see, because typecheck "
                "looks at one component at a time: a machine seen but never imported, a "
                "missing main component, a broken architectural link. Worth running "
                "before a full proof campaign."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project"},
                    "main_component": {
                        "type": "string",
                        "description": "The component at the top of the IMPORTS graph",
                    },
                },
                "required": ["project_name", "main_component"],
            },
        ),
        Tool(
            name="atelierb_make_all",
            description=(
                "Run one action over every component of a project: the one-shot way to "
                "typecheck everything, generate every proof obligation, or prove the lot, "
                "without naming components. The action is a bbatch command abbreviation, "
                "t, po or pr; a number is refused."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project"},
                    "action": {
                        "type": "string",
                        "description": "t to typecheck, po to generate proof obligations, pr to prove",
                    },
                    "force": {
                        "type": "integer",
                        "description": "Proof force, when the action is a proof",
                    },
                },
                "required": ["project_name", "action"],
            },
        ),
        Tool(
            name="atelierb_remake",
            description=(
                "Bring a whole project up to date, redoing whatever is stale. Answers "
                "'already up to date' when there is nothing to do."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project"},
                    "force": {
                        "type": "integer",
                        "description": "Proof force to use for the proof stage",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_archive",
            description=(
                "Archive a project into a tar file, the companion of atelierb_unprove and "
                "of any risky proof attempt: snapshot first, restore if it goes wrong. "
                "NOT CONFIRMED on the reference installation, where every attempt answered "
                "'Cannot Attach project' and left a zero-byte file; the cause was not "
                "isolated."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project to archive"},
                    "archive_path": {"type": "string", "description": "Path of the tar file to write"},
                    "scope": {
                        "type": "string",
                        "description": "What to include",
                        "enum": ["sources", "all", "sources_and_proofs"],
                        "default": "sources_and_proofs",
                    },
                },
                "required": ["project_name", "archive_path"],
            },
        ),
        Tool(
            name="atelierb_restore",
            description=(
                "Restore a project from a tar archive. Writes to disk, and refuses when a "
                "project directory of that name already exists rather than writing over "
                "it. NOT CONFIRMED, for the same reason as atelierb_archive."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "archive_path": {"type": "string", "description": "Path of the tar archive to read"},
                    "project_name": {"type": "string", "description": "Name to give the restored project"},
                    "project_path": {
                        "type": "string",
                        "description": "Where to put the project directory. Defaults to the workspace.",
                    },
                },
                "required": ["archive_path", "project_name"],
            },
        ),
        Tool(
            name="atelierb_generate_rust",
            description=(
                "Generate Rust code for an implementation and its dependencies, the Rust "
                "counterpart of atelierb_generate_c, with the same prerequisite that "
                "atelierb_b0check passes first. KNOWN DEFECT in Atelier B itself: when the "
                "installation path contains a space, which the default Program Files path "
                "does, the translator mis-parses its own command line and fails."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project"},
                    "component_name": {
                        "type": "string",
                        "description": "The implementation to translate",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_version",
            description=(
                "Report the Atelier B version, edition and resource settings. Useful as a "
                "first diagnostic, and the only readable place for several settings: the "
                "resources say where the external solvers and ProB are wired, and where "
                "the project database lives."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="atelierb_metrics",
            description=(
                "Detailed proof metrics for a whole project. Splits the results finer "
                "than atelierb_status: separate counts for what an external mechanism "
                "discharged and what Atelier B's own prover did, plus unreliable and "
                "disproved verdicts. Project-wide by design; the underlying command "
                "ignores a component name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project"},
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_list_files",
            description="List B source files in the workspace. Supports filtering by project and extension (.mch, .ref, .imp, .erf, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Optional project name to filter files",
                    },
                    "extension_filter": {
                        "type": "string",
                        "description": "Optional extension filter (e.g., '.mch', '.imp')",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="atelierb_read_file",
            description=(
                "Read the content of a B source file (.mch, .ref, .imp, etc.), C code (.c, .h), "
                "or Makefile from the workspace. Content is returned verbatim. For a .pmi file, "
                "a 'po_labels' list names the proof obligation each entry of its flat theories "
                "(ProofState, MethodList, PassList) belongs to; those entries carry no operation "
                "name of their own, so do not try to infer it from their position."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path from workspace root to the file",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="atelierb_write_file",
            description="Write or update the content of a B source file (.mch, .ref, .imp, etc.), C code (.c, .h), or Makefile in the workspace. Creates a backup by default.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path from workspace root to the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content to write to the file",
                    },
                    "create_backup": {
                        "type": "boolean",
                        "description": "If true (default), creates a .bak backup before overwriting",
                        "default": True,
                    },
                },
                "required": ["file_path", "content"],
            },
        ),
        Tool(
            name="atelierb_list_project_structure",
            description="Get the directory structure of a B project showing files and subdirectories",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_create_project",
            description=(
                "Create a new Atelier B project in the workspace with bdp, lang, and src "
                "subdirectories, and register it so it appears in the Atelier B IDE"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the new project",
                    },
                    "project_type": {
                        "type": "string",
                        "description": "Type of project: SYSTEM (default), SOFTWARE, or VALIDATION",
                        "enum": ["SYSTEM", "SOFTWARE", "VALIDATION"],
                        "default": "SYSTEM",
                    },
                    "register": {
                        "type": "boolean",
                        "description": (
                            "Write the <project>.desc workspace descriptor so the project shows up "
                            "in the Atelier B IDE. Default true. Set false only for throwaway "
                            "projects that should stay out of the user's project tree; such a "
                            "project still works through bbatch but stays invisible in the IDE."
                        ),
                        "default": True,
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_add_component",
            description="Add a new B component (machine, refinement, or implementation) to a project. Creates the file in src/ with a template and registers it with Atelier B.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project to add the component to",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component (without extension)",
                    },
                    "component_type": {
                        "type": "string",
                        "description": "Type of component: machine, refinement, or implementation",
                        "enum": ["machine", "refinement", "implementation"],
                    },
                    "content": {
                        "type": "string",
                        "description": "Optional initial content for the file. If not provided, a template will be generated.",
                    },
                },
                "required": ["project_name", "component_name", "component_type"],
            },
        ),
        Tool(
            name="atelierb_remove_component",
            description="Remove a component from an Atelier B project. Optionally delete the source file from disk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component to remove",
                    },
                    "delete_file": {
                        "type": "boolean",
                        "description": "If true, also delete the source file from disk. Default: false (only unregister)",
                        "default": False,
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_remove_project",
            description="Remove an Atelier B project. WARNING: If delete_files is true, permanently deletes all project files!",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project to remove",
                    },
                    "delete_files": {
                        "type": "boolean",
                        "description": "If true, also delete the project directory and all files. Default: false (only unregister)",
                        "default": False,
                    },
                },
                "required": ["project_name"],
            },
        ),
        Tool(
            name="atelierb_generate_c",
            description="Generate C code for a single B component (implementation or basic machine). Output goes to lang/c directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "component_name": {
                        "type": "string",
                        "description": "Name of the component to translate (usually an implementation)",
                    },
                    "profile": {
                        "type": "string",
                        "description": "C translation profile: C9X (default), LIGHT, or PROJECT",
                        "enum": ["C9X", "LIGHT", "PROJECT"],
                        "default": "C9X",
                    },
                },
                "required": ["project_name", "component_name"],
            },
        ),
        Tool(
            name="atelierb_generate_project_c",
            description="Generate C code for a complete B project from a toplevel component. Output goes to lang/c directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project",
                    },
                    "toplevel_component": {
                        "type": "string",
                        "description": "Name of the toplevel component (entry point)",
                    },
                    "profile": {
                        "type": "string",
                        "description": "C translation profile: C9X (default), LIGHT, or PROJECT",
                        "enum": ["C9X", "LIGHT", "PROJECT"],
                        "default": "C9X",
                    },
                    "generate_main": {
                        "type": "boolean",
                        "description": "If true, generate a main() function for the toplevel",
                        "default": False,
                    },
                },
                "required": ["project_name", "toplevel_component"],
            },
        ),
    ])


async def call_tool(ctx, params) -> CallToolResult:
    """Handle tool calls."""
    import json

    # `arguments` is optional on the wire: tools that take no parameter arrive
    # with None, where the v1 signature always handed over a dict.
    name = params.name
    arguments = params.arguments or {}

    try:
        if name == "atelierb_list_projects":
            result = await atelierb_list_projects()
        elif name == "atelierb_infos_project":
            result = await atelierb_infos_project(arguments["project_name"])
        elif name == "atelierb_list_components":
            result = await atelierb_list_components(arguments["project_name"])
        elif name == "atelierb_typecheck":
            result = await atelierb_typecheck(
                arguments["project_name"],
                arguments["component_name"],
            )
        elif name == "atelierb_b0check":
            result = await atelierb_b0check(
                arguments["project_name"],
                arguments["component_name"],
            )
        elif name == "atelierb_pogenerate":
            result = await atelierb_pogenerate(
                arguments["project_name"],
                arguments["component_name"],
                arguments.get("differential", False),
            )
        elif name == "atelierb_prove":
            result = await atelierb_prove(
                arguments["project_name"],
                arguments["component_name"],
                arguments.get("force", 0),
                arguments.get("timeout_seconds"),
            )
        elif name == "atelierb_status":
            result = await atelierb_status(
                arguments["project_name"],
                arguments.get("component_name"),
            )
        elif name == "atelierb_unproved_status":
            result = await atelierb_unproved_status(
                arguments["project_name"],
                arguments.get("component_name"),
            )
        elif name == "atelierb_infos_component":
            result = await atelierb_infos_component(
                arguments["project_name"],
                arguments["component_name"],
            )
        elif name == "atelierb_proof_timeout":
            result = await atelierb_proof_timeout()
        elif name == "atelierb_list_proof_mechanisms":
            result = await atelierb_list_proof_mechanisms(arguments.get("project_name"))
        elif name == "atelierb_unprove":
            result = await atelierb_unprove(
                arguments["project_name"],
                arguments["component_name"],
            )
        elif name == "atelierb_extprove":
            result = await atelierb_extprove(
                arguments["project_name"],
                arguments["component_name"],
                arguments["mechanism"],
                arguments.get("fast_only", False),
            )
        elif name == "atelierb_extreplay":
            result = await atelierb_extreplay(
                arguments["project_name"],
                arguments["component_name"],
                arguments.get("mechanism"),
            )
        elif name == "atelierb_counter_example":
            result = await atelierb_counter_example(
                arguments["project_name"],
                arguments["component_name"],
                arguments["po"],
                arguments["mechanism"],
                arguments["driver"],
            )
        elif name == "atelierb_project_check":
            result = await atelierb_project_check(
                arguments["project_name"], arguments["main_component"]
            )
        elif name == "atelierb_make_all":
            result = await atelierb_make_all(
                arguments["project_name"], arguments["action"], arguments.get("force")
            )
        elif name == "atelierb_remake":
            result = await atelierb_remake(arguments["project_name"], arguments.get("force"))
        elif name == "atelierb_archive":
            result = await atelierb_archive(
                arguments["project_name"],
                arguments["archive_path"],
                arguments.get("scope", "sources_and_proofs"),
            )
        elif name == "atelierb_restore":
            result = await atelierb_restore(
                arguments["archive_path"],
                arguments["project_name"],
                arguments.get("project_path"),
            )
        elif name == "atelierb_generate_rust":
            result = await atelierb_generate_rust(
                arguments["project_name"], arguments["component_name"]
            )
        elif name == "atelierb_version":
            result = await atelierb_version()
        elif name == "atelierb_metrics":
            result = await atelierb_metrics(arguments["project_name"])
        elif name == "atelierb_list_files":
            result = await atelierb_list_files(
                arguments.get("project_name"),
                arguments.get("extension_filter"),
            )
        elif name == "atelierb_read_file":
            result = await atelierb_read_file(arguments["file_path"])
        elif name == "atelierb_write_file":
            result = await atelierb_write_file(
                arguments["file_path"],
                arguments["content"],
                arguments.get("create_backup", True),
            )
        elif name == "atelierb_list_project_structure":
            result = await atelierb_list_project_structure(arguments["project_name"])
        elif name == "atelierb_create_project":
            result = await atelierb_create_project(
                arguments["project_name"],
                arguments.get("project_type", "SYSTEM"),
                arguments.get("register", True),
            )
        elif name == "atelierb_add_component":
            result = await atelierb_add_component(
                arguments["project_name"],
                arguments["component_name"],
                arguments["component_type"],
                arguments.get("content"),
            )
        elif name == "atelierb_remove_component":
            result = await atelierb_remove_component(
                arguments["project_name"],
                arguments["component_name"],
                arguments.get("delete_file", False),
            )
        elif name == "atelierb_remove_project":
            result = await atelierb_remove_project(
                arguments["project_name"],
                arguments.get("delete_files", False),
            )
        elif name == "atelierb_generate_c":
            result = await atelierb_generate_c(
                arguments["project_name"],
                arguments["component_name"],
                arguments.get("profile", "C9X"),
            )
        elif name == "atelierb_generate_project_c":
            result = await atelierb_generate_project_c(
                arguments["project_name"],
                arguments["toplevel_component"],
                arguments.get("profile", "C9X"),
                arguments.get("generate_main", False),
            )
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        # Reported as a normal result, not a protocol error, so the client sees
        # the same `success: false` payload the tools themselves return.
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"success": False, "error": str(e)}),
                )
            ]
        )


# Handlers are registered on the constructor: mcp 2.0 dropped the
# @server.list_tools() / @server.call_tool() decorators.
server = Server("atelierb-mcp", on_list_tools=list_tools, on_call_tool=call_tool)


async def run_server():
    """Run the MCP server."""
    # Validate configuration
    errors = settings.validate_paths()
    if errors:
        for error in errors:
            logger.warning(f"Configuration warning: {error}")

    logger.info(f"Starting Atelier B MCP Server")
    logger.info(f"  Atelier B path: {settings.path}")
    logger.info(f"  Workspace: {settings.workspace}")
    logger.info(f"  bbatch: {settings.bbatch_path}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
