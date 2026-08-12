# Testing Patterns

The test-craft detail behind `references/build-loop.md#test-craft` — full examples, the anti-pattern
table, and the sizing model. Open this when writing the tests for a slice, not when deciding whether
to write them.

Every principle here is stack-agnostic; the illustrations happen to be TypeScript. Read the shape,
not the syntax — `#expect` in Swift Testing and `assert` in pytest fail the same way for the same
reasons. The proportions below are one methodology, hedged deliberately: weight them differently if
your integration layer is where the risk actually lives.

## The pyramid, with proportions

```
          ╱╲
         ╱  ╲         E2E (~5%)      full user flow, real browser/staging, minutes
        ╱    ╲
       ╱──────╲       Integration (~15%)   crosses a boundary — API, DB, filesystem
      ╱        ╲
     ╱          ╲     Unit (~80%)    pure logic, isolated, milliseconds each
    ╱────────────╲
```

| Size | Constraints | Speed | Example |
|---|---|---|---|
| **Small** | Single process, no I/O, no network, no DB | Milliseconds | Pure function tests, data transforms |
| **Medium** | Multi-process OK, localhost only, no external services | Seconds | API tests against a test DB, component tests |
| **Large** | Multi-machine OK, external services allowed | Minutes | E2E tests, staging integration, perf benchmarks |

Decision guide:

```
Pure logic, no side effects?           → unit (small)
Crosses a boundary (API/DB/FS)?        → integration (medium)
Critical user flow, must work e2e?     → e2e (large) — limit these to critical paths
```

Pick the cheapest level that can actually fail when the behavior breaks. A unit test standing in for
an integration behavior is tautological — it can't fail when the real thing does.

**The Beyonce rule.** If you liked it, you should have put a test on it. Refactors and migrations
aren't responsible for catching your bugs — your tests are. A change that breaks untested code was
always going to break it; the test just would have said so first.

## DAMP over DRY

Production code should avoid repetition. Tests should not, when avoiding it costs readability —
each test should read as a self-contained specification. Examples below are TypeScript/Jest; the
principle is stack-agnostic.

```typescript
// DAMP: each test tells its own complete story
it('rejects tasks with empty titles', () => {
  const input = { title: '', assignee: 'user-1' };
  expect(() => createTask(input)).toThrow('Title is required');
});

it('trims whitespace from titles', () => {
  const input = { title: '  Buy groceries  ', assignee: 'user-1' };
  const task = createTask(input);
  expect(task.title).toBe('Buy groceries');
});

// Over-DRY: shared setup obscures what each test actually verifies —
// don't extract a helper just to avoid repeating the input shape.
```

Duplication in tests is acceptable when it keeps each test independently understandable.

## Real > fake > stub > mock

```
1. Real implementation  → highest confidence, catches real bugs
2. Fake                 → in-memory version of a dependency (e.g. a fake DB)
3. Stub                 → returns canned data, no behavior
4. Mock (interaction)   → verifies method calls — use sparingly
```

Use mocks only where the real implementation is too slow, non-deterministic, or has side effects you
can't control (external APIs, email sending). Over-mocking produces tests that pass while production
breaks.

## Arrange-Act-Assert

```typescript
it('marks overdue tasks when deadline has passed', () => {
  // Arrange
  const task = createTask({ title: 'Test', deadline: new Date('2025-01-01') });

  // Act
  const result = checkOverdue(task, new Date('2025-01-02'));

  // Assert
  expect(result.isOverdue).toBe(true);
});
```

## One assertion per concept

```typescript
// Good: each test verifies one behavior
it('rejects empty titles', () => { /* ... */ });
it('trims whitespace from titles', () => { /* ... */ });
it('enforces maximum title length', () => { /* ... */ });

// Bad: three behaviors, one test — a failure doesn't say which one broke
it('validates titles correctly', () => {
  expect(() => createTask({ title: '' })).toThrow();
  expect(createTask({ title: '  hello  ' }).title).toBe('hello');
  expect(() => createTask({ title: 'a'.repeat(256) })).toThrow();
});
```

## Test state, not interactions

Assert on the outcome, not on which internal method fired. Interaction assertions break on
refactors that don't change behavior:

```typescript
// Good: tests what the function does
it('returns tasks sorted by creation date, newest first', async () => {
  const tasks = await listTasks({ sortBy: 'createdAt', sortOrder: 'desc' });
  expect(tasks[0].createdAt.getTime()).toBeGreaterThan(tasks[1].createdAt.getTime());
});

// Bad: tests how it works internally
it('calls db.query with ORDER BY created_at DESC', async () => {
  await listTasks({ sortBy: 'createdAt', sortOrder: 'desc' });
  expect(db.query).toHaveBeenCalledWith(expect.stringContaining('ORDER BY created_at DESC'));
});
```

## Name tests descriptively, and name the behavior

```typescript
// Good: reads like a specification, and BH-014 is greppable
describe('TaskService.completeTask', () => {
  it('sets status to completed and records timestamp — BH-014', ...);
  it('throws NotFoundError for non-existent task — BH-015', ...);
  it('is idempotent, completing an already-completed task is a no-op — BH-016', ...);
});

// Bad: vague, and un-greppable against the behavior spec
describe('TaskService', () => {
  it('works', ...);
  it('handles errors', ...);
});
```

`grep BH-014` across the test tree should find every test proving that behavior. A `BH-###` with no
hits is an uncovered behavior; a test citing no `BH-###` is either missing a citation or testing
something nobody specified.

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Testing implementation details | Breaks on refactors that don't change behavior | Test inputs and outputs, not internal structure |
| Flaky tests (timing, order-dependent) | Erodes trust in the whole suite | Deterministic assertions, isolated test state |
| Testing framework code | Wastes effort on third-party behavior | Only test your own code |
| Snapshot abuse | Large snapshots nobody reviews, break on any change | Use sparingly, review every change |
| No test isolation | Passes alone, fails in the suite | Each test sets up and tears down its own state |
| Mocking everything | Tests pass while production breaks | Real > fake > stub > mock; mock only at slow/non-deterministic boundaries |
