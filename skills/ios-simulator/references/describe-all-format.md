# idb ui describe-all — Output Format Reference

## Table of Contents
1. [Command Usage](#command-usage)
2. [Flat Format (default)](#flat-format-default)
3. [Nested Format](#nested-format)
4. [Element Fields](#element-fields)
5. [Common Role Values](#common-role-values)
6. [Computing Tap Coordinates](#computing-tap-coordinates)
7. [Searching for Elements](#searching-for-elements)
8. [Example Output](#example-output)

---

## Command Usage

```bash
# Flat list of all elements (default)
idb ui describe-all --json --udid <UDID>

# Nested tree (elements have children array)
idb ui describe-all --json --nested --udid <UDID>

# Describe a single element at a point
idb ui describe-point <x> <y> --json --udid <UDID>
```

---

## Flat Format (default)

Returns a **JSON array** of all accessibility elements on screen as a flat list.
The first element is always the Application root.

```json
[
  {
    "AXFrame": "{{0, 0}, {402, 874}}",
    "AXUniqueId": null,
    "frame": { "y": 0, "x": 0, "width": 402, "height": 874 },
    "role_description": "application",
    "AXLabel": "MyApp",
    "content_required": false,
    "type": "Application",
    "title": null,
    "help": null,
    "custom_actions": [],
    "AXValue": null,
    "enabled": true,
    "role": "AXApplication",
    "subrole": null
  },
  {
    "AXFrame": "{{14.5, 280}, {373, 365}}",
    "AXUniqueId": null,
    "frame": { "y": 280.83, "x": 14.5, "width": 373, "height": 365.67 },
    "role_description": "button",
    "AXLabel": "Submit",
    "content_required": false,
    "type": "Button",
    "title": null,
    "help": "Tap to submit",
    "custom_actions": [],
    "AXValue": null,
    "enabled": true,
    "role": "AXButton",
    "subrole": null
  }
]
```

---

## Nested Format

With `--nested`, each element gains a `children` array containing child elements.
The `subrole` field is present at the top level instead of inside the element.

```json
[
  {
    "role": "AXApplication",
    "AXLabel": "MyApp",
    "frame": { "y": 0, "x": 0, "width": 402, "height": 874 },
    "children": [
      {
        "role": "AXButton",
        "AXLabel": "Submit",
        "frame": { "y": 280.83, "x": 14.5, "width": 373, "height": 365.67 },
        "children": [],
        ...
      }
    ]
  }
]
```

---

## Element Fields

| Field | Type | Description |
|---|---|---|
| `frame` | object | Bounding rect in **logical points** (not pixels) |
| `frame.x` | float | Left edge x-coordinate |
| `frame.y` | float | Top edge y-coordinate |
| `frame.width` | float | Element width |
| `frame.height` | float | Element height |
| `AXFrame` | string | Same as frame, as a string: `"{{x, y}, {w, h}}"` |
| `role` | string | Accessibility role (e.g. `AXButton`, `AXTextField`) |
| `type` | string | Human-readable type (e.g. `Button`, `TextField`) |
| `role_description` | string | Readable description (e.g. `"button"`, `"text field"`) |
| `AXLabel` | string\|null | Primary accessibility label (what VoiceOver reads) |
| `title` | string\|null | Element title (often null, use AXLabel instead) |
| `AXValue` | string\|null | Current value (text field content, toggle state, etc.) |
| `AXUniqueId` | string\|null | Unique element identifier (set by developer, often null) |
| `help` | string\|null | Accessibility hint |
| `enabled` | bool | Whether the element accepts interaction |
| `content_required` | bool | AXRequiredAttribute |
| `custom_actions` | array | Custom accessibility actions |
| `subrole` | string\|null | Accessibility subrole |
| `children` | array | Child elements (nested format only) |

---

## Common Role Values

| `role` | `type` | Description |
|---|---|---|
| `AXApplication` | `Application` | Root application element |
| `AXButton` | `Button` | Tappable button |
| `AXTextField` | `TextField` | Single-line text input |
| `AXSecureTextField` | `SecureTextField` | Password input |
| `AXTextArea` | `TextArea` | Multi-line text input |
| `AXStaticText` | `StaticText` | Non-interactive text label |
| `AXHeading` | `Heading` | Section heading |
| `AXImage` | `Image` | Image element |
| `AXCell` | `Cell` | Table/collection cell |
| `AXGroup` | `Group` | Grouping element |
| `AXScrollArea` | `ScrollArea` | Scrollable container |
| `AXPopUpButton` | `PopUpButton` | Dropdown / picker button |
| `AXLink` | `Link` | Hyperlink |
| `AXSwitch` | `Switch` | Toggle switch |
| `AXSlider` | `Slider` | Slider control |
| `AXSegmentedControl` | `SegmentedControl` | Segmented picker |
| `AXCheckBox` | `CheckBox` | Checkbox / radio button |
| `AXProgressIndicator` | `ProgressIndicator` | Progress bar |
| `AXWebArea` | `WebArea` | Web content container |
| `AXTabGroup` | `TabGroup` | Tab bar |
| `AXNavigationBar` | `NavigationBar` | Navigation bar |

---

## Computing Tap Coordinates

All coordinates in `frame` are in **logical points**. Pass these directly to `idb ui tap`.

```python
def element_center(element: dict) -> tuple[float, float]:
    frame = element["frame"]
    cx = frame["x"] + frame["width"] / 2
    cy = frame["y"] + frame["height"] / 2
    return cx, cy

# Then tap:
cx, cy = element_center(element)
subprocess.run(["idb", "ui", "tap", str(int(cx)), str(int(cy)), "--udid", udid])
```

**Key point**: logical points ≠ pixels. A 3x Retina screen with 1242px width has 414pt width.
Always use point values from `frame`, never pixel values.

---

## Searching for Elements

```python
def find_by_label(elements: list, query: str) -> dict | None:
    q = query.lower()
    # Exact match first
    for e in elements:
        if q in [
            (e.get("AXLabel") or "").lower(),
            (e.get("title") or "").lower(),
            (e.get("AXValue") or "").lower(),
        ]:
            return e
    # Partial match
    for e in elements:
        texts = [
            (e.get("AXLabel") or "").lower(),
            (e.get("title") or "").lower(),
            (e.get("AXValue") or "").lower(),
        ]
        if any(q in t for t in texts if t):
            return e
    return None

def find_by_role(elements: list, role: str) -> list:
    return [e for e in elements if e.get("role") == role]

def find_interactive(elements: list) -> list:
    INTERACTIVE = {
        "AXButton", "AXTextField", "AXSecureTextField", "AXTextArea",
        "AXPopUpButton", "AXCell", "AXLink", "AXSwitch",
    }
    return [e for e in elements if e.get("role") in INTERACTIVE and e.get("enabled", True)]
```

---

## Example Output

Real output from a booted simulator running a flashcard app:

```json
[
  {"role": "AXApplication", "AXLabel": "Flashcards", "frame": {"y": 0, "x": 0, "width": 402, "height": 874}},
  {"role": "AXPopUpButton", "AXLabel": "Filter", "frame": {"y": 66, "x": 349, "width": 30, "height": 36}},
  {"role": "AXHeading", "AXLabel": "My Deck", "frame": {"y": 119.67, "x": 16, "width": 173.33, "height": 40.67}},
  {"role": "AXStaticText", "AXLabel": "4/144", "frame": {"y": 200, "x": 174.17, "width": 53.67, "height": 24}},
  {"role": "AXButton", "AXLabel": "Question", "frame": {"y": 280.83, "x": 14.5, "width": 373, "height": 365.67}},
  {"role": "AXButton", "AXLabel": "Go Left", "frame": {"y": 681, "x": 129, "width": 52, "height": 50}},
  {"role": "AXButton", "AXLabel": "Go Right", "frame": {"y": 681, "x": 221, "width": 52, "height": 50}},
  {"role": "AXGroup", "AXLabel": "Tab Bar", "frame": {"y": 791, "x": 0, "width": 402, "height": 83}}
]
```

To tap the "Question" button:
- `cx = 14.5 + 373/2 = 201`
- `cy = 280.83 + 365.67/2 = 463`
- Command: `idb ui tap 201 463 --udid <UDID>`
