---
name: executor-advisor
description: Coordinate a single-controller Executor-Advisor workflow in Codex. Keep the root thread as the sole executor and consult one persistent, read-only `advisor` custom subagent at high-value planning, stuck, and final-review checkpoints. Accept per-task advisor model and reasoning requests in the invocation. Use for long-horizon or high-risk coding, research, architecture, debugging, migration, concurrency, security, performance, and review tasks where a second opinion can improve the result; skip routine or directly verifiable work.
---

# Executor-Advisor

## Install

Install the files into separate locations:

```sh
mkdir -p ~/.codex/skills/executor-advisor ~/.codex/agents
cp SKILL.md ~/.codex/skills/executor-advisor/SKILL.md
cp agents/advisor.toml ~/.codex/agents/advisor.toml
```

`SKILL.md` belongs in the skill directory. `advisor.toml` belongs in the
global agent directory so Codex can discover the custom `advisor` agent type.
Restart Codex after installing or updating either file.

## Keep one controller

- Keep the current root thread as the executor. It owns the user conversation,
  decisions, edits, commands, tests, and final response.
- Use one custom `advisor` subagent for analysis and criticism only.
- Reuse the same advisor thread throughout the task. Never create advisor
  descendants or an advisor debate loop.
- Treat advice as evidence. Verify it before acting.

## Check the prerequisite

Use the custom agent type `advisor` from
`~/.codex/agents/advisor.toml`.

Verify that the `advisor` agent type is available before using this workflow.
By default, use the strongest available advisor model with `medium` reasoning.
If `advisor` is unavailable, do not silently substitute a write-capable worker.
Continue executor-only. When the user explicitly invoked this skill, say that
the advisor was unavailable and point to the Install section; for implicit use,
mention it only when it materially lowers confidence. Do not claim a model,
reasoning level, sandbox, or agent type is active unless the current session
confirms it.

## Resolve per-task settings

Treat an explicit invocation such as this as a per-task advisor override:

```text
$executor-advisor use gpt-5.6-sol with reasoning medium as advisor
```

Apply settings in this order:

1. Model and reasoning explicitly requested by the user.
2. Otherwise, the strongest advisor model available to the current user with
   `medium` reasoning.

Use runtime per-spawn settings when available; otherwise steer the new advisor
in its spawn instruction with the exact requested model and reasoning effort.
Never rewrite persistent configuration just to satisfy one task.

When using the default, request the runtime's highest-capability available model,
not the fastest or cheapest model. Do not invent a model ID when availability
cannot be inspected.

Reuse an existing advisor only when its effective settings match the request.
Otherwise spawn one replacement for the task. If the runtime rejects or cannot
confirm the requested settings, say so and continue executor-only; never silently
downgrade or claim the override succeeded.

## Consult only at high-value moments

Orient first: read the request and the minimum relevant files or evidence. Then
consult at any of these checkpoints:

1. **Plan:** before substantive work when the approach, requirements, or risks
   are non-obvious.
2. **Recovery:** when errors repeat, evidence conflicts, or the approach may need
   to change.
3. **Review:** after making the deliverable durable and running local checks,
   before declaring difficult work complete.

Skip consultation for routine edits, mechanical work, simple questions, and
changes whose next step and verification are direct. Default to two calls per
task (plan and review); allow one reconcile call when new evidence creates a
material disagreement.

## Start once, then send deltas

After resolving settings, check existing agent threads and reuse `advisor` when
it already exists with matching settings. Otherwise spawn one custom `advisor`
agent and give it the task context, requested settings, and focused request
below. Keep the thread after its turn finishes; an idle or done turn is still
reusable.

For later calls, send only changed requirements, new evidence, test results,
decisions, and the new question. If the thread is no longer addressable, create
one replacement and rehydrate it with a compact summary of the objective,
constraints, affected files, decisions, evidence, prior advice, and open
question.

## Ask a focused question

Use this compact request shape:

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

Send only context that can affect the decision. For an independent review, send
the artifact and requirements without leaking the executor's intended verdict.

## Integrate the advice

1. Compare the advice with user requirements and primary evidence.
2. Separate confirmed facts from hypotheses and preferences.
3. Accept only changes that improve correctness, safety, simplicity, or
   verification.
4. When advice conflicts with evidence, gather the cheapest decisive evidence
   and use the single reconcile call.
5. Execute all state-changing work from the root thread and give the user the
   integrated result, not the advisor transcript.

If the advisor fails, times out, or remains low quality after one focused
follow-up, continue independently. Do not repeatedly retry.

## Preserve the read-only boundary

The advisor may inspect files, diffs, logs, and test output and may recommend
changes or checks. It must not edit files, run state-changing commands, commit,
publish, contact external systems, spawn agents, or answer the user directly.

Configure the advisor with a read-only sandbox, but do not rely on the sandbox
alone: live parent permission overrides may take precedence. If the advisor
attempts a state change, stop it and disregard the attempted mutation.
