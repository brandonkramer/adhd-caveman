#!/usr/bin/env python3
"""Eval harness: validate / plan / run / score for adhd-caveman.

Real runs call an isolated CLI when available. Without a CLI, use
--fixture-dir for dry replay. Budget is tracked when the runner reports cost.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases.jsonl"
RUBRIC = ROOT / "evals" / "rubric.md"

WEIGHTS = {
    "correctness": 0.30,
    "actionability": 0.25,
    "structure": 0.15,
    "safety": 0.15,
    "concision": 0.15,
}


@dataclass
class Case:
    id: str
    prompt: str
    risk: str
    criteria: list[str]
    raw: dict


def load_cases() -> list[Case]:
    out: list[Case] = []
    for line in CASES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out.append(
            Case(
                id=row["id"],
                prompt=row["prompt"],
                risk=row.get("risk", "low"),
                criteria=list(row.get("criteria", [])),
                raw=row,
            )
        )
    return out


def cmd_validate(_: argparse.Namespace) -> int:
    if not CASES.is_file() or not RUBRIC.is_file():
        print("INCONCLUSIVE: missing cases or rubric")
        return 2
    cases = load_cases()
    ids = [c.id for c in cases]
    ok = True
    if len(ids) != len(set(ids)):
        print("FAIL: duplicate case ids")
        ok = False
    if len(cases) < 10:
        print(f"FAIL: need ≥10 cases, got {len(cases)}")
        ok = False
    for c in cases:
        if not c.prompt.strip() or not c.criteria:
            print(f"FAIL: incomplete case {c.id}")
            ok = False
    if ok:
        print(f"PASS: {len(cases)} cases, rubric present")
        return 0
    return 1


def cmd_plan(args: argparse.Namespace) -> int:
    cases = load_cases()
    n = len(cases) * args.trials * len(args.conditions)
    print(f"cases={len(cases)} trials={args.trials} conditions={args.conditions}")
    print(f"calls={n}")
    print(f"budget_usd={args.budget_usd}")
    print("conditions: " + ", ".join(args.conditions))
    return 0


def read_skill(path: Path | None) -> str:
    if path is None:
        return ""
    text = path.read_text(encoding="utf-8")
    # strip YAML front matter for injection as system text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def already_done(output: Path, key: tuple) -> bool:
    if not output.is_file():
        return False
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        k = (row["case_id"], row["trial"], row["condition"], row["runner"])
        if k == key:
            return True
    return False


def append_jsonl(output: Path, row: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_cursor(prompt: str, system: str, model: str | None) -> tuple[str, float | None]:
    bin_name = shutil.which("cursor") or shutil.which("agent")
    if not bin_name:
        raise RuntimeError("cursor/agent CLI not found")
    # Prefer non-interactive print mode; flags vary by install.
    cmd = [bin_name, "agent", "-p", "--force"]
    if model:
        cmd.extend(["--model", model])
    full = prompt if not system else f"SYSTEM:\n{system}\n\nUSER:\n{prompt}"
    env = os.environ.copy()
    # Reduce chance of picking up user always-on rules from other projects.
    env.pop("CURSOR_USER_RULES", None)
    proc = subprocess.run(
        cmd,
        input=full,
        text=True,
        capture_output=True,
        env=env,
        timeout=300,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cursor failed")
    return proc.stdout.strip(), None


def run_claude(prompt: str, system: str, model: str | None) -> tuple[str, float | None]:
    bin_name = shutil.which("claude")
    if not bin_name:
        raise RuntimeError("claude CLI not found")
    cmd = [
        bin_name,
        "-p",
        prompt,
        "--setting-sources",
        "",
        "--output-format",
        "text",
    ]
    if model:
        cmd.extend(["--model", model])
    else:
        cmd.extend(["--model", "claude-sonnet-4-20250514"])
    if system:
        cmd.extend(["--system-prompt", system])
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=300, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "claude failed")
    return proc.stdout.strip(), None


def run_codex(prompt: str, system: str, model: str | None) -> tuple[str, float | None]:
    bin_name = shutil.which("codex")
    if not bin_name:
        raise RuntimeError("codex CLI not found")
    full = prompt if not system else f"{system}\n\n{prompt}"
    cmd = [bin_name, "exec", "--ephemeral", "--skip-git-repo-check", full]
    if model:
        cmd.extend(["--model", model])
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=300, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "codex failed")
    return proc.stdout.strip(), None


def run_fixture(
    case_id: str, condition: str, fixture_dir: Path
) -> tuple[str, float | None]:
    path = fixture_dir / f"{condition}__{case_id}.txt"
    if not path.is_file():
        raise RuntimeError(f"missing fixture {path}")
    return path.read_text(encoding="utf-8").strip(), 0.0


RUNNERS = {
    "cursor": run_cursor,
    "claude": run_claude,
    "codex": run_codex,
}


def cmd_run(args: argparse.Namespace) -> int:
    cases = load_cases()
    if args.case:
        cases = [c for c in cases if c.id in args.case]
        if not cases:
            print("FAIL: no matching cases")
            return 1

    skill_text = read_skill(Path(args.condition_skill)) if args.condition_skill else ""
    spent = 0.0
    output = Path(args.output)
    runner = args.runner

    for condition in args.condition:
        system = skill_text if condition == "candidate" else ""
        if condition == "baseline" and args.baseline_system:
            system = Path(args.baseline_system).read_text(encoding="utf-8")
        for trial in range(1, args.trials + 1):
            for case in cases:
                key = (case.id, trial, condition, runner)
                if already_done(output, key):
                    print(f"skip {key}")
                    continue
                if spent >= args.budget_usd and not args.allow_unmetered:
                    print(f"STOP: budget ${args.budget_usd:.2f} exhausted (spent ${spent:.4f})")
                    return 1
                try:
                    if args.fixture_dir:
                        text, cost = run_fixture(
                            case.id, condition, Path(args.fixture_dir)
                        )
                    else:
                        fn = RUNNERS[runner]
                        text, cost = fn(case.prompt, system, args.model)
                except Exception as exc:  # noqa: BLE001 — surface provider errors
                    row = {
                        "case_id": case.id,
                        "trial": trial,
                        "condition": condition,
                        "runner": runner,
                        "ok": False,
                        "error": str(exc),
                        "ts": time.time(),
                    }
                    append_jsonl(output, row)
                    print(f"error {key}: {exc}")
                    continue
                if cost is None:
                    if not args.allow_unmetered:
                        print(
                            "FAIL: runner reported no cost; pass --allow-unmetered "
                            "only if the provider has its own hard cap"
                        )
                        return 1
                    cost = 0.0
                spent += float(cost)
                row = {
                    "case_id": case.id,
                    "trial": trial,
                    "condition": condition,
                    "runner": runner,
                    "ok": True,
                    "response": text,
                    "cost_usd": cost,
                    "model": args.model,
                    "ts": time.time(),
                }
                append_jsonl(output, row)
                print(f"ok {key} chars={len(text)} cost={cost}")
    print(f"spent_usd={spent:.4f}")
    return 0


def weighted(row: dict) -> float:
    return sum(float(row[k]) * w for k, w in WEIGHTS.items())


def cmd_score(args: argparse.Namespace) -> int:
    path = Path(args.scores)
    if not path.is_file():
        print("INCONCLUSIVE: scores file missing")
        return 2
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_cond: dict[str, list[dict]] = {}
    for row in rows:
        by_cond.setdefault(row["condition"], []).append(row)

    print("| condition | n | weighted | blockers |")
    print("|---|---:|---:|---:|")
    summary = {}
    for cond, items in sorted(by_cond.items()):
        blockers = sum(1 for r in items if r.get("blocker"))
        w = sum(weighted(r) for r in items) / len(items)
        summary[cond] = {"weighted": w, "blockers": blockers, "n": len(items)}
        print(f"| {cond} | {len(items)} | {w:.3f} | {blockers} |")

    if "baseline" in summary and "candidate" in summary:
        base = summary["baseline"]
        cand = summary["candidate"]
        ok = (
            cand["blockers"] == 0
            and cand["weighted"] > base["weighted"]
        )
        # per-dimension closeness for correctness/safety if present
        def avg(cond: str, key: str) -> float:
            items = by_cond[cond]
            return sum(float(r[key]) for r in items) / len(items)

        for key in ("correctness", "safety"):
            if abs(avg("candidate", key) - avg("baseline", key)) > 0.1 and avg(
                "candidate", key
            ) < avg("baseline", key):
                ok = False
                print(f"gate fail: {key} dropped >0.1 vs baseline")
        print("RELEASE" if ok else "HOLD")
        return 0 if ok else 1
    print("INCONCLUSIVE: need baseline and candidate scores")
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate")

    plan = sub.add_parser("plan")
    plan.add_argument("--trials", type=int, default=1)
    plan.add_argument("--budget-usd", type=float, default=5.0)
    plan.add_argument(
        "--conditions",
        nargs="+",
        default=["baseline", "candidate"],
    )

    run = sub.add_parser("run")
    run.add_argument("--runner", choices=sorted(RUNNERS), required=True)
    run.add_argument("--condition", action="append", required=True)
    run.add_argument("--condition-skill", default=None)
    run.add_argument("--baseline-system", default=None)
    run.add_argument("--trials", type=int, default=1)
    run.add_argument("--budget-usd", type=float, default=2.0)
    run.add_argument("--allow-unmetered", action="store_true")
    run.add_argument("--output", default=str(ROOT / "evals" / "results" / "responses.jsonl"))
    run.add_argument("--model", default=None)
    run.add_argument("--case", action="append", default=None)
    run.add_argument("--fixture-dir", default=None)

    score = sub.add_parser("score")
    score.add_argument("scores")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "plan":
        return cmd_plan(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "score":
        return cmd_score(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
