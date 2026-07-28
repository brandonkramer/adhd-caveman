#!/usr/bin/env python3
"""Append/remove adhd-caveman marker block in OpenClaw SOUL.md."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIPPET = (ROOT / "docs" / "openclaw-SOUL.snippet.md").read_text(encoding="utf-8").strip() + "\n"
BEGIN = "<!-- ADHD-CAVEMAN:BEGIN -->"
END = "<!-- ADHD-CAVEMAN:END -->"


def default_soul() -> Path:
    return Path.home() / ".openclaw" / "workspace" / "SOUL.md"


def strip_block(text: str) -> str:
    out = text
    while BEGIN in out and END in out:
        b = out.index(BEGIN)
        e = out.index(END, b) + len(END)
        out = (out[:b] + out[e:]).strip() + ("\n" if out[e:].strip() or out[:b].strip() else "")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--soul", type=Path, default=None)
    p.add_argument("--uninstall", action="store_true")
    args = p.parse_args()
    soul = args.soul or default_soul()
    soul.parent.mkdir(parents=True, exist_ok=True)
    existing = soul.read_text(encoding="utf-8") if soul.is_file() else ""
    cleaned = strip_block(existing)
    if args.uninstall:
        soul.write_text(cleaned, encoding="utf-8")
        # also copy skill into openclaw workspace skills if present
        print(f"removed adhd-caveman block from {soul}")
        return 0
    if BEGIN in cleaned and END in cleaned:
        print(f"already present in {soul}")
        return 0
    skill_src = ROOT / "skills" / "adhd-caveman" / "SKILL.md"
    skill_dst = soul.parent / "skills" / "adhd-caveman" / "SKILL.md"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    skill_dst.write_text(skill_src.read_text(encoding="utf-8"), encoding="utf-8")
    next_text = (cleaned.rstrip() + "\n\n" + SNIPPET) if cleaned.strip() else SNIPPET
    soul.write_text(next_text, encoding="utf-8")
    print(f"appended block → {soul}")
    print(f"copied skill → {skill_dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
