# _remove() Feature Construction Design

## Overview

The `_remove()` method improvement refactors the current conditional logic into an abstract method pattern where each class type (OPContainer, OPLeaf, OProxyExtension) implements its own removal logic. This enables direct leaf removal (`opr.items('op1')._remove()`), provides cleaner separation of concerns, better polymorphism, and preparation for extension removal capabilities.

## Goals

- **Polymorphic Removal**: Each class type handles its own removal logic
- **Direct Leaf Removal**: Enable `leaf._remove()` for self-removal from parent containers
- **Storage Consistency**: Automatic storage cleanup for all removal operations
- **Extension Support**: Placeholder framework for extension removal (future feature)
- **Robust Error Handling**: Log warnings instead of crashing for invalid operations
- **Flexible API**: Support for removing self, named children, and extension branches

## Current State Analysis

### Existing Implementation Issues

1. **Conditional Logic**: `OPBaseWrapper._remove()` uses complex conditional branching for different removal types
2. **Direct Leaf Removal**: `OPLeaf._remove()` raises `NotImplementedError`, preventing direct leaf self-removal (though container-based removal works)
3. **Storage Coupling**: Removal logic is tightly coupled with storage update mechanisms
4. **Extension Unprepared**: No framework for extension removal (extensions not yet implemented)

### Current Usage Patterns

```python
# Container self-removal (works)
container._remove()  # Remove container from parent

# Named child removal (works)
container._remove('child_name')  # Remove specific child (including leaves)

# Multiple removal (works)
container._remove(['child1', 'child2'])  # Remove multiple children

# Container-based leaf removal (works)
opr.items._remove('op1')  # ✅ Works - removes leaf from container

# Direct leaf self-removal (should work, currently fails)
opr.items('op1')._remove()  # ❌ Currently: NotImplementedError
```

## Requirements

### Functional Requirements

1. **Abstract Method Pattern**: `OPBaseWrapper._remove()` becomes abstract, each subclass implements specific logic
2. **Type-Specific Removal**:
   - `OPContainer._remove(name=None)`: Remove self or named children (including leaves)
   - `OPLeaf._remove()`: NEW - Remove self from parent container
   - `OProxyExtension._remove()`: Remove extension branch (placeholder)
3. **Storage Updates**: All removal operations update TouchDesigner storage automatically
4. **Extension Cleanup**: Remove associated extension branches when removing containers/leafs

### Non-Functional Requirements

1. **Error Handling**: Log warnings for invalid operations, don't crash
2. **Performance**: Minimize storage I/O operations
3. **Maintainability**: Clean separation between removal types
4. **Extensibility**: Easy to add new removal behaviors

## Design Specification

### Method Signatures

```python
class OPBaseWrapper(ABC):
    @abstractmethod
    def _remove(self, name=None):
        """Remove self, named child, or extension. Implementation varies by type."""
        pass

class OPContainer(OPBaseWrapper):
    def _remove(self, name=None):
        """
        Remove container operations.

        Args:
            name: None (remove self), str (remove child), list (remove multiple)
        Returns:
            self for chaining
        """
        pass

class OPLeaf(OPBaseWrapper):
    def _remove(self):
        """
        Remove leaf from parent container.

        Returns:
            self for chaining
        """
        pass

class OProxyExtension(OPBaseWrapper):
    def _remove(self):
        """
        Remove extension branch (placeholder - extensions not yet implemented).

        Returns:
            self for chaining
        """
        pass
```

### Removal Behaviors

#### OPContainer._remove()

1. **Remove Self (`name=None`)**:
   - Find self in parent container
   - Remove from parent's `_children` dict
   - Clean up storage hierarchy
   - Prevent root container removal

2. **Remove Child (`name=str`)**:
   - Validate child exists
   - Remove from `_children` dict
   - Clean up storage hierarchy

3. **Remove Multiple (`name=list`)**:
   - Iterate through names
   - Recursively call single removal

#### OPLeaf._remove()

1. **Validate Parent**: Ensure leaf has parent container
2. **Refresh Check**: Call `_refresh()` to detect OP name changes (future: when implemented)
3. **Extension Cleanup**: Remove extension branches (placeholder)
4. **Remove from Parent**: Remove self from parent's `_children` dict
5. **Storage Update**: Clean up storage hierarchy

#### OProxyExtension._remove() (Placeholder)

1. **Future Implementation**: Remove extension metadata and references
2. **Storage Cleanup**: Remove extension branch from storage
3. **Parent Notification**: Update parent container's extension registry

### Storage Handling

