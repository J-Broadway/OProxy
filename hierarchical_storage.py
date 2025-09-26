# hierarchical_storage.dat

def init_node(dict_structure, path):
    """
    Initialize a node in the hierarchical dictionary structure based on the path.
    Path can be a string like 'Test.another' or a list ['Test', 'another'].
    Creates 'OPs', 'Extensions', 'Children' if not present; uses dict for 'OPs' (detailed format).
    """
    if isinstance(path, str):
        path = path.split('.')
    
    current = dict_structure
    for i, segment in enumerate(path):
        if i > 0:
            current = current['Children']
        if segment not in current:
            current[segment] = {'OPs': {}, 'Extensions': [], 'Children': {}}
        current = current[segment]

def get_node(dict_structure, path):
    """
    Retrieve the node dictionary at the given path.
    Path can be a string like 'Test.another' or a list ['Test', 'another'].
    Returns the sub-dict at that path or an empty dict if not found.
    """
    if isinstance(path, str):
        path = path.split('.')
    
    current = dict_structure
    for i, segment in enumerate(path):
        if i > 0:
            current = current.get('Children', {})
        current = current.get(segment, {})
        if not current:  # Early exit if path segment not found
            return {}
    return current

def get_node_path(path):
    """
    Utility to get the path as a string for logging or keys.
    """
    if isinstance(path, list):
        return '.'.join(path)
    return path

def update_nested(dict_structure, path, key, value):
    """
    Update a specific key (e.g., 'OPs' or 'Extensions') at the node specified by path.
    """
    node = get_node(dict_structure, path)
    node[key] = value

def remove_node(dict_structure, path, recursive=True):
    """
    Remove a node at the given path, optionally recursing to prune children first, and cleaning up empty parents if necessary.
    """
    if isinstance(path, str):
        path = path.split('.')
    
    # Validate path exists before attempting removal
    current = dict_structure
    parents = []
    for i, segment in enumerate(path):
        if segment not in current:
            # Path doesn't exist, nothing to remove
            return
        parents.append((current, segment))
        if i + 1 < len(path):
            if 'Children' not in current[segment]:
                # Path is incomplete, nothing to remove
                return
            current = current[segment]['Children']
    
    # If recursive, prune children first
    if recursive and 'Children' in current[segment]:
        node_to_remove = current[segment]
        # Recurse to children and remove them
        for child_name in list(node_to_remove['Children'].keys()):
            child_path = '.'.join(path + [child_name])
            remove_node(dict_structure, child_path, recursive=True)
    
    # Remove the node itself
    if segment in current:
        del current[segment]
    
    # Clean up empty parents upwards
    for parent_dict, parent_seg in reversed(parents[:-1]):
        if parent_seg in parent_dict:
            child_node = parent_dict[parent_seg]
            if not child_node.get('OPs', {}) and not child_node.get('Extensions', []) and not child_node.get('Children', {}):
                del parent_dict[parent_seg]
            else:
                break

def traverse_tree(dict_structure, func, path=[]):
    """
    Recursively traverse the tree, applying func to each node (with current_path).
    func takes (node, current_path).
    """
    for name, node in dict_structure.items():
        current_path = path + [name]
        func(node, current_path)
        traverse_tree(node['Children'], func, current_path)

def flatten_ops(dict_structure, path=[]):
    """
    Recursively collect all OPs from the tree starting from path.
    Returns a list of all descendant OPs.
    """
    ops = []
    current = get_node(dict_structure, path)
    ops.extend(current['OPs'] if isinstance(current['OPs'], list) else [v['op'] for v in current['OPs'].values()])
    for child_name, child_node in current['Children'].items():
        ops.extend(flatten_ops(dict_structure, path + [child_name]))
    return ops