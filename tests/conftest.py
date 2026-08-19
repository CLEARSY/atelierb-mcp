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

"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest

from atelierb_mcp.bbatch_wrapper import BbatchResult, BbatchWrapper
from atelierb_mcp.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return Settings(
        path="C:/Program Files/Atelier B Community Edition 24.04.2 24.04.2",
        workspace="C:/Work/B/WK25.02",
        bbatch_cmd="bbatch.exe",
    )


@pytest.fixture
def sample_projects_output():
    """Sample output from show_projects_list command."""
    return """Beginning interpretation ...

Printing Project list ...

      Airlock
      Algo_CC_arc
      P4
      test_FIN

End of Project list

End of interpretation (1 lines)"""


@pytest.fixture
def sample_components_output():
    """Sample output from show_machines_list command."""
    return """Beginning interpretation ...

Machine1
Machine2_r
Machine2_i
AbstractMachine

End of interpretation (1 lines)"""


@pytest.fixture
def sample_status_output():
    """Output of the status command, captured verbatim from bbatch.

    This used to be hand-written, inventing lines ("Status of component X",
    "Proof obligations : 5 / 10") that bbatch never prints. The parser was
    written against that invention and returned None on every real component,
    with its test staying green throughout. Read the real thing instead.
    """
    return (Path(__file__).parent / "fixtures" / "status_probe.txt").read_text(
        encoding="utf-8", errors="replace"
    )


@pytest.fixture
def sample_global_status_output():
    """Sample output from status_global command (table format)."""
    return """Beginning interpretation ...

Project status
+---------------------+----+-----+-----+-----+-----+-----+------+------+--------+--------+
| COMPONENT           | TC | POG | nPO | nUn | %Pr | B0C |  Cc  | Rust | nRules | nLines |
+---------------------+----+-----+-----+-----+-----+-----+------+------+--------+--------+
| Machine1            | OK | OK  |  10 |   5 |  50 | OK  |      |      |      0 |     49 |
| Machine2_r          | OK | OK  |   8 |   0 | 100 | OK  |  -   |  -   |      0 |     44 |
| Machine2_i          | OK | OK  |   5 |   2 |  60 | OK  |      |      |      0 |     15 |
+---------------------+----+-----+-----+-----+-----+-----+------+------+--------+--------+
| TOTAL               | OK | OK  |  23 |   7 |  70 | OK  |  -   | OK   |      0 |    108 |
+---------------------+----+-----+-----+-----+-----+-----+------+------+--------+--------+
End of interpretation (3 lines)"""


class MockBbatchWrapper(BbatchWrapper):
    """Mock bbatch wrapper for testing."""

    def __init__(self, responses: dict[str, str] | None = None):
        """Initialize with predefined responses."""
        self.responses = responses or {}
        self.commands_executed: list[str] = []

    async def execute(self, commands: str | list[str]) -> BbatchResult:
        """Return mocked response based on command."""
        if isinstance(commands, list):
            command_str = "\n".join(commands)
        else:
            command_str = commands

        self.commands_executed.append(command_str)

        # Find matching response
        for key, response in self.responses.items():
            if key in command_str:
                return BbatchResult(
                    success=True,
                    output=response,
                    command=command_str,
                )

        return BbatchResult(
            success=False,
            output="",
            error=f"No mock response for: {command_str}",
            command=command_str,
        )


@pytest.fixture
def mock_bbatch(
    sample_projects_output,
    sample_components_output,
    sample_status_output,
    sample_global_status_output,
):
    """Create a mock bbatch wrapper with sample responses."""
    return MockBbatchWrapper(
        responses={
            "spl": sample_projects_output,
            "sml": sample_components_output,
            "s ": sample_status_output,
            "sg": sample_global_status_output,
        }
    )
