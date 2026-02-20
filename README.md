# skills

A Claude Code plugin marketplace with useful skills for iOS development and automation.

## Installation

Register this repository as a Claude Code plugin marketplace:

```
/plugin marketplace add https://github.com/ninjaproger/skills
```

Then browse and install skills via `/plugin` → **Browse and install plugins** → `ninjaproger-skills`.

## Skills

### `ios-simulator`

Automate iOS simulators using [idb](https://github.com/facebook/idb) and `xcrun simctl`.

**Capabilities:**
- **Build** — compile an app for the simulator via `xcodebuild`
- **Install / Launch / Terminate** — manage app lifecycle
- **Navigate** — tap, swipe, scroll, type text, press keys, open URLs, press HOME/LOCK/SIRI
- **Inspect** — dump the full accessibility tree, find elements by label, take screenshots

**Key feature:** every navigation command runs `idb ui describe-all` before and after the action to validate the current UI state and resolve exact tap coordinates from live element frames — no hardcoded pixel values needed.

```bash
# List simulators
python skills/ios-simulator/scripts/ios_sim.py list

# Launch an app
python skills/ios-simulator/scripts/ios_sim.py launch com.example.MyApp --udid <UDID>

# Tap an element by label (uses describe-all to find coordinates)
python skills/ios-simulator/scripts/ios_sim.py tap-element "Sign In" --udid <UDID>

# Scroll down
python skills/ios-simulator/scripts/ios_sim.py scroll down --udid <UDID>
```

**Requirements:** `pip install fb-idb` · `brew install idb-companion` · Xcode

---

### `tca-architect`

Design the architecture of a modular iOS app using [Swift Package Manager](https://www.swift.org/documentation/package-manager/) and [The Composable Architecture](https://github.com/pointfreeco/swift-composable-architecture) (TCA).

Use this skill when **starting a new project** or designing how to split an existing app into modules.

**Capabilities:**
- **Module decomposition** — split an app into infrastructure (`DesignSystem`, `Models`, `Services`) and feature modules with a clean dependency graph
- **Package.swift** — complete templates for multi-target SPM packages with external dependencies, test targets, and resource bundles
- **TCA patterns** — `@Reducer`, `@ObservableState`, async effects, `@Reducer enum Destination` navigation, delegate actions
- **Dependency injection** — `@DependencyClient` macro, manual struct clients, actor-based databases, live/test/mock implementations

---

### `tca-developer`

Implement new features in an existing modular TCA+SPM iOS app, following the exact conventions of the codebase.

Use this skill when **adding a screen or sub-feature** to an existing project.

**Capabilities:**
- **Reducer** — `@Reducer`, `@ObservableState`, async effects, `@Presents` navigation, delegate actions
- **View** — four-state body (loading/error/empty/content), navigation wiring, `Toggle` bindings, private sub-views, file-local components
- **SwiftUI previews** — one preview per meaningful state: loading, loaded, empty, error, and feature-specific variants (completed, failed, etc.)
- **Tests** — `TestStore` setup, dependency mocking, async flow assertions, computed property tests, idempotency tests
- **Registration** — `Package.swift` target additions and `AppCore` tab wiring

Both TCA skills derive their patterns from the [Sky107](https://github.com/ninjaproger/Sky107) reference project.

---

### `codex-agent`

Delegate complex, multi-step coding tasks to the [OpenAI Codex CLI](https://developers.openai.com/codex/cli/reference) agent running in the background.

Use this skill when you want to **offload autonomous work to Codex** — letting it read files, write code, and run shell commands without interrupting your session.

**Capabilities:**
- **TCA feature development** — prompt Codex to implement a full reducer + view + tests + Package.swift registration, pointing it at an existing feature for style reference
- **iOS Simulator automation** — prompt Codex to navigate the simulator using `ios_sim.py` (tap, scroll, screenshot, verify UI state)
- **Combined flows** — implement a feature *and* verify it in the simulator in a single Codex run

```bash
# Implement a TCA feature in the background
codex exec --full-auto --cd /path/to/your/project \
  "Add a Bookmarks feature following the style of Sources/Flashcards/. \
   Create reducer, view (4 previews), tests, and register in Package.swift."

# Automate the simulator
codex exec --full-auto \
  "Using python path/to/ios_sim.py, open the app on the booted simulator, \
   navigate to the Settings screen, and take a screenshot."
```

**Requirements:** `npm install -g @openai/codex` (or `brew install openai-codex`)

---

## Adding a Skill

1. Scaffold: `python ~/.claude/plugins/cache/anthropic-agent-skills/document-skills/<version>/skills/skill-creator/scripts/init_skill.py <skill-name> --path skills/`
2. Implement `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`)
3. Add scripts, references, and assets as needed; delete unused placeholder dirs
4. Register: add `"./skills/<skill-name>"` to the `skills` array of the relevant plugin in `.claude-plugin/marketplace.json`
5. Package: `python ... package_skill.py skills/<skill-name> .`
