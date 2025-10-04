# OProxy Logging System Refactor Plan

## Overview
Refactor the OProxy codebase from using `utils.log()` to the new `self.Log()` system provided by OPLogger. This will provide better logging capabilities including file output, status levels, process grouping, and improved console formatting.

## Current State
- **Total log calls:** 88 across 6 files
- **Current system:** `utils.log(message)` - simple print wrapper
- **New system:** `self.Log(msg, status='info', process=None, multi=True)` - advanced logging with file output, status levels, and process grouping

## Refactor Scope
- Replace all `utils.log()` calls with `self.Log()` calls
- Categorize each log appropriately with status and process
- Do not add new logging - only refactor existing calls
- Maintain existing debugging detail level

## Files to Refactor

### oproxy.py (6 calls)
```python
# Line 42: utils.log("OProxy root initialized")
self.Log("OProxy root initialized", status='info', process='Init')

# Line 61: utils.log(f"WARNING: Could not migrate invalid OP path '{op_info}' for '{op_name}'")
self.Log(f"Could not migrate invalid OP path '{op_info}' for '{op_name}'", status='warning', process='Migration')

# Line 74: utils.log("Checking for storage format migration...")
self.Log("Checking for storage format migration", status='debug', process='Migration')

# Line 92: utils.log("Migrating storage from old string format to new object format...")
self.Log("Migrating storage from old string format to new object format", status='info', process='Migration')

# Line 94: utils.log("Storage migration completed")
self.Log("Storage migration completed", status='info', process='Migration')

# Line 96: utils.log("Storage already in new format, no migration needed")
self.Log("Storage already in new format, no migration needed", status='debug', process='Migration')
```

### OPBaseWrapper.py (47 calls)
**Status Distribution:** debug: 41, info: 4, warning: 2

#### _remove operations (11 calls):
```python
# Line 81: Cannot remove leaf - no parent container
self.Log("Cannot remove leaf - no parent container", status='warning', process='_remove')

# Line 93: Removing leaf from parent container
self.Log(f"Removing leaf '{my_name}' from parent container", status='debug', process='_remove')

# Line 111: Could not find leaf in parent container children
self.Log("Could not find leaf in parent container children", status='warning', process='_remove')

# Line 178: Extension removal placeholder - not yet implemented
self.Log("Extension removal placeholder - not yet implemented", status='debug', process='_remove')

# Line 179: Future extension removal description
self.Log("Future: Will remove extension from parent and clean up storage", status='debug', process='_remove')

# Line 427: Removing self from parent
self.Log(f"Removing self ('{my_name}') from parent", status='debug', process='_remove')

# Line 435: Could not find self in parent children
self.Log("Could not find self in parent children", status='warning', process='_remove')

# Line 437: Cannot remove root container
self.Log("Cannot remove root container", status='warning', process='_remove')

# Line 450: Removing child from container
self.Log(f"Removing child '{name}' from container '{self.path or 'root'}'", status='debug', process='_remove')

# Line 458: Child not found in container
self.Log(f"Child '{name}' not found in container '{self.path or 'root'}'", status='warning', process='_remove')
```

#### _add_init operations (12 calls):
```python
# Line 257: Creating new container
self.Log(f"Creating new container '{name}'", status='debug', process='_add')

# Line 265: Single OP converted to list
self.Log(f"Single OP provided, converted to list: {op}", status='debug', process='_add')

# Line 268: List of OPs provided
self.Log(f"List of OPs provided, count: {len(op_list)}", status='debug', process='_add')

# Line 273: Validating OP
self.Log(f"Validating OP {i+1}/{len(op_list)}: {op_item}", status='debug', process='_add')

# Line 277: Validated OP
self.Log(f"Validated OP: {validated_op.name} (path: {validated_op.path})", status='debug', process='_add')

# Line 283: Creating container with path
self.Log(f"Creating container with path '{child_path}'", status='debug', process='_add')

# Line 287: Adding OPs as leaves
self.Log(f"Adding {len(validated_ops)} OPs as leaves to container '{name}'", status='debug', process='_add')

# Line 290: Creating leaf for OP
self.Log(f"Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'", status='debug', process='_add')

# Line 295: Adding container to parent children
self.Log(f"Adding container '{name}' to parent children dict", status='debug', process='_add')

# Line 298: Successfully created container (SUCCESS)
self.Log(f"Successfully created container '{name}' with {len(validated_ops)} OPs", status='info', process='_add')
```

