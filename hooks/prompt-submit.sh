#!/usr/bin/env sh
# UserPromptSubmit: per-turn reinforcement + off/on phrase handling.
#
# Claude Code often drops *plugin* SessionStart context in interactive mode.
# User-level hooks (settings.json) + this short additionalContext keep the
# voice alive every turn (caveman pattern).
#
# Never blocks the prompt: any failure exits 0.
# Pure POSIX sh.

if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
  config_dir="$CLAUDE_CONFIG_DIR"
elif [ -n "${CODEX_HOME:-}" ]; then
  config_dir="$CODEX_HOME"
else
  config_dir="${HOME}/.claude"
fi

off_path="$config_dir/.adhd-caveman-off"
active_path="$config_dir/.adhd-caveman-active"

[ -f "$off_path" ] && exit 0
[ -f "$HOME/.claude/.adhd-caveman-off" ] && exit 0

# Read user prompt (hook stdin). Cap size.
prompt=$(dd bs=4096 count=1 2>/dev/null || true)
prompt_lc=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

wants_off=0
printf '%s' "$prompt_lc" | grep -q 'normal mode' && wants_off=1
printf '%s' "$prompt_lc" | grep -q 'stop caveman' && wants_off=1
printf '%s' "$prompt_lc" | grep -q 'stop adhd mode' && wants_off=1

if [ "$wants_off" -eq 1 ]; then
  rm -f "$active_path" 2>/dev/null || true
  # Confirm off once; no ongoing reinforcement.
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"ADHD-caveman off for this session."}}'
  exit 0
fi

wants_on=0
printf '%s' "$prompt_lc" | grep -q '/adhd-caveman' && wants_on=1
printf '%s' "$prompt_lc" | grep -q 'adhd caveman' && wants_on=1
printf '%s' "$prompt_lc" | grep -q 'talk like caveman' && wants_on=1

if [ "$wants_on" -eq 1 ]; then
  printf '%s\n' "full" > "$active_path" 2>/dev/null || true
fi

# Only reinforce when SessionStart (or explicit on) marked active.
[ -f "$active_path" ] || exit 0

level=$(cat "$active_path" 2>/dev/null || printf 'full')
[ -n "$level" ] || level=full

# Short reminder — full ruleset comes from SessionStart / skill invoke.
ctx="ADHD-CAVEMAN MODE ACTIVE ($level). First line=next action. Multi-step=numbered list (cap 5). Restate Step N/M only if prior multi-step state. No preamble/closers. Drop filler; structure beats compression. Destructive=confirm+preview. Thanks=one short line. Never announce the style."

# Minimal JSON escape for the context string.
ctx_json=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null) || \
ctx_json=$(printf '%s' "$ctx" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g' | awk 'BEGIN{printf "\""} {printf "%s%s", (NR>1?"\\n":""), $0} END{printf "\""}')

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":%s}}\n' "$ctx_json"
exit 0
