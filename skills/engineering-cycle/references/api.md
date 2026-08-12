# API and Module Boundaries

Open this when designing a module seam, a package interface, or an endpoint. The dominant
interface problem in this bundle is not OpenAPI — it's the boundary between packages: a
multi-target Swift Package Manager architecture where every public package interface is an API,
and every module contract between subsystems is a promise someone else is building on. REST and
GraphQL are one instance of this problem, not the whole of it. The stack-neutral principles below
apply to all of them; the HTTP and TypeScript specifics come after.

## Core principles

**Hyrum's Law.** With enough consumers, every observable behavior of your system — including
undocumented quirks, error message text, timing, ordering — becomes a de facto contract, no matter
what the documented contract says. Be intentional about what you expose; don't leak implementation
details; assume anything observable will be depended on.

**The One-Version Rule.** Don't force consumers to choose between versions of the same
dependency or API. Diamond-dependency problems come from different consumers needing different
versions of the same thing. Design so only one version exists at a time — extend rather than fork.

**Contract first.** Define the interface — the types, the method signatures, what each call
promises — before implementing it. The contract is the spec; implementation follows it, not the
other way around.

**Consistent error semantics.** Pick one error strategy for a given boundary and use it
everywhere inside it. If some calls throw, others return `null`, and others return `Result`, the
caller can't predict behavior without reading the implementation — which defeats the point of
having a boundary.

**Validate at boundaries, trust internal code.** Validation belongs where external input enters:
route handlers, form submissions, third-party API responses (**always untrusted — see
`references/security.md`**), environment variable loading. It does not belong between two internal
functions that already share a type contract — re-validating there is noise that hides where the
real trust boundary is.

**Prefer addition over modification.** Add optional fields; don't change an existing field's type
or remove it. A consumer who never asked for the new field should see nothing change.

**Predictable naming.** Consistent conventions — plural nouns for resources, `is`/`has`/`can` for
booleans, one casing scheme per boundary — are part of the contract. A caller who has to check
per-endpoint whether it's `taskId` or `task_id` is reading undocumented API surface.

**Plan for deprecation at design time.** Every boundary you add now is a boundary you'll need to
change later. Decide the deprecation path — how a field or method gets marked, how long it
overlaps with its replacement, how consumers are notified — when you design the interface, not
when you're forced to break it. Full process: `references/migration.md`.

## Module and package boundaries are APIs too

The moment a type, function, or protocol is `public` and another target imports it, it is a public
API — subject to the same Hyrum's Law and same-version discipline as a REST endpoint, whether or
not anyone calls it that. Treat a package boundary with the same rigor:

- **Public surface is a decision, not a default.** Every `public` declaration is a promise you
  now have to keep. Default to the narrowest access level that satisfies the actual consumer, and
  widen it only when a real caller needs it — not preemptively.
- **A module contract is the interface plus the invariants the interface doesn't state in
  types** — call order, thread-safety, what happens on repeated calls. Undocumented invariants are
  exactly the Hyrum's Law surface: a consumer will depend on the actual behavior, not the intended
  one.
- **Breaking an internal package is still a breaking change.** "It's internal" is not an exemption
  from the deprecation path above — it just means the consumer list is shorter and easier to find,
  which makes coordination cheaper, not optional.

<!-- stack: apple -->
### Swift Package Manager specifics

- **Access control is the enforcement mechanism, not documentation.** `public` is visible to every
  importer, including outside the package; `package` (Swift 5.9+) is visible across targets in the
  same package but not beyond it — the right default for cross-module APIs that are internal to
  your app; `internal` (the implicit default) stays inside one target. Reach for `package` before
  reaching for `public` when the only consumers are other targets in the same package.
- **A public type's conformances are part of its API.** Adding a protocol conformance to a public
  type is additive and safe; removing one is a breaking change even though the type's own members
  didn't move — Hyrum's Law again, this time via `extension` and conditional conformance.
- **A framework target set to library evolution / ABI-stable mode has a stricter contract** than a
  plain SPM library — resilient types, `@frozen` decisions, and inlinable code all become part of
  the public contract. Know which mode a package target is in before assuming "add a field" is
  free.

<!-- stack: backend -->
## REST and GraphQL specifics

**Resource design** — plural nouns, no verbs in the URL:

```
GET    /api/tasks              List (query params for filtering)
POST   /api/tasks              Create
GET    /api/tasks/:id          Get one
PATCH  /api/tasks/:id          Partial update
DELETE /api/tasks/:id          Idempotent delete
GET    /api/tasks/:id/comments Sub-resource list
```

**Pagination** — every list endpoint takes it, from the start:

```
GET /api/tasks?page=1&pageSize=20&sortBy=createdAt&sortOrder=desc
-> { "data": [...], "pagination": { "page": 1, "pageSize": 20, "totalItems": 142, "totalPages": 8 } }
```

**Filtering** via query params: `GET /api/tasks?status=in_progress&assignee=user123`.

**PATCH accepts partial objects** — only the fields present change; everything else is preserved.
Don't reach for PUT-with-full-object to avoid implementing partial-update semantics.

**Error shape, one format for every endpoint:**

```typescript
interface APIError {
  error: { code: string; message: string; details?: unknown };
}
// 400 invalid data · 401 not authenticated · 403 not authorized
// 404 not found · 409 conflict · 422 validation failed · 500 server error (never leak internals)
```

<!-- stack: web -->
## TypeScript interface patterns

**Discriminated unions for variants** — the compiler narrows for the caller instead of the caller
checking optional fields by hand:

```typescript
type TaskStatus =
  | { type: 'pending' }
  | { type: 'in_progress'; assignee: string; startedAt: Date }
  | { type: 'completed'; completedAt: Date; completedBy: string }
  | { type: 'cancelled'; reason: string; cancelledAt: Date };
```

**Input/output separation** — the type a caller sends is not the type the system returns:

```typescript
interface CreateTaskInput { title: string; description?: string }
interface Task { id: string; title: string; description: string | null; createdAt: Date; createdBy: string }
```

**Branded types for IDs** — prevents passing a `UserId` where a `TaskId` is expected, at compile
time instead of via a runtime bug report:

```typescript
type TaskId = string & { readonly __brand: 'TaskId' };
type UserId = string & { readonly __brand: 'UserId' };
```

## Verify

- [ ] Every endpoint/method has typed input and output, defined before the implementation
- [ ] Error responses follow one consistent format across the boundary
- [ ] Validation happens at the boundary only — not re-checked between trusted internal calls
- [ ] List endpoints support pagination
- [ ] New fields are additive and optional; nothing existing changed type or was removed
- [ ] Public/`package`/internal access level chosen deliberately, not left at the widest default
- [ ] Naming is consistent with the rest of the boundary
- [ ] A deprecation path is named for anything this interface will eventually replace
