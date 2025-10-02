# utils.dat
import td
hierarchical_storage    = mod('hierarchical_storage')
from collections import deque

class Logger:
    """Enhanced logging system with multi-line support and process tracking"""
    
    def __init__(self):
        self.multi_mode = False
        self.multi_buffer = []
        self.multi_process = None
        self.multi_level = None
        # Track full state: (process, level, multi) for proper context detection
        self.last_state = None
    
    def __del__(self):
        """Destructor to flush any remaining multi-line buffer"""
        self._flush_multi_buffer()
    
    def _format_process(self, process):
        """Format process parameter for display"""
        if process is None:
            return ""
        if isinstance(process, str):
            return f":{process}"
        if isinstance(process, (list, tuple)):
            return f":{':'.join(process)}"
        return f":{str(process)}"
    
    def _format_prefix(self, level, process=None):
        """Format the log prefix with level and optional process"""
        level_upper = level.upper()
        process_str = self._format_process(process)
        return f"<OProxy [{level_upper}{process_str}]>"
    
    def _flush_multi_buffer(self):
        """Flush the multi-line buffer and exit multi-mode"""
        if not self.multi_buffer:
            # Even if buffer is empty, reset multi-mode state
            self.multi_mode = False
            self.multi_process = None
            self.multi_level = None
            return
        
        # Print the header with process and level
        header = self._format_prefix(self.multi_level, self.multi_process)
        print(header)
        
        # Print all buffered messages with indentation
        for msg in self.multi_buffer:
            print(f" {msg}")
        
        # Clear buffer and exit multi-mode
        self.multi_buffer.clear()
        self.multi_mode = False
        self.multi_process = None
        self.multi_level = None
    
    def _should_flush(self, process, level, multi):
        """Check if we should flush based on state change"""
        current_state = (process, level, multi)
        
        # If no previous state, don't flush
        if self.last_state is None:
            return False
        
        # If any parameter changed, flush
        if current_state != self.last_state:
            return True
        
        # If transitioning from multi=True to multi=False, flush
        if self.last_state[2] is True and current_state[2] is False:
            return True
        
        return False
    
    def log(self, msg, level='info', process=None, multi=False):
        """
        Enhanced logging function with multi-line support and process tracking
        
        Args:
            msg: The log message
            level: The status level ('info', 'warning', 'error')
            process: Process name (str) or hierarchical list for context
            multi: Whether to use multi-line mode
        """
        # In multi-line mode, inherit process and level from previous call if not provided
        if multi and self.multi_mode:
            if process is None:
                process = self.multi_process
            if level == 'info':  # Only inherit if using default level
                level = self.multi_level
        
        # Check if we should flush based on state change
        if self._should_flush(process, level, multi):
            self._flush_multi_buffer()
        
        if multi:
            if not self.multi_mode:
                # Entering multi-mode for the first time
                self.multi_mode = True
                self.multi_process = process
                self.multi_level = level
                self.multi_buffer = [msg]
            else:
                # Already in multi-mode, add to buffer
                self.multi_buffer.append(msg)
        else:
            # Single-line logging - ALWAYS flush any existing multi-line buffer first
            # This implements Option 1: automatic flushing when transitioning to single-line
            if self.multi_mode:
                self._flush_multi_buffer()
            
            # Single-line logging
            prefix = self._format_prefix(level, process)
            print(f"{prefix} {msg}")
        
        # Update last state AFTER processing
        self.last_state = (process, level, multi)
    
    def reset(self):
        """Reset the logger state (useful for testing)"""
        self.multi_mode = False
        self.multi_buffer.clear()
        self.multi_process = None
        self.multi_level = None
        self.last_state = None
    
    def get_state(self):
        """Get current logger state for debugging"""
        return {
            'multi_mode': self.multi_mode,
            'multi_buffer': self.multi_buffer.copy(),
            'multi_process': self.multi_process,
            'multi_level': self.multi_level,
            'last_state': self.last_state
        }
    
    def flush(self):
        """Manually flush the multi-line buffer"""
        self._flush_multi_buffer()

# Create global logger instance
_logger = Logger()

def log(msg, level='info', process=None, multi=False):
    """Global log function that delegates to the logger instance"""
    _logger.log(msg, level, process, multi)

def get_logger():
    """Get the logger instance for advanced usage"""
    return _logger

def reset_logger():
    """Reset the logger state (useful for testing)"""
    global _logger
    _logger.reset()

def flush_logger():
    """Flush any pending multi-line messages in the logger"""
    global _logger
    _logger.flush()

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

