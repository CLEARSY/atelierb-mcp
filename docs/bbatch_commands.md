# bbatch Commands Reference

This document provides a complete reference of all bbatch CLI commands for Atelier B.

## Usage

bbatch is an interactive CLI. Commands are sent via stdin:

```bash
echo "command" | bbatch.exe
echo -e "cmd1\ncmd2" | bbatch.exe  # Multiple commands
```

## General Commands

| Abbrev | Command | Description |
|--------|---------|-------------|
| `cd` | `change_directory` | `change_directory <path>` - Change current directory |
| `ddm` | `disable_dependence_mode` | Disable dependence mode |
| `erf` | `edit_res_file` | `edit_res_file <resource_file>` - Edit a resource file |
| `eur` | `edit_users_res` | Edit user file resources `$HOME/.AtelierB` |
| `edm` | `enable_dependence_mode` | Enable dependence mode |
| `h` | `help` | `help [command]` - Get help on commands |
| `hh` | `html_help` | `html_help <helpfile>` - Edit a help file with HTML viewer (files in `AB/bin/help`) |
| `hph` | `html_prover_help` | Edit the Interactive Prover help file with HTML viewer |
| `hrb` | `html_rules_base` | Edit the Rule Base file with HTML viewer |
| `lsb` | `list_sources_b` | List names of B source files in current directory |
| `lrf` | `load_res_file` | `load_res_file <resource_file>` - Load a resource file |
| `pc` | `print_code` | `print_code <tool> <type> NORM/PLAIN` - Print decoded/coded messages |
| `pwd` | `print_working_directory` | Print the name of the current directory |
| `q` | `quit` | Exit bbatch |
| `rs` | `restore_source` | `restore_source <path_tar> <project> <component>` - Restore a component |
| `spm` | `show_proof_mechanisms` | List installed proof mechanisms |
| `srb` | `show_rules_base` | Edit the rules base file |
| `v` | `version_print` | Print version information |

## Project Level Commands

| Abbrev | Command | Description |
|--------|---------|-------------|
| `add` | `add_definitions_directory` | `add_definitions_directory <project> <fullpath>` - Add a definition directory |
| `apl` | `add_project_lib` | `add_project_lib <project> <lib>` - Add a library to a project |
| `apr` | `add_project_reader` | `add_project_reader <project> <reader>` - Add a reader to a project |
| `apu` | `add_project_user` | `add_project_user <project> <user>` - Add a user to a project |
| `apm` | `add_proof_mechanism` | `add_proof_mechanism <mechanism>` - Add proof mechanism for current project |
| `arc` | `archive` | `archive <project> <path_tar> <whole>` - Archive a project. `whole`: 0=source only, 1=all, 2=source+proof |
| `crp` | `create_project` | `create_project <name> <pdb_dir> <lang_dir> [type]` - Create project. Type: SYSTEM, SOFTWARE, VALIDATION |
| `crpm` | `create_project_manifest` | `create_project_manifest <name> <pdb_dir> <lang_dir> <type> <manifest>` - Create project from manifest |
| `epr` | `edit_project_res` | Edit project file resources `<bdp>/.AtelierB` |
| `xtm` | `extmetrics` | Print detailed proof metrics |
| `glfa` | `get_list_from_archive` | `get_list_from_archive <path_archive>` - Display list of B sources in archive |
| `gchk` | `global_project_check` | `global_project_check [-v] [-D]` - Run project check. `-v`: verbose, `-D`: disable verifications |
| `ip` | `infos_project` | `infos_project <name>` - Show information about the project |
| `mip` | `migrate_project` | `migrate_project <project>` - Migrate project from Compatible to NG mode |
| `op` | `open_project` | `open_project <name>` - Open a project (required for machine-level commands) |
| `rde` | `remote_delta3` | `remote_delta3 <dir> <name>` - Remote generate WD proof obligations |
| `rpo` | `remote_pogenerate` | `remote_pogenerate <dir> <name> <diff> <eventB>` - Remote generate proof obligations |
| `rpr` | `remote_prove` | `remote_prove <dir> <name> <force> <pmi_ext> <delta>` - Remote prove a component |
| `rdd` | `remove_definitions_directory` | `remove_definitions_directory <project> <fullpath>` - Remove a definition directory |
| `rp` | `remove_project` | `remove_project <name>` - Remove a project from Atelier B database |
| `rpl` | `remove_project_lib` | `remove_project_lib <project> <lib>` - Remove a library from a project |
| `rpu` | `remove_project_user` | `remove_project_user <project> <user>` - Remove a user from a project |
| `rpm` | `remove_proof_mechanism` | `remove_proof_mechanism <mechanism>` - Remove proof mechanism from current project |
| `res` | `restore` | `restore <path_tar> <project> [path_project] [path_src]` - Restore a project from archive |
| `sddl` | `show_definitions_directory_list` | `show_definitions_directory_list <project>` - Show definition directories |
| `sll` | `show_libs_list` | `show_libs_list <name>` - Show list of possible libraries |
| `spll` | `show_project_libs_list` | `show_project_libs_list <name>` - Show project libraries |
| `sppm` | `show_project_proof_mechanisms` | List proof mechanisms authorized in current project |
| `sprl` | `show_project_readers_list` | `show_project_readers_list <name>` - Show authorized readers |
| `spul` | `show_project_users_list` | `show_project_users_list <name>` - List authorized users |
| `spl` | `show_projects_list` | Show names of projects visible to current user |

