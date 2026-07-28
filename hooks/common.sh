#!/usr/bin/env sh
# Shared helpers for adhd-caveman hooks. Sourced by other scripts; not a hook.

resolve_config_dir() {
  if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
    printf '%s' "$CLAUDE_CONFIG_DIR"
  elif [ -n "${CODEX_HOME:-}" ]; then
    printf '%s' "$CODEX_HOME"
  elif [ -d "$HOME/.codex" ] && [ ! -d "$HOME/.claude" ]; then
    printf '%s' "$HOME/.codex"
  else
    printf '%s' "${HOME}/.claude"
  fi
}

off_flags_present() {
  config_dir="$1"
  [ -f "$config_dir/.adhd-caveman-off" ] && return 0
  [ -f "$HOME/.claude/.adhd-caveman-off" ] && return 0
  [ -f "${CODEX_HOME:-$HOME/.codex}/.adhd-caveman-off" ] && return 0
  return 1
}

resolve_skill_path() {
  plugin_root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
  if [ -n "$plugin_root" ] && [ -f "$plugin_root/skills/adhd-caveman/SKILL.md" ]; then
    printf '%s' "$plugin_root/skills/adhd-caveman/SKILL.md"
    return 0
  fi
  script_dir=$(dirname -- "$1")
  for candidate in \
    "$script_dir/../skills/adhd-caveman/SKILL.md" \
    "$script_dir/../../skills/adhd-caveman/SKILL.md"
  do
    if [ -f "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

strip_skill_frontmatter() {
  awk '
    NR == 1 && $0 ~ /^---[[:space:]]*$/ { in_fm = 1; next }
    in_fm && $0 ~ /^---[[:space:]]*$/ { in_fm = 0; next }
    !in_fm { print }
  ' "$1"
}

# Emit Claude Code hookSpecificOutput JSON. $1=event name, $2=context text.
emit_additional_context() {
  event="$1"
  ctx="$2"
  ctx_json=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null) || \
  ctx_json=$(printf '%s' "$ctx" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk 'BEGIN{printf "\""} {printf "%s%s", (NR>1?"\\n":""), $0} END{printf "\""}')
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}\n' "$event" "$ctx_json"
}

REINFORCE_CTX='ADHD-CAVEMAN MODE ACTIVE. First line=next action. Multi-step=numbered list (cap 5). Restate Step N/M only if prior multi-step state. No preamble/closers. Drop filler; structure beats compression. Destructive=confirm+preview. Thanks=one short line. Never announce the style.'
