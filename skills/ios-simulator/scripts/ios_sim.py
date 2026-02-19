#!/usr/bin/env python3
"""
ios_sim.py - iOS Simulator automation via idb and xcrun simctl

Navigation commands (tap, swipe, scroll, text, key, button, openurl) automatically
run `idb ui describe-all` before and after each action to validate UI state and
provide exact element coordinates.

Requirements:
  pip install fb-idb
  brew install idb-companion

Usage:
  python ios_sim.py <command> [options]

Run `python ios_sim.py --help` or `python ios_sim.py <command> --help` for details.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Optional

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: list, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def udid_flags(udid: Optional[str]) -> list:
    return ["--udid", udid] if udid else []


# ---------------------------------------------------------------------------
# describe-all helpers
# ---------------------------------------------------------------------------

def describe_all(udid: Optional[str]) -> list:
    """Return flat JSON list of all UI accessibility elements on screen."""
    cmd = ["idb", "ui", "describe-all", "--json"] + udid_flags(udid)
    result = run(cmd)
    return json.loads(result.stdout)


def find_element(elements: list, query: str) -> Optional[dict]:
    """
    Find a UI element by label, title, or value (case-insensitive).
    Tries exact match first, then partial match.
    """
    q = query.lower()
    for exact in (True, False):
        for e in elements:
            candidates = [
                (e.get("AXLabel") or "").lower(),
                (e.get("title") or "").lower(),
                (e.get("AXValue") or "").lower(),
            ]
            if exact:
                if q in candidates:
                    return e
            else:
                if any(q in c for c in candidates if c):
                    return e
    return None


def element_center(element: dict) -> tuple:
    """Return (cx, cy) center of an element's frame."""
    frame = element.get("frame", {})
    cx = frame.get("x", 0) + frame.get("width", 0) / 2
    cy = frame.get("y", 0) + frame.get("height", 0) / 2
    return cx, cy


def print_ui_summary(elements: list, label: str = "UI State") -> None:
    """Print a concise, human-readable accessibility summary."""
    sep = "─" * 56
    print(f"\n{sep}")
    print(f"  {label}")
    print(sep)

    app = next((e for e in elements if e.get("role") == "AXApplication"), None)
    if app:
        print(f"  App    : {app.get('AXLabel', '?')}")
    print(f"  Elements: {len(elements)}")

    INTERACTIVE = {
        "AXButton", "AXTextField", "AXSecureTextField", "AXTextArea",
        "AXPopUpButton", "AXMenuItem", "AXCell", "AXLink", "AXSwitch",
        "AXSegmentedControl", "AXSlider", "AXCheckBox",
    }
    interactive = [
        e for e in elements
        if e.get("role") in INTERACTIVE and e.get("enabled", True)
    ]
    if interactive:
        print(f"\n  Interactive ({len(interactive)}):")
        for e in interactive[:15]:
            text = (
                e.get("AXLabel")
                or e.get("title")
                or e.get("AXValue")
                or ""
            )
            role = e.get("type") or e.get("role") or "?"
            cx, cy = element_center(e)
            print(f"    [{role:<22s}] '{text}'  →  tap({cx:.0f}, {cy:.0f})")
        if len(interactive) > 15:
            print(f"    … and {len(interactive) - 15} more")
    print(sep)


def with_ui_hooks(udid: Optional[str], action_name: str, action_fn) -> tuple:
    """
    Execute a navigation action wrapped with pre/post describe-all hooks.
    Returns (pre_elements, post_elements).
    """
    print(f"\n▶ {action_name} — capturing PRE-action UI state …")
    pre = describe_all(udid)
    print_ui_summary(pre, f"PRE  | {action_name}")

    action_fn()

    time.sleep(1.0)  # wait for navigation transition animation to finish

    print(f"\n▶ {action_name} — capturing POST-action UI state …")
    post = describe_all(udid)
    print_ui_summary(post, f"POST | {action_name}")

    return pre, post


# ---------------------------------------------------------------------------
# Simulator management (xcrun simctl)
# ---------------------------------------------------------------------------

def cmd_list(_args) -> None:
    """List available iOS simulators."""
    result = run(["xcrun", "simctl", "list", "devices", "--json"])
    data = json.loads(result.stdout)
    print(f"\n{'UDID':<38}  {'State':<10}  {'Name'}")
    print("─" * 78)
    for runtime, devices in data["devices"].items():
        if not any(d.get("isAvailable") for d in devices):
            continue
        # Show runtime label
        rt_label = runtime.replace("com.apple.CoreSimulator.SimRuntime.", "")
        for d in devices:
            if not d.get("isAvailable"):
                continue
            state = "● BOOTED" if d["state"] == "Booted" else d["state"]
            print(f"{d['udid']}  {state:<10}  {d['name']}  [{rt_label}]")


