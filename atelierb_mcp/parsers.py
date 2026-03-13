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

"""Parsers for bbatch output."""

import re
from dataclasses import dataclass, field


@dataclass
class ProjectInfo:
    """Information about a B project."""

    name: str
    bdp_path: str | None = None
    lang_path: str | None = None
    project_type: str | None = None


@dataclass
class ComponentInfo:
    """Information about a B component."""

    name: str
    component_type: str  # MACHINE, REFINEMENT, IMPLEMENTATION
    status: str | None = None


@dataclass
class ComponentStatus:
    """Detailed status of a component."""

    name: str
    typecheck_ok: bool = False
    po_generated: bool = False
    total_po: int = 0
    proved_po: int = 0
    unproved_po: int = 0

    @property
    def proof_percentage(self) -> float:
        """Calculate proof percentage."""
        if self.total_po == 0:
            return 100.0
        return (self.proved_po / self.total_po) * 100


@dataclass
class ProofObligation:
    """A proof obligation."""

    name: str
    goal: str
    hypotheses: list[str] = field(default_factory=list)
    proved: bool = False


def parse_projects_list(output: str) -> list[str]:
    """Parse the output of show_projects_list (spl) command.

    Args:
        output: Raw bbatch output.

    Returns:
        List of project names.
    """
    projects = []
    in_list = False

    for line in output.splitlines():
        line = line.strip()

        if "Printing Project list" in line:
            in_list = True
            continue

        if "End of Project list" in line:
            break

        if in_list and line and not line.startswith("Beginning") and not line.startswith("End"):
            projects.append(line)

    return projects


def parse_components_list(output: str) -> list[ComponentInfo]:
    """Parse the output of show_machines_list (sml) command.

    Args:
        output: Raw bbatch output.

    Returns:
        List of ComponentInfo objects.
    """
    components = []
    in_list = False

    for line in output.splitlines():
        line = line.strip()

        # Start capturing after "Printing machine list"
        if "Printing machine list" in line:
            in_list = True
            continue

        # Stop at "End of machine list"
        if "End of machine list" in line:
            break

        # Capture component names within the list
        if in_list and line:
            # Determine type based on naming convention:
            # - *_i = IMPLEMENTATION
            # - *_r = REFINEMENT
            # - otherwise = MACHINE
            if line.endswith("_i"):
                comp_type = "IMPLEMENTATION"
            elif line.endswith("_r"):
                comp_type = "REFINEMENT"
            elif "_bs" in line or "_ctx" in line:
                comp_type = "MACHINE"  # Base or context machine
            else:
                comp_type = "MACHINE"

            components.append(ComponentInfo(name=line, component_type=comp_type))

    return components


def parse_status(output: str) -> ComponentStatus | None:
    """Parse the output of status (s) command.

    Args:
        output: Raw bbatch output.

    Returns:
        ComponentStatus object or None if parsing fails.
    """
    status = ComponentStatus(name="")

    # Look for component name
    name_match = re.search(r"Status of component\s+(\w+)", output, re.IGNORECASE)
    if name_match:
        status.name = name_match.group(1)

    # Look for typecheck status
    if re.search(r"typecheck.*ok|tc.*ok|checked", output, re.IGNORECASE):
        status.typecheck_ok = True

    # Look for PO counts
    # Common patterns: "X / Y proved", "X proved out of Y", etc.
    po_match = re.search(r"(\d+)\s*/\s*(\d+)", output)
    if po_match:
        status.proved_po = int(po_match.group(1))
        status.total_po = int(po_match.group(2))
        status.unproved_po = status.total_po - status.proved_po
        status.po_generated = True

    return status if status.name else None


