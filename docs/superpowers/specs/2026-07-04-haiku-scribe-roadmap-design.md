# Haiku Scribe Product Roadmap Design

Date: 2026-07-04
Status: Draft for review
Scope: Product roadmap spec above the existing PRDs
Inputs:
- `docs/haiku_scribe_prd.md`
- `docs/haiku_scribe_skill_prd.md`

## Purpose

This document defines the product roadmap shape for Haiku Scribe before any phase-specific implementation spec is written. It does not replace the existing PRDs. It constrains how they should be executed over time.

The goal is to make the rollout sequence explicit and defensible:

- what each version is trying to prove;
- what each version includes;
- what each version explicitly excludes;
- what evidence is required before moving forward;
- which future spec should be written next for that version.

This roadmap is intentionally normative and strictly sequential. A later version does not start because it is interesting or technically possible. It starts only when the previous version has met both its product and technical gates.

## Why A Roadmap Spec Exists

The source PRDs contain a coherent overall direction, but they also span multiple different product layers:

- a native read-only Haiku subagent;
- personal installation and diagnostics;
- audit hooks and reports;
- prompt nudges and optional soft enforcement;
- repository or team rollout;
- plugin packaging;
- enterprise-managed deployment;
- future optional extensions such as MCP or a separate Codegraph variant.

Treating that as one implementation target would create immediate scope blur. This roadmap exists to prevent that blur. It is a guardrail for future sessions.

## Planning Rules

The roadmap follows these rules:

1. Versions are product versions, not workstreams.
2. Versions are strictly sequential.
3. Every version must have clear in-scope and out-of-scope boundaries.
4. Every version must define both a product or usage gate and a technical or security gate.
5. Every version must also define non-passage conditions.
6. Every version should point to the next dedicated spec that must be written before implementation for that phase begins.
7. The roadmap is not an implementation plan. It is a phase contract.

## Recommended Version Sequence

The product should be rolled out in this order:

1. `v0` manual workflow validation
2. `v1` personal packaging baseline
3. `v1.1` audit-only instrumentation
4. `v1.2` prompt nudges
5. `v1.3` optional soft enforcement
6. `v2` team or project mode
7. `v3` Claude Code plugin packaging
8. `v4` enterprise-managed rollout
9. `v5` optional advanced extensions

This order expresses dependency truth:

- usefulness must be proven before packaging;
- packaging must be proven before instrumentation can be trusted;
- instrumentation must be proven before guidance can be tuned;
- guidance must be proven before friction is added;
- personal stability must be proven before team distribution;
- team stability must be proven before plugin packaging;
- packaged stability must be proven before enterprise governance;
- core native value must be proven before optional complexity is considered.

## Version Details

## `v0` Manual Workflow Validation

### Objective

Prove that a native Claude Code subagent named `haiku-scribe`, running on Haiku and constrained to read-only context compression, is genuinely useful in real sessions before any installation or governance machinery is built.

### In Scope

- the manual `haiku-scribe` subagent definition;
- a clear delegation contract for when the main Claude should invoke it;
- a required response shape for summaries, evidence, unknowns, and suggested direct reads;
- clear rules that keep final reasoning, editing, and security-sensitive conclusions with the main model;
- manual trial usage on realistic bulk-reading tasks.

### Explicitly Out Of Scope

- installer commands;
- automatic configuration changes;
- hooks;
- reports;
- prompt nudges;
- soft enforcement;
- project or team rollout;
- plugin packaging;
- enterprise-managed controls;
- MCP;
- Codegraph integration in the base product.

### Entry Dependencies

- a stable written contract for what Haiku Scribe is and is not;
- agreement that the manual workflow is the first proof target;
- no dependency on external providers, local runtimes, or custom MCP infrastructure.

### Main Risks

- the subagent may summarize cheaply but not usefully;
- the boundary between evidence extraction and reasoning may remain too fuzzy;
- the output contract may be too loose to support later automation;
- manual invocation may feel too awkward to validate the core idea fairly.

### Future Dedicated Spec

`v0-manual-subagent-design.md`

