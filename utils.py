hierarchical_storage    = mod('hierarchical_storage')

# Enhanced logging with levels (info, warning, error)
def log(msg, level='info'):
    prefix = {
        'info': "<OProxy [INFO]> ",
        'warning': "<OProxy [WARNING]> ",
        'error': "<OProxy [ERROR]> "
    }.get(level.lower(), "<OProxy> ")
    print(f"{prefix}{msg}")

def _update_storage(self):
    if not hasattr(self, '_opr') or not hasattr(self, '_dictPath'):
        return
    dict_path = self._dictPath
    current_ops_list = [w.op for w in self]
    hierarchical_storage.update_nested(self._opr.OProxies, dict_path, 'OPs', current_ops_list)
    
    node = hierarchical_storage.get_node(self._opr._OProxies, dict_path)
    if 'OPs' not in node:
        node['OPs'] = {}
    mapping = node['OPs']
    current_ops = set(current_ops_list)
    # Remove missing from _OProxies
    to_del = [k for k, v in list(mapping.items()) if v['op'] not in current_ops]
    for k in to_del:
        del mapping[k]
    # Add new ones (not in existing _OProxies ops)
    existing_proxied_ops = {v['op'] for v in mapping.values()}
    new_ops = [op for op in current_ops_list if op not in existing_proxied_ops]
    for op in new_ops:
        initial_name = op.name
        if initial_name in mapping:
            i = 1
            while f"{initial_name}_{i}" in mapping:
                i += 1
            initial_name = f"{initial_name}_{i}"
        mapping[initial_name] = {'op': op, 'initial_path': op.path}

