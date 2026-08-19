<!--
Copyright (C) 2026 CLEARSY (https://www.clearsy.com)
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# bbatch coverage in the MCP server

Audit date: **2026-05-25**. Cross-reference between the canonical bbatch
CLI command list in [`bbatch_commands.md`](bbatch_commands.md) and the MCP
tools registered in `atelierb_mcp/server.py`.

## Edition target

The MCP server primarily targets **Atelier B Community Edition**, since
most development on top of this server happens against the public CE
distribution. Commands that exist in `bbatch` but are **Pro-only** are
marked `[Pro]` in the tables below and listed separately at the bottom of
the priority section. They are not candidates for Phase 1 / Phase 2
implementation work as long as the server's target is CE.

**Known Pro-only commands** (confirmed by the maintainer):

- `vr` / `verify_rule`: mechanical rule verification.

If you spot another Pro-only command not yet flagged, edit the table
below: change `Status` to `PRO-ONLY` and add a reference here. The
priority lists below assume CE; rebalance only if the server's target
changes.

## Summary

| | Count |
|---|---|
| **bbatch commands documented** | 81 |
| **MCP tools registered** | 21 |
| **bbatch commands exposed** as their own MCP tool | 18 |
| bbatch commands handled **internally** by the wrapper (not their own tool) | 2 (`op`, `clp`) |
| MCP tools that don't wrap a bbatch command (filesystem helpers) | 4 |
| bbatch commands **out of scope** (interactive editor / legacy format / printer / subprocess lifecycle) | 22 |
| bbatch commands **Pro-only** (not in Community Edition; out of scope while server targets CE) | 1+ (confirmed: `vr`; others TBC) |
| bbatch commands **not exposed** but in scope on CE (the actual gap to close) | **38** |

**Coverage of in-scope CE bbatch commands**: 18 / (18 + 38) = **32.1 %**.

Trends:

- Project lifecycle (create / open / close / remove / list / info): well covered.
- Component management (add / remove / typecheck / B0 check): well covered.
- Proof core (PO generate / auto-prove / status): well covered.
- Code generation: C is covered (b2c, p2c); **Rust (b2rust) is not**.
- Proof analytics (unproved-only filters, counter-examples, external mechanisms, rule verification, metrics): **almost entirely uncovered**.
- Graphs / cross-references / dependence: **uncovered**.
- Archive / restore / batch operations: **uncovered**.

## Status legend

- **EXPOSED**: a dedicated MCP tool wraps this bbatch command.
- **INTERNAL**: the wrapper uses this command behind the scenes; no dedicated tool surface is needed.
- **NOT EXPOSED**: in scope, but no MCP tool reaches this functionality. Candidate for a future tool.
- **OUT OF SCOPE**: interactive editor, legacy doc format, printer setup, or subprocess lifecycle that does not translate to the MCP request/response shape. Will not be exposed.
- **PRO-ONLY**: bbatch command exists only in Atelier B Pro, not in Community Edition. Will not be exposed as long as the server targets CE.

## A. General Commands (18)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| cd | change_directory | OUT OF SCOPE | filesystem nav done via MCP file tools |
| ddm | disable_dependence_mode | NOT EXPOSED | wrapper-level setting candidate |
| edm | enable_dependence_mode | NOT EXPOSED | wrapper-level setting candidate |
| erf | edit_res_file | OUT OF SCOPE | interactive editor |
| eur | edit_users_res | OUT OF SCOPE | interactive editor |
| h | help | OUT OF SCOPE | duplicated by MCP tool docstrings |
| hh | html_help | OUT OF SCOPE | interactive HTML viewer |
| hph | html_prover_help | OUT OF SCOPE | interactive HTML viewer |
| hrb | html_rules_base | OUT OF SCOPE | interactive HTML viewer |
| lsb | list_sources_b | NOT EXPOSED | partial overlap with `atelierb_list_files`; a bbatch-native variant could be added if filesystem helper drifts |
| lrf | load_res_file | NOT EXPOSED | wrapper-level setting candidate |
| pc | print_code | NOT EXPOSED | low priority |
| pwd | print_working_directory | OUT OF SCOPE | filesystem nav |
| q | quit | OUT OF SCOPE | subprocess lifecycle handled by wrapper |
| rs | restore_source | NOT EXPOSED | component-level restore from archive |
| spm | show_proof_mechanisms | NOT EXPOSED | useful for listing what's available before `xtp` |
| srb | show_rules_base | OUT OF SCOPE | interactive editor |
| v | version_print | NOT EXPOSED | quick win; useful for server diagnostics |

## B. Project Level Commands (31)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| add | add_definitions_directory | NOT EXPOSED | library / definitions management |
| apl | add_project_lib | NOT EXPOSED | library management |
| apm | add_proof_mechanism | NOT EXPOSED | configure provers per project |
| apr | add_project_reader | NOT EXPOSED | access control; low priority for MCP |
| apu | add_project_user | NOT EXPOSED | access control; low priority for MCP |
| arc | archive | NOT EXPOSED | **high-value**: snapshot before risky proofs |
| crp | create_project | EXPOSED | `atelierb_create_project` |
| crpm | create_project_manifest | NOT EXPOSED | manifest-driven project creation |
| epr | edit_project_res | OUT OF SCOPE | interactive editor |
| xtm | extmetrics | NOT EXPOSED | proof metrics; useful for status dashboards |
| glfa | get_list_from_archive | NOT EXPOSED | inspect archive before restore |
| gchk | global_project_check | NOT EXPOSED | **high-value**: full-project pre-flight |
| ip | infos_project | EXPOSED | `atelierb_infos_project` |
| mip | migrate_project | NOT EXPOSED | one-off Compatible → NG migration |
| op | open_project | INTERNAL | wrapper opens projects for each command |
| rde | remote_delta3 | NOT EXPOSED | remote variant; defer until remote workflow exists |
| rpo | remote_pogenerate | NOT EXPOSED | remote variant |
| rpr | remote_prove | NOT EXPOSED | remote variant |
| rdd | remove_definitions_directory | NOT EXPOSED | library management |
| rp | remove_project | EXPOSED | `atelierb_remove_project` |
| rpl | remove_project_lib | NOT EXPOSED | library management |
| rpm | remove_proof_mechanism | NOT EXPOSED | per-project prover unconfig |
| rpu | remove_project_user | NOT EXPOSED | access control |
| res | restore | NOT EXPOSED | **high-value**: paired with `arc` for checkpoint/restore |
| sddl | show_definitions_directory_list | NOT EXPOSED | library management |
| sll | show_libs_list | NOT EXPOSED | library catalogue |
| spll | show_project_libs_list | NOT EXPOSED | library catalogue |
| sppm | show_project_proof_mechanisms | NOT EXPOSED | useful before `xtp` |
| sprl | show_project_readers_list | NOT EXPOSED | access control |
| spul | show_project_users_list | NOT EXPOSED | access control |
| spl | show_projects_list | EXPOSED | `atelierb_list_projects` |

## C. Machine Level: Typechecking & Verification (4)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| t | typecheck | EXPOSED | `atelierb_typecheck` |
| b0c | b0check | EXPOSED | `atelierb_b0check` |
| pchk | project_check | NOT EXPOSED | **high-value**: IMPORTS-graph integrity check |
| gchk | global_project_check | NOT EXPOSED | (duplicated under "General", same command) |

## D. Machine Level: Proof Generation & Proving (9)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| po | pogenerate | EXPOSED | `atelierb_pogenerate` |
| pr | prove | EXPOSED | `atelierb_prove` |
| xtp | extprove | NOT EXPOSED | **high-value**: external mechanisms (mlSMT, mlproof, ...) |
| xtr | extreplay | NOT EXPOSED | replay external proof; paired with `xtp` |
| xce | extcounter_example | NOT EXPOSED | **highest-value**: counter-example for failed PO |
| vr | verify_rule | PRO-ONLY | mechanical rule verification; **not in Community Edition**; out of scope while server targets CE |
| u | unprove | NOT EXPOSED | **high-value**: reset to redo proofs |
| to | timeout | `atelierb_proof_timeout` (read) + `timeout_seconds` on `atelierb_prove` | read-only as a tool: `to N` is scoped to one bbatch session, so setting it standalone changes nothing |
| co | concurrency | NOT EXPOSED | set proof concurrency threads |

## E. Machine Level: Status & Information (7)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| s | status | EXPOSED | `atelierb_status` (with component name) |
| sg | status_global | EXPOSED | `atelierb_status` (without component name) |
| us | unproved_status | `atelierb_unproved_status` | with a component name |
| ug | unproved_global | `atelierb_unproved_status` | without a component name |
| ic | infos_component | `atelierb_infos_component` | kind, source location, owner |
| sml | show_machines_list | EXPOSED | `atelierb_list_components` |
| ps | project_status | NOT EXPOSED | project graph; overlaps with graph commands below |

## F. Machine Level: Code Generation (5)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| b2c | ComenCtrans | EXPOSED | `atelierb_generate_c` |
| b2c_old | ComenCOldtrans | NOT EXPOSED | legacy translator; low priority |
| p2c | ComenCtransall | EXPOSED | `atelierb_generate_project_c` |
| b2rust | Rusttrans | NOT EXPOSED | **high-value**: Rust output (D11 / future code-gen work) |
| dge | data_generation | NOT EXPOSED | ProB-based data generation (D03 / D08 cross-link) |

## G. Machine Level: Component Management (7)

| Abbrev | Command | Status | Mapped MCP tool / Rationale |
|---|---|---|---|
| af | add_file | EXPOSED | `atelierb_add_component` |
| rc | remove_component | EXPOSED | `atelierb_remove_component` |
| rg | remove_generated_files | NOT EXPOSED | cleanup helper |
| clp | close_project | INTERNAL | wrapper closes after each command |
| e | edit | OUT OF SCOPE | interactive editor |
| ep | edit_pmm | OUT OF SCOPE | interactive editor |
| sn | set_native | NOT EXPOSED | rarely-touched project flag |

## H. Machine Level: Documentation (7)

All NOT EXPOSED or OUT OF SCOPE.

| Abbrev | Command | Status | Rationale |
|---|---|---|---|
| sdl | show_doc_latex | NOT EXPOSED | LaTeX/PDF gen; viable but low priority |
| pdl | print_doc_latex | OUT OF SCOPE | printer driver |
| cdf | create_doc_framemaker | OUT OF SCOPE | legacy format |
| cdi | create_doc_ileaf | OUT OF SCOPE | legacy format |
| cdr | create_doc_rtf | OUT OF SCOPE | legacy format |
| pdi | print_doc_ileaf | OUT OF SCOPE | legacy + printer |
| spp | set_print_params | OUT OF SCOPE | printer setup |

## I. Machine Level: Graphs & Analysis (6)

All NOT EXPOSED. Surfacing the dependence / call / cross-ref graphs over
MCP is a natural Phase-3 deliverable for the Resources facet of the
protocol (see CLAUDE.md, Phase 3).

| Abbrev | Command | Status | Rationale |
|---|---|---|---|
| dg | dep_graph | NOT EXPOSED | dependence graph; useful for architectural review |
| fg | formula_graph | NOT EXPOSED | formula AST viewer |
| hg | homonymy_graph | NOT EXPOSED | identifier-collision analysis |
| ocg | op_call_graph | NOT EXPOSED | operation call graph |
| gpx | get_project_xref | NOT EXPOSED | cross-references |
| svf | show_vcg_file | NOT EXPOSED | VCG viewer (mostly interactive) |

## J. Machine Level: Browsing & Proofs (2)

| Abbrev | Command | Status | Rationale |
|---|---|---|---|
| b | browse | OUT OF SCOPE | interactive browser session |
| bart | bart | NOT EXPOSED | BART auto-refinement; potentially high value but interactive component questions arise |

## K. Machine Level: Batch Operations (2)

| Abbrev | Command | Status | Rationale |
|---|---|---|---|
| m | make_all | NOT EXPOSED | **high-value**: one-shot project workflow (typecheck → POG → prove all) |
| r | remake | NOT EXPOSED | **high-value**: remake all |

## Edition availability, measured 2026-08-19

The Phase 1 entries below used to carry "CE availability: TBC", which blocked
them. Measured against the installed Community Edition 24.04.2:

- `help` lists **96 commands**, including all 14 of the Phase 1 list.
- `spm` reports **15 installed proof mechanisms**: `altergo`, `cvc4_ddrp1_pp`,
  `cvc4_pp`, `cvc4_simple`, `cvc5_ddrp1_pp`, `cvc5_pp`, `cvc5_simple`,
  `iprover_pp`, `smtlib_simple`, `smtpp_rp0`, `smtpp_rp1`, `vampire_pp`,
  `z3_ddrp1_pp`, `z3_pp`, `z3_simple`. So `xtp` and `xce` have real drivers.
- `v` shows `ATB*B2RUST*Configuration_Directory` and `ATB*BART*RefinerFile`, so
  Rust generation and BART really ship in CE.

**All four TBC flags therefore resolve to available.**

One caveat, and it is the 2026-05-25 lesson restated: **appearing in `help` does
not mean a command works**. `vr` is listed too, yet it is Pro-only, confirmed by
the maintainer. Presence in `help` is necessary, never sufficient; only running
the command settles it.

## Priority list for closing the gap

Ranked by **user-facing value × implementation cost** for Claude-driven workflows. Each row references the bbatch abbrev and the rationale for the priority.

### Phase 1: high-value additions (target near term, Community Edition only)

| # | Command(s) | Proposed MCP tool name | Why |
|---|---|---|---|
| 1 | `xce` | `atelierb_counter_example` | When a PO fails, this is the single most useful next step. Today the user sees "fail" without diagnostic content. CE availability confirmed 2026-08-19: 15 mechanisms installed. |
| 2 | `us` / `ug` | `atelierb_unproved_status` (with optional component name) | **DONE 2026-08-19.** "What's left to prove?" is the most asked question during a proof session. |
| 3 | `xtp` / `xtr` | `atelierb_extprove`, `atelierb_extreplay` | Apply external proof mechanisms (mlSMT, ...) before manual interactive proof. Often closes hard POs auto. CE availability confirmed 2026-08-19: 15 mechanisms installed. |
| 4 | `u` | `atelierb_unprove` | Reset proof state to redo. Today the user has to delete `.pmi` files manually. |
| 5 | `m` / `r` | `atelierb_make_all`, `atelierb_remake` | One-shot "typecheck + POG + prove all" for project bootstrapping. |
| 6 | `pchk` | `atelierb_project_check` | IMPORTS-graph integrity. Catches structural issues `typecheck` misses. |
| 7 | `arc` / `res` | `atelierb_archive`, `atelierb_restore` | Snapshot before risky proof attempts; restore on backtrack. Pairs naturally with `unprove`. |
| 8 | `to` | `atelierb_proof_timeout` (read) + `timeout_seconds` on `atelierb_prove` | **DONE 2026-08-19.** Measured: `to N` holds only for the bbatch session that issues it, and the server starts one per command, so a standalone setter would report success and change nothing. The value travels with the proof instead. |
| 9 | `ic` | `atelierb_infos_component` | **DONE 2026-08-19.** Kind, source location and owner, complementing `status`. |
| 10 | `b2rust` | `atelierb_generate_rust` | Rust code generation; future D11 work needs this surface. CE availability confirmed 2026-08-19. |

### Pro-only (will not be exposed while server targets CE)

| Command | Note |
|---|---|
| `vr` / `verify_rule` | Mechanical rule verification. Pro-only confirmed 2026-05-25. |

If the Pro edition is added as a secondary target later, `vr` becomes a high-value Phase 1 candidate (the mechanism feeds D01-RuleVerifier, a separate project, if/when RuleVerifier runs on Pro). RuleVerifier's "Atelier B kernel proof" channel (per the registry) is the auto-prover, not `vr`, so RuleVerifier on CE is unaffected by this gap.

### Phase 2: medium-value (after Phase 1 lands)

| # | Command(s) | Proposed MCP tool name | Why |
|---|---|---|---|
| 11 | `dge` | `atelierb_data_generation` | ProB-driven data generation; cross-link to D03 data-validation work. |
| 12 | `xtm` | `atelierb_metrics` | Proof metrics; useful for dashboards. |
| 13 | `co` | `atelierb_proof_concurrency` | Per-session concurrency tuning (`to` is now Phase 1). |
| 14 | `spm` / `sppm` | `atelierb_proof_mechanisms`, `atelierb_project_proof_mechanisms` | List available + per-project provers. Useful sidecar to `xtp`. |
| 15 | `dg` / `ocg` / `gpx` | `atelierb_dep_graph`, `atelierb_op_call_graph`, `atelierb_xref` | Architectural visualisation; natural Phase-3 Resources material. |
| 16 | `v` | `atelierb_version` | Diagnostic; one-line wrapper. Quick win. |
| 17 | `bart` | `atelierb_bart` | Auto-refinement; medium-complexity wrapper (BART is interactive in places). CE availability confirmed 2026-08-19. |

### Phase 3: lower-value / niche

- Library / definitions management (`add` / `rdd` / `apl` / `rpl` / `sll` / `spll` / `sddl`): bundle as `atelierb_project_libraries` (read) + dedicated mutate operations.
- Reader / user / permission management (`apr` / `rpu` / `sprl` / `spul`): skip unless multi-user workflow is requested.
- `crpm` create_project_manifest: skip unless manifest-driven onboarding is wanted.
- `mip` migrate_project: one-shot; CLI is fine.
- Remote variants (`rde` / `rpo` / `rpr`): skip until a remote workflow exists.
- `sdl` show_doc_latex: viable but low demand; defer.

### Explicit non-goals

- All interactive-editor commands (`e`, `ep`, `erf`, `eur`, `epr`, `srb`).
- All HTML viewer commands (`hh`, `hph`, `hrb`).
- Legacy doc formats (`cdf` FrameMaker, `cdi` Interleaf, `cdr` RTF, `pdi`).
- Printer setup (`spp`).
- Subprocess lifecycle (`q`, `cd`, `pwd`).

## Cross-project implications

- **D01-RuleVerifier** (a separate project, not part of this repository): `vr` (verify_rule) is Pro-only and not in scope for the CE-targeting MCP server. RuleVerifier on CE uses the auto-prover ("Atelier B kernel proof" per the registry), not `vr`, so this audit does not block RuleVerifier.
- **Code generation to Python and other targets** and the Rust-generation interest need `b2rust` exposed (Phase 1 item #10). Confirm `b2rust` exists in CE before scheduling implementation.
- **Phase-3 of this server's roadmap** (Resources facet, per `CLAUDE.md`) aligns naturally with graph commands (`dg`, `ocg`, `gpx`, `fg`, `hg`). When Phase 3 starts, prioritise graph surfaces over more bbatch tools.
- The maintainer's cross-project Atelier B interaction guide, kept outside this repository, does not yet cover `xtp` / `xce` / `bart`; updating it should happen in parallel with each Phase 1 tool addition. The guide should also gain an "Edition" column or note marking which commands are Pro-only.
