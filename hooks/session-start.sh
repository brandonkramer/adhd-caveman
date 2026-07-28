#!/usr/bin/env sh
# SessionStart: inject adhd-caveman ruleset as hookSpecificOutput.additionalContext.
#
# Claude interactive mode often drops *plugin* SessionStart context even when
# this script runs (side effects still work). For reliable always-on:
#   python3 scripts/install_claude_hooks.py
#
# Never blocks session start: any failure exits 0.

. "$(dirname -- "$0")/common.sh" || exit 0

config_dir=$(resolve_config_dir)
off_flags_present "$config_dir" && exit 0

skill_path=$(resolve_skill_path "$0") || exit 0
active_path="$config_dir/.adhd-caveman-active"
off_path="$config_dir/.adhd-caveman-off"

printf '%s\n' "full" > "$active_path" 2>/dev/null || true

body=$(strip_skill_frontmatter "$skill_path") || exit 0

ctx=$(printf '%s\n' \
  "ADHD-CAVEMAN MODE ACTIVE (SessionStart). Rules below apply every response." \
  "Off this session: say \"normal mode\", \"stop caveman\", or \"stop adhd mode\"." \
  "Off always-on: touch ${off_path} (or remove/disable the plugin)." \
  "Codex: trust plugin hooks via /hooks before SessionStart injection runs." \
  "" \
  "$body")

# Prefer JSON (2026 docs). ADHD_CAVEMAN_PLAIN=1 keeps legacy bare stdout for debug.
if [ "${ADHD_CAVEMAN_PLAIN:-}" = "1" ]; then
  printf '%s\n' "$ctx"
else
  emit_additional_context "SessionStart" "$ctx"
fi
exit 0
