import td
import types  # Added for MethodType
import ast_mod  # Import ast_mod for extraction

OPBaseWrapper           = mod('OPBaseWrapper').OPBaseWrapper 
OP_Proxy                = mod('OP_Proxy').OP_Proxy
hierarchical_storage    = mod('hierarchical_storage')
log                     = mod('utils').log  # Added for warnings
proxy_remove            = mod('proxy_methods').proxy_remove
format_ascii_tree       = mod('utils').format_ascii_tree  # Import ASCII formatting helper

class OPContainer(list, OPBaseWrapper):
    """
    Base class for OP groups. Now uses OP_Proxy for individuals.
    """
    def __init__(self, ops):
        super().__init__([OP_Proxy(o) for o in ops])  # Wrap each OP on init
        self._by_name_or_path = {}
        self._parent = None  # Set during creation in oproxy for removal back-ref
        for wrapped in self:
            op = wrapped.op
            self._by_name_or_path[op.name] = wrapped
            self._by_name_or_path[op.path] = wrapped
    
    def __call__(self, identifier):
        """Return wrapped OP by name or path."""
        return self._by_name_or_path.get(identifier)
    
    def cls(self):
        """Return the class type for extension."""
        return type(self)
    
    def __repr__(self):
        return f"{type(self).__name__}({[w.op for w in self]})" 
    
    def __getattr__(self, name):
        # Check if the attribute exists on the container itself (e.g., extensions)
        if hasattr(self.__class__, name):
            attr = getattr(self.__class__, name)
            # If the attribute is a descriptor, call its __get__ method
            if hasattr(attr, '__get__'):
                return attr.__get__(self, type(self))
            return attr  # Otherwise, return the attribute directly
        # Delegate to child OPs for group operations
        return [getattr(w, name) for w in self]
    
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
                    result = obj(*args) if args else obj()
                    if isinstance(obj, type):  # Class instantiation
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
                        # For callable results (functions), bind as method
                        setattr(type(self), attr_name, types.MethodType(result, self))
                else:
                    setattr(type(self), attr_name, obj)  # Attach class type or function
            except Exception as e:
                raise RuntimeError(f"Failed to load and attach from DAT {dat.path}: {e}") from e
            
            # Persist extension in storage (serializable)
            node = hierarchical_storage.get_node(self._opr._OProxies, self._dictPath)
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
            log(f"Non-persistent extension '{attr_name}' added to {self._dictPath}; won't survive project reload or extension re-init\n"
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
            detail (str): The level of detail ('full', 'minimal', 'dev'); default is 'full'.
            asDict (bool): If True, return the raw dictionary instead of printing; default is False.
        Returns:
            dict or None: Raw storage dicts if asDict=True, otherwise None.
        """
        # Determine the root opr instance
        opr_instance = self if hasattr(self, 'storage') else getattr(self, '_opr', None)
        if not opr_instance or not hasattr(opr_instance, 'storage'):
            log("<OProxy [WARNING]> No storage or parent reference available for tree", level='warning')
            return None if asDict else None

        # Get raw storage dictionaries
        oproxies = opr_instance.storage['OProxies'].getRaw()
        oproxies_detailed = opr_instance.storage['_OProxies'].getRaw()

        # Determine starting path
        start_path = []
        if hasattr(self, '_dictPath') and self._dictPath:
            start_path = self._dictPath.split('.')
        if child:
            start_path.extend(child.split('.'))

        # Validate starting path
        current_oproxies = oproxies
        current_oproxies_detailed = oproxies_detailed
        for i, segment in enumerate(start_path):
            if i > 0:
                current_oproxies = current_oproxies.get('Children', {})
                current_oproxies_detailed = current_oproxies_detailed.get('Children', {})
            if segment not in current_oproxies or segment not in current_oproxies_detailed:
                log(f"<OProxy [WARNING]> Child '{child}' not found in storage at path {'.'.join(start_path[:i+1])}", level='warning')
                return None if asDict else None
            current_oproxies = current_oproxies[segment]
            current_oproxies_detailed = current_oproxies_detailed[segment]

        # Return raw dictionaries if asDict=True
        if asDict:
            return {'OProxies': current_oproxies, '_OProxies': current_oproxies_detailed}

        # Build and print the tree
        node_name = start_path[-1] if child else None
        tree_str = format_ascii_tree(
            node_oproxies=current_oproxies,
            node_oproxies_detailed=current_oproxies_detailed,
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