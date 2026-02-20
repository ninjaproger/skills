# Feature Template

Complete file templates for a new feature called `Certificates`. Substitute the real feature name throughout.

## Table of Contents
1. [Reducer file](#1-reducer-file)
2. [View file with previews](#2-view-file-with-previews)
3. [Test file](#3-test-file)
4. [Package.swift additions](#4-packageswift-additions)
5. [AppCore wiring (new tab)](#5-appcore-wiring-new-tab)
6. [Sub-feature (navigation destination)](#6-sub-feature-navigation-destination)

---

## 1. Reducer file

`Sources/Certificates/CertificatesReducer.swift`

```swift
import ComposableArchitecture
import Models
import Services

@Reducer
public struct CertificatesReducer {

    // MARK: - Destination (remove if no navigation from this feature)
    @Reducer
    public enum Destination {
        case detail(CertificateDetailReducer)
    }

    // MARK: - State
    @ObservableState
    public struct State: Equatable {
        public var items: [Certificate] = []
        public var isLoading = false
        public var loadError: String?
        @Presents public var destination: Destination.State?

        // Computed properties live on State, not the view
        public var isEmpty: Bool { !isLoading && items.isEmpty && loadError == nil }

        public init() {}
    }

    // MARK: - Action
    public enum Action {
        case onAppear
        case loadItems
        case itemsLoaded(Result<[Certificate], Error>)
        case itemTapped(Certificate)
        case destination(PresentationAction<Destination.Action>)
        case delegate(Delegate)

        @CasePathable
        public enum Delegate {
            case itemSelected(Certificate)
        }
    }

    // MARK: - Dependencies
    @Dependency(\.certificateClient) var certificateClient

    public init() {}

    // MARK: - Body
    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {

            case .onAppear:
                guard state.items.isEmpty else { return .none }   // idempotency guard
                return .send(.loadItems)

            case .loadItems:
                state.isLoading = true
                state.loadError = nil
                return .run { [client = certificateClient] send in
                    await send(.itemsLoaded(Result { try await client.fetchAll() }))
                }

            case .itemsLoaded(.success(let items)):
                state.isLoading = false
                state.items = items
                return .none

            case .itemsLoaded(.failure(let error)):
                state.isLoading = false
                state.loadError = error.localizedDescription
                return .none

            case .itemTapped(let item):
                state.destination = .detail(CertificateDetailReducer.State(item: item))
                return .none

            case .destination(.presented(.detail(.delegate(.dismissed)))):
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

extension CertificatesReducer.Destination.State: Equatable {}
```

---

## 2. View file with previews

`Sources/Certificates/CertificatesView.swift`

```swift
import ComposableArchitecture
import SwiftUI

public struct CertificatesView: View {
    @Bindable var store: StoreOf<CertificatesReducer>

    public init(store: StoreOf<CertificatesReducer>) {
        self.store = store
    }

    public var body: some View {
        Group {
            if store.isLoading {
                ProgressView("Loading certificates...")
            } else if let error = store.loadError {
                ContentUnavailableView(
                    "Error Loading Certificates",
                    systemImage: "exclamationmark.triangle",
                    description: Text(error)
                )
            } else if store.isEmpty {
                ContentUnavailableView(
                    "No Certificates",
                    systemImage: "doc.badge.checkmark",
                    description: Text("Complete chapters to earn certificates.")
                )
            } else {
                certificateList
            }
        }
        .navigationTitle("Certificates")
        .navigationBarTitleDisplayMode(.large)
        .onAppear { store.send(.onAppear) }
        .navigationDestination(
            item: $store.scope(state: \.destination?.detail, action: \.destination.detail)
        ) { store in
            CertificateDetailView(store: store)
        }
    }

    // MARK: - Private sub-views

    @ViewBuilder
    private var certificateList: some View {
        List(store.items) { item in
            CertificateRow(item: item)
                .onTapGesture { store.send(.itemTapped(item)) }
        }
    }
}

// MARK: - File-local sub-components

private struct CertificateRow: View {
    let item: Certificate

    var body: some View {
        HStack {
            Image(systemName: "doc.badge.checkmark")
                .foregroundStyle(.green)
            VStack(alignment: .leading) {
                Text(item.title).font(.headline)
                Text(item.dateEarned.formatted(date: .abbreviated, time: .omitted))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Previews

#Preview("Certificates - Loading") {
    NavigationStack {
        CertificatesView(
            store: Store(initialState: CertificatesReducer.State()) {
                CertificatesReducer()
            }
        )
    }
}

#Preview("Certificates - Loaded") {
    var state = CertificatesReducer.State()
    state.isLoading = false
    state.items = Certificate.samples
    return NavigationStack {
        CertificatesView(
            store: Store(initialState: state) {
                CertificatesReducer()
            }
        )
    }
}

#Preview("Certificates - Empty") {
    var state = CertificatesReducer.State()
    state.isLoading = false
    return NavigationStack {
        CertificatesView(
            store: Store(initialState: state) {
                CertificatesReducer()
            }
        )
    }
}

#Preview("Certificates - Error") {
    var state = CertificatesReducer.State()
    state.isLoading = false
    state.loadError = "Unable to load certificates. Please try again."
    return NavigationStack {
        CertificatesView(
            store: Store(initialState: state) {
                CertificatesReducer()
            }
        )
    }
}
```

---

## 3. Test file

`Tests/CertificatesTests/CertificatesReducerTests.swift`

```swift
import ComposableArchitecture
import Foundation
import Models
import Testing
@testable import Certificates

// MARK: - Test data factory functions (file-level)

func makeCertificate(title: String = "Part 107 Certificate") -> Certificate {
    Certificate(id: UUID(), title: title, dateEarned: Date())
}

// MARK: - Tests

@Suite("CertificatesReducer Tests")
@MainActor
struct CertificatesReducerTests {

    // MARK: Loading

    @Test("onAppear triggers loadItems when items is empty")
    func onAppearTriggersLoad() async {
        let store = TestStore(initialState: CertificatesReducer.State()) {
            CertificatesReducer()
        } withDependencies: {
            $0.certificateClient.fetchAll = { [] }
        }
        store.exhaustivity = .off

        await store.send(.onAppear)
        // receives .loadItems and .itemsLoaded automatically
    }

    @Test("onAppear skips load when items already loaded")
    func onAppearSkipsLoad() async {
        var state = CertificatesReducer.State()
        state.items = [makeCertificate()]
        let store = TestStore(initialState: state) {
            CertificatesReducer()
        }

        await store.send(.onAppear)
        // no further actions — TestStore will fail on unexpected receives
    }

    @Test("loadItems sets isLoading and clears error")
    func loadItemsSetsLoading() async {
        var initialState = CertificatesReducer.State()
        initialState.loadError = "previous error"

        let store = TestStore(initialState: initialState) {
            CertificatesReducer()
        } withDependencies: {
            $0.certificateClient.fetchAll = { [makeCertificate()] }
        }
        store.exhaustivity = .off

        await store.send(.loadItems) {
            $0.isLoading = true
            $0.loadError = nil
        }
    }

    @Test("itemsLoaded success populates items")
    func itemsLoadedSuccess() async {
        let items = [makeCertificate(), makeCertificate(title: "Advanced")]
        let store = TestStore(initialState: CertificatesReducer.State()) {
            CertificatesReducer()
        } withDependencies: {
            $0.certificateClient.fetchAll = { items }
        }

        await store.send(.loadItems) { $0.isLoading = true }
        await store.receive(\.itemsLoaded.success) {
            $0.isLoading = false
            $0.items = items
        }
    }

    @Test("itemsLoaded failure sets loadError")
    func itemsLoadedFailure() async {
        struct FetchError: Error, LocalizedError {
            var errorDescription: String? { "Network unavailable" }
        }
        let store = TestStore(initialState: CertificatesReducer.State()) {
            CertificatesReducer()
        } withDependencies: {
            $0.certificateClient.fetchAll = { throw FetchError() }
        }

        await store.send(.loadItems) { $0.isLoading = true }
        await store.receive(\.itemsLoaded.failure) {
            $0.isLoading = false
            $0.loadError = "Network unavailable"
        }
    }

    // MARK: Navigation

    @Test("itemTapped sets destination to detail")
    func itemTappedSetsDestination() async {
        var state = CertificatesReducer.State()
        let item = makeCertificate()
        state.items = [item]

        let store = TestStore(initialState: state) { CertificatesReducer() }

        await store.send(.itemTapped(item)) {
            $0.destination = .detail(CertificateDetailReducer.State(item: item))
        }
    }

    // MARK: Computed properties (no store needed)

    @Test("isEmpty is true when not loading and items is empty")
    func isEmptyComputed() {
        let state = CertificatesReducer.State()
        #expect(state.isEmpty == true)
    }

    @Test("isEmpty is false when items exist")
    func isEmptyFalseWithItems() {
        var state = CertificatesReducer.State()
        state.items = [makeCertificate()]
        #expect(state.isEmpty == false)
    }

    @Test("isEmpty is false while loading")
    func isEmptyFalseWhileLoading() {
        var state = CertificatesReducer.State()
        state.isLoading = true
        #expect(state.isEmpty == false)
    }
}
```

---

## 4. Package.swift additions

```swift
// In products array:
.library(name: "Certificates", targets: ["Certificates"]),

// In targets array:
.target(name: "Certificates", dependencies: [
    "DesignSystem", "Models", "Services",
    .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
]),
.testTarget(name: "CertificatesTests", dependencies: [
    "Certificates",
    .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
]),
```

Add `"CertificateDetail"` as a separate target only if its reducer+view are too large for one file or it needs independent testing.

---

## 5. AppCore wiring (new tab)

Only needed when this is a top-level tab. Edit `Sources/AppCore/AppCoreView.swift`:

```swift
// 1. Import at top
import Certificates

// 2. State
public struct State: Equatable {
    // ... existing fields ...
    var certificates = CertificatesReducer.State()
}

// 3. Action
public enum Action {
    // ... existing cases ...
    case certificates(CertificatesReducer.Action)
}

// 4. Tab enum
public enum Tab: Hashable {
    // ... existing cases ...
    case certificates
}

// 5. Scope in body (before Reduce)
Scope(state: \.certificates, action: \.certificates) {
    CertificatesReducer()
}

// 6. Reduce: handle cross-tab delegates if needed
case .certificates(.delegate(.someEvent)):
    // ...
    return .none

// 7. TabView tab in AppCoreView
NavigationStack {
    CertificatesView(store: store.scope(state: \.certificates, action: \.certificates))
}
.tabItem { Label("Certificates", systemImage: "doc.badge.checkmark") }
.tag(AppCoreReducer.Tab.certificates)
```

Also add `"Certificates"` to `AppCore`'s target dependencies in `Package.swift`.

---

## 6. Sub-feature (navigation destination)

When `CertificateDetail` is navigated to from `Certificates` (not a tab):

```swift
// CertificateDetailReducer.swift
@Reducer
public struct CertificateDetailReducer {
    @ObservableState
    public struct State: Equatable {
        public let item: Certificate          // let — passed in, immutable
        public var isSharing = false

        public init(item: Certificate) {      // explicit init when let fields exist
            self.item = item
        }
    }

    public enum Action {
        case shareTapped
        case delegate(Delegate)

        @CasePathable
        public enum Delegate {
            case dismissed
        }
    }

    public init() {}

    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .shareTapped:
                state.isSharing = true
                return .none
            case .delegate:
                return .none
            }
        }
    }
}

// Preview for the detail view
#Preview("Certificate Detail") {
    NavigationStack {
        CertificateDetailView(
            store: Store(
                initialState: CertificateDetailReducer.State(item: Certificate.sample)
            ) {
                CertificateDetailReducer()
            }
        )
    }
}
```

The parent (`CertificatesReducer`) already has `.detail(CertificateDetailReducer)` in its `Destination` enum and sets `state.destination = .detail(CertificateDetailReducer.State(item: item))` when navigating.