def cmd_boot(args) -> None:
    """Boot a simulator."""
    print(f"Booting {args.udid} …")
    run(["xcrun", "simctl", "boot", args.udid])
    print("Done.")


def cmd_shutdown(args) -> None:
    """Shutdown a simulator."""
    print(f"Shutting down {args.udid} …")
    run(["xcrun", "simctl", "shutdown", args.udid])
    print("Done.")


# ---------------------------------------------------------------------------
# Build (xcodebuild)
# ---------------------------------------------------------------------------

def cmd_build(args) -> None:
    """Build an app for the simulator."""
    derived = args.derived_data or "/tmp/ios_sim_derived"
    os.makedirs(derived, exist_ok=True)

    if args.workspace:
        project_flags = ["-workspace", args.workspace]
    else:
        project_flags = ["-project", args.project]

    destination = (
        f"id={args.udid}" if args.udid
        else "platform=iOS Simulator,name=iPhone 16 Pro"
    )

    cmd = [
        "xcodebuild",
        *project_flags,
        "-scheme", args.scheme,
        "-sdk", "iphonesimulator",
        "-configuration", args.configuration,
        "-derivedDataPath", derived,
        f"-destination={destination}",
        "build",
    ]
    print("Building:", " ".join(cmd))
    run(cmd, capture=False)

    app_dir = os.path.join(derived, "Build", "Products", f"{args.configuration}-iphonesimulator")
    print(f"\nBuild products: {app_dir}")
    apps = [f for f in os.listdir(app_dir) if f.endswith(".app")] if os.path.isdir(app_dir) else []
    for a in apps:
        print(f"  → {os.path.join(app_dir, a)}")


# ---------------------------------------------------------------------------
# App management (idb / xcrun simctl)
# ---------------------------------------------------------------------------

def cmd_install(args) -> None:
    """Install an .app or .ipa on the simulator."""
    cmd = ["idb", "install", args.app_path] + udid_flags(args.udid)
    print(f"Installing {args.app_path} …")
    run(cmd, capture=False)
    print("Installed.")


def cmd_launch(args) -> None:
    """Launch an app by bundle ID."""
    cmd = ["idb", "launch", args.bundle_id] + udid_flags(args.udid)
    print(f"Launching {args.bundle_id} …")
    run(cmd)
    print(f"Launched {args.bundle_id}.")
    time.sleep(1.5)
    # Show initial UI state
    elements = describe_all(args.udid)
    print_ui_summary(elements, f"LAUNCHED | {args.bundle_id}")


def cmd_terminate(args) -> None:
    """Terminate a running app."""
    cmd = ["idb", "terminate", args.bundle_id] + udid_flags(args.udid)
    print(f"Terminating {args.bundle_id} …")
    run(cmd)
    print(f"Terminated {args.bundle_id}.")


def cmd_list_apps(args) -> None:
    """List installed apps."""
    cmd = ["idb", "list-apps", "--json", "--fetch-process-state"] + udid_flags(args.udid)
    result = run(cmd)
    apps = json.loads(result.stdout)
    print(f"\n{'Bundle ID':<50}  {'State':<12}  Name")
    print("─" * 80)
    for app in apps:
        state = app.get("process_state", "?")
        name = app.get("name") or app.get("bundle_id", "?")
        bid = app.get("bundle_id", "?")
        print(f"{bid:<50}  {state:<12}  {name}")


# ---------------------------------------------------------------------------
# Navigation commands — all wrapped with describe-all hooks
# ---------------------------------------------------------------------------

def cmd_tap(args) -> None:
    """Tap at (x, y) with pre/post UI validation."""
    def action():
        cmd = ["idb", "ui", "tap", str(args.x), str(args.y)] + udid_flags(args.udid)
        if args.duration:
            cmd += ["--duration", str(args.duration)]
        run(cmd)
        print(f"Tapped ({args.x}, {args.y})")

    with_ui_hooks(args.udid, f"tap({args.x}, {args.y})", action)


