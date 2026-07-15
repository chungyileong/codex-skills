#!/usr/bin/env python3
"""Install or adjust the Executor Advisor custom-agent file."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "advisor.toml"
REQUIRED_KEYS = {
    "name",
    "description",
    "sandbox_mode",
    "developer_instructions",
}
OPTIONAL_STRING_KEYS = {"model", "model_reasoning_effort"}
REASONING_EFFORTS = {"ultra", "max", "xhigh", "high", "medium", "low", "minimal", "none"}
SETTING_RE = r"(?m)^[ \t]*{key}[ \t]*=[^\n]*(?:\n|$)"


def advisor_path():
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "agents" / "advisor.toml"


def available_models():
    try:
        result = subprocess.run(
            ["codex", "debug", "models"], check=True, capture_output=True, text=True
        )
        return json.loads(result.stdout)["models"]
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as error:
        raise SystemExit(f"could not list Codex models: {error}") from error


def resolve_model(model):
    requested = model.strip()
    for candidate in available_models():
        slug = candidate["slug"]
        normalized = re.sub(r"[\s_-]+", "-", requested.casefold())
        if requested == slug or normalized == re.sub(r"[\s_-]+", "-", slug.casefold()) or requested.casefold() == candidate.get("display_name", "").casefold():
            return slug
    raise SystemExit(f"model is not available in Codex: {requested}")


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


def validation_errors(text):
    try:
        config = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [f"invalid TOML: {error}"]

    errors = []
    missing = sorted(REQUIRED_KEYS - config.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    wrong_types = sorted(
        key
        for key in REQUIRED_KEYS | OPTIONAL_STRING_KEYS
        if key in config and not isinstance(config[key], str)
    )
    if wrong_types:
        errors.append(f"fields must be strings: {', '.join(wrong_types)}")

    if config.get("name") != "advisor":
        errors.append('name must be "advisor"')
    if config.get("sandbox_mode") != "read-only":
        errors.append('sandbox_mode must be "read-only"')

    model = config.get("model")
    if isinstance(model, str) and model:
        try:
            models = available_models()
        except SystemExit as error:
            errors.append(str(error))
        else:
            supported = {candidate.get("slug") for candidate in models}
            if model not in supported:
                errors.append(f"model is not available in Codex: {model}")
    elif "model" in config and not model:
        errors.append("model must be a non-empty string")

    reasoning = config.get("model_reasoning_effort")
    if isinstance(reasoning, str) and reasoning not in REASONING_EFFORTS:
        errors.append(f"unsupported reasoning effort: {reasoning}")
    return errors


def print_status(path, text=None):
    if text is None and path.exists():
        text = path.read_text()
    print(f"path: {path}")
    print(f"installed: {'yes' if text is not None else 'no'}")
    if text is None:
        print("validation: missing")
        return ["advisor config is missing"]

    errors = validation_errors(text)
    print(f"validation: {'valid' if not errors else 'invalid'}")
    for error in errors:
        print(f"error: {error}")
    print(f"model: {setting(text, 'model')}")
    print(f"reasoning: {setting(text, 'model_reasoning_effort')}")
    return errors


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
        if print_status(target):
            raise SystemExit(1)
        return

    existed = target.exists()
    current = target.read_text() if existed else None
    if existed and not args.reset and not any((args.model, args.inherit_model, args.reasoning, args.inherit_reasoning)):
        errors = validation_errors(current)
        if errors:
            raise SystemExit("existing advisor config is invalid; use --reset to repair it")
    text = TEMPLATE.read_text() if args.reset or current is None else current

    if args.reset or current is None:
        text = set_setting(text, "model", resolve_model(setting(text, "model").strip('"')))

    if args.model is not None:
        text = set_setting(text, "model", resolve_model(args.model))
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
