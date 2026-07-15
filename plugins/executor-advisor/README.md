# Executor Advisor

Use one read-only advisor for high-value planning and final review while the
main Codex task remains the only executor.

The plugin includes the Executor Advisor workflow and an `advisor-setup` skill
that manages the custom agent configuration safely.

## Install

Add this repository's marketplace once, then install the plugin:

```sh
codex plugin marketplace add chungyileong/codex-skills
codex plugin add executor-advisor@chungyileong-codex-skills
```

Start a new Codex task and ask:

```text
Set up my default advisor.
```

The setup skill creates `~/.codex/agents/advisor.toml` without replacing an
existing file. Start one more new task when prompted so Codex can discover the
new custom agent.

Then use it naturally:

```text
Use Executor Advisor for this architecture review.
```

## Configure the advisor

Setup resolves the default model to an exact slug from `codex debug models`.
Ask Codex to change it:

```text
Set my advisor model to GPT-5.6-Sol and reasoning to high.
Make my advisor inherit the task model and reasoning.
Show my advisor configuration.
Reset my advisor to the plugin defaults.
```

Configuration changes preserve the rest of your agent file. Reset creates
`advisor.toml.bak` first.

If the requested model is unavailable for your account, choose one from
`codex debug models` or ask the setup skill to inherit the task model and
reasoning.

## Update

```sh
codex plugin marketplace upgrade chungyileong-codex-skills
codex plugin add executor-advisor@chungyileong-codex-skills
```

Plugin updates never overwrite your personal `~/.codex/agents/advisor.toml`.
Ask Codex to reset the advisor only when you want the latest bundled defaults.
