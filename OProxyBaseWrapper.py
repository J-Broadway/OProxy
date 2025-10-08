# OProxyBaseWrapper.py - Composite Pattern for OProxy
from abc import ABC, abstractmethod
import td
import types
import time
import traceback
import inspect
import json
import keyword
from utils import td_isinstance

''' LLM Notes:
Comments that begin with #! are meant to be updated dynamically when incongruencies
in comment vs codebase are found.
'''

# Import utils module for storage functions
utils = mod('utils')
Log = parent.opr.Log # Use this instead of self.Log() <-- will return errors.

class OProxyBaseWrapper(ABC):
    """Abstract Component: Common interface for leaves and composites."""

    def __init__(self, path="", parent=None):
        self._path = path  # Hierarchical path (e.g., 'effects.advanced')
        self._parent = parent

    def _find_root(self):
        """Internal method: Traverse up parent chain to find root container."""
        current = self
        while current._parent is not None:
            current = current._parent
        return current

    @abstractmethod
    def _add(self, name, op):
        """Add a child (OP or sub-container)."""
        pass

    @abstractmethod
    def _remove(self, name=None):
        """Remove self, named child, or extension. Implementation varies by type."""
        pass

    @abstractmethod
    def _tree(self):
        """Return a string representation of the hierarchy."""
        pass

    @abstractmethod
    def _refresh(self, target=None):
        """Abstract refresh method - implemented by subclasses."""
        pass

    @abstractmethod
    def _extend(self, attr_name=None, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False, returnObj=False):
        """
        Extend the proxy object with an attribute or method from a Text DAT.

        Parameters:
        - attr_name (str): Name for the extension (defaults to func or cls name if not provided)
        - cls (str): Class name to extract from DAT
        - func (str): Function name to extract from DAT
        - dat (DAT): Text DAT containing the extension (required)
        - args (tuple|list): Arguments for instantiation/calling when call=True
        - monkey_patch (bool): Allow overwriting existing attributes

        Returns:
        - self by default for chaining
        - The created extension object if returnObj=True

        Raises:
        - ValueError: Invalid parameters, naming conflicts, extraction failures
        """
        pass

    def _clear(self, flush_logger=True):
        """
        Clear all stored OProxy data and reload empty hierarchy.
        Only works on root containers.

        Args:
            flush_logger (bool): Whether to flush the logger. Defaults to True.

        Raises:
            RuntimeError: If called on non-root container
        """
        root = self._find_root()
        if root is not self:
            # Delegate to root
            return root._clear(flush_logger)
        else:
            # This should be implemented by the root class
            raise NotImplementedError("_clear must be implemented by root container class")

    def _get_storage_branch(self, keys=None):
        """
        Get the storage branch dict for this object.
        Private helper for _storage method.
        """
        root = self._find_root()
        if hasattr(root, 'OProxies'):
            storage = root.OProxies.getRaw() if hasattr(root.OProxies, 'getRaw') else dict(root.OProxies)
        else:
            raise RuntimeError("No storage found")

        if self._path == "":
            if isinstance(self, OProxyContainer) and self.is_root:
                branch = storage
            elif isinstance(self, OProxyExtension):
                if not hasattr(self, '_extension_name'):
                    raise AttributeError("Extension has no _extension_name")
                parent_branch = self.parent._get_storage_branch(keys=None)
                if 'extensions' not in parent_branch:
                    raise KeyError("No extensions in parent")
                if self._extension_name not in parent_branch['extensions']:
                    raise KeyError(self._extension_name)
                branch = parent_branch['extensions'][self._extension_name]
            else:
                raise RuntimeError("Empty path for non-root non-extension")
        else:
            path_segments = self._path.split('.')
            branch = storage
            for segment in path_segments[:-1]:
                if segment not in branch['children']:
                    raise KeyError(segment)
                branch = branch['children'][segment]
            last = path_segments[-1]
            if isinstance(self, OProxyContainer):
                if last not in branch['children']:
                    raise KeyError(last)
                branch = branch['children'][last]
            elif isinstance(self, OProxyLeaf):
                if last not in branch['ops']:
                    raise KeyError(last)
                branch = branch['ops'][last]
            else:
                raise TypeError("Unsupported type for path navigation")

        if keys is not None:
            if isinstance(keys, str):
                if keys not in branch:
                    raise KeyError(f"'{keys}' not found")
                branch = branch[keys]
            elif isinstance(keys, list):
                result = {}
                for k in keys:
                    if k not in branch:
                        raise KeyError(f"'{k}' not found")
                    result[k] = branch[k]
                branch = result
            else:
                raise TypeError("keys must be str or list of str")

        return branch

    # Shared proxy methods (implemented in subclasses)
    def __getattr__(self, name):
        raise NotImplementedError

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            raise NotImplementedError

    @property
    def path(self):
        return self._path

    @property
    def parent(self):
        return self._parent

