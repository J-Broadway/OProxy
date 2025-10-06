# _storage() Method Construction Plan

## Overview

The `_storage()` method will be added to `OPContainer`, `OProxyExtension`, and `OPLeaf` classes to provide read-only access to serialized storage branches. This allows users to inspect the internal storage structure in a human-readable JSON format, useful for debugging and understanding the hierarchy.

### Requirements
- **Readonly Access**: Method does not modify storage, only reads and serializes
- **Hierarchical Navigation**: Use `self._path` to locate position in storage tree
- **Flexible Querying**: Support viewing entire branches or specific sub-branches
- **Serialization**: Convert TouchDesigner OP objects to serializable dicts
- **Public Usage**: Intended for user inspection, not internal operations
- **Error Handling**: Raise appropriate errors for invalid paths/keys

### Method Signature
```python
def _storage(self, keys=None):
    """
    Public method to view serialized storage branch. Intended for public usage, not internal; use _store() for serialization.
    """
```

### Behavior Examples
- `opr._storage()` # prints entire storage tree
- `opr.item._storage()` # prints 'item' branch only
- `opr._storage('item')` # equivalent to above
- `opr._storage(['item1', 'item2'])` # prints multiple branches
- `opr._storage('doesnt_exist')` # raises KeyError

## Current State Analysis

### Storage Architecture
- Root storage accessed via `root.OProxies` (DependDict from TDStoreTools)
- Structure: `{'children': {...}, 'extensions': {}}`
- Nested containers: `children[container_name] = {'children': {}, 'ops': {}, 'extensions': {}}`
- OPs stored as: `ops[op_name] = {'path': str, 'op': TD_OP, 'extensions': {}}`
- Extensions stored as metadata dicts

### Class Hierarchy
- `OPBaseWrapper` (abstract base)
  - `OPContainer` (root and nested containers)
  - `OPLeaf` (individual OPs)
  - `OProxyExtension` (extensions on containers/leaves)

### Path Structure
- Root: `path=""`
- Containers: `path="container_name"` or `"parent.subcontainer"`
- Leaves: `path="container.op_name"` or `"parent.container.op_name"`
- Extensions: `path=""` (no path, located via parent)

## Design Decisions

### 1. Navigation Strategy
**Decision**: Use path segments to traverse storage tree starting from root.
- For containers/leaves: Split `self._path` by '.' and navigate `['children']` for each segment except last
- For containers: Last segment in `['children']`
- For leaves: Last segment in `['ops']`
- For extensions: Special handling using parent branch and `_extension_name`

**Rationale**: Consistent with storage structure, handles deep nesting.

### 2. Root Access
**Decision**: Find root via parent traversal, access `root.OProxies.getRaw()` for DependDict unwrapping.

**Rationale**: Ensures we get the current storage state without dependency overhead.

### 3. Serialization
**Decision**: Create `make_serializable()` in `utils.py` to handle:
- TD OP objects → `{'name': str, 'type': str, 'path': str}`
- DependDict → raw dict via `.getRaw()`
- Dependency unwrapping via `.val`
- Recursive handling of nested structures

**Rationale**: TD objects aren't JSON serializable; need clean conversion.

### 4. Keys Parameter Handling
**Decision**: Support `keys` as `str`, `list`, or `None`:
- `None`: Return entire branch
- `str`: Return sub-branch at that key
- `list`: Return dict of sub-branches

**Rationale**: Flexible querying while maintaining simple interface.

### 5. Error Handling
**Decision**: Raise `KeyError` for missing paths/keys, `TypeError` for invalid keys parameter.

**Rationale**: Standard Python exceptions for clear error reporting.

### 6. Output Format
**Decision**: Print JSON with `indent=4` and return the string for flexibility.

**Rationale**: Immediate visual feedback while allowing programmatic use.

## Implementation Plan

### Phase 1: Serialization Infrastructure

#### 1.1 Add `make_serializable()` to utils.py
**Task**: Implement recursive serialization function
**Files**: `utils.py`
**Code**:
```python
def make_serializable(storage):
    # Handle TD objects, DependDict, dependencies, recursion
```

