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

## Quick Start

```bash
# Ensure skills are installed, then run:
codex exec --full-auto --cd [PROJECT_ROOT] \
  "Use the tca-developer skill to implement [FEATURE_NAME]. ..."
```

---

## Sibling Skill Paths

This skill is part of a plugin. The other skills (`tca-developer`, `tca-architect`, `ios-simulator`)
are installed in the **same plugin directory** as this skill.

Derive their absolute paths by replacing the last path component of this skill's base directory:

- This skill's base: `.../skills/codex-agent/`
- tca-developer:     `.../skills/tca-developer/`
- ios-simulator:     `.../skills/ios-simulator/`

Use the resolved absolute path wherever `<SKILL_PATH>` appears below.

Codex registers skills by file path in `~/.codex/config.toml`. When the path points to the source
skill directory, it always reads the latest SKILL.md from disk — no explicit update step needed.

To check which skills are registered, open an interactive Codex session and run `/skills`.
To install a missing skill, open an interactive Codex session and run `$skill-installer install <SKILL_PATH>`.

---

## Run

### TCA Feature Development

```bash
codex exec --full-auto --cd [PROJECT_ROOT] \
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

The `ios_sim.py` script is at `<ios-simulator-skill-path>/scripts/ios_sim.py`. Resolve this path
from this skill's base directory before running.

```bash
codex exec --full-auto \
  "Use the ios-simulator skill to [TASK]. \
   Simulator script: <IOS_SIMULATOR_SKILL_PATH>/scripts/ios_sim.py. Print a summary when done."
```

---

### TCA Feature Development + Simulator Verification

```bash
codex exec --full-auto --cd [PROJECT_ROOT] \
  "Use the tca-developer skill to implement [FEATURE_NAME]. \
   Validate with: [TEST_COMMAND]. \
   Then use the ios-simulator skill to verify the UI. \
   Simulator script: <IOS_SIMULATOR_SKILL_PATH>/scripts/ios_sim.py. Print a summary."
```

---

## Tips

- `--full-auto` = `--sandbox workspace-write --ask-for-approval never` — Codex edits files and runs shell commands without pausing
- Use `--output-last-message /tmp/result.md` for long runs, then read the file to review the summary
- For simulator tasks, provide the UDID or tell Codex to run `ios_sim.py list` first
- `codex exec resume --last` continues the previous session

## References

- **`references/codex-cli.md`** — Full flag reference for `codex exec`. Read when you need non-default flags (output format, sandbox mode, session resume).