def _update_storage(proxy_instance):
    """Update storage for a proxy instance"""
    if '_opr' not in proxy_instance.__dict__ or '_proxy_name' not in proxy_instance.__dict__:
        return

    opr_instance = proxy_instance._opr
    proxy_name = proxy_instance._proxy_name
    dict_path = proxy_instance._dictPath

    # Get the node for this proxy
    root_storage = opr_instance.OProxies.getRaw()
    node = hierarchical_storage.get_node(root_storage, dict_path)

    # Ensure the node exists and has the required structure
    if not node:
        log(f"No storage node found for path '{dict_path}', initializing", level='warning', process='_update_storage')
        hierarchical_storage.init_node(root_storage, dict_path)
        node = hierarchical_storage.get_node(root_storage, dict_path)
    
    # Update the OPs list
    ops_list = []
    for wrapped_op in proxy_instance:
        if hasattr(wrapped_op, 'op') and wrapped_op.op.valid:
            ops_list.append({
                'op': wrapped_op.op,
                'name': wrapped_op.op.name,
                'path': wrapped_op.op.path
            })
    
    # Update the node
    node['OPs'] = {op['name']: {'op': op['op']} for op in ops_list}
    
    # CRITICAL FIX: Force update the storage to persist changes
    # This ensures that modifications to the node are actually saved
    if dict_path:
        # For child containers, we need to update the parent storage
        if '.' in dict_path:
            # This is a child container - the storage is already updated via the node reference
            pass
        else:
            # This is a root-level container - force update the storage
            # Since we may have already set the storage in _root_add, check if update is needed
            if 'Children' not in root_storage or dict_path not in root_storage['Children']:
                if 'Children' not in root_storage:
                    root_storage['Children'] = {}
                # Always update the specific container in the root storage
                root_storage['Children'][dict_path] = node
                if hasattr(opr_instance, 'ownerComp') and hasattr(opr_instance.ownerComp, 'store'):
                    opr_instance.ownerComp.store['OProxies'] = root_storage
                opr_instance.OProxies = root_storage
    
    # Auto-flushes multi-line

def _add(self, new_op):
    """Enhanced _add method with improved logging"""
    # Import OP_Proxy locally to avoid circular import issues
    OP_Proxy = mod('OP_Proxy').OP_Proxy
    
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
    
    # Start multi-line logging for add operation
    
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