#### _add_insert operations (11 calls):
```python
# Line 309: Adding to existing container
self.Log(f"Adding to existing container '{container.path or 'root'}'", status='debug', process='_add')

# Line 314: Single OP converted to list
self.Log(f"Single OP provided, converted to list: {op}", status='debug', process='_add')

# Line 317: List of OPs provided
self.Log(f"List of OPs provided, count: {len(op_list)}", status='debug', process='_add')

# Line 324: Validating OP
self.Log(f"Validating OP {i+1}/{len(op_list)}: {op_item}", status='debug', process='_add')

# Line 330: OP already exists - skipping
self.Log(f"OP '{validated_op.name}' already exists in container - skipping", status='warning', process='_add')

# Line 334: Validated OP
self.Log(f"Validated OP: {validated_op.name} (path: {validated_op.path})", status='debug', process='_add')

# Line 342: Adding new OPs to existing container
self.Log(f"Adding {added_count} new OPs to existing container '{container.path or 'root'}'", status='debug', process='_add')

# Line 345: Creating leaf for OP
self.Log(f"Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'", status='debug', process='_add')

# Line 349: Successfully added OPs (SUCCESS)
self.Log(f"Successfully added {added_count} OPs to container '{container.path or 'root'}'", status='info', process='_add')

# Line 356: No new OPs to add
self.Log(f"No new OPs to add to container '{container.path or 'root'}'", status='warning', process='_add')
```

#### _add operations (2 calls):
```python
# Line 391: Processing name in container
self.Log(f"Processing '{name}' in container '{self.path or 'root'}'", status='debug', process='_add')

# Line 397: Container already exists
self.Log(f"'{name}' OPContainer already exists - adding to existing container", status='info', process='_add')
```

#### Storage operations (2 calls):
```python
# Line 523: Saving container hierarchy
self.Log("Saving container hierarchy to storage", status='debug', process='_update_storage')

# Line 533: Saved containers to storage (SUCCESS)
self.Log(f"Saved {len(children_data)} top-level containers to storage", status='info', process='_update_storage')

# Line 552: Failed to update storage (ERROR)
self.Log(f"Failed to update storage: {e}", status='error', process='_update_storage')
```

#### Refresh operations (9 calls):
```python
# Line 123: Leaf refresh failed (ERROR)
self.Log(f"Leaf refresh failed for {self.path}: {e}", status='error', process='_refresh')

# Line 619: Container refresh failed (ERROR)
self.Log(f"Container refresh failed for {self.path}: {e}", status='error', process='_refresh')

# Line 711: Loading nested container
self.Log(f"Loading nested container '{container_name}' under '{parent_path}'", status='debug', process='_refresh')

# Line 730: Loading nested OP
self.Log(f"Loading nested OP '{op_name}' from '{op_path}'", status='debug', process='_refresh')

# Line 738: Using stored OP object
self.Log(f"Using stored OP object for nested '{op_name}' (original path may have changed)", status='debug', process='_refresh')

# Line 744: OP name changed
self.Log(f"Nested OP name changed from '{op_name}' to '{current_name}', updating mapping", status='info', process='_refresh')

# Line 763: OP not found warning
self.Log(f"Nested OP '{op_path}' not found or invalid, skipping", status='warning', process='_refresh')
```

### proxy_methods.py (24 calls)
**Status Distribution:** info: 7, warning: 11, debug: 6

#### Remove operations (16 calls):
```python
# Line 82: Removed OP from parent container
self.Log(f"Removed OP '{op_name}' from parent container", status='info', process='_remove')

# Line 89: Removed branch from storage
self.Log(f"Removed entire branch '{self._dictPath}' from storage", status='info', process='_remove')

# Line 107: OP not found in parent container
self.Log(f"OP '{op_name}' not found in parent container", status='warning', process='_remove')

# Line 109: Parent container not found
self.Log(f"Parent container not found for path '{parent_path}'", status='warning', process='_remove')

# Line 123: Removed root OP
self.Log(f"Removed root OP '{op_name}'", status='info', process='_remove')

# Line 128: Root OP not found
self.Log(f"Root OP '{op_name}' not found", status='warning', process='_remove')

# Line 143: Removed child proxy
self.Log(f"Removed child proxy '{child_name}'", status='info', process='_remove')

# Line 145: Error removing child proxy
self.Log(f"Error removing child proxy '{child_name}': {e}", status='warning', process='_remove')

# Line 150: Removed child from storage (fallback)
self.Log(f"Removed child '{child_name}' directly from storage (fallback)", status='info', process='_remove')

# Line 152: Error removing child from storage
self.Log(f"Error removing child '{child_name}' from storage: {e2}", status='warning', process='_remove')

# Line 158: Removed child from storage
self.Log(f"Removed child '{child_name}' directly from storage", status='info', process='_remove')

# Line 160: Error removing child from storage
self.Log(f"Error removing child '{child_name}' from storage: {e}", status='warning', process='_remove')

# Line 180: Removed root container
self.Log(f"Removed root container '{name}' from storage", status='info', process='_remove')

# Line 203: Invalid OP in remove list
self.Log(f"Invalid OP in remove list: {e}", status='warning', process='_remove')
```

