#!/usr/bin/env sh
# SessionStart: inject adhd-caveman ruleset into context.
#
# Works for Claude Code and Codex plugins. Always-on when the plugin is
# enabled, unless the user opted out with an .adhd-caveman-off flag.
#
# Claude interactive mode often drops *plugin* SessionStart context even when
# this script runs (side effects still work). For reliable always-on, also run:
#   python3 scripts/install_claude_hooks.py
# which wires this script into ~/.claude/settings.json (user hooks).
#
# Never blocks session start: any failure exits 0.
# Pure POSIX sh (macOS/Linux/Git Bash).

# Config home: Claude uses CLAUDE_CONFIG_DIR (~/.claude); Codex uses
# CODEX_HOME (~/.codex). Prefer whichever host set; else probe both.
if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
  config_dir="$CLAUDE_CONFIG_DIR"
elif [ -n "${CODEX_HOME:-}" ]; then
  config_dir="$CODEX_HOME"
elif [ -d "$HOME/.codex" ] && [ ! -d "$HOME/.claude" ]; then
  config_dir="$HOME/.codex"
else
  config_dir="${HOME}/.claude"
fi

off_path="$config_dir/.adhd-caveman-off"
active_path="$config_dir/.adhd-caveman-active"

# Also honor the other harness's off-flag if present.
[ -f "$off_path" ] && exit 0
[ -f "$HOME/.claude/.adhd-caveman-off" ] && exit 0
[ -f "${CODEX_HOME:-$HOME/.codex}/.adhd-caveman-off" ] && exit 0

# Plugin root: Codex sets PLUGIN_ROOT (+ CLAUDE_PLUGIN_ROOT for compat).
plugin_root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"

skill_path=""
if [ -n "$plugin_root" ] && [ -f "$plugin_root/skills/adhd-caveman/SKILL.md" ]; then
  skill_path="$plugin_root/skills/adhd-caveman/SKILL.md"
else
  script_dir=$(dirname -- "$0")
  for candidate in \
    "$script_dir/../skills/adhd-caveman/SKILL.md" \
    "$script_dir/../../skills/adhd-caveman/SKILL.md"
  do
    if [ -f "$candidate" ]; then
      skill_path="$candidate"
      break
    fi
  done
fi

[ -n "$skill_path" ] && [ -f "$skill_path" ] || exit 0

printf '%s\n' "full" > "$active_path" 2>/dev/null || true

body=$(awk '
  NR == 1 && $0 ~ /^---[[:space:]]*$/ { in_fm = 1; next }
  in_fm && $0 ~ /^---[[:space:]]*$/ { in_fm = 0; next }
  !in_fm { print }
' "$skill_path") || exit 0

printf '%s\n' \
  "ADHD-CAVEMAN MODE ACTIVE (SessionStart). Rules below apply every response." \
  "Off this session: say \"normal mode\", \"stop caveman\", or \"stop adhd mode\"." \
  "Off always-on: touch ${off_path} (or remove/disable the plugin)." \
  "Codex: trust plugin hooks via /hooks before SessionStart injection runs." \
  "" \
  "$body"
