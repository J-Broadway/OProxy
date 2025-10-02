# OProxy _add() Method Enhancement - Construction Document

## Overview
Enhance the `_add()` method in `OPContainer` to support adding OPs to existing containers instead of only creating new containers. This change makes the API more intuitive for incremental container building.

## Current Behavior
```python
opr._add('items', ['op1', 'op2'])  # Creates new 'items' container
opr._add('items', ['op3', 'op4'])  # ERROR: Container 'items' already exists - skipping
```

## Proposed Behavior
```python
opr._add('items', ['op1', 'op2'])  # Creates new 'items' container with op1, op2
opr._add('items', ['op3', 'op4'])  # Adds op3, op4 to existing 'items' container
# Result: 'items' contains op1, op2, op3, op4
```

## Implementation Strategy

### Core Logic Refactor
Split `_add()` into two internal methods:
- `_add_init(name, op)`: Create new container (current behavior)
- `_add_insert(container, op)`: Add OPs to existing container (new behavior)

### Main _add() Flow
```python
def _add(self, name, op):
    if name in self._children:
        existing = self._children[name]
        if isinstance(existing, OPContainer):
            self._add_insert(existing, op)
        else:
            raise ValueError(f"Cannot add container '{name}' - already exists as OP")
    else:
        self._add_init(name, op)
```

## Validation Requirements

### Name Validation
- **Reserved Names**: Block internal attributes, methods, properties
- **Magic Methods**: Block dunder methods with escape hatch suggestion
- **Future Convention**: Note about double underscore migration for internal names

### OP Validation
- **Existence Check**: Fail fast on invalid/non-existent OPs
- **Type Validation**: Ensure OPs are valid TouchDesigner objects
- **Duplicate Handling**: Skip OPs that already exist in target container

### Container State Validation
- **Mixed Children**: Allow containers with both sub-containers and OPs
- **Type Conflicts**: Prevent OP names from conflicting with sub-container names

## Edge Cases & Conflict Resolution

### 1. Container vs OP Name Conflicts
```python
opr._add('media', ['movie1'])      # Creates 'media' container
opr.media._add('effects', ['blur1'])  # Creates 'effects' sub-container
opr.media._add('effects', 'new_op')   # ✓ Adds 'new_op' to 'effects' container
```

### 2. Reserved Name Conflicts
```python
opr._add('items', ['op1'])
opr.items._add('_children', ['op2'])   # ✗ ERROR: Reserved internal name
opr.items._add('__str__', ['op3'])     # ✗ ERROR: Magic method (suggest _extend)
opr.items._add('path', ['op4'])        # ✗ ERROR: Reserved property
```

### 3. Case Sensitivity
- 'Media' and 'media' should be separate containers (assuming TouchDesigner case sensitivity)
- Follow TouchDesigner's native OP naming conventions

### 4. Invalid OP Handling
- Stop processing on first invalid OP (fail fast)
- Provide clear error messages indicating which OP failed validation

## Storage & Persistence

### Update Strategy
- **Immediate Persistence**: Save to TouchDesigner storage after each addition
- **Root Container Updates**: Traverse to root and call `__save_to_storage()`
- **Incremental Updates**: Support adding to existing hierarchies without full rebuild

### Storage Structure
Maintain existing nested storage format:
```python
{
    'children': {
        'container_name': {
            'children': {...},  # Nested containers
            'ops': {...},       # OPs in this container
            'extensions': {...}
        }
    }
}
```

## Implementation Details

### _add_init(name, op)
- Create new OPContainer with given name
- Validate and add initial OPs as OPLeaf instances
- Update storage immediately
- Mirror current implementation logic

### _add_insert(container, op)
- Validate OPs against existing container contents
- Skip duplicates with logging
- Add new OPs as OPLeaf instances
- Update storage immediately
- Handle both single OP and list inputs

### Validation Function
```python
def _validate_child_name(self, container, name):
    # Check reserved names, conflicts, etc.
    pass
```

## Logging Strategy
- **Container Creation**: "Created container 'name' with X OPs"
- **Addition to Existing**: "Added X OPs to existing container 'name'"
- **Duplicates**: "OP 'name' already exists - skipping"
- **Errors**: Clear messages for validation failures

## Testing Scenarios

### Basic Functionality
1. Create new container with single OP
2. Create new container with multiple OPs
3. Add single OP to existing container
4. Add multiple OPs to existing container
5. Add OPs to container with existing sub-containers

### Conflict Testing
1. Attempt to create container with reserved name
2. Attempt to add OP with duplicate name
3. Attempt to add to non-existent container
4. Invalid OP handling

### Edge Cases
1. Empty OP lists
2. Mixed valid/invalid OPs (fail fast behavior)
3. Deep nesting operations
4. Storage persistence across sessions

## Migration Considerations

### Backward Compatibility
- Existing code continues to work unchanged
- New behavior is additive, not replacing

### Documentation Updates
- Update method docstrings with new behavior
- Add examples for incremental container building
- Document validation rules and error conditions

## Future Extensions

### Deferred Implementation
- `_extend()` method enhancement for magic method overrides
- Double underscore convention for internal attributes
- Batch operations for multiple container updates
- Conditional validation modes (strict vs permissive)

## Success Criteria
- [ ] All existing tests pass
- [ ] New incremental addition behavior works
- [ ] Validation prevents conflicts appropriately
- [ ] Storage persistence works correctly
- [ ] Error messages are clear and actionable
- [ ] Performance impact is minimal
