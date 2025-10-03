# _refresh() Refactor Construction Plan

## Overview

Refactor `_refresh()` to work on all OPContainers and OPLeaves (not just root), enabling branch-specific refreshes and automatic name change detection for OPs and extensions.

## Current State Analysis

### Problems with Current Implementation
- `_refresh()` only works on root containers (`if not self.is_root: raise RuntimeError`)
- Always does full hierarchy rebuild
- No granular control over what gets refreshed
- Cannot detect or handle OP name changes in TouchDesigner

### Recent Storage Improvements
- Storage structure updated to include raw OP objects for name change detection
- New format: `{'path': '/path', 'op': <OP object>, 'extensions': {}}`
- Enables detection when `stored_key != stored_op.name`

## Design Decisions

### 1. Polymorphic Architecture (Chosen)
**Each class implements its own `_refresh()` method:**
- `OPContainer._refresh()` - Refreshes container OPs + extensions + recursively refreshes children
- `OPLeaf._refresh()` - Refreshes leaf extensions only
- Future: `OProxyExtension._refresh()` - Extension-specific refresh

**Benefits:**
- Clean separation of concerns
- Automatic routing via inheritance (no manual type checking)
- Easy to extend for new types
- Each class handles its own refresh logic

### 2. Depth-First Recursion (Chosen)
**Process each branch completely before siblings:**
```
opr.one._refresh()
├── one._refresh_ops() + _refresh_extensions()
├── one.two._refresh()          # Recursive call
│   ├── two._refresh_ops() + _refresh_extensions()
│   └── two.three._refresh()    # Deeper recursion
└── Storage update
```

**Benefits:**
- Dependencies flow parent → child correctly
- Path updates work when parent names change
- Memory efficient for typical OProxy trees
- Matches nested storage structure

### 3. Immediate Storage Updates
**Update storage immediately when changes detected, not batched.**

**Rationale:**
- Simpler implementation
- Ensures consistency if refresh is interrupted
- Easier debugging

### 4. Graceful Error Handling
**Log errors but don't halt execution:**
- Individual container/leaf failures don't break entire refresh
- Allows partial success
- Easier debugging in complex projects

## Implementation Plan

### Phase 1: Core Refactor

#### 1.1 Update `OPBaseWrapper._refresh()` (Abstract)
**File:** `OPBaseWrapper.py`
**Changes:**
- Remove root-only restriction
- Make abstract (implemented by subclasses)
- Add basic error handling framework

```python
def _refresh(self, target=None):
    """Abstract refresh method - implemented by subclasses"""
    raise NotImplementedError("_refresh must be implemented by subclasses")
```

#### 1.2 Implement `OPContainer._refresh()`
**File:** `OPBaseWrapper.py` (in `OPContainer` class)
**Logic:**
- Refresh OPs directly in this container
- Refresh extensions on this container (placeholder)
- Recursively refresh all child containers (depth-first)
- Update storage via root

```python
def _refresh(self, target=None):
    """Refresh container and all descendants"""
    try:
        self._refresh_ops(target)
        self._refresh_extensions(target)

        # Recursive refresh of children
        for child in self._children.values():
            if isinstance(child, OPContainer):
                child._refresh()

        # Update storage if this is root
        if self.is_root:
            self._update_storage()

    except Exception as e:
        utils.log(f"Container refresh failed for {self.path}: {e}")
```

#### 1.3 Implement `OPLeaf._refresh()`
**File:** `OPBaseWrapper.py` (in `OPLeaf` class)
**Logic:**
- Refresh extensions on this leaf (placeholder)
- No recursion (leaves have no children)

```python
def _refresh(self, target=None):
    """Refresh leaf extensions"""
    try:
        self._refresh_extensions(target)
    except Exception as e:
        utils.log(f"Leaf refresh failed for {self.path}: {e}")
```

#### 1.4 Add Helper Methods

**`_refresh_ops(self, target=None)`**
- Load stored container data
- For each stored OP:
  - Check if OP still exists and is valid
  - Compare stored key vs current OP name
  - Update container mapping if name changed
  - Update OPLeaf path if necessary

**`_refresh_extensions(self, target=None)`**
- Placeholder for extension refresh logic
- Will re-extract from DATs when `_extend()` is implemented

**`_get_stored_container_data(self)`**
- Navigate storage structure to find this container's data
- Handle nested storage hierarchy

### Phase 2: Error Handling & Validation

#### 2.1 Add Comprehensive Error Handling
- Wrap all operations in try/catch
- Log specific error types (OP not found, storage corrupted, etc.)
- Continue processing other items when one fails

#### 2.2 Add Validation
- Check storage structure integrity
- Validate OP objects are still accessible
- Handle corrupted storage gracefully

### Phase 3: Testing & Validation

#### 3.1 Unit Tests
- Test OP name change detection
- Test container refresh recursion
- Test error handling scenarios
- Test storage updates

#### 3.2 Integration Tests
- Full branch refresh scenarios
- Mixed success/failure cases
- Performance testing with large hierarchies

## Usage Examples with Execution Flow (After Implementation)

### Root Refresh (Existing Behavior)
```python
opr._refresh()  # Full hierarchy refresh
```

