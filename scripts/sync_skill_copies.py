#!/usr/bin/env python3
"""Copy canonical skill → Cursor skill path."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "adhd-caveman" / "SKILL.md"
DST = ROOT / ".cursor" / "skills" / "adhd-caveman" / "SKILL.md"


def main() -> int:
    if not SRC.is_file():
        print(f"missing canonical skill: {SRC}")
        return 1
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DST)
    print(f"synced {SRC.relative_to(ROOT)} → {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