That future spec should define the exact subagent contract, tool restrictions, prompt shape, output contract, and manual evaluation protocol.

### Gate To Pass

Product or usage gate:
- real workflow trials show that Haiku Scribe reduces raw context loading pressure in bulk-reading situations without making the main workflow feel worse.

Technical or security gate:
- the subagent contract is unambiguous about allowed behavior, forbidden behavior, evidence expectations, and main-model verification responsibility.

### Non-Passage Conditions

Do not open `v1` if any of the following remain true:

- users cannot tell when they should use Haiku Scribe;
- summaries are too generic to support focused follow-up reads;
- the subagent regularly drifts into conclusions reserved for the main model;
- safety boundaries depend on convention alone rather than a clear contract.

## `v1` Personal Packaging Baseline

### Objective

Turn the validated manual workflow into a personal product that one user can install, verify, and remove safely without relying on ad hoc file edits.

### In Scope

- `setup`;
- `doctor`;
- `uninstall`;
- backups before config mutation;
- dry-run behavior;
- safe merge of user settings;
- bounded ownership markers for inserted guidance;
- validation that the subagent still matches the intended safety contract.

### Explicitly Out Of Scope

- audit events;
- usage reports;
- nudges;
- enforcement;
- team distribution;
- plugin packaging;
- enterprise-managed policy.

### Entry Dependencies

- `v0` has shown that the manual workflow is useful enough to deserve packaging;
- the subagent contract is stable enough to encode into setup and doctor checks.

### Main Risks

- setup may damage or confuse existing Claude Code configuration;
- doctor may check configuration shape without checking user-visible behavior;
- uninstall may remove unrelated user content;
- idempotency may fail and produce duplicated blocks or conflicting permissions.

### Future Dedicated Spec

`v1-personal-cli-design.md`

That future spec should define command UX, file ownership model, merge strategy, backup strategy, doctor contract, and uninstall behavior.

### Gate To Pass

Product or usage gate:
- a single user can repeatedly install, understand, verify, and remove Haiku Scribe without relying on manual repair or undocumented tribal knowledge.

Technical or security gate:
- setup, doctor, and uninstall are idempotent, reversible, and narrow in the configuration they own.

### Non-Passage Conditions

Do not open `v1.1` if any of the following remain true:

- installation requires manual cleanup to recover from expected cases;
- doctor cannot reliably catch model or permission drift;
- uninstall is unsafe around unrelated settings;
- the owned versus unowned configuration boundary is not explicit.

## `v1.1` Audit-Only Instrumentation

### Objective

Measure real usage and missed delegation opportunities before adding guidance or friction.

### Current Decision

After local V1 guidance-routing trials on July 6, 2026, do not build the full v1.1 audit/report product as the immediate next phase.

The trials already showed a repeated missed-routing pattern:

- global `CLAUDE.md` guidance loads;
- the `haiku-scribe` agent listing is visible;
- the main session uses compact discovery such as CodeGraph or prior-session context;
- the main session then crosses into broad raw reads/searches without calling `haiku-scribe`.

This is enough evidence to justify a v1.2-lite nudge experiment. Keep only micro-audit in that experiment: local timestamp, session id, trigger reason, tool, and whether a nudge fired. Defer the full audit dashboard, aggregation, token estimates, and reports until a nudge proves useful and needs tuning.

### In Scope

- audit-only hooks;
- local event capture for direct reads, likely expensive reads, and Haiku Scribe invocations;
- conservative local reporting over recent activity;
- enough metadata to understand project, session, and usage patterns.

### Explicitly Out Of Scope

- any blocking behavior;
- any user-facing enforcement;
- team-level aggregation;
- enterprise telemetry export;
- prompt nudges.

### Entry Dependencies

- `v1` packaging is stable enough that instrumentation can be added without compounding configuration fragility;
- the product has a clear notion of what counts as a likely missed delegation candidate.

### Main Risks

- audit data may be too noisy to guide product decisions;
- event capture may miss the cases that matter;
- reporting may overstate savings and create false confidence;
- the hook surface may create surprising installation complexity.

