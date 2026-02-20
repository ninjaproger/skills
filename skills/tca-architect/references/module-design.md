# Module Design & Package.swift

## Module Decomposition Strategy

### Infrastructure Layer (no TCA, no UI)

| Module | Contents | Dependencies |
|--------|----------|-------------|
| `DesignSystem` | Colors, fonts, spacing constants, shared UI helpers | none |
| `Models` | Pure Swift value types (`struct`/`enum`) with `Codable`, `Equatable`, `Sendable`, `Identifiable` | optional: SQLiteData |
| `Services` | Dependency clients (interfaces) + actor-based databases | Models, swift-dependencies |

**Rules:**
- `Models` never imports TCA, SwiftUI, or Services
- `DesignSystem` never imports Models or Services
- `Services` never imports TCA or SwiftUI — it defines interfaces, not implementations
- Live implementations go in `Services/<Client>+Live.swift`

### Feature Layer (TCA + SwiftUI)

One SPM target per feature. Features may be:

- **Tab features** — top-level tabs in `AppCore` (e.g., `Home`, `Settings`, `Profile`)
- **Sub-features** — navigated to from a parent feature (e.g., `ItemDetail`, `EditForm`)
- **Shared feature components** — reusable TCA reducers used by multiple parents (e.g., `Quiz`, `ChapterStep` in Sky107)
- **Stub features** — placeholder tab that reserves its slot but has no logic yet (use `EmptyReducer()`)

### Dependency Graph Rules

```
DesignSystem ←─ (no deps)
Models       ←─ DesignSystem? (rarely), external data libs
Services     ←─ Models, swift-dependencies
<Feature>    ←─ DesignSystem, Models, Services, <child features>, ComposableArchitecture
AppCore      ←─ DesignSystem, <all tab features>, ComposableArchitecture, SwiftUINavigation
```

**No circular dependencies.** A feature may depend on another feature only if it is its direct parent in the navigation hierarchy. Shared components (e.g., `Quiz`) should be their own module depended on by multiple features.

### When to Split a Feature into Sub-Modules

Split when:
- A reducer is > ~300 lines
- A UI component is reused by multiple parent features
- A navigation destination has its own destinations (nested navigation)
- You want to test it in isolation

Keep together when:
- A view + reducer together are < ~200 lines
- The feature is never reused
- It's a stub/placeholder

---

## Package.swift Template

```swift
// swift-tools-version: 6.1
import PackageDescription

let package = Package(
    name: "MyAppKit",
    platforms: [.iOS(.v17)],
    products: [
        // Infrastructure
        .library(name: "AppCore",     targets: ["AppCore"]),
        .library(name: "DesignSystem", targets: ["DesignSystem"]),
        .library(name: "Models",      targets: ["Models"]),
        .library(name: "Services",    targets: ["Services"]),
        // Feature modules
        .library(name: "Home",        targets: ["Home"]),
        .library(name: "Settings",    targets: ["Settings"]),
        // Sub-features
        .library(name: "ItemDetail",  targets: ["ItemDetail"]),
    ],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.17.0"),
        .package(url: "https://github.com/pointfreeco/swift-navigation",              from: "2.4.0"),
        .package(url: "https://github.com/pointfreeco/swift-dependencies",            from: "1.6.0"),
        .package(url: "https://github.com/pointfreeco/swift-snapshot-testing",        from: "1.17.0"),
    ],
    targets: [
        // MARK: - Infrastructure
        .target(name: "DesignSystem"),

        .target(name: "Models", dependencies: []),

        .target(name: "Services", dependencies: [
            "Models",
            .product(name: "Dependencies",      package: "swift-dependencies"),
            .product(name: "DependenciesMacros", package: "swift-dependencies"),
        ]),

        // MARK: - Sub-features
        .target(name: "ItemDetail", dependencies: [
            "DesignSystem", "Models", "Services",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),

        // MARK: - Tab Features
        .target(name: "Home", dependencies: [
            "DesignSystem", "Models", "Services", "ItemDetail",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),

        .target(
            name: "Settings",
            dependencies: [
                "DesignSystem", "Models", "Services",
                .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
            ]
        ),

        // MARK: - App Core
        .target(name: "AppCore", dependencies: [
            "DesignSystem", "Home", "Settings",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
            .product(name: "SwiftUINavigation",       package: "swift-navigation"),
        ]),

        // MARK: - Tests
        .testTarget(name: "HomeTests", dependencies: [
            "Home",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),
        .testTarget(name: "SettingsTests", dependencies: [
            "Settings",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),
        .testTarget(name: "ServicesTests", dependencies: [
            "Services",
            .product(name: "DependenciesTestSupport", package: "swift-dependencies"),
        ]),
    ]
)
```

**Notes:**
- One product and one target per module (same name)
- Add `resources: [.process("Resources")]` to targets that embed JSON/images via `Bundle.module`
- `SwiftUINavigation` is only needed by `AppCore` (or features using `NavigationStack` bindings)
- `DependenciesTestSupport` in test targets enables `withDependencies` in tests

---

## Accessing Bundle.module Across Modules

When module A owns static resources (JSON files, images) and module B also needs them:

**Problem:** `Bundle.module` only works inside the module that owns the `Resources/` directory.

**Solution:** Module A exposes a public bundle accessor:

```swift
// Sources/Home/HomeBundle.swift
public enum HomeBundle {
    public static let bundle = Bundle.module
}
```

Module B (which depends on A) accesses it as `HomeBundle.bundle`. No circular dependency needed.

---

## Stub Feature Pattern

Use for tab placeholders that aren't implemented yet:

```swift
// Sources/Analytics/AnalyticsView.swift
import ComposableArchitecture
import SwiftUI

@Reducer
public struct AnalyticsReducer {
    @ObservableState
    public struct State: Equatable {
        public init() {}
    }
    public enum Action {}
    public var body: some ReducerOf<Self> { EmptyReducer() }
}

public struct AnalyticsView: View {
    let store: StoreOf<AnalyticsReducer>
    public init(store: StoreOf<AnalyticsReducer>) { self.store = store }
    public var body: some View {
        Text("Coming Soon").navigationTitle("Analytics")
    }
}
```

---

## File Naming Conventions

| File | Naming |
|------|--------|
| Reducer | `<Feature>Reducer.swift` |
| View | `<Feature>View.swift` |
| Both together (small) | `<Feature>View.swift` (contains reducer + view) |
| Dependency client interface | `<Domain>Client.swift` |
| Live implementation | `<Domain>Client+Live.swift` |
| Mock for previews | `<Domain>Client+Mock.swift` (static `mock` on the struct) |
| Actor database | `<Domain>Database.swift` |
| Bundle accessor | `<Module>Bundle.swift` |
| DependencyValues extensions | `Services.swift` (collects all `DependencyValues` extensions) |
