# Loop: adhd-caveman cycle

Run one optimization cycle against the frozen loop.

## Context

- Contract: `.agents/projects/adhd-caveman/`
- Canonical voice: `skills/adhd-caveman/SKILL.md` (sync Cursor copy after edits)
- Always-on (Claude): `hooks/session-start.sh` injects that skill — do not add `AGENTS.md` / `CLAUDE.md`
- Loop: `.agents/projects/adhd-caveman/LOOP.md`
- Cases: `evals/cases.jsonl` · Rubric: `evals/rubric.md`

## Procedure

1. Read `project.toml` current task and `LOOP.md` gates. Do not weaken frozen
   thresholds after seeing treatment output.
2. State one falsifiable hypothesis.
3. Run cheapest check first:
   ```bash
   python3 scripts/check_static.py
   python3 scripts/run_evals.py validate
   ```
4. If authorized and budget allows, run a real isolated trial:
   ```bash
   python3 scripts/run_evals.py run \
     --runner cursor \
     --condition candidate \
     --condition-skill skills/adhd-caveman/SKILL.md \
     --trials 1 \
     --budget-usd 2.00 \
     --output evals/results/responses.jsonl
   ```
5. Score with `evals/rubric.md`. Classify PASS / FAIL / INCONCLUSIVE.
6. If FAIL: one bounded edit to `skills/adhd-caveman/SKILL.md`, then
   `python3 scripts/sync_skill_copies.py`, then re-run static + failing cases.
7. Record evidence under `evals/results/` and update RESEARCH.md at the next
   task checkpoint. Never mark a task done from narration alone.

## Stop

Stop before changing goal, public claims, safety rules, or frozen gates.
Ask the user.
