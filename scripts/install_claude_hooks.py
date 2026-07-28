#!/usr/bin/env python3
"""Wire adhd-caveman hooks into ~/.claude/settings.json (caveman pattern).

Plugin SessionStart often runs but Claude interactive mode drops plugin
additionalContext. User-level settings.json hooks still inject. This copies
hooks+skill to ~/.claude/adhd-caveman/ and registers:

  - SessionStart     → session-start.sh (full skill, JSON additionalContext)
  - UserPromptSubmit → prompt-submit.sh (per-turn reinforce)
  - PreCompact       → precompact.sh (re-assert after compression)
  - statusLine       → statusline.sh (only if none configured)

Usage:
  python3 scripts/install_claude_hooks.py
  python3 scripts/install_claude_hooks.py --uninstall
  python3 scripts/install_claude_hooks.py --with-statusline
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "adhd-caveman"
HOOK_FILES = (
    "common.sh",
    "session-start.sh",
    "prompt-submit.sh",
    "precompact.sh",
    "statusline.sh",
    "hooks.json",
)


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
    for name in HOOK_FILES:
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


def hook_entry(command: str, status: str, matcher: str | None = None) -> dict:
    entry: dict = {
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": 5,
                "statusMessage": status,
            }
        ]
    }
    if matcher:
        entry["matcher"] = matcher
    return entry


def wire(settings: dict, dest: Path, with_statusline: bool) -> dict:
    hooks = settings.setdefault("hooks", {})
    start = strip_marker(list(hooks.get("SessionStart") or []))
    prompt = strip_marker(list(hooks.get("UserPromptSubmit") or []))
    compact = strip_marker(list(hooks.get("PreCompact") or []))

    start.append(
        hook_entry(
            f'sh "{dest / "hooks" / "session-start.sh"}"',
            "adhd-caveman session start…",
            matcher="startup|resume|clear|compact",
        )
    )
    prompt.append(
        hook_entry(
            f'sh "{dest / "hooks" / "prompt-submit.sh"}"',
            "adhd-caveman prompt reinforce…",
        )
    )
    compact.append(
        hook_entry(
            f'sh "{dest / "hooks" / "precompact.sh"}"',
            "adhd-caveman precompact…",
        )
    )
    hooks["SessionStart"] = start
    hooks["UserPromptSubmit"] = prompt
    hooks["PreCompact"] = compact
    settings["hooks"] = hooks

    if with_statusline:
        badge_cmd = f'bash "{dest / "hooks" / "statusline.sh"}"'
        existing = settings.get("statusLine")
        if not existing:
            settings["statusLine"] = {"type": "command", "command": badge_cmd}
        # If user already has a statusLine, leave it; compose into their
        # script manually (see README) — do not clobber custom lines.
    return settings


def unwire(settings: dict) -> dict:
    hooks = settings.get("hooks") or {}
    for key in ("SessionStart", "UserPromptSubmit", "PreCompact"):
        if key in hooks:
            hooks[key] = strip_marker(list(hooks[key]))
            if not hooks[key]:
                del hooks[key]
    if hooks:
        settings["hooks"] = hooks
    elif "hooks" in settings:
        del settings["hooks"]
    sl = settings.get("statusLine")
    if isinstance(sl, dict) and MARKER in (sl.get("command") or ""):
        del settings["statusLine"]
    elif isinstance(sl, str) and MARKER in sl:
        del settings["statusLine"]
    return settings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--uninstall", action="store_true")
    p.add_argument("--with-statusline", action="store_true")
    p.add_argument("--settings", type=Path, default=None)
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
    data = wire(data, dest, with_statusline=args.with_statusline)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"synced files → {dest}")
    print(
        "wired SessionStart + UserPromptSubmit + PreCompact → "
        f"{settings_file}"
    )
    if args.with_statusline:
        print("statusLine: configured (or left existing alone)")
    print("Restart Claude Code (new session) so hooks reload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
