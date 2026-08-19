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
    is_not_ng_project,
    parse_component_info,
    parse_global_status,
    parse_proof_mechanisms,
    parse_status,
    parse_timeout,
)

# The external-prover commands only run on a project migrated to NG mode. The
# bare bbatch message says nothing about the way out, so spell it here once.
_NG_HINT = (
    "This project is not in NG mode, which the external proof mechanisms require. "
    "Migrating it is done with the bbatch command `mip` and is IRREVERSIBLE: proof "
    "statuses move from .pmi to .pos files. Saved interactive proofs survive and can "
    "be replayed with atelierb_prove at force -2, but back up the project's bdp/ "
    "directory first. This server deliberately does not migrate projects on its own."
)


def _ng_guard(result, project_name: str, **extra) -> dict | None:
    """Return a helpful error payload when bbatch refused for lack of NG mode."""
    if not is_not_ng_project(result.output):
        return None
    return {
        "success": False,
        "error": f"Project '{project_name}' is not in NG mode.",
        "hint": _NG_HINT,
        "project": project_name,
        "raw_output": result.output,
        **extra,
    }


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


async def atelierb_list_proof_mechanisms(project_name: str | None = None) -> dict:
    """List the external proof mechanisms available.

    Without a project name, lists what Atelier B ships (`spm`). With one, lists
    what that project has enabled (`sppm`), which is the set atelierb_extprove
    will accept: a mechanism installed but not enabled on the project cannot be
    used there.

    Args:
        project_name: Project to inspect. Omit for the installation-wide list.

    Returns:
        Dictionary with the mechanism names and 'success' status.
    """
    if project_name is None:
        result = await bbatch.proof_mechanisms()
        scope = "installation"
    else:
        result = await bbatch.project_proof_mechanisms(project_name)
        scope = "project"
        refused = _ng_guard(result, project_name)
        if refused:
            return refused

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or "Failed to list proof mechanisms",
            "raw_output": result.output,
        }

    mechanisms = parse_proof_mechanisms(result.output)
    return {
        "success": True,
        "scope": scope,
        "project": project_name,
        "mechanisms": mechanisms,
        "count": len(mechanisms),
        "raw_output": result.output,
    }


async def atelierb_unprove(project_name: str, component_name: str) -> dict:
    """Discard the proof state of a component, sending every PO back to unproved.

    Destructive and not undoable from here. Interactive proof scripts saved with
    the interactive prover survive and can be replayed with atelierb_prove at
    force -2, but automatic verdicts are lost, and on an NG project this also
    clears the verdicts external mechanisms wrote in the .pos file. Take an
    archive first if the proof state matters.

    Args:
        project_name: Name of the project.
        component_name: Name of the component to unprove.

    Returns:
        Dictionary with the outcome and 'success' status.
    """
    result = await bbatch.unprove(project_name, component_name)

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"Failed to unprove '{component_name}'",
            "project": project_name,
            "component": component_name,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "raw_output": result.output,
    }


async def atelierb_extprove(
    project_name: str,
    component_name: str,
    mechanism: str,
    fast_only: bool = False,
) -> dict:
    """Submit a component's unproved POs to an external prover (SMT solver).

    Only proof obligations that are still unproved are submitted, so this is the
    natural follow-up to atelierb_prove rather than a replacement.

    Requires a project migrated to NG mode, with the mechanism enabled on it and
    its binary wired in the project resource file. Calling
    atelierb_list_proof_mechanisms with a project name reports what is usable there.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.
        mechanism: Mechanism name, validated against the project's enabled list.
        fast_only: Use only the mechanism's fast drivers rather than all of them.
            This selects drivers, not which proof obligations are submitted.

    Returns:
        Dictionary with the proof outcome and 'success' status.
    """
    # Validate against the project rather than against a list frozen in the
    # schema: what is usable depends on the installation and on the project.
    available = await atelierb_list_proof_mechanisms(project_name)
    if not available["success"]:
        return available

    if mechanism not in available["mechanisms"]:
        return {
            "success": False,
            "error": f"Mechanism '{mechanism}' is not enabled on project '{project_name}'.",
            "available_mechanisms": available["mechanisms"],
            "hint": (
                "Enable it on the project with the bbatch command `apm <mechanism>`, "
                "and check its binary is wired in the project's bdp/AtelierB resource "
                "file. atelierb_list_proof_mechanisms without a project name lists "
                "everything the installation ships."
            ),
            "project": project_name,
            "component": component_name,
        }

    result = await bbatch.extprove(project_name, component_name, mechanism, fast_only)

    refused = _ng_guard(result, project_name, component=component_name)
    if refused:
        return refused

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"External proof failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "mechanism": mechanism,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "mechanism": mechanism,
        "fast_only": fast_only,
        "raw_output": result.output,
    }


async def atelierb_extreplay(
    project_name: str, component_name: str, mechanism: str | None = None
) -> dict:
    """Replay the external proofs already recorded for a component.

    Re-runs the mechanisms on the proof obligations they discharged before,
    which is how an external verdict is checked again after the model changed.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.
        mechanism: Restrict the replay to one mechanism. Omit to replay all.

    Returns:
        Dictionary with the replay outcome and 'success' status.
    """
    result = await bbatch.extreplay(project_name, component_name, mechanism)

    refused = _ng_guard(result, project_name, component=component_name)
    if refused:
        return refused

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"External replay failed for '{component_name}'",
            "project": project_name,
            "component": component_name,
            "mechanism": mechanism,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "mechanism": mechanism,
        "raw_output": result.output,
    }


async def atelierb_counter_example(
    project_name: str,
    component_name: str,
    po: str,
    mechanism: str,
    driver: str,
) -> dict:
    """Ask an external mechanism for a counter-example on one proof obligation.

    When a proof obligation resists, a counter-example says why: it exhibits a
    valuation satisfying the hypotheses and falsifying the goal, which usually
    points straight at a missing invariant or guard.

    Requires an NG project with the mechanism enabled, as atelierb_extprove does.

    Args:
        project_name: Name of the project.
        component_name: Name of the component.
        po: The proof obligation, written Operation.index, for instance
            Operation_clear.5. Reading the component's .pmi through
            atelierb_read_file reports the labels.
        mechanism: Mechanism name, as reported by atelierb_list_proof_mechanisms.
        driver: Driver of that mechanism to run.

    Returns:
        Dictionary with the counter-example output and 'success' status.
    """
    result = await bbatch.counter_example(
        project_name, component_name, po, mechanism, driver
    )

    refused = _ng_guard(result, project_name, component=component_name, po=po)
    if refused:
        return refused

    if not result.success:
        error = extract_error_message(result.output) or result.error
        return {
            "success": False,
            "error": error or f"No counter-example obtained for '{po}'",
            "project": project_name,
            "component": component_name,
            "po": po,
            "mechanism": mechanism,
            "driver": driver,
            "raw_output": result.output,
        }

    return {
        "success": True,
        "project": project_name,
        "component": component_name,
        "po": po,
        "mechanism": mechanism,
        "driver": driver,
        "raw_output": result.output,
    }