### Future Dedicated Spec

`v1-1-audit-reporting-design.md`

That future spec should define event schema, storage strategy, report contract, conservative estimation rules, and graceful failure behavior.

This spec is no longer the next recommended spec. The next recommended spec is a focused v1.2-lite prompt-nudge design with embedded micro-audit.

### Gate To Pass

Product or usage gate:
- audit output reveals real and repeated delegation opportunities worth acting on.

Technical or security gate:
- event capture and reporting are accurate enough, local-only, and bounded enough to support product decisions without increasing the tool's blast radius.

### Non-Passage Conditions

Do not open `v1.2` if any of the following remain true:

- missed-delegation detection is mostly noise;
- report outputs cannot be trusted directionally;
- instrumentation materially complicates installation or diagnosis;
- the product cannot distinguish strong signals from weak hints.

## `v1.2` Prompt Nudges

### Objective

Improve adoption by reminding the main workflow to use Haiku Scribe when context suggests bulk reading, while keeping the experience lightweight and non-blocking.

### In Scope

- short reminder nudges for likely bulk-reading situations;
- conservative classification of prompts and read patterns;
- behavior designed to guide, not force.

### Explicitly Out Of Scope

- blocking reads;
- user override mechanisms beyond ignoring a nudge;
- team governance;
- policy enforcement.

### Entry Dependencies

- `v1.1` has shown enough repeated missed-delegation patterns to justify intervention;
- the product can express nudges without creating substantial context pollution.

### Main Risks

- nudges may fire too often and become background noise;
- nudges may appear in the wrong moments and reduce trust;
- classification may be too brittle to scale into later guardrails.

### Future Dedicated Spec

`v1-2-prompt-nudges-design.md`

That future spec should define trigger heuristics, copy contract, suppression rules, and measurement strategy.

### Gate To Pass

Product or usage gate:
- nudges materially improve correct Haiku Scribe usage without becoming annoying or ignored.

Technical or security gate:
- classification and injection behavior are conservative, predictable, and diagnosable.

### Non-Passage Conditions

Do not open `v1.3` if any of the following remain true:

- nudges are frequent but not useful;
- adoption improves only by increasing noise;
- the classification logic cannot justify why a nudge fired;
- the intervention surface is not stable enough to add even optional friction.

## `v1.3` Optional Soft Enforcement

### Objective

Add a disabled-by-default guardrail for clearly expensive direct reads, only after the workflow, packaging, instrumentation, and nudges have earned trust.

### In Scope

- optional soft enforcement for a narrow class of costly direct reads;
- explicit user override;
- messaging that explains why a read was blocked or redirected;
- diagnostics for false positives and override usage.

### Explicitly Out Of Scope

- hard enforcement by default;
- broad policy controls;
- team-admin policy;
- enterprise enforcement models.

### Entry Dependencies

- `v1.2` has shown that guidance can improve behavior without degrading trust;
- the product can identify a conservative subset of direct reads where intervention is justified.

### Main Risks

- false positives may damage trust quickly;
- override semantics may be confusing;
- enforcement may be introduced before the product deserves that power.

### Future Dedicated Spec

`v1-3-soft-enforcement-design.md`

That future spec should define the exact enforcement boundary, allow and block rules, override mechanism, diagnostics, and rollback expectations.

### Gate To Pass

Product or usage gate:
- advanced users accept the optional guardrail as helpful rather than obstructive.

Technical or security gate:
- false positives are rare enough, diagnosable enough, and reversible enough that the feature can exist without destabilizing normal work.

### Non-Passage Conditions

Do not open `v2` if any of the following remain true:

- the override path is unclear or unreliable;
- false positives are difficult to debug;
- enforcement is being used to compensate for weak guidance;
- the product still needs per-user manual babysitting.

## `v2` Team Or Project Mode

### Objective

Make the product shareable across a repository or team without losing the bounded safety and predictable behavior proven in personal use.

### In Scope

- project-level setup model;
- project-level doctor behavior;
- shared routing guidance and documentation;
- shared defaults for the validated safety model;
- repository-scoped installation and validation patterns.

