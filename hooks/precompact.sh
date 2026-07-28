#!/usr/bin/env sh
# PreCompact: re-inject short rules before context compression drops SessionStart.
# Never blocks. Exit 0 always.

. "$(dirname -- "$0")/common.sh" || exit 0

config_dir=$(resolve_config_dir)
off_flags_present "$config_dir" && exit 0
[ -f "$config_dir/.adhd-caveman-active" ] || exit 0

level=$(cat "$config_dir/.adhd-caveman-active" 2>/dev/null || printf 'full')
ctx="ADHD-CAVEMAN MODE ACTIVE ($level) — re-assert after compact. $REINFORCE_CTX"
emit_additional_context "PreCompact" "$ctx"
exit 0