def cmd_tap_element(args) -> None:
    """
    Find a UI element by label (using describe-all) and tap its center.
    This is the preferred way to tap since it uses live coordinates.
    """
    print(f"\n▶ tap-element '{args.label}' — running describe-all to find target …")
    elements = describe_all(args.udid)
    print_ui_summary(elements, f"PRE  | tap-element '{args.label}'")

    elem = find_element(elements, args.label)
    if elem is None:
        print(f"ERROR: No element found matching '{args.label}'", file=sys.stderr)
        print("Available labels:")
        for e in elements:
            lbl = e.get("AXLabel") or e.get("title") or e.get("AXValue") or ""
            if lbl:
                print(f"  [{e.get('type', e.get('role'))}] '{lbl}'")
        sys.exit(1)

    cx, cy = element_center(elem)
    role = elem.get("type") or elem.get("role") or "?"
    lbl = elem.get("AXLabel") or elem.get("title") or ""
    print(f"\nFound: [{role}] '{lbl}'  →  tapping ({cx:.0f}, {cy:.0f})")

    cmd = ["idb", "ui", "tap", str(int(cx)), str(int(cy))] + udid_flags(args.udid)
    run(cmd)

    time.sleep(1.0)  # wait for navigation transition animation to finish
    post = describe_all(args.udid)
    print_ui_summary(post, f"POST | tap-element '{args.label}'")


def cmd_swipe(args) -> None:
    """Swipe from (x1,y1) to (x2,y2) with pre/post UI validation."""
    def action():
        cmd = [
            "idb", "ui", "swipe",
            str(args.x1), str(args.y1),
            str(args.x2), str(args.y2),
        ] + udid_flags(args.udid)
        if args.duration:
            cmd += ["--duration", str(args.duration)]
        if args.delta:
            cmd += ["--delta", str(args.delta)]
        run(cmd)
        print(f"Swiped ({args.x1},{args.y1}) → ({args.x2},{args.y2})")

    with_ui_hooks(args.udid, f"swipe({args.x1},{args.y1}→{args.x2},{args.y2})", action)


def cmd_scroll(args) -> None:
    """
    Scroll in a direction using a swipe gesture.

    Direction semantics (matches physical gesture):
      down  → finger swipes up   (reveals content below current view)
      up    → finger swipes down (reveals content above current view)
      left  → finger swipes right (reveals content to the left)
      right → finger swipes left  (reveals content to the right)
    """
    # Probe screen dimensions from describe-all
    elements = describe_all(args.udid)
    app = next((e for e in elements if e.get("role") == "AXApplication"), None)
    if app:
        frame = app.get("frame", {})
        w = frame.get("width", 390)
        h = frame.get("height", 844)
    else:
        w, h = 390, 844

    cx, cy = w / 2, h / 2
    dist = args.distance  # swipe distance in points

    direction_map = {
        "down":  (cx, cy + dist / 2, cx, cy - dist / 2),   # finger moves up
        "up":    (cx, cy - dist / 2, cx, cy + dist / 2),   # finger moves down
        "left":  (cx + dist / 2, cy, cx - dist / 2, cy),   # finger moves left
        "right": (cx - dist / 2, cy, cx + dist / 2, cy),   # finger moves right
    }
    x1, y1, x2, y2 = direction_map[args.direction]
    x1, y1, x2, y2 = max(0, x1), max(0, y1), max(0, x2), max(0, y2)

    def action():
        cmd = [
            "idb", "ui", "swipe",
            str(int(x1)), str(int(y1)),
            str(int(x2)), str(int(y2)),
            "--duration", str(args.speed),
        ] + udid_flags(args.udid)
        run(cmd)
        print(f"Scrolled {args.direction}: swipe ({int(x1)},{int(y1)}) → ({int(x2)},{int(y2)})")

    print_ui_summary(elements, f"PRE  | scroll-{args.direction}")
    action()
    time.sleep(1.0)  # wait for navigation transition animation to finish
    post = describe_all(args.udid)
    print_ui_summary(post, f"POST | scroll-{args.direction}")


def cmd_text(args) -> None:
    """Type text with pre/post UI validation."""
    def action():
        cmd = ["idb", "ui", "text", args.text] + udid_flags(args.udid)
        run(cmd)
        print(f"Typed: {args.text!r}")

    with_ui_hooks(args.udid, f"text({args.text!r})", action)


