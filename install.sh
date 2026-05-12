#!/usr/bin/env bash
# my-opencode-config installer
# Run this script from the repo root directory.
# Usage: bash install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DST="$HOME/.agents/skills"
AGENTS_SRC="$REPO_DIR/config/agents"
AGENTS_DST="$HOME/.config/opencode/agents"
OPENCODE_SRC="$REPO_DIR/config/opencode.json"
OPENCODE_DST="$HOME/.config/opencode/opencode.json"
ZENMUX_MCP_DIR="$REPO_DIR/mcp/zenmux-mcp"
echo "=== my-opencode-config installer ==="
echo ""

# ── 1. Install skills ──────────────────────────────────────────────
echo "[1/3] Installing skills..."
mkdir -p "$SKILLS_DST"
for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name="$(basename "$skill_dir")"
    if [ -f "$skill_dir/SKILL.md" ]; then
        echo "  + $skill_name"
        rm -rf "$SKILLS_DST/$skill_name"
        cp -r "$skill_dir" "$SKILLS_DST/$skill_name"
    fi
done
echo "  Skills installed to $SKILLS_DST"

# ── 2. Install opencode config ─────────────────────────────────────
echo "[2/3] Installing opencode config..."
mkdir -p "$(dirname "$OPENCODE_DST")"
if [ -f "$OPENCODE_DST" ]; then
    echo "  Backing up existing opencode.json to opencode.json.bak"
    cp "$OPENCODE_DST" "$(dirname "$OPENCODE_DST")/opencode.json.bak"
fi
cp "$OPENCODE_SRC" "$OPENCODE_DST"
if [ -d "$ZENMUX_MCP_DIR" ]; then
    python3 -m venv "$ZENMUX_MCP_DIR/.venv"
    "$ZENMUX_MCP_DIR/.venv/bin/python" -m pip install -r "$ZENMUX_MCP_DIR/requirements.txt"
    python3 - "$OPENCODE_DST" "$REPO_DIR" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
repo_dir = sys.argv[2]
config = json.loads(config_path.read_text())
command = config["mcp"]["zenmux-mcp"]["command"]
config["mcp"]["zenmux-mcp"]["command"] = [item.replace("YOUR_REPO_PATH", repo_dir) for item in command]
config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False) + "\n")
PY
fi
echo "  Config installed to $OPENCODE_DST"
echo "  ⚠  Edit $OPENCODE_DST and replace YOUR_EXA_API_KEY / YOUR_ZENMUX_API_KEY"

# ── 3. Install agent definitions ───────────────────────────────────
echo "[3/3] Installing agent definitions..."
mkdir -p "$AGENTS_DST"
if [ -d "$AGENTS_SRC" ]; then
    for agent_file in "$AGENTS_SRC"/*.md; do
        agent_name="$(basename "$agent_file")"
        echo "  + $agent_name"
        cp "$agent_file" "$AGENTS_DST/$agent_name"
    done
fi
echo "  Agents installed to $AGENTS_DST"

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit ~/.config/opencode/opencode.json — set YOUR_EXA_API_KEY and YOUR_ZENMUX_API_KEY"
echo "  2. Restart opencode"
