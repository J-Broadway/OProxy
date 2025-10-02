# utils.dat
import td


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