def cmd_key(args) -> None:
    """Press a key by keycode with pre/post UI validation."""
    NAMED_KEYS = {
        "enter": 40, "return": 40,
        "backspace": 42, "delete": 42,
        "tab": 43,
        "space": 44,
        "escape": 41,
        "right": 79, "left": 80, "down": 81, "up": 82,
        "home": 74, "end": 77,
        "f1": 58, "f2": 59, "f3": 60, "f4": 61,
    }
    key_val = args.key
    if isinstance(key_val, str) and not key_val.isdigit():
        key_val = str(NAMED_KEYS.get(key_val.lower(), key_val))

    def action():
        cmd = ["idb", "ui", "key", str(key_val)] + udid_flags(args.udid)
        run(cmd)
        print(f"Key press: {args.key} (code {key_val})")

    with_ui_hooks(args.udid, f"key({args.key})", action)


def cmd_button(args) -> None:
    """Press a hardware button (HOME, LOCK, SIRI, SIDE_BUTTON, APPLE_PAY)."""
    valid = {"APPLE_PAY", "HOME", "LOCK", "SIDE_BUTTON", "SIRI"}
    button = args.button.upper()
    if button not in valid:
        print(f"ERROR: Invalid button '{button}'. Choose from: {valid}", file=sys.stderr)
        sys.exit(1)

    def action():
        cmd = ["idb", "ui", "button", button] + udid_flags(args.udid)
        run(cmd)
        print(f"Button: {button}")

    with_ui_hooks(args.udid, f"button({button})", action)


def cmd_openurl(args) -> None:
    """Open a URL in the simulator with pre/post UI validation."""
    def action():
        cmd = ["idb", "open", args.url] + udid_flags(args.udid)
        run(cmd)
        print(f"Opened URL: {args.url}")

    with_ui_hooks(args.udid, f"openurl({args.url})", action)


# ---------------------------------------------------------------------------
# Inspection commands
# ---------------------------------------------------------------------------

def cmd_describe(args) -> None:
    """Dump all UI elements with coordinates (describe-all)."""
    elements = describe_all(args.udid)

    if args.json:
        print(json.dumps(elements, indent=2))
        return

    print_ui_summary(elements, "Full UI Accessibility Tree")

    if args.verbose:
        print("\nAll elements:")
        for e in elements:
            label = e.get("AXLabel") or e.get("title") or e.get("AXValue") or ""
            role = e.get("type") or e.get("role") or "?"
            frame = e.get("frame", {})
            cx, cy = element_center(e)
            enabled = "enabled" if e.get("enabled", True) else "disabled"
            print(f"  [{role:<24}] '{label}'  frame=({frame.get('x',0):.0f},{frame.get('y',0):.0f},{frame.get('width',0):.0f}×{frame.get('height',0):.0f})  center=({cx:.0f},{cy:.0f})  {enabled}")


def cmd_find(args) -> None:
    """Find a UI element by label and print its tap coordinates."""
    elements = describe_all(args.udid)
    elem = find_element(elements, args.label)
    if elem is None:
        print(f"No element found for '{args.label}'")
        print("\nAvailable labels:")
        for e in elements:
            lbl = e.get("AXLabel") or e.get("title") or e.get("AXValue") or ""
            if lbl:
                role = e.get("type") or e.get("role") or "?"
                cx, cy = element_center(e)
                print(f"  [{role}] '{lbl}'  center=({cx:.0f},{cy:.0f})")
        sys.exit(1)

    cx, cy = element_center(elem)
    role = elem.get("type") or elem.get("role") or "?"
    lbl = elem.get("AXLabel") or elem.get("title") or elem.get("AXValue") or ""
    frame = elem.get("frame", {})

    print(f"\nFound: [{role}] '{lbl}'")
    print(f"  Frame : x={frame.get('x',0):.0f}, y={frame.get('y',0):.0f}, "
          f"w={frame.get('width',0):.0f}, h={frame.get('height',0):.0f}")
    print(f"  Center: ({cx:.0f}, {cy:.0f})")
    print(f"  Tap   : idb ui tap {int(cx)} {int(cy)}")
    if args.udid:
        print(f"          (add --udid {args.udid})")


