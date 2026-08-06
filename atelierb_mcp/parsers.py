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


def _theory_entries(content: str, name: str) -> list[str]:
    """Return the ';'-separated entries of a THEORY block, in file order."""
    match = re.search(rf"THEORY\s+{name}\s+IS\s*\n(.+?)\nEND", content, re.DOTALL)
    if not match:
        return []
    return [e.strip() for e in match.group(1).strip().split(';') if e.strip()]


def parse_po_labels(po_content: str) -> list[str]:
    """Extract the ordered `Operation.index` labels from a .po file.

    The ProofList theory of a .po file holds one entry per proof obligation, in
    file order. Each entry ends with an explicit `Operation.index` conjunct just
    before the comma that introduces the formula, for example::

        _f(1) & _f(2) & _f(10) & Operation_clear.9,(_f(22) & ... => _f(42));

    This label is the only authoritative source for the (operation, index) pair
    of a proof obligation.

    Args:
        po_content: Raw text content of the .po file.

    Returns:
        One label per proof obligation, in file order. Empty if the ProofList
        theory is absent; entries whose label cannot be read yield an empty
        string so that positions stay aligned.
    """
    content = po_content.lstrip('﻿')  # some files carry a UTF-8 BOM
    match = re.search(r"THEORY\s+ProofList\s+IS\s*\n(.+?)\nEND", content, re.DOTALL)
    if not match:
        return []

    labels = []
    for entry in match.group(1).strip().split(';\n'):
        if not entry.strip():
            continue
        found = re.search(r"([A-Za-z_]\w*\.\d+)\s*,\s*\(", entry)
        labels.append(found.group(1) if found else '')

    return labels


def label_pmi_entries(pmi_content: str, po_content: str) -> list[dict] | None:
    """Pair each entry of a .pmi flat list with its proof obligation label.

    The ProofState, MethodList and PassList theories of a .pmi file are flat:
    one entry per proof obligation, but with nothing saying which (operation,
    index) an entry belongs to. That information lives in the sibling .po file,
    whose ProofList entries carry explicit labels and align 1:1 with the flat
    lists. Entry i of a flat list therefore describes the proof obligation named
    by label i.

    The order is NOT derivable from the .pmi header. It is neither the header
    order nor its reverse (measured across the 350 .pmi files of a workspace,
    a reversal rule reproduces the labels in only 75 % of cases), so the .po is
    the only reliable key.

    Args:
        pmi_content: Raw text content of the .pmi file.
        po_content: Raw text content of the sibling .po file.

    Returns:
        One dict per proof obligation with its file position, label, status and
        proof method. Empty for a component that has no proof obligation. None
        if the two files do not line up, in which case no guess is made.
    """
    labels = parse_po_labels(po_content)
    statuses = _theory_entries(pmi_content, 'ProofState')
    methods = _theory_entries(pmi_content, 'MethodList')
    if len(statuses) != len(labels):
        return None

    return [
        {
            'entry': i + 1,
            'po': labels[i],
            'status': statuses[i],
            'method': methods[i] if i < len(methods) else '?',
        }
        for i in range(len(labels))
    ]


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
