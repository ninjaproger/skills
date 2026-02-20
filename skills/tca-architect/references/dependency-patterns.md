# Dependency Patterns

## Table of Contents
1. [@DependencyClient Macro (preferred)](#1-dependencyclient-macro-preferred)
2. [Manual Struct Pattern](#2-manual-struct-pattern)
3. [Actor as Dependency](#3-actor-as-dependency)
4. [Live Implementation](#4-live-implementation)
5. [Mock for Previews](#5-mock-for-previews)
6. [Using Dependencies in Reducers](#6-using-dependencies-in-reducers)
7. [DependencyValues Extensions](#7-dependencyvalues-extensions)
8. [Choosing a Pattern](#8-choosing-a-pattern)

---

## 1. @DependencyClient Macro (preferred)

`@DependencyClient` auto-generates `unimplemented()` stubs for properties without a default value. Simpler to write, less boilerplate.

```swift
// Sources/Services/UserClient.swift
import Dependencies
import DependenciesMacros
import Foundation
import Models

@DependencyClient
public struct UserClient: Sendable {
    // Properties with defaults → used as testValue stubs automatically
    public var fetchProfile: @Sendable (_ userId: UUID) async throws -> User
    public var updateProfile: @Sendable (_ user: User) async throws -> User
    public var logout: @Sendable () async throws -> Void
    // Properties with default value → not marked unimplemented in test
    public var isLoggedIn: @Sendable () -> Bool = { false }
}

extension UserClient: DependencyKey {
    public static let liveValue: UserClient = .live  // defined in UserClient+Live.swift
}

extension UserClient: TestDependencyKey {
    // @DependencyClient generates testValue automatically — unimplemented for each property
    public static let testValue = UserClient()
}

extension DependencyValues {
    public var userClient: UserClient {
        get { self[UserClient.self] }
        set { self[UserClient.self] = newValue }
    }
}
```

---

## 2. Manual Struct Pattern

Use when you need explicit control over the `testValue` stubs (e.g., to add custom error messages) or when not using the `DependenciesMacros` package.

```swift
// Sources/Services/ChapterClient.swift
import Dependencies
import Foundation
import Models

public struct ChapterClient: Sendable {
    public var fetchChapter: @Sendable (UUID, Bundle) async throws -> Chapter
    public var getProgress: @Sendable (UUID) async throws -> ChapterProgress
    public var markStepComplete: @Sendable (UUID, UUID) async throws -> ChapterProgress

    public init(
        fetchChapter: @escaping @Sendable (UUID, Bundle) async throws -> Chapter,
        getProgress: @escaping @Sendable (UUID) async throws -> ChapterProgress,
        markStepComplete: @escaping @Sendable (UUID, UUID) async throws -> ChapterProgress
    ) {
        self.fetchChapter = fetchChapter
        self.getProgress = getProgress
        self.markStepComplete = markStepComplete
    }
}

extension ChapterClient: TestDependencyKey {
    public static let testValue = ChapterClient(
        fetchChapter:     unimplemented("ChapterClient.fetchChapter"),
        getProgress:      unimplemented("ChapterClient.getProgress"),
        markStepComplete: unimplemented("ChapterClient.markStepComplete")
    )
}

extension DependencyValues {
    public var chapterClient: ChapterClient {
        get { self[ChapterClient.self] }
        set { self[ChapterClient.self] = newValue }
    }
}
```

---

## 3. Actor as Dependency

Use for stateful in-process stores (e.g., a database/cache actor) rather than service clients.

```swift
// Sources/Services/UserDatabase.swift
import Dependencies
import Foundation
import Models

public actor UserDatabase {
    private var cache: [UUID: User] = [:]

    public static let shared = UserDatabase()

    public func get(_ id: UUID) async throws -> User {
        if let user = cache[id] { return user }
        throw DatabaseError.notFound
    }

    public func save(_ user: User) async throws {
        cache[user.id] = user
        // persist to UserDefaults / SQLite
    }
}

extension UserDatabase: DependencyKey {
    public nonisolated static let liveValue = UserDatabase.shared
}

extension UserDatabase: TestDependencyKey {
    public nonisolated static let testValue = UserDatabase()  // fresh instance per test
}

extension DependencyValues {
    public var userDatabase: UserDatabase {
        get { self[UserDatabase.self] }
        set { self[UserDatabase.self] = newValue }
    }
}
```

---

## 4. Live Implementation

Put live implementations in a `+Live` file to keep the interface clean:

```swift
// Sources/Services/UserClient+Live.swift
import Foundation
import Models

extension UserClient {
    public static let live = UserClient(
        fetchProfile: { userId in
            let url = URL(string: "https://api.example.com/users/\(userId)")!
            let (data, _) = try await URLSession.shared.data(from: url)
            return try JSONDecoder().decode(User.self, from: data)
        },
        updateProfile: { user in
            // POST request ...
            return user
        },
        logout: {
            // clear keychain, session tokens...
        },
        isLoggedIn: {
            // check keychain
            return UserDefaults.standard.bool(forKey: "isLoggedIn")
        }
    )
}
```

---

## 5. Mock for Previews

Add a `.mock` static for SwiftUI previews:

```swift
// Sources/Services/UserClient+Mock.swift (or inline in UserClient.swift)
extension UserClient {
    public static let mock = UserClient(
        fetchProfile: { _ in .mock },
        updateProfile: { $0 },
        logout: {},
        isLoggedIn: { true }
    )
}

extension User {
    public static let mock = User(id: UUID(), name: "Jane Doe", email: "jane@example.com")
}
```

In previews:
```swift
#Preview {
    UserProfileView(store: Store(initialState: .init()) {
        UserProfileReducer()
    } withDependencies: {
        $0.userClient = .mock
    })
}
```

---

## 6. Using Dependencies in Reducers

Declare at the top of the reducer struct using `@Dependency`:

```swift
@Reducer
public struct UserProfileReducer {
    @Dependency(\.userClient) var userClient
    @Dependency(\.userDatabase) var database

    public var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .loadProfile:
                return .run { [userId = state.userId, userClient] send in
                    await send(.profileLoaded(Result {
                        try await userClient.fetchProfile(userId)
                    }))
                }
            // ...
            }
        }
    }
}
```

**Always capture dependencies explicitly** in `.run` closures to satisfy Swift 6 strict concurrency:
```swift
// ✅ Correct
return .run { [client = userClient] send in ... }

// ❌ Avoid — may cause Sendable warnings
return .run { send in
    _ = self.userClient  // captures self
}
```

---

## 7. DependencyValues Extensions

Collect all `DependencyValues` extensions in a single file for discoverability:

```swift
// Sources/Services/Services.swift
import Dependencies

extension DependencyValues {
    public var userClient: UserClient {
        get { self[UserClient.self] }
        set { self[UserClient.self] = newValue }
    }

    public var chapterClient: ChapterClient {
        get { self[ChapterClient.self] }
        set { self[ChapterClient.self] = newValue }
    }

    public var userDatabase: UserDatabase {
        get { self[UserDatabase.self] }
        set { self[UserDatabase.self] = newValue }
    }
}
```

---

## 8. Choosing a Pattern

| Scenario | Pattern |
|----------|---------|
| Stateless API/service wrapper | `@DependencyClient` macro |
| Need custom `unimplemented` messages | Manual struct |
| In-process stateful store (cache, DB) | Actor conforming to `DependencyKey` |
| Testing: override one method | `withDependencies { $0.client.fetch = { ... } }` |
| Preview: full mock | Static `.mock` on the client struct |

**Decision guide:**
- Start with `@DependencyClient` — it's the least boilerplate
- Switch to manual struct only if you need custom test error messages or `unimplemented` is unavailable
- Use an actor when the dependency holds mutable state shared across the process