def cmd_screenshot(args) -> None:
    """Take a screenshot."""
    cmd = ["idb", "screenshot", args.path] + udid_flags(args.udid)
    run(cmd)
    print(f"Screenshot saved: {args.path}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="iOS Simulator automation via idb + xcrun simctl",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---- Simulator management ----
    sub.add_parser("list", help="List available simulators")

    p = sub.add_parser("boot", help="Boot a simulator")
    p.add_argument("udid", help="Simulator UDID")

    p = sub.add_parser("shutdown", help="Shutdown a simulator")
    p.add_argument("udid", help="Simulator UDID")

    # ---- Build ----
    p = sub.add_parser("build", help="Build app for simulator via xcodebuild")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--project", "-p", help=".xcodeproj path")
    grp.add_argument("--workspace", "-w", help=".xcworkspace path")
    p.add_argument("--scheme", "-s", required=True)
    p.add_argument("--configuration", "-c", default="Debug")
    p.add_argument("--derived-data", "-d", help="DerivedData path (default /tmp/ios_sim_derived)")
    p.add_argument("--udid", help="Target simulator UDID")

    # ---- App management ----
    p = sub.add_parser("install", help="Install .app or .ipa")
    p.add_argument("app_path", help="Path to .app bundle or .ipa")
    p.add_argument("--udid", help="Target simulator UDID")

    p = sub.add_parser("launch", help="Launch app by bundle ID")
    p.add_argument("bundle_id")
    p.add_argument("--udid")

    p = sub.add_parser("terminate", help="Terminate running app")
    p.add_argument("bundle_id")
    p.add_argument("--udid")

    p = sub.add_parser("list-apps", help="List installed apps")
    p.add_argument("--udid")

    # ---- Navigation (all use describe-all hooks) ----
    p = sub.add_parser("tap", help="Tap at x,y coordinates")
    p.add_argument("x", type=float)
    p.add_argument("y", type=float)
    p.add_argument("--duration", type=float)
    p.add_argument("--udid")

    p = sub.add_parser("tap-element", help="Find element by label and tap its center")
    p.add_argument("label", help="AXLabel, title, or value to search for")
    p.add_argument("--udid")

    p = sub.add_parser("swipe", help="Swipe from (x1,y1) to (x2,y2)")
    p.add_argument("x1", type=float)
    p.add_argument("y1", type=float)
    p.add_argument("x2", type=float)
    p.add_argument("y2", type=float)
    p.add_argument("--duration", type=float, help="Swipe duration in seconds")
    p.add_argument("--delta", type=int, help="Pixels between touch points")
    p.add_argument("--udid")

    p = sub.add_parser("scroll", help="Scroll in a direction")
    p.add_argument("direction", choices=["up", "down", "left", "right"])
    p.add_argument("--distance", type=float, default=300,
                   help="Scroll distance in points (default 300)")
    p.add_argument("--speed", type=float, default=0.4,
                   help="Swipe duration in seconds (default 0.4; lower = faster)")
    p.add_argument("--udid")

    p = sub.add_parser("text", help="Type text into focused element")
    p.add_argument("text")
    p.add_argument("--udid")

    p = sub.add_parser("key", help="Press a key by keycode or name (enter, backspace, tab, …)")
    p.add_argument("key")
    p.add_argument("--udid")

    p = sub.add_parser("button", help="Press hardware button: HOME, LOCK, SIRI, SIDE_BUTTON, APPLE_PAY")
    p.add_argument("button")
    p.add_argument("--udid")

    p = sub.add_parser("openurl", help="Open a URL (http/https or deep-link scheme)")
    p.add_argument("url")
    p.add_argument("--udid")

    # ---- Inspection ----
    p = sub.add_parser("describe", help="Describe all UI elements on screen")
    p.add_argument("--json", action="store_true", help="Raw JSON output")
    p.add_argument("--verbose", "-v", action="store_true", help="Show all elements")
    p.add_argument("--udid")

    p = sub.add_parser("find", help="Find element by label and print tap coordinates")
    p.add_argument("label")
    p.add_argument("--udid")

    p = sub.add_parser("screenshot", help="Take a screenshot")
    p.add_argument("path", help="Output file path (.png)")
    p.add_argument("--udid")

    return parser


COMMANDS = {
    "list": cmd_list,
    "boot": cmd_boot,
    "shutdown": cmd_shutdown,
    "build": cmd_build,
    "install": cmd_install,
    "launch": cmd_launch,
    "terminate": cmd_terminate,
    "list-apps": cmd_list_apps,
    "tap": cmd_tap,
    "tap-element": cmd_tap_element,
    "swipe": cmd_swipe,
    "scroll": cmd_scroll,
    "text": cmd_text,
    "key": cmd_key,
    "button": cmd_button,
    "openurl": cmd_openurl,
    "describe": cmd_describe,
    "find": cmd_find,
    "screenshot": cmd_screenshot,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
