"""Proof-related MCP tools for Atelier B."""

from ..bbatch_wrapper import bbatch
from ..parsers import extract_error_message, parse_global_status, parse_status


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
    project_name: str, component_name: str, force: int = 0
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

    Returns:
        Dictionary with proof result and 'success' status.
    """
    result = await bbatch.prove(project_name, component_name, force)

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
            "status": {
                "typecheck_ok": status.typecheck_ok if status else None,
                "po_generated": status.po_generated if status else None,
                "total_po": status.total_po if status else 0,
                "proved_po": status.proved_po if status else 0,
                "unproved_po": status.unproved_po if status else 0,
                "proof_percentage": status.proof_percentage if status else None,
            } if status else None,
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