def format_ascii_tree(node_oproxies, prefix="", detail='full', node_name=None):
    """
    Helper function to format an ASCII-style tree from OProxies data.
    Args:
        node_oproxies (dict): The OProxies node data (top-level or single node).
        prefix (str): The prefix for indentation.
        detail (str): The level of detail ('full', 'minimal').
        node_name (str, optional): The name of the single node when child is specified (e.g., 'chops').
    Returns:
        str: The formatted tree as a string.
    """
    tree = []
    
    # Check if node_oproxies is a single node (e.g., when child='chops' is specified)
    # A single node has 'OPs', 'Extensions', and 'Children' keys
    # The root storage structure has 'Extensions' and 'Children' keys but no 'OPs'
    is_single_node = isinstance(node_oproxies, dict) and 'OPs' in node_oproxies and 'Extensions' in node_oproxies and 'Children' in node_oproxies
    is_root_storage = isinstance(node_oproxies, dict) and 'Children' in node_oproxies and 'OPs' not in node_oproxies
    # Check if this is the actual OProxies structure with containers as direct children
    is_oproxies_structure = isinstance(node_oproxies, dict) and 'Extensions' in node_oproxies and 'Children' in node_oproxies and any(key not in ['OPs', 'Extensions', 'Children'] for key in node_oproxies.keys())
    
    def build_tree_with_proper_pipes():
        """Build the tree with proper pipe handling according to design principle"""
        result = []
        
        def format_sections_with_pipes(node_data, section_prefix, parent_has_more_siblings):
            """Format the OPs, Extensions, and Children sections with proper pipe handling"""
            ops = node_data.get('OPs', {})
            extensions = node_data.get('Extensions', [])
            children = node_data.get('Children', {})
            
            # Always show sections based on detail level, even if empty
            has_ops = detail in ['full', 'minimal']
            has_extensions = detail in ['full', 'minimal']
            has_children = detail in ['full', 'minimal']
            
            # Determine which sections to show and their order
            sections = []
            if has_ops:
                sections.append('ops')
            if has_extensions:
                sections.append('extensions')
            if has_children:
                sections.append('children')
            
            # Build pipe prefix based on whether parent has more siblings
            pipe_prefix = "│  " if parent_has_more_siblings else "   "
            
            # Add OPs section
            if has_ops:
                is_last_section = sections[-1] == 'ops'
                connector = "└─" if is_last_section else "├─"
                result.append(f"{section_prefix}{pipe_prefix}{connector} <OPs>" + (" []" if not ops else ""))
                if ops:
                    op_items = list(ops.items())
                    for i, (op_name, op_data) in enumerate(op_items):
                        is_last_op = i == len(op_items) - 1
                        op_connector = "└─" if is_last_op else "├─"
                        
                        # Build prefix for OP line
                        op_prefix = pipe_prefix
                        if not is_last_section:
                            op_prefix += "│  "
                        else:
                            op_prefix += "   "
                        
                        result.append(f"{section_prefix}{op_prefix}{op_connector} {op_name}")
                        
                        # OP details - only show in full detail mode
                        if detail == 'full':
                            op_detail_prefix = op_prefix
                            if not is_last_op:
                                op_detail_prefix += "│  "
                            else:
                                op_detail_prefix += "   "
                            
                            result.append(f"{section_prefix}{op_detail_prefix}└─ op: type:{op_data['op'].type} path:{op_data['op'].path}")
            
            # Add Extensions section
            if has_extensions:
                is_last_section = sections[-1] == 'extensions'
                connector = "└─" if is_last_section else "├─"
                result.append(f"{section_prefix}{pipe_prefix}{connector} <Extensions>" + (" []" if not extensions else ""))
                if extensions:
                    if detail == 'minimal':
                        for i, ext in enumerate(extensions):
                            is_last_ext = i == len(extensions) - 1
                            ext_connector = "└─" if is_last_ext else "├─"
                            
                            # Build prefix for extension line
                            ext_prefix = pipe_prefix
                            if not is_last_section:
                                ext_prefix += "│  "
                            else:
                                ext_prefix += "   "
                            
                            result.append(f"{section_prefix}{ext_prefix}{ext_connector} {ext['name']}")
                    else:  # full detail
                        for i, ext in enumerate(extensions):
                            is_last_ext = i == len(extensions) - 1
                            ext_connector = "└─" if is_last_ext else "├─"
                            
                            # Build prefix for extension line
                            ext_prefix = pipe_prefix
                            if not is_last_section:
                                ext_prefix += "│  "
                            else:
                                ext_prefix += "   "
                            
                            result.append(f"{section_prefix}{ext_prefix}{ext_connector} {ext['name']}")
                            
                            # Extension details
                            details = []
                            if ext.get('name') is not None:
                                details.append(('name', ext['name']))
                            if ext.get('cls') is not None:
                                details.append(('cls', ext['cls']))
                            if ext.get('func') is not None:
                                details.append(('func', ext['func']))
                            if ext.get('dat_path') is not None:
                                details.append(('dat_path', ext['dat_path']))
                            if ext.get('call') is not None:
                                details.append(('call', ext['call']))
                            # Always include args, even if None
                            details.append(('args', ext.get('args')))
                            
                            for j, (key, value) in enumerate(details):
                                is_last_detail = j == len(details) - 1
                                detail_connector = "└─" if is_last_detail else "├─"
                                
                                # Build prefix for detail line
                                detail_prefix = ext_prefix
                                if not is_last_ext:
                                    detail_prefix += "│  "
                                else:
                                    detail_prefix += "   "
                                
                                if key == 'args' and isinstance(value, (list, tuple)) and value:
                                    result.append(f"{section_prefix}{detail_prefix}{detail_connector} {key}:")
                                    for k, arg in enumerate(value):
                                        # Args use - instead of └─
                                        result.append(f"{section_prefix}{detail_prefix}      - {arg}")
                                else:
                                    result.append(f"{section_prefix}{detail_prefix}{detail_connector} {key}: {value}")
            
            # Add Children section (always last)
            if has_children:
                connector = "└─"  # Always last section
                result.append(f"{section_prefix}{pipe_prefix}{connector} <Children>" + (" []" if not children else ""))
                if children:
                    child_items = list(children.items())
                    for i, (child_name, child_data) in enumerate(child_items):
                        is_last_child = i == len(child_items) - 1
                        
                        if detail == 'full':
                            # In full mode, let format_node_with_pipes handle everything
                            child_ancestor_stack = []  # Empty to avoid extra pipes
                            nested_prefix = section_prefix + pipe_prefix + "   "  # 3 spaces for correct indentation
                            format_node_with_pipes(child_data, child_name, is_root=False, is_last=is_last_child, ancestor_stack=child_ancestor_stack, node_prefix=nested_prefix)
                        else:
                            # In minimal mode, show child name and recursively process children
                            child_ancestor_stack = []  # Empty to avoid extra pipes
                            nested_prefix = section_prefix + pipe_prefix + "   "  # 3 spaces for correct indentation
                            format_node_with_pipes(child_data, child_name, is_root=False, is_last=is_last_child, ancestor_stack=child_ancestor_stack, node_prefix=nested_prefix)
        
        def format_node_with_pipes(node_data, node_name, is_root=False, is_last=False, ancestor_stack=[], node_prefix=None):
            """Format a single node with proper pipe handling"""
            ops = node_data.get('OPs', {})
            extensions = node_data.get('Extensions', [])
            children = node_data.get('Children', {})
            
            # Use provided node_prefix or fall back to global prefix
            current_prefix = node_prefix if node_prefix is not None else prefix
            
            # Build the prefix for this line based on ancestor stack
            line_prefix = ""
            for i, has_more_siblings in enumerate(ancestor_stack):
                if has_more_siblings:
                    line_prefix += "│  "
                else:
                    line_prefix += "   "
            
            # Add node name with angle brackets
            if is_root:
                result.append(f"{current_prefix}<{node_name}>")
            else:
                connector = "└─" if is_last else "├─"
                result.append(f"{current_prefix}{line_prefix}{connector} {node_name}")
            
            # Use the shared format_sections_with_pipes function for consistency
            if not is_root:
                parent_has_more_siblings = not is_last
                format_sections_with_pipes(node_data, current_prefix + line_prefix, parent_has_more_siblings)
        
        if is_single_node and node_name:
            # Single node display (no < > around name, add sections separately)
            result.append(f"{prefix}{node_name}")
            # Add sections with indentation
            format_sections_with_pipes(node_oproxies, prefix + "  ", True)  # True for [END] following
        elif is_oproxies_structure:
            # OProxies structure display - containers are direct children
            result.append(f"{prefix}<root>")
            
            # Get containers (direct children) and root extensions
            containers = {k: v for k, v in node_oproxies.items() if k not in ['OPs', 'Extensions', 'Children']}
            root_extensions = node_oproxies.get('Extensions', [])
            
            # Determine if we have any content to show
            has_containers = bool(containers)
            has_root_extensions = bool(root_extensions)
            
            # Show containers first
            if has_containers:
                container_items = list(containers.items())
                for i, (name, data) in enumerate(container_items):
                    # Root containers always use ├─ because [END] is coming after all containers
                    connector = "├─"
                    result.append(f"{prefix}  {connector} {name}")
                    
                    # For children of root containers, determine if there are more siblings
                    # Always has more siblings because [END] is coming after all containers
                    has_more_siblings = True
                    format_sections_with_pipes(data, prefix + "  ", has_more_siblings)
            
            # Show root extensions last (always show, even if empty)
            result.append(f"{prefix}  ├─ <Extensions>" + (" []" if not root_extensions else ""))
            if root_extensions:
                for i, ext in enumerate(root_extensions):
                    is_last_ext = i == len(root_extensions) - 1
                    ext_connector = "└─" if is_last_ext else "├─"
                    result.append(f"{prefix}  │  {ext_connector} {ext['name']}")
                    
                    # Extension details for full mode
                    if detail == 'full':
                        details = []
                        if ext.get('name') is not None:
                            details.append(('name', ext['name']))
                        if ext.get('cls') is not None:
                            details.append(('cls', ext['cls']))
                        if ext.get('func') is not None:
                            details.append(('func', ext['func']))
                        if ext.get('dat_path') is not None:
                            details.append(('dat_path', ext['dat_path']))
                        if ext.get('call') is not None:
                            details.append(('call', ext['call']))
                        # Always include args, even if None
                        details.append(('args', ext.get('args')))
                        
                        for j, (key, value) in enumerate(details):
                            is_last_detail = j == len(details) - 1
                            detail_connector = "└─" if is_last_detail else "├─"
                            
                            # Build prefix for detail line
                            detail_prefix = "│  "
                            if not is_last_ext:
                                detail_prefix += "│  "
                            else:
                                detail_prefix += "   "
                            
                            if key == 'args' and isinstance(value, (list, tuple)) and value:
                                result.append(f"{prefix}  {detail_prefix}{detail_connector} {key}:")
                                for k, arg in enumerate(value):
                                    # Args use - instead of └─
                                    result.append(f"{prefix}  {detail_prefix}      - {arg}")
                            else:
                                result.append(f"{prefix}  {detail_prefix}{detail_connector} {key}: {value}")
        elif is_root_storage:
            # Root storage display - show root extensions and children
            result.append(f"{prefix}<root>")
            
            # Get root children (containers) and root extensions
            root_children = node_oproxies.get('Children', {})
            root_extensions = node_oproxies.get('Extensions', [])
            
            # Determine if we have any content to show
            has_containers = bool(root_children)
            has_root_extensions = bool(root_extensions)
            
            # Show containers first
            if has_containers:
                container_items = list(root_children.items())
                for i, (name, data) in enumerate(container_items):
                    is_last_container = i == len(container_items) - 1 and not has_root_extensions
                    # Root containers need proper indentation - they should be indented from <root>
                    connector = "└─" if is_last_container else "├─"
                    result.append(f"{prefix}  {connector} {name}")
                    
                    # For children of root containers, determine if there are more siblings
                    # If this is the last container and there are no root extensions, then no more siblings
                    # Otherwise, there are more siblings (either more containers or root extensions)
                    has_more_siblings = not is_last_container or has_root_extensions
                    format_sections_with_pipes(data, prefix + "  ", has_more_siblings)
            
            # Show root extensions last
            if has_root_extensions:
                result.append(f"{prefix}  └─ <Extensions>" + (" []" if not root_extensions else ""))
                if root_extensions:
                    for i, ext in enumerate(root_extensions):
                        is_last_ext = i == len(root_extensions) - 1
                        ext_connector = "└─" if is_last_ext else "├─"
                        result.append(f"{prefix}  │  {ext_connector} {ext['name']}")
                        
                        # Extension details for full mode
                        if detail == 'full':
                            details = []
                            if ext.get('name') is not None:
                                details.append(('name', ext['name']))
                            if ext.get('cls') is not None:
                                details.append(('cls', ext['cls']))
                            if ext.get('func') is not None:
                                details.append(('func', ext['func']))
                            if ext.get('dat_path') is not None:
                                details.append(('dat_path', ext['dat_path']))
                            if ext.get('call') is not None:
                                details.append(('call', ext['call']))
                            # Always include args, even if None
                            details.append(('args', ext.get('args')))
                            
                            for j, (key, value) in enumerate(details):
                                is_last_detail = j == len(details) - 1
                                detail_connector = "└─" if is_last_detail else "├─"
                                
                                # Build prefix for detail line
                                detail_prefix = "│  "
                                if not is_last_ext:
                                    detail_prefix += "│  "
                                else:
                                    detail_prefix += "   "
                                
                                if key == 'args' and isinstance(value, (list, tuple)) and value:
                                    result.append(f"{prefix}  {detail_prefix}{detail_connector} {key}:")
                                    for k, arg in enumerate(value):
                                        # Args use - instead of └─
                                        result.append(f"{prefix}  {detail_prefix}      - {arg}")
                                else:
                                    result.append(f"{prefix}  {detail_prefix}{detail_connector} {key}: {value}")
        else:
            # Regular node display - node_oproxies contains root-level containers
            result.append(f"{prefix}<root>")
            container_items = list(node_oproxies.items())
            for i, (name, data) in enumerate(container_items):
                is_last_container = i == len(container_items) - 1
                # Root containers need proper indentation - they should be indented from <root>
                # All root containers use ├─ because [END] is coming after them
                connector = "├─"  # Never use └─ for root containers because [END] is coming
                result.append(f"{prefix}  {connector} {name}")
                
                # For children of root containers, always has more siblings because [END] is coming
                root_has_more_siblings = True  # Always true because [END] is coming
                format_sections_with_pipes(data, prefix + "  ", root_has_more_siblings)
        
        # Add [END] marker with proper pipe handling
        if is_single_node:
            result.append(f"{prefix}  └─[END]")
        elif is_oproxies_structure:
            # For OProxies structure, only show [END] if there's content
            containers = {k: v for k, v in node_oproxies.items() if k not in ['OPs', 'Extensions', 'Children']}
            root_extensions = node_oproxies.get('Extensions', [])
            if containers or root_extensions:
                result.append(f"{prefix}  └─[END]")
        elif is_root_storage:
            # For root storage, only show [END] if there's content
            root_children = node_oproxies.get('Children', {})
            root_extensions = node_oproxies.get('Extensions', [])
            if root_children or root_extensions:
                result.append(f"{prefix}  └─[END]")
        elif not is_single_node and node_oproxies:
            result.append(f"{prefix}  └─[END]")
        else:
            result.append(f"{prefix}  └─[END]")
        
        return result
    
    # Build the tree with proper pipe handling
    tree = build_tree_with_proper_pipes()
    
    return '\n'.join(tree)