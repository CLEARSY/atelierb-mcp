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

"""Tests for bbatch output parsers."""

import re
from pathlib import Path

import pytest

from atelierb_mcp.parsers import (
    extract_error_message,
    label_pmi_entries,
    parse_components_list,
    parse_global_status,
    parse_po_labels,
    parse_projects_list,
    parse_status,
)

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


class TestParseProjectsList:
    """Tests for parse_projects_list function."""

    def test_parse_projects_list(self, sample_projects_output):
        """Test parsing standard project list output."""
        projects = parse_projects_list(sample_projects_output)

        assert len(projects) == 4
        assert "Airlock" in projects
        assert "Algo_CC_arc" in projects
        assert "P4" in projects
        assert "test_FIN" in projects

    def test_parse_empty_projects_list(self):
        """Test parsing empty project list."""
        output = """Beginning interpretation ...

Printing Project list ...

End of Project list

End of interpretation (1 lines)"""

        projects = parse_projects_list(output)
        assert projects == []

    def test_parse_projects_with_noise(self):
        """Test parsing project list with extra content."""
        output = """Beginning interpretation ...

Printing Project list ...

      MyProject
      TestProject

End of Project list

End of interpretation (1 lines)"""

        projects = parse_projects_list(output)
        assert len(projects) == 2
        assert "MyProject" in projects


class TestParseGlobalStatus:
    """Tests for parse_global_status function."""

    def test_parse_global_status(self, sample_global_status_output):
        """Test parsing global status output (table format)."""
        statuses = parse_global_status(sample_global_status_output)

        assert len(statuses) == 3

        # Check Machine1: nPO=10, nUn=5, so proved=5
        m1 = next(s for s in statuses if s.name == "Machine1")
        assert m1.proved_po == 5
        assert m1.total_po == 10
        assert m1.unproved_po == 5
        assert m1.proof_percentage == 50.0

        # Check Machine2_r: nPO=8, nUn=0, so proved=8
        m2r = next(s for s in statuses if s.name == "Machine2_r")
        assert m2r.proved_po == 8
        assert m2r.total_po == 8
        assert m2r.unproved_po == 0
        assert m2r.proof_percentage == 100.0

        # Check Machine2_i: nPO=5, nUn=2, so proved=3
        m2i = next(s for s in statuses if s.name == "Machine2_i")
        assert m2i.proved_po == 3
        assert m2i.total_po == 5
        assert m2i.unproved_po == 2
        assert m2i.proof_percentage == 60.0


class TestParseStatus:
    """Tests for parse_status function."""

    def test_parse_status(self, sample_status_output):
        """Test parsing component status output."""
        status = parse_status(sample_status_output)

        assert status is not None
        assert status.name == "Machine1"
        assert status.typecheck_ok is True
        assert status.proved_po == 5
        assert status.total_po == 10
        assert status.proof_percentage == 50.0


class TestExtractErrorMessage:
    """Tests for extract_error_message function."""

    def test_extract_bbatch_error(self):
        """Test extracting BBATCH error."""
        output = "BBATCH (ERROR): unknown project 'foo'"
        error = extract_error_message(output)
        assert error == "unknown project 'foo'"

    def test_extract_generic_error(self):
        """Test extracting generic error."""
        output = "Error: component not found"
        error = extract_error_message(output)
        assert error == "component not found"

    def test_no_error(self):
        """Test when no error present."""
        output = "Operation completed successfully"
        error = extract_error_message(output)
        assert error is None


