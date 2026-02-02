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

"""Tests for bbatch wrapper."""

import pytest

from atelierb_mcp.bbatch_wrapper import BbatchResult, BbatchWrapper


class TestBbatchResult:
    """Tests for BbatchResult dataclass."""

    def test_success_result(self):
        """Test successful result."""
        result = BbatchResult(
            success=True,
            output="Operation completed",
            command="spl",
        )
        assert result.success is True
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = BbatchResult(
            success=False,
            output="",
            error="Command failed",
            command="invalid",
        )
        assert result.success is False
        assert result.error == "Command failed"


class TestBbatchWrapperIntegration:
    """Integration tests for BbatchWrapper (requires actual bbatch)."""

    @pytest.mark.integration
    async def test_list_projects(self):
        """Test listing projects with real bbatch."""
        wrapper = BbatchWrapper()
        result = await wrapper.list_projects()

        # This test requires actual bbatch installation
        assert result.output is not None
        assert "interpretation" in result.output.lower()

    @pytest.mark.integration
    async def test_get_version(self):
        """Test getting version with real bbatch."""
        wrapper = BbatchWrapper()
        result = await wrapper.get_version()

        assert result.output is not None
