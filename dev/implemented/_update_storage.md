# _update_storage() Construction Plan

## Overview

Implement `_update_storage()` method to provide incremental storage updates for individual containers, replacing the current full hierarchy rebuild approach used by `__save_to_storage()`. This enables efficient storage updates during granular refresh operations.

## Current State Analysis

### Problems with Current Implementation
- `__save_to_storage()` always rebuilds entire hierarchy from scratch
- Called after every change (add, remove, etc.)
- Inefficient for large hierarchies during granular operations
- No way to update just changed branches

### Storage Structure Reminder
```
OProxies['children'] = {
    'container1': {
        'ops': {
            'op1': {'path': '/path', 'op': <OP>, 'extensions': {}}
        },
        'children': {
            'nested_container': {...}
        }
    }
}
```

## Design Decisions

### 1. Incremental Updates (Chosen)
**Update only the affected container's data in storage**
- Find the container's location in storage hierarchy
- Replace only that container's data
- Preserve all other container data unchanged

**Benefits:**
- Faster updates for large hierarchies
- Enables granular refresh operations
- Reduces storage I/O overhead

### 2. Root-Only Updates
**Only root containers can update storage directly**
- Non-root containers call `root._update_storage()`
- Maintains single source of truth
- Prevents concurrent update conflicts

## Implementation Plan

### Core Method: `_update_storage()`

**File:** `OPBaseWrapper.py` (in `OPContainer` class)

**Logic:**
- Can only be called on root containers
- Rebuild this container's storage data
- Update the specific location in root storage
- Preserve all other container data

```python
def _update_storage(self):
    """Update storage with current container's data (incremental update)."""
    if not self.is_root:
        raise RuntimeError("_update_storage() can only be called on root containers")

    try:
        # Rebuild this container's complete storage structure
        container_data = self.__build_storage_structure()

        # For root container, replace entire children structure
        self.OProxies['children'] = container_data

        utils.log(f"DEBUG _update_storage: Updated storage for root container")

    except Exception as e:
        utils.log(f"ERROR _update_storage: Failed to update storage: {e}")
        raise
```

### Helper Method: `_update_container_in_storage()`

**For non-root containers to update their specific data:**

```python
def _update_container_in_storage(self, container_data):
    """Update a specific container's data in root storage (called by non-roots)."""
    if self.is_root:
        # Root calls _update_storage() directly
        return self._update_storage()

    # Find root and update specific container location
    root = self.__find_root()
    if not hasattr(root, 'OProxies'):
        return

    # Navigate to parent location in storage
    path_segments = self.path.split('.')
    parent_path = '.'.join(path_segments[:-1])  # Parent container path
    container_name = path_segments[-1]  # This container's name

    # For simplicity, trigger full root update for now
    # TODO: Implement true incremental update navigation
    root._update_storage()
```

## Usage Examples

### Root Container Update
```python
# After changes to root container
root._update_storage()  # Updates entire hierarchy
```

### Branch Container Update (Future Enhancement)
```python
# After changes to specific branch
branch_container._update_container_in_storage(branch_data)
# Should update only that branch in storage
```

## Integration with _refresh()

### Current _refresh() Usage
- Root refresh: `opr._refresh()` → calls `self._update_storage()`
- Branch refresh: `opr.media._refresh()` → needs to call root `_update_storage()`

### Updated Flow
```python
def _refresh(self):
    """Refresh container and all descendants"""
    try:
        self._refresh_ops()
        self._refresh_extensions()

        # Recursive refresh of children
        for child in self._children.values():
            if isinstance(child, OPContainer):
                child._refresh()

        # Update storage if this is root
        if self.is_root:
            self._update_storage()  # New incremental method

    except Exception as e:
        utils.log(f"Container refresh failed for {self.path}: {e}")
```

## Files Requiring Changes

1. **`OPBaseWrapper.py`**
   - Add `_update_storage()` method to `OPContainer`
   - Add `_update_container_in_storage()` helper method
   - Update `_refresh()` methods to use new storage update approach

## Risk Assessment

### Low Risk
- Backward compatibility maintained
- Fallback to full rebuild if needed
- Storage structure unchanged

### Medium Risk
- Initial implementation may still do full rebuilds
- True incremental updates require careful path navigation
- Testing complex storage hierarchies

## Success Criteria

1. **Functionality**: `_update_storage()` updates storage without full rebuild
2. **Performance**: Faster than `__save_to_storage()` for large hierarchies
3. **Correctness**: All container data preserved except updated container
4. **Integration**: Works seamlessly with `_refresh()` operations

## Implementation Order

1. **Implement basic `_update_storage()`** (may do full rebuild initially)
2. **Integrate with `_refresh()` methods**
3. **Add incremental update logic** (future enhancement)
4. **Performance testing and optimization**

This implementation provides the foundation for efficient storage updates during granular refresh operations.
