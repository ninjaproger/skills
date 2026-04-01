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

## Quick Start

```bash
gemini skills install <TCA_DEVELOPER_SKILL_PATH> && gemini skills enable tca-developer
cd [PROJECT_ROOT] && gemini --approval-mode yolo "Use the tca-developer skill to implement [FEATURE_NAME]. ..."
```

---

## Sibling Skill Paths

This skill is part of a plugin. The other skills (`tca-developer`, `tca-architect`, `ios-simulator`)
are installed in the **same plugin directory** as this skill.

Derive their absolute paths by replacing the last path component of this skill's base directory:

- This skill's base: `.../skills/gemini-agent/`
- tca-developer:     `.../skills/tca-developer/`
- ios-simulator:     `.../skills/ios-simulator/`

Use the resolved absolute path wherever `<SKILL_PATH>` appears below.

Install a skill (idempotent — safe to re-run after updating skill source):

```bash
gemini skills install <TCA_DEVELOPER_SKILL_PATH>
gemini skills enable tca-developer
gemini skills list   # confirm it appears and is enabled
```

Only install `ios-simulator` when simulator testing is requested:

```bash
gemini skills install <IOS_SIMULATOR_SKILL_PATH>
gemini skills enable ios-simulator
```

---

## Run

### TCA Feature Development

```bash
cd [PROJECT_ROOT] && gemini --approval-mode yolo \
  "Use the tca-developer skill to implement [FEATURE_NAME]. \
   Explore Sources/, use [REFERENCE_FEATURE] as style reference. \
   When implementation is done, validate by running: [TEST_COMMAND]. \
   Report test results and a summary of files created."
```

Where `[TEST_COMMAND]` is the project's test command, e.g.:

```
xcodebuild test -project MyApp.xcodeproj -scheme MyAppTests \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -skipMacroValidation
```

Identify `[REFERENCE_FEATURE]` by listing `Sources/` and picking the nearest existing feature.

---

### iOS Simulator Automation

The `ios_sim.py` script is at `<IOS_SIMULATOR_SKILL_PATH>/scripts/ios_sim.py`. Resolve this path
from this skill's base directory before running.

```bash
gemini --approval-mode yolo \
  "Use the ios-simulator skill to [TASK]. \
   Simulator script: <IOS_SIMULATOR_SKILL_PATH>/scripts/ios_sim.py. Print a summary when done."
```

---

### TCA Feature Development + Simulator Verification

```bash
cd [PROJECT_ROOT] && gemini --approval-mode yolo \
  "Use the tca-developer skill to implement [FEATURE_NAME]. \
   Validate with: [TEST_COMMAND]. \
   Then use the ios-simulator skill to verify the UI. \
   Simulator script: <IOS_SIMULATOR_SKILL_PATH>/scripts/ios_sim.py. Print a summary."
```

---

## Tips

- `--approval-mode yolo` lets Gemini execute tools and edit files without pausing for approval
- Use `--output-format json` for machine-readable output in CI
- Use `gemini -r "latest"` to follow up on a previous run
- For simulator tasks, provide the UDID or tell Gemini to run `ios_sim.py list` first

## References

- **`references/gemini-cli.md`** — Full flag reference for `gemini`. Read when you need non-default flags (output format, session resume, model selection).