**Execution Flow:**
```
opr (OPContainer)._refresh()
├── _refresh_ops()           # Check OPs in root container
├── _refresh_extensions()    # Refresh root extensions (placeholder)
├── media._refresh()         # Recursive call to child container
│   ├── _refresh_ops()       # Check OPs in media container
│   ├── _refresh_extensions() # Refresh media extensions (placeholder)
│   ├── movie1._refresh()    # Recursive call to child leaf
│   │   └── _refresh_extensions() # Refresh movie1 extensions
│   └── movie2._refresh()    # Recursive call to child leaf
│       └── _refresh_extensions() # Refresh movie2 extensions
├── audio._refresh()         # Recursive call to sibling container
│   └── ... (similar flow)
└── _update_storage()        # Save entire hierarchy to storage
```

### Branch Refresh (New)
```python
opr.media._refresh()  # Refresh entire 'media' branch only
```

**Execution Flow:**
```
opr.media (OPContainer)._refresh()
├── _refresh_ops()           # Check OPs directly in media container
├── _refresh_extensions()    # Refresh media container extensions
├── media.movie1._refresh()  # Recursive call to child leaf
│   └── _refresh_extensions() # Refresh movie1 extensions
├── media.effects._refresh() # Recursive call to child container
│   ├── _refresh_ops()       # Check OPs in effects container
│   ├── _refresh_extensions() # Refresh effects extensions
│   ├── effects.blur._refresh() # Recursive call to grandchild leaf
│   │   └── _refresh_extensions() # Refresh blur extensions
│   └── effects.glow._refresh() # Recursive call to grandchild leaf
│       └── _refresh_extensions() # Refresh glow extensions
└── _update_storage()        # Find root and update storage
```

### Leaf Refresh (New)
```python
opr.media('movie1')._refresh()  # Refresh extensions on specific OP
```

**Execution Flow:**
```
opr.media('movie1') (OPLeaf)._refresh()
└── _refresh_extensions()    # Refresh extensions attached to movie1
                               # No recursion (leaves have no children)
                               # No storage update (leaf changes don't affect hierarchy)
```

### Specific Target from Root (Future Enhancement)
```python
opr._refresh('media')  # Refresh specific branch from root
```

**Execution Flow:**
```
opr (OPContainer)._refresh('media')
├── Find 'media' in _children
├── Delegate to: media._refresh()  # Same as opr.media._refresh()
└── No full hierarchy refresh
```

### OP Name Change Detection Example

**Scenario:** User renames `movie1` to `background_movie` in TouchDesigner

**Before Refresh:**
```python
opr.media._children = {'movie1': <OPLeaf>}
# Storage: {'movie1': {'op': <OP object>, 'path': '/project/movie1', ...}}
```

**During Refresh:**
```python
media._refresh_ops()
├── Load stored data for 'movie1'
├── stored_op.name = 'background_movie'  # OP was renamed!
├── stored_key ('movie1') != current_name ('background_movie')
├── Update mapping: del _children['movie1']
├── Add _children['background_movie'] = <OPLeaf>
└── Update OPLeaf._path to 'media.background_movie'
```

**After Refresh:**
```python
opr.media._children = {'background_movie': <OPLeaf>}
# API now works: opr.media('background_movie').name  # Returns correctly
```

### Error Handling Example

**Scenario:** One OP is missing, others work fine

```python
opr.media._refresh()
├── _refresh_ops()
│   ├── 'movie1' OP exists ✓ → update if renamed
│   ├── 'movie2' OP missing ✗ → log error, remove from container
│   └── 'movie3' OP exists ✓ → update if renamed
├── _refresh_extensions() ✓
├── movie1._refresh() ✓
├── movie2._refresh() ✓ (but OP was removed)
└── _update_storage() ✓
# Result: Partial success, missing OP logged but doesn't break refresh
```

## Files Requiring Changes

1. **`OPBaseWrapper.py`**
   - Update abstract `_refresh()` in `OPBaseWrapper`
   - Implement `_refresh()` in `OPContainer`
   - Implement `_refresh()` in `OPLeaf`
   - Add helper methods: `_refresh_ops()`, `_refresh_extensions()`, `_get_stored_container_data()`

2. **`utils.py`** (potentially)
   - May need storage navigation helpers

## Risk Assessment

### Low Risk
- Backward compatibility maintained (root refresh still works)
- Storage structure already supports new format
- Errors are logged, not thrown

### Medium Risk
- Recursive calls could cause stack overflow with extremely deep hierarchies
- Storage updates might be slow for large projects

### Mitigation Strategies
- Add recursion depth limits if needed
- Optimize storage updates (only update changed branches)
- Comprehensive testing before deployment

## Success Criteria

1. **Functionality**: `opr.media._refresh()` refreshes the media branch correctly
2. **Name Detection**: OP renames are detected and container mappings updated
3. **Recursion**: Deep hierarchies refresh correctly (depth-first)
4. **Error Handling**: Partial failures don't break entire refresh
5. **Storage**: Changes persist correctly across project reloads
6. **Performance**: No significant performance regression

## Implementation Order

1. **Phase 1.1**: Abstract `_refresh()` method
2. **Phase 1.4**: Helper methods (`_refresh_ops`, storage navigation)
3. **Phase 1.2**: `OPContainer._refresh()` implementation
4. **Phase 1.3**: `OPLeaf._refresh()` implementation
5. **Phase 2**: Error handling improvements
6. **Phase 3**: Testing and validation

## Future Enhancements

- Add `target` parameter support for selective refresh
- Implement extension refresh when `_extend()` is complete
- Add refresh performance profiling
- Consider breadth-first optimization for very wide trees

This refactor establishes the foundation for dynamic OP and extension management while maintaining the clean polymorphic architecture.
