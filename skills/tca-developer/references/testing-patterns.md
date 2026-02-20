# Testing Patterns

## Table of Contents
1. [TestStore setup](#1-teststore-setup)
2. [State mutation assertions](#2-state-mutation-assertions)
3. [Async loading flow](#3-async-loading-flow)
4. [Error handling](#4-error-handling)
5. [Delegate actions](#5-delegate-actions)
6. [Navigation (destination)](#6-navigation-destination)
7. [Computed property tests (no store)](#7-computed-property-tests-no-store)
8. [Idempotency tests](#8-idempotency-tests)
9. [Child-to-parent delegate interception](#9-child-to-parent-delegate-interception)
10. [Test file structure](#10-test-file-structure)

---

## 1. TestStore setup

```swift
import ComposableArchitecture
import Testing
@testable import FeatureModule   // or without @testable if types are public

@Suite("FeatureReducer Tests")
@MainActor                        // always @MainActor for TestStore
struct FeatureReducerTests {

    @Test("description")
    func testName() async {
        let store = TestStore(
            initialState: FeatureReducer.State()   // or pre-built state
        ) {
            FeatureReducer()
        } withDependencies: {
            // Override only what's needed for this test
            $0.someClient.fetchAll = { [item1, item2] }
            $0.someClient.save = { _ in }
        }

        // Optional: turn off exhaustive checking when testing a subset of actions
        store.exhaustivity = .off

        await store.send(.someAction) { /* assert state */ }
        await store.receive(\.someOtherAction) { /* assert state */ }
    }
}
```

**`exhaustivity = .off`**: Use when the test only cares about specific actions and you don't want to enumerate all intermediate `.run` effects. Default is exhaustive (every action must be asserted).

---

## 2. State mutation assertions

Inside `send(_:)` and `receive(_:)` closures, `$0` is the `inout State` after the action runs. Assert only the fields that change.

```swift
await store.send(.loadItems) {
    $0.isLoading = true
    $0.loadError = nil
}

await store.receive(\.itemsLoaded.success) {
    $0.isLoading = false
    $0.items = expectedItems
}

// No closure needed when state doesn't change:
await store.send(.cancelTapped)
await store.receive(\.delegate.dismissed)
```

---

## 3. Async loading flow

```swift
@Test("full load flow: loading state → success → populated items")
func fullLoadFlow() async {
    let items = [makeItem(), makeItem(title: "Second")]

    let store = TestStore(initialState: FeatureReducer.State()) {
        FeatureReducer()
    } withDependencies: {
        $0.itemClient.fetchAll = { items }
    }

    await store.send(.loadItems) {
        $0.isLoading = true
        $0.loadError = nil
    }
    await store.receive(\.itemsLoaded.success) {
        $0.isLoading = false
        $0.items = items
    }
}
```

---

## 4. Error handling

```swift
@Test("load failure sets loadError string")
func loadFailure() async {
    struct TestError: Error, LocalizedError {
        var errorDescription: String? { "Connection lost" }
    }

    let store = TestStore(initialState: FeatureReducer.State()) {
        FeatureReducer()
    } withDependencies: {
        $0.itemClient.fetchAll = { throw TestError() }
    }

    await store.send(.loadItems) { $0.isLoading = true }
    await store.receive(\.itemsLoaded.failure) {
        $0.isLoading = false
        $0.loadError = "Connection lost"
    }
}
```

---

## 5. Delegate actions

```swift
// Assert a delegate action is sent:
await store.send(.doneTapped)
await store.receive(\.delegate.dismissed)

// Assert delegate with payload:
await store.send(.saveTapped)
await store.receive(\.delegate.saved) { _ in
    // No state change in child for delegate actions
}

// Verify the exact payload (use store.exhaustivity = .off for surrounding noise):
store.exhaustivity = .off
await store.send(.submitTapped)
await store.receive(\.delegate.completed) { state in
    // delegate actions don't mutate state in the child
}
```

---

## 6. Navigation (destination)

```swift
@Test("itemTapped sets destination to detail")
func itemTappedSetsDestination() async {
    let item = makeItem()
    var state = FeatureReducer.State()
    state.items = [item]

    let store = TestStore(initialState: state) { FeatureReducer() }

    await store.send(.itemTapped(item)) {
        $0.destination = .detail(DetailReducer.State(item: item))
    }
}

@Test("child detail dismiss clears destination")
func detailDismissed() async {
    let item = makeItem()
    var state = FeatureReducer.State()
    state.destination = .detail(DetailReducer.State(item: item))

    let store = TestStore(initialState: state) { FeatureReducer() }

    await store.send(.destination(.presented(.detail(.delegate(.dismissed))))) {
        $0.destination = nil
    }
}
```

---

## 7. Computed property tests (no store)

Computed properties on `State` can be tested without `TestStore` — cheaper and faster.

```swift
@Test("isEmpty is true when not loading and items empty")
func isEmptyWhenNoItems() {
    let state = FeatureReducer.State()
    #expect(state.isEmpty == true)
}

@Test("isEmpty is false while loading")
func isEmptyFalseWhileLoading() {
    var state = FeatureReducer.State()
    state.isLoading = true
    #expect(state.isEmpty == false)
}

@Test("canSubmit requires all questions answered")
func canSubmitRequiresAllAnswers() {
    var state = QuizReducer.State(quiz: makeQuiz(), chapterId: UUID(), existingAttempts: [])
    #expect(state.canSubmit == false)

    // Answer all questions
    for question in state.quiz.questions {
        state.selectedAnswers[question.id] = question.options[0].id
    }
    #expect(state.canSubmit == true)
}
```

---

## 8. Idempotency tests

Verify that re-triggering an action when already in final state is a no-op.

```swift
@Test("onAppear does not reload when items already loaded")
func onAppearIdempotent() async {
    var state = FeatureReducer.State()
    state.items = [makeItem()]   // already loaded

    let store = TestStore(initialState: state) { FeatureReducer() }

    await store.send(.onAppear)
    // Nothing received — test passes because TestStore verifies no unexpected actions
}

@Test("markComplete is no-op when already completed")
func markCompleteAlreadyCompleted() async {
    let store = TestStore(
        initialState: StepDetailReducer.State(step: makeStep(), isCompleted: true, chapterId: UUID())
    ) {
        StepDetailReducer()
    }

    await store.send(.markCompleteTapped)
    // No state change, no actions received
}
```

---

## 9. Child-to-parent delegate interception

Test that the parent responds correctly to a child's delegate action.

```swift
@Test("child progress update propagates to parent chapterProgresses dict")
func childProgressDelegateUpdatesParent() async {
    let chapterId = UUID()
    let stepId = UUID()

    let store = TestStore(initialState: CourseReducer.State()) {
        CourseReducer()
    } withDependencies: {
        $0.courseProgressDatabase = .testValue
    }

    let progress = ChapterProgress(chapterId: chapterId, completedSteps: [stepId])

    // Simulate child sending delegate upward
    await store.send(
        .destination(.presented(.chapter(.delegate(.progressUpdated(progress)))))
    ) {
        $0.chapterProgresses[chapterId] = progress
    }
}

@Test("settings progressReset sends course reload")
func settingsProgressResetCausesReload() async {
    let store = TestStore(initialState: AppCoreReducer.State()) {
        AppCoreReducer()
    } withDependencies: {
        $0.courseProgressDatabase.resetAllProgress = {}
    }
    store.exhaustivity = .off

    await store.send(.settings(.delegate(.progressReset)))
    await store.receive(\.course.loadCourse)
}
```

---

## 10. Test file structure

```swift
import ComposableArchitecture
import Foundation
import Models
import Testing
@testable import TargetModule

// MARK: - Test data factory functions (top-level, reusable across test methods)

func makeItem(
    id: UUID = UUID(),
    title: String = "Test Item"
) -> Item {
    Item(id: id, title: title, createdAt: Date())
}

func makeItems(count: Int = 3) -> [Item] {
    (1...count).map { makeItem(title: "Item \($0)") }
}

// MARK: - Test suite

@Suite("FeatureReducer Tests")
@MainActor
struct FeatureReducerTests {

    // Group related tests:
    // - Loading tests
    // - Navigation tests
    // - Computed property tests
    // - Idempotency tests
    // - Delegate tests

    @Test("loading: success path")
    func loadSuccess() async { ... }

    @Test("loading: failure sets error")
    func loadFailure() async { ... }

    @Test("navigation: tap sets destination")
    func tapSetsDestination() async { ... }

    @Test("computed: isEmpty logic")
    func isEmptyLogic() { ... }
}
```

**Tips:**
- Use `@MainActor` on the `@Suite` to avoid repeating it on every `@Test`
- Factory functions at file scope are reusable across test methods without a shared setup method
- Use `store.exhaustivity = .off` freely — it doesn't weaken the test, just skips unrelated actions
- Prefer `#expect(x == y)` over `XCTAssertEqual` — the Swift Testing framework gives better diffs