### Explicitly Out Of Scope

- enterprise-managed deployment;
- org-wide policy control;
- plugin-first distribution if the underlying team workflow is not yet stable.

### Entry Dependencies

- the product is stable in personal use across setup, diagnosis, audit, guidance, and optional guardrails;
- the configuration surfaces are stable enough to be shared.

### Main Risks

- user-level and repo-level ownership may become tangled;
- team defaults may overreach and break local expectations;
- support burden may grow if diagnostics are not strong enough.

### Future Dedicated Spec

`v2-team-project-mode-design.md`

That future spec should define ownership boundaries, repository installation shape, local versus shared precedence rules, and team diagnostics.

### Gate To Pass

Product or usage gate:
- the workflow is useful and understandable when shared across a repository pilot, not just by one careful user.

Technical or security gate:
- ownership, precedence, and recovery behavior are clear enough for shared environments.

### Non-Passage Conditions

Do not open `v3` if any of the following remain true:

- team setup depends on repeated manual intervention;
- local and shared config precedence is still ambiguous;
- repository rollout creates new safety uncertainty;
- the team value proposition is still mostly theoretical.

## `v3` Claude Code Plugin Packaging

### Objective

Package the proven product into a cleaner installation and upgrade path without changing the underlying contract.

### In Scope

- plugin packaging;
- install and upgrade behavior appropriate to the plugin surface;
- alignment between plugin packaging and the already validated product contract.

### Explicitly Out Of Scope

- changing the core product model just to fit packaging;
- enterprise-managed rollout;
- new advanced capabilities unrelated to packaging.

### Entry Dependencies

- the shared product shape is stable enough to be packaged as a maintained distribution artifact;
- versioned ownership boundaries already exist conceptually from earlier phases.

### Main Risks

- packaging may hide unresolved product instability;
- the plugin form may tempt premature expansion of scope;
- upgrade behavior may be underspecified.

### Future Dedicated Spec

`v3-plugin-packaging-design.md`

That future spec should define packaging boundaries, install and upgrade behavior, ownership migration, and compatibility expectations.

### Gate To Pass

Product or usage gate:
- plugin packaging simplifies adoption relative to earlier installation paths.

Technical or security gate:
- the packaging model preserves safety boundaries, diagnostics, and reversibility.

### Non-Passage Conditions

Do not open `v4` if any of the following remain true:

- packaging masks unresolved configuration ownership issues;
- upgrades are not predictable;
- the plugin is easier to install but harder to diagnose or remove;
- distribution has improved while governance remains immature.

## `v4` Enterprise-Managed Rollout

### Objective

Add enterprise-governed deployment and policy surfaces only after the personal and team product has already proven itself.

### In Scope

- managed settings support;
- managed safety defaults;
- managed audit visibility;
- policy exception visibility;
- deployment model suitable for enterprise review.

### Explicitly Out Of Scope

- unrelated new product features;
- optional advanced extensions used as justification for enterprise rollout.

### Entry Dependencies

- the packaged product is stable enough to deserve organizational governance;
- there is clear evidence that the product's value extends beyond individual enthusiasm.

### Main Risks

- governance needs may expose earlier ambiguities in ownership or policy semantics;
- enterprise packaging may demand observability surfaces the product is not ready to support;
- the product may become policy-heavy before its core remains simple.

### Future Dedicated Spec

`v4-enterprise-managed-rollout-design.md`

That future spec should define managed surfaces, exception model, reporting boundaries, and admin-facing contracts.

### Gate To Pass

Product or usage gate:
- the product shows enough organizational value to justify managed rollout effort.

Technical or security gate:
- managed controls, visibility, and exception handling are coherent enough for enterprise review.

### Non-Passage Conditions

Do not open `v5` if any of the following remain true:

- enterprise rollout is still compensating for unclear core behavior;
- governance surfaces outpace the stability of the underlying product;
- admin controls are being used to paper over weak user-facing product design.

## `v5` Optional Advanced Extensions

### Objective

Explore only those extensions that remain justified after the native product has matured, such as MCP support or a separate Codegraph-enabled variant.

