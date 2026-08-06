<!--
Copyright (C) 2026 CLEARSY (https://www.clearsy.com)
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Reading `.pmi` proof files: use the sibling `.po`

## Summary

A `.pmi` file holds three flat lists with one entry per proof obligation
(`ProofState`, `MethodList`, `PassList`), but **nothing in the file says which
`(operation, index)` an entry belongs to**. That information lives in the
sibling `.po` file.

> **The rule.** Entry `i` of a `.pmi` flat list describes the proof obligation
> named by line `i` of the `ProofList` theory of the sibling `.po` file, which
> carries an explicit `Operation.index` label.

There is no positional rule to apply, no permutation to guess, and nothing to
derive from the header. Read the labels.

Verified on the 350 `.pmi` files of a real workspace: every one has a sibling
`.po`, and every one aligns 1:1 with it (zero count mismatch).

## Where the labels are

The `ProofList` theory of a `.po` file lists one entry per proof obligation, in
file order. The label is the last conjunct before the comma that introduces the
formula:

```
THEORY ProofList IS
_f(1) & _f(2) & _f(10) & _f(11) & WellDefinedness_clear.2,(_f(22) & ... => _f(56));
_f(1) & _f(2) & _f(10) & _f(11) & WellDefinedness_clear.1,(_f(22) & ... => _f(55));
_f(1) & _f(2) & _f(10) & _f(11) & Operation_clear.9,(_f(22) & ... => _f(42));
...
END
```

Pairing that list with `ProofState` and `MethodList` of the `.pmi`, index by
index, gives the status and the saved proof script of each named proof
obligation.

## Group summaries: the third field is not the unproved count

`BalanceX` and `Status` both carry per-group summaries, with **different field
layouts**:

```
BalanceX:  name, total, provedInteractively, ?, provedAutomatically, 0, 0, 0
Status:    name, total, provedInteractively, provedAutomatically, 0, 0, 0
```

Unproved proof obligations are the remainder:

```
unproved = total - provedInteractively - provedAutomatically
```

This is not guesswork: it is the layout bbatch itself prints in its status table,
column for column.

```
+--------------------------+------+-------+-------+------+-----+
|                          | NbPO | NbPRi | NbPRa | NbUn | %Pr |
+--------------------------+------+-------+-------+------+-----+
| Operation_clear          |    9 |     0 |     6 |    3 |  66 |
| Operation_query          |    1 |     1 |     0 |    0 | 100 |
```

`NbPRi` (proved interactively) and `NbPRa` (proved automatically) are the header
fields; `NbUn` is derived, not stored.

Reading the third field as "unproved" is not merely imprecise, it is **inverted
in the common case**: a group proved entirely by interactive proof reads as
entirely unproved.

| Line (`BalanceX`) | Naive reading (field 3 = unproved) | Correct reading | bbatch says |
|---|---|---|---|
| `Operation_bump,4,1,0,3` | 1 unproved | 1 interactive, 3 automatic, **0 unproved** | Proved 4, Unproved 0 |
| `Operation_clear,9,0,0,6` | 0 unproved | 0 interactive, 6 automatic, **3 unproved** | Proved 6, Unproved 3 |
| `Operation_query,1,1,0,0` | 1 unproved | 1 interactive, 0 automatic, **0 unproved** | Proved 1, Unproved 0 |

### The header can lag behind the flat list

Measured over the same 350 files: totals and interactive counts always agree
with the per-PO statuses, but the **automatic** counter is sometimes lower than
reality (60 groups across 43 files, never higher). So per-operation counts
should be derived from the statuses, never from the header. For authoritative
counts, `bbatch` remains the reference (`atelierb_status`).

A related detail, left as-is: a handful of groups (6, measured) appear in the
header but have no proof obligation in the `.po`.

## `.pmm` files are not per-PO lists

The `User_Pass` theory of a `.pmm` holds one entry per **interactively proved**
proof obligation, each carrying its own `Operation(...)` filter. It is not
aligned with the proof obligation list and must not be treated as if it were.

On `Algo_CC/M0_i`: 22 proof obligations but 8 `User_Pass` entries, tagged
`Operation_algo` (5), `WellDefinedness_algo` (2), `ValuesLemmas` (1). Those are
exactly the interactive counts of the header (`M0_i,22,8,0,13`).

## Why the previous "reverse the entries" rule was wrong

An earlier version of this document, and the code that followed it, claimed the
flat lists were stored in reverse order of the bbatch numbering, so that
reversing them and then splitting by the header groups would recover the
mapping.

**That rule is wrong.** Measured against the `.po` labels, it reproduces the
correct mapping on only **189 of 252** applicable files, and fails on 63.

It survived review because it happens to hold on small specimens. On
`WBProof_PmiProbe` (13 POs, 4 groups) the `.po` group order is exactly the
reverse of the header order, so reversal is indistinguishable from the truth.
On a real component it is not:

| Component | Group order in the `.po` |
|---|---|
| `WBProof_PmiProbe/probe` | `WellDefinednessAssertions, Operation_bump, Initialisation, AssertionLemmas` (exact reverse of the header) |
| `WBProof_SensorStore/sensor_store_i` | `WellDefinedness_clear, WellDefinedness_query, WellDefinednessInvariant, Operation_clear, Operation_query, Operation_set_one, Initialisation` (neither the header order nor its reverse) |

The visible symptom on `sensor_store_i`: proof scripts saved on
`Operation_query.1`, `Operation_set_one.3` and `.4` were reported under
`Operation_clear.3`, `.4` and `.5`, and the three unproved POs of
`Operation_clear` were attributed to other operations.

A second, independent defect compounded it: comparing the naively decoded header
against the count of `Unproved` entries suggested a gross inconsistency (14
against 3, 18 against 3, 18 against 2 on three real projects) and led to the
conclusion that no permutation could reconcile the two sections. Once the header
fields are decoded correctly, the two agree.

Both defects are fixed. The reversal functions have been removed; `.pmi` and
`.pmm` files are now returned exactly as they are on disk.

## Implementation

In `atelierb_mcp/parsers.py`:

- `parse_po_labels(po_content) -> list[str]`: the ordered labels of a `.po`.
- `label_pmi_entries(pmi_content, po_content) -> list[dict] | None`: pairs each
  flat entry with its label, status and method. Returns `None` if the two files
  do not line up, rather than guessing.

`atelierb_read_file` returns `.pmi` content verbatim and adds a `po_labels`
field when the sibling `.po` is available.

The same pairing is used by the PRI server (`atelierb_pri/parsers.py`,
`parse_pmi_file(content, po_content)`), which reports `labels_available` so a
client can tell when the attribution is guaranteed.

## Non-regression test

`tests/test_parsers.py::TestPmiPoPairing`, on fixtures copied from two real
components. The pair is deliberate: `probe` is compatible with the old reversal
rule and `sensor_store_i` is not, so a fix validated on `probe` alone looks
correct and is not.

The specimen is cheap to rebuild: fresh project, one machine with several PO
groups **of different sizes**, `pogenerate`, `prove` at force 0, then in PRI go
to proof obligations at chosen positions and prove each with a uniquely
identifiable script `ah(K = K) & mp & pr` where `K` encodes the intended
position. This works even on POs the automatic prover already discharges: the
saved script turns them into `Proved(Util)` with a readable signature. Then `sw`
each, quit, and read the `.pmi`.
