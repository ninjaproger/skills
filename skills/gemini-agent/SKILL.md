---
name: gemini-agent
description: >
  Delegate complex, multi-step coding tasks to the Google Gemini CLI agent running in the background.
  Use when the user wants to offload autonomous coding work to gemini — including TCA feature
  development (new reducer/view/tests in a modular iOS app) and iOS Simulator automation (build,
  install, navigate, inspect). Gemini runs non-interactively via `gemini "prompt"`, handles tool
  calls and file edits autonomously, and returns a final summary. Use for tasks that benefit from
  background execution: "implement X feature using gemini", "have gemini add tests for Y",
  "use gemini to navigate the simulator and verify Z", "run gemini in the background to build this".
---

# Gemini Agent

## Overview

Use `gemini "prompt"` to run Gemini as a background agent. Because Gemini CLI reads from stdin,
skill file contents are piped directly into the prompt — no directory access flags needed.

## Quick Start

```bash
# One-shot execution (non-interactive)
gemini --approval-mode yolo "YOUR PROMPT"

# Pipe skill files + prompt (recommended for rich context)
(cat [SKILL_FILE_1] [SKILL_FILE_2]; echo "---"; echo "YOUR PROMPT") | gemini --approval-mode yolo

# From a specific working directory
cd [PROJECT_ROOT] && gemini --approval-mode yolo "YOUR PROMPT"

# Resume last session
gemini -r "latest" "follow-up prompt"
```

> See `references/gemini-cli.md` for all flags.

---

## Step 1 — Locate Skill Files

Find the skill base directories from your context (`Base directory for this skill:` lines):

- **tca-developer** — always needed for TCA feature development; find its `SKILL.md` and `references/`
- **ios-simulator** — only when the user asks to test in the simulator; find its `SKILL.md` and `scripts/ios_sim.py`

---

## Step 2 — Build the Gemini Prompt

Pipe skill files directly into the prompt using stdin — this embeds the full conventions without
requiring Gemini to read files outside the project directory.

### TCA Feature Development (0 → 1)

```bash
cd [PROJECT_ROOT] && (
  cat [TCA_DEVELOPER_BASE]/SKILL.md
  cat [TCA_DEVELOPER_BASE]/references/feature-template.md
  cat [TCA_DEVELOPER_BASE]/references/view-patterns.md
  cat [TCA_DEVELOPER_BASE]/references/testing-patterns.md
  echo "---"
  echo "Feature to implement: [FEATURE_NAME]"
  echo ""
  echo "Explore first:"
  echo "1. List Sources/ to understand the module structure"
  echo "2. Read Sources/[REFERENCE_FEATURE]/ (reducer + view) — use it as the style reference to match exactly"
  echo "3. Read Sources/Models/ and Sources/Services/ for relevant types and dependency clients"
  echo ""
  echo "Then implement (following the conventions from the skill files above):"
  echo "4. Sources/[FEATURE_NAME]/[FEATURE_NAME]Reducer.swift"
  echo "5. Sources/[FEATURE_NAME]/[FEATURE_NAME]View.swift — 4 previews: loading, loaded, empty, error"
  echo "6. Tests/[FEATURE_NAME]Tests/[FEATURE_NAME]ReducerTests.swift"
  echo "7. Register targets in Package.swift"
  echo ""
  echo "When done, print a summary of files created and any AppCore wiring still needed."
) | gemini --approval-mode yolo
```

Identify `[REFERENCE_FEATURE]` by listing `Sources/` and picking the nearest existing feature.

---

### iOS Simulator Automation

```bash
(
  cat [IOS_SIMULATOR_BASE]/SKILL.md
  echo "---"
  echo "Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py"
  echo "App bundle ID: [BUNDLE_ID]"
  echo "Simulator UDID: [UDID — or run \`python .../ios_sim.py list\` to find one]"
  echo ""
  echo "Task: [TASK DESCRIPTION]"
  echo ""
  echo "When done, print a summary of screens visited and the final UI state."
) | gemini --approval-mode yolo
```

---

### TCA Feature Development + Simulator Verification

Use when the user asks to both implement a feature and verify it in the simulator.

```bash
cd [PROJECT_ROOT] && (
  cat [TCA_DEVELOPER_BASE]/SKILL.md
  cat [TCA_DEVELOPER_BASE]/references/feature-template.md
  cat [TCA_DEVELOPER_BASE]/references/view-patterns.md
  cat [TCA_DEVELOPER_BASE]/references/testing-patterns.md
  cat [IOS_SIMULATOR_BASE]/SKILL.md
  echo "---"
  echo "Project root: [PROJECT_ROOT]"
  echo "Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py"
  echo "App bundle ID: [BUNDLE_ID]"
  echo ""
  echo "Task:"
  echo "1. Implement [FEATURE_NAME] following the tca-developer skill conventions"
  echo "   (explore Sources/ first; use [REFERENCE_FEATURE] as style reference)"
  echo "2. Build: python .../ios_sim.py build --workspace [WORKSPACE] --scheme [SCHEME]"
  echo "3. Install and launch on the booted simulator"
  echo "4. Navigate to the new feature, verify the UI, take a screenshot"
  echo "5. Report any issues found"
) | gemini --approval-mode yolo
```

---

## Tips

- `--approval-mode yolo` lets Gemini execute tools and edit files without pausing for approval
- Piping skill files via stdin is the idiomatic way to give Gemini context from outside the project
- Use `--output-format json` for machine-readable output in CI
- Use `gemini -r "latest"` to follow up on a previous run
- For simulator tasks, provide the UDID or tell Gemini to run `ios_sim.py list` first
