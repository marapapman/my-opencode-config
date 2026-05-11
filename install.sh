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
MCP_SRC="$REPO_DIR/config/mcp.json"
MCP_DST="$HOME/.codebuddy/mcp.json"

echo "=== my-opencode-config installer ==="
echo ""

# ── 1. Install skills ──────────────────────────────────────────────
echo "[1/4] Installing skills..."
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
echo "[2/4] Installing opencode config..."
mkdir -p "$(dirname "$OPENCODE_DST")"
if [ -f "$OPENCODE_DST" ]; then
    echo "  Backing up existing opencode.json to opencode.json.bak"
    cp "$OPENCODE_DST" "$(dirname "$OPENCODE_DST")/opencode.json.bak"
fi
cp "$OPENCODE_SRC" "$OPENCODE_DST"
echo "  Config installed to $OPENCODE_DST"
echo "  ⚠  Edit $OPENCODE_DST and replace YOUR_EXA_API_KEY with your actual key"

# ── 3. Install agent definitions ───────────────────────────────────
echo "[3/4] Installing agent definitions..."
mkdir -p "$AGENTS_DST"
if [ -d "$AGENTS_SRC" ]; then
    for agent_file in "$AGENTS_SRC"/*.md; do
        agent_name="$(basename "$agent_file")"
        echo "  + $agent_name"
        cp "$agent_file" "$AGENTS_DST/$agent_name"
    done
fi
echo "  Agents installed to $AGENTS_DST"

# ── 4. Install MCP config ──────────────────────────────────────────
echo "[4/4] Installing MCP config..."
mkdir -p "$(dirname "$MCP_DST")"
if [ -f "$MCP_DST" ]; then
    echo "  Backing up existing mcp.json to mcp.json.bak"
    cp "$MCP_DST" "$(dirname "$MCP_DST")/mcp.json.bak"
fi
cp "$MCP_SRC" "$MCP_DST"
echo "  MCP config installed to $MCP_DST"
echo "  ⚠  Edit $MCP_DST and replace YOUR_Z_AI_API_KEY with your actual key"

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit ~/.config/opencode/opencode.json — set YOUR_EXA_API_KEY"
echo "  2. Edit ~/.codebuddy/mcp.json — set YOUR_Z_AI_API_KEY"
echo "  3. Restart opencode"
