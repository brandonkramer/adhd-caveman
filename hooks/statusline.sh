#!/usr/bin/env bash
# Optional Claude Code statusLine badge. Wire via install_claude_hooks.py
# when no statusLine is already configured, or compose into an existing script.

resolve_active_flag() {
  for d in "${CLAUDE_CONFIG_DIR:-}" "${HOME}/.claude"; do
    [ -n "$d" ] || continue
    if [ -f "${d}/.adhd-caveman-active" ]; then
      printf '%s' "${d}/.adhd-caveman-active"
      return 0
    fi
  done
  return 1
}

flag=$(resolve_active_flag) || exit 0
mode=$(tr -d '[:space:]' <"$flag" 2>/dev/null || true)
if [ -z "$mode" ] || [ "$mode" = "full" ]; then
  printf '\033[38;5;33m[ADHD-CAVEMAN]\033[0m'
else
  upper=$(printf '%s' "$mode" | tr '[:lower:]' '[:upper:]')
  printf '\033[38;5;33m[ADHD-CAVEMAN:%s]\033[0m' "$upper"
fi
