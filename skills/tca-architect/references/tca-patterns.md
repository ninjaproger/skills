# TCA Patterns

## Table of Contents
1. [Feature Reducer Template](#1-feature-reducer-template)
2. [Async Effects](#2-async-effects)
3. [Navigation: Destination Enum](#3-navigation-destination-enum)
4. [Delegate Actions (Child → Parent)](#4-delegate-actions-child--parent)
5. [Feature Composition with Scope](#5-feature-composition-with-scope)
6. [Alerts](#6-alerts)
7. [Testing with TestStore](#7-testing-with-teststore)

---

## 1. Feature Reducer Template

```swift
// Sources/ItemList/ItemListReducer.swift
import ComposableArchitecture
import Models
import Services

@Reducer
public struct ItemListReducer {

    // MARK: - Destination (navigation targets)
    @Reducer
    public enum Destination {
        case detail(ItemDetailReducer)
        case createItem(CreateItemReducer)
    }

    // MARK: - State
    @ObservableState
    public struct State: Equatable {
        public var items: [Item] = []
        public var isLoading = false
        public var errorMessage: String?
        @Presents public var destination: Destination.State?

        public init() {}
    }

    // MARK: - Actions
    public enum Action {
        case onAppear
        case loadItems
        case itemsLoaded(Result<[Item], Error>)
        case itemTapped(Item)
        case addItemTapped
        case destination(PresentationAction<Destination.Action>)
        case delegate(Delegate)

        @CasePathable
        public enum Delegate {
            case itemSelected(Item)
        }
    }

    // MARK: - Dependencies
    @Dependency(\.itemClient) var itemClient

    public init() {}

    // MARK: - Body
    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .onAppear:
                guard state.items.isEmpty else { return .none }
                return .send(.loadItems)

            case .loadItems:
                state.isLoading = true
                state.errorMessage = nil
                return .run { send in
                    await send(.itemsLoaded(Result { try await itemClient.fetchAll() }))
                }

            case .itemsLoaded(.success(let items)):
                state.isLoading = false
                state.items = items
                return .none

            case .itemsLoaded(.failure(let error)):
                state.isLoading = false
                state.errorMessage = error.localizedDescription
                return .none

            case .itemTapped(let item):
                state.destination = .detail(ItemDetailReducer.State(item: item))
                return .none

            case .addItemTapped:
                state.destination = .createItem(CreateItemReducer.State())
                return .none

            case .destination(.presented(.detail(.delegate(.deleted(let id))))):
                state.items.removeAll { $0.id == id }
                state.destination = nil
                return .none

            case .destination:
                return .none

            case .delegate:
                return .none
            }
        }
        .ifLet(\.$destination, action: \.destination)
    }
}

extension ItemListReducer.Destination.State: Equatable {}
```

**View:**

```swift
// Sources/ItemList/ItemListView.swift
import ComposableArchitecture
import SwiftUI

public struct ItemListView: View {
    @Bindable var store: StoreOf<ItemListReducer>

    public init(store: StoreOf<ItemListReducer>) {
        self.store = store
    }

    public var body: some View {
        List(store.items) { item in
            Button(item.title) { store.send(.itemTapped(item)) }
        }
        .navigationTitle("Items")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Add") { store.send(.addItemTapped) }
            }
        }
        .onAppear { store.send(.onAppear) }
        // Push navigation
        .navigationDestination(
            item: $store.scope(state: \.destination?.detail, action: \.destination.detail)
        ) { store in
            ItemDetailView(store: store)
        }
        // Sheet navigation
        .sheet(
            item: $store.scope(state: \.destination?.createItem, action: \.destination.createItem)
        ) { store in
            CreateItemView(store: store)
        }
    }
}
```

---

## 2. Async Effects

**Pattern:** Wrap async throwing work in `Result { ... }`, dispatch as a result action.

```swift
// Inside Reduce body:
case .loadItems:
    state.isLoading = true
    return .run { [itemClient] send in
        await send(
            .itemsLoaded(
                Result { try await itemClient.fetchAll() }
            )
        )
    }

// Handle result:
case .itemsLoaded(.success(let items)):
    state.isLoading = false
    state.items = items
    return .none

case .itemsLoaded(.failure(let error)):
    state.isLoading = false
    state.errorMessage = error.localizedDescription
    return .none
```

**Capture dependencies explicitly** in the closure to avoid Swift 6 sendability warnings:

```swift
return .run { [chapterId = state.chapterId, client = itemClient] send in
    await send(.loaded(Result { try await client.fetch(chapterId) }))
}
```

**Parallel effects:**

```swift
return .run { send in
    async let items = itemClient.fetchAll()
    async let user = userClient.currentUser()
    let (i, u) = try await (items, user)
    await send(.dataLoaded(items: i, user: u))
}
```

**Cancellation:**

```swift
enum CancelID { case load }

case .loadItems:
    return .run { send in
        await send(.itemsLoaded(Result { try await itemClient.fetchAll() }))
    }
    .cancellable(id: CancelID.load, cancelInFlight: true)

case .cancelLoad:
    return .cancel(id: CancelID.load)
```

---

## 3. Navigation: Destination Enum

Use `@Reducer enum Destination` for all navigation from a single parent. This handles push, sheet, and alert from the same optional `destination` state.

```swift
@Reducer
public struct ParentReducer {
    @Reducer
    public enum Destination {
        case detail(DetailReducer)        // pushed via navigationDestination
        case edit(EditReducer)            // presented as sheet
        case deleteAlert(AlertState<Action.Alert>) // alert
    }

    @ObservableState
    public struct State: Equatable {
        @Presents public var destination: Destination.State?
    }

    public enum Action {
        case destination(PresentationAction<Destination.Action>)
        case alert(Alert)

        @CasePathable
        public enum Alert {
            case confirmDelete
        }
    }

    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .detailTapped(let item):
                state.destination = .detail(DetailReducer.State(item: item))
                return .none

            case .editTapped:
                state.destination = .edit(EditReducer.State())
                return .none

            case .deleteTapped:
                state.destination = .deleteAlert(
                    AlertState {
                        TextState("Delete Item?")
                    } actions: {
                        ButtonState(role: .destructive, action: .confirmDelete) {
                            TextState("Delete")
                        }
                        ButtonState(role: .cancel) { TextState("Cancel") }
                    }
                )
                return .none

            case .destination(.presented(.deleteAlert(.confirmDelete))):
                // perform deletion
                return .none

            case .destination:
                return .none
            }
        }
        .ifLet(\.$destination, action: \.destination)
    }
}

// In View:
.navigationDestination(
    item: $store.scope(state: \.destination?.detail, action: \.destination.detail)
) { DetailView(store: $0) }

.sheet(
    item: $store.scope(state: \.destination?.edit, action: \.destination.edit)
) { EditView(store: $0) }

.alert($store.scope(state: \.destination?.deleteAlert, action: \.destination.deleteAlert))
```

**Important:** Add conformance if needed:
```swift
extension ParentReducer.Destination.State: Equatable {}
```

---

## 4. Delegate Actions (Child → Parent)

Child reducers surface results upward via `delegate` actions. The parent intercepts them.

**Child defines:**
```swift
public enum Action {
    // ...
    case delegate(Delegate)

    @CasePathable
    public enum Delegate {
        case saved(Item)
        case deleted(UUID)
        case cancelled
    }
}

// In Reduce body — delegates always return .none in the child:
case .delegate:
    return .none

// Child fires a delegate:
case .saveButtonTapped:
    // ... do work ...
    return .send(.delegate(.saved(state.item)))
```

**Parent intercepts via deep pattern match:**
```swift
// Parent handles child delegate from Destination:
case .destination(.presented(.edit(.delegate(.saved(let item))))):
    state.items.append(item)
    state.destination = nil
    return .none

// Parent handles child delegate from Scope (tab-level):
case .settings(.delegate(.loggedOut)):
    state.selectedTab = .home
    return .none
```

**Delegate chain bubbles up through multiple levels:**
```
QuizReducer → delegate(.completed)
  → ChapterReducer intercepts → sends .delegate(.progressUpdated)
    → CourseReducer intercepts → updates chapterProgresses
```

---

## 5. Feature Composition with Scope

`Scope` wires a child reducer into a parent's state/action. Always put `Scope` blocks **before** the parent `Reduce` block so child reducers run first.

```swift
public var body: some ReducerOf<Self> {
    Scope(state: \.home,     action: \.home)     { HomeReducer()     }
    Scope(state: \.settings, action: \.settings) { SettingsReducer() }

    Reduce { state, action in
        // parent logic runs AFTER child reducers
    }
}
```

**Scoping the store in a view:**
```swift
HomeView(store: store.scope(state: \.home, action: \.home))
```

---

## 6. Alerts

Simple alerts without a child reducer use `AlertState` directly on `@Presents`:

```swift
@ObservableState
public struct State: Equatable {
    @Presents var alert: AlertState<Action.Alert>?
}

public enum Action {
    case alert(PresentationAction<Alert>)

    @CasePathable
    public enum Alert: Equatable {
        case confirmReset
    }
}

// In body:
Reduce { state, action in
    switch action {
    case .resetTapped:
        state.alert = AlertState {
            TextState("Reset Progress?")
        } actions: {
            ButtonState(role: .destructive, action: .confirmReset) {
                TextState("Reset")
            }
            ButtonState(role: .cancel) { TextState("Cancel") }
        } message: {
            TextState("This cannot be undone.")
        }
        return .none

    case .alert(.presented(.confirmReset)):
        // perform reset
        return .none

    case .alert:
        return .none
    }
}
.ifLet(\.$alert, action: \.alert)

// In view:
.alert($store.scope(state: \.alert, action: \.alert))
```

---

## 7. Testing with TestStore

```swift
import ComposableArchitecture
import Testing
@testable import ItemList

@Suite struct ItemListReducerTests {
    @Test func loadItems() async {
        let items = [Item(id: UUID(), title: "Test")]

        let store = TestStore(initialState: ItemListReducer.State()) {
            ItemListReducer()
        } withDependencies: {
            $0.itemClient.fetchAll = { items }
        }

        await store.send(.onAppear)
        await store.send(.loadItems) {
            $0.isLoading = true
        }
        await store.receive(\.itemsLoaded.success) {
            $0.isLoading = false
            $0.items = items
        }
    }

    @Test func delegateFired() async {
        let item = Item(id: UUID(), title: "Test")
        let store = TestStore(initialState: ItemDetailReducer.State(item: item)) {
            ItemDetailReducer()
        }
        store.exhaustivity = .off  // only check what matters

        await store.send(.deleteTapped)
        await store.receive(\.delegate.deleted)
    }
}
```

**Key APIs:**
- `withDependencies` — override specific dependency properties
- `store.exhaustivity = .off` — skip verifying unrelated state changes
- `await store.receive(\.delegate.deleted)` — verify delegate action was sent
- `$0.isLoading = true` in send/receive closure — assert exact state mutation
