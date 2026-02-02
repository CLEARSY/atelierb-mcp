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

import pytest

from atelierb_mcp.parsers import (
    extract_error_message,
    parse_components_list,
    parse_global_status,
    parse_projects_list,
    parse_status,
)


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
