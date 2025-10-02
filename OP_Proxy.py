# OP_Proxy.DAT
import td
import types 
import ast_mod

hierarchical_storage = mod('hierarchical_storage')
log = mod('utils').log
td_isinstance = mod('utils').td_isinstance  # Import centralized TD type checking

class OP_Proxy:
    """ 
    Wrapper for individual OPs, allowing per-item and all-items extensions.
    
    DEPRECATED: This class is being phased out in favor of hybrid OPContainer
    that can function as both proxy and container. Use OPContainer instead.
    """
    def __init__(self, op):
        self._op = op  # The wrapped TD OP
        self._custom_attrs = {}  # Per-instance custom attributes/methods
        self._parent_container = None  # Set during addition to container for removal back-ref
    
    @property
    def op(self):
        return self._op  # Access the original OP 
    
    def __getattr__(self, name):
        # First check per-instance customs, then class-level (via self.__class__), then delegate to OP
        if name in self._custom_attrs:
            attr = self._custom_attrs[name]
            if callable(attr):
                return lambda *args, **kwargs: attr(self, *args, **kwargs)  # Bind self if method
            return attr
        elif hasattr(self.__class__, name):  # Class-wide extensions
            return getattr(self.__class__, name)
        else:
            return getattr(self._op, name)  # Delegate to OP (e.g., .par, .path)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):  # Internal attrs
            super().__setattr__(name, value)
        else:
            self._custom_attrs[name] = value  # Per-instance set

    def __getitem__(self, key):
        return self.op[key]  # Delegate subscription (e.g., for CHOP channels)
    
    def __setitem__(self, key, value):
        self.op[key] = value  # Delegate assignment (works for DATs; errors for CHOPs etc.)
    
    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False):
        """
        Extend the proxy instance with an attribute or method using ast_mod for DAT-based extraction.
        'cls' or 'func' specifies the class or function name to extract from 'dat'; if neither, 'value' is used directly.
        'args' is a tuple/list of positional arguments for instantiation/calling when call=True.
        """
        # Validate parameters
        if not (cls or func) and dat is not None:
            raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
        if (cls and func) or (not cls and not func):
            raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
        
        if dat:
            # Use td_isinstance for DAT validation with string path support
            try:
                dat = td_isinstance(dat, 'dat', allow_string=True)
            except (TypeError, ValueError) as e:
                raise
            
            try:
                obj = ast_mod.Main(cls=cls, func=func, op=dat)
                if call and args is not None and not isinstance(args, (tuple, list)):
                    raise TypeError("args must be a tuple or list of positional arguments when call=True")
                
                if call:
                    if isinstance(obj, type):  # Class instantiation
                        result = obj(*args) if args else obj()
                        self._custom_attrs[attr_name] = result
                    else:  # Function
                        # Bind the function as a method and call it with self
                        bound_method = types.MethodType(obj, self)
                        result = bound_method(*args) if args else bound_method()  # Call with self
                        self._custom_attrs[attr_name] = bound_method  # Store bound method
                else:
                    self._custom_attrs[attr_name] = obj  # Store class or unbound function
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
            # Non-persistent: attach directly to custom_attrs, skip storage
            log(f"Non-persistent extension '{attr_name}' added to {self._dictPath}; won't survive project reload or extension re-init", level='warning')
            self._custom_attrs[attr_name] = cls or func  # Use cls/func directly if no dat
        
        log(f"Extension '{attr_name}' added successfully", process='_extend')
        return self  # Allow chaining

    def _remove(self):
        if self._parent_container:
            self._parent_container._remove(to_remove=self._op)  # Delegate to parent's remove for OP pruning
        
        return self  # Or None if removed

    # Add these to match the string representation of the wrapped OP
    def __str__(self):
        return str(self._op)
    
    def __repr__(self):
        return repr(self._op)