def format_ascii_tree(node_oproxies, node_oproxies_detailed, prefix="", detail='full', node_name=None):
    """
    Helper function to format an ASCII-style tree from OProxies and _OProxies data.
    Args:
        node_oproxies (dict): The OProxies node data (top-level or single node).
        node_oproxies_detailed (dict): The _OProxies node data (top-level or single node).
        prefix (str): The prefix for indentation.
        detail (str): The level of detail ('full', 'minimal', 'dev').
        node_name (str, optional): The name of the single node when child is specified (e.g., 'chops').
    Returns:
        str: The formatted tree as a string.
    """
    tree = []
    
    # Check if node_oproxies is a single node (e.g., when child='chops' is specified)
    is_single_node = isinstance(node_oproxies, dict) and 'OPs' in node_oproxies and 'Extensions' in node_oproxies and 'Children' in node_oproxies
    
    if detail == 'minimal':
        if is_single_node and node_name:
            tree.append(f"{prefix}{node_name}")
        else:
            tree.append(f"{prefix}root")
            for name in node_oproxies:
                tree.append(f"{prefix}  ├─ {name}")
    elif detail == 'full':
        if is_single_node and node_name:
            tree.append(f"{prefix}{node_name}")
            ops = node_oproxies.get('OPs', [])
            extensions = node_oproxies.get('Extensions', [])
            children = node_oproxies.get('Children', {})
            if ops:
                tree.append(f"{prefix}  ├─ OPs")
                for op in ops:
                    tree.append(f"{prefix}  │  ├─ {op}")
            if extensions:
                tree.append(f"{prefix}  ├─ Extensions")
                for ext in extensions:
                    ext_parts = [f"name: {ext['name']}"]
                    if ext.get('func'):
                        ext_parts.append(f"func: {ext['func']}")
                    if ext.get('cls'):
                        ext_parts.append(f"cls: {ext['cls']}")
                    if ext.get('call') is not None:
                        ext_parts.append(f"call: {ext['call']}")
                    if ext.get('args'):
                        ext_parts.append(f"args: {ext['args']}")
                    tree.append(f"{prefix}  │  ├─ {', '.join(ext_parts)}")
            if children:
                tree.append(f"{prefix}  └─ Children: {children}")
        else:
            tree.append(f"{prefix}root")
            for name, data in node_oproxies.items():
                ops = data.get('OPs', [])
                extensions = data.get('Extensions', [])
                children = data.get('Children', {})
                tree.append(f"{prefix}  ├─ {name}")
                if ops:
                    tree.append(f"{prefix}  │  ├─ OPs")
                    for op in ops:
                        tree.append(f"{prefix}  │  │  ├─ {op}")
                if extensions:
                    tree.append(f"{prefix}  │  ├─ Extensions")
                    for ext in extensions:
                        ext_parts = [f"name: {ext['name']}"]
                        if ext.get('func'):
                            ext_parts.append(f"func: {ext['func']}")
                        if ext.get('cls'):
                            ext_parts.append(f"cls: {ext['cls']}")
                        if ext.get('call') is not None:
                            ext_parts.append(f"call: {ext['call']}")
                        if ext.get('args'):
                            ext_parts.append(f"args: {ext['args']}")
                        tree.append(f"{prefix}  │  │  ├─ {', '.join(ext_parts)}")
                if children:
                    tree.append(f"{prefix}  │  └─ Children: {children}")
    else:  # detail == 'dev'
        tree.append(f"{prefix}root")
        tree.append(f"{prefix}  ├─ OProxies")
        if is_single_node and node_name:
            ops = node_oproxies.get('OPs', [])
            extensions = node_oproxies.get('Extensions', [])
            children = node_oproxies.get('Children', {})
            tree.append(f"{prefix}  │  ├─ {node_name}")
            if ops:
                tree.append(f"{prefix}  │  │  ├─ OPs")
                for op in ops:
                    tree.append(f"{prefix}  │  │  │  ├─ {op}")
            if extensions:
                tree.append(f"{prefix}  │  │  ├─ Extensions: {extensions}")
            if children:
                tree.append(f"{prefix}  │  │  └─ Children: {children}")
        else:
            for name, data in node_oproxies.items():
                ops = data.get('OPs', [])
                extensions = data.get('Extensions', [])
                children = data.get('Children', {})
                tree.append(f"{prefix}  │  ├─ {name}")
                if ops:
                    tree.append(f"{prefix}  │  │  ├─ OPs")
                    for op in ops:
                        tree.append(f"{prefix}  │  │  │  ├─ {op}")
                if extensions:
                    tree.append(f"{prefix}  │  │  ├─ Extensions: {extensions}")
                if children:
                    tree.append(f"{prefix}  │  │  └─ Children: {children}")
        tree.append(f"{prefix}  └─ _OProxies")
        if is_single_node and node_name:
            ops = node_oproxies_detailed.get('OPs', {})
            extensions = node_oproxies_detailed.get('Extensions', [])
            children = node_oproxies_detailed.get('Children', {})
            tree.append(f"{prefix}     ├─ {node_name}")
            if ops:
                tree.append(f"{prefix}     │  ├─ OPs")
                for op_name, op_data in ops.items():
                    tree.append(f"{prefix}     │  │  ├─ {op_name}")
                    tree.append(f"{prefix}     │  │  │  ├─ op: {op_data['op']}")
                    tree.append(f"{prefix}     │  │  │  └─ initial_path: {op_data['initial_path']}")
            if extensions:
                tree.append(f"{prefix}     │  ├─ Extensions")
                for i, ext in enumerate(extensions):
                    ext_str = f"[{i}]"
                    for key, value in ext.items():
                        if value is not None:  # Skip None values for cleaner output
                            ext_str += f"\n{prefix}     │  │     ├─ {key}: {value}"
                    tree.append(f"{prefix}     │  │  {ext_str}")
            if children:
                tree.append(f"{prefix}     │  └─ Children: {children}")
        else:
            for name, data in node_oproxies_detailed.items():
                ops = data.get('OPs', {})
                extensions = data.get('Extensions', [])
                children = data.get('Children', {})
                tree.append(f"{prefix}     ├─ {name}")
                if ops:
                    tree.append(f"{prefix}     │  ├─ OPs")
                    for op_name, op_data in ops.items():
                        tree.append(f"{prefix}     │  │  ├─ {op_name}")
                        tree.append(f"{prefix}     │  │  │  ├─ op: {op_data['op']}")
                        tree.append(f"{prefix}     │  │  │  └─ initial_path: {op_data['initial_path']}")
                if extensions:
                    tree.append(f"{prefix}     │  ├─ Extensions")
                    for i, ext in enumerate(extensions):
                        ext_str = f"[{i}]"
                        for key, value in ext.items():
                            if value is not None:  # Skip None values for cleaner output
                                ext_str += f"\n{prefix}     │  │     ├─ {key}: {value}"
                        tree.append(f"{prefix}     │  │  {ext_str}")
                if children:
                    tree.append(f"{prefix}     │  └─ Children: {children}")
    
    return '\n'.join(tree)