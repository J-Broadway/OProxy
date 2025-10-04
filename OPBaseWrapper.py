# OPBaseWrapper.py - Composite Pattern for OProxy
from abc import ABC, abstractmethod
import td
import types
import time
import traceback
from utils import td_isinstance

''' LLM Notes:
Comments that begin with #! are meant to be updated dynamically when incongruencies
in comment vs codebase are found.
'''

# Import utils module for storage functions
utils = mod('utils')
Log = parent.opr.Log # Use this instead of self.Log() <-- will return errors.

class OPBaseWrapper(ABC):
    """Abstract Component: Common interface for leaves and composites."""

    def __init__(self, path="", parent=None):
        self._path = path  # Hierarchical path (e.g., 'effects.advanced')
        self._parent = parent
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
    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
        """
        Extend the proxy object with an attribute or method from a Text DAT.

        Parameters:
        - attr_name (str): Name for the extension
        - cls (str): Class name to extract from DAT
        - func (str): Function name to extract from DAT
        - dat (DAT): Text DAT containing the extension (required)
        - args (tuple|list): Arguments for instantiation/calling when call=True
        - call (bool): Whether to instantiate/call immediately
        - monkey_patch (bool): Allow overwriting existing attributes

        Returns:
        - self: For method chaining

        Raises:
        - ValueError: Invalid parameters, naming conflicts, extraction failures
        """
        pass

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

