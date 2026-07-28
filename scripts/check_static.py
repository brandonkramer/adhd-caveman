#!/usr/bin/env python3
"""Deterministic checks on voice surfaces + fixture responses.

Exit 0 = PASS. Exit 1 = FAIL. Exit 2 = INCONCLUSIVE (missing inputs).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "adhd-caveman" / "SKILL.md"
CURSOR_SKILL = ROOT / ".cursor" / "skills" / "adhd-caveman" / "SKILL.md"
HOOK_SH = ROOT / "hooks" / "session-start.sh"
HOOK_PROMPT = ROOT / "hooks" / "prompt-submit.sh"
HOOK_JSON = ROOT / "hooks" / "hooks.json"
CODEX_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
CASES = ROOT / "evals" / "cases.jsonl"
FIXTURES = ROOT / "evals" / "fixtures" / "static_responses.jsonl"

FORBIDDEN_IN_RESPONSES = [
    r"(?i)^sure[!.,]?\s",
    r"(?i)^great question",
    r"(?i)hope this helps",
    r"(?i)let me know if you (need|want)",
    r"(?i)^i'?d be happy to",
    r"(?i)\buh oh\b",
    r"(?i)there seems to be (a |an )?problem",
]

REQUIRED_SKILL_PHRASES = [
    "Shape (ADHD",
    "Mouth (caveman",
    "Conflict rule",
    "full",
    "SessionStart",
]

REQUIRED_HOOK_MARKERS = [
    "adhd-caveman-off",
    "SKILL.md",
    "ADHD-CAVEMAN MODE ACTIVE",
    "PLUGIN_ROOT",
]


def load_cases() -> list[dict]:
    rows = []
    for line in CASES.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def check_voice_files() -> list[str]:
    errors: list[str] = []
    if not SKILL.is_file():
        errors.append(f"missing skill: {SKILL.relative_to(ROOT)}")
        return errors
    text = SKILL.read_text(encoding="utf-8")
    for phrase in REQUIRED_SKILL_PHRASES:
        if phrase not in text:
            errors.append(f"SKILL.md: missing required phrase {phrase!r}")
    # lean skill body (frontmatter + rules); warn via fail over 12KB
    if SKILL.stat().st_size > 12_288:
        errors.append(f"SKILL.md too large: {SKILL.stat().st_size} bytes > 12288")

    if not CURSOR_SKILL.is_file():
        errors.append(f"missing Cursor skill copy: {CURSOR_SKILL.relative_to(ROOT)}")
    elif SKILL.read_text(encoding="utf-8") != CURSOR_SKILL.read_text(encoding="utf-8"):
        errors.append("Cursor skill copy out of sync; run scripts/sync_skill_copies.py")

    if (ROOT / "AGENTS.md").exists():
        errors.append("AGENTS.md must not exist — SessionStart hook is always-on")
    if (ROOT / "CLAUDE.md").exists():
        errors.append("CLAUDE.md must not exist — SessionStart hook is always-on")

    if not HOOK_SH.is_file():
        errors.append("missing hooks/session-start.sh")
    else:
        hook = HOOK_SH.read_text(encoding="utf-8")
        for marker in REQUIRED_HOOK_MARKERS:
            if marker not in hook:
                errors.append(f"session-start.sh: missing {marker!r}")
        if not HOOK_SH.stat().st_mode & 0o111:
            errors.append("hooks/session-start.sh is not executable")

    if not HOOK_PROMPT.is_file():
        errors.append("missing hooks/prompt-submit.sh")
    elif not HOOK_PROMPT.stat().st_mode & 0o111:
        errors.append("hooks/prompt-submit.sh is not executable")
    else:
        prompt_hook = HOOK_PROMPT.read_text(encoding="utf-8")
        if "UserPromptSubmit" not in prompt_hook:
            errors.append("prompt-submit.sh: missing UserPromptSubmit marker")
        if "additionalContext" not in prompt_hook:
            errors.append("prompt-submit.sh: missing additionalContext")

    if not HOOK_JSON.is_file():
        errors.append("missing hooks/hooks.json")
    else:
        data = json.loads(HOOK_JSON.read_text(encoding="utf-8"))
        try:
            cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        except (KeyError, IndexError, TypeError):
            errors.append("hooks.json: SessionStart command missing")
        else:
            if "session-start.sh" not in cmd:
                errors.append("hooks.json: SessionStart must invoke session-start.sh")
        try:
            pcmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        except (KeyError, IndexError, TypeError):
            errors.append("hooks.json: UserPromptSubmit command missing")
        else:
            if "prompt-submit.sh" not in pcmd:
                errors.append("hooks.json: UserPromptSubmit must invoke prompt-submit.sh")

    if not CLAUDE_PLUGIN.is_file():
        errors.append("missing .claude-plugin/plugin.json")
    else:
        claude = json.loads(CLAUDE_PLUGIN.read_text(encoding="utf-8"))
        if claude.get("name") != "adhd-caveman":
            errors.append(".claude-plugin/plugin.json: name must be adhd-caveman")

    if not CODEX_PLUGIN.is_file():
        errors.append("missing .codex-plugin/plugin.json")
    else:
        codex = json.loads(CODEX_PLUGIN.read_text(encoding="utf-8"))
        if codex.get("name") != "adhd-caveman":
            errors.append(".codex-plugin/plugin.json: name must be adhd-caveman")
        if codex.get("skills") != "./skills/":
            errors.append(".codex-plugin/plugin.json: skills must be ./skills/")
        if codex.get("hooks") not in ("./hooks/hooks.json", "hooks/hooks.json"):
            errors.append(".codex-plugin/plugin.json: hooks must point at hooks.json")
    return errors


def check_cases() -> list[str]:
    errors: list[str] = []
    if not CASES.is_file():
        return [f"missing {CASES.relative_to(ROOT)}"]
    rows = load_cases()
    if len(rows) < 10:
        errors.append(f"need ≥10 cases, found {len(rows)}")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate case ids")
    required = {
        "multi-step-progress",
        "destructive-action",
        "structure-vs-ultra",
        "react-rerender",
        "medical-boundary",
    }
    missing = required - set(ids)
    if missing:
        errors.append(f"missing required cases: {sorted(missing)}")
    for r in rows:
        for key in ("id", "prompt", "criteria"):
            if key not in r:
                errors.append(f"case missing {key}: {r.get('id', '?')}")
    return errors


def check_fixtures() -> list[str]:
    if not FIXTURES.is_file():
        return []
    errors: list[str] = []
    for line in FIXTURES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row["text"]
        expect = row["expect"]
        hit = any(re.search(p, text) for p in FORBIDDEN_IN_RESPONSES)
        if expect == "fail" and not hit:
            errors.append(f"fixture {row['id']}: expected forbidden hit, none found")
        if expect == "pass" and hit:
            errors.append(f"fixture {row['id']}: unexpected forbidden hit")
    return errors


def check_hook_smoke() -> list[str]:
    import os
    import subprocess
    import tempfile

    errors: list[str] = []
    if not HOOK_SH.is_file():
        return ["hook smoke skipped: missing script"]

    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        env["CLAUDE_CONFIG_DIR"] = tmp
        proc = subprocess.run(
            ["sh", str(HOOK_SH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            errors.append(f"hook smoke: exit {proc.returncode}")
        out = proc.stdout
        if "ADHD-CAVEMAN MODE ACTIVE" not in out:
            errors.append("hook smoke: missing ACTIVE banner")
        if "Shape (ADHD" not in out:
            errors.append("hook smoke: skill body not injected")
        off = Path(tmp) / ".adhd-caveman-off"
        off.write_text("", encoding="utf-8")
        proc2 = subprocess.run(
            ["sh", str(HOOK_SH)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if proc2.returncode != 0:
            errors.append(f"hook smoke off-flag: exit {proc2.returncode}")
        if proc2.stdout.strip():
            errors.append("hook smoke off-flag: expected empty stdout")

        # Codex-shaped env: PLUGIN_ROOT + CODEX_HOME
        env_codex = os.environ.copy()
        env_codex["PLUGIN_ROOT"] = str(ROOT)
        env_codex["CODEX_HOME"] = tmp
        env_codex.pop("CLAUDE_PLUGIN_ROOT", None)
        env_codex.pop("CLAUDE_CONFIG_DIR", None)
        off.unlink(missing_ok=True)
        proc3 = subprocess.run(
            ["sh", str(HOOK_SH)],
            capture_output=True,
            text=True,
            env=env_codex,
            check=False,
        )
        if proc3.returncode != 0 or "ADHD-CAVEMAN MODE ACTIVE" not in proc3.stdout:
            errors.append("hook smoke: Codex PLUGIN_ROOT/CODEX_HOME path failed")

        # UserPromptSubmit reinforcement (active flag present)
        if HOOK_PROMPT.is_file():
            (Path(tmp) / ".adhd-caveman-active").write_text("full\n", encoding="utf-8")
            proc4 = subprocess.run(
                ["sh", str(HOOK_PROMPT)],
                input="please continue",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            if proc4.returncode != 0:
                errors.append(f"prompt-submit smoke: exit {proc4.returncode}")
            elif "additionalContext" not in proc4.stdout or "ADHD-CAVEMAN" not in proc4.stdout:
                errors.append("prompt-submit smoke: missing reinforcement JSON")
            proc5 = subprocess.run(
                ["sh", str(HOOK_PROMPT)],
                input="normal mode please",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            if proc5.returncode != 0:
                errors.append(f"prompt-submit off smoke: exit {proc5.returncode}")
            elif "off for this session" not in proc5.stdout:
                errors.append("prompt-submit off smoke: expected off confirmation")
    return errors


def main() -> int:
    if not CASES.is_file():
        print("INCONCLUSIVE: cases.jsonl missing")
        return 2
    errors: list[str] = []
    errors.extend(check_voice_files())
    errors.extend(check_cases())
    errors.extend(check_fixtures())
    errors.extend(check_hook_smoke())
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    print(f"  skill: {SKILL.relative_to(ROOT)} ({SKILL.stat().st_size} bytes)")
    print(f"  hook: {HOOK_SH.relative_to(ROOT)}")
    print(f"  cases: {len(load_cases())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
