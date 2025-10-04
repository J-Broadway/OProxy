# Storage Architecture Refactor for _extend() Support

## Overview

The current OProxy storage architecture stores OPs as simple string paths, but the `_extend()` feature requires storing extensions on both containers and individual OPs. This refactor changes the storage structure to support nested objects while maintaining all existing functionality.

## Current vs New Storage Structure

### Current Structure (Flat OP Storage)
```python
{
    'children': {
        'container_name': {
            'children': {...},        # Nested containers
            'ops': {                  # ❌ Simple string paths only
                'op1': '/project1/op1',
                'op2': '/project1/op2'
            },
            'extensions': {}          # Container extensions only
        }
    }
}
```

### New Structure (Nested OP Objects)
```python
{
    'children': {
        'container_name': {
            'children': {...},        # Nested containers
            'ops': {                  # ✅ Objects with path + extensions
                'op1': {
                    'path': '/project1/op1',
                    'op': <OP object>,    # Raw OP object for name change detection
                    'extensions': {
                        'custom_method': {
                            'cls': None,
                            'func': 'my_func',
                            'dat_path': '/project1/my_dat',
                            'call': False,
                            'args': None,
                            'monkey_patch': False
                        }
                    }
                },
                'op2': {
                    'path': '/project1/op2',
                    'op': <OP object>,    # Raw OP object for name change detection
                    'extensions': {}      # Empty extensions dict
                }
            },
            'extensions': {           # Container extensions
                'container_method': {
                    'cls': 'MyClass',
                    'func': None,
                    'dat_path': '/project1/my_dat',
                    'call': False,
                    'args': None,
                    'monkey_patch': False
                }
            }
        }
    }
}
```

## Key Changes

### 1. OP Storage Structure
- **Before**: `'ops': {'op_name': 'op_path'}`
- **After**: `'ops': {'op_name': {'path': 'op_path', 'op': <OP object>, 'extensions': {...}}}`

### 2. Extension Storage Levels
- **Container Level**: `container['extensions']` - applies to OPContainer
- **Leaf Level**: `container['ops']['op_name']['extensions']` - applies to individual OPLeaf

### 3. Name Change Detection
- **Raw OP Storage**: Store raw OP objects to enable `stored_key != stored_op.name` comparison
- **Automatic Updates**: OP objects automatically reflect path/name changes when TouchDesigner renames OPs
- **Container Updates**: During `_refresh()`, detect name changes and update container mappings accordingly

### 4. Backward Compatibility
- Since you're the only developer, we can break existing storage format
- Clean migration: clear existing storage and rebuild with new structure

## Implementation Plan

### Phase 1: Core Storage Structure Changes

#### 1.1 Update `OPBaseWrapper.__build_storage_structure()`
**File**: `OPBaseWrapper.py`  
**Location**: Lines ~417-437  
**Current Code**:
```python
# Add OPs from this container
for op_name, op_child in child._children.items():
    if hasattr(op_child, '_op'):  # It's an OPLeaf
        container_data['ops'][op_name] = op_child._op.path
```

**New Code**:
```python
# Add OPs from this container
for op_name, op_child in child._children.items():
    if hasattr(op_child, '_op'):  # It's an OPLeaf
        # Create OP object with path, raw OP, and extensions
        op_data = {
            'path': op_child._op.path,
            'op': op_child._op,  # Store raw OP object for name change detection
            'extensions': getattr(op_child, '_extensions', {})  # Will be added by _extend()
        }
        container_data['ops'][op_name] = op_data
```

#### 1.2 Update `OPBaseWrapper._refresh()`
**File**: `OPBaseWrapper.py`  
**Location**: Lines ~459-470  
**Current Code**:
```python
# Load OPs into the container
ops_data = container_data.get('ops', {})
for op_name, op_path in ops_data.items():
    utils.log(f"DEBUG _refresh: Loading OP '{op_name}' from '{op_path}'")
    op = td.op(op_path)
    if op and op.valid:
        leaf_path = f"{container_path}.{op_name}"
        leaf = OPLeaf(op, path=leaf_path, parent=container)
        container._children[op_name] = leaf
```

**New Code**:
```python
# Load OPs into the container
ops_data = container_data.get('ops', {})
for op_name, op_info in ops_data.items():
    if isinstance(op_info, str):
        # Legacy format support (simple path string)
        op_path = op_info
        stored_op = None
        op_extensions = {}
    else:
        # New format (object with path, raw OP, and extensions)
        op_path = op_info.get('path', '')
        stored_op = op_info.get('op')  # Raw OP object for name change detection
        op_extensions = op_info.get('extensions', {})

    utils.log(f"DEBUG _refresh: Loading OP '{op_name}' from '{op_path}'")

    # Try to get OP by stored path first
    op = td.op(op_path) if op_path else None

    # If that fails but we have a stored OP object, use it (handles renames)
    if not (op and op.valid) and stored_op and stored_op.valid:
        op = stored_op
        utils.log(f"DEBUG _refresh: Using stored OP object for '{op_name}' (original path may have changed)")

    if op and op.valid:
        # Check for name changes
        current_name = op.name
        if op_name != current_name:
            utils.log(f"DEBUG _refresh: OP name changed from '{op_name}' to '{current_name}', updating mapping")
            # Use current name as key instead of stored name
            actual_key = current_name
        else:
            actual_key = op_name

        leaf_path = f"{container_path}.{actual_key}"
        leaf = OPLeaf(op, path=leaf_path, parent=container)

        # Load extensions onto the leaf
        if op_extensions:
            leaf._extensions = op_extensions
            # Re-apply extensions (will be implemented in _extend)
            for ext_name, ext_data in op_extensions.items():
                # TODO: Apply extension logic here
                pass

        container._children[actual_key] = leaf
    else:
        utils.log(f"DEBUG _refresh: Warning - OP '{op_path}' not found or invalid, skipping")
```

