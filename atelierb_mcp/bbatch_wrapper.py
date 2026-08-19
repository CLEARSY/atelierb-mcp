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

"""Subprocess wrapper for bbatch CLI communication."""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)


def _bbatch_env() -> dict[str, str]:
    """Environment for the bbatch subprocess, with HOME guaranteed.

    bbatch has Unix heritage and reads HOME to find its user settings. Without
    it, it does not fail: it answers wrongly. `xtm` reports `The project mode is
    not NG.` for a project that is in Compatible mode, and a caller has no way
    to tell that apart from a real answer.

    A client that starts this server with a trimmed environment gets exactly
    that, and the MCP SDK's own default environment is trimmed. So HOME is
    filled in from USERPROFILE when the parent process did not pass it.
    """
    env = dict(os.environ)
    if not env.get("HOME"):
        fallback = env.get("USERPROFILE") or str(Path.home())
        if fallback:
            env["HOME"] = fallback
    return env


@dataclass
class BbatchResult:
    """Result from a bbatch command execution."""

    success: bool
    output: str
    error: str | None = None
    command: str = ""


class BbatchWrapper:
    """Wrapper for communicating with bbatch CLI via subprocess."""

    def __init__(
        self,
        bbatch_path: Path | None = None,
        timeout: float | None = None,
    ):
        """Initialize the bbatch wrapper.

        Args:
            bbatch_path: Path to bbatch executable. Defaults to settings.
            timeout: Command timeout in seconds. Defaults to settings.
        """
        self.bbatch_path = bbatch_path or settings.bbatch_path
        self.timeout = timeout or settings.command_timeout
        self._process: asyncio.subprocess.Process | None = None

    async def execute(self, commands: str | list[str]) -> BbatchResult:
        """Execute one or more bbatch commands.

        Args:
            commands: Single command string or list of commands.

        Returns:
            BbatchResult with output and status.
        """
        if isinstance(commands, list):
            command_str = "\n".join(commands)
        else:
            command_str = commands

        # Ensure command ends with newline for bbatch to process it
        if not command_str.endswith("\n"):
            command_str += "\n"

        logger.debug(f"Executing bbatch commands: {command_str!r}")

        try:
            process = await asyncio.create_subprocess_exec(
                str(self.bbatch_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=_bbatch_env(),
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=command_str.encode("utf-8")),
                timeout=self.timeout,
            )

            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace") if stderr else None

            # Check for errors in output
            success = process.returncode == 0 and "ERROR" not in output.upper()

            return BbatchResult(
                success=success,
                output=output,
                error=error_output if error_output else None,
                command=command_str,
            )

        except asyncio.TimeoutError:
            logger.error(f"bbatch command timed out after {self.timeout}s")
            return BbatchResult(
                success=False,
                output="",
                error=f"Command timed out after {self.timeout} seconds",
                command=command_str,
            )
        except FileNotFoundError:
            logger.error(f"bbatch not found at {self.bbatch_path}")
            return BbatchResult(
                success=False,
                output="",
                error=f"bbatch executable not found at {self.bbatch_path}",
                command=command_str,
            )
        except Exception as e:
            logger.error(f"bbatch execution error: {e}")
            return BbatchResult(
                success=False,
                output="",
                error=str(e),
                command=command_str,
            )

    async def execute_with_project(
        self, project_name: str, commands: str | list[str]
    ) -> BbatchResult:
        """Execute commands within a project context.

        Args:
            project_name: Name of the project to open.
            commands: Commands to execute after opening project.

        Returns:
            BbatchResult with output and status.
        """
        if isinstance(commands, str):
            commands = [commands]

        full_commands = [f"op {project_name}"] + commands + ["clp"]
        return await self.execute(full_commands)

    async def list_projects(self) -> BbatchResult:
        """List all available projects."""
        return await self.execute("spl")

    async def get_version(self) -> BbatchResult:
        """Get bbatch version information."""
        return await self.execute("v")

    async def typecheck(self, project: str, component: str) -> BbatchResult:
        """Typecheck a component."""
        return await self.execute_with_project(project, f"t {component}")

    async def b0check(self, project: str, component: str) -> BbatchResult:
        """B0 check a component (verify B0 compliance for C code generation).

        Args:
            project: Name of the project.
            component: Name of the component to check (usually an implementation).

        Returns:
            BbatchResult with output and status.
        """
        return await self.execute_with_project(project, f"b0c {component}")

    async def pogenerate(
        self, project: str, component: str, differential: bool = False
    ) -> BbatchResult:
        """Generate proof obligations for a component."""
        option = "1" if differential else "0"
        return await self.execute_with_project(project, f"po {component} {option}")

    async def prove(
        self,
        project: str,
        component: str,
        force: int = 0,
        timeout: int | None = None,
    ) -> BbatchResult:
        """Run automatic prover on a component.

        Args:
            project: Project name.
            component: Component name.
            force: Proof force level (0-3 auto, 10-13 forced, -1 fast, -2 replay).
            timeout: Per-proof-obligation timeout in seconds, 0 for no limit.
                Issued as `to` in the same session, just before `pr`: the setting
                is session-scoped, so it has to travel with the proof itself.
        """
        commands = [] if timeout is None else [f"to {timeout}"]
        commands.append(f"pr {component} {force}")
        return await self.execute_with_project(project, commands)

    async def unproved_status(self, project: str, component: str) -> BbatchResult:
        """Status of a component, listing only the groups with unproved POs."""
        return await self.execute_with_project(project, f"us {component}")

    async def unproved_global(self, project: str) -> BbatchResult:
        """Status of every component of the project that still has unproved POs."""
        return await self.execute_with_project(project, "ug")

    async def metrics(self, project: str) -> BbatchResult:
        """Detailed proof metrics for a project (`xtm`).

        Project-wide: `xtm` answers `arg <name> not used` to a component name.
        """
        return await self.execute_with_project(project, "xtm")

    async def project_check(self, project: str, main_component: str) -> BbatchResult:
        """Run the Project Checker on the IMPORTS graph, from a main component."""
        return await self.execute_with_project(project, f"pchk {main_component}")

    async def archive(self, project: str, archive_path: str, scope: int) -> BbatchResult:
        """Archive a project to a tar file.

        `arc` refuses a project that is already open, unlike every other
        project-level command, so this one does not go through
        `execute_with_project`.
        """
        return await self.execute(f"arc {project} {archive_path} {scope}")

    async def restore(
        self, archive_path: str, project: str, project_path: str | None = None
    ) -> BbatchResult:
        """Restore a project from a tar archive. Also refuses an open project."""
        command = f"res {archive_path} {project}"
        if project_path:
            command += f" {project_path}"
        return await self.execute(command)

    async def make_all(
        self, project: str, action: str, force: int | None = None
    ) -> BbatchResult:
        """Run one action over every component of the project.

        `action` is a bbatch command abbreviation (`t`, `po`, `pr`), not a
        number: `m 0` answers `Unknown function name: 0`.
        """
        command = f"m {action}" if force is None else f"m {action} {force}"
        return await self.execute_with_project(project, command)

    async def remake(self, project: str, force: int | None = None) -> BbatchResult:
        """Bring the whole project up to date."""
        command = "r" if force is None else f"r {force}"
        return await self.execute_with_project(project, command)

    async def translate_to_rust(self, project: str, component: str) -> BbatchResult:
        """Generate Rust for an implementation and its dependencies."""
        return await self.execute_with_project(project, f"b2rust {component}")

    async def unprove(self, project: str, component: str) -> BbatchResult:
        """Discard the proof state of a component, sending every PO back to unproved."""
        return await self.execute_with_project(project, f"u {component}")

    async def proof_mechanisms(self) -> BbatchResult:
        """List the proof mechanisms installed with Atelier B (`spm`)."""
        return await self.execute("spm")

    async def project_proof_mechanisms(self, project: str) -> BbatchResult:
        """List the proof mechanisms enabled on a project (`sppm`, NG projects only)."""
        return await self.execute_with_project(project, "sppm")

    async def extprove(
        self, project: str, component: str, mechanism: str, fast_only: bool = False
    ) -> BbatchResult:
        """Submit the component's unproved POs to an external mechanism.

        The third argument of `xtp` selects the drivers, not the scope: 0 uses
        every driver of the mechanism, 1 only the fast ones. Either way only
        unproved proof obligations are submitted.
        """
        option = "1" if fast_only else "0"
        return await self.execute_with_project(
            project, f"xtp {component} {mechanism} {option}"
        )

    async def extreplay(
        self, project: str, component: str, mechanism: str | None = None
    ) -> BbatchResult:
        """Replay the external proofs already recorded for a component."""
        command = f"xtr {component}" if mechanism is None else f"xtr {component} {mechanism}"
        return await self.execute_with_project(project, command)

    async def counter_example(
        self, project: str, component: str, po: str, mechanism: str, driver: str
    ) -> BbatchResult:
        """Ask an external mechanism for a counter-example on one proof obligation."""
        return await self.execute_with_project(
            project, f"xce {component} {po} {mechanism} {driver}"
        )

    async def proof_timeout(self) -> BbatchResult:
        """Read the configured proof timeout (0 = no limit).

        General command, no open project needed. Read-only on purpose: `to N`
        only holds for the bbatch session that issues it, and this wrapper
        starts a fresh session per call, so a standalone setter would report
        success and change nothing. Pass `timeout` to `prove()` instead, which
        sets it in the same session as the proof.
        """
        return await self.execute("to")

    async def status(self, project: str, component: str) -> BbatchResult:
        """Get status of a component."""
        return await self.execute_with_project(project, f"s {component}")

    async def status_global(self, project: str) -> BbatchResult:
        """Get global status of all components in a project."""
        return await self.execute_with_project(project, "sg")

    async def list_components(self, project: str) -> BbatchResult:
        """List all components in a project."""
        return await self.execute_with_project(project, "sml")

    async def infos_project(self, project: str) -> BbatchResult:
        """Get information about a project."""
        return await self.execute(f"ip {project}")

    async def infos_component(self, project: str, component: str) -> BbatchResult:
        """Get information about a component."""
        return await self.execute_with_project(project, f"ic {component}")

    async def create_project(
        self,
        name: str,
        bdp_dir: str,
        lang_dir: str,
        project_type: str = "SYSTEM",
    ) -> BbatchResult:
        """Create a new Atelier B project.

        Args:
            name: Name of the project.
            bdp_dir: Path to the project database directory (bdp).
            lang_dir: Path to the translation directory (lang) for generated code.
            project_type: Project type (SYSTEM, SOFTWARE, or VALIDATION).

        Returns:
            BbatchResult with output and status.
        """
        return await self.execute(f'crp {name} "{bdp_dir}" "{lang_dir}" {project_type}')

    async def add_file(
        self,
        project: str,
        file_path: str,
        group_component: str | None = None,
    ) -> BbatchResult:
        """Add a file to a project.

        Args:
            project: Name of the project.
            file_path: Path to the file to add.
            group_component: Optional component to group with.

        Returns:
            BbatchResult with output and status.
        """
        if group_component:
            cmd = f'af -g {group_component} "{file_path}"'
        else:
            cmd = f'af "{file_path}"'
        return await self.execute_with_project(project, cmd)

    async def remove_component(self, project: str, component: str) -> BbatchResult:
        """Remove a component from a project.

        Args:
            project: Name of the project.
            component: Name of the component to remove.

        Returns:
            BbatchResult with output and status.
        """
        return await self.execute_with_project(project, f"rc {component}")

    async def remove_project(self, project: str) -> BbatchResult:
        """Remove a project from Atelier B database.

        Note: This only removes the project from Atelier B's database,
        it does not delete the project files from disk.

        Args:
            project: Name of the project to remove.

        Returns:
            BbatchResult with output and status.
        """
        return await self.execute(f"rp {project}")

    async def translate_to_c(
        self, project: str, component: str, profile: str = "C9X"
    ) -> BbatchResult:
        """Translate a component (implementation or basic machine) to C code.

        Args:
            project: Name of the project.
            component: Name of the component to translate.
            profile: C translation profile (C9X, LIGHT, or PROJECT).

        Returns:
            BbatchResult with output and status.
        """
        return await self.execute_with_project(project, f"b2c {component} {profile}")

    async def translate_project_to_c(
        self,
        project: str,
        toplevel: str,
        profile: str = "C9X",
        generate_main: bool = False,
    ) -> BbatchResult:
        """Translate a complete project to C code.

        Args:
            project: Name of the project.
            toplevel: Name of the toplevel component.
            profile: C translation profile (C9X, LIGHT, or PROJECT).
            generate_main: If True, generate a main() function.

        Returns:
            BbatchResult with output and status.
        """
        mode = "main" if generate_main else ""
        cmd = f"p2c {toplevel} {profile}"
        if mode:
            cmd += f" {mode}"
        return await self.execute_with_project(project, cmd)


# Global wrapper instance
bbatch = BbatchWrapper()
