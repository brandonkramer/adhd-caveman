# Evaluations

Frozen cases: `cases.jsonl`. Scoring contract: `rubric.md`.
Project loop: `.agents/projects/adhd-caveman/LOOP.md`.

Two tiers:

1. **Static** (cheap, every edit) — `scripts/check_static.py`
2. **Real runs** (metered) — `scripts/run_evals.py run …`

## Validate

```bash
python3 scripts/check_static.py
python3 scripts/run_evals.py validate
python3 scripts/run_evals.py plan --trials 3
```

## Real runs (isolated)

Isolate from operator config **and SessionStart hooks** so baseline is not
contaminated by this style (the sharp case is an enabled plugin injecting the
skill into the baseline arm).

```bash
# baseline
python3 scripts/run_evals.py run \
  --runner cursor \
  --condition baseline \
  --trials 1 \
  --budget-usd 2.00 \
  --output evals/results/responses.jsonl

# candidate (this skill)
python3 scripts/run_evals.py run \
  --runner cursor \
  --condition candidate \
  --condition-skill skills/adhd-caveman/SKILL.md \
  --trials 1 \
  --budget-usd 2.00 \
  --output evals/results/responses.jsonl
```

Also supports `--runner claude` and `--runner codex` when those CLIs exist.
Claude defaults to `claude-opus-5` (not Sonnet); pass `--model haiku` for cheap
smoke. Cursor runner uses `agent -p --mode ask` in an **isolated HOME** (empty
`~/.cursor/skills` + `~/.agents/skills`, seeded auth only) plus empty
`--workspace`, so user always-on skills cannot leak into baseline. Codex runner
uses `codex exec --ephemeral -s read-only` in an empty `-C` workspace (resolves
nvm `codex` if needed). Without a CLI, dry-run fixtures under `--fixture-dir`.

## Score

Blind the `condition` field, write `evals/results/scores.jsonl`, then:

```bash
python3 scripts/run_evals.py score evals/results/scores.jsonl
```

## Cursor optimize loop

In Cursor: run the `/loop-adhd-caveman-cycle` command (see `.cursor/commands/loop-adhd-caveman-cycle.md`)
or follow `LOOP.md` iteration procedure. One hypothesis per cycle. Do not weaken
gates after seeing treatment output.