def parse_global_status(output: str) -> list[ComponentStatus]:
    """Parse the output of status_global (sg) command.

    Args:
        output: Raw bbatch output.

    Returns:
        List of ComponentStatus objects.
    """
    statuses = []

    # Table format:
    # | COMPONENT           | TC | POG | nPO | nUn | %Pr | B0C |  Cc  | Rust | nRules | nLines |
    # | Airlock             | OK | OK  |   1 |   0 | 100 | OK  |      |      |      0 |     49 |
    # Pattern: | ComponentName | TC | POG | nPO | nUn | %Pr | ...
    pattern = re.compile(
        r"\|\s*(\w+)\s*\|\s*(OK|KO|--)\s*\|\s*(OK|KO|--)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    )

    for match in pattern.finditer(output):
        name = match.group(1)
        # Skip header and TOTAL rows
        if name in ("COMPONENT", "TOTAL"):
            continue

        tc_ok = match.group(2) == "OK"
        pog_ok = match.group(3) == "OK"
        total_po = int(match.group(4))
        unproved = int(match.group(5))
        proved = total_po - unproved

        status = ComponentStatus(
            name=name,
            typecheck_ok=tc_ok,
            po_generated=pog_ok,
            total_po=total_po,
            proved_po=proved,
            unproved_po=unproved,
        )
        statuses.append(status)

    return statuses


def parse_project_info(output: str) -> ProjectInfo | None:
    """Parse the output of infos_project (ip) command.

    Args:
        output: Raw bbatch output.

    Returns:
        ProjectInfo object or None if parsing fails.
    """
    info = ProjectInfo(name="")

    # Look for project name - format: "Name : ProjectName"
    name_match = re.search(r"Name\s*:\s*(\w+)", output, re.IGNORECASE)
    if name_match:
        info.name = name_match.group(1)

    # Look for database path - format: "Database path : C:\...\bdp"
    bdp_match = re.search(r"Database\s*path\s*:\s*(.+)", output, re.IGNORECASE)
    if bdp_match:
        info.bdp_path = bdp_match.group(1).strip()

    # Look for translation path - format: "Translation path : C:\...\lang"
    lang_match = re.search(r"Translation\s*path\s*:\s*(.+)", output, re.IGNORECASE)
    if lang_match:
        info.lang_path = lang_match.group(1).strip()

    # Look for project type
    type_match = re.search(r"type\s*:\s*(\w+)", output, re.IGNORECASE)
    if type_match:
        info.project_type = type_match.group(1)

    return info if info.name else None


def _parse_theories(content: str) -> list[tuple[str, str, str]]:
    """Parse a PMI/PMM file into a list of (header, body, separator) tuples.

    Each theory block has the form:
        THEORY Name [IS]
        entry1;
        entry2;
        ...
        entryN
        END

    Theories are separated by '&'.

    Returns:
        List of (header_line, body_text, trailing_separator) tuples.
        header_line includes 'THEORY Name IS' or 'THEORY Name'.
        body_text is everything between the header and END (may be empty).
        trailing_separator is '&' or '' for the last theory.
    """
    theories = []
    # Strip BOM if present
    content = content.lstrip('\ufeff')
    # Split on '&' separators between theories
    # The file format is: THEORY ... END & THEORY ... END & ...
    # We split on '&' that appears on its own line between END and THEORY
    blocks = re.split(r'\n&\s*\n', content)

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        # Extract header (THEORY line)
        header_match = re.match(
            r'(THEORY\s+\S+(?:\s+IS)?)\s*\n(.*?)\nEND\s*$', block, re.DOTALL
        )
        if header_match:
            header = header_match.group(1)
            body = header_match.group(2).strip()
            sep = '&' if i < len(blocks) - 1 else ''
            theories.append((header, body, sep))
        else:
            # Theory with no body (e.g., "THEORY EnumerateX\nEND")
            header_match2 = re.match(r'(THEORY\s+\S+)\s*\n?END\s*$', block, re.DOTALL)
            if header_match2:
                header = header_match2.group(1)
                sep = '&' if i < len(blocks) - 1 else ''
                theories.append((header, '', sep))

    return theories


def _reverse_theory_entries(body: str) -> str:
    """Reverse the semicolon-separated entries in a theory body.

    Entries are separated by ';' followed by a newline. The last entry
    has no trailing semicolon.
    """
    if not body.strip():
        return body

    # Split on ';' followed by newline (preserving entry content)
    entries = re.split(r';\s*\n', body)

    # The last entry doesn't have a trailing ';', but intermediate ones do
    # After split, each entry except the last had ';\\n' removed
    entries = [e.strip() for e in entries if e.strip()]

    if len(entries) <= 1:
        return body

    # Reverse the entries
    entries.reverse()

    # Reconstruct with ';' separators
    return ';\n'.join(entries)


def _reconstruct_theories(theories: list[tuple[str, str, str]]) -> str:
    """Reconstruct a PMI/PMM file from parsed theories."""
    parts = []
    for header, body, sep in theories:
        if body:
            parts.append(f'{header}\n{body}\nEND')
        else:
            parts.append(f'{header}\nEND')
        if sep:
            parts.append('&')

    return '\n'.join(parts) + '\n'


# Theories in PMI files whose entries need to be reversed to match bbatch ordering.
# BalanceX and Status contain group summaries (already in bbatch order).
# ProofState, MethodList, PassList contain per-PO entries in reverse order.
PMI_THEORIES_TO_REVERSE = {'ProofState', 'MethodList', 'PassList'}

# Theories in PMM files whose entries need to be reversed.
PMM_THEORIES_TO_REVERSE = {'User_Pass'}


def reorder_pmi_content(content: str) -> str:
    """Reorder PMI file content so per-PO entries match bbatch numbering.

    In PMI files, the BalanceX/Status theories list proof obligation groups
    in bbatch order (e.g., AssertionLemmas, Operation_algo, WellDefinedness_algo).
    However, the per-PO theories (ProofState, MethodList, PassList) store entries
    in REVERSE order. This function reverses those entries so that entry N
    corresponds to bbatch PO number N.

    Args:
        content: Raw PMI file content.

    Returns:
        Reordered PMI file content.
    """
    theories = _parse_theories(content)
    if not theories:
        return content

    reordered = []
    for header, body, sep in theories:
        # Extract theory name from header
        name_match = re.match(r'THEORY\s+(\S+)', header)
        theory_name = name_match.group(1) if name_match else ''

        if theory_name in PMI_THEORIES_TO_REVERSE and body:
            body = _reverse_theory_entries(body)

        reordered.append((header, body, sep))

    return _reconstruct_theories(reordered)


def reorder_pmm_content(content: str) -> str:
    """Reorder PMM file content so entries match bbatch numbering.

    In PMM files, the User_Pass theory stores proof method entries in
    reverse order compared to bbatch's PO numbering. This function
    reverses those entries.

    Args:
        content: Raw PMM file content.

    Returns:
        Reordered PMM file content.
    """
    theories = _parse_theories(content)
    if not theories:
        return content

    reordered = []
    for header, body, sep in theories:
        name_match = re.match(r'THEORY\s+(\S+)', header)
        theory_name = name_match.group(1) if name_match else ''

        if theory_name in PMM_THEORIES_TO_REVERSE and body:
            body = _reverse_theory_entries(body)

        reordered.append((header, body, sep))

    return _reconstruct_theories(reordered)


def extract_error_message(output: str) -> str | None:
    """Extract error message from bbatch output.

    Args:
        output: Raw bbatch output.

    Returns:
        Error message or None if no error found.
    """
    # Look for BBATCH error format first (more specific): "BBATCH (ERROR): message"
    bbatch_error = re.search(r"BBATCH\s*\(ERROR\)\s*:\s*(.+)", output)
    if bbatch_error:
        return bbatch_error.group(1).strip()

    # Look for generic ERROR patterns: "Error: message"
    error_match = re.search(r"(?:ERROR|Error|error)\s*:\s*(.+)", output)
    if error_match:
        return error_match.group(1).strip()

    return None
