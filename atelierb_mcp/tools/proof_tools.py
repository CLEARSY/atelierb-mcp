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

"""Proof-related MCP tools for Atelier B."""

from ..bbatch_wrapper import bbatch
from ..parsers import (
    extract_error_message,
    parse_component_info,
    parse_global_status,
    parse_status,
    parse_timeout,
)


def _status_payload(status) -> dict:
    """Shared shape for the status dictionaries, groups included."""
    return {
        "typecheck_ok": status.typecheck_ok,
        "po_generated": status.po_generated,
        "total_po": status.total_po,
        "proved_po": status.proved_po,
        "unproved_po": status.unproved_po,
        "proved_interactively": status.proved_interactively,
        "proved_automatically": status.proved_automatically,
        "proof_percentage": status.proof_percentage,
        "groups": [
            {
                "name": g.name,
                "total_po": g.total_po,
                "proved_po": g.proved_po,
                "unproved_po": g.unproved_po,
                "proved_interactively": g.proved_interactively,
                "proved_automatically": g.proved_automatically,
            }
            for g in status.groups
        ],
    }


async def atelierb_typecheck(project_name: str, component_name: str) -> dict:
    """Typecheck a B component.

    Args:
        project_name: Name of the project.
        component_name: Name of the component to typecheck.

    Returns:
        Dictionary with typecheck result and 'success' status.
    """
    result = await bbatch.typecheck(project_name, component_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Typecheck failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "raw_output": result.output,
        }

    # Check for typecheck errors in output
    has_errors = "error" in result.output.lower() and "0 error" not in result.output.lower()

    return {
        "success": not has_errors,
        "project": project_name,
        "component": component_name,
        "typecheck_passed": not has_errors,
        "raw_output": result.output,
    }


async def atelierb_b0check(project_name: str, component_name: str) -> dict:
    """B0 check a B component (verify B0 compliance for C code generation).

    B0 is a subset of the B language that can be directly translated to C code.
    This check verifies that an implementation (or basic machine) is B0 compliant,
    which is required before generating C code.

    Args:
        project_name: Name of the project.
        component_name: Name of the component to check (usually an implementation).

    Returns:
        Dictionary with B0 check result and 'success' status.
    """
    result = await bbatch.b0check(project_name, component_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"B0 check failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "raw_output": result.output,
        }

    # Check for B0 check errors in output
    has_errors = "error" in result.output.lower() and "0 error" not in result.output.lower()

    return {
        "success": not has_errors,
        "project": project_name,
        "component": component_name,
        "b0_compliant": not has_errors,
        "raw_output": result.output,
    }


async def atelierb_pogenerate(
    project_name: str, component_name: str, differential: bool = False
) -> dict:
    """Generate proof obligations for a B component.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.
        differential: If True, only generate new/changed POs.

    Returns:
        Dictionary with PO generation result and 'success' status.
    """
    result = await bbatch.pogenerate(project_name, component_name, differential)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"PO generation failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "differential": differential,
        "raw_output": result.output,
    }


async def atelierb_prove(
    project_name: str,
    component_name: str,
    force: int = 0,
    timeout_seconds: int | None = None,
) -> dict:
    """Run automatic prover on a B component.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.
        force: Proof force level:
            - 0, 1, 2, 3: Automatic forces (increasing strength)
            - 10, 11, 12, 13: Same as 0-3 but forced
            - -1: Fast
            - -2: Replay
        timeout_seconds: Per-proof-obligation time limit, 0 for none. Omit to
            keep the configured default, which `atelierb_proof_timeout` reports.
            The setting is session-scoped in bbatch, so it is issued here rather
            than through a separate call, which would have no effect.

    Returns:
        Dictionary with proof result and 'success' status.
    """
    if timeout_seconds is not None and timeout_seconds < 0:
        return {
            "success": False,
            "error": f"Timeout must be zero or positive, got {timeout_seconds}",
        }

    result = await bbatch.prove(project_name, component_name, force, timeout_seconds)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Proof failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "force": force,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "force": force,
        "timeout_seconds": timeout_seconds,
        "raw_output": result.output,
    }


