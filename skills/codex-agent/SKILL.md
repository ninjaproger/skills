---
name: codex-agent
description: >
  Delegate complex, multi-step coding tasks to the OpenAI Codex CLI agent running in the background.
  Use when the user wants to offload autonomous coding work to codex — including TCA feature
  development (new reducer/view/tests in a modular iOS app) and iOS Simulator automation (build,
  install, navigate, inspect). Codex runs non-interactively via `codex exec`, handles tool calls
  and file edits autonomously, and returns a final summary. Use for tasks that benefit from
  background execution: "implement X feature using codex", "have codex add tests for Y",
  "use codex to navigate the simulator and verify Z", "run codex in the background to build this".
---

# Codex Agent

## Overview

Use `codex exec` to run Codex as a background agent. Codex is given the skill files it needs
as reading material so it starts with full context and can work from 0 to 1 autonomously.

## Quick Start

```bash
codex exec --full-auto --cd [PROJECT_ROOT] --add-dir [SKILL_BASE] "PROMPT"
codex exec --full-auto --output-last-message /tmp/result.md "PROMPT"
codex exec resume --last   # continue previous session
```

> See `references/codex-cli.md` for all flags.

---

## Step 1 — Locate Skill Files

Find the skill base directories from your context (`Base directory for this skill:` lines):

- **tca-developer** — always needed for TCA feature development; find its `SKILL.md` and `references/`
- **ios-simulator** — only when the user asks to test in the simulator; find its `SKILL.md` and `scripts/ios_sim.py`

Use `--add-dir [SKILL_BASE]` for each skill directory so Codex can read files outside the project.

---

## Step 2 — Build the Codex Prompt

### TCA Feature Development (0 → 1)

```
Before writing any code, read these skill files to understand the conventions:
- [TCA_DEVELOPER_BASE]/SKILL.md
- [TCA_DEVELOPER_BASE]/references/feature-template.md
- [TCA_DEVELOPER_BASE]/references/view-patterns.md
- [TCA_DEVELOPER_BASE]/references/testing-patterns.md

Project root: [PROJECT_ROOT]
Feature to implement: [FEATURE_NAME]

Explore first:
1. List Sources/ to understand the module structure
2. Read Sources/[REFERENCE_FEATURE]/ (reducer + view) — use it as the style reference to match exactly
3. Read Sources/Models/ and Sources/Services/ for relevant types and dependency clients

Then implement (following the skill conventions):
4. Sources/[FEATURE_NAME]/[FEATURE_NAME]Reducer.swift
5. Sources/[FEATURE_NAME]/[FEATURE_NAME]View.swift — 4 previews: loading, loaded, empty, error
6. Tests/[FEATURE_NAME]Tests/[FEATURE_NAME]ReducerTests.swift
7. Register targets in Package.swift

When done, print a summary of files created and any AppCore wiring still needed.
```

```bash
codex exec --full-auto \
  --cd [PROJECT_ROOT] \
  --add-dir [TCA_DEVELOPER_BASE] \
  "PROMPT_ABOVE"
```

Identify `[REFERENCE_FEATURE]` by listing `Sources/` and picking the nearest existing feature.

---

### iOS Simulator Automation

```
Before starting, read this file for instructions:
- [IOS_SIMULATOR_BASE]/SKILL.md

Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py
App bundle ID: [BUNDLE_ID]
Simulator UDID: [UDID — or run `python .../ios_sim.py list` to find one]

Task: [TASK DESCRIPTION]

When done, print a summary of screens visited and the final UI state.
```

```bash
codex exec --full-auto \
  --add-dir [IOS_SIMULATOR_BASE] \
  "PROMPT_ABOVE"
```

---

### TCA Feature Development + Simulator Verification

Use when the user asks to both implement a feature and verify it in the simulator.

```
Before writing any code, read these skill files:
- [TCA_DEVELOPER_BASE]/SKILL.md
- [TCA_DEVELOPER_BASE]/references/feature-template.md
- [TCA_DEVELOPER_BASE]/references/view-patterns.md
- [TCA_DEVELOPER_BASE]/references/testing-patterns.md
- [IOS_SIMULATOR_BASE]/SKILL.md

Project root: [PROJECT_ROOT]
Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py
App bundle ID: [BUNDLE_ID]

Task:
1. Implement [FEATURE_NAME] following the tca-developer skill conventions
   (explore Sources/ first; use [REFERENCE_FEATURE] as style reference)
2. Build: python .../ios_sim.py build --workspace [WORKSPACE] --scheme [SCHEME]
3. Install and launch on the booted simulator
4. Navigate to the new feature, verify the UI, take a screenshot
5. Report any issues found
```

```bash
codex exec --full-auto \
  --cd [PROJECT_ROOT] \
  --add-dir [TCA_DEVELOPER_BASE] \
  --add-dir [IOS_SIMULATOR_BASE] \
  "PROMPT_ABOVE"
```

---

## Tips

- `--full-auto` = `--sandbox workspace-write --ask-for-approval never` — Codex edits files and runs shell commands without pausing
- Always `--add-dir` for every skill base directory Codex needs to read
- Use `--output-last-message /tmp/result.md` for long runs, then read the file to review the summary
- For simulator tasks, provide the UDID or tell Codex to run `ios_sim.py list` first