class OProxyLeaf(OProxyBaseWrapper):
    """Leaf: Proxies a single OP."""

    def __init__(self, op, path="", parent=None):
        super().__init__(path, parent)
        self._op = td.op(op) if isinstance(op, str) else op
        if not self._op or not self._op.valid:
            raise ValueError(f"Invalid OP: {op}")
        self._extensions = {}  # Extensions applied to this OP

    def _add(self, name, op):
        raise NotImplementedError("Cannot add to a leaf")

    def _remove(self):
        """
        Remove this leaf from its parent container.

        This enables direct leaf removal: opr.items('op1')._remove()

        Future: When extensions are implemented, this will also clean up
        any extensions associated with this leaf.
        """
        if self._parent is None:
            Log("Cannot remove leaf - no parent container", status='warning', process='_remove')
            return self

        # Find this leaf in parent's children
        parent_container = self._parent
        my_name = None
        for child_name, child in parent_container._children.items():
            if child is self:
                my_name = child_name
                break

        if my_name is not None:
            Log(f"Removing leaf '{my_name}' from parent container", status='debug', process='_remove')
            del parent_container._children[my_name]

            # Find root by traversing up parent chain (avoid name mangling issues)
            root = parent_container
            while root._parent is not None:
                root = root._parent

            # Update storage
            if hasattr(root, 'OProxies'):
                utils.remove(self, root.OProxies, parent_container.path)
                root._save_to_storage()

            # Future: Clean up extensions associated with this leaf
            # This will be implemented when _extend() and extensions are added
            # utils.log(f"DEBUG _remove: TODO - Clean up extensions for leaf '{my_name}'")

        else:
            Log("Could not find leaf in parent container children", status='warning', process='_remove')

        return self

    def _tree(self):
        return f"Leaf: {self._op.name} ({self._op.path})"

    def _refresh(self, target=None):
        """Refresh leaf - check for name changes and refresh extensions"""
        try:
            # Check for name changes and update parent's children dictionary if needed
            if self._parent:
                # Find current key for this leaf in parent's children
                current_key = None
                for child_name, child in self._parent._children.items():
                    if child is self:
                        current_key = child_name
                        break

                if current_key and current_key != self._op.name:
                    Log(f"Leaf OP name changed from '{current_key}' to '{self._op.name}', updating parent mapping", status='info', process='_refresh')
                    # Preserve order when renaming key
                    children = self._parent._children
                    keys = list(children.keys())
                    values = list(children.values())
                    index = keys.index(current_key)
                    keys[index] = self._op.name
                    children.clear()
                    children.update(zip(keys, values))
                    # Update path to reflect new name
                    self._path = f"{self._parent.path}.{self._op.name}" if self._parent.path else self._op.name
                    if self._parent:
                        self._find_root()._update_storage()

            self._refresh_extensions(target)
        except Exception as e:
            Log(f"Leaf refresh failed for {self.path}: {e}\n{traceback.format_exc()}", status='error', process='_refresh')

    def _refresh_extensions(self, target=None):
        """Load stored extension metadata and re-extract from DATs for this leaf."""
        if not self._parent:
            return

        # Get the stored data for this leaf from parent's storage
        stored_data = self._parent._get_stored_container_data()
        if not stored_data:
            return

        ops_data = stored_data.get('ops', {})

        # Find this leaf in stored ops
        leaf_name = None
        for stored_name, op_info in ops_data.items():
            if isinstance(op_info, dict):
                stored_path = op_info.get('path', '')
                if stored_path == self._op.path:
                    leaf_name = stored_name
                    extensions_data = op_info.get('extensions', {})
                    break

        if not leaf_name or not extensions_data:
            return

        mod_ast = mod('mod_AST')

        for ext_name, metadata in extensions_data.items():
            try:
                # New: Add fallback
                dat_path = metadata['dat_path']
                dat_op = metadata.get('dat_op')

                dat = td.op(dat_path) if dat_path else None
                if not (dat and dat.valid) and dat_op and dat_op.valid:
                    dat = dat_op
                    Log(f"Using stored DAT for leaf extension '{ext_name}' on '{self.path}' (path may have changed)", status='debug', process='_refresh')

                if dat and dat.valid:
                    if dat_path != dat.path:
                        Log(f"Leaf extension '{ext_name}' DAT path changed to '{dat.path}', updating metadata", status='debug', process='_refresh')
                        metadata['dat_path'] = dat.path
                        metadata['dat_op'] = dat
                        changed = True
                    else:
                        changed = False

                    # Then existing re-extract, but use dat for op=
                    actual_obj = mod_ast.Main(
                        cls=metadata['cls'],
                        func=metadata['func'],
                        source_dat=dat,  # Use resolved dat
                        log=Log
                    )

                    # Re-wrap in factory template
                    extension = OProxyExtension(actual_obj, self,
                                              source_dat=metadata['dat_path'],
                                              metadata=metadata)

                    # Store extension name for removal purposes
                    extension._extension_name = ext_name

                    # Apply to parent object
                    setattr(self, ext_name, extension)

                    # Store in registry
                    self._extensions[ext_name] = extension

                    # After setting extension
                    if changed and self._parent:
                        self._find_root()._update_storage()

                else:
                    Log(f"Could not resolve DAT for extension '{ext_name}' on leaf '{self.path}'", status='warning', process='_refresh')
                    continue

            except Exception as e:
                Log(f"Failed to reload extension '{ext_name}' on leaf '{self.path}': {e}\n{traceback.format_exc()}", status='warning', process='_refresh')

    def __getattr__(self, name):
        return getattr(self._op, name)

    def __setattr__(self, name, value):
        if name.startswith('_') or name == '_op':
            super().__setattr__(name, value)
        else:
            setattr(self._op, name, value)

    def __str__(self):
        return str(self._op)

    def __repr__(self):
        return repr(self._op)

    def _extend(self, attr_name=None, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False, returnObj=False):
        """
        Extend the leaf with an attribute or method from a Text DAT.

        Leaf extensions are bound to the leaf instance (self refers to the OProxyLeaf).
        """
        try:
            # Parameter validation
            if not (cls or func) and dat is not None:
                raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
            if (cls and func) or (not cls and not func):
                raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
            if not dat:
                raise ValueError("'dat' parameter is required for extensions")

            # Auto-default attr_name to func or cls name if not provided
            if attr_name is None:
                attr_name = func or cls

            # Import AST extraction module
            mod_ast = mod('mod_AST')

            # Validate DAT
            try:
                dat = td_isinstance(dat, 'textdat', allow_string=True)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid DAT: {e}")

            # Check for naming conflicts
            if hasattr(self, attr_name) and not monkey_patch:
                existing_attr = getattr(self, attr_name)
                if not isinstance(existing_attr, OProxyExtension):
                    raise ValueError(f"Name '{attr_name}' conflicts with existing method/property. "
                                   f"To overwrite, use monkey_patch=True.")

            # Extract the actual object
            try:
                actual_obj = mod_ast.Main(cls=cls, func=func, source_dat=dat, log=Log)
            except Exception as e:
                dat_op = dat if isinstance(dat, td.OP) else op(dat)
                path_str = dat_op.path if dat_op is not None else dat
                raise RuntimeError(f"Failed to extract from DAT {path_str}: {e}") from e

            # Prepare metadata
            metadata = {
                'cls': cls, 'func': func, 'dat_path': dat.path,
                'dat_op': dat,  # Add this for rename fallback
                'args': args, 'call': call, 'created_at': time.time()
            }

            # Create extension wrapper
            extension = OProxyExtension(actual_obj, self, dat, metadata)

            # Store extension name for removal purposes
            extension._extension_name = attr_name

            # Handle call parameter
            if call:
                if args is not None and not isinstance(args, (tuple, list)):
                    raise TypeError("args must be a tuple or list of positional arguments when call=True")

                if call:
                    if isinstance(actual_obj, type):  # Class instantiation
                        result = actual_obj(*args) if args else actual_obj()
                        extension = OProxyExtension(result, self, dat, metadata)
                        extension._extension_name = attr_name
                    else:  # Function call
                        bound_method = types.MethodType(actual_obj, self)
                        result = bound_method(*args) if args else bound_method()
                        extension = OProxyExtension(bound_method, self, dat, metadata)
                        extension._extension_name = attr_name

            # Apply extension to parent object (make it accessible)
            setattr(self, attr_name, extension)

            # Store in internal registry for management
            self._extensions[attr_name] = extension

            # Update storage by finding root and updating
            root = self
            while root._parent is not None:
                root = root._parent
            if hasattr(root, 'OProxies'):
                root._update_storage()

            Log(f"Extension '{attr_name}' added to leaf '{self.path}'", status='info', process='_extend')
            if returnObj:
                return extension
            else:
                return self
        except Exception as e:
            Log(f"Extension creation failed for '{attr_name}': {e}\n{traceback.format_exc()}", status='error', process='_extend')
            raise

    def _storage(self, keys=None, as_dict=False):
        """
        Public method to view serialized storage branch. Intended for public usage, not internal; use _store() for serialization.

        Args:
            keys: Optional keys to filter the returned data
            as_dict: If True, return dictionary object instead of JSON string

        Returns:
            Dictionary object if as_dict=True, JSON string otherwise
        """
        branch = self._get_storage_branch(keys)
        serialized = utils.make_serializable(branch)
        if as_dict:
            Log(f"Storage branch for leaf '{self.path or 'root'}' returned as dictionary", status='info', process='_storage')
            return serialized
        else:
            output = json.dumps(serialized, indent=4)
            Log(f"Storage branch for leaf '{self.path or 'root'}'\n\"{self.path or 'root'}\" : {output}", status='info', process='_storage')
            return output

    @property
    def op(self):
        return self._op


