---
name: tca-architect
description: >
  Architect modular iOS apps using Swift Package Manager and The Composable Architecture (TCA).
  Use when designing or implementing a new iOS app (or feature module) that should be split into
  separate SPM packages, each owning a TCA feature reducer, view, and tests. Covers the full
  workflow: module decomposition, Package.swift dependency graph, reducer/view/navigation patterns,
  dependency injection via swift-dependencies, and the delegate action pattern for cross-module
  communication. Trigger when the user asks to: architect a TCA app, create a new SPM module/feature,
  set up a modular iOS project, add a feature to an existing TCA app, wire navigation between features,
  or design a dependency client.
---

# TCA + SPM Modular Architecture

## Project Layout

```
MyApp/
├── MyApp/                   # Xcode app target — THIN HOST ONLY (~16 lines)
│   └── MyApp.swift          # @main — creates one Store, renders root view
└── MyAppKit/                # Single SPM package containing ALL code
    ├── Package.swift
    ├── Sources/
    │   ├── AppCore/         # Root reducer + root view, composes all tab features
    │   ├── DesignSystem/    # Tokens, colors, fonts — no TCA dependency
    │   ├── Models/          # Pure Swift value types — no TCA, no UI
    │   ├── Services/        # Dependency clients + actors — no UI
    │   └── <Feature>/       # One module per feature (tab or sub-feature)
    └── Tests/
        └── <Feature>Tests/
```

**Rule**: The Xcode target never contains business logic. All code lives in the SPM package and is fully testable without a simulator.

## Workflow

1. **Decompose features** → Read `references/module-design.md`
2. **Set up Package.swift** → Read `references/module-design.md` (Package.swift section)
3. **Implement reducers/views/navigation** → Read `references/tca-patterns.md`
4. **Define dependency clients** → Read `references/dependency-patterns.md`
5. **Wire root AppCore** → See App Entry Point below

## App Entry Point

```swift
// MyApp/MyAppApp.swift
import ComposableArchitecture
import AppCore
import SwiftUI

@main
struct MyApp: App {
    let store = Store(initialState: AppCoreReducer.State()) {
        AppCoreReducer()
    }
    var body: some Scene {
        WindowGroup { AppCoreView(store: store) }
    }
}
```

## AppCore (Root Reducer + TabView)

`AppCore` imports every tab feature and composes them with `Scope`. The `Reduce` block at the end handles cross-feature logic by intercepting child delegate actions.

```swift
// Sources/AppCore/AppCoreView.swift
@Reducer
public struct AppCoreReducer {
    public enum Tab: Hashable { case home, profile, settings }

    @ObservableState
    public struct State: Equatable {
        var selectedTab: Tab = .home
        var home    = HomeReducer.State()
        var profile = ProfileReducer.State()
        var settings = SettingsReducer.State()
        public init() {}
    }

    public enum Action {
        case selectedTabChanged(Tab)
        case home(HomeReducer.Action)
        case profile(ProfileReducer.Action)
        case settings(SettingsReducer.Action)
    }

    public var body: some ReducerOf<Self> {
        Scope(state: \.home,     action: \.home)     { HomeReducer()     }
        Scope(state: \.profile,  action: \.profile)  { ProfileReducer()  }
        Scope(state: \.settings, action: \.settings) { SettingsReducer() }

        Reduce { state, action in
            switch action {
            case .selectedTabChanged(let tab):
                state.selectedTab = tab; return .none
            case .settings(.delegate(.loggedOut)):
                state.selectedTab = .home; return .none
            case .home, .profile, .settings:
                return .none
            }
        }
    }
}

public struct AppCoreView: View {
    @Bindable var store: StoreOf<AppCoreReducer>
    public var body: some View {
        TabView(selection: $store.selectedTab.sending(\.selectedTabChanged)) {
            NavigationStack {
                HomeView(store: store.scope(state: \.home, action: \.home))
            }
            .tabItem { Label("Home", systemImage: "house") }
            .tag(AppCoreReducer.Tab.home)
            // … other tabs
        }
    }
}
```

## Key Principles

- **`@ObservableState`** on every `State` — enables direct `store.property` reads in SwiftUI
- **`@Bindable var store`** in views — enables two-way `$store.field` bindings
- **`Scope` before `Reduce`** — child reducers always run before parent logic
- **Delegate actions** for child→parent communication — see `references/tca-patterns.md`
- **`@Reducer enum Destination`** for push/sheet/alert navigation — see `references/tca-patterns.md`
- **`@DependencyClient` or manual struct** for services — see `references/dependency-patterns.md`

## Reference Files

- **`references/module-design.md`** — Module decomposition guide, Package.swift templates, dependency graph rules, shared bundle access pattern
- **`references/tca-patterns.md`** — Full reducer pattern, navigation (Destination enum + @Presents), delegate actions, async effects, testing
- **`references/dependency-patterns.md`** — `@DependencyClient` macro pattern, manual struct pattern, actor-as-dependency, live/test/mock implementations
