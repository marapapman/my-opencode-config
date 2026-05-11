# my-opencode-config

Opencode configuration: 14 skills (de-Claudified from anthropics/skills) and agent definitions.

## Contents

| Component | Location | Description |
|-----------|----------|-------------|
| Skills | `skills/` | 14 general-purpose skills (document processing, web testing, MCP building, design, etc.) |
| Opencode config | `config/opencode.json` | Main config with Exa search MCP |
| Agent defs | `config/agents/` | 5 specialized agent instructions (build, precision-specialist, quick-scanner, fallback-solver, multimodal-describer) |

## Skills list

| Skill | Purpose |
|-------|---------|
| `agent-browser` | Browser automation via Playwright |
| `algorithmic-art` | p5.js generative art |
| `canvas-design` | Visual design on canvas |
| `guided-doc-writing` | Structured document writing workflow |
| `docx` | Word document manipulation |
| `frontend-design` | Production-grade frontend interfaces |
| `internal-comms` | Corporate communication templates |
| `mcp-builder` | MCP server development guide |
| `pdf` | PDF processing (merge, split, OCR, forms) |
| `pptx` | PowerPoint presentation manipulation |
| `slack-gif-creator` | Animated GIFs for Slack |
| `theme-factory` | Reusable color/font themes |
| `webapp-testing` | Playwright-based web app testing |
| `xlsx` | Spreadsheet manipulation |

## Agent-oriented installation instructions

An AI agent should execute these steps in order.

### Step 1: Clone the repository

```bash
git clone git@github.com:marapapman/my-opencode-config.git /tmp/my-opencode-config
```

### Step 2: Run the installer

```bash
cd /tmp/my-opencode-config && bash install.sh
```

The installer copies:
- `skills/` → `~/.agents/skills/`
- `config/opencode.json` → `~/.config/opencode/opencode.json`
- `config/agents/*.md` → `~/.config/opencode/agents/`

Existing config files are backed up to `*.bak` before overwriting.

### Step 3: Set API keys

Edit the config and replace the placeholder with your actual key:

```
~/.config/opencode/opencode.json   →  replace "YOUR_EXA_API_KEY"
```

### Step 4: Restart opencode

The updated skills and config take effect after restart.

## Manual installation (if automating without bash)

```bash
# Skills
mkdir -p ~/.agents/skills
cp -r skills/* ~/.agents/skills/

# Opencode config
mkdir -p ~/.config/opencode/agents
cp config/opencode.json ~/.config/opencode/opencode.json
cp config/agents/*.md ~/.config/opencode/agents/
```
