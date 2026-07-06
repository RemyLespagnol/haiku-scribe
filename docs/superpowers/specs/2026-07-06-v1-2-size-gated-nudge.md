# v1.2 — Cost-aware nudge recalibration

## Verdict driving this

`docs/superpowers/evaluations/2026-07-06-v1-2-break-even-sweep.md`: delegation to
`haiku-scribe` is most valuable when it prevents broad raw context from entering
the main session. It becomes actively harmful when the main session delegates and
then re-reads the same raw source. The sweep makes one product constraint clear:
V1.2 should nudge conservatively and teach the anti-double-read rule, not shrink
Haiku Scribe into a large-file-only tool.

## Decisions

- **Keep keyword nudges for V1.2.** `UserPromptSubmit` remains the primary
  adoption nudge for clearly broad-context prompts such as repository scans,
  architecture reviews, flow mapping, transcripts, and large-file requests.
  Trigger markers stay conservative to avoid training users to ignore the hook.
- **Keep `PreToolUse` follow-up.** For a prompt already flagged as broad context
  gathering, the first direct `Read` or `Grep` gets one follow-up reminder.
  Dedup remains per `(session_id, prompt_id)`.
- **Add size as an extra signal, not the product definition.** Direct `Read` of a
  file larger than `HAIKU_SCRIBE_SIZE_THRESHOLD` (default 256_000 bytes) can
  nudge even without a prompt marker. This catches the strongest break-even
  cases while preserving the scout model for broad reconnaissance.
- **Encode the anti-double-read rule.** Guidance and hook copy should warn that
  delegating and then re-reading the same raw source costs more than either path
  alone. If exact line-level detail is needed immediately, read directly. If
  delegating, ask for a structured extraction useful enough to avoid broad
  re-reading.
- **Keep Haiku Scribe as a scout.** Do not replace the broad-context contract
  with "massive and substitutable only." That economic rule is a caution for
  when nudges should fire and how the agent should answer, not the whole product.

## Out of scope

No hard blocking, no soft enforcement, no team rollout, and no re-sweep in this
iteration. The 256KB threshold is a first-pass setting derived from existing
sweep data and remains adjustable via `HAIKU_SCRIBE_SIZE_THRESHOLD`.
