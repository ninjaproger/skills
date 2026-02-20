# View Patterns

## Table of Contents
1. [Four-state body (loading / error / empty / content)](#1-four-state-body)
2. [Navigation wiring](#2-navigation-wiring)
3. [Toggle and binding patterns](#3-toggle-and-binding-patterns)
4. [Private sub-views and file-local components](#4-private-sub-views-and-file-local-components)
5. [Sheets that own a NavigationStack](#5-sheets-that-own-a-navigationstack)
6. [Toolbar and menus](#6-toolbar-and-menus)
7. [State-driven animation](#7-state-driven-animation)
8. [Alerts (TCA-managed)](#8-alerts-tca-managed)
9. [Preview data helpers](#9-preview-data-helpers)

---

## 1. Four-state body

Use `Group { }` as the branching container. Order: loading → error → empty → content.

```swift
public var body: some View {
    Group {
        if store.isLoading {
            ProgressView("Loading...")
        } else if let error = store.loadError {
            ContentUnavailableView(
                "Error Loading Data",
                systemImage: "exclamationmark.triangle",
                description: Text(error)
            )
        } else if store.items.isEmpty {
            ContentUnavailableView(
                "No Items",
                systemImage: "tray",
                description: Text("Items you add will appear here.")
            )
        } else {
            contentView       // @ViewBuilder private var
        }
    }
    .navigationTitle("Title")
    .onAppear { store.send(.onAppear) }
}
```

**Computed state** — prefer keeping isEmpty logic on `State`:
```swift
// In State:
public var isEmpty: Bool { !isLoading && items.isEmpty && loadError == nil }

// In View:
} else if store.isEmpty {
```

**ZStack variant** (used in Flashcards when animation between states is needed):
```swift
ZStack {
    if store.isLoading { loadingView }
    else if let error = store.loadError { errorView(error) }
    else if store.isEmpty { emptyView }
    else { contentView }
}
.animation(.easeInOut, value: store.isLoading)
```

---

## 2. Navigation wiring

### Push navigation (navigationDestination)

```swift
// In view body:
.navigationDestination(
    item: $store.scope(state: \.destination?.detail, action: \.destination.detail)
) { childStore in
    DetailView(store: childStore)
        .navigationTitle(childStore.item.title)  // title set by parent
}
```

### Sheet navigation

```swift
.sheet(
    item: $store.scope(state: \.destination?.editForm, action: \.destination.editForm)
) { childStore in
    EditFormView(store: childStore)   // EditFormView wraps its own NavigationStack
}
```

### Multiple destinations from one parent

```swift
// All destinations share one @Presents optional — only one can be active at a time
.navigationDestination(
    item: $store.scope(state: \.destination?.step, action: \.destination.step)
) { StepDetailView(store: $0) }
.sheet(
    item: $store.scope(state: \.destination?.quiz, action: \.destination.quiz)
) { QuizView(store: $0) }
.sheet(
    item: $store.scope(state: \.destination?.results, action: \.destination.results)
) { ResultsView(store: $0) }
```

### Passing pure data to callbacks (no child store)

When a sub-view is purely presentational, pass callbacks instead of a store:

```swift
// In parent view:
ChapterContentView(
    chapter: store.chapter,
    onStepTapped: { store.send(.stepTapped($0)) },
    onQuizTapped: { store.send(.startQuizTapped) }
)

// Sub-view (no TCA dependency):
private struct ChapterContentView: View {
    let chapter: Chapter
    let onStepTapped: (ChapterStep) -> Void
    let onQuizTapped: () -> Void
    // ...
}
```

---

## 3. Toggle and binding patterns

### TCA Toggle (ignore the Bool, send action)

```swift
Toggle(isOn: Binding(
    get: { store.notificationsEnabled },
    set: { _ in store.send(.toggleNotifications) }
)) {
    Label("Notifications", systemImage: "bell")
}
```

### Two-way binding for text fields

```swift
// State has: @BindingState var searchText: String = ""
// Action has: case binding(BindingAction<State>)
// Body includes: BindingReducer()

TextField("Search", text: $store.searchText)   // direct $store binding
```

Only use `@BindingState` + `BindingReducer()` for fields where every keystroke should update state. For fields that only matter on submit, use a local `@State` + action on submit.

### Tab selection binding

```swift
// Root TabView wired to TCA:
TabView(selection: $store.selectedTab.sending(\.selectedTabChanged)) {
    // ...
}
```

---

## 4. Private sub-views and file-local components

Break complex views into pieces. Prefer `@ViewBuilder private var` for sections and `private struct` for reusable row-level components.

```swift
public struct ItemListView: View {
    @Bindable var store: StoreOf<ItemListReducer>

    public var body: some View {
        contentView
            .navigationTitle("Items")
    }

    // Computed vars for sections
    @ViewBuilder
    private var contentView: some View {
        ScrollView {
            progressHeader
            itemGrid
        }
    }

    private var progressHeader: some View {
        VStack {
            ProgressView(value: store.progressFraction)
            Text("\(store.completedCount) of \(store.totalCount) complete")
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var itemGrid: some View {
        LazyVGrid(columns: [.init(.flexible()), .init(.flexible())]) {
            ForEach(store.items) { item in
                ItemCard(item: item, isCompleted: store.completedIds.contains(item.id))
                    .onTapGesture { store.send(.itemTapped(item)) }
            }
        }
        .padding()
    }
}

// File-private component — stays in this file, not exposed as public
private struct ItemCard: View {
    let item: Item
    let isCompleted: Bool

    var body: some View {
        VStack {
            Image(systemName: isCompleted ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(isCompleted ? .green : .secondary)
            Text(item.title).font(.caption)
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}
```

---

## 5. Sheets that own a NavigationStack

When a feature is always presented as a sheet (e.g. Quiz), it owns its `NavigationStack` internally:

```swift
public struct QuizView: View {
    @Bindable var store: StoreOf<QuizReducer>

    public var body: some View {
        NavigationStack {           // ← inside the view, not the parent
            ScrollView {
                // content
            }
            .navigationTitle("Quiz")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { store.send(.cancelTapped) }
                }
            }
        }
    }
}
```

---

## 6. Toolbar and menus

```swift
.toolbar {
    ToolbarItem(placement: .primaryAction) {
        Button("Add") { store.send(.addTapped) }
    }

    ToolbarItem(placement: .topBarTrailing) {
        filterMenu
    }
}

private var filterMenu: some View {
    Menu {
        Toggle(
            "Show Completed",
            isOn: Binding(
                get: { store.showCompleted },
                set: { _ in store.send(.toggleShowCompleted) }
            )
        )
        Divider()
        Button("Reset Filters") { store.send(.resetFiltersTapped) }
    } label: {
        Image(systemName: "line.3.horizontal.decrease.circle")
    }
}
```

---

## 7. State-driven animation

```swift
// Card flip (Flashcards pattern):
CardFace(isFlipped: store.showAnswer)
    .rotation3DEffect(
        .degrees(store.showAnswer ? 180 : 0),
        axis: (x: 0, y: 1, z: 0)
    )
    .animation(.easeInOut(duration: 0.4), value: store.showAnswer)

// Fade between states:
contentView
    .opacity(store.isLoading ? 0 : 1)
    .animation(.easeInOut, value: store.isLoading)
```

---

## 8. Alerts (TCA-managed)

```swift
// In view body — single line:
.alert($store.scope(state: \.alert, action: \.alert))

// For Destination-style alerts:
// (when alert is one case of @Reducer enum Destination)
// No special view modifier needed beyond the existing navigationDestination/sheet setup;
// use .alert on $store.scope(state: \.destination?.confirmDelete, ...) pattern
```

---

## 9. Preview data helpers

Add `static` preview helpers on model types in the `Models` module (or inline in the preview file):

```swift
// In Models/Certificate.swift or in Sources/Certificates/CertificatesView.swift:
#if DEBUG
extension Certificate {
    static let sample = Certificate(
        id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!,
        title: "FAA Part 107 Certificate",
        dateEarned: Date()
    )

    static let samples: [Certificate] = [
        Certificate(id: UUID(), title: "FAA Part 107", dateEarned: Date()),
        Certificate(id: UUID(), title: "Advanced Operations", dateEarned: Date()),
        Certificate(id: UUID(), title: "Night Waiver", dateEarned: Date()),
    ]
}
#endif
```

Using fixed UUIDs (`UUID(uuidString:)`) makes previews stable across re-renders.
