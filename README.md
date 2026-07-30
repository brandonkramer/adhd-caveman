# adhd-caveman

ADHD shape + caveman mouth for coding agents.

- **Shape** from [i-have-adhd](https://github.com/ayghri/i-have-adhd): action first, numbered steps, state restated, no fluff closers.
- **Mouth** from [caveman](https://github.com/JuliusBrussee/caveman): drop filler, keep substance, levels `lite|full|ultra`.
- **Conflict rule:** structure always beats compression.

Always-on is **hooks** (SessionStart + UserPromptSubmit + PreCompact), not `CLAUDE.md` / `AGENTS.md`.

```
source of truth          always-on                         measure
────────────────         ─────────                         ───────
skills/.../SKILL.md  →   settings.json hooks (reliable) +  evals/ + LOOP.md
                         plugin hooks (best-effort)        /loop-adhd-caveman-cycle
```

## Install

### Agent Skills (2026 default discovery)

```bash
npx skills add brandonkramer/adhd-caveman -g -a claude,codex,cursor -y
```

### Claude Code

```bash
claude plugin marketplace add brandonkramer/adhd-caveman
claude plugin install adhd-caveman@adhd-caveman
# Required for reliable always-on in interactive Claude:
python3 scripts/install_claude_hooks.py
# Optional badge (skips if you already have statusLine — compose manually):
python3 scripts/install_claude_hooks.py --with-statusline
```

If you already have a custom `statusLine`, append a call to
`~/.claude/adhd-caveman/hooks/statusline.sh` in that script (do not clobber).

Restart Claude (new session). Update marketplace after pulls: `claude plugin marketplace update adhd-caveman`.

| Want | Do |
|------|-----|
| Always on | Plugin **plus** `install_claude_hooks.py` |
| Off permanently | `touch ~/.claude/.adhd-caveman-off` |
| Off this session | Say `normal mode` / `stop caveman` / `stop adhd mode` |
| Intensity | `/adhd-caveman lite\|full\|ultra` |
| Uninstall settings hooks | `python3 scripts/install_claude_hooks.py --uninstall` |

### Codex

```bash
codex plugin marketplace add brandonkramer/adhd-caveman --ref main
codex plugin add adhd-caveman@adhd-caveman
```

Trust plugin hooks (`/hooks`). Off: `touch ~/.codex/.adhd-caveman-off`.

### Cursor

- Skill: `.cursor/skills/adhd-caveman/SKILL.md` or `npx skills add … -a cursor`
- Loop: `/loop-adhd-caveman-cycle`

### OpenClaw

```bash
python3 scripts/install_openclaw_soul.py
```

Appends a marker block to `~/.openclaw/workspace/SOUL.md` and copies the skill.

## Surfaces

| File | Role |
|------|------|
| `skills/adhd-caveman/SKILL.md` | Canonical rules (v0.2.0 plugin) |
| `hooks/{session-start,prompt-submit,precompact}.sh` | Always-on + reinforce + compact |
| `scripts/install_claude_hooks.py` | Wire user `settings.json` |
| `docs/openclaw-SOUL.snippet.md` | OpenClaw always-on snippet |
| `evals/` | Frozen cases + rubric |

## Optimize loop

```bash
python3 scripts/check_static.py
python3 scripts/run_evals.py validate
```

In Cursor: **/loop-adhd-caveman-cycle**.

## Credits

- [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT)
- [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (MIT)

## License

MIT
