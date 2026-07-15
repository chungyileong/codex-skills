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