#### Current Storage Structure
```
OProxies: {
    "children": {
        "container_name": {
            "children": {...},
            "ops": {...},
            "extensions": {...}
        }
    }
}
```

#### Removal Storage Updates

1. **Container Removal**: Delete entire branch from `children` dict
2. **Leaf Removal**: Remove OP entry from parent's `ops` dict and extension branches
3. **Extension Removal**: Remove from `extensions` dict
4. **Persistence**: Call `root.__save_to_storage()` after all removals

### Error Handling Strategy

- **Invalid Names**: Log warning, return self (don't crash)
- **Root Removal**: Log warning, return self (don't crash)
- **Missing Extensions**: Log warning (when extensions implemented)
- **Storage Errors**: Log error, continue operation

## Implementation Plan

### Phase 1: Abstract Method Refactor

1. **Update OPBaseWrapper**:
   - Make `_remove()` abstract with signature `def _remove(self, name=None)`
   - Remove current conditional implementation

2. **Implement OPContainer._remove()**:
   - Extract current logic from OPBaseWrapper
   - Maintain backward compatibility
   - Add better error handling

3. **Implement OPLeaf._remove()**:
   - Remove `NotImplementedError`
   - Implement self-removal logic
   - Add extension cleanup placeholder

4. **Create OProxyExtension._remove()**:
   - Placeholder implementation with docstring
   - Future extension removal framework

### Phase 2: Extension Framework Preparation

1. **Extension Validation**:
   - Add `_refresh()` integration (when available)
   - Placeholder validation logic

2. **Storage Extension Cleanup**:
   - Framework for removing extension branches
   - Metadata cleanup procedures

### Phase 3: Testing & Validation

1. **Unit Tests**: Test each removal type
2. **Integration Tests**: Test storage consistency
3. **Error Handling Tests**: Test invalid operations
4. **Regression Tests**: Ensure backward compatibility

## Testing Strategy

### Unit Tests

```python
def test_container_remove_self():
    """Test OPContainer self-removal"""
    # Create container hierarchy
    # Remove container
    # Verify removed from parent
    # Verify storage updated

def test_container_remove_child():
    """Test OPContainer child removal"""
    # Create container with children
    # Remove specific child
    # Verify child removed
    # Verify storage updated

def test_leaf_remove():
    """Test OPLeaf self-removal"""
    # Create container with leaf
    # Remove leaf
    # Verify leaf removed from container
    # Verify storage updated

def test_invalid_removal():
    """Test error handling for invalid removals"""
    # Try to remove non-existent child
    # Verify warning logged
    # Verify no crash
```

### Integration Tests

- **Storage Consistency**: Verify storage matches container hierarchy after removals
- **Extension Cleanup**: Test extension removal (when implemented)
- **Refresh Integration**: Test _refresh() + _remove() workflow

## Future Considerations

### Extension Removal Implementation

When extensions are implemented, `OProxyExtension._remove()` will need to:

1. **Validate Extension**: Check if extension exists and is valid
2. **Clean References**: Remove from parent's extension registry
3. **Storage Cleanup**: Remove extension data from storage
4. **Dependency Handling**: Handle extensions that depend on other extensions

### Advanced Features

1. **Cascading Removal**: Option to remove with dependencies
2. **Dry Run Mode**: Preview what would be removed
3. **Undo Support**: Framework for removal undo operations
4. **Bulk Operations**: Optimized removal for multiple items

## Risk Assessment

### Low Risk
- **Backward Compatibility**: Maintaining existing API signatures
- **Error Handling**: Log-and-continue approach prevents crashes

### Medium Risk
- **Storage Corruption**: Incorrect storage updates could corrupt hierarchy
- **Extension Dependencies**: Future extension removal might break dependencies

### Mitigation Strategies

1. **Comprehensive Testing**: Extensive test coverage for all removal scenarios
2. **Storage Validation**: Verify storage integrity after each removal
3. **Gradual Rollout**: Implement and test each class separately
4. **Documentation**: Clear documentation of removal behaviors and limitations

## Implementation Checklist

- [ ] Create abstract `_remove()` method in OPBaseWrapper
- [ ] Implement OPContainer._remove() with current logic
- [ ] Implement OPLeaf._remove() for self-removal
- [ ] Create OProxyExtension._remove() placeholder
- [ ] Add comprehensive error handling
- [ ] Update storage cleanup logic
- [ ] Add extension cleanup placeholders
- [ ] Create unit tests for all removal types
- [ ] Create integration tests for storage consistency
- [ ] Update documentation and examples
- [ ] Test backward compatibility
