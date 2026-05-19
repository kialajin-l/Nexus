#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./install.sh <claude-code|codex|hermes|openclaw|deepseek>"
  exit 1
fi

case "$TARGET" in
  claude-code)
    SKILL_DIR="${HOME}/.claude/skills/nexus"
    ;;
  codex)
    SKILL_DIR="${HOME}/.codex/skills/nexus"
    ;;
  hermes)
    SKILL_DIR="${HOME}/.hermes/skills/nexus"
    ;;
  openclaw)
    SKILL_DIR="${HOME}/.openclaw/skills/nexus"
    ;;
  deepseek)
    SKILL_DIR="${HOME}/.deepseek/skills/nexus"
    ;;
  *)
    echo "Unsupported target: $TARGET"
    echo "Supported targets: claude-code, codex, hermes, openclaw, deepseek"
    exit 1
    ;;
esac

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SKILL_DIR"

copy_file() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
}

copy_dir_contents() {
  local src_dir="$1"
  local dest_dir="$2"
  mkdir -p "$dest_dir"
  cp -R "$src_dir"/. "$dest_dir"/
}

CONFIG_FILE="$SKILL_DIR/config/nexus.json"
CONFIG_BACKUP=""

if [[ -f "$CONFIG_FILE" ]]; then
  CONFIG_BACKUP="$(mktemp)"
  cp "$CONFIG_FILE" "$CONFIG_BACKUP"
fi

rm -rf "$SKILL_DIR/SKILL.md" "$SKILL_DIR/adapters" "$SKILL_DIR/src" "$SKILL_DIR/.codex-plugin"

copy_file "$ROOT_DIR/SKILL.md" "$SKILL_DIR/SKILL.md"
copy_dir_contents "$ROOT_DIR/adapters" "$SKILL_DIR/adapters"
copy_dir_contents "$ROOT_DIR/src" "$SKILL_DIR/src"

if [[ -n "$CONFIG_BACKUP" ]]; then
  mkdir -p "$SKILL_DIR/config"
  cp "$CONFIG_BACKUP" "$CONFIG_FILE"
  rm -f "$CONFIG_BACKUP"
else
  copy_dir_contents "$ROOT_DIR/config" "$SKILL_DIR/config"
fi

if [[ -d "$ROOT_DIR/.codex-plugin" ]]; then
  copy_dir_contents "$ROOT_DIR/.codex-plugin" "$SKILL_DIR/.codex-plugin"
fi

echo "Installed Nexus to: $SKILL_DIR"
echo
echo "Next steps:"
echo "1. Run: nexus setup --config \"$SKILL_DIR/config/nexus.json\" --db-path \"<db-path>\" --obsidian-root \"<vault-path>\""
echo "2. Review: $SKILL_DIR/config/nexus.json"
echo "3. If you want shared memory across local agents, point them to the same db_path"