## Machine Level Commands

These commands require `open_project` to be called first.

### Typechecking & Verification

| Abbrev | Command | Description |
|--------|---------|-------------|
| `t` | `typecheck` | `typecheck <name>` - Type check a component |
| `b0c` | `b0check` | `b0check <name>` - B0 check a component |
| `pchk` | `project_check` | `project_check <name>` - Run Project Checker on IMPORTS graph |
| `gchk` | `global_project_check` | `global_project_check [-v] [-D]` - Run project check on current project |

### Proof Generation & Proving

| Abbrev | Command | Description |
|--------|---------|-------------|
| `po` | `pogenerate` | `pogenerate <name> [option]` - Generate Proof Obligations. Option: 0=full, 1=differential |
| `pr` | `prove` | `prove <name> <force>` - Call automatic prover. Force: 0-3 (auto), 10-13 (forced), -1 (fast), -2 (replay), -3 to -7 (user modes) |
| `xtp` | `extprove` | `extprove <component> <mechanism> [option]` - Apply external proof mechanism. Option: 0=all, 1=fast only |
| `xtr` | `extreplay` | `extreplay <component> [mechanism]` - Replay external proof mechanism |
| `xce` | `extcounter_example` | `extcounter_example <component> <po> <mechanism> <driver>` - Show counter example |
| `vr` | `verify_rule` | `verify_rule <component> <rule> [suffix]` - Verify a rule in component PMM |
| `u` | `unprove` | `unprove <name> [suffix]` - Unprove all PO of a component |
| `to` | `timeout` | `timeout [sec]` - Get/set proof timeout (0=no timeout) |
| `co` | `concurrency` | `concurrency [N]` - Get/set external proof concurrency threads |

### Status & Information

| Abbrev | Command | Description |
|--------|---------|-------------|
| `s` | `status` | `status <name>` - Get status of a component |
| `sg` | `status_global` | `status_global [suffix]` - Print status of every component (suffix for WD lemmas) |
| `us` | `unproved_status` | `unproved_status <name>` - Get status filtering proved lemmas |
| `ug` | `unproved_global` | Print status of every unproved component |
| `ic` | `infos_component` | `infos_component <name>` - Print information about a component |
| `sml` | `show_machines_list` | `show_machines_list [own] [mach] [ref] [impl] [name]` - List components. Filters available |
| `ps` | `project_status` | `project_status [file] [type] [Lib] [Nav] [links] [Hide] [GIP]` - Print project graph with options |

### Code Generation

| Abbrev | Command | Description |
|--------|---------|-------------|
| `b2c` | `ComenCtrans` | `ComenCtrans <name> [profile]` - Translate implementation to C. Profile: C9X, LIGHT, PROJECT |
| `b2c_old` | `ComenCOldtrans` | `ComenCOldtrans <name>` - Translate implementation to C (old) |
| `p2c` | `ComenCtransall` | `ComenCtransall <name> <profile> [mode]` - Translate project to C. `mode=main` for main function |
| `b2rust` | `Rusttrans` | `Rusttrans <impl>` - Generate Rust for implementation and dependencies |
| `dge` | `data_generation` | `data_generation <name>` - Data generation with ProB |

