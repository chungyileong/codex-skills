---
name: advisor-setup
description: Install, inspect, update, or reset the Executor Advisor custom agent in Codex. Use when the user asks to set up the advisor, change its model or reasoning effort, inherit task settings, show advisor configuration, reset advisor defaults, or fix a missing `advisor` agent type.
---

# Advisor Setup

Use the bundled `scripts/configure_advisor.py` script. Resolve it relative to
this `SKILL.md`; never guess an installed plugin cache path.

## Map the request

- Set up or initialize: run the script with no options. It creates the default
  only when the target does not exist.
- Show or diagnose: run with `--status`.
- Set a persistent model: run with `--model <model>`. The script queries
  `codex debug models` and writes the catalog's exact `slug` (it also accepts a
  matching display name).
- Set persistent reasoning: run with `--reasoning <effort>`.
- Inherit the task model or reasoning: use `--inherit-model` or
  `--inherit-reasoning`.
- Reset to bundled defaults: run with `--reset`. Do this only when the user
  explicitly asks; it backs up the existing file first.

Combine model and reasoning options in one command when the user requests both.
If Codex cannot list models or the requested model is unavailable, stop without
writing the advisor file and report the error.
Do not edit the bundled template to customize one user.

After creating or changing the installed agent, tell the user to start a new
Codex task so custom-agent discovery uses the new configuration. If the script
reports no change, do not claim a restart is required.