class OProxyExtension(OProxyBaseWrapper):
    """
    Factory template for all OProxy extensions. Provides consistent interface,
    delegation to extracted objects, and metadata tracking.

    Extensions will be able to be removed independently of their parent containers/leafs.
    """

    def __init__(self, actual_obj, parent, source_dat=None, metadata=None):
        """
        Initialize extension with extracted object and metadata.

        Args:
            actual_obj: The extracted class/function from AST module
            parent: Parent container or leaf this extension belongs to
            source_dat: Original DAT object where extension was defined
            metadata: Extension metadata (cls, func, dat_path, etc.)
        """
        super().__init__(path="", parent=parent)
        self._actual = actual_obj  # The extracted class/function
        self._source_dat = source_dat
        self._metadata = metadata or {}
        self._extensions = {}  # Initialize extensions dict for hierarchy

        # Dynamically copy attributes from actual object for delegation
        self._copy_attributes_from_actual()

    def _copy_attributes_from_actual(self):
        """Copy non-private attributes from the actual object to enable delegation."""
        for attr_name in dir(self._actual):
            if not attr_name.startswith('_') and not hasattr(self, attr_name):
                try:
                    attr = getattr(self._actual, attr_name)
                    setattr(self, attr_name, attr)
                except (AttributeError, TypeError):
                    # Skip attributes that can't be copied
                    pass

    def __getattr__(self, name):
        """Delegate attribute access to the actual object."""
        if name.startswith('_'):
            # Don't delegate private attributes
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        try:
            return getattr(self._actual, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __call__(self, *args, **kwargs):
        """Allow calling if the actual object is callable."""
        try:
            if callable(self._actual):
                if isinstance(self._actual, type):  # Class instantiation
                    instance = self._actual(*args, **kwargs)
                    # For extensions wrapping classes, replace with the instance
                    # so subsequent attribute access works on the instance
                    self._actual = instance
                    return instance
                elif inspect.isfunction(self._actual) or inspect.ismethod(self._actual):
                    sig = inspect.signature(self._actual)
                    params = list(sig.parameters.values())
                    if params and params[0].name == 'self':
                        # Bind the function to the parent container as 'self'
                        bound_method = types.MethodType(self._actual, self._parent)
                        return bound_method(*args, **kwargs)
                    else:
                        # Call without binding (static function)
                        return self._actual(*args, **kwargs)
                else:
                    # Other callables (e.g., instances with __call__)
                    return self._actual(*args, **kwargs)
            else:
                raise TypeError(f"'{self.__class__.__name__}' object is not callable")
        except Exception as e:
            Log(f"Error calling extension: {e}\n{traceback.format_exc()}", status='error', process='__call__')
            raise

    @property
    def extension_info(self):
        """Access metadata about this extension."""
        return {
            'source_dat': self._source_dat,
            'parent': self._parent,
            'metadata': self._metadata,
            'actual_type': type(self._actual).__name__,
            'is_callable': callable(self._actual)
        }

    def _build_storage_structure(self):
        """Build hierarchical structure for this extension's extensions."""
        return {
            name: {
                'metadata': ext._metadata,
                'extensions': ext._build_storage_structure()
            } for name, ext in self._extensions.items()
        }

    def _remove(self):
        """
        Remove this extension from its parent and recursively clean up nested extensions.

        Implementation:
        - Recursively remove all child extensions first
        - Remove extension from parent's _extensions registry
        - Remove extension attribute from parent object
        - Clean up extension data from storage
        - Update storage persistence
        """
        # First, recursively remove all child extensions
        extensions_to_remove = list(self._extensions.keys())  # Create a copy of keys
        for ext_name in extensions_to_remove:
            try:
                child_extension = self._extensions[ext_name]
                Log(f"Recursively removing child extension '{ext_name}' from extension '{getattr(self, '_extension_name', 'unknown')}'", status='debug', process='_remove')
                child_extension._remove()
            except Exception as e:
                Log(f"Failed to remove child extension '{ext_name}': {e}", status='error', process='_remove')
                continue

        # Now remove this extension from its parent
        if self._parent:
            # Remove from parent's extension registry
            if hasattr(self._parent, '_extensions') and hasattr(self, '_extension_name'):
                if self._extension_name in self._parent._extensions:
                    del self._parent._extensions[self._extension_name]

            # Remove extension attribute from parent
            if hasattr(self._parent, self._extension_name):
                delattr(self._parent, self._extension_name)

            # Clean up storage (find root and update storage)
            try:
                root = self._parent
                while root and root._parent is not None:
                    root = root._parent
                if hasattr(root, 'OProxies'):
                    root._update_storage()
            except Exception as e:
                Log(f"Failed to update storage during extension removal: {e}", status='error', process='_remove')

        Log(f"Extension '{getattr(self, '_extension_name', 'unknown')}' and all nested extensions removed successfully", status='info', process='_remove')
        return self

    def _add(self, name, op):
        """Extensions cannot add children."""
        raise NotImplementedError("Extensions cannot add children")

    def _tree(self):
        """Return string representation of extension."""
        return f"Extension: {self.__class__.__name__}"

    def _refresh(self, target=None):
        """Refresh extension state and re-extract from source DAT"""
        try:
            # Check source DAT validity and re-extract if needed
            self._refresh_source_dat()
            # Refresh any sub-extensions (future-proofing)
            self._refresh_extensions(target)
        except Exception as e:
            Log(f"Extension refresh failed for {getattr(self, '_extension_name', 'unknown')}: {e}\n{traceback.format_exc()}", status='error', process='_refresh')

    def _refresh_source_dat(self):
        """Check and refresh the source DAT connection"""
        if not hasattr(self, '_source_dat') or not hasattr(self, '_metadata'):
            return  # No source DAT to refresh

        metadata = self._metadata
        stored_path = metadata.get('dat_path')
        stored_dat = metadata.get('dat_op')

        # Try current path first
        dat = td.op(stored_path) if stored_path else None

        # Fall back to stored DAT object
        if not (dat and dat.valid) and stored_dat and stored_dat.valid:
            dat = stored_dat
            Log(f"Using stored DAT object for extension '{getattr(self, '_extension_name', 'unknown')}' (path may have changed)", status='debug', process='_refresh')

        if dat and dat.valid:
            # Check for path changes
            if stored_path != dat.path:
                Log(f"Extension '{getattr(self, '_extension_name', 'unknown')}' source DAT path changed from '{stored_path}' to '{dat.path}'", status='info', process='_refresh')
                metadata['dat_path'] = dat.path
                metadata['dat_op'] = dat
                changed = True
            else:
                changed = False

            # Re-extract the underlying object
            mod_ast = mod('mod_AST')
            actual_obj = mod_ast.Main(
                cls=metadata['cls'],
                func=metadata['func'],
                source_dat=dat,
                log=Log
            )

            # Update the extension's internal object
            self._actual = actual_obj

            # Update storage if path changed
            if changed and self._parent:
                self._find_root()._update_storage()

        else:
            Log(f"Source DAT for extension '{getattr(self, '_extension_name', 'unknown')}' not found or invalid", status='warning', process='_refresh')

    def _refresh_extensions(self, target=None):
        """Load stored extension metadata and recursively refresh sub-extensions."""
        # Get the stored extensions data for this extension
        extensions_data = self._get_stored_extension_data()
        if not extensions_data:
            return

        mod_ast = mod('mod_AST')

        for ext_name, ext_data in extensions_data.items():
            try:
                # Extract metadata and sub-extensions data
                metadata = ext_data.get('metadata', {})
                sub_extensions_data = ext_data.get('extensions', {})

                # Resolve DAT with fallback
                dat_path = metadata.get('dat_path')
                dat_op = metadata.get('dat_op')

                dat = td.op(dat_path) if dat_path else None
                if not (dat and dat.valid) and dat_op and dat_op.valid:
                    dat = dat_op
                    Log(f"Using stored DAT for extension '{ext_name}' on extension '{getattr(self, '_extension_name', 'unknown')}' (path may have changed)", status='debug', process='_refresh')

                if dat and dat.valid:
                    if dat_path and dat_path != dat.path:
                        Log(f"Extension '{ext_name}' DAT path changed to '{dat.path}', updating metadata", status='debug', process='_refresh')
                        metadata['dat_path'] = dat.path
                        metadata['dat_op'] = dat
                        changed = True
                    else:
                        changed = False

                    # Re-extract the actual object
                    actual_obj = mod_ast.Main(
                        cls=metadata.get('cls'),
                        func=metadata.get('func'),
                        source_dat=dat,
                        log=Log
                    )

                    # Create extension wrapper
                    extension = OProxyExtension(actual_obj, self, dat, metadata)
                    extension._extension_name = ext_name

                    # Recursively refresh sub-extensions if any
                    if sub_extensions_data:
                        # Temporarily set the extensions data for recursive refresh
                        extension._temp_extensions_data = sub_extensions_data
                        extension._refresh_extensions()
                        delattr(extension, '_temp_extensions_data')

                    # Apply to parent object
                    setattr(self, ext_name, extension)

                    # Store in registry
                    self._extensions[ext_name] = extension

                    # Update storage if metadata changed
                    if changed:
                        root = self
                        while root and root._parent is not None:
                            root = root._parent
                        if hasattr(root, 'OProxies'):
                            root._update_storage()

                else:
                    Log(f"Could not resolve DAT for extension '{ext_name}' on extension '{getattr(self, '_extension_name', 'unknown')}'", status='warning', process='_refresh')
                    continue

            except Exception as e:
                Log(f"Failed to refresh extension '{ext_name}' on extension '{getattr(self, '_extension_name', 'unknown')}': {e}\n{traceback.format_exc()}", status='error', process='_refresh')
                continue

    def _get_stored_extension_data(self):
        """Get the stored extensions data for this extension from the storage hierarchy."""
        # Find the path to this extension in the storage structure
        path_parts = self._get_extension_storage_path()
        if not path_parts:
            return None

        # Navigate the storage structure
        root = self._find_root()
        if not hasattr(root, 'OProxies'):
            return None

        current_data = root.OProxies.getRaw() if hasattr(root.OProxies, 'getRaw') else dict(root.OProxies)

        # Navigate through the path to find this extension's data
        for part in path_parts[:-1]:  # All parts except the last (which is this extension's name)
            if isinstance(current_data, dict) and part in current_data:
                current_data = current_data[part]
            else:
                return None

        # The last part should be the extensions dict for the parent of this extension
        if isinstance(current_data, dict) and 'extensions' in current_data:
            parent_extensions = current_data['extensions']
            ext_name = path_parts[-1]
            if isinstance(parent_extensions, dict) and ext_name in parent_extensions:
                ext_data = parent_extensions[ext_name]
                if isinstance(ext_data, dict) and 'extensions' in ext_data:
                    return ext_data['extensions']

        return None

    def _get_extension_storage_path(self):
        """Get the path to this extension in the storage hierarchy."""
        path_parts = []
        current = self

        # Walk up the hierarchy collecting extension names
        while current and isinstance(current, OProxyExtension):
            if hasattr(current, '_extension_name'):
                path_parts.insert(0, current._extension_name)
            current = current._parent

        # Now walk up to find the container/leaf path
        container_path = []
        while current and current._parent is not None:
            if hasattr(current, 'path') and current.path:
                container_path.insert(0, current.path)
            current = current._parent

        # Combine container path with extension path
        full_path = container_path + path_parts
        return full_path if full_path else None

    def _extend(self, attr_name=None, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False, max_depth=10, returnObj=False):
        """
        Extend this extension with an attribute or method from a Text DAT.

        Extension extensions are bound to the extension instance (self refers to the OProxyExtension).

        Args:
            max_depth: Maximum nesting depth to prevent infinite recursion (default: 10)
        """
        try:
            # Parameter validation
            if not (cls or func) and dat is not None:
                raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
            if (cls and func) or (not cls and not func):
                raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
            if not dat:
                raise ValueError("'dat' parameter is required for extensions")

            # Auto-default attr_name to func or cls name if not provided
            if attr_name is None:
                attr_name = func or cls

            # Validate attr_name as Python identifier
            if not isinstance(attr_name, str):
                raise ValueError(f"attr_name must be a string, got {type(attr_name).__name__}")
            if not attr_name:
                raise ValueError("attr_name cannot be empty")
            if not attr_name.isidentifier():
                raise ValueError(f"attr_name '{attr_name}' is not a valid Python identifier. "
                               f"Names must contain only letters, digits, and underscores, "
                               f"cannot start with a digit, and cannot contain spaces or special characters. "
                               f"Use underscores instead of spaces (e.g., 'my_extension' instead of 'my extension').")
            if keyword.iskeyword(attr_name):
                raise ValueError(f"attr_name '{attr_name}' is a Python keyword and cannot be used")

            # Check depth limit
            current_depth = self._get_extension_depth()
            if current_depth >= max_depth:
                raise ValueError(f"Maximum extension depth ({max_depth}) exceeded. "
                               f"Current depth: {current_depth}. Cannot extend further.")

            # Check for circular dependencies
            if self._would_create_circular_dependency(cls, func, dat):
                raise ValueError(f"Extending with cls='{cls}', func='{func}' from '{dat}' "
                               f"would create a circular dependency")

            # Import AST extraction module
            mod_ast = mod('mod_AST')

            # Validate DAT
            try:
                dat = td_isinstance(dat, 'textdat', allow_string=True)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid DAT: {e}")

            # Check for naming conflicts
            if hasattr(self, attr_name) and not monkey_patch:
                existing_attr = getattr(self, attr_name)
                if not isinstance(existing_attr, OProxyExtension):
                    raise ValueError(f"Name '{attr_name}' conflicts with existing method/property. "
                                   f"To overwrite, use monkey_patch=True.")

            # Extract the actual object
            try:
                actual_obj = mod_ast.Main(cls=cls, func=func, source_dat=dat, log=Log)
            except Exception as e:
                dat_op = dat if isinstance(dat, td.OP) else op(dat)
                path_str = dat_op.path if dat_op is not None else dat
                raise RuntimeError(f"Failed to extract from DAT {path_str}: {e}") from e

            # Prepare metadata
            metadata = {
                'cls': cls, 'func': func, 'dat_path': dat.path,
                'dat_op': dat,  # Add this for rename fallback
                'args': args, 'call': call, 'created_at': time.time()
            }

            # Create extension wrapper
            extension = OProxyExtension(actual_obj, self, dat, metadata)

            # Store extension name for removal purposes
            extension._extension_name = attr_name

            # Handle call parameter
            if call:
                if args is not None and not isinstance(args, (tuple, list)):
                    raise TypeError("args must be a tuple or list of positional arguments when call=True")

                if call:
                    if isinstance(actual_obj, type):  # Class instantiation
                        result = actual_obj(*args) if args else actual_obj()
                        extension = OProxyExtension(result, self, dat, metadata)
                        extension._extension_name = attr_name
                    else:  # Function call
                        bound_method = types.MethodType(actual_obj, self)
                        result = bound_method(*args) if args else bound_method()
                        extension = OProxyExtension(bound_method, self, dat, metadata)
                        extension._extension_name = attr_name

            # Apply extension to parent object (make it accessible)
            setattr(self, attr_name, extension)

            # Store in internal registry for management
            self._extensions[attr_name] = extension

            # Update storage by finding root and updating
            root = self
            while root and root._parent is not None:
                root = root._parent
            if hasattr(root, 'OProxies'):
                root._update_storage()

            Log(f"Extension '{attr_name}' added to extension '{getattr(self, '_extension_name', 'unknown')}'", status='info', process='_extend')
            if returnObj:
                return extension
            else:
                return self
        except Exception as e:
            Log(f"Extension creation failed for '{attr_name}': {e}\n{traceback.format_exc()}", status='error', process='_extend')
            raise

    def _get_extension_depth(self):
        """Get the current nesting depth of this extension."""
        depth = 0
        current = self._parent
        while current is not None:
            if isinstance(current, OProxyExtension):
                depth += 1
            current = getattr(current, '_parent', None)
        return depth

    def _would_create_circular_dependency(self, cls, func, dat):
        """
        Check if extending with the given parameters would create a circular dependency.

        Returns True if circular dependency would be created.
        """
        # Get the source DAT path for comparison
        if hasattr(dat, 'path'):
            source_path = dat.path
        else:
            source_path = str(dat)

        # Walk up the parent chain and check if any parent extension
        # was created from the same source
        current = self._parent
        while current is not None:
            if isinstance(current, OProxyExtension):
                # Check if this parent extension was created from the same source
                parent_metadata = getattr(current, '_metadata', {})
                parent_dat_path = parent_metadata.get('dat_path')
                if parent_dat_path == source_path:
                    # Same source DAT - check if same extraction (cls/func)
                    parent_cls = parent_metadata.get('cls')
                    parent_func = parent_metadata.get('func')
                    if parent_cls == cls and parent_func == func:
                        return True
            current = getattr(current, '_parent', None)
        return False

    def _storage(self, keys=None, as_dict=False):
        """
        Public method to view serialized storage branch. Intended for public usage, not internal; use _store() for serialization.

        Args:
            keys: Optional keys to filter the returned data
            as_dict: If True, return dictionary object instead of JSON string

        Returns:
            Dictionary object if as_dict=True, JSON string otherwise
        """
        branch = self._get_storage_branch(keys)
        serialized = utils.make_serializable(branch)
        if as_dict:
            Log(f"Storage branch for extension '{getattr(self, '_extension_name', 'unknown')}' returned as dictionary", status='info', process='_storage')
            return serialized
        else:
            output = json.dumps(serialized, indent=4)
            Log(f"Storage branch for extension '{getattr(self, '_extension_name', 'unknown')}'\n\"{getattr(self, '_extension_name', 'unknown')}\" : {output}", status='info', process='_storage')
            return output


class OProxyContainer(OProxyBaseWrapper):
    """Composite: Container for OPs or sub-containers."""

    def __init__(self, ownerComp=None, path="", parent=None, ops=None, root=False):
        super().__init__(path, parent)
        self._children = {}  # name -> OProxyBaseWrapper (leaf or sub-container)
        self._ownerComp = ownerComp  # Only root has this for storage
        self._is_root = root  # Explicit root flag to avoid recursion issues
        self._extensions = {}  # Extensions applied to this container
        if ops:
            for op in ops:
                self._add(op.name, op)  # Auto-add initial OPs as leaves
        if self.is_root:
            pass

    @property
    def is_root(self):
        return self._is_root or (self._parent is None and self._ownerComp is not None)

    def _validate_child_name(self, container, name):
        """Validate that a name can be used as a child in the given container"""

        # Validate Python identifier rules
        if not isinstance(name, str):
            raise ValueError(f"Name must be a string, got {type(name).__name__}")
        if not name:
            raise ValueError("Name cannot be empty")
        if not name.isidentifier():
            raise ValueError(f"Name '{name}' is not a valid Python identifier. "
                           f"Names must contain only letters, digits, and underscores, "
                           f"cannot start with a digit, and cannot contain spaces or special characters. "
                           f"Use underscores instead of spaces (e.g., 'my_container' instead of 'my container').")
        if keyword.iskeyword(name):
            raise ValueError(f"Name '{name}' is a Python keyword and cannot be used")

        # Reserved names that cannot be used as child names
        reserved_names = {
            # Internal attributes (current single underscore convention)
            '_children', '_path', '_parent', '_ownerComp', '_is_root', '_op',
            # Properties
            'path', 'parent', 'is_root',
            # Methods
            '_add', '_remove', '_tree', '_refresh', '__save_to_storage', '__find_root',
            '__build_storage_structure', '__load_nested_containers', '_validate_child_name',
            # Magic methods
            '__str__', '__repr__', '__len__', '__iter__', '__getitem__', '__call__',
            '__getattr__', '__setattr__'
        }

        if name in reserved_names:
            if name.startswith('__'):
                raise ValueError(f"Magic method '{name}' cannot be used as child name. "
                               f"Use _extend('{name}', monkey_patch=True) if really needed (future feature).")
            elif name.startswith('_'):
                raise ValueError(f"Internal name '{name}' is reserved. "
                               f"Future versions will use double underscore convention (__{name[1:]}).")
            else:
                raise ValueError(f"Name '{name}' is reserved for {container.__class__.__name__} methods/properties")

        # Check for conflicts with existing children types
        if name in container._children:
            existing_child = container._children[name]
            if isinstance(existing_child, OProxyContainer):
                # This is OK - we'll add to the existing container
                pass
            else:  # OProxyLeaf
                raise ValueError(f"Name '{name}' already exists as an OP in '{container.path or 'root'}'")

        return True

    def _add_init(self, name, op):
        """Create new container with initial OPs"""
        Log(f"Creating new container '{name}'", status='info', process='_add')

        # Validate the container name
        self._validate_child_name(self, name)

        # Normalize op parameter to list of OP objects
        if not isinstance(op, (list, tuple)):
            op_list = [op]
            Log(f"Single OP provided, converted to list: {op}", status='debug', process='_add')
        else:
            op_list = op
            Log(f"List of OPs provided, count: {len(op_list)}", status='debug', process='_add')

        # Validate and convert all OPs (fail fast on first invalid)
        validated_ops = []
        for i, op_item in enumerate(op_list):
            Log(f"Validating OP {i+1}/{len(op_list)}: {op_item}", status='debug', process='_add')
            try:
                validated_op = td_isinstance(op_item, 'op') # TouchDesigner OP Type Checking
                validated_ops.append(validated_op)
                Log(f"Validated OP: {validated_op.name} (path: {validated_op.path})", status='debug', process='_add')
            except Exception as e:
                raise ValueError(f"Failed to validate OP '{op_item}': {e}")

        # Create new container with proper path
        child_path = f"{self.path}.{name}" if self.path else name
        Log(f"Creating container with path '{child_path}'", status='debug', process='_add')
        container = OProxyContainer(path=child_path, parent=self)

        # Add validated OPs as leaves to the container
        Log(f"Adding {len(validated_ops)} OPs as leaves to container '{name}'", status='debug', process='_add')
        for validated_op in validated_ops:
            leaf_path = f"{child_path}.{validated_op.name}"
            Log(f"Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'", status='debug', process='_add')
            leaf = OProxyLeaf(validated_op, path=leaf_path, parent=container)
            container._children[validated_op.name] = leaf

        # Add container to this container's children
        Log(f"Adding container '{name}' to parent children dict", status='debug', process='_add')
        self._children[name] = container

        Log(f"Successfully created container '{name}' with {len(validated_ops)} OPs", status='info', process='_add')

        # Store in TouchDesigner storage by finding root and saving entire hierarchy
        root = self._find_root()
        if hasattr(root, 'OProxies'):  # Ensure it's a proper root with storage
            root.__save_to_storage()

        return container

    def _add_insert(self, container, op):
        """Add OPs to existing container"""
        Log(f"Adding to existing container '{container.path or 'root'}'", status='debug', process='_add')

        # Normalize op parameter to list of OP objects
        if not isinstance(op, (list, tuple)):
            op_list = [op]
            Log(f"Single OP provided, converted to list: {op}", status='debug', process='_add')
        else:
            op_list = op
            Log(f"List of OPs provided, count: {len(op_list)}", status='debug', process='_add')

        # Validate and convert all OPs (fail fast on first invalid)
        validated_ops = []
        added_count = 0

        for i, op_item in enumerate(op_list):
            Log(f"Validating OP {i+1}/{len(op_list)}: {op_item}", status='debug', process='_add')
            try:
                validated_op = td_isinstance(op_item, 'op') # TouchDesigner OP Type Checking

                # Check if OP already exists in container
                if validated_op.name in container._children:
                    Log(f"OP '{validated_op.name}' already exists in container - skipping", status='warning', process='_add')
                    continue

                validated_ops.append(validated_op)
                Log(f"Validated OP: {validated_op.name} (path: {validated_op.path})", status='debug', process='_add')
                added_count += 1

            except Exception as e:
                raise ValueError(f"Failed to validate OP '{op_item}': {e}")

        # Add validated OPs as leaves to the existing container
        if added_count > 0:
            Log(f"Adding {added_count} new OPs to existing container '{container.path or 'root'}'", status='debug', process='_add')
            for validated_op in validated_ops:
                leaf_path = f"{container.path}.{validated_op.name}" if container.path else validated_op.name
                Log(f"Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'", status='debug', process='_add')
                leaf = OProxyLeaf(validated_op, path=leaf_path, parent=container)
                container._children[validated_op.name] = leaf

            Log(f"Successfully added {added_count} OPs to container '{container.path or 'root'}'", status='info', process='_add')

            # Update TouchDesigner storage
            root = self._find_root()
            if hasattr(root, 'OProxies'):
                root.__save_to_storage()
        else:
            Log(f"No new OPs to add to container '{container.path or 'root'}'", status='warning', process='_add')

        return added_count

    def _add(self, name, op=None, returnObj=False):
        '''
        Add OPs to a container. Creates new container if it doesn't exist, or adds to existing container.

        Usage examples:
        opr = parent.src.OProxy

        # Create new container with OPs
        opr._add('Media', ['moviefilein1', 'moviefilein2'])
        # Now opr.Media contains moviefilein1, moviefilein2

        # Add more OPs to existing container
        opr._add('Media', ['moviefilein3', 'moviefilein4'])
        # Now opr.Media contains moviefilein1, moviefilein2, moviefilein3, moviefilein4

        # Add single OP to existing container
        opr._add('Media', 'moviefilein5')
        # Now opr.Media contains all 5 moviefile OPs

        Parameters:
        - name: Container name (string)
        - op: Single OP or list of OPs to add
        - returnObj (bool): If True, returns the added/created container; otherwise returns self for chaining. Defaults to False.

        Behavior:
        - If container doesn't exist: Creates new container with provided OPs
        - If container exists: Adds OPs to existing container (skips duplicates)
        - If name conflicts with existing OP: Raises ValueError
        - Reserved names (methods, properties, magic methods): Raises ValueError

        Future: Use _extend() for monkey patching magic methods
        '''
        try:
            # Validate arguments - op is required
            if op is None:
                raise TypeError("_add() missing 1 required positional argument: 'op'")

            Log(f"Processing '{name}' in container '{self.path or 'root'}'", status='debug', process='_add')

            # Check if container already exists
            if name in self._children:
                existing = self._children[name]
                if isinstance(existing, OProxyContainer):
                    Log(f"'{name}' OProxyContainer already exists - adding to existing container", status='info', process='_add')
                    self._add_insert(existing, op)
                    obj = existing
                else:
                    raise ValueError(f"Cannot add container '{name}' - already exists as OP in '{self.path or 'root'}'")
            else:
                # Create new container
                obj = self._add_init(name, op)
        except Exception as e:
            Log(f"_add operation failed: {e}", status='error', process='_add')
            raise
        return obj if returnObj else self

    def _remove(self, name=None):
        """
        Remove containers, leafs, or extensions.

        Usage:
        - container._remove()           # Remove this container from its parent
        - container._remove('child')    # Remove named child from this container
        - container._remove(['child1', 'child2'])  # Remove multiple children
        - extension._remove()           # Remove this extension
        """
        try:
            # Case 0: _remove() on extension - delegate to extension's remove method
            if isinstance(self, OProxyExtension):
                return self._remove()

            # Case 1: _remove() - remove self from parent
            if name is None:
                if self._parent is not None:
                    # Remove self from parent
                    parent_container = self._parent
                    my_name = None
                    # Find my name in parent's children
                    for child_name, child in parent_container._children.items():
                        if child is self:
                            my_name = child_name
                            break

                    if my_name is not None:
                        Log(f"Removing self ('{my_name}') from parent", status='debug', process='_remove')
                        del parent_container._children[my_name]
                        # Find root and save entire updated hierarchy
                        root = parent_container._find_root()
                        if hasattr(root, 'OProxies'):
                            utils.remove(self, root.OProxies, parent_container.path)
                            root.__save_to_storage()
                    else:
                        Log("Could not find self in parent children", status='warning', process='_remove')
                else:
                    Log("Cannot remove root container", status='warning', process='_remove')
                return self

            # Case 2: _remove([names]) - remove multiple children
            elif isinstance(name, (list, tuple)):
                for item_name in name:
                    self._remove(item_name)  # Recursive call for single item removal
                return self

            # Case 3: _remove('name') - remove single child
            else:
                if name in self._children:
                    container_to_remove = self._children[name]
                    Log(f"Removing child '{name}' from container '{self.path or 'root'}'", status='info', process='_remove')
                    del self._children[name]
                    # Find root and save entire updated hierarchy
                    root = self._find_root()
                    if hasattr(root, 'OProxies'):
                        utils.remove(container_to_remove, root.OProxies, self.path)
                        root.__save_to_storage()
                else:
                    Log(f"Child '{name}' not found in container '{self.path or 'root'}'", status='warning', process='_remove')
                return self
        except Exception as e:
            Log(f"_remove operation failed: {e}", status='error', process='_remove')
            raise

    def _tree(self, indent=""):
        lines = [f"{indent}Container: {self.path or 'root'}"]
        for name, child in self._children.items():
            lines.append(child._tree(indent + "  "))
        return "\n".join(lines)

    def __getattr__(self, name):
        if name in self._children:
            return self._children[name]
        # Strict mode: raise error for non-existent containers/attributes
        # instead of confusing delegation behavior
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'. "
                           f"Use _add() to create containers or access existing ones: {list(self._children.keys())}")

    def __setattr__(self, name, value):
        if name.startswith('_') or name in ('_children', '_ownerComp', 'OProxies') or isinstance(value, OProxyExtension):
            object.__setattr__(self, name, value)  # Bypass OProxyBaseWrapper's restriction
        else:
            for child in self._children.values():
                setattr(child, name, value)

    def __str__(self):
        op_names = [child._op.name for child in self._children.values() if hasattr(child, '_op')]
        return f"OProxyContainer '{self.path or 'root'}' {op_names}"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        """Iterate over the OProxyLeaf wrappers in this container."""
        for child in self._children.values():
            if hasattr(child, '_op'):  # It's an OProxyLeaf
                yield child

    def __len__(self):
        """Return the number of OPs in this container."""
        return len([child for child in self._children.values() if hasattr(child, '_op')])

    def __getitem__(self, index):
        """Access OPs by index position."""
        op_leaves = [child for child in self._children.values() if hasattr(child, '_op')]
        return op_leaves[index]

    def __call__(self, name):
        """Access OPs by name (function call syntax)."""
        if name in self._children and hasattr(self._children[name], '_op'):
            return self._children[name]
        raise KeyError(f"No OP named '{name}' in this container")

    def __save_to_storage(self):
        """Save the current container hierarchy to TouchDesigner storage."""
        if not self.is_root:
            raise RuntimeError("__save_to_storage() can only be called on root containers")

        Log("Saving container hierarchy to storage", status='debug', process='_update_storage')

        # Build the complete nested storage structure
        children_data = self._build_storage_structure()

        # Replace children structure using setItem for proper dependency handling
        self.OProxies.setItem('children', children_data)

        Log(f"Saved {len(children_data)} top-level containers to storage", status='debug', process='_update_storage')

    def _save_to_storage(self):
        """Public method to save the container hierarchy to storage."""
        self.__save_to_storage()

    def _update_storage(self):
        """Update storage with current container's data (incremental update)."""
        if not self.is_root:
            raise RuntimeError("_update_storage() can only be called on root containers")

        try:
            # Prevent recursive updates from storage dependencies
            if hasattr(self, '_updating_storage') and self._updating_storage:
                return
            self._updating_storage = True

            # Rebuild this container's complete storage structure
            container_data = self._build_storage_structure()

            # For root container, replace entire children structure using setItem for proper dependency handling
            self.OProxies.setItem('children', container_data)

            # Update root extensions using setItem for proper dependency handling
            self.OProxies.setItem('extensions', {name: {'metadata': ext._metadata, 'extensions': ext._build_storage_structure()} for name, ext in self._extensions.items()})

            self._updating_storage = False

        except Exception as e:
            if hasattr(self, '_updating_storage'):
                self._updating_storage = False
            Log(f"Failed to update storage: {e}\n{traceback.format_exc()}", status='error', process='_update_storage')
            raise

    def _update_container_in_storage(self, container_data):
        """Update a specific container's data in root storage (called by non-roots)."""
        if self.is_root:
            # Root calls _update_storage() directly
            return self._update_storage()

        # Find root and update specific container location
        root = self._find_root()
        if not hasattr(root, 'OProxies'):
            return

        # Navigate to parent location in storage
        path_segments = self.path.split('.')
        parent_path = '.'.join(path_segments[:-1])  # Parent container path
        container_name = path_segments[-1]  # This container's name

        # For simplicity, trigger full root update for now
        # TODO: Implement true incremental update navigation
        root._update_storage()

    def _build_storage_structure(self):
        """Recursively build the nested storage structure from container hierarchy."""
        result = {}

        for name, child in self._children.items():
            if isinstance(child, OProxyContainer):
                # Build structure for this container
                container_data = {
                    'children': child._build_storage_structure(),  # Recursively build nested children
                    'ops': {},  # OPs in this container
                    'extensions': {name: {'metadata': ext._metadata, 'extensions': ext._build_storage_structure()} for name, ext in child._extensions.items()}  # Hierarchical extensions
                }
                if hasattr(child, '_monkey_patch'):
                    container_data['monkey_patch'] = child._monkey_patch

                # Add OPs from this container
                for op_name, op_child in child._children.items():
                    if hasattr(op_child, '_op'):  # It's an OProxyLeaf
                        # Create OP object with path, raw OP, and extensions
                        op_data = {
                            'path': op_child._op.path,
                            'op': op_child._op,  # Store raw OP object for name change detection
                            'extensions': {name: {'metadata': ext._metadata, 'extensions': ext._build_storage_structure()} for name, ext in op_child._extensions.items()}  # Hierarchical extensions
                        }
                        if hasattr(op_child, '_monkey_patch'):
                            op_data['monkey_patch'] = op_child._monkey_patch
                        container_data['ops'][op_name] = op_data

                result[name] = container_data

        return result

    def _refresh(self, target=None):
        """Refresh container and all descendants"""
        try:
            self._refresh_ops(target)
            self._refresh_extensions(target)

            # For root containers, load children from storage first
            if self.is_root and hasattr(self, 'OProxies'):
                children_data = self.OProxies.get('children', {})
                if children_data:
                    self._load_nested_containers(self, children_data, "")

                # Load root extensions from storage
                extensions_data = self.OProxies.get('extensions', {})
                for ext_name, ext_metadata in extensions_data.items():
                    try:
                        cls = ext_metadata.get('cls')
                        func = ext_metadata.get('func')
                        dat_path = ext_metadata.get('dat_path')
                        dat_op = ext_metadata.get('dat_op')  # New: get stored dat_op
                        args = ext_metadata.get('args')
                        call = ext_metadata.get('call', False)

                        if args is not None and not isinstance(args, (tuple, list)):
                            args = [args]
                        elif args is not None:
                            args = list(args)

                        # New: Try path first, fallback to stored dat_op
                        dat = td.op(dat_path) if dat_path else None
                        if not (dat and dat.valid) and dat_op and dat_op.valid:
                            dat = dat_op
                            Log(f"Using stored DAT for extension '{ext_name}' (path may have changed)", status='debug', process='_refresh')

                        if dat and dat.valid:
                            current_name = dat.name  # Use DAT name for extension name? No, extension name is ext_name, but if DAT renamed, perhaps update if needed. Wait, extension name is user-chosen.

                            # Detect if path changed
                            if dat_path != dat.path:
                                Log(f"Extension '{ext_name}' DAT path changed from '{dat_path}' to '{dat.path}', updating metadata", status='debug', process='_refresh')
                                ext_metadata['dat_path'] = dat.path
                                ext_metadata['dat_op'] = dat  # Refresh reference
                                changed = True
                            else:
                                changed = False

                            # Recreate extension
                            extension = self._extend(ext_name, cls=cls, func=func, dat=dat, args=args, call=call)
                            Log(f"Loaded root extension '{ext_name}' from storage", status='debug', process='_refresh')

                            if changed:
                                self._update_storage()  # Update storage if changed

                        else:
                            raise ValueError(f"Invalid DAT for extension '{ext_name}': Could not resolve {dat_path}")

                    except Exception as e:
                        Log(f"Failed to load root extension '{ext_name}' from storage: {e}", status='warning', process='_refresh')

            # Recursive refresh of children
            for child in self._children.values():
                if isinstance(child, OProxyContainer):
                    child._refresh()

            # Update storage
            if self.is_root:
                self._update_storage()
            else:
                # Find root and update storage for non-root containers
                root = self
                while root._parent is not None:
                    root = root._parent
                if hasattr(root, 'OProxies'):
                    root._update_storage()

        except Exception as e:
            Log(f"Container refresh failed for {self.path}: {e}\n{traceback.format_exc()}", status='error', process='_refresh')

    def _refresh_ops(self, target=None):
        """Load stored container data and check for OP name changes"""
        # Root containers don't have stored data for themselves
        if not self.path:
            return

        stored_data = self._get_stored_container_data()
        if not stored_data:
            return

        ops_data = stored_data.get('ops', {})

        # Rebuild children dictionary to preserve order from storage
        new_children = {}

        for stored_key, op_info in ops_data.items():
            if isinstance(op_info, str):
                # Legacy format support (simple path string)
                op_path = op_info
                stored_op = None
                op_extensions = {}
            else:
                # New format (object with path, raw OP, and extensions)
                op_path = op_info.get('path', '')
                stored_op = op_info.get('op')  # Raw OP object for name change detection
                op_extensions = op_info.get('extensions', {})

            Log(f"Loading nested OP '{stored_key}' from '{op_path}'", status='debug', process='_refresh')

            # Try to get OP by stored path first
            op = td.op(op_path) if op_path else None

            # If that fails but we have a stored OP object, use it (handles renames)
            if not (op and op.valid) and stored_op and stored_op.valid:
                op = stored_op
                Log(f"Using stored OP object for nested '{stored_key}' (original path may have changed)", status='debug', process='_refresh')

            if op and op.valid:
                # Check for name changes
                current_name = op.name
                if stored_key != current_name:
                    Log(f"Nested OP name changed from '{stored_key}' to '{current_name}', updating mapping", status='info', process='_refresh')

                # Add with current name (which may be different from stored_key)
                leaf_path = f"{self.path}.{current_name}"
                leaf = OProxyLeaf(op, path=leaf_path, parent=self)

                # Load extensions onto the leaf
                if op_extensions:
                    leaf._extensions = op_extensions

                new_children[current_name] = leaf
            else:
                # OP not found or invalid - skip adding to new children
                Log(f"Nested OP '{op_path}' not found or invalid, skipping", status='warning', process='_refresh')

        # Replace the children dictionary with the rebuilt one
        self._children = new_children

    def _refresh_extensions(self, target=None):
        """Load stored extension metadata and re-extract from DATs."""
        stored_data = self._get_stored_container_data()
        if not stored_data:
            return

        extensions_data = stored_data.get('extensions', {})  # Assuming containers store 'extensions' like root

        for ext_name, metadata in extensions_data.items():
            try:
                # New: Add fallback
                dat_path = metadata['dat_path']
                dat_op = metadata.get('dat_op')

                dat = td.op(dat_path) if dat_path else None
                if not (dat and dat.valid) and dat_op and dat_op.valid:
                    dat = dat_op
                    Log(f"Using stored DAT for container extension '{ext_name}' on '{self.path}' (path may have changed)", status='debug', process='_refresh')

                if dat and dat.valid:
                    if dat_path != dat.path:
                        Log(f"Container extension '{ext_name}' DAT path changed to '{dat.path}', updating metadata", status='debug', process='_refresh')
                        metadata['dat_path'] = dat.path
                        metadata['dat_op'] = dat
                        changed = True
                    else:
                        changed = False

                    # Then existing re-extract, but use dat for op=
                    actual_obj = mod_ast.Main(
                        cls=metadata['cls'],
                        func=metadata['func'],
                        source_dat=dat,  # Use resolved dat
                        log=Log
                    )

                    # Re-wrap in factory template
                    extension = OProxyExtension(actual_obj, self,
                                              source_dat=metadata['dat_path'],
                                              metadata=metadata)

                    # Store extension name for removal purposes
                    extension._extension_name = ext_name

                    # Apply to parent object
                    setattr(self, ext_name, extension)

                    # Store in registry
                    self._extensions[ext_name] = extension

                    # After setting extension
                    if changed and self._parent:
                        self._find_root()._update_storage()

                else:
                    Log(f"Could not resolve DAT for container extension '{ext_name}' on container '{self.path}'", status='warning', process='_refresh')
                    continue

            except Exception as e:
                Log(f"Failed to reload extension '{ext_name}' on container '{self.path}': {e}\n{traceback.format_exc()}", status='warning', process='_refresh')

    def _get_stored_container_data(self):
        """Navigate storage hierarchy to find data for this container."""
        root = self._find_root()
        if not hasattr(root, 'OProxies'):
            return None

        path_segments = self.path.split('.')
        # Filter out empty segments (can happen with empty root path)
        path_segments = [seg for seg in path_segments if seg]
        current_data = root.OProxies.get('children', {})

        # Navigate down the hierarchy following path segments
        for i, segment in enumerate(path_segments):
            if segment in current_data:
                segment_data = current_data[segment]
                # Check if it's dict-like (including TDStoreTools.DependDict)
                if hasattr(segment_data, 'get') and hasattr(segment_data, 'keys'):
                    # If this is the last segment, return the container data
                    if i == len(path_segments) - 1:
                        return segment_data
                    # Otherwise continue to children
                    current_data = segment_data.get('children', {})
                else:
                    return None
            else:
                return None

        return None

    def _load_nested_containers(self, parent_container, children_data, parent_path):
        """Helper method to recursively load nested containers."""
        for container_name, container_data in children_data.items():
            Log(f"Loading nested container '{container_name}' under '{parent_path}'", status='debug', process='_refresh')

            container_path = f"{parent_path}.{container_name}"
            monkey_patch_data = container_data.get('monkey_patch')
            if monkey_patch_data:
                cls_name = monkey_patch_data['cls']
                dat_path = monkey_patch_data['dat']
                mod_ast = mod('mod_AST')
                extracted_cls = mod_ast.Main(cls=cls_name, func=None, source_dat=dat_path, log=Log)
                container = extracted_cls(path=container_path, parent=parent_container, ops=None, root=False)
                container._monkey_patch = monkey_patch_data
            else:
                container = OProxyContainer(path=container_path, parent=parent_container)
            container._extensions = container_data.get('extensions', {})

            # Load OPs
            ops_data = container_data.get('ops', {})
            for op_name, op_info in ops_data.items():
                if isinstance(op_info, str):
                    # Legacy format support (simple path string)
                    op_path = op_info
                    stored_op = None
                    op_extensions = {}
                else:
                    # New format (object with path, raw OP, and extensions)
                    op_path = op_info.get('path', '')
                    stored_op = op_info.get('op')  # Raw OP object for name change detection
                    op_extensions = op_info.get('extensions', {})

                Log(f"Loading nested OP '{op_name}' from '{op_path}'", status='debug', process='_refresh')

                # Try to get OP by stored path first
                op = td.op(op_path) if op_path else None

                # If that fails but we have a stored OP object, use it (handles renames)
                if not (op and op.valid) and stored_op and stored_op.valid:
                    op = stored_op
                    Log(f"Using stored OP object for nested '{op_name}' (original path may have changed)", status='debug', process='_refresh')

                if op and op.valid:
                    # Check for name changes
                    current_name = op.name
                    if op_name != current_name:
                        Log(f"Nested OP name changed from '{op_name}' to '{current_name}', updating mapping", status='info', process='_refresh')
                        actual_key = current_name
                    else:
                        actual_key = op_name

                    leaf_path = f"{container_path}.{actual_key}"
                    monkey_patch_data = op_info.get('monkey_patch') if not isinstance(op_info, str) else None
                    if monkey_patch_data:
                        cls_name = monkey_patch_data['cls']
                        dat_path = monkey_patch_data['dat']
                        mod_ast = mod('mod_AST')
                        extracted_cls = mod_ast.Main(cls=cls_name, func=None, source_dat=dat_path, log=Log)
                        leaf = extracted_cls(op=op, path=leaf_path, parent=container)
                        leaf._monkey_patch = monkey_patch_data
                    else:
                        leaf = OProxyLeaf(op, path=leaf_path, parent=container)

                    # Load extensions onto the leaf
                    if op_extensions:
                        leaf._extensions = op_extensions
                        # Re-apply extensions (will be implemented in _extend)
                        for ext_name, ext_data in op_extensions.items():
                            # TODO: Apply extension logic here
                            pass

                    container._children[actual_key] = leaf
                else:
                    Log(f"Nested OP '{op_path}' not found or invalid, skipping", status='warning', process='_refresh')

            # Recursively load deeper nesting
            nested_children = container_data.get('children', {})
            if nested_children:
                self._load_nested_containers(container, nested_children, container_path)

            parent_container._children[container_name] = container

    def _extend(self, attr_name=None, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False, returnObj=False):
        """
        Extend the container with an attribute or method from a Text DAT.

        Container extensions are bound to the container instance (self refers to the OProxyContainer).
        """
        # Parameter validation
        if not (cls or func) and dat is not None:
            raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
        if (cls and func) or (not cls and not func):
            raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
        if not dat:
            raise ValueError("'dat' parameter is required for extensions")

        # Auto-default attr_name to func or cls name if not provided
        if attr_name is None:
            attr_name = func or cls

        # Validate attr_name as Python identifier
        if not isinstance(attr_name, str):
            raise ValueError(f"attr_name must be a string, got {type(attr_name).__name__}")
        if not attr_name:
            raise ValueError("attr_name cannot be empty")
        if not attr_name.isidentifier():
            raise ValueError(f"attr_name '{attr_name}' is not a valid Python identifier. "
                           f"Names must contain only letters, digits, and underscores, "
                           f"cannot start with a digit, and cannot contain spaces or special characters. "
                           f"Use underscores instead of spaces (e.g., 'my_extension' instead of 'my extension').")
        if keyword.iskeyword(attr_name):
            raise ValueError(f"attr_name '{attr_name}' is a Python keyword and cannot be used")

        if monkey_patch:
            if func is not None:
                raise NotImplementedError("'func' not supported when monkey_patch=True")
            if args is not None:
                raise NotImplementedError("'args' not supported when monkey_patch=True")
            if call:
                raise NotImplementedError("'call' not supported when monkey_patch=True")
            if cls is None:
                raise ValueError("'cls' is required when monkey_patch=True")
            if attr_name in self._extensions:
                raise NotImplementedError("Monkey-patching extensions not supported; remove and re-extend instead.")
            if attr_name not in self._children:
                raise ValueError(f"Cannot monkey-patch '{attr_name}': not found in children")
            existing = self._children[attr_name]
            if not isinstance(existing, (OProxyContainer, OProxyLeaf)):
                raise TypeError(f"Cannot monkey-patch type '{type(existing).__name__}'")

            mod_ast = mod('mod_AST')
            try:
                extracted_cls = mod_ast.Main(cls=cls, func=None, source_dat=dat, log=Log)
            except Exception as e:
                dat_op = dat if isinstance(dat, td.OP) else op(dat)
                path_str = dat_op.path if dat_op is not None else dat
                raise RuntimeError(f"Failed to extract class '{cls}' from DAT {path_str}: {e}") from e
            if not isinstance(extracted_cls, type):
                raise TypeError(f"Extracted '{cls}' is not a class")

            if isinstance(existing, OProxyContainer):
                if not issubclass(extracted_cls, OProxyContainer):
                    raise TypeError(f"Class '{cls}' must subclass OProxyContainer")
                new_instance = extracted_cls(path=existing._path, parent=existing._parent, ops=None, root=existing._is_root)
                new_instance._ownerComp = existing._ownerComp
                new_instance._children = existing._children
                for child in new_instance._children.values():
                    child._parent = new_instance
                new_instance._extensions = existing._extensions
                for ext in new_instance._extensions.values():
                    ext._parent = new_instance
                dat_op = td_isinstance(dat, 'textdat', allow_string=True)
                new_instance._monkey_patch = {'cls': cls, 'dat': dat_op.path}
                self._children[attr_name] = new_instance
            elif isinstance(existing, OProxyLeaf):
                if not issubclass(extracted_cls, OProxyLeaf):
                    raise TypeError(f"Class '{cls}' must subclass OProxyLeaf")
                new_instance = extracted_cls(op=existing._op, path=existing._path, parent=existing._parent)
                new_instance._extensions = existing._extensions
                for ext in new_instance._extensions.values():
                    ext._parent = new_instance
                dat_op = td_isinstance(dat, 'textdat', allow_string=True)
                new_instance._monkey_patch = {'cls': cls, 'dat': dat_op.path}
                self._children[attr_name] = new_instance

            root = self._find_root()
            if hasattr(root, 'OProxies'):
                root._update_storage()
            Log(f"Monkey-patched '{attr_name}' with '{cls}'", status='info', process='_extend')
            if returnObj:
                return new_instance
            else:
                return self

        try:
            # Import AST extraction module
            mod_ast = mod('mod_AST')

            # Validate DAT
            try:
                dat = td_isinstance(dat, 'textdat', allow_string=True)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid DAT: {e}")

            # Check for naming conflicts
            if hasattr(self, attr_name) and not monkey_patch:
                existing_attr = getattr(self, attr_name)
                if isinstance(existing_attr, (OProxyContainer, OProxyLeaf)):
                    raise ValueError(f"Name '{attr_name}' conflicts with existing container/leaf. Use monkey_patch=True to replace.")
                if not isinstance(existing_attr, OProxyExtension):
                    raise ValueError(f"Name '{attr_name}' conflicts with existing method/property. To overwrite, use monkey_patch=True.")

            # Extract the actual object
            try:
                actual_obj = mod_ast.Main(cls=cls, func=func, source_dat=dat, log=Log)
            except Exception as e:
                dat_op = dat if isinstance(dat, td.OP) else op(dat)
                path_str = dat_op.path if dat_op is not None else dat
                raise RuntimeError(f"Failed to extract from DAT {path_str}: {e}") from e

            # Prepare metadata
            metadata = {
                'cls': cls, 'func': func, 'dat_path': dat.path,
                'dat_op': dat,  # Add this for rename fallback
                'args': list(args) if args is not None else None, 'call': call, 'created_at': time.time()
            }

            extension = None

            # Handle call parameter
            if call:
                if args is not None:
                    if not isinstance(args, (tuple, list)):
                        raise TypeError("args must be a tuple or list of positional arguments when call=True")
                    # Convert to list for consistent handling
                    args = list(args)

                try:
                    if isinstance(actual_obj, type):  # Class instantiation
                        instance = actual_obj(*args) if args else actual_obj()
                        extension = OProxyExtension(instance, self, dat, metadata)
                        extension._extension_name = attr_name
                    else:  # Function call
                        sig = inspect.signature(actual_obj)
                        params = list(sig.parameters.values())
                        has_self = params and params[0].name == 'self'

                        if has_self:
                            bound_method = types.MethodType(actual_obj, self)
                            bound_method(*args) if args else bound_method()
                        else:
                            actual_obj(*args) if args else actual_obj()

                        extension = OProxyExtension(actual_obj, self, dat, metadata)
                        extension._extension_name = attr_name
                except Exception as e:
                    Log(f"Extension call execution failed during _extend: {e}\n{traceback.format_exc()}", status='error', process='_extend')
                    raise
            else:
                extension = OProxyExtension(actual_obj, self, dat, metadata)
                extension._extension_name = attr_name

            # Apply extension to parent object (make it accessible)
            setattr(self, attr_name, extension)

            # Store in internal registry for management
            self._extensions[attr_name] = extension

            # Update storage by finding root and updating
            root = self
            while root._parent is not None:
                root = root._parent
            if hasattr(root, 'OProxies'):
                root._update_storage()

            Log(f"Extension '{attr_name}' added to container '{self.path or 'root'}'", status='info', process='_extend')
            if returnObj:
                return extension
            else:
                return self
        except Exception as e:
            Log(f"Extension creation failed for '{attr_name}': {e}\n{traceback.format_exc()}", status='error', process='_extend')
            raise
        return self

    def _storage(self, keys=None, as_dict=False):
        """
        Public method to view serialized storage branch. Intended for public usage, not internal; use _store() for serialization.

        Args:
            keys: Optional keys to filter the returned data
            as_dict: If True, return dictionary object instead of JSON string

        Returns:
            Dictionary object if as_dict=True, JSON string otherwise
        """
        branch = self._get_storage_branch(keys)
        serialized = utils.make_serializable(branch)
        if as_dict:
            Log(f"Storage branch for container '{self.path or 'root'}' returned as dictionary", status='info', process='_storage')
            return serialized
        else:
            output = json.dumps(serialized, indent=4)
            Log(f"Storage branch for container '{self.path or 'root'}'\n\"{self.path or 'root'}\" : {output}", status='info', process='_storage')
            return output
