# proxy_methods.dat
import td

log 			        = mod('utils').log
OP_Proxy		        = mod('OP_Proxy').OP_Proxy
_update_storage         = mod('utils')._update_storage
hierarchical_storage    = mod('hierarchical_storage')

# Define the Add method for dynamic classes (updated to wrap new OPs)
def proxy_add(self, new_op):
    if isinstance(new_op, td.OP):
        if not new_op.valid:
            raise ValueError("Provided 'new_op' is not a valid OP (new_op.valid == False)")
        new_op = [new_op]  # Normalize to list
    elif isinstance(new_op, list):
        if not new_op:
            raise ValueError("Provided 'new_op' list cannot be empty")
        for item in new_op:
            if not isinstance(item, td.OP):
                raise TypeError(f"All elements in 'new_op' must be OPs, but found {type(item).__name__}")
            if not item.valid:
                raise ValueError("All elements in 'new_op' must be valid OPs (item.valid == True)")
    else:
        raise TypeError(f"Expected 'new_op' to be a valid OP or list of valid OPs, but got {type(new_op).__name__}")
    
    # Deduplicate against current list
    current_ops = {w.op for w in self}
    to_add = []
    for op in new_op:
        if op in current_ops:
            log(f"OP already in proxy, skipping: {op.path}")
        else:
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
        # Recurse to remove children first
        node = hierarchical_storage.get_node(self._opr._OProxies, self._dictPath)
        for child_name in list(node['Children']):
            child_proxy = getattr(self, child_name, None)
            if child_proxy:
                child_proxy._remove()  # Recursive call
        
        # Remove self from parent
        if hasattr(self, '_opr') and hasattr(self, '_dictPath'):
            parent_path, name = self._dictPath.rsplit('.', 1) if '.' in self._dictPath else (None, self._dictPath)
            if parent_path:
                parent_proxy = hierarchical_storage.get_node(self._opr.OProxies, parent_path)
                if name in parent_proxy['Children']:
                    del parent_proxy['Children'][name]
            else:
                del self._opr.OProxies[name]  # Root removal
            
            hierarchical_storage.remove_node(self._opr.OProxies, self._dictPath)
            hierarchical_storage.remove_node(self._opr._OProxies, self._dictPath)
        
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
    node = hierarchical_storage.get_node(self._opr._OProxies, dict_path)
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
                # Update lookup: remove old
                self._by_name_or_path.pop(old_key, None)
                # Add new (find wrapper)
                wrapper = next((w for w in self if w.op == op), None)
                if wrapper:
                    self._by_name_or_path[new_key] = wrapper
                # Update mapping: move to new key, handle conflict
                resolved_new_key = new_key
                if new_key in mapping:
                    i = 1
                    while f"{new_key}_{i}" in mapping:
                        i += 1
                    resolved_new_key = f"{new_key}_{i}"
                mapping[resolved_new_key] = {'op': op, 'initial_path': op.path}  # Update initial_path if needed, but keep original
                del mapping[old_key]
                # Append for printing
                refreshed_ops.append((op, old_key, resolved_new_key))
        
        # Print dynamic statements for refreshed OPs
        for op, old_key, new_key in refreshed_ops:
            log(f"Refreshed OP {op.path}: name changed from {old_key} to {new_key}")
    
    # Sync ExtensionDATs similar to OPs
    extension_mapping = node.get('ExtensionDATs', {})
    extension_changes = []
    refreshed_extensions = []
    
    for key, data in list(extension_mapping.items()):
        op = data.get('op')
        if op is None or not op.valid:
            # Try to resolve from initial_path if moved
            initial_path = data.get('initial_path')
            new_op = td.op(initial_path)
            if new_op and new_op.valid and new_op.name == key:
                data['op'] = new_op
                log(f"Updated Extension DAT path for {key} to {new_op.path}")
            else:
                extension_changes.append(('remove', key, op))
                continue
        current_name = op.name
        if current_name != key:
            extension_changes.append(('update', key, current_name, op))
    
    if extension_changes:
        for change in extension_changes:
            if change[0] == 'remove':
                key, op = change[1], change[2]
                op_name = op.name if op else key
                log(f"Extension DAT {op_name} not found or invalid; removing")
                del extension_mapping[key]
            elif change[0] == 'update':
                old_key, new_key, op = change[1:]
                resolved_new_key = new_key
                if new_key in extension_mapping:
                    i = 1
                    while f"{new_key}_{i}" in extension_mapping:
                        i += 1
                    resolved_new_key = f"{new_key}_{i}"
                extension_mapping[resolved_new_key] = {'op': op, 'initial_path': op.path}
                del extension_mapping[old_key]
                refreshed_extensions.append((op, old_key, resolved_new_key))
                
                # Update dat_key in Extensions if referencing this
                for ext in node.get('Extensions', []):
                    if ext.get('dat_key') == old_key:
                        ext['dat_key'] = resolved_new_key
                        log(f"Updated extension {ext['name']} dat_key from {old_key} to {resolved_new_key}")
        
        # Print for refreshed Extension DATs
        for op, old_key, new_key in refreshed_extensions:
            log(f"Refreshed Extension DAT {op.path}: name changed from {old_key} to {new_key}")
    
    # Recurse to children
    for child_name in list(node['Children']):
        child_proxy = getattr(self, child_name, None)
        if child_proxy:
            child_proxy._refresh()  # Changed to _refresh for consistency with class_dict
    
    return self  # Allow chaining