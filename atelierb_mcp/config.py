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

"""Configuration management for Atelier B MCP Server."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Atelier B MCP Server."""

    model_config = SettingsConfigDict(
        env_prefix="ATELIERB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Path to Atelier B installation directory
    path: Path = Field(
        default=Path("C:/Program Files/Atelier B Community Edition 24.04.2 24.04.2"),
        description="Path to Atelier B installation directory",
    )

    # Path to B projects workspace
    workspace: Path = Field(
        default=Path("C:/Work/B/WK25.02"),
        description="Path to B projects workspace",
    )

    # Command to launch bbatch (relative to ATELIERB_PATH/bin or absolute)
    bbatch_cmd: str = Field(
        default="bbatch.exe",
        description="bbatch executable name or full path",
    )

    # Timeout for bbatch commands in seconds
    command_timeout: float = Field(
        default=120.0,
        description="Timeout for bbatch commands in seconds",
    )

    @property
    def bbatch_path(self) -> Path:
        """Get the full path to bbatch executable."""
        if os.path.isabs(self.bbatch_cmd):
            return Path(self.bbatch_cmd)
        return self.path / "bin" / self.bbatch_cmd

    def validate_paths(self) -> list[str]:
        """Validate that required paths exist. Returns list of errors."""
        errors = []
        if not self.path.exists():
            errors.append(f"Atelier B installation not found at: {self.path}")
        if not self.bbatch_path.exists():
            errors.append(f"bbatch executable not found at: {self.bbatch_path}")
        if not self.workspace.exists():
            errors.append(f"Workspace directory not found at: {self.workspace}")
        return errors


# Global settings instance
settings = Settings()