class OPLeaf(OPBaseWrapper):
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
        """Refresh leaf extensions"""
        try:
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
                # Re-extract the actual object
                actual_obj = mod_ast.Main(
                    cls=metadata['cls'],
                    func=metadata['func'],
                    op=metadata['dat_path'],
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

    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
        """
        Extend the leaf with an attribute or method from a Text DAT.

        Leaf extensions are bound to the leaf instance (self refers to the OPLeaf).
        """
        # Parameter validation
        if not (cls or func) and dat is not None:
            raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
        if (cls and func) or (not cls and not func):
            raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
        if not dat:
            raise ValueError("'dat' parameter is required for extensions")

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
            actual_obj = mod_ast.Main(cls=cls, func=func, op=dat, log=Log)
        except Exception as e:
            raise RuntimeError(f"Failed to extract from DAT {dat.path}: {e}") from e

        # Prepare metadata
        metadata = {
            'cls': cls, 'func': func, 'dat_path': dat.path,
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
        return self


class OProxyExtension(OPBaseWrapper):
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
                return self._actual(*args, **kwargs)
            else:
                raise TypeError(f"'{self.__class__.__name__}' object is not callable")
        except Exception as e:
            Log(f"Extension call failed: {e}\n{traceback.format_exc()}", status='error', process='__call__')
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

    def _remove(self):
        """
        Remove this extension from its parent and clean up storage.

        Implementation will:
        - Remove extension from parent's _extensions registry
        - Remove extension attribute from parent object
        - Clean up extension data from storage
        - Update storage persistence
        """
        if self._parent:
            # Remove from parent's extension registry
            if hasattr(self._parent, '_extensions') and hasattr(self, '_extension_name'):
                if self._extension_name in self._parent._extensions:
                    del self._parent._extensions[self._extension_name]

            # Remove extension attribute from parent
            if hasattr(self._parent, self._extension_name):
                delattr(self._parent, self._extension_name)

            # Clean up storage (will call parent's storage update)
            if hasattr(self._parent, '_update_storage'):
                self._parent._update_storage()

        Log(f"Extension '{getattr(self, '_extension_name', 'unknown')}' removed successfully", status='info', process='_remove')
        return self

    def _add(self, name, op):
        """Extensions cannot add children."""
        raise NotImplementedError("Extensions cannot add children")

    def _tree(self):
        """Return string representation of extension."""
        return f"Extension: {self.__class__.__name__}"

    def _refresh(self, target=None):
        """Extensions don't refresh themselves."""
        raise NotImplementedError("Extensions cannot be refreshed")

    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
        """Extensions cannot extend themselves."""
        raise NotImplementedError("Extensions cannot be extended")


class OPContainer(OPBaseWrapper):
    """Composite: Container for OPs or sub-containers."""

    def __init__(self, ownerComp=None, path="", parent=None, ops=None, root=False):
        super().__init__(path, parent)
        self._children = {}  # name -> OPBaseWrapper (leaf or sub-container)
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
            if isinstance(existing_child, OPContainer):
                # This is OK - we'll add to the existing container
                pass
            else:  # OPLeaf
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
        container = OPContainer(path=child_path, parent=self)

        # Add validated OPs as leaves to the container
        Log(f"Adding {len(validated_ops)} OPs as leaves to container '{name}'", status='debug', process='_add')
        for validated_op in validated_ops:
            leaf_path = f"{child_path}.{validated_op.name}"
            Log(f"Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'", status='debug', process='_add')
            leaf = OPLeaf(validated_op, path=leaf_path, parent=container)
            container._children[validated_op.name] = leaf

        # Add container to this container's children
        Log(f"Adding container '{name}' to parent children dict", status='debug', process='_add')
        self._children[name] = container

        Log(f"Successfully created container '{name}' with {len(validated_ops)} OPs", status='info', process='_add')

        # Store in TouchDesigner storage by finding root and saving entire hierarchy
        root = self.__find_root()
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
                leaf = OPLeaf(validated_op, path=leaf_path, parent=container)
                container._children[validated_op.name] = leaf

            Log(f"Successfully added {added_count} OPs to container '{container.path or 'root'}'", status='info', process='_add')

            # Update TouchDesigner storage
            root = self.__find_root()
            if hasattr(root, 'OProxies'):
                root.__save_to_storage()
        else:
            Log(f"No new OPs to add to container '{container.path or 'root'}'", status='warning', process='_add')

        return added_count

    def _add(self, name, op):
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

        Behavior:
        - If container doesn't exist: Creates new container with provided OPs
        - If container exists: Adds OPs to existing container (skips duplicates)
        - If name conflicts with existing OP: Raises ValueError
        - Reserved names (methods, properties, magic methods): Raises ValueError

        Future: Use _extend() for monkey patching magic methods
        '''
        Log(f"Processing '{name}' in container '{self.path or 'root'}'", status='debug', process='_add')

        # Check if container already exists
        if name in self._children:
            existing = self._children[name]
            if isinstance(existing, OPContainer):
                Log(f"'{name}' OPContainer already exists - adding to existing container", status='info', process='_add')
                self._add_insert(existing, op)
            else:
                raise ValueError(f"Cannot add container '{name}' - already exists as OP in '{self.path or 'root'}'")
        else:
            # Create new container
            self._add_init(name, op)

    def _remove(self, name=None):
        """
        Remove containers, leafs, or extensions.

        Usage:
        - container._remove()           # Remove this container from its parent
        - container._remove('child')    # Remove named child from this container
        - container._remove(['child1', 'child2'])  # Remove multiple children
        - extension._remove()           # Remove this extension
        """
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
                    root = parent_container.__find_root()
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
                root = self.__find_root()
                if hasattr(root, 'OProxies'):
                    utils.remove(container_to_remove, root.OProxies, self.path)
                    root.__save_to_storage()
            else:
                Log(f"Child '{name}' not found in container '{self.path or 'root'}'", status='warning', process='_remove')
            return self

    def __find_root(self):
        """Internal method: Traverse up parent chain to find root container."""
        current = self
        while current._parent is not None:
            current = current._parent
        return current


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
        if name.startswith('_') or name in ('_children', '_ownerComp', 'OProxies'):
            object.__setattr__(self, name, value)  # Bypass OPBaseWrapper's restriction
        else:
            for child in self._children.values():
                setattr(child, name, value)

    def __str__(self):
        op_names = [child._op.name for child in self._children.values() if hasattr(child, '_op')]
        return f"OPContainer '{self.path or 'root'}' {op_names}"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        """Iterate over the OPLeaf wrappers in this container."""
        for child in self._children.values():
            if hasattr(child, '_op'):  # It's an OPLeaf
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
        children_data = self.__build_storage_structure()

        # Clear existing children and update with new data
        # This modifies the existing dictionary object rather than replacing it
        self.OProxies['children'].clear()
        self.OProxies['children'].update(children_data)

        Log(f"Saved {len(children_data)} top-level containers to storage", status='debug', process='_update_storage')

    def _save_to_storage(self):
        """Public method to save the container hierarchy to storage."""
        self.__save_to_storage()

    def _update_storage(self):
        """Update storage with current container's data (incremental update)."""
        if not self.is_root:
            raise RuntimeError("_update_storage() can only be called on root containers")

        try:
            # Rebuild this container's complete storage structure
            container_data = self.__build_storage_structure()

            # For root container, replace entire children structure
            self.OProxies['children'] = container_data

        except Exception as e:
            Log(f"Failed to update storage: {e}\n{traceback.format_exc()}", status='error', process='_update_storage')
            raise

    def _update_container_in_storage(self, container_data):
        """Update a specific container's data in root storage (called by non-roots)."""
        if self.is_root:
            # Root calls _update_storage() directly
            return self._update_storage()

        # Find root and update specific container location
        root = self.__find_root()
        if not hasattr(root, 'OProxies'):
            return

        # Navigate to parent location in storage
        path_segments = self.path.split('.')
        parent_path = '.'.join(path_segments[:-1])  # Parent container path
        container_name = path_segments[-1]  # This container's name

        # For simplicity, trigger full root update for now
        # TODO: Implement true incremental update navigation
        root._update_storage()

    def __build_storage_structure(self):
        """Recursively build the nested storage structure from container hierarchy."""
        result = {}

        for name, child in self._children.items():
            if isinstance(child, OPContainer):
                # Build structure for this container
                container_data = {
                    'children': child.__build_storage_structure(),  # Recursively build nested children
                    'ops': {},  # OPs in this container
                    'extensions': getattr(child, '_extensions', {})  # Container extensions
                }

                # Add OPs from this container
                for op_name, op_child in child._children.items():
                    if hasattr(op_child, '_op'):  # It's an OPLeaf
                        # Create OP object with path, raw OP, and extensions
                        op_data = {
                            'path': op_child._op.path,
                            'op': op_child._op,  # Store raw OP object for name change detection
                            'extensions': getattr(op_child, '_extensions', {})  # Will be added by _extend()
                        }
                        container_data['ops'][op_name] = op_data

                result[name] = container_data

        return result

    def _refresh(self, target=None):
        """Refresh container and all descendants"""
        try:
            self._refresh_ops(target)
            self._refresh_extensions(target)

            # Recursive refresh of children
            for child in self._children.values():
                if isinstance(child, OPContainer):
                    child._refresh()

            # Update storage if this is root
            if self.is_root:
                self._update_storage()

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

            # Try to get OP by stored path first
            op = td.op(op_path) if op_path else None

            # If that fails but we have a stored OP object, use it (handles renames)
            if not (op and op.valid) and stored_op and stored_op.valid:
                op = stored_op

            if op and op.valid:
                # Check for name changes
                current_name = op.name
                if stored_key != current_name:
                    # Remove old mapping
                    if stored_key in self._children:
                        del self._children[stored_key]

                    # Add with new name
                    leaf_path = f"{self.path}.{current_name}"
                    leaf = OPLeaf(op, path=leaf_path, parent=self)

                    # Load extensions onto the leaf
                    if op_extensions:
                        leaf._extensions = op_extensions

                    self._children[current_name] = leaf
            else:
                # OP not found or invalid - remove from container
                if stored_key in self._children:
                    del self._children[stored_key]

    def _refresh_extensions(self, target=None):
        """Load stored extension metadata and re-extract from DATs."""
        stored_data = self._get_stored_container_data()
        if not stored_data:
            return

        extensions_data = stored_data.get('extensions', {})
        mod_ast = mod('mod_AST')

        for ext_name, metadata in extensions_data.items():
            try:
                # Re-extract the actual object
                actual_obj = mod_ast.Main(
                    cls=metadata['cls'],
                    func=metadata['func'],
                    op=metadata['dat_path'],
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

            except Exception as e:
                Log(f"Failed to reload extension '{ext_name}': {e}\n{traceback.format_exc()}", status='warning', process='_refresh')

    def _get_stored_container_data(self):
        """Navigate storage hierarchy to find data for this container."""
        root = self.__find_root()
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
            container = OPContainer(path=container_path, parent=parent_container)

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
                        # Use current name as key instead of stored name
                        actual_key = current_name
                    else:
                        actual_key = op_name

                    leaf_path = f"{container_path}.{actual_key}"
                    leaf = OPLeaf(op, path=leaf_path, parent=container)

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

    def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
        """
        Extend the container with an attribute or method from a Text DAT.

        Container extensions are bound to the container instance (self refers to the OPContainer).
        """
        # Parameter validation
        if not (cls or func) and dat is not None:
            raise ValueError("Must specify either 'cls' or 'func' when 'dat' is provided")
        if (cls and func) or (not cls and not func):
            raise ValueError("Must specify exactly one of 'cls' or 'func' when 'dat' is provided, or neither for direct value")
        if not dat:
            raise ValueError("'dat' parameter is required for extensions")

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
                if not isinstance(existing_attr, OProxyExtension):
                    raise ValueError(f"Name '{attr_name}' conflicts with existing method/property. "
                                   f"To overwrite, use monkey_patch=True.")

            # Extract the actual object
            try:
                actual_obj = mod_ast.Main(cls=cls, func=func, op=dat, log=Log)
            except Exception as e:
                raise RuntimeError(f"Failed to extract from DAT {dat.path}: {e}") from e

            # Prepare metadata
            metadata = {
                'cls': cls, 'func': func, 'dat_path': dat.path,
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

                try:
                    if isinstance(actual_obj, type):  # Class instantiation
                        result = actual_obj(*args) if args else actual_obj()
                        extension = OProxyExtension(result, self, dat, metadata)
                        extension._extension_name = attr_name
                    else:  # Function call
                        bound_method = types.MethodType(actual_obj, self)
                        result = bound_method(*args) if args else bound_method()
                        extension = OProxyExtension(bound_method, self, dat, metadata)
                        extension._extension_name = attr_name
                except Exception as e:
                    Log(f"Extension call execution failed during _extend: {e}\n{traceback.format_exc()}", status='error', process='_extend')
                    raise

            # Apply extension to parent object (make it accessible)
            setattr(self, attr_name, extension)

            # Store in internal registry for management
            self._extensions[attr_name] = extension

            # Update storage with extension metadata
            self._update_storage()

            Log(f"Extension '{attr_name}' added to container '{self.path or 'root'}'", status='info', process='_extend')
        except Exception as e:
            Log(f"Extension creation failed for '{attr_name}': {e}\n{traceback.format_exc()}", status='error', process='_extend')
            raise
        return self
