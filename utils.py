# utils.dat
import td

def store(container, storage_dict, parent_path=""):
    """
    Store an OProxyContainer into the TouchDesigner storage structure.

    Args:
        container: OProxyContainer to store
        storage_dict: The root storage dict (e.g., self.OProxies)
        parent_path: Path to parent container (empty string for root level)
    """
    if not hasattr(container, '_children'):
        raise TypeError("Object must be an OProxyContainer with _children attribute")

    # Build the container's storage representation
    container_data = {
        'extensions': {},
        'ops': {},       # For OPs in this container
        'children': {},  # For nested containers
    }

    # Process all children
    for name, child in container._children.items():
        if hasattr(child, '_op'):  # This is an OProxyLeaf
            # Store OP as object with path, raw OP, and extensions
            op_data = {
                'path': child._op.path,
                'op': child._op,  # Store raw OP object for name change detection
                'extensions': getattr(child, '_extensions', {})
            }
            container_data['ops'][name] = op_data
        elif hasattr(child, '_children'):  # This is a nested OProxyContainer
            # Recursively store nested container
            nested_storage = storage_dict
            if parent_path:
                # Navigate to the parent location in storage
                path_parts = parent_path.split('.')
                for part in path_parts:
                    if part not in nested_storage['children']:
                        nested_storage['children'][part] = {'children': {}, 'ops': {}, 'extensions': []}
                    nested_storage = nested_storage['children'][part]

            # Store the nested container
            store(child, nested_storage, f"{parent_path}.{name}" if parent_path else name)

    # Store this container in the appropriate location
    if parent_path:
        # Navigate to parent location and store
        current_dict = storage_dict
        path_parts = parent_path.split('.')

        # Create path if it doesn't exist
        for part in path_parts:
            if part not in current_dict['children']:
                current_dict['children'][part] = {'children': {}, 'ops': {}, 'extensions': []}
            current_dict = current_dict['children'][part]

        # Store the container data
        current_dict['children'][container.path.split('.')[-1]] = container_data
    else:
        # Root level storage
        storage_dict['children'][container.path or 'root'] = container_data


def remove(container, storage_dict, parent_path=""):
    """
    Remove a container from the TouchDesigner storage structure.

    Args:
        container: OProxyContainer to remove
        storage_dict: The root storage dict (e.g., self.OProxies)
        parent_path: Path to parent container (empty string for root level)
    """
    if parent_path:
        # Navigate to parent location and remove the container
        current_dict = storage_dict
        path_parts = parent_path.split('.')

        # Navigate to parent
        for part in path_parts:
            if part in current_dict['children']:
                current_dict = current_dict['children'][part]
            else:
                return  # Parent path doesn't exist

        # Remove the container
        container_name = container.path.split('.')[-1]
        if container_name in current_dict['children']:
            del current_dict['children'][container_name]
    else:
        # Root level removal
        container_name = container.path or 'root'
        if container_name in storage_dict['children']:
            del storage_dict['children'][container_name]


def td_isinstance(value, expected_type, allow_string=True):
    """
    Centralized TouchDesigner type checking and validation with string path support.
    
    Args:
        value: The value to validate (str, td.OP, td.DAT, etc.)
        expected_type: Expected TD type ('op', 'dat', 'chop', 'top', 'sop', 'mat', 'comp', 'pop', 'textDAT')
        allow_string: Whether to allow string paths and convert them with op()
    
    Returns:
        Validated TD object of the expected type
        
    Raises:
        TypeError: If value is not the expected type and cannot be converted
        ValueError: If string path doesn't resolve to a valid TD object
    """
    if not isinstance(expected_type, str):
        raise TypeError(f"expected_type must be a string, got {type(expected_type).__name__}")
    
    expected_type = expected_type.lower()
    
    # Build valid types list based on what's available in this TD version
    valid_types = ['op', 'dat', 'chop', 'top', 'sop', 'mat', 'comp', 'textdat']
    if hasattr(td, 'POP'):
        valid_types.append('pop')
    
    if expected_type not in valid_types:
        raise ValueError(f"expected_type must be one of {valid_types}, got '{expected_type}'")
    
    # Handle string paths if allowed
    if isinstance(value, str) and allow_string:
        try:
            resolved = td.op(value)
            if resolved is None:
                raise ValueError(f"String '{value}' does not resolve to a valid OP (resolved to None)")
            value = resolved
        except Exception as e:
            raise ValueError(f"String '{value}' does not resolve to a valid OP: {e}")
    
    # Type mapping for validation - only include types that exist in this TD version
    type_map = {
        'op': td.OP,
        'dat': td.DAT,
        'chop': td.CHOP,
        'top': td.TOP,
        'sop': td.SOP,
        'mat': td.MAT,
        'comp': td.COMP,
        'textdat': td.textDAT
    }
    
    # Add POP only if it exists in this TD version
    if hasattr(td, 'POP'):
        type_map['pop'] = td.POP
    
    expected_td_type = type_map[expected_type]
    
    # Validate the type
    if not isinstance(value, expected_td_type):
        if isinstance(value, str):
            raise TypeError(f"Expected {expected_td_type.__name__}, got string '{value}' (use allow_string=True to convert)")
        else:
            raise TypeError(f"Expected {expected_td_type.__name__}, got {type(value).__name__}")
    
    # Additional validation for OPs
    if hasattr(value, 'valid') and not value.valid:
        raise ValueError(f"Provided OP is not valid: {value}")
    
    return value


def make_serializable(storage):
    """
    Make storage dictionary serializable by replacing TouchDesigner operator objects with dicts
    and removing redundant path keys.

    Recursively walks the storage structure and:
    - Replaces TouchDesigner operator objects with serializable dicts containing name, type, path
    - Removes the separate 'path' key since it's now included in the operator dict

    Args:
        storage: The storage dictionary to make serializable

    Returns:
        A new dictionary with operator objects replaced by serializable dicts
    """
    if hasattr(storage, 'getRaw'):
        storage = storage.getRaw()
    if hasattr(storage, 'items') and callable(storage.items):
        serializable = {}
        for key, value in storage.items():
            if hasattr(value, 'val'):
                value = value.val
            if key in ['op', 'dat_op'] and hasattr(value, 'name') and hasattr(value, 'path') and hasattr(value, 'OPType'):
                serializable[key] = {
                    'name': value.name,
                    'type': value.OPType,
                    'path': value.path
                }
            elif (key == 'path' and 'op' in storage) or (key == 'dat_path' and 'dat_op' in storage):
                continue
            else:
                serializable[key] = make_serializable(value)
        return serializable
    elif isinstance(storage, list):
        return [make_serializable(item) for item in storage]
    else:
        return storage