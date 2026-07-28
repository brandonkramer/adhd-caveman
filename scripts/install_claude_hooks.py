#!/usr/bin/env python3
"""Wire adhd-caveman hooks into ~/.claude/settings.json (caveman pattern).

Plugin SessionStart often runs but Claude interactive mode drops plugin
additionalContext. User-level settings.json hooks still inject. This copies
hooks+skill to a stable dir under ~/.claude/adhd-caveman/ and registers:

  - SessionStart  → session-start.sh (full skill body)
  - UserPromptSubmit → prompt-submit.sh (short per-turn reinforce)

Usage:
  python3 scripts/install_claude_hooks.py
  python3 scripts/install_claude_hooks.py --uninstall
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "adhd-caveman"


def claude_dir() -> Path:
    return Path.home() / ".claude"


def install_dir() -> Path:
    return claude_dir() / "adhd-caveman"


def settings_path() -> Path:
    return claude_dir() / "settings.json"


def sync_files(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    hooks = dest / "hooks"
    skills = dest / "skills" / "adhd-caveman"
    hooks.mkdir(parents=True, exist_ok=True)
    skills.mkdir(parents=True, exist_ok=True)
    for name in ("session-start.sh", "prompt-submit.sh", "hooks.json"):
        src = ROOT / "hooks" / name
        if not src.is_file():
            raise SystemExit(f"missing {src}")
        target = hooks / name
        shutil.copy2(src, target)
        if name.endswith(".sh"):
            target.chmod(0o755)
    skill = ROOT / "skills" / "adhd-caveman" / "SKILL.md"
    if not skill.is_file():
        raise SystemExit(f"missing {skill}")
    shutil.copy2(skill, skills / "SKILL.md")


def load_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def has_marker(entry: dict) -> bool:
    for h in entry.get("hooks") or []:
        cmd = h.get("command") or ""
        if MARKER in cmd:
            return True
    return False


def strip_marker(hooks_list: list) -> list:
    return [e for e in hooks_list if not has_marker(e)]


def wire(settings: dict, dest: Path) -> dict:
    hooks = settings.setdefault("hooks", {})
    start = strip_marker(list(hooks.get("SessionStart") or []))
    prompt = strip_marker(list(hooks.get("UserPromptSubmit") or []))

    session_cmd = f'sh "{dest / "hooks" / "session-start.sh"}"'
    prompt_cmd = f'sh "{dest / "hooks" / "prompt-submit.sh"}"'

    start.append(
        {
            "matcher": "startup|resume|clear|compact",
            "hooks": [
                {
                    "type": "command",
                    "command": session_cmd,
                    "timeout": 5,
                    "statusMessage": "adhd-caveman session start…",
                }
            ],
        }
    )
    prompt.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": prompt_cmd,
                    "timeout": 5,
                    "statusMessage": "adhd-caveman prompt reinforce…",
                }
            ],
        }
    )
    hooks["SessionStart"] = start
    hooks["UserPromptSubmit"] = prompt
    settings["hooks"] = hooks
    return settings


def unwire(settings: dict) -> dict:
    hooks = settings.get("hooks") or {}
    if "SessionStart" in hooks:
        hooks["SessionStart"] = strip_marker(list(hooks["SessionStart"]))
        if not hooks["SessionStart"]:
            del hooks["SessionStart"]
    if "UserPromptSubmit" in hooks:
        hooks["UserPromptSubmit"] = strip_marker(list(hooks["UserPromptSubmit"]))
        if not hooks["UserPromptSubmit"]:
            del hooks["UserPromptSubmit"]
    if hooks:
        settings["hooks"] = hooks
    elif "hooks" in settings:
        del settings["hooks"]
    return settings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--uninstall", action="store_true")
    p.add_argument(
        "--settings",
        type=Path,
        default=None,
        help="Override settings.json path (default ~/.claude/settings.json)",
    )
    args = p.parse_args()
    dest = install_dir()
    settings_file = args.settings or settings_path()

    if args.uninstall:
        data = load_settings(settings_file)
        data = unwire(data)
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        if settings_file.is_file():
            shutil.copy2(settings_file, settings_file.with_suffix(".json.bak"))
        settings_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        if dest.is_dir():
            shutil.rmtree(dest)
        print(f"uninstalled adhd-caveman hooks from {settings_file}")
        print(f"removed {dest}")
        return 0

    sync_files(dest)
    data = load_settings(settings_file)
    if settings_file.is_file():
        shutil.copy2(settings_file, settings_file.with_suffix(".json.bak"))
    data = wire(data, dest)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"synced files → {dest}")
    print(f"wired SessionStart + UserPromptSubmit → {settings_file}")
    print("Restart Claude Code (new session) so hooks reload.")
    print("Note: plugin may still fire SessionStart (flag file); settings inject is what reaches the model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
