---
name: executor-advisor
description: Coordinate a single-controller Executor-Advisor workflow in Codex. Keep the root task as the sole executor and consult at most one read-only `advisor` custom subagent per logical task at high-value planning, recovery, and final-review checkpoints. Use for long-horizon or high-risk coding, research, architecture, debugging, concurrency, security, performance, and review tasks where a second opinion can materially improve the result; skip routine or directly verifiable work.
---

# Executor Advisor

## Keep one controller

- Keep the current root task as the executor. It owns the user conversation,
  decisions, edits, commands, tests, and final response.
- Use at most one active `advisor` per logical task for analysis and criticism;
  permit at most one replacement. Reuse it across turns; never spawn per turn.
- Never run advisors concurrently or create a third. A new initial advisor is
  allowed only for a genuinely new task.
- Treat advice as evidence and verify it before acting.

## Ensure the advisor exists

Use exactly the custom agent type/name `advisor`, discovered from
`~/.codex/agents/advisor.toml`, or from `$CODEX_HOME/agents/advisor.toml` when
`CODEX_HOME` is set.

If it is unavailable, first run the sibling setup script at
`../advisor-setup/scripts/configure_advisor.py --status` as a read-only
diagnostic. Resolve that path relative to this skill. If the status is valid,
retry discovery. If the config is missing, malformed, unsupported, or cannot
be verified, stop and request explicit authorization before changing persistent
configuration. After authorization, use no options only to initialize a
missing config, or use `--reset` to repair an existing one; recheck discovery
after setup. If a valid config still cannot be discovered, report the discovery
failure and ask the user to start a new task; do not change persistent
configuration, silently substitute a write-capable worker, or claim an advisor
was used.

The bundled default is resolved to an exact available Codex model slug with
medium reasoning. Persistent user configuration wins. Honor a per-task model
or reasoning override only when the spawn interface supports and confirms it;
otherwise explain that it was not applied and point the user to the
`advisor-setup` skill for a persistent change.

## Consult only at high-value moments

Orient first by reading the request and minimum relevant evidence. Consult at:

1. **Plan:** before substantive work when the approach, requirements, or risks
   are non-obvious.
2. **Recovery:** when errors repeat, evidence conflicts, or the approach may
   need to change.
3. **Review:** after the deliverable is durable and local checks pass, before
   declaring difficult work complete.

Skip this workflow for routine edits, mechanical work, simple questions, and
changes whose next step and verification are direct. Default to plan and review;
allow one reconcile call when new evidence creates a material disagreement.
Use at most two advisor calls by default: one plan call and one final-review
call. Allow one third call only for material recovery or reconciliation; do not
add calls for routine work.

## Start once, then send deltas

For a genuinely new logical task with no advisor previously created, create one
initial advisor and retain it in the root task context. Reuse it across ordinary
turns. For later calls, send only changed requirements, new evidence, test
results, decisions, and the new question.
Do not resend unchanged constraints or background. Include the full constraints
only in the initial request or when rehydrating a replacement thread; later
deltas should mention constraints only when they changed.

On resume failure, retry the same advisor once; a transient failure is not proof
of loss. Create one replacement only after verified loss of the initial advisor
and only if no replacement has previously been created for this logical task.
Rehydrate it with a compact summary of the objective, constraints, affected
files, decisions, evidence, prior advice, and open question. If loss cannot be
verified, do not spawn; continue independently and disclose the limitation.

## Ask one focused question

Use this shape:

```text
Objective: <user outcome>
Decision needed: <one exact question>
Current executor view: <plan or hypothesis>
Evidence: <relevant files, behavior, logs, tests, measurements>
Constraints: <safety, compatibility, scope, performance, user requirements>
Uncertainty: <assumptions or low-confidence points>

Challenge the current view, identify hidden risks, recommend the smallest robust
next step, and give concrete verification. Return the configured advisor response
format only.
```

For an independent review, send the artifact and requirements without leaking
the executor's intended verdict.

## Integrate the advice

1. Compare it with user requirements and primary evidence.
2. Separate confirmed facts from hypotheses and preferences.
3. Accept only changes that improve correctness, safety, simplicity, or
   verification.
4. When advice conflicts with evidence, gather the cheapest decisive evidence
   and use the single reconcile call.
5. Execute all state-changing work from the root task and give the user the
   integrated result, not the advisor transcript.

If the advisor fails, times out, or remains low quality after one focused
follow-up, continue independently and disclose the limitation when material.

## Preserve the read-only boundary

The advisor may inspect files, diffs, logs, and test output and recommend
changes or checks. It must not edit files, run state-changing commands, commit,
publish, contact external systems, spawn agents, or answer the user directly.

The agent file requests a read-only sandbox, but live parent permission
overrides can take precedence. Enforce the behavioral boundary too. If the
advisor attempts a state change, stop it and disregard the attempted mutation.
