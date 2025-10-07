# _add() Chaining Implementation Plan

## Overview

Enable chaining for _add() methods across OProxy classes to improve API fluency, aligning with _extend() behavior. Include optional returnObj flag to return the new object instead of self.

## Current State

- _add() currently returns None, preventing chaining.

## Proposed Changes

1. Update _add() in OProxyContainer to return self after addition (or the new container/leaf if returnObj=True).

2. Ensure additions are properly stored and refreshed.

3. Document best practices: Prefer attribute access for hierarchies, use returnObj for selective returns in chains.

## Implementation Phases

### Phase 1: Method Updates

- Modify _add() to perform addition and return self (or new object if returnObj=True).

### Phase 2: Testing

- Add chaining test cases with and without returnObj.
- Verify no side effects on existing code.

## API Examples

```python
# Basic chaining (returns self)
opr._add('container1', ops1)._add('container2', ops2)._extend(...)

# With returnObj to get new container
new_container = opr._add('container', ops, returnObj=True)
new_container._extend(...)

# Selective return in chain
hey = opr._add('one', ...)._add('two', ...)._add('three', returnObj=True)._add('four', ...)
# hey is now opr.one.two.three

# Best practice: Attribute access
opr._add('one', ...)._add('two', ...)
hey = opr.one.two  # Cleaner for static hierarchies
```

## Benefits

- Consistent chaining API across methods.
- Improved developer experience with fluent interfaces.
- Flexible returns via returnObj for complex building patterns.

## Potential Concerns

- Backwards compatibility: Code expecting None may need updates (add deprecation warning if needed).
- Overuse of returnObj could lead to less readable code; emphasize attribute access in docs.
