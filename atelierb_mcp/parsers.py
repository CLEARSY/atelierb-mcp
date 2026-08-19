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
class ProofGroup:
    """Per-group proof counters, one row of the `s` / `us` status table.

    A group is a proof-obligation family of the component, such as
    `AssertionLemmas`, `Initialisation` or `Operation_foo`.
    """

    name: str
    total_po: int = 0
    proved_interactively: int = 0
    proved_automatically: int = 0
    unproved_po: int = 0
    percentage: int = 0
    # NG projects report three more counters, absent in Compatible mode.
    proved_by_mechanism: int = 0
    unreliably_proved: int = 0
    disproved: int = 0

    @property
    def proved_po(self) -> int:
        """Proved by any route that counts as a proof."""
        return (
            self.proved_interactively
            + self.proved_automatically
            + self.proved_by_mechanism
        )


@dataclass
class ComponentStatus:
    """Detailed status of a component."""

    name: str
    typecheck_ok: bool = False
    po_generated: bool = False
    total_po: int = 0
    proved_po: int = 0
    unproved_po: int = 0
    proved_interactively: int = 0
    proved_automatically: int = 0
    proved_by_mechanism: int = 0
    unreliably_proved: int = 0
    disproved: int = 0
    groups: list["ProofGroup"] = field(default_factory=list)

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


# The status table does not always have the same columns. A Compatible-mode
# project prints
#     |                 | NbPO | NbPRi | NbPRa | NbUn | %Pr |
# while an NG project adds the external-mechanism counters
#     |       | NbPO | NbPRi | NbPRa | NbPRm | NbUnr | NbDis | NbUn | %Pr |
# so the columns are read from the header rather than counted by position.
# Reading NbUn positionally reports zero unproved on every NG project, which is
# exactly where the external provers are used.
_STATUS_HEADER = re.compile(r"\|\s*\|\s*NbPO\s*\|(.+?)\|\s*%Pr\s*\|")
_STATUS_FIELDS = {
    "NbPO": "total_po",
    "NbPRi": "proved_interactively",
    "NbPRa": "proved_automatically",
    "NbPRm": "proved_by_mechanism",
    "NbUnr": "unreliably_proved",
    "NbDis": "disproved",
    "NbUn": "unproved_po",
}


def _status_columns(output: str) -> list[str] | None:
    """Column names of the status table, read off its header row."""
    match = _STATUS_HEADER.search(output)
    if not match:
        return None
    middle = [c.strip() for c in match.group(1).split("|") if c.strip()]
    return ["NbPO", *middle, "%Pr"]


def _status_rows(output: str, columns: list[str]):
    """Yield (name, {column: value}) for each data row of the status table."""
    cells = r"\|\s*(\d+)\s*" * len(columns)
    row = re.compile(r"\|\s*(\S+)\s*" + cells + r"\|")
    for match in row.finditer(output):
        values = dict(zip(columns, (int(v) for v in match.groups()[1:])))
        yield match.group(1), values


def parse_status(output: str) -> ComponentStatus | None:
    """Parse the output of status (s) or unproved_status (us).

    Both commands print the same table, `us` listing only the groups that still
    have unproved proof obligations. The last row repeats the component name and
    carries the totals; the rows above it are the per-group counters.

    Args:
        output: Raw bbatch output.

    Returns:
        ComponentStatus object or None if parsing fails.
    """
    name_match = re.search(
        r"Printing the status of\s+(\S+)", output, re.IGNORECASE
    )
    if not name_match:
        return None
    name = name_match.group(1)

    status = ComponentStatus(name=name)

    # "probe POGenerated C:\...\probe.mch" states what has been done so far.
    if re.search(rf"^\s*{re.escape(name)}\s+POGenerated", output, re.IGNORECASE | re.MULTILINE):
        status.po_generated = True
        status.typecheck_ok = True  # POG only runs on a typechecked component
    elif re.search(rf"^\s*{re.escape(name)}\s+TypeChecked", output, re.IGNORECASE | re.MULTILINE):
        status.typecheck_ok = True

    columns = _status_columns(output)
    if columns is None:
        return status

    for row_name, values in _status_rows(output, columns):
        group = ProofGroup(name=row_name, percentage=values.get("%Pr", 0))
        for column, attribute in _STATUS_FIELDS.items():
            if column in values:
                setattr(group, attribute, values[column])

        if group.name == name:
            # The row repeating the component name carries the totals.
            for attribute in _STATUS_FIELDS.values():
                setattr(status, attribute, getattr(group, attribute))
            status.proved_po = group.proved_po
        else:
            status.groups.append(group)

    return status


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