#### Cleanup operations (5 calls):
```python
# Line 98: Cleaned up extensions
self.Log(f"Cleaned up {ext_count} orphaned extension(s) from '{self._dictPath}'", status='info', process='Cleanup')

# Line 101: No extensions found
self.Log(f"No extensions found at '{self._dictPath}' during cleanup", status='debug', process='Cleanup')

# Line 103: No node or extensions found
self.Log(f"No node or Extensions found at '{self._dictPath}' during cleanup", status='debug', process='Cleanup')

# Line 105: Error during extension cleanup
self.Log(f"Error during extension cleanup for '{self._dictPath}': {e}", status='warning', process='Cleanup')

# Line 126: Cleaned up extensions from root OP
self.Log(f"Cleaned up {ext_count} extension(s) from root OP '{op_name}'", status='info', process='Cleanup')
```

#### Proxy operations (3 calls):
```python
# Line 222: OP not found in proxy
self.Log(f"OP not found in proxy: {item_desc}", status='warning', process='Proxy')

# Line 240: No storage node found
self.Log(f"No storage node found for path '{dict_path}'", status='warning', process='_refresh')

# Line 244: Storage node missing OPs key
self.Log(f"Storage node missing 'OPs' key for path '{dict_path}', initializing", status='warning', process='_refresh')
```

#### Refresh operations (3 calls):
```python
# Line 261: No changes found
self.Log("No changes found", status='debug', process='_refresh')

# Line 268: OP not found
self.Log(f"{op_name} is not found, if moved use Update() to update path", status='warning', process='_refresh')

# Line 293: OP name changed
self.Log(f"OP {op.path}: name changed from '{old_key}' -> '{new_key}'", status='info', process='_refresh')
```

### mod_AST.py (1 call)
```python
# Line 133: Error executing block
self.Log(f"Error executing block for '{target_name}' from {op.path}: {str(e)} at line {e.lineno if hasattr(e, 'lineno') else 'unknown'}", status='error', process='Execute')
```

### OP_Proxy.py (2 calls)
```python
# Line 107: Non-persistent extension warning
self.Log(f"Non-persistent extension '{attr_name}' added to {self._dictPath}; won't survive project reload or extension re-init", status='warning', process='_extend')

# Line 110: Extension added successfully
self.Log(f"Extension '{attr_name}' added successfully", status='info', process='_extend')
```

## Implementation Considerations

### Logger Access
- Classes inheriting from `oproxyExt` have direct access to `self.Log()`
- Classes not inheriting from `oproxyExt` may need logger instance passed or accessed differently
- Consider whether to modify class hierarchies or pass logger instances

### Process Categories Used
- **Init**: System initialization
- **Migration**: Storage format migration
- **_remove**: Object removal operations (_remove method calls)
- **_add**: Object addition operations (_add method calls)
- **_update_storage**: Storage save/update operations (_update_storage method calls)
- **_refresh**: Container/OP refresh operations (_refresh method calls)
- **Cleanup**: Extension cleanup operations
- **Proxy**: Proxy-specific operations
- **Execute**: Module execution errors
- **_extend**: Extension operations (_extend method calls)

### Status Level Distribution
- **debug**: 47 calls (internal operation details)
- **info**: 23 calls (successful operations, state changes)
- **warning**: 16 calls (non-critical issues, skips)
- **error**: 2 calls (actual failures/exceptions)

## Benefits of Refactor
- **File Logging**: Logs can be written to files when configured
- **Status Levels**: Better categorization of log severity
- **Process Grouping**: Related operations grouped for better readability
- **Improved Console Output**: Formatted prefixes with component names
- **Configurable**: Can be enabled/disabled per component

## Migration Steps
1. Ensure all classes have access to `self.Log()` instance
2. Replace `utils.log()` calls one file at a time
3. Test each file to ensure logging still works correctly
4. Verify log file output if configured
5. Remove or deprecate `utils.log()` function

## Testing
- Verify console output format is correct
- Test file logging functionality if enabled
- Ensure log grouping works properly for multi-message sequences
- Confirm status levels are appropriate for each message type
