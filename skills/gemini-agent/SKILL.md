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
# Ensure skills are up to date, then run:
gemini skills install [TCA_DEVELOPER_BASE] && gemini skills enable tca-developer
cd [PROJECT_ROOT] && gemini --approval-mode yolo "Use the tca-developer skill to implement [FEATURE_NAME]. ..."
```

---

## Check & Update Skills

Always reinstall before running — this ensures the latest version is active (install is idempotent;
it updates if already present):

```bash
gemini skills install [TCA_DEVELOPER_BASE]
gemini skills enable tca-developer
```

Confirm it is active:

```bash
gemini skills list   # tca-developer should appear and be enabled
```

**ios-simulator** (only when simulator testing is requested):

```bash
gemini skills install [IOS_SIMULATOR_BASE]
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

```bash
gemini --approval-mode yolo \
  "Use the ios-simulator skill to [TASK]. \
   Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py. Print a summary when done."
```

---

### TCA Feature Development + Simulator Verification

```bash
cd [PROJECT_ROOT] && gemini --approval-mode yolo \
  "Use the tca-developer skill to implement [FEATURE_NAME]. \
   Validate with: [TEST_COMMAND]. \
   Then use the ios-simulator skill to verify the UI. \
   Simulator script: [IOS_SIMULATOR_BASE]/scripts/ios_sim.py. Print a summary."
```

---

## Tips

- `--approval-mode yolo` lets Gemini execute tools and edit files without pausing for approval
- Use `--output-format json` for machine-readable output in CI
- Use `gemini -r "latest"` to follow up on a previous run
- For simulator tasks, provide the UDID or tell Gemini to run `ios_sim.py list` first

## References

- **`references/gemini-cli.md`** — Full flag reference for `gemini`. Read when you need non-default flags (output format, session resume, model selection).
