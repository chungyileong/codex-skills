#!/usr/bin/env python3
"""Install or adjust the Executor Advisor custom-agent file."""

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "advisor.toml"
SETTING_RE = r"(?m)^[ \t]*{key}[ \t]*=[^\n]*(?:\n|$)"


def advisor_path():
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "agents" / "advisor.toml"


def set_setting(text, key, value):
    instructions = re.search(r"(?m)^developer_instructions[ \t]*=", text)
    split = instructions.start() if instructions else len(text)
    header, body = text[:split], text[split:]
    pattern = re.compile(SETTING_RE.format(key=re.escape(key)))
    header = pattern.sub("", header)
    if value is None:
        return header + body

    line = f"{key} = {json.dumps(value)}\n"
    marker = re.search(r"(?m)^sandbox_mode[ \t]*=", header)
    if marker:
        header = header[: marker.start()] + line + header[marker.start() :]
    else:
        header = header.rstrip() + "\n" + line
    return header + body


def setting(text, key):
    instructions = re.search(r"(?m)^developer_instructions[ \t]*=", text)
    header = text[: instructions.start()] if instructions else text
    match = re.search(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*(.+)$", header)
    return match.group(1).strip() if match else "inherited"


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".advisor-", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def print_status(path, text=None):
    if text is None and path.exists():
        text = path.read_text()
    print(f"path: {path}")
    print(f"installed: {'yes' if text is not None else 'no'}")
    if text is not None:
        print(f"model: {setting(text, 'model')}")
        print(f"reasoning: {setting(text, 'model_reasoning_effort')}")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true", help="show the installed advisor settings")
    parser.add_argument("--reset", action="store_true", help="replace the installed file with bundled defaults")

    model = parser.add_mutually_exclusive_group()
    model.add_argument("--model", help="set a persistent advisor model")
    model.add_argument("--inherit-model", action="store_true", help="inherit model selection from the parent task")

    reasoning = parser.add_mutually_exclusive_group()
    reasoning.add_argument(
        "--reasoning",
        choices=("ultra", "max", "xhigh", "high", "medium", "low", "minimal", "none"),
        help="set persistent advisor reasoning effort",
    )
    reasoning.add_argument("--inherit-reasoning", action="store_true", help="inherit reasoning effort from the parent task")
    args = parser.parse_args()
    if args.status and any((args.reset, args.model, args.inherit_model, args.reasoning, args.inherit_reasoning)):
        parser.error("--status cannot be combined with configuration changes")
    if args.model is not None and not args.model.strip():
        parser.error("--model cannot be empty")
    return args


def main():
    args = parse_args()
    target = advisor_path()

    if args.status:
        print_status(target)
        return

    existed = target.exists()
    current = target.read_text() if existed else None
    text = TEMPLATE.read_text() if args.reset or current is None else current

    if args.model is not None:
        text = set_setting(text, "model", args.model.strip())
    elif args.inherit_model:
        text = set_setting(text, "model", None)

    if args.reasoning is not None:
        text = set_setting(text, "model_reasoning_effort", args.reasoning)
    elif args.inherit_reasoning:
        text = set_setting(text, "model_reasoning_effort", None)

    changed = current != text
    if changed:
        if args.reset and existed:
            backup = target.with_name("advisor.toml.bak")
            shutil.copy2(target, backup)
            print(f"backup: {backup}")
        write_atomic(target, text)

    print(f"changed: {'yes' if changed else 'no'}")
    print_status(target, text)


if __name__ == "__main__":
    main()