#### 1.2 Test serialization
**Task**: Verify OP objects convert correctly
**Files**: Manual testing in TD

### Phase 2: Core Method Implementation

#### 2.1 Add `_storage()` to OPContainer
**Task**: Implement navigation and serialization logic
**Files**: `OPBaseWrapper.py` (OPContainer class)
**Logic**:
- Handle root vs nested containers
- Navigate storage tree
- Apply keys filtering
- Serialize and output

#### 2.2 Add `_storage()` to OPLeaf
**Task**: Implement leaf-specific navigation
**Files**: `OPBaseWrapper.py` (OPLeaf class)
**Logic**: Similar to container but last segment in 'ops'

#### 2.3 Add `_storage()` to OProxyExtension
**Task**: Handle extension access via parent
**Files**: `OPBaseWrapper.py` (OProxyExtension class)
**Logic**: Use parent._storage() + extensions[key]

#### 2.4 Import requirements
**Task**: Ensure `import json` in OPBaseWrapper.py
**Files**: `OPBaseWrapper.py`

### Phase 3: Integration and Testing

#### 3.1 Basic functionality tests
**Task**: Test each class type with various scenarios
**Files**: `dev/tests/test_functions.py` or new test file
**Cases**:
- Root container full storage
- Nested container branches
- Leaf branches
- Extension branches
- Keys parameter variations
- Error cases

#### 3.2 Storage state verification
**Task**: Ensure no storage modifications occur
**Files**: Test scripts
**Verify**: Storage unchanged after calls

#### 3.3 Performance testing
**Task**: Test with large hierarchies
**Files**: Manual testing
**Concern**: Deep recursion on large storage

### Phase 4: Documentation and Polish

#### 4.1 Update docstrings
**Task**: Ensure clear documentation for public usage
**Files**: OPBaseWrapper.py

#### 4.2 Add usage examples
**Task**: Document common patterns
**Files**: Relevant docs

## Testing Strategy

### Unit Tests
- Mock storage structures
- Test navigation logic
- Test serialization edge cases
- Test error conditions

### Integration Tests
- Full OProxy hierarchy
- Real TD OP objects
- Storage persistence across reloads

### Manual Testing
- TouchDesigner DAT testing
- Visual verification of JSON output
- Performance with large hierarchies

## Risk Assessment

### High Risk
- **Storage Corruption**: Method modifies storage accidentally
  - **Mitigation**: Extensive readonly testing, no assignment operations

### Medium Risk
- **Performance Issues**: Deep recursion on large hierarchies
  - **Mitigation**: Test with realistic data sizes, consider caching

- **Serialization Errors**: TD objects change unexpectedly
  - **Mitigation**: Robust error handling, test with various OP types

### Low Risk
- **Path Navigation**: Incorrect path parsing
  - **Mitigation**: Unit tests for path logic, validate against storage structure

- **Extension Access**: Extensions not properly accessible
  - **Mitigation**: Test extension scenarios thoroughly

## Success Criteria

1. **Functionality**: All example usages work correctly
2. **Readonly**: No storage modifications during calls
3. **Performance**: Reasonable response time on typical hierarchies
4. **Error Handling**: Clear, appropriate errors for invalid inputs
5. **Serialization**: Clean JSON output without TD-specific objects

## Implementation Checklist

- [ ] Add `make_serializable()` to `utils.py`
- [ ] Implement `_storage()` in `OPContainer`
- [ ] Implement `_storage()` in `OPLeaf`
- [ ] Implement `_storage()` in `OProxyExtension`
- [ ] Add JSON import to `OPBaseWrapper.py`
- [ ] Basic functionality testing
- [ ] Error case testing
- [ ] Performance testing
- [ ] Documentation updates

## Dependencies

- **Storage Structure**: Relies on current nested storage format
- **TDStoreTools**: DependDict handling
- **utils.py**: Serialization function

## Next Steps

1. Implement serialization function
2. Add method stubs to classes
3. Implement navigation logic
4. Basic testing
5. Full integration testing
