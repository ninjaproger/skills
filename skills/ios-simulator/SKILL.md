---
name: ios-simulator
description: >
  Automate iOS simulators: build, install, launch, terminate, and navigate (tap, swipe, scroll,
  type text, press keys, open URLs, press HOME/LOCK/SIRI) using idb and xcrun simctl.
  Use when asked to interact with an iOS app in the simulator, automate UI flows, run a
  navigation sequence, take screenshots, or inspect the UI accessibility tree.
  All navigation commands use `idb ui describe-all` before and after each action to validate
  the current UI state and obtain exact tap coordinates.
---

# iOS Simulator Skill

## Quick Start

```bash
# 1. List simulators and find a booted one
python scripts/ios_sim.py list

# 2. Boot (if not already booted)
python scripts/ios_sim.py boot <UDID>

# 3. Build app (if you have source)
python scripts/ios_sim.py build --project MyApp.xcodeproj --scheme MyApp

# 4. Install + launch
python scripts/ios_sim.py install /path/to/MyApp.app --udid <UDID>
python scripts/ios_sim.py launch com.example.MyApp --udid <UDID>

# 5. Inspect the current screen
python scripts/ios_sim.py describe --udid <UDID>

# 6. Tap by element label (recommended — uses live describe-all for coordinates)
python scripts/ios_sim.py tap-element "Sign In" --udid <UDID>

# 7. Tap at explicit coordinates
python scripts/ios_sim.py tap 195 422 --udid <UDID>

# 8. Type text, press Enter
python scripts/ios_sim.py text "hello@example.com" --udid <UDID>
python scripts/ios_sim.py key enter --udid <UDID>

# 9. Scroll / swipe
python scripts/ios_sim.py scroll down --udid <UDID>
python scripts/ios_sim.py swipe 195 700 195 200 --duration 0.5 --udid <UDID>

# 10. Open a URL or deep link
python scripts/ios_sim.py openurl "myapp://home" --udid <UDID>

# 11. Screenshot
python scripts/ios_sim.py screenshot /tmp/screen.png --udid <UDID>
```

---

## describe-all Hook Pattern

Every navigation command (`tap`, `tap-element`, `swipe`, `scroll`, `text`, `key`, `button`, `openurl`)
automatically runs `idb ui describe-all --json` **before** and **after** the action.

This achieves two goals:
1. **Pre-hook**: confirms which screen is active and reveals exact element coordinates
2. **Post-hook**: validates the action had the expected effect (screen changed, element appeared/disappeared)

The `tap-element` command uses the pre-hook describe-all to dynamically locate the element by
`AXLabel` / `title` / `AXValue` and computes its center coordinates — no hardcoded pixel coordinates needed.

> See `references/describe-all-format.md` for the full JSON schema and coordinate math.

---

## All Commands

### Simulator Lifecycle

| Command | Description |
|---|---|
| `list` | List all available simulators with UDIDs and boot states |
| `boot <udid>` | Boot a simulator |
| `shutdown <udid>` | Shut down a simulator |

### App Management

| Command | Description |
|---|---|
| `build --project P --scheme S [--udid U] [--derived-data D]` | Build app via xcodebuild for iphonesimulator |
| `install <app_path> [--udid U]` | Install .app bundle or .ipa |
| `launch <bundle_id> [--udid U]` | Launch app; shows initial UI state |
| `terminate <bundle_id> [--udid U]` | Terminate running app |
| `list-apps [--udid U]` | List installed apps and their running state |

### Navigation (all include describe-all hooks)

| Command | Description |
|---|---|
| `tap-element <label> [--udid U]` | **Preferred**: find element by label, tap center |
| `tap <x> <y> [--duration S] [--udid U]` | Tap at specific coordinates (points) |
| `swipe <x1> <y1> <x2> <y2> [--duration S] [--delta N] [--udid U]` | Swipe gesture |
| `scroll <direction> [--distance N] [--speed S] [--udid U]` | Directional scroll (up/down/left/right) |
| `text <text> [--udid U]` | Type text into focused element |
| `key <keycode_or_name> [--udid U]` | Press key: `enter`, `backspace`, `tab`, `up/down/left/right`, or numeric HID code |
| `button <name> [--udid U]` | Hardware button: `HOME`, `LOCK`, `SIRI`, `SIDE_BUTTON`, `APPLE_PAY` |
| `openurl <url> [--udid U]` | Open URL (http, https, or custom scheme deep link) |

### Inspection

| Command | Description |
|---|---|
| `describe [--json] [-v] [--udid U]` | Show UI accessibility tree summary (or raw JSON) |
| `find <label> [--udid U]` | Locate element by label, print frame + tap coordinates |
| `screenshot <path> [--udid U]` | Save screenshot to file |

---

## Scroll Direction Reference

`scroll` uses `idb ui swipe` internally. Directions match the **content movement** the user sees:

| `direction` | Finger movement | Content reveals |
|---|---|---|
| `down` | finger swipes up | content below |
| `up` | finger swipes down | content above |
| `left` | finger swipes right | content to the left |
| `right` | finger swipes left | content to the right |

Adjust `--distance` (default 300pt) and `--speed` (default 0.4s) for faster/slower scrolls.

---

## Build Output Location

After `build`, the `.app` bundle is at:
```
<derived-data>/Build/Products/<Configuration>-iphonesimulator/MyApp.app
```
Default `derived-data` is `/tmp/ios_sim_derived`.

For workspaces (CocoaPods/SPM):
```bash
python scripts/ios_sim.py build --workspace MyApp.xcworkspace --scheme MyApp
```

---

## References

- **`references/describe-all-format.md`** — Full JSON schema for `idb ui describe-all` output, coordinate math, element field reference, and search patterns. Read this when building custom element-finding logic.
