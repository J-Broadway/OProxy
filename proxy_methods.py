# proxy_methods.dat
import td

log 			        = mod('utils').log
OP_Proxy		        = mod('OP_Proxy').OP_Proxy
_update_storage         = mod('utils')._update_storage
hierarchical_storage    = mod('hierarchical_storage')
td_isinstance           = mod('utils').td_isinstance  # Import centralized TD type checking

# Define the Add method for dynamic classes (updated to wrap new OPs)
def proxy_add(self, new_op):
    if isinstance(new_op, td.OP):
        # Use td_isinstance for validation
        try:
            new_op = td_isinstance(new_op, 'op', allow_string=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Provided 'new_op' is not a valid OP: {e}")
        new_op = [new_op]  # Normalize to list
    elif isinstance(new_op, list):
        if not new_op:
            raise ValueError("Provided 'new_op' list cannot be empty")
        validated_ops = []
        for item in new_op:
            try:
                validated_item = td_isinstance(item, 'op', allow_string=True)
                validated_ops.append(validated_item)
            except (TypeError, ValueError) as e:
                raise TypeError(f"All elements in 'new_op' must be valid OPs, but found {type(item).__name__}: {e}")
        new_op = validated_ops
    else:
        raise TypeError(f"Expected 'new_op' to be a valid OP or list of valid OPs, but got {type(new_op).__name__}")
    
    # Deduplicate against current list
    current_ops = {w.op for w in self}
    to_add = []
    for op in new_op:
        if op not in current_ops:
            to_add.append(op)
    
    if not to_add:
        return self  # Nothing to add
    
    # Append wrapped to the list and update lookup
    for op in to_add:
        wrapped = OP_Proxy(op)
        self.append(wrapped)
        self._by_name_or_path[op.name] = wrapped
        self._by_name_or_path[op.path] = wrapped
    
    # Persist
    _update_storage(self)
    
    return self  # Allow chaining

# Define the Remove method for dynamic classes (updated for wrapped)
def proxy_remove(self, to_remove=None):
    if to_remove is None:  # Remove self (container) and children recursively
        # Check if this is a single OP hybrid container (created via __call__)
        if hasattr(self, '_opr') and hasattr(self, '_dictPath') and len(self) == 1:
            # This is a single OP hybrid container - remove the specific OP from its parent
            # Access the wrapped OP directly from the list to avoid __getitem__ recursion
            wrapped_op = list.__getitem__(self, 0)
            op_to_remove = wrapped_op.op
            parent_path, op_name = self._dictPath.rsplit('.', 1) if '.' in self._dictPath else (None, self._dictPath)
            
            if parent_path:
                # Get the parent container instance
                parent_container = self._opr.get_proxy_by_path(parent_path)
                if parent_container:
                    # Remove from parent's actual list and lookup
                    wrapped_to_remove = None
                    for wrapped in parent_container:
                        if wrapped.op == op_to_remove:
                            wrapped_to_remove = wrapped
                            break
                    
                    if wrapped_to_remove:
                        parent_container.remove(wrapped_to_remove)
                        # Clean up lookup
                        parent_container._by_name_or_path.pop(op_to_remove.name, None)
                        parent_container._by_name_or_path.pop(op_to_remove.path, None)
                        log(f"Removed OP '{op_name}' from parent container")
                        
                        # Update storage
                        _update_storage(parent_container)
                        
                        # Remove the entire branch from storage including extensions
                        hierarchical_storage.remove_node(self._opr.OProxies, self._dictPath, recursive=True)
                        log(f"Removed entire branch '{self._dictPath}' from storage")
                        
                        # Additional cleanup: explicitly remove any remaining extension data
                        # This ensures complete cleanup of hybrid container data
                        try:
                            node = hierarchical_storage.get_node(self._opr.OProxies, self._dictPath)
                            if node and 'Extensions' in node:
                                ext_count = len(node['Extensions'])
                                if ext_count > 0:
                                    log(f"Cleaned up {ext_count} orphaned extension(s) from '{self._dictPath}'")
                                    del node['Extensions']
                                else:
                                    log(f"No extensions found at '{self._dictPath}' during cleanup")
                            else:
                                log(f"No node or Extensions found at '{self._dictPath}' during cleanup")
                        except Exception as e:
                            log(f"Error during extension cleanup for '{self._dictPath}': {e}", level='warning')
                    else:
                        log(f"OP '{op_name}' not found in parent container", level='warning')
                else:
                    log(f"Parent container not found for path '{parent_path}'", level='warning')
            else:
                # Root level removal
                oproxies_raw = self._opr.OProxies.getRaw()
                if op_name in oproxies_raw:
                    # Check for extensions before removal
                    node = oproxies_raw[op_name]
                    ext_count = len(node.get('Extensions', []))
                    
                    del oproxies_raw[op_name]
                    # Update storage after deletion
                    if hasattr(self._opr, 'ownerComp') and hasattr(self._opr.ownerComp, 'store'):
                        self._opr.ownerComp.store['OProxies'] = oproxies_raw
                    self._opr.OProxies = oproxies_raw
                    log(f"Removed root OP '{op_name}'")
                    
                    if ext_count > 0:
                        log(f"Cleaned up {ext_count} extension(s) from root OP '{op_name}'")
                else:
                    log(f"Root OP '{op_name}' not found", level='warning')
            
            return self  # Return self for chaining
        
        # Regular container removal - recurse to remove children first
        node = hierarchical_storage.get_node(self._opr.OProxies, self._dictPath)
        if 'Children' in node and node['Children']:
            # Get a copy of children names to avoid modification during iteration
            child_names = list(node['Children'].keys())
            for child_name in child_names:
                # Try to get the child proxy, but don't fail if it doesn't exist
                child_proxy = getattr(self, child_name, None)
                if child_proxy and hasattr(child_proxy, '_remove'):
                    try:
                        child_proxy._remove()  # Recursive call
                        log(f"Removed child proxy '{child_name}'")
                    except Exception as e:
                        log(f"Error removing child proxy '{child_name}': {e}", level='warning')
                        # Fall back to direct storage removal
                        child_path = f"{self._dictPath}.{child_name}" if self._dictPath else child_name
                        try:
                            hierarchical_storage.remove_node(self._opr.OProxies, child_path, recursive=True)
                            log(f"Removed child '{child_name}' directly from storage (fallback)")
                        except Exception as e2:
                            log(f"Error removing child '{child_name}' from storage: {e2}", level='warning')
                else:
                    # Child proxy doesn't exist as attribute, remove directly from storage
                    child_path = f"{self._dictPath}.{child_name}" if self._dictPath else child_name
                    try:
                        hierarchical_storage.remove_node(self._opr.OProxies, child_path, recursive=True)
                        log(f"Removed child '{child_name}' directly from storage")
                    except Exception as e:
                        log(f"Error removing child '{child_name}' from storage: {e}", level='warning')
        
        # Remove self from parent
        if hasattr(self, '_opr') and hasattr(self, '_dictPath'):
            parent_path, name = self._dictPath.rsplit('.', 1) if '.' in self._dictPath else (None, self._dictPath)
            if parent_path:
                # Nested container - remove from parent's Children
                parent_proxy = hierarchical_storage.get_node(self._opr.OProxies, parent_path)
                if name in parent_proxy['Children']:
                    del parent_proxy['Children'][name]
                hierarchical_storage.remove_node(self._opr.OProxies, self._dictPath)
            else:
                # Root-level container - remove directly from OProxies
                oproxies_raw = self._opr.OProxies.getRaw()
                if name in oproxies_raw:
                    del oproxies_raw[name]
                    # Update storage after deletion
                    if hasattr(self._opr, 'ownerComp') and hasattr(self._opr.ownerComp, 'store'):
                        self._opr.ownerComp.store['OProxies'] = oproxies_raw
                    self._opr.OProxies = oproxies_raw
                    log(f"Removed root container '{name}' from storage")
        
        # Clean up attribute from parent
        if hasattr(self, '_parent'):  # Assume _parent back-ref added if needed
            delattr(self._parent, self._proxy_name)
        
        return self  # Or None if destroyed
    
    else:
        if isinstance(to_remove, (td.OP, str)):
            to_remove = [to_remove]  # Normalize to list
        elif not isinstance(to_remove, list):
            raise TypeError(f"Expected 'to_remove' to be an OP, str (name/path), or list thereof, but got {type(to_remove).__name__}")
        
        removed = False
        for item in to_remove:
            # Find the wrapped OP to remove (by object, name, or path)
            wrapped_to_remove = None
            if isinstance(item, td.OP):
                # Use td_isinstance for validation
                try:
                    item = td_isinstance(item, 'op', allow_string=False)
                except (TypeError, ValueError) as e:
                    log(f"Invalid OP in remove list: {e}", level='warning')
                    continue
                for wrapped in self:
                    if wrapped.op == item:
                        wrapped_to_remove = wrapped
                        break
                item_desc = item.path if item else str(item)
            else:  # str
                wrapped_to_remove = self._by_name_or_path.get(item)
                item_desc = item
            
            if wrapped_to_remove:
                self.remove(wrapped_to_remove)  # Remove from list
                # Clean up dict
                op = wrapped_to_remove.op
                self._by_name_or_path.pop(op.name, None)
                self._by_name_or_path.pop(op.path, None)
                removed = True
            else:
                log(f"OP not found in proxy: {item_desc}")
        
        if removed:
            # Persist only if something was removed
            _update_storage(self)
        
        return self  # Allow chaining

# Define the Refresh method for dynamic classes
def proxy_refresh(self):
    if not hasattr(self, '_opr') or not hasattr(self, '_dictPath'):
        return self  # No-op if no back-ref
    
    dict_path = self._dictPath
    node = hierarchical_storage.get_node(self._opr.OProxies, dict_path)
    
    # Ensure the node has the required structure
    if not node:
        log(f"No storage node found for path '{dict_path}'", level='warning', process='proxy_refresh')
        return self
    
    if 'OPs' not in node:
        log(f"Storage node missing 'OPs' key for path '{dict_path}', initializing", level='warning', process='proxy_refresh')
        node['OPs'] = {}
    
    mapping = node['OPs']
    changes = []  # Collect changes: ('remove', key, op) or ('update', old_key, new_key, op)
    refreshed_ops = []  # For printing dynamic statements on updates
    
    for key, data in list(mapping.items()):  # Use list to avoid runtime modification issues
        op = data.get('op')
        if op is None or not op.valid:
            changes.append(('remove', key, op))
            continue
        current_name = op.name
        if current_name != key:
            changes.append(('update', key, current_name, op))
    
    if not changes:
        log("No changes found")
    else:
        # Apply changes
        for change in changes:
            if change[0] == 'remove':
                key, op = change[1], change[2]
                op_name = op.name if op else key
                log(f"{op_name} is not found, if moved use Update() to update path")
                # Do not auto-delete; keep in mapping for potential recovery
            elif change[0] == 'update':
                old_key, new_key, op = change[1:]
                # Find wrapper for this OP
                wrapper = next((w for w in self if w.op == op), None)
                if wrapper:
                    # Keep old key as alias for backward compatibility
                    self._by_name_or_path[old_key] = wrapper
                    # Add new key
                    self._by_name_or_path[new_key] = wrapper
                # Update mapping: move to new key, handle conflict
                resolved_new_key = new_key
                if new_key in mapping:
                    i = 1
                    while f"{new_key}_{i}" in mapping:
                        i += 1
                    resolved_new_key = f"{new_key}_{i}"
                mapping[resolved_new_key] = {'op': op}
                del mapping[old_key]
                # Append for printing
                refreshed_ops.append((op, old_key, resolved_new_key))
        
        # Print dynamic statements for refreshed OPs
        for op, old_key, new_key in refreshed_ops:
            log(f"OP {op.path}: name changed from '{old_key}' -> '{new_key}'", process='Refresh')
    
    
    # Recurse to children
    if 'Children' in node:
        for child_name in list(node['Children']):
            child_proxy = getattr(self, child_name, None)
            if child_proxy:
                child_proxy._refresh()  # Changed to _refresh for consistency with class_dict
    
    return self  # Allow chaining