#### 1.3 Update `utils.store()`
**File**: `utils.py`  
**Location**: Lines ~25-36  
**Current Code**:
```python
# Process all children
for name, child in container._children.items():
    if hasattr(child, '_op'):  # This is an OPLeaf
        # Store OP path directly
        container_data['ops'][name] = child._op.path
```

**New Code**:
```python
# Process all children
for name, child in container._children.items():
    if hasattr(child, '_op'):  # This is an OPLeaf
        # Store OP as object with path, raw OP, and extensions
        op_data = {
            'path': child._op.path,
            'op': child._op,  # Store raw OP object for name change detection
            'extensions': getattr(child, '_extensions', {})
        }
        container_data['ops'][name] = op_data
```

#### 1.4 Update `utils.remove()`
**File**: `utils.py`  
**Location**: Need to handle new nested structure  
**Impact**: Ensure removal logic works with nested OP objects

### Phase 2: Extension Support Infrastructure

#### 2.1 Add Extension Storage to OP Classes
**File**: `OPBaseWrapper.py`  
**Changes**:
- Add `_extensions` attribute to `OPContainer` and `OPLeaf`
- Initialize as empty dict in `__init__`

#### 2.2 Update Container Extension Storage
**File**: `OPBaseWrapper.__build_storage_structure()`  
**Current**: `'extensions': {}`  
**Ensure**: Container extensions are properly stored

### Phase 3: Migration Strategy

#### 3.1 Storage Migration Function
Create a migration function that:
1. Detects old format storage
2. Converts to new format
3. Clears and rebuilds storage

#### 3.2 Migration Trigger
Call migration during root initialization if old format detected

### Phase 4: Testing & Validation

#### 4.1 Storage Structure Tests
- Verify new nested structure is created correctly
- Test extension storage on containers
- Test extension storage on leaves

#### 4.2 Persistence Tests
- Test storage survives project reload
- Test extension reloading during `_refresh()`

#### 4.3 Backward Compatibility Tests
- Test migration from old to new format
- Update `expected` variables in `oproxy_tests.py` to match new storage structure
- Ensure existing tests still pass

## Implementation Checklist

### Core Storage Changes
- [ ] Update `OPBaseWrapper.__build_storage_structure()` for nested OP objects
- [ ] Update `OPBaseWrapper._refresh()` to handle new OP structure and load extensions
- [ ] Update `utils.store()` to create nested OP objects
- [ ] Update `utils.remove()` to handle nested OP objects

### Extension Infrastructure
- [ ] Add `_extensions` attribute to `OPContainer` and `OPLeaf`
- [ ] Ensure container extensions are properly stored/loaded
- [ ] Implement extension re-application during `_refresh()`

### Testing
- [ ] Update `expected` variables in `oproxy_tests.py` to match new OP object structure
- [ ] Update existing tests to work with new storage
- [ ] Add tests for name change detection during `_refresh()`
- [ ] Add tests for extension storage/loading
- [ ] Add tests for nested OP object structure
- [ ] Verify persistence across project reloads

## Files Requiring Changes

1. **`OPBaseWrapper.py`**
   - `__build_storage_structure()` - Change OP storage to objects
   - `_refresh()` - Handle new OP structure and extension loading
   - Add `_extensions` attribute to classes

2. **`utils.py`**
   - `store()` - Update OP storage to objects
   - `remove()` - Handle nested OP objects

3. **`oproxy.py`** (potentially)
   - Add migration logic to root initialization

4. **`dev/tests/oproxy_tests.py`**
   - Update tests to work with new storage structure

## Risk Assessment

### Low Risk Changes
- Storage structure changes are internal and don't affect public API
- Existing functionality remains intact
- Migration can be tested thoroughly before deployment

### Medium Risk Changes
- Extension loading during `_refresh()` needs careful implementation
- Migration logic must handle all edge cases

### Mitigation Strategies
- Implement incrementally with thorough testing at each step
- Keep existing functionality working during transition
- Add comprehensive logging for debugging

## Success Criteria

1. **Storage Structure**: New nested format correctly stores OPs and extensions
2. **Persistence**: Extensions survive project reload via TouchDesigner storage
3. **Loading**: Extensions are properly re-applied during `_refresh()`
4. **Compatibility**: All existing tests pass with new storage
5. **Migration**: Clean transition from old to new storage format

## Next Steps

1. **Update Storage Structure**: Implement the new OP object format with 'path', 'op', and 'extensions' fields
2. **Implement Name Change Detection**: Add logic in `_refresh()` to detect when `stored_key != stored_op.name` and update container mappings
3. **Update Tests**: Modify `expected` variables in `oproxy_tests.py` to match the new storage structure with OP objects
4. **Test Storage Persistence**: Verify OP objects survive project reloads and enable name change detection
5. **Implement Migration**: Handle transition from old string-based format to new object format
6. **Add Extension Infrastructure**: Implement `_extensions` attribute and extension re-application during refresh

This refactor establishes the foundation for `_extend()` functionality while maintaining all existing OProxy capabilities.
