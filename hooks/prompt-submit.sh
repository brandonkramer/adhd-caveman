#!/usr/bin/env sh
# UserPromptSubmit: per-turn reinforcement + off/on phrase handling.
# Never blocks the prompt: any failure exits 0.

. "$(dirname -- "$0")/common.sh" || exit 0

config_dir=$(resolve_config_dir)
off_path="$config_dir/.adhd-caveman-off"
active_path="$config_dir/.adhd-caveman-active"

off_flags_present "$config_dir" && exit 0

prompt=$(dd bs=4096 count=1 2>/dev/null || true)
prompt_lc=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

wants_off=0
printf '%s' "$prompt_lc" | grep -q 'normal mode' && wants_off=1
printf '%s' "$prompt_lc" | grep -q 'stop caveman' && wants_off=1
printf '%s' "$prompt_lc" | grep -q 'stop adhd mode' && wants_off=1

if [ "$wants_off" -eq 1 ]; then
  rm -f "$active_path" 2>/dev/null || true
  emit_additional_context "UserPromptSubmit" "ADHD-caveman off for this session."
  exit 0
fi

wants_on=0
printf '%s' "$prompt_lc" | grep -q '/adhd-caveman' && wants_on=1
printf '%s' "$prompt_lc" | grep -q 'adhd caveman' && wants_on=1
printf '%s' "$prompt_lc" | grep -q 'talk like caveman' && wants_on=1

if [ "$wants_on" -eq 1 ]; then
  printf '%s\n' "full" > "$active_path" 2>/dev/null || true
fi

[ -f "$active_path" ] || exit 0

level=$(cat "$active_path" 2>/dev/null || printf 'full')
[ -n "$level" ] || level=full
ctx="ADHD-CAVEMAN MODE ACTIVE ($level). $REINFORCE_CTX"
emit_additional_context "UserPromptSubmit" "$ctx"
exit 0
