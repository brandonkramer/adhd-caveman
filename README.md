# adhd-caveman

ADHD shape + caveman mouth for coding agents.

- **Shape** from [i-have-adhd](https://github.com/ayghri/i-have-adhd): action first, numbered steps, state restated, no fluff closers.
- **Mouth** from [caveman](https://github.com/JuliusBrussee/caveman): drop filler, keep substance, levels `lite|full|ultra`.
- **Conflict rule:** structure always beats compression.

Always-on is a **SessionStart hook**, not `CLAUDE.md` / `AGENTS.md`.

```
source of truth          always-on                    measure
────────────────         ─────────                    ───────
skills/.../SKILL.md  →   SessionStart hook        +   evals/ + LOOP.md
                         (Claude Code + Codex)        /loop-adhd-caveman-cycle
```

## Install

### Claude Code

```bash
claude plugin marketplace add brandonkramer/adhd-caveman
claude plugin install adhd-caveman@adhd-caveman
```

| Want | Do |
|------|-----|
| Always on (default) | Install plugin |
| Off permanently | `touch ~/.claude/.adhd-caveman-off` |
| Off this session | Say `normal mode` / `stop caveman` / `stop adhd mode` |
| Intensity | `/adhd-caveman lite\|full\|ultra` |

### Codex

```bash
codex plugin marketplace add brandonkramer/adhd-caveman --ref main
codex plugin add adhd-caveman@adhd-caveman
```

Then type `$adhd-caveman`. For SessionStart always-on, **trust the plugin hooks**
(` /hooks ` in Codex) — Codex skips bundled hooks until trusted.

| Want | Do |
|------|-----|
| Always on | Install plugin + trust hooks |
| Off permanently | `touch ~/.codex/.adhd-caveman-off` |
| Off this session | Say `normal mode` / `stop caveman` / `stop adhd mode` |
| On demand | `$adhd-caveman` (no AGENTS.md paste) |

### Cursor

- Skill: `.cursor/skills/adhd-caveman/SKILL.md`
- Loop cycle: `/loop-adhd-caveman-cycle`
- No always-on `AGENTS.md` — invoke the skill, or add a Cursor rule if you want project-wide always-on.

## Surfaces

| File | Role |
|------|------|
| `skills/adhd-caveman/SKILL.md` | Canonical rules |
| `hooks/session-start.sh` + `hooks/hooks.json` | Claude + Codex SessionStart injection |
| `.claude-plugin/` | Claude Code plugin manifest |
| `.codex-plugin/` | Codex plugin manifest |
| `.cursor/skills/.../SKILL.md` | Cursor copy (`scripts/sync_skill_copies.py`) |

## Optimize loop

```bash
python3 scripts/check_static.py
python3 scripts/run_evals.py validate

# dry-run fixtures
python3 scripts/run_evals.py run \
  --runner cursor \
  --condition baseline --condition candidate \
  --fixture-dir evals/fixtures \
  --case direct-answer --case multi-step-progress --case structure-vs-ultra \
  --allow-unmetered \
  --output evals/results/fixture-run.jsonl
```

Live Codex arm (isolated):

```bash
python3 scripts/run_evals.py run \
  --runner codex \
  --condition candidate \
  --condition-skill skills/adhd-caveman/SKILL.md \
  --allow-unmetered \
  --budget-usd 2 \
  --output evals/results/responses.jsonl
```

In Cursor: **/loop-adhd-caveman-cycle**. Contract: `.agents/projects/adhd-caveman/`.

## Credits

- [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT)
- [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (MIT)

## License

MIT.