### Component Management

| Abbrev | Command | Description |
|--------|---------|-------------|
| `af` | `add_file` | `add_file [-g <component>] <file1> ... <file7>` - Add files to project |
| `rc` | `remove_component` | `remove_component <comp1> ... <comp7>` - Remove components from project |
| `rg` | `remove_generated_files` | `remove_generated_files <tag>` - Remove files generated with given tag |
| `clp` | `close_project` | Close the previously opened project |
| `e` | `edit` | `edit <name>` - Edit component in text editor |
| `ep` | `edit_pmm` | `edit_pmm <name>` - Edit component's PMM file |
| `sn` | `set_native` | `set_native <int>` - Set project native (0) or heterogeneous (1) |

### Documentation

| Abbrev | Command | Description |
|--------|---------|-------------|
| `sdl` | `show_doc_latex` | `show_doc_latex <name> <type> [pdf]` - Generate LaTeX/PDF doc. Type: PLAIN, NORM |
| `pdl` | `print_doc_latex` | `print_doc_latex <name> <type>` - Generate and print LaTeX doc |
| `cdf` | `create_doc_framemaker` | `create_doc_framemaker <name> <type>` - Generate FrameMaker doc |
| `cdi` | `create_doc_ileaf` | `create_doc_ileaf <name> <type>` - Generate INTERLEAF doc |
| `cdr` | `create_doc_rtf` | `create_doc_rtf <name> <type>` - Generate RTF doc |
| `pdi` | `print_doc_ileaf` | `print_doc_ileaf <name> <type>` - Print INTERLEAF doc |
| `spp` | `set_print_params` | `set_print_params <printer> <mode> <first> <last>` - Set print parameters |

### Graphs & Analysis

| Abbrev | Command | Description |
|--------|---------|-------------|
| `dg` | `dep_graph` | `dep_graph <name>` - Show dependence graph of component |
| `fg` | `formula_graph` | `formula_graph <name> [clause] [fold_level/depth]` - Generate formula graph |
| `hg` | `homonymy_graph` | `homonymy_graph <name> [ident] [module_mode]` - Generate homonymy graph |
| `ocg` | `op_call_graph` | `op_call_graph <name> [op] [module_mode]` - Generate operation call graph |
| `gpx` | `get_project_xref` | `get_project_xref <mode> [id/comp]` - Get cross references. Mode: 0=component, 1=identifier, 2=all |
| `svf` | `show_vcg_file` | `show_vcg_file <vcg>` - Run VCG with file from project pdb |

### Browsing & Proofs

| Abbrev | Command | Description |
|--------|---------|-------------|
| `b` | `browse` | `browse <name> [obvious] [delta]` - Run browser session. obvious: 0/1, delta: `_wd` for WD lemmas |
| `bart` | `bart` | `bart <component>` - Use BART to automatically refine component |

### Batch Operations

| Abbrev | Command | Description |
|--------|---------|-------------|
| `m` | `make_all` | `make_all <action> [force] [prove_force]` - Run action on all components |
| `r` | `remake` | `remake [force]` - Remake all for the project |

## Prove Force Values

The `prove` command accepts these force values:

| Value | Mode |
|-------|------|
| 0, 1, 2, 3 | Automatic forces (increasing strength) |
| 10, 11, 12, 13 | Same as 0-3 but proof is forced |
| -1 | Fast |
| -2 | Replay |
| -3 | User |
| -4 | User without filters |
| -5 | User without Pattern filter |
| -6 | User without Operation filter |
| -7 | User with stop on failed command |

## Common Workflows

### Typecheck and Prove a Component

```bash
echo -e "op MyProject\nt MyComponent\npo MyComponent\npr MyComponent 0" | bbatch.exe
```

### Get Project Status

```bash
echo -e "op MyProject\nsg" | bbatch.exe
```

### List All Components

```bash
echo -e "op MyProject\nsml" | bbatch.exe
```