class TestPmiPoPairing:
    """Entry i of the .pmi flat lists describes the PO named by line i of the .po.

    Two specimens are used together on purpose. `probe` happens to be compatible
    with the old "reverse the flat list" rule; `sensor_store_i` is not. A fix
    validated on `probe` alone looks correct and is not.
    """

    def _labelled(self, component):
        entries = label_pmi_entries(
            read_fixture(f"{component}.pmi"), read_fixture(f"{component}.po")
        )
        assert entries is not None
        return {e["po"]: e for e in entries}

    def _header_groups(self, component):
        """BalanceX groups: name -> (total, provedInteractively, provedAutomatically).

        Field 3 is NOT the unproved count; unproved POs are the remainder.
        """
        text = read_fixture(f"{component}.pmi")
        body = re.search(r"THEORY\s+BalanceX\s+IS\s*\n(.+?)\nEND", text, re.DOTALL)
        groups = {}
        entries = [e.strip() for e in body.group(1).strip().split(";") if e.strip()]
        for entry in entries[1:]:  # entry 0 is the component total
            f = [x.strip() for x in entry.split(",")]
            groups[f[0]] = (int(f[1]), int(f[2]), int(f[4]))
        return groups

    def test_probe_markers_land_where_they_were_placed(self):
        """Markers ah(K = K) were saved on known POs; they must come back there."""
        by_po = self._labelled("probe")
        assert "ah(101 = 101)" in by_po["Initialisation.1"]["method"]
        assert "ah(202 = 202)" in by_po["Operation_bump.2"]["method"]
        assert "ah(303 = 303)" in by_po["WellDefinednessAssertions.3"]["method"]

    def test_probe_unproved_are_the_assertion_lemmas(self):
        by_po = self._labelled("probe")
        unproved = {po for po, e in by_po.items() if e["status"] == "Unproved"}
        assert unproved == {
            "AssertionLemmas.1",
            "AssertionLemmas.2",
            "AssertionLemmas.3",
        }

    def test_sensor_store_interactive_proofs_land_on_the_right_operations(self):
        """This is the case the reversal rule gets wrong."""
        by_po = self._labelled("sensor_store_i")
        interactive = {po for po, e in by_po.items() if e["status"] == "Proved(Util)"}
        assert interactive == {
            "Operation_query.1",
            "Operation_set_one.3",
            "Operation_set_one.4",
        }

    def test_sensor_store_unproved_all_belong_to_operation_clear(self):
        by_po = self._labelled("sensor_store_i")
        unproved = {po for po, e in by_po.items() if e["status"] == "Unproved"}
        assert unproved == {
            "Operation_clear.5",
            "Operation_clear.8",
            "Operation_clear.9",
        }

    def test_reversal_rule_is_not_a_general_rule(self):
        """Reversing the flat list matches the .po on probe and fails elsewhere.

        Kept as an executable record of why the earlier fix looked right: the
        rule holds on the small specimen and breaks on a real component.
        """
        for component, holds in [("probe", True), ("sensor_store_i", False)]:
            enumerated = [
                f"{name}.{i}"
                for name, (total, _, _) in self._header_groups(component).items()
                for i in range(1, total + 1)
            ]
            actual = parse_po_labels(read_fixture(f"{component}.po"))
            assert (list(reversed(enumerated)) == actual) is holds

    def test_header_counts_agree_with_the_pairing(self):
        """Decoding field 3 as unproved would invert these assertions."""
        for component in ("probe", "sensor_store_i"):
            observed = {}
            for entry in label_pmi_entries(
                read_fixture(f"{component}.pmi"), read_fixture(f"{component}.po")
            ):
                name = entry["po"].rpartition(".")[0]
                counts = observed.setdefault(name, [0, 0, 0])
                counts[0] += 1
                if entry["status"].startswith("Proved(Util"):
                    counts[1] += 1
                elif entry["status"].startswith("Proved"):
                    counts[2] += 1
            for name, expected in self._header_groups(component).items():
                assert tuple(observed[name]) == expected, f"{component}/{name}"

    def test_sensor_store_operation_clear_has_three_unproved(self):
        """Explicit regression on the numbers bbatch reports for this component."""
        groups = self._header_groups("sensor_store_i")
        total, interactive, automatic = groups["Operation_clear"]
        assert (total, interactive, automatic) == (9, 0, 6)
        assert total - interactive - automatic == 3

    def test_po_labels_follow_file_order(self):
        labels = parse_po_labels(read_fixture("probe.po"))
        assert labels[0] == "WellDefinednessAssertions.3"
        assert labels[-1] == "AssertionLemmas.1"
        assert len(labels) == 13

    def test_mismatched_files_are_not_guessed(self):
        """A .po that does not line up yields no labels rather than a wrong pairing."""
        assert (
            label_pmi_entries(
                read_fixture("sensor_store_i.pmi"), read_fixture("probe.po")
            )
            is None
        )

    def test_missing_prooflist_yields_no_labels(self):
        assert parse_po_labels("THEORY Formulas IS\nx;\ny\nEND\n") == []

    def test_crlf_content_is_handled(self):
        """A Windows checkout hands these files over with CRLF line endings."""
        pmi = read_fixture("sensor_store_i.pmi").replace("\n", "\r\n")
        po = read_fixture("sensor_store_i.po").replace("\n", "\r\n")
        entries = label_pmi_entries(pmi, po)
        assert entries is not None
        assert len(entries) == 28
        assert entries[19]["po"] == "Operation_query.1"

    def test_component_without_proof_obligations_pairs_empty(self):
        """A component with no PO has both theories empty; that is aligned, not broken."""
        pmi = (
            "THEORY BalanceX IS\nAirlock_i,0,0,0,0,0,0,0\nEND\n&\n"
            "THEORY ProofState\nEND\n&\nTHEORY MethodList\nEND\n"
        )
        po = "THEORY ProofList\nEND\n&\nTHEORY Formulas\nEND\n"
        assert label_pmi_entries(pmi, po) == []
