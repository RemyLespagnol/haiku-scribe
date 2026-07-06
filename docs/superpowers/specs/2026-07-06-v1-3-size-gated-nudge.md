# v1.3 — Size-gated nudge, substitutable scout output

## Verdict driving this

`docs/superpowers/evaluations/2026-07-06-v1-2-break-even-sweep.md`: delegation to
`haiku-scribe` pays only when material overflows the main context window AND a
structured (summary-level) extraction is enough to finish the task. Outside that
window it is neutral (small files) or actively harmful (+50% cost when the main
session delegates and then re-reads the raw source).

## Decisions

- **Trigger = real file size at `PreToolUse`, not prompt keywords.** The v1.2
  keyword nudge on `UserPromptSubmit` was not correlated with the actual
  break-even condition. `v1_2_hooks.py` now nudges only when a `Read` targets a
  file whose `stat().st_size` exceeds `HAIKU_SCRIBE_SIZE_THRESHOLD`
  (default 256_000 bytes, a first-pass figure derived from the sweep — not
  re-validated per project). Dedup is per `(session_id, file_path)`.
- **Keyword nudge removed.** No more `UserPromptSubmit` handler, no
  `BROAD_PROMPT_MARKERS`, no initial/followup nudge pairing.
- **Agent output must be substitutable, not just a resume.** The v1.2 contract's
  compact-brief-only shape forced a double read (delegate, then re-read the raw
  source) whenever the task needed exact detail — the single biggest cost sink
  in the sweep. The agent contract and guidance now require: delegate only when
  the material is both massive and summary-sufficient; otherwise read directly;
  never delegate then re-read.
- **Guidance recalibrated.** Dropped the "4+ files" trigger (well under
  break-even) and the "stop and call it immediately" enforcement framing.

## Out of scope

No re-sweep in this iteration. The 256KB threshold is a first setting derived
from the existing sweep data, adjustable via `HAIKU_SCRIBE_SIZE_THRESHOLD`.