def parse_proof_mechanisms(output: str) -> list[str]:
    """Extract the mechanism names listed by `spm` or `sppm`.

    Both print a header, one indented name per line, then a closing line::

        Available proof mechanisms...
              z3_pp
              z3_simple
        End of proof mechanisms

    Args:
        output: Raw bbatch output.

    Returns:
        The mechanism names, in the order listed. Empty when the project has
        none enabled, which is a legitimate answer rather than a failure.
    """
    mechanisms = []
    collecting = False
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "proof mechanisms" in stripped.lower():
            # "Available proof mechanisms..." opens, "End of ..." closes.
            collecting = not stripped.lower().startswith("end")
            continue
        if collecting:
            mechanisms.append(stripped)

    return mechanisms


def is_not_ng_project(output: str) -> bool:
    """Tell whether bbatch refused because the project is not in NG mode.

    The external-prover commands (`xtp`, `xtr`, `xce`) and the mechanism
    commands (`apm`, `sppm`) only work on a project migrated to NG mode, and
    answer `The project mode is not NG.` otherwise. That message is worth
    recognising: on its own it says nothing about what to do next.
    """
    return "project mode is not ng" in output.lower()


def parse_version(output: str) -> dict | None:
    """Parse the output of version_print (v).

    The command prints the edition and version on one line, then a long dump of
    the resource settings, one `NAME: value` pair per line. Those resources are
    the only readable place for several project-level facts, so they are kept
    rather than discarded.

    Args:
        output: Raw bbatch output.

    Returns:
        Dictionary with `version`, `edition` and the `resources` mapping, or
        None when the version line is absent.
    """
    match = re.search(
        r"ATELIER B(?:\s*\(([^)]+)\))?\s*version\s*(\S+?)\s*:", output, re.IGNORECASE
    )
    if not match:
        return None

    resources = {}
    for name, value in re.findall(r"^\s*(ATB\*[\w*]+)\s*:\s*(.*?)\s*$", output, re.MULTILINE):
        resources[name] = value

    compiler = re.search(r"B Compiler version\s+(\S+)", output)

    return {
        "edition": match.group(1) or "unknown",
        "version": match.group(2),
        "b_compiler": compiler.group(1) if compiler else None,
        "resources": resources,
    }


# The metrics table of `xtm`, one row per component plus a TOTAL row:
#   | Component | Po | Pr | Unr | Dis | Unp | Ext | ATB |
#   |     probe | 13 | 10 |   0 |   0 |   3 |   0 |  10 |
_METRICS_ROW = re.compile(
    r"\|\s*(\S+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    r"\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
)


def parse_metrics(output: str) -> dict:
    """Parse the output of extmetrics (xtm).

    Unlike the status commands, `xtm` is project-wide and ignores a component
    argument, answering `arg <name> not used`. Its columns split the proof
    results finer than `status` does: `Ext` counts what an external mechanism
    discharged and `ATB` what Atelier B's own prover did.

    Args:
        output: Raw bbatch output.

    Returns:
        Dictionary with a `components` list and the `total` row, both empty when
        no table is present.
    """
    components, total = [], None
    for row in _METRICS_ROW.finditer(output):
        entry = {
            "name": row.group(1),
            "total_po": int(row.group(2)),
            "proved": int(row.group(3)),
            "unreliably_proved": int(row.group(4)),
            "disproved": int(row.group(5)),
            "unproved": int(row.group(6)),
            "proved_externally": int(row.group(7)),
            "proved_by_atelierb": int(row.group(8)),
        }
        if entry["name"].upper() == "TOTAL":
            total = entry
        else:
            components.append(entry)

    return {"components": components, "total": total}


def parse_component_info(output: str) -> dict | None:
    """Parse the output of infos_component (ic).

    The command prints one `KEY --> value` pair per line::

        SPECIFICATION  --> probe
        LOCATION       --> C:\\Work\\B\\WK25.02\\WBProof_PmiProbe\\src/probe.mch
        OWNER          --> tl

    Keys vary with the component: a refinement or implementation adds its own
    lines, so the parser keeps whatever it finds rather than expecting a fixed
    set. Keys are lowercased so callers get stable field names.

    Args:
        output: Raw bbatch output.

    Returns:
        Dictionary of the pairs found, or None if the output has none.
    """
    info = {}
    for key, value in re.findall(r"^\s*([A-Z][A-Z_ ]*?)\s*-->\s*(.+?)\s*$", output, re.MULTILINE):
        info[key.strip().lower().replace(" ", "_")] = value.strip()

    return info or None


def parse_timeout(output: str) -> int | None:
    """Parse the output of timeout (to).

    Reads `Proof Timeout Value is 0 (no timeout)`, where the value is in
    seconds and 0 means no limit.

    Args:
        output: Raw bbatch output.

    Returns:
        The timeout in seconds, or None if the line is absent.
    """
    match = re.search(r"Proof\s+Timeout\s+Value\s+is\s+(\d+)", output, re.IGNORECASE)
    return int(match.group(1)) if match else None


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
    content = content.replace('\r\n', '\n')
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
    # Some files carry a UTF-8 BOM, and a Windows checkout yields CRLF.
    content = po_content.lstrip('﻿').replace('\r\n', '\n')
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
