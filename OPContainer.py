import td
import types  # Added for MethodType
import ast_mod  # Import ast_mod for extraction

OPBaseWrapper           = mod('OPBaseWrapper').OPBaseWrapper 
OP_Proxy                = mod('OP_Proxy').OP_Proxy
hierarchical_storage    = mod('hierarchical_storage')
log                     = mod('utils').log  # Added for warnings
proxy_remove            = mod('proxy_methods').proxy_remove
proxy_refresh           = mod('proxy_methods').proxy_refresh
format_ascii_tree       = mod('utils').format_ascii_tree  # Import ASCII formatting helper

class OPContainer(list, OPBaseWrapper):
    """
    Base class for OP groups. Now uses OP_Proxy for individuals.
    """
    def __init__(self, ops=None):
        # Handle empty initialization for hybrid containers
        if ops is None:
            ops = []
        elif not isinstance(ops, list):
            ops = [ops]  # Normalize single OP to list
        
        super().__init__([OP_Proxy(o) for o in ops])  # Wrap each OP on init
        self._by_name_or_path = {}
        self._parent = None  # Set during creation in oproxy for removal back-ref
        for wrapped in self:
            op = wrapped.op
            self._by_name_or_path[op.name] = wrapped
            self._by_name_or_path[op.path] = wrapped
    
    def __call__(self, identifier):
        """Return wrapped OP by name or path as a hybrid container."""
        wrapped_op = self._by_name_or_path.get(identifier)
        if wrapped_op is None:
            return None
        
        # Create a hybrid container with the single OP
        hybrid_container = OPContainer([wrapped_op.op])
        
        # Copy essential attributes for persistence
        if hasattr(self, '_opr'):
            hybrid_container._opr = self._opr
        if hasattr(self, '_dictPath'):
            # Create a path for the individual OP
            op_name = wrapped_op.op.name
            hybrid_container._dictPath = f"{self._dictPath}.{op_name}"
        
        # Ensure the hybrid container has access to container methods
        # by setting up the same dynamic class structure as in oproxy._add
        if hasattr(self, '_opr'):
            class_dict = {
                '_add': lambda self, name, op, restore=True: self._opr._add(name, op, parent=self, restore=restore),
                '_remove': proxy_remove,
                '_refresh': proxy_refresh
            }
            # Create a dynamic subclass with container methods
            HybridContainerClass = type(f"Hybrid_{op_name}", (OPContainer,), class_dict)
            # Create new instance with the same data
            hybrid_container = HybridContainerClass([wrapped_op.op])
            # Copy attributes
            hybrid_container._opr = self._opr
            hybrid_container._parent = self
            hybrid_container._proxy_name = op_name
            hybrid_container._dictPath = f"{self._dictPath}.{op_name}"
            
            # Initialize storage node for hybrid container to enable extension storage
            hierarchical_storage.init_node(self._opr.OProxies, hybrid_container._dictPath)
            
            # CRITICAL FIX: Copy extensions from both parent container and hybrid container's own storage
            # This ensures that extensions applied to either the parent or the hybrid are available
            if hasattr(self, '_opr') and hasattr(self, '_dictPath'):
                # First, try to get extensions from the hybrid container's own storage
                hybrid_node = hierarchical_storage.get_node(self._opr.OProxies, hybrid_container._dictPath)
                
                # Also check parent container for extensions
                parent_node = hierarchical_storage.get_node(self._opr.OProxies, self._dictPath)
                
                # Collect extensions from both sources
                all_extensions = []
                if 'Extensions' in hybrid_node:
                    all_extensions.extend(hybrid_node['Extensions'])
                if 'Extensions' in parent_node:
                    all_extensions.extend(parent_node['Extensions'])
                
                if all_extensions:
                    for ext in all_extensions:
                        try:
                            dat_path = ext['dat_path']
                            dat_op = op(dat_path)
                            if not dat_op or not isinstance(dat_op, td.DAT):
                                continue
                            cls = ext.get('cls')
                            func = ext.get('func')
                            call = ext.get('call', False)
                            args = ext.get('args')
                            # Convert args to a standard list if it's a TouchDesigner storage object
                            if args is not None and not isinstance(args, (tuple, list)):
                                try:
                                    args = list(args)
                                except Exception:
                                    continue
                            if args and not isinstance(args, (tuple, list)):
                                continue
                            if args and isinstance(args, tuple) and len(args) == 1 and not isinstance(args[0], (tuple, list)):
                                args = (args[0],)
                            obj = ast_mod.Main(cls=cls, func=func, op=dat_op)
                            if call:
                                result = obj(*args) if args else obj()
                                if isinstance(obj, type):  # Class instantiation
                                    class InstanceDelegate:
                                        def __init__(self, instance):
                                            self.instance = instance
                                        def __get__(self, obj, owner):
                                            if obj is None:
                                                return self.instance
                                            method_or_attr = getattr(self.instance, owner.__name__)
                                            if callable(method_or_attr):
                                                def wrapped_method(*args, **kwargs):
                                                    try:
                                                        return method_or_attr(*args, **kwargs)
                                                    except Exception as e:
                                                        log(f"Error in method '{owner.__name__}' of extension '{ext['name']}' from DAT {dat_path}: {str(e)}", level='error')
                                                        raise
                                                return wrapped_method
                                            return method_or_attr
                                    setattr(type(hybrid_container), ext['name'], InstanceDelegate(result))
                                else:
                                    setattr(type(hybrid_container), ext['name'], types.MethodType(obj, hybrid_container))
                            else:
                                setattr(type(hybrid_container), ext['name'], obj)
                        except Exception as e:
                            log(f"Failed to copy extension '{ext.get('name', 'unknown')}' to hybrid container: {e}")
        
        return hybrid_container
    
    def cls(self):
        """Return the class type for extension."""
        return type(self)
    
    def __getattr__(self, name):
        # Check if the attribute exists on the container itself (e.g., extensions, container methods)
        if hasattr(self.__class__, name):
            attr = getattr(self.__class__, name)
            # If the attribute is a descriptor, call its __get__ method
            if hasattr(attr, '__get__'):
                return attr.__get__(self, type(self))
            return attr  # Otherwise, return the attribute directly
        
        # Check for child containers in storage first
        # Only look for child containers if this is NOT a multi-OP container
        # Multi-OP containers should not have child containers accessible via attribute access
        if hasattr(self, '_opr') and hasattr(self, '_dictPath') and len(self) <= 1:
            node = hierarchical_storage.get_node(self._opr.OProxies, self._dictPath)
            if 'Children' in node and name in node['Children']:
                # Child container exists, create and return it
                child_data = node['Children'][name]
                child_ops = [op_data['op'] for op_data in child_data.get('OPs', {}).values()]
                
                # Create child container with proper methods
                class_dict = {
                    '_add': lambda self, name, op, restore=True: self._opr._add(name, op, parent=self, restore=restore),
                    '_remove': proxy_remove,
                    '_refresh': proxy_refresh
                }
                ChildContainerClass = type(name, (OPContainer,), class_dict)
                child_container = ChildContainerClass(child_ops)
                child_container._opr = self._opr
                child_container._parent = self
                child_container._proxy_name = name
                child_container._dictPath = f"{self._dictPath}.{name}"
                
                # Restore any child containers recursively
                if 'Children' in child_data:
                    self._opr._restore_children(child_container, child_data['Children'])
                
                return child_container
        
        # Container methods should be available on the container itself
        # These are already defined on the class, so they should be caught by the first check above
        
        # Context-aware delegation based on container size
        if len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid __getitem__ recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            if hasattr(wrapped_op.op, name):
                return getattr(wrapped_op.op, name)
            # Fall back to OP_Proxy behavior
            return getattr(wrapped_op, name)
        else:
            # Multiple OPs or empty - container behavior
            # Check if any wrapped OP has the attribute before trying to access it
            results = []
            for w in self:
                if hasattr(w, name):
                    results.append(getattr(w, name))
                elif hasattr(w.op, name):
                    results.append(getattr(w.op, name))
                else:
                    # If no OP has the attribute, raise AttributeError
                    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            return results
    
    def __setattr__(self, name, value):
        if name.startswith('_'):  # Internal attrs
            super().__setattr__(name, value)
        elif len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid __getitem__ recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            if hasattr(wrapped_op.op, name):
                setattr(wrapped_op.op, name, value)
            else:
                # Fall back to OP_Proxy behavior
                setattr(wrapped_op, name, value)
        else:
            # Multiple OPs or empty - container behavior
            for w in self:
                if hasattr(w, name):
                    setattr(w, name, value)
    
    def __getitem__(self, key):
        if len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            return wrapped_op.op[key]
        else:
            # Multiple OPs or empty - container behavior
            return [w[key] for w in self]
    
    def __setitem__(self, key, value):
        if len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            wrapped_op.op[key] = value
        else:
            # Multiple OPs or empty - container behavior
            for w in self:
                w[key] = value
    
    def __str__(self):
        if len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            return str(wrapped_op.op)
        else:
            # Multiple OPs or empty - container behavior
            return f"{type(self).__name__}({[w.op for w in self]})"
    
    def __repr__(self):
        if len(self) == 1:
            # Single OP - proxy behavior
            # Access the wrapped OP directly to avoid recursion
            wrapped_op = list.__getitem__(self, 0)  # Use list.__getitem__ to avoid recursion
            return repr(wrapped_op.op)
        else:
            # Multiple OPs or empty - container behavior
            return f"{type(self).__name__}({[w.op for w in self]})"
    
    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False):
        """
        Extend the proxy class with an attribute or method using ast_mod for DAT-based extraction.
        'cls' or 'func' specifies the class or function name to extract from 'dat'; if neither, 'value' is used directly.
        'args' is a tuple/list of positional arguments for instantiation/calling when call=True.
        """
        if not (cls or func) and dat is not None:
            raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
        if (cls and func) or (not cls and not func):
            raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
        
        if dat:
            if not isinstance(dat, td.DAT):
                raise TypeError("Provided 'dat' must be a td.DAT instance")
            try:
                obj = ast_mod.Main(cls=cls, func=func, op=dat)
                # Ensure args is properly validated as a sequence, handling single-element tuples
                if call and args is not None:
                    if not isinstance(args, (tuple, list)):
                        raise TypeError("args must be a tuple or list of positional arguments when call=True")
                    # Ensure args is treated as a sequence of arguments
                    if isinstance(args, tuple) and len(args) == 1 and not isinstance(args[0], (tuple, list)):
                        args = (args[0],)  # Normalize single-element tuple to ensure proper unpacking
                if call:
                    if isinstance(obj, type):  # Class instantiation
                        result = obj(*args) if args else obj()
                        # Use a descriptor to delegate attribute access to the instance
                        class InstanceDelegate:
                            def __init__(self, instance):
                                self.instance = instance
                            def __get__(self, obj, owner):
                                if obj is None:
                                    return self.instance
                                # Return a bound method or attribute from the instance
                                method_or_attr = getattr(self.instance, owner.__name__)
                                if callable(method_or_attr):
                                    def wrapped_method(*args, **kwargs):
                                        try:
                                            return method_or_attr(*args, **kwargs)
                                        except Exception as e:
                                            log(f"Error in method '{owner.__name__}' of extension '{attr_name}' from DAT {dat.path}: {str(e)}", level='error')
                                            raise
                                    return wrapped_method
                                return method_or_attr
                        # Store the instance for attribute access
                        setattr(type(self), attr_name, InstanceDelegate(result))
                    else:
                        # Function call - bind the function as a method and call it
                        bound_method = types.MethodType(obj, self)
                        result = bound_method(*args) if args else bound_method()
                        # Store the result as a method that returns the result
                        def method_wrapper(*method_args, **method_kwargs):
                            return result
                        setattr(type(self), attr_name, method_wrapper)
                else:
                    setattr(type(self), attr_name, obj)  # Attach class type or function
            except Exception as e:
                raise RuntimeError(f"Failed to load and attach from DAT {dat.path}: {e}") from e
            
            # Persist extension in storage (serializable)
            if hasattr(self, '_opr') and hasattr(self, '_dictPath'):
                node = hierarchical_storage.get_node(self._opr.OProxies, self._dictPath)
                if 'Extensions' not in node:
                    node['Extensions'] = []
                # Check for duplicate and overwrite if exists
                existing_ext = next((ext for ext in node['Extensions'] if ext['name'] == attr_name), None)
                if existing_ext:
                    log(f"Extension '{attr_name}' has been overwritten")
                    node['Extensions'].remove(existing_ext)
                node['Extensions'].append({
                    'name': attr_name,
                    'cls': cls,
                    'func': func,
                    'dat_path': dat.path,
                    'call': call,
                    'args': args
                })
            else:
                # Non-persistent: attach directly, skip storage
                log(f"Non-persistent extension '{attr_name}' added; won't survive project reload or extension re-init\n"
                    "Highly Recommended: Adding 'dat=me' for extension persistence.")
                setattr(type(self), attr_name, cls or func)  # Use cls/func directly if no dat
        else:
            # Non-persistent: attach directly, skip storage
            log(f"Non-persistent extension '{attr_name}' added; won't survive project reload or extension re-init\n"
                "Highly Recommended: Adding 'dat=me' for extension persistence.")
            setattr(type(self), attr_name, cls or func)  # Use cls/func directly if no dat
        
        return self  # For chaining
    
    def _extendItems(self, attr_name, value):
        """Extend all OPs in the proxy (recursively via base _extend)."""
        if callable(value):
            def bound_method(self_wrapper, *args, **kwargs):
                return value(self_wrapper, *args, **kwargs)
            for wrapper in self:
                setattr(type(wrapper), attr_name, bound_method)  # Apply to each child's class
        else:
            for wrapper in self:
                setattr(type(wrapper), attr_name, value)
        return self  # Allow chaining
    
    def flatten_ops(self):
        """Recursively collect all descendant OPs."""
        return hierarchical_storage.flatten_ops(self._opr.OProxies, self._dictPath)
    
    def _remove(self, to_remove=None):
        proxy_remove(self, to_remove=to_remove)
        if to_remove is None and self._parent:  # Clean up attribute from parent for container removal
            delattr(self._parent, self._proxy_name)
        return self  # Or None if fully removed
    
    def _tree(self, child=None, detail='full', asDict=False):
        """
        Print or return an ASCII-style tree of the proxy structure.
        Args:
            child (str, optional): The child node to start printing from (e.g., 'chops').
            detail (str): The level of detail ('full', 'minimal'); default is 'full'.
            asDict (bool): If True, return the raw dictionary instead of printing; default is False.
        Returns:
            dict or None: Raw storage dict if asDict=True, otherwise None.
        """
        # Determine the root opr instance
        opr_instance = self if hasattr(self, 'storage') else getattr(self, '_opr', None)
        if not opr_instance or not hasattr(opr_instance, 'storage'):
            log("<OProxy [WARNING]> No storage or parent reference available for tree", level='warning')
            return None if asDict else None

        # Get raw storage dictionary
        oproxies = opr_instance.storage['OProxies'].getRaw()

        # Determine starting path
        start_path = []
        if hasattr(self, '_dictPath') and self._dictPath:
            start_path = self._dictPath.split('.')
        if child:
            start_path.extend(child.split('.'))

        # Validate starting path
        current_oproxies = oproxies
        for i, segment in enumerate(start_path):
            if i > 0:
                current_oproxies = current_oproxies.get('Children', {})
            if segment not in current_oproxies:
                log(f"<OProxy [WARNING]> Child '{child}' not found in storage at path {'.'.join(start_path[:i+1])}", level='warning')
                return None if asDict else None
            current_oproxies = current_oproxies[segment]

        # Return raw dictionary if asDict=True
        if asDict:
            return {'OProxies': current_oproxies}

        # Build and print the tree
        node_name = start_path[-1] if child else None
        tree_str = format_ascii_tree(
            node_oproxies=current_oproxies,
            prefix="",
            detail=detail,
            node_name=node_name
        )
        if not tree_str:
            log("<OProxy [WARNING]> Empty tree generated", level='warning')
            return None

        # Print the tree and return None to avoid console printing the return value
        print(f"<OProxy [INFO]>\n{tree_str}")
        return None