async def atelierb_status(project_name: str, component_name: str | None = None) -> dict:
    """Get proof status of a component or entire project.

    Args:
        project_name: Name of the project.
        component_name: Name of the component (optional). If None, returns global status.

    Returns:
        Dictionary with status information and 'success' status.
    """
    if component_name:
        result = await bbatch.status(project_name, component_name)

        if not result.success:
            error = extract_error_message(result.output) or result.error
            return {
                "success": False,
                "error": error or f"Failed to get status for '{component_name}'",
                "project": project_name,
                "component": component_name,
                "raw_output": result.output,
            }

        status = parse_status(result.output)
        return {
            "success": True,
            "project": project_name,
            "component": component_name,
            "status": _status_payload(status) if status else None,
            "raw_output": result.output,
        }
    else:
        result = await bbatch.status_global(project_name)

        if not result.success:
            error = extract_error_message(result.output) or result.error
            return {
                "success": False,
                "error": error or f"Failed to get global status for project '{project_name}'",
                "project": project_name,
                "raw_output": result.output,
            }

        statuses = parse_global_status(result.output)
        return {
            "success": True,
            "project": project_name,
            "components": [
                {
                    "name": s.name,
                    "total_po": s.total_po,
                    "proved_po": s.proved_po,
                    "unproved_po": s.unproved_po,
                    "proof_percentage": s.proof_percentage,
                }
                for s in statuses
            ],
            "summary": {
                "total_components": len(statuses),
                "total_po": sum(s.total_po for s in statuses),
                "total_proved": sum(s.proved_po for s in statuses),
                "total_unproved": sum(s.unproved_po for s in statuses),
            },
            "raw_output": result.output,
        }


async def atelierb_unproved_status(
    project_name: str, component_name: str | None = None
) -> dict:
    """Report what is left to prove, filtering out everything already proved.

    Wraps `us` for a single component and `ug` for the whole project. It answers
    "what is left to prove?" directly, where `atelierb_status` returns
    everything and leaves the filtering to the caller.

    Args:
        project_name: Name of the project.
        component_name: Name of the component. When omitted, every component of
            the project that still has unproved proof obligations is reported.

    Returns:
        Dictionary with the unproved breakdown and 'success' status.
    """
    if component_name:
        result = await bbatch.unproved_status(project_name, component_name)

        if not result.success:
            error = extract_error_message(result.output) or result.error
            return {
                "success": False,
                "error": error or f"Failed to get unproved status for '{component_name}'",
                "project": project_name,
                "component": component_name,
                "raw_output": result.output,
            }

        status = parse_status(result.output)
        return {
            "success": True,
            "project": project_name,
            "component": component_name,
            # Only the groups that still carry unproved POs are listed by `us`.
            "unproved": _status_payload(status) if status else None,
            "raw_output": result.output,
        }

    result = await bbatch.unproved_global(project_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to get unproved status for '{project_name}'",
            "project": project_name,
            "raw_output": result.output,
        }

    statuses = parse_global_status(result.output)
    unproved = [s for s in statuses if s.unproved_po > 0]
    return {
        "success": True,
        "project": project_name,
        "components": [
            {
                "name": s.name,
                "total_po": s.total_po,
                "proved_po": s.proved_po,
                "unproved_po": s.unproved_po,
                "proof_percentage": s.proof_percentage,
            }
            for s in unproved
        ],
        "summary": {
            "components_with_unproved": len(unproved),
            "total_unproved": sum(s.unproved_po for s in unproved),
        },
        "raw_output": result.output,
    }


async def atelierb_infos_component(project_name: str, component_name: str) -> dict:
    """Get the metadata of a component: kind, source location, owner.

    Complements `atelierb_status`, which reports proof progress but not where
    the component lives or what it is.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.

    Returns:
        Dictionary with the component metadata and 'success' status.
    """
    result = await bbatch.infos_component(project_name, component_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to get information for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "raw_output": result.output,
        }

    info = parse_component_info(result.output)
    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "info": info,
        "raw_output": result.output,
    }


async def atelierb_proof_timeout() -> dict:
    """Read the configured timeout of the automatic prover, in seconds.

    Read-only by design. `to N` only holds for the bbatch session that issues
    it, and the server starts a fresh session for every command, so a setter
    exposed here would report success and change nothing at all. To actually
    bound a proof, pass `timeout_seconds` to `atelierb_prove`, which issues the
    setting in the same session as the proof.

    Returns:
        Dictionary with the timeout value and 'success' status. 0 means the
        prover runs without any time limit.
    """
    result = await bbatch.proof_timeout()

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or "Failed to read the proof timeout",
            "raw_output": result.output,
        }

    value = parse_timeout(result.output)
    return {
        "success": True,
        "timeout_seconds": value,
        "no_timeout": value == 0,
        "raw_output": result.output,
    }
