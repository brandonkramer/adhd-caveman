#!/usr/bin/env bash
# Optional Claude Code statusLine badge. Wire via install_claude_hooks.py
# when no statusLine is already configured.

flag="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.adhd-caveman-active"
if [ -f "$flag" ]; then
  mode=$(tr -d '[:space:]' <"$flag" 2>/dev/null || true)
  if [ -z "$mode" ] || [ "$mode" = "full" ]; then
    printf '\033[38;5;33m[ADHD-CAVEMAN]\033[0m'
  else
    upper=$(printf '%s' "$mode" | tr '[:lower:]' '[:upper:]')
    printf '\033[38;5;33m[ADHD-CAVEMAN:%s]\033[0m' "$upper"
  fi
fi
