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

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Add `"./skills/<skill-name>"` to the `skills` array of the relevant plugin in `.claude-plugin/marketplace.json`
