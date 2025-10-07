# OProxyExtension._refresh() Implementation Plan

## Overview

Implement `_refresh()` method for `OProxyExtension` class to enable extension-specific refresh capabilities, following the same polymorphic architecture as `OPContainer._refresh()` and `OPLeaf._refresh()`. This allows individual extensions to refresh their state, re-extract their underlying objects from source DATs, and handle any attached sub-extensions.

## Current State Analysis

### Problems with Current Implementation
- `OProxyExtension._refresh()` raises `NotImplementedError`
- Extensions cannot refresh themselves when their source DATs change
- No mechanism to update extension state after DAT modifications
- Extensions may become stale if underlying objects change
- Cannot detect or handle DAT path/name changes for extensions

### Recent Context
- `OPContainer._refresh()` and `OPLeaf._refresh()` implemented with polymorphic design
- Storage system includes extension metadata for reload capability
- Extensions are stored with source DAT paths and raw DAT objects
- Re-extraction logic exists in `_refresh_extensions()` methods

## Design Decisions

### 1. Extension Refresh Logic
**Each extension refreshes its own state and sub-extensions:**

- Check if source DAT is still valid and accessible
- Re-extract underlying object from DAT if needed
- Update internal state to match current DAT content
- Refresh any attached sub-extensions (if supported in future)
- Update storage if changes detected

### 2. DAT Change Detection
**Handle DAT path and name changes similar to OP refresh:**

- Store original DAT path and raw DAT object
- Attempt to locate DAT by stored path first
- Fall back to stored DAT object if path lookup fails
- Update metadata if DAT path has changed
- Log changes for debugging

### 3. State Consistency
**Ensure extension remains synchronized with DAT:**

- Re-extract object using same `mod_ast.Main()` parameters
- Preserve extension metadata and configuration
- Maintain extension name and parent references
- Update storage after successful refresh

## Implementation Plan

### Phase 1: Core Implementation

#### 1.1 Replace NotImplementedError
**File:** `OPBaseWrapper.py` (in `OProxyExtension` class)
**Changes:**
- Remove `raise NotImplementedError`
- Implement actual refresh logic

```python
def _refresh(self, target=None):
    """Refresh extension state and re-extract from source DAT"""
    try:
        # Check source DAT validity and re-extract if needed
        self._refresh_source_dat()
        # Refresh any sub-extensions (future-proofing)
        self._refresh_extensions(target)
    except Exception as e:
        Log(f"Extension refresh failed for {self._extension_name}: {e}\n{traceback.format_exc()}", status='error', process='_refresh')
```

#### 1.2 Add `_refresh_source_dat()` Method
**Logic:**
- Access stored metadata (source_dat path and dat_op)
- Try to get DAT by current path
- Fall back to stored DAT object
- If DAT found and valid, re-extract underlying object
- Update extension's internal object reference
- Update metadata if path changed

```python
def _refresh_source_dat(self):
    """Check and refresh the source DAT connection"""
    if not hasattr(self, '_source_dat') or not hasattr(self, '_metadata'):
        return  # No source DAT to refresh

    metadata = self._metadata
    stored_path = metadata.get('dat_path')
    stored_dat = metadata.get('dat_op')

    # Try current path first
    dat = td.op(stored_path) if stored_path else None

    # Fall back to stored DAT object
    if not (dat and dat.valid) and stored_dat and stored_dat.valid:
        dat = stored_dat
        Log(f"Using stored DAT object for extension '{self._extension_name}' (path may have changed)", status='debug', process='_refresh')

    if dat and dat.valid:
        # Check for path changes
        if stored_path != dat.path:
            Log(f"Extension '{self._extension_name}' source DAT path changed from '{stored_path}' to '{dat.path}'", status='info', process='_refresh')
            metadata['dat_path'] = dat.path
            metadata['dat_op'] = dat
            changed = True
        else:
            changed = False

        # Re-extract the underlying object
        mod_ast = mod('mod_AST')
        actual_obj = mod_ast.Main(
            cls=metadata['cls'],
            func=metadata['func'],
            op=dat,
            log=Log
        )

        # Update the extension's internal object
        self._actual = actual_obj

        # Update storage if path changed
        if changed and self._parent:
            self._find_root()._update_storage()

    else:
        Log(f"Source DAT for extension '{self._extension_name}' not found or invalid", status='warning', process='_refresh')
```

#### 1.3 Add `_refresh_extensions()` Method (Future-Proofing)
**Logic:**
- Placeholder for refreshing sub-extensions
- Currently empty since extensions don't support sub-extensions
- Allows future expansion if needed

```python
def _refresh_extensions(self, target=None):
    """Refresh any attached sub-extensions (currently none)"""
    # Placeholder for future sub-extension support
    # Extensions currently cannot have extensions attached
    pass
```

## Integration with Existing Refresh Flow

### Extension Refresh in Parent Context
When parent containers/leaves call `_refresh_extensions()`, they already handle extension reloading. The extension's own `_refresh()` provides additional capability for:

1. **Direct Extension Refresh:** `extension._refresh()` called directly on an extension
2. **Recursive Extension Updates:** Parent refresh flows can call extension refresh
3. **Extension State Validation:** Extensions can validate their own source DATs

### Storage Update Integration
- Extensions update root storage when DAT paths change
- Uses existing `_find_root()._update_storage()` mechanism
- Maintains consistency with container/leaf refresh patterns

## Error Handling & Validation

### Graceful Degradation
- Log errors but don't halt parent refresh operations
- Invalid DATs are reported as warnings
- Extensions remain functional even if refresh fails partially

### Validation Checks
- Verify source DAT exists and is valid
- Confirm metadata contains required fields
- Ensure parent reference is maintained

## Success Criteria

1. **Functionality**: `extension._refresh()` successfully re-extracts from source DAT
2. **Change Detection**: Detects and handles DAT path/name changes
3. **State Consistency**: Extension object stays synchronized with DAT content
4. **Error Resilience**: Failed refresh doesn't break parent operations
5. **Storage Updates**: Changes trigger appropriate storage updates

## Implementation Order

1. **Implement `_refresh_source_dat()`** - Core DAT validation and re-extraction
2. **Update `_refresh()` method** - Main refresh orchestration
3. **Add `_refresh_extensions()` placeholder** - Future-proofing
4. **Integration testing** - Verify with parent refresh flows
5. **Edge case testing** - DAT deletion, path changes, invalid objects

This implementation completes the polymorphic refresh architecture by enabling extensions to maintain their own state consistency, following the same patterns established for containers and leaves.
