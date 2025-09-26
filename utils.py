# utils.dat
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
    
    node = hierarchical_storage.get_node(self._opr.OProxies, dict_path)
    if 'OPs' not in node:
        node['OPs'] = {}
    mapping = node['OPs']
    current_ops = set(current_ops_list)
    # Remove missing from OProxies
    to_del = [k for k, v in list(mapping.items()) if v['op'] not in current_ops]
    for k in to_del:
        del mapping[k]
    # Add new ones (not in existing OProxies ops)
    existing_proxied_ops = {v['op'] for v in mapping.values()}
    new_ops = [op for op in current_ops_list if op not in existing_proxied_ops]
    for op in new_ops:
        initial_name = op.name
        if initial_name in mapping:
            i = 1
            while f"{initial_name}_{i}" in mapping:
                i += 1
            initial_name = f"{initial_name}_{i}"
        mapping[initial_name] = {'op': op}

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
    is_single_node = isinstance(node_oproxies, dict) and 'OPs' in node_oproxies and 'Extensions' in node_oproxies and 'Children' in node_oproxies
    
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
        else:
            # Root display - node_oproxies contains root-level containers
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
        if not is_single_node and node_oproxies:
            result.append(f"{prefix}  └─[END]")
        else:
            result.append(f"{prefix}  └─[END]")
        
        return result
    
    # Build the tree with proper pipe handling
    tree = build_tree_with_proper_pipes()
    
    return '\n'.join(tree)