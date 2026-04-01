# Module Design & Package.swift

## Module Decomposition Strategy

All code lives in one SPM package with four strict layers. Higher layers depend on lower layers — never the reverse.

### Layer 1 — Infrastructure (no TCA, no UI)

| Module | Contents | Dependencies |
|--------|----------|-------------|
| `DesignSystem` | Colors, fonts, spacing tokens, shared UI helpers | none |
| `Models` | Pure Swift value types (`struct`/`enum`) with `Codable`, `Equatable`, `Sendable`, `Identifiable` | optional: SQLiteData |
| `Services` | Dependency clients (interfaces) + actor-based databases | Models, swift-dependencies |

**Rules:**
- `Models` never imports TCA, SwiftUI, or Services
- `DesignSystem` never imports Models or Services
- `Services` never imports TCA or SwiftUI — it defines interfaces, not implementations
- Live implementations go in `Services/<Client>+Live.swift`

### Layer 2 — Shared Components (TCA + SwiftUI, no specific feature knowledge)

Reusable TCA reducers + views used by 2 or more feature modules. They live in their own SPM target.

| When to create | Example |
|----------------|---------|
| A reducer+view is used by 2+ feature modules | `Quiz` used by `CourseChapter` |
| A sub-feature has its own nested navigation and needs isolated testing | `ChapterStep`, `SectionalChart` |
| A generic component drives content loaded from outside (bundle param) | `CourseChapter` receives a `bundle: Bundle` |

**Rules:**
- Shared components MUST NOT import any Feature module (no upward dependency)
- Shared components MAY import other shared components they build on
- If a component is only ever used by one feature, put it inside that feature's target instead

### Layer 3 — Feature Modules (TCA + SwiftUI)

One SPM target per top-level tab or independently navigable feature:

- **Tab features** — top-level tabs in `AppCore` (e.g., `Course`, `Settings`, `Flashcards`)
- **Stub features** — placeholder tab with no logic yet (use `EmptyReducer()`)

Features own their content data. Any JSON files, images, or other assets they need go in `<Feature>/Resources/` with `resources: [.process("Resources")]` in `Package.swift`.

### Layer 4 — AppCore

Single module that imports every tab feature and wires them into a `TabView`. No business logic — only composition and cross-tab delegate handling.

### Dependency Graph

```
DesignSystem  ←─ (no deps)
Models        ←─ (no deps beyond external Codable/data libs)
Services      ←─ Models, swift-dependencies
<Shared>      ←─ DesignSystem, Models, Services, ComposableArchitecture
<Feature>     ←─ DesignSystem, Models, Services, <shared components it needs>, ComposableArchitecture
AppCore       ←─ DesignSystem, <all tab features>, ComposableArchitecture, SwiftUINavigation
```

**No circular dependencies.** A shared component may depend on another shared component only if it is a lower-level building block. Feature modules must not import each other.

### When to Split

**Create a new module when:**
- A reducer+view is reused by 2+ feature modules → Shared Component
- A reducer exceeds ~300 lines → consider splitting destination into its own module
- A navigation destination has its own nested destinations → isolated testability warrants a module

**Keep together when:**
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
        // MARK: Infrastructure
        .library(name: "AppCore",      targets: ["AppCore"]),
        .library(name: "DesignSystem", targets: ["DesignSystem"]),
        .library(name: "Models",       targets: ["Models"]),
        .library(name: "Services",     targets: ["Services"]),
        // MARK: Shared Components
        .library(name: "Quiz",         targets: ["Quiz"]),
        .library(name: "ItemStep",     targets: ["ItemStep"]),
        // MARK: Feature Modules
        .library(name: "Home",         targets: ["Home"]),
        .library(name: "Settings",     targets: ["Settings"]),
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
            .product(name: "Dependencies",       package: "swift-dependencies"),
            .product(name: "DependenciesMacros", package: "swift-dependencies"),
        ]),

        // MARK: - Shared Components
        // Reusable TCA reducers — no feature-specific knowledge
        .target(name: "Quiz", dependencies: [
            "DesignSystem", "Models", "Services",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),

        .target(name: "ItemStep", dependencies: [
            "DesignSystem", "Models", "Services",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),

        // MARK: - Feature Modules
        // resources: [.process("Resources")] whenever the module owns JSON/images
        .target(name: "Home", dependencies: [
            "DesignSystem", "Models", "Services",
            "Quiz",       // shared component
            "ItemStep",   // shared component
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ], resources: [.process("Resources")]),  // owns home-content.json etc.

        .target(name: "Settings", dependencies: [
            "DesignSystem", "Models", "Services",
            .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
        ]),

        // MARK: - AppCore
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
        .testTarget(name: "QuizTests", dependencies: [
            "Quiz",
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
- One product + one target per module (same name)
- Add `resources: [.process("Resources")]` to any target that bundles JSON/images
- Create a `<Module>Bundle.swift` in every module with a `Resources/` folder (see below)
- `SwiftUINavigation` only needed by `AppCore`
- `DependenciesTestSupport` in test targets enables `withDependencies`

---

## Bundle.module Accessor

**Rule:** Every module with a `Resources/` folder **must** expose a public bundle accessor. `Bundle.module` only resolves correctly inside the module that owns the `Resources/` directory.

```swift
// Sources/Home/HomeBundle.swift
public enum HomeBundle {
    public static let bundle = Bundle.module
}
```

Any module that depends on `Home` accesses `HomeBundle.bundle`. No circular dependency needed.

This is also how you pass a bundle into child reducers that load content from the parent module's resources (see `tca-patterns.md` § Bundle parameter pattern).

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
