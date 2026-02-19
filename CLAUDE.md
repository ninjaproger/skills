# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a Claude Code plugin marketplace (`ninjaproger-skills`) containing Python-based skills. The marketplace is defined in `.claude-plugin/marketplace.json`; individual skills live in `skills/`.

## Marketplace Architecture

`.claude-plugin/marketplace.json` lists plugins. Each plugin entry has a `skills` array of paths to skill directories. The current single plugin (`ios-simulator`) points to `./skills/ios-simulator`.

Skill directories must contain `SKILL.md` with YAML frontmatter (`name` in kebab-case, `description`). Optional subdirectories: `scripts/` (executable code), `references/` (docs loaded into context), `assets/` (output templates).

## Common Commands

```bash
# Run the ios-simulator script directly
python skills/ios-simulator/scripts/ios_sim.py <command> --help

# List available simulators
python skills/ios-simulator/scripts/ios_sim.py list

# Scaffold a new skill
python ~/.claude/plugins/cache/anthropic-agent-skills/document-skills/1ed29a03dc85/skills/skill-creator/scripts/init_skill.py <skill-name> --path skills/

# Validate and package a skill into a .skill file
python ~/.claude/plugins/cache/anthropic-agent-skills/document-skills/1ed29a03dc85/skills/skill-creator/scripts/package_skill.py skills/<skill-name> .
```

The `init_skill.py` and `package_skill.py` scripts come from the installed `document-skills@anthropic-agent-skills` plugin. `package_skill.py` requires `pyyaml` (`pip install pyyaml`).

## Prerequisites

Install the `skill-creator` plugin before working on skills in this repo. It provides the `/skill-creator` skill, `init_skill.py`, and `package_skill.py`.

```
# Option A — standalone plugin (recommended)
/plugin install skill-creator@claude-plugins-official

# Option B — bundled inside document-skills (already installed if you set up this marketplace)
/plugin install document-skills@anthropic-agent-skills
```

Also install system dependencies for `ios-simulator`:

```bash
pip install fb-idb pyyaml
brew tap facebook/fb && brew install idb-companion
# Xcode must be installed via the App Store
```

## Creating Skills, Agents, and Commands

Always invoke the `/skill-creator` skill when creating or modifying skills, agents, or commands in this repository. It provides the authoritative workflow, design patterns, and validation tooling.

## Adding a New Skill

1. Scaffold: run `init_skill.py <skill-name> --path skills/`
2. Implement `skills/<skill-name>/SKILL.md` — name must be kebab-case
3. Add scripts/references/assets as needed; delete unused placeholder dirs
4. Register: add `"./skills/<skill-name>"` to the `skills` array of the relevant plugin in `.claude-plugin/marketplace.json`
5. Package: run `package_skill.py skills/<skill-name> .` to produce `<skill-name>.skill`
