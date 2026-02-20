---
name: tca-developer
description: >
  Develop new features in a modular iOS app using The Composable Architecture (TCA) and Swift
  Package Manager. Use when implementing a new screen, adding a sub-feature, extending an existing
  reducer, adding SwiftUI previews, or writing TCA tests. Covers the full development workflow:
  reading the existing codebase, creating reducer + view files, wiring navigation, writing SwiftUI
  previews for all meaningful states (loaded, empty, error, and feature-specific variants), and
  writing TestStore tests. Always explore the target module before writing code to match its
  existing style and conventions.
---

# TCA Feature Development

## Workflow

1. **Explore first** — read the target module and its neighbours before writing anything
2. **Create the reducer** — see `references/feature-template.md`
3. **Create the view** — see `references/view-patterns.md`
4. **Add previews** — one per meaningful state; see Preview Rules below
5. **Write tests** — see `references/testing-patterns.md`
6. **Register** — add target to `Package.swift`; wire into parent if it's a new tab

## Explore Before Writing

Before implementing any feature, read:
- An existing feature's reducer + view (understand current patterns)
- The parent module (understand how this feature is composed in)
- `Sources/Services/` for available dependency clients
- `Sources/Models/` for the relevant data types

## Reducer Checklist

- `@Reducer` macro on a `struct`
- `@ObservableState` on `State`, which conforms to `Equatable`
- `public init() {}` when all state fields have defaults; explicit memberwise init otherwise
- Idempotency guard in `.onAppear`: `guard state.data == nil else { return .none }`
- `@Reducer enum Destination` when the feature navigates to children (`@Presents` + `ifLet`)
- `delegate(Delegate)` action + `@CasePathable enum Delegate` for upward communication
- `case .delegate: return .none` — the reducer always ignores its own delegate cases
- Capture dependencies explicitly in `.run`: `[client = someClient]`
- Errors stored as `String?` via `error.localizedDescription`, not as `Error` type

## View Checklist

- `@Bindable var store: StoreOf<FeatureReducer>` — always `@Bindable`
- `public init(store:)` — always explicit public init
- `store.send(.onAppear)` in `.onAppear` modifier
- Use `Group { }` for multi-branch body (loading / error / empty / content)
- Use `ContentUnavailableView` for error and empty states
- Wire navigation destinations with `$store.scope(state:action:)`
- Toggle bindings: `Binding(get: { store.flag }, set: { _ in store.send(.toggleFlag) })`
- Break complex body into `@ViewBuilder private var` computed properties

## Preview Rules

Every view **must** have at minimum:
1. A **default/loading** preview — `State()` with live reducer (triggers `.onAppear`)
2. A **content** preview — pre-built state with representative sample data
3. An **empty state** preview — empty collections, zero-progress state
4. Any **feature-specific variants** that render meaningfully different UI (error, completed, failed, passed, etc.)

```swift
// Pattern A — live reducer, fires onAppear
#Preview("FeatureName") {
    NavigationStack {
        FeatureView(store: Store(initialState: .init()) { FeatureReducer() })
    }
}

// Pattern B — pre-built state with data
#Preview("FeatureName - Loaded") {
    var state = FeatureReducer.State()
    state.items = [.sample1, .sample2]
    return NavigationStack {
        FeatureView(store: Store(initialState: state) { FeatureReducer() })
    }
}

// Pattern C — empty state
#Preview("FeatureName - Empty") {
    var state = FeatureReducer.State()
    state.items = []
    state.isLoading = false
    return NavigationStack {
        FeatureView(store: Store(initialState: state) { FeatureReducer() })
    }
}

// Pattern D — error state
#Preview("FeatureName - Error") {
    var state = FeatureReducer.State()
    state.loadError = "Failed to load data"
    return NavigationStack {
        FeatureView(store: Store(initialState: state) { FeatureReducer() })
    }
}
```

- Wrap in `NavigationStack { }` when the view uses `.navigationTitle` or `.navigationDestination`
- Preview name format: `"FeatureName - StateName"` e.g. `"Quiz - Partially Answered"`
- Do **not** use `withDependencies` in previews — use the live reducer directly
- Add `static var sample: Self` / `static var samples: [Self]` on model types for preview data

## Key Decisions

| Question | Answer |
|----------|--------|
| Reducer + View in one file? | Yes, when combined ≤ ~200 lines |
| Where do computed properties go? | On `State`, not the view |
| How to pass data to a child feature? | Initialize child's `State` when setting `destination` |
| How to communicate upward? | `.delegate(Delegate)` action |
| Where does error text live? | `state.loadError: String?` via `error.localizedDescription` |
| How to cancel in-flight effects? | `.cancellable(id:, cancelInFlight: true)` |
| Where do sub-view components live? | File-private structs in the same `.swift` file |

## Reference Files

- **`references/feature-template.md`** — Complete file templates: reducer, view with previews, tests, Package.swift snippet, AppCore wiring. Read when starting a new feature from scratch.
- **`references/view-patterns.md`** — View sub-patterns: loading/error/empty states, navigation wiring, Toggle binding, private sub-views, file-local components, animation. Read when implementing or refining a view.
- **`references/testing-patterns.md`** — TestStore setup, dependency mocking, async flow testing, delegate testing, computed property tests, idempotency tests. Read when writing or debugging tests.