### In Scope

- optional MCP evaluation, if still necessary;
- a separate optional Codegraph-enabled variant, if still necessary;
- extension-specific validation of whether added complexity buys real value.

### Explicitly Out Of Scope

- expanding the base product just because advanced capabilities exist;
- merging Codegraph or MCP into the base Haiku Scribe without a separate justification and boundary model.

### Entry Dependencies

- the core native product has already been proven useful, governable, and distributable;
- there is a concrete unmet need that the base architecture cannot satisfy cleanly.

### Main Risks

- optional extensions may destabilize the product's original simplicity;
- complexity may be introduced as novelty rather than necessity;
- base and advanced variants may become confused.

### Future Dedicated Spec

No single default spec should be assumed. Each extension requires its own separate product justification and design document.

### Gate To Pass

Product or usage gate:
- a validated unmet need exists that the base product cannot address well enough.

Technical or security gate:
- the extension can be isolated cleanly without weakening the guarantees of the base product.

### Non-Passage Conditions

Do not start an advanced extension if any of the following remain true:

- the extension is justified mainly by curiosity;
- the extension blurs the original product boundary;
- the core product still has unresolved usability, safety, or governance debt.

## Cross-Version Maturity Matrix

This matrix is intentionally short. It exists to make the progression legible across versions.

| Axis | v0 | v1 | v1.1 | v1.2 | v1.3 | v2 | v3 | v4 | v5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Subagent capability | manual, bounded | packaged personal | observed | guided | guarded | shared | packaged | governed | optionally extended |
| Install model | manual | personal CLI | personal CLI plus hooks | same | same | team or repo aware | plugin | managed | extension-specific |
| Auditability | manual judgment | doctor only | local audit and reports | measured nudges | measured overrides | shared validation | packaged diagnostics | managed visibility | extension-specific |
| Safety posture | contract only | enforced by setup plus doctor | observed in use | guided conservatively | optional friction | shared defaults | packaged defaults | managed defaults | isolated per extension |
| Deployment scope | individual experiment | individual user | individual user | individual user | advanced individual user | repository or team | broad self-serve distribution | enterprise | optional specialized users |

## Decision Rules For Future Sessions

Future brainstorming and implementation planning sessions should use this roadmap as a routing document.

When a new idea appears, classify it in one of four ways:

1. belongs to the current version;
2. belongs to a later named version;
3. requires a new explicit version change to this roadmap;
4. should be rejected because it weakens the product boundary.

This rule matters because Haiku Scribe can easily accrete attractive but destabilizing ideas:

- new providers;
- broader agent powers;
- more invasive enforcement;
- richer telemetry;
- tighter IDE integration;
- advanced repository intelligence.

Those ideas are not automatically bad. They are bad when they bypass the roadmap and collapse proof order.

## What This Roadmap Intentionally Does Not Decide

This document does not decide:

- the exact prompt for the `haiku-scribe` subagent;
- the exact CLI syntax;
- the exact settings file schema;
- the exact hook API shape;
- the exact report format;
- the exact plugin manifest shape;
- the exact enterprise admin interfaces.

Those belong in later version-specific specs. This document decides sequencing and proof obligations, not implementation detail.

## Recommended Next Specs

Assuming this roadmap is accepted, the future spec sequence should be:

1. `v0-manual-subagent-design.md`
2. `v1-personal-cli-design.md`
3. `v1-1-audit-reporting-design.md`
4. `v1-2-prompt-nudges-design.md`
5. `v1-3-soft-enforcement-design.md`
6. `v2-team-project-mode-design.md`
7. `v3-plugin-packaging-design.md`
8. `v4-enterprise-managed-rollout-design.md`

These should be handled in separate sessions, one phase at a time.

## Review Notes

This roadmap should be reviewed against three questions:

1. Are any versions too broad for a single dedicated spec?
2. Are any gates too vague to support a real go or no-go decision?
3. Is any feature currently placed too early relative to the product's safety and proof burden?

If the answer to any of those is yes, adjust the roadmap before writing the next phase spec.
