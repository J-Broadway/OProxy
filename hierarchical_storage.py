# hierarchical_storage.dat

def init_node(dict_structure, path):
    """
    """
    if isinstance(path, str):
        path = path.split('.') if path else []
    
    # Handle root initialization (empty path)
    if not path:
        if 'Extensions' not in dict_structure:
            dict_structure['Extensions'] = []
        if 'Children' not in dict_structure:
            dict_structure['Children'] = {}
        return
    
    # Handle container initialization
    current = dict_structure
    for i, segment in enumerate(path):
        if i == 0:
            # First segment - ensure we're working with Children section
            if 'Children' not in current:
                current['Children'] = {}
            current = current['Children']
        else:
            # Subsequent segments - navigate through Children
            current = current['Children']
        if segment not in current:
            current[segment] = {'OPs': {}, 'Extensions': [], 'Children': {}}
        current = current[segment]

def get_node(dict_structure, path):
    """
    """
    if isinstance(path, str):
        path = path.split('.') if path else []
    
    # Handle root access (empty path)
    if not path:
        return dict_structure
    
    # Handle container access
    current = dict_structure
    for i, segment in enumerate(path):
        if i == 0:
            # First segment - look in Children section
            current = current.get('Children', {})
        else:
            # Subsequent segments - navigate through Children
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
    Update a specific key (e.g., 'OPs', 'Extensions', 'Children') at the node specified by path.
    Empty path ('') updates root structure.
    """
    node = get_node(dict_structure, path)
    if node:  # Only update if node exists
        node[key] = value

def remove_node(dict_structure, path, recursive=True):
    """
    Remove a node at the given path, optionally recursing to prune children first, and cleaning up empty parents if necessary.
    Empty path ('') cannot be removed (root structure).
    """
    if isinstance(path, str):
        path = path.split('.') if path else []
    
    # Cannot remove root structure
    if not path:
        return
    
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
    Starts from Children section to avoid processing root Extensions.
    """
    # Start from Children section to avoid processing root Extensions
    children = dict_structure.get('Children', {})
    for name, node in children.items():
        current_path = path + [name]
        # Only process nodes that are dictionaries (container nodes)
        if isinstance(node, dict):
            func(node, current_path)
            # Only recurse into Children if it exists and is a dictionary
            if 'Children' in node and isinstance(node['Children'], dict):
                traverse_tree(node, func, current_path)

def flatten_ops(dict_structure, path=[]):
    """
    Recursively collect all OPs from the tree starting from path.
    Returns a list of all descendant OPs.
    Empty path ('') starts from root but only collects from Children.
    """
    ops = []
    current = get_node(dict_structure, path)
    
    # For root path, only collect from Children (not root Extensions)
    if not path:
        children = current.get('Children', {})
        for child_name, child_node in children.items():
            ops.extend(flatten_ops(dict_structure, [child_name]))
        return ops
    
    # For container paths, collect OPs from this container
    if 'OPs' in current:
        if isinstance(current['OPs'], list):
            ops.extend(current['OPs'])
        else:
            ops.extend([v['op'] for v in current['OPs'].values()])
    
    # Recurse into children
    if 'Children' in current:
        for child_name, child_node in current['Children'].items():
            ops.extend(flatten_ops(dict_structure, path + [child_name]))
    
    return ops