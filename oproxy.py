# oproxy.dat 
from TDStoreTools import StorageManager
import TDFunctions as TDF
import td
import types  # For MethodType in extension binding
import ast_mod  # Import ast_mod for extraction

# Imports from modular DATs
log = mod('utils').log
_update_storage = mod('utils')._update_storage
OPContainer = mod('OPContainer').OPContainer
OP_Proxy = mod('OP_Proxy').OP_Proxy
proxy_add = mod('proxy_methods').proxy_add
proxy_remove = mod('proxy_methods').proxy_remove
proxy_refresh = mod('proxy_methods').proxy_refresh
hierarchical_storage = mod('hierarchical_storage')

class opr:
    def __init__(self, ownerComp):
        """
        Initializes the OProxy system, setting up storage, restoring proxies, and applying extensions.
        Persistent extensions are re-bound after full tree restoration for consistency across reloads.
        """
        self.ownerComp = ownerComp
        
        # Initialize StorageManager for persistent proxies
        storedItems = [
            {'name': 'OProxies', 'default': {}, 'readOnly': False,
             'property': True, 'dependable': True},
        ]
        self.storage = StorageManager(self, ownerComp, storedItems)
        
        stored_proxies = self.OProxies.getRaw()
        for name, data in stored_proxies.items():
            # Convert dict-based OPs to list for _add
            ops_list = [op_data['op'] for op_data in data['OPs'].values()]
            
            # Skip empty main containers during restore
            if not ops_list:
                continue
                
            proxy = self._add(name, ops_list, restore=True)
            self._restore_children(proxy, data['Children'])
            proxy._refresh()
        
        # Apply persistent extensions after full restore
        self._apply_extensions()
        
        # Vestige log removed as per request

    def _restore_children(self, parent_proxy, children_data):
        for child_name, child_data in children_data.items():
            # Convert dict-based OPs to list for _add
            ops_list = [op_data['op'] for op_data in child_data['OPs'].values()]
            
            # Handle empty child containers (hybrid containers with no OPs)
            if not ops_list:
                # Skip empty containers during restore - they will be created on-demand via __call__
                # when the user accesses them
                continue
            else:
                child_proxy = parent_proxy._add(child_name, ops_list, restore=True)
                self._restore_children(child_proxy, child_data['Children'])

    def _add(self, name, op, parent=None, restore=True):
        # Type/validation checks and normalization
        if not isinstance(name, str) or not name:
            raise TypeError(f"Expected 'name' to be a non-empty str, but got {type(name).__name__}")
        
        def to_op(item):
            if item is None:
                raise ValueError("Provided item is None; ensure the OP exists and op() resolves correctly")
            if isinstance(item, td.OP):
                if not item.valid:
                    raise ValueError(f"Provided OP is not valid: {item}")
                return item
            elif isinstance(item, str):
                resolved = td.op(item)
                if resolved is None:
                    log(f"OP not found for path/name: '{item}'")
                    raise ValueError(f"String '{item}' does not resolve to a valid OP (resolved to None)")
                if not isinstance(resolved, td.OP) or not resolved.valid:
                    log(f"Invalid OP resolved for '{item}': {resolved}")
                    raise ValueError(f"String '{item}' resolves to an invalid OP")
                return resolved
            else:
                raise TypeError(f"Expected item to be str or OP, but got {type(item).__name__}")
        
        if isinstance(op, (td.OP, str)):
            op = [to_op(op)]  # Normalize to list
        elif isinstance(op, list):
            if not op:
                raise ValueError("Provided 'op' list cannot be empty")
            op = [to_op(item) for item in op]
        else:
            raise TypeError(f"Expected 'op' to be str, OP, or list thereof, but got {type(op).__name__}")
        
        # Deduplicate input ops (preserve order) 
        seen = set()
        unique_op = []
        for o in op:
            if o not in seen:
                unique_op.append(o)
                seen.add(o)
            else:
                log(f"Duplicate OP in input, skipping: {o.path}")
        op = unique_op
        if not op:
            return None  # No ops to add, return None or raise?
        
        attach_to = parent or self
        if hasattr(attach_to, name):
            log(f"'{name}' already exists skipping...")
            proxy_instance = getattr(attach_to, name)
            
            # Inline addition (from proxy_add)
            current_ops = {w.op for w in proxy_instance}
            to_add = [o for o in op if o not in current_ops]
            if to_add:
                for o in to_add:
                    wrapped = OP_Proxy(o)
                    proxy_instance.append(wrapped)
                    proxy_instance._by_name_or_path[o.name] = wrapped
                    proxy_instance._by_name_or_path[o.path] = wrapped
                _update_storage(proxy_instance)
            else:
                log("No new OPs to add after dedup")
        else:
            # Metaprogram a dynamic subclass with the given name, inheriting methods
            class_dict = {
                '_add': lambda self, name, op, restore=True: self._opr._add(name, op, parent=self, restore=restore),
                '_remove': proxy_remove,
                '_refresh': proxy_refresh
            }
            DynamicProxyClass = type(name, (OPContainer,), class_dict)
            
            # Instantiate and attach to the extension instance
            proxy_instance = DynamicProxyClass(op)
            proxy_instance._parent = parent or self
            setattr(attach_to, name, proxy_instance)
            
            # Set back-references for storage updates
            proxy_instance._opr = self
            proxy_instance._proxy_name = name
            
            # Set _dictPath
            if parent:
                proxy_instance._dictPath = f"{parent._dictPath}.{name}"
            else:
                proxy_instance._dictPath = name
            
            # Persist to storage using hierarchical structure
            hierarchical_storage.init_node(self.OProxies, proxy_instance._dictPath)
            node = hierarchical_storage.get_node(self.OProxies, proxy_instance._dictPath)
            node['OPs'] = {}
            for o in op:
                initial_name = o.name
                # Handle duplicate initial names
                if initial_name in node['OPs']:
                    i = 1
                    while f"{initial_name}_{i}" in node['OPs']:
                        i += 1
                    initial_name = f"{initial_name}_{i}"
                node['OPs'][initial_name] = {'op': o}
        
        return proxy_instance  # Return for chaining

    def _apply_extensions(self):
        """
        Traverses the proxy tree and re-binds persistent extensions from storage using ast_mod.
        For each extension, extracts the class or function from the specified DAT and attaches it to the proxy.
        Handles errors gracefully by logging and skipping invalid extensions.
        Limitations: Classes/functions must be top-level defs in the DAT; nested definitions not supported.
        If DAT is missing/renamed, binding fails (use _refresh for path updates).
        """
        def apply(node, path):
            proxy = self.get_proxy_by_path('.'.join(path))
            if not proxy:
                log(f"Proxy not found for path {'.'.join(path)}; skipping extensions")
                return
            extensions = [dict(ext) for ext in list(node.get('Extensions', []))]
            for ext in extensions:
                try:
                    dat_path = ext['dat_path']
                    dat_op = op(dat_path)
                    if not dat_op or not isinstance(dat_op, td.DAT):
                        raise ValueError(f"DAT not found or invalid at {dat_path}")
                    cls = ext.get('cls')
                    func = ext.get('func')
                    call = ext.get('call', False)
                    args = ext.get('args')
                    # Convert args to a standard list if it’s a TouchDesigner storage object
                    if args is not None and not isinstance(args, (tuple, list)):
                        try:
                            args = list(args)
                        except Exception as e:
                            raise TypeError(f"Invalid args type for extension '{ext['name']}': failed to convert to list: {e}")
                    if args and not isinstance(args, (tuple, list)):
                        raise TypeError(f"Invalid args type for extension '{ext['name']}': must be tuple or list")
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
                            setattr(type(proxy), ext['name'], InstanceDelegate(result))
                        else:
                            setattr(type(proxy), ext['name'], types.MethodType(obj, proxy))
                    else:
                        setattr(type(proxy), ext['name'], obj)
                    log(f"Applied extension '{ext['name']}' to {'.'.join(path)} from {dat_path}")
                except Exception as e:
                    log(f"Failed to apply extension '{ext.get('name', 'unknown')}' to {'.'.join(path)}: {e}")

        hierarchical_storage.traverse_tree(self.OProxies.getRaw(), apply)

    def _remove(self, path, to_remove=None):
        if to_remove is None:  # Remove container at path
            proxy = self.get_proxy_by_path(path)
            if proxy:
                proxy._remove(to_remove=None)
        else:  # Remove OP from container at path
            proxy = self.get_proxy_by_path(path)
            if proxy:
                proxy._remove(to_remove=to_remove)
        
    def get_proxy_by_path(self, path):
        if isinstance(path, str):
            path = path.split('.')
        
        current = self
        for segment in path:
            current = getattr(current, segment, None)
            if not current:
                return None
        return current

    def _refresh(self):
        """
        Refreshes the proxy tree by syncing OP paths with storage and re-applying extensions.
        Updates DAT paths in OProxies if renamed and re-runs _apply_extensions for consistency.
        """
        def update_paths(node, path):
            proxy = self.get_proxy_by_path('.'.join(path))
            if proxy and 'OPs' in node:
                for name, data in list(node['OPs'].items()):
                    op = data['op']
                    current_path = op.path
                    log(f"OP {name} in {'.'.join(path)}: {current_path}")
            # Update DAT paths in Extensions
            if 'Extensions' in node:
                for ext in node['Extensions']:
                    dat_path = ext.get('dat_path')
                    if dat_path:
                        dat_op = op(dat_path)
                        if dat_op and dat_op.path != dat_path:
                            ext['dat_path'] = dat_op.path
                            log(f"Updated DAT path for extension '{ext['name']}' in {'.'.join(path)}: {dat_op.path}")

        # Update paths in storage
        hierarchical_storage.traverse_tree(self.OProxies.getRaw(), update_paths)

        # Re-apply extensions after path updates
        self._apply_extensions()

    def _tree(self, child=None, detail='full', asDict=False):
        """
        Print or return an ASCII-style tree of the proxy structure from the root.
        Args:
            child (str, optional): The child node to start printing from (e.g., 'chops').
            detail (str): The level of detail ('full', 'minimal'); default is 'full'.
            asDict (bool): If True, return the raw dictionary instead of printing; default is False.
        Returns:
            str or dict: The formatted tree string or raw storage dict if asDict=True.
        """
        return OPContainer._tree(self, child, detail, asDict)

    def _clear(self):
        """
        Clear the entire OProxy dictionary by removing all top-level containers.
        This provides a clean way to reset the entire proxy system.
        """
        log("Clearing entire OProxy dictionary...")
        oproxies_raw = self.OProxies.getRaw()
        top_level_names = list(oproxies_raw.keys())
        
        for name in top_level_names:
            try:
                self._remove(name)
                log(f"Removed container '{name}'")
            except Exception as e:
                log(f"Error removing container '{name}': {e}", level='warning')
                # Force remove from storage if proxy removal fails
                try:
                    hierarchical_storage.remove_node(self.OProxies, name, recursive=True)
                    log(f"Force removed container '{name}' from storage")
                except Exception as e2:
                    log(f"Error force removing container '{name}': {e2}", level='error')
        
        log("OProxy dictionary cleared")
        return self