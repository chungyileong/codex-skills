# Executor Advisor for Codex

Use one read-only advisor for high-value planning and final review while the
main Codex task remains the only executor.

This is a plugin, not a standalone skill. The old `$skill-installer` flow could
copy the workflow but could not register `advisor.toml` in
`~/.codex/agents/`. The plugin includes an `advisor-setup` skill that handles
that separate Codex configuration safely.

## Install

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
Use Executor Advisor for this migration.
```

## Configure the advisor

The default uses `gpt-5.6` with medium reasoning. Ask Codex to change it:

```text
Set my advisor model to gpt-5.6 and reasoning to high.
Make my advisor inherit the task model and reasoning.
Show my advisor configuration.
Reset my advisor to the plugin defaults.
```

Configuration changes preserve the rest of your agent file. Reset creates
`advisor.toml.bak` first.

If `gpt-5.6` is unavailable for your account, choose an available model or ask
the setup skill to inherit the task model and reasoning.

## Migrate from the old skill install

If you previously used `$skill-installer`, remove or move
`~/.codex/skills/executor-advisor` after installing this plugin so Codex does
not show two copies of the workflow. Keep `~/.codex/agents/advisor.toml`; setup
will preserve it.

## Update

```sh
codex plugin marketplace upgrade chungyileong-codex-skills
codex plugin add executor-advisor@chungyileong-codex-skills
```

Plugin updates never overwrite your personal `~/.codex/agents/advisor.toml`.
Ask Codex to reset the advisor only when you want the latest bundled defaults.
