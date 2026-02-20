# skills

A personal Claude Code plugin marketplace with skills for iOS development and automation.

## Installation

Register this repository as a Claude Code plugin marketplace:

```
/plugin marketplace add <git-remote-url>
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

### `tca-architect`

Architect modular iOS apps using [Swift Package Manager](https://www.swift.org/documentation/package-manager/) and [The Composable Architecture](https://github.com/pointfreeco/swift-composable-architecture) (TCA).

**Capabilities:**
- **Module decomposition** — split an app into infrastructure (`DesignSystem`, `Models`, `Services`) and feature modules with a clean dependency graph
- **Package.swift** — complete templates for multi-target SPM packages with external dependencies, test targets, and resource bundles
- **TCA reducers** — `@Reducer`, `@ObservableState`, async effects with `Result { }`, cancellation
- **Navigation** — `@Reducer enum Destination` + `@Presents` + `ifLet` for push/sheet/alert from a single parent
- **Delegate actions** — child→parent communication pattern, multi-level delegate chains, cross-tab events
- **Dependency injection** — `@DependencyClient` macro, manual struct clients, actor-based databases, live/test/mock implementations

Patterns are derived from a real-world reference project ([Sky107](https://github.com/ninjaproger/Sky107)).

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Add `"./skills/<skill-name>"` to the `skills` array of the relevant plugin in `.claude-plugin/marketplace.json`
