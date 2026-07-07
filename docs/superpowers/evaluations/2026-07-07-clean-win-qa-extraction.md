# Clean-Win Field Case — QA Extraction (real session)

Date: 2026-07-07
Session: `da36d837-0e0a-44ec-92d8-65c715df82ec` (repo `dev/formats`, main model Opus 4.8)
Costs via `bench/cost.py` (reproduces official `/cost` to the cent).

Counterpart to `2026-07-06-v1-2-break-even-sweep.md`: that sweep found the
*loss* case (large file + detail-demanding task → main re-reads → +50%). This is
the same tool hitting its intended *win* case in real use, so the two sit side by side.

## Task

Unprompted, real work — not a fixture:

> "J'aimerais avoir une liste de QA Tasks qu'on a faites sur ADV-30177a et
> ADV-30177b, pour rejouer des non-reg. Tu les retrouverais, avec les docs et le code ?"

Shape: ratisser plusieurs docs de specs/plans → produire une extraction structurée
et actionnable. Exactly the broad read-only gathering haiku-scribe is for.

## What happened

- **Trigger fired**: main delegated to `haiku-scribe` (1 subagent).
- **Scout**: 3 `Read` calls, **single pass**, on 3 docs totalling **65,796 bytes (~16k tokens)**.
- **Scout output**: 13,482 chars / 1,844 words — a structured **QA reproduction
  checklist** (tickets 1–4, deleted goldens, prioritised manual repro steps).
  Substitutable, not a vague summary.
- **No re-read**: after the `Agent` call the main did 2 `Read`s, but on session
  *memory* files — **not** the scout's docs. The +50% double-read failure mode did
  not occur.

## Costs

| | |
| --- | --- |
| Total | **$4.970107** |
| Opus (main) | $4.901635 |
| Haiku (scout) | **$0.068471** |
| `raw_into_main` | 121,822 |

## Findings

1. **Clean win pattern, confirmed in the wild.** All three break-even conditions
   held: broad read-only volume, a task that tolerates an extraction (checklist,
   not exact stats), and a main that *trusted* the output instead of re-reading.
   The scout kept ~16k raw tokens out of Opus for **$0.068** and returned a ~5×
   compressed, directly usable artefact.
2. **The scout is a rounding error on cost (1.4%).** $0.068 of $4.97. The dominant
   cost is the conversation itself + `raw_into_main` (121k of scaffolding, not
   files). haiku-scribe optimises the right slice, but it is a small slice — the
   bigger lever on long Opus sessions remains trimming the session scaffolding.
3. **Ran on the pre-fix (file-count) contract, unaffected.** Only 3 reads, so the
   old "stop around 15 files" cap never bit. The 2026-07-07 budget change
   (volume-based, one-pass, explicit-coverage) targets the 30+ file survey case,
   not this one.

## Verdict

When the task is the right shape, the tool behaves exactly as designed: relevant
trigger, single-pass coverage, substitutable output, no re-read, negligible scout
cost. Keep this next to the break-even sweep as the "win" bookend — the product is
viable *inside its window*, and this is what the inside of the window looks like.
