# OPBaseWrapper.py - Composite Pattern for OProxy
from abc import ABC, abstractmethod
import td
from utils import td_isinstance

''' LLM Notes:
Comments that begin with #! are meant to be updated dynamically when incongruencies
in comment vs codebase are found.
'''

# Import utils module for storage functions
utils = mod('utils')

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
            utils.log("DEBUG _remove: Cannot remove leaf - no parent container")
            return self

        # Find this leaf in parent's children
        parent_container = self._parent
        my_name = None
        for child_name, child in parent_container._children.items():
            if child is self:
                my_name = child_name
                break

        if my_name is not None:
            utils.log(f"DEBUG _remove: Removing leaf '{my_name}' from parent container")
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
            utils.log("DEBUG _remove: Could not find leaf in parent container children")

        return self

    def _tree(self):
        return f"Leaf: {self._op.name} ({self._op.path})"

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


class OProxyExtension(OPBaseWrapper):
    """
    Placeholder class for future extension functionality.

    When _extend() is implemented, this will be the base class for all extensions.
    Extensions will be able to be removed independently of their parent containers/leafs.
    """

    def __init__(self, parent, extension_data=None):
        """
        Initialize extension placeholder.

        Args:
            parent: Parent container or leaf this extension belongs to
            extension_data: Future extension metadata/configuration
        """
        # Placeholder - actual implementation will come with _extend()
        super().__init__(path="", parent=parent)
        self._extension_data = extension_data or {}

    def _remove(self):
        """
        Remove this extension (placeholder implementation).

        Future implementation will:
        - Remove extension from parent's extension registry
        - Clean up extension data from storage
        - Update any extension dependencies
        - Remove extension attributes from parent

        For now, this is a placeholder that logs the intended behavior.
        """
        utils.log("DEBUG _remove: Extension removal placeholder - not yet implemented")
        utils.log("Future: Will remove extension from parent and clean up storage")

        # Placeholder for future extension removal logic:
        # if self._parent:
        #     # Remove from parent's extension registry
        #     # Clean up storage data
        #     # Update dependencies

        return self

    def _add(self, name, op):
        """Extensions cannot add children."""
        raise NotImplementedError("Extensions cannot add children")

    def _tree(self):
        """Return string representation of extension."""
        return f"Extension: {self.__class__.__name__}"


class OPContainer(OPBaseWrapper):
    """Composite: Container for OPs or sub-containers."""

    def __init__(self, ownerComp=None, path="", parent=None, ops=None, root=False):
        super().__init__(path, parent)
        self._children = {}  # name -> OPBaseWrapper (leaf or sub-container)
        self._ownerComp = ownerComp  # Only root has this for storage
        self._is_root = root  # Explicit root flag to avoid recursion issues
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
        utils.log(f"DEBUG _add_init: Creating new container '{name}'")

        # Validate the container name
        self._validate_child_name(self, name)

        # Normalize op parameter to list of OP objects
        if not isinstance(op, (list, tuple)):
            op_list = [op]
            utils.log(f"DEBUG _add_init: Single OP provided, converted to list: {op}")
        else:
            op_list = op
            utils.log(f"DEBUG _add_init: List of OPs provided, count: {len(op_list)}")

        # Validate and convert all OPs (fail fast on first invalid)
        validated_ops = []
        for i, op_item in enumerate(op_list):
            utils.log(f"DEBUG _add_init: Validating OP {i+1}/{len(op_list)}: {op_item}")
            try:
                validated_op = td_isinstance(op_item, 'op') # TouchDesigner OP Type Checking
                validated_ops.append(validated_op)
                utils.log(f"DEBUG _add_init: Validated OP: {validated_op.name} (path: {validated_op.path})")
            except Exception as e:
                raise ValueError(f"Failed to validate OP '{op_item}': {e}")

        # Create new container with proper path
        child_path = f"{self.path}.{name}" if self.path else name
        utils.log(f"DEBUG _add_init: Creating container with path '{child_path}'")
        container = OPContainer(path=child_path, parent=self)

        # Add validated OPs as leaves to the container
        utils.log(f"DEBUG _add_init: Adding {len(validated_ops)} OPs as leaves to container '{name}'")
        for validated_op in validated_ops:
            leaf_path = f"{child_path}.{validated_op.name}"
            utils.log(f"DEBUG _add_init: Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'")
            leaf = OPLeaf(validated_op, path=leaf_path, parent=container)
            container._children[validated_op.name] = leaf

        # Add container to this container's children
        utils.log(f"DEBUG _add_init: Adding container '{name}' to parent children dict")
        self._children[name] = container

        utils.log(f"DEBUG _add_init: Successfully created container '{name}' with {len(validated_ops)} OPs")

        # Store in TouchDesigner storage by finding root and saving entire hierarchy
        root = self.__find_root()
        if hasattr(root, 'OProxies'):  # Ensure it's a proper root with storage
            root.__save_to_storage()

        return container

    def _add_insert(self, container, op):
        """Add OPs to existing container"""
        utils.log(f"DEBUG _add_insert: Adding to existing container '{container.path or 'root'}'")

        # Normalize op parameter to list of OP objects
        if not isinstance(op, (list, tuple)):
            op_list = [op]
            utils.log(f"DEBUG _add_insert: Single OP provided, converted to list: {op}")
        else:
            op_list = op
            utils.log(f"DEBUG _add_insert: List of OPs provided, count: {len(op_list)}")

        # Validate and convert all OPs (fail fast on first invalid)
        validated_ops = []
        added_count = 0

        for i, op_item in enumerate(op_list):
            utils.log(f"DEBUG _add_insert: Validating OP {i+1}/{len(op_list)}: {op_item}")
            try:
                validated_op = td_isinstance(op_item, 'op') # TouchDesigner OP Type Checking

                # Check if OP already exists in container
                if validated_op.name in container._children:
                    utils.log(f"DEBUG _add_insert: OP '{validated_op.name}' already exists in container - skipping")
                    continue

                validated_ops.append(validated_op)
                utils.log(f"DEBUG _add_insert: Validated OP: {validated_op.name} (path: {validated_op.path})")
                added_count += 1

            except Exception as e:
                raise ValueError(f"Failed to validate OP '{op_item}': {e}")

        # Add validated OPs as leaves to the existing container
        if added_count > 0:
            utils.log(f"DEBUG _add_insert: Adding {added_count} new OPs to existing container '{container.path or 'root'}'")
            for validated_op in validated_ops:
                leaf_path = f"{container.path}.{validated_op.name}" if container.path else validated_op.name
                utils.log(f"DEBUG _add_insert: Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'")
                leaf = OPLeaf(validated_op, path=leaf_path, parent=container)
                container._children[validated_op.name] = leaf

            utils.log(f"DEBUG _add_insert: Successfully added {added_count} OPs to container '{container.path or 'root'}'")

            # Update TouchDesigner storage
            root = self.__find_root()
            if hasattr(root, 'OProxies'):
                root.__save_to_storage()
        else:
            utils.log(f"DEBUG _add_insert: No new OPs to add to container '{container.path or 'root'}'")

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
        utils.log(f"DEBUG _add: Processing '{name}' in container '{self.path or 'root'}'")

        # Check if container already exists
        if name in self._children:
            existing = self._children[name]
            if isinstance(existing, OPContainer):
                utils.log(f"'{name}' OPContainer already exists - adding to existing container")
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
        """
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
                    utils.log(f"DEBUG _remove: Removing self ('{my_name}') from parent")
                    del parent_container._children[my_name]
                    # Find root and save entire updated hierarchy
                    root = parent_container.__find_root()
                    if hasattr(root, 'OProxies'):
                        utils.remove(self, root.OProxies, parent_container.path)
                        root.__save_to_storage()
                else:
                    utils.log("DEBUG _remove: Could not find self in parent children")
            else:
                utils.log("DEBUG _remove: Cannot remove root container")
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
                utils.log(f"DEBUG _remove: Removing child '{name}' from container '{self.path or 'root'}'")
                del self._children[name]
                # Find root and save entire updated hierarchy
                root = self.__find_root()
                if hasattr(root, 'OProxies'):
                    utils.remove(container_to_remove, root.OProxies, self.path)
                    root.__save_to_storage()
            else:
                utils.log(f"DEBUG _remove: Child '{name}' not found in container '{self.path or 'root'}'")
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

        utils.log("DEBUG __save_to_storage: Saving container hierarchy to storage...")

        # Build the complete nested storage structure
        children_data = self.__build_storage_structure()

        # Clear existing children and update with new data
        # This modifies the existing dictionary object rather than replacing it
        self.OProxies['children'].clear()
        self.OProxies['children'].update(children_data)

        utils.log(f"DEBUG __save_to_storage: Saved {len(children_data)} top-level containers to storage")

    def _save_to_storage(self):
        """Public method to save the container hierarchy to storage."""
        self.__save_to_storage()

    def __build_storage_structure(self):
        """Recursively build the nested storage structure from container hierarchy."""
        result = {}

        for name, child in self._children.items():
            if isinstance(child, OPContainer):
                # Build structure for this container
                container_data = {
                    'children': child.__build_storage_structure(),  # Recursively build nested children
                    'ops': {},  # OPs in this container
                    'extensions': {}
                }

                # Add OPs from this container
                for op_name, op_child in child._children.items():
                    if hasattr(op_child, '_op'):  # It's an OPLeaf
                        container_data['ops'][op_name] = op_child._op.path

                result[name] = container_data

        return result

    def _refresh(self):
        """Refresh/reload the container hierarchy from TouchDesigner storage."""
        if not self.is_root:
            raise RuntimeError("_refresh() can only be called on root containers")

        utils.log("DEBUG _refresh: Loading container hierarchy from storage...")

        # Clear existing children for fresh reload
        self._children.clear()

        # Load from storage
        children_data = self.OProxies.get('children', {})

        for container_name, container_data in children_data.items():
            utils.log(f"DEBUG _refresh: Loading container '{container_name}'")

            # Create the container
            container_path = container_name  # Root level containers
            container = OPContainer(path=container_path, parent=self)

            # Load OPs into the container
            ops_data = container_data.get('ops', {})
            for op_name, op_path in ops_data.items():
                utils.log(f"DEBUG _refresh: Loading OP '{op_name}' from '{op_path}'")
                op = td.op(op_path)
                if op and op.valid:
                    leaf_path = f"{container_path}.{op_name}"
                    leaf = OPLeaf(op, path=leaf_path, parent=container)
                    container._children[op_name] = leaf
                else:
                    utils.log(f"DEBUG _refresh: Warning - OP '{op_path}' not found or invalid")

            # Recursively load nested children containers
            nested_children = container_data.get('children', {})
            if nested_children:
                self._load_nested_containers(container, nested_children, container_path)

            # Add container to root's children
            self._children[container_name] = container

        utils.log(f"DEBUG _refresh: Loaded {len(self._children)} containers from storage")

    def _load_nested_containers(self, parent_container, children_data, parent_path):
        """Helper method to recursively load nested containers."""
        for container_name, container_data in children_data.items():
            utils.log(f"DEBUG _refresh: Loading nested container '{container_name}' under '{parent_path}'")

            container_path = f"{parent_path}.{container_name}"
            container = OPContainer(path=container_path, parent=parent_container)

            # Load OPs
            ops_data = container_data.get('ops', {})
            for op_name, op_path in ops_data.items():
                op = td.op(op_path)
                if op and op.valid:
                    leaf_path = f"{container_path}.{op_name}"
                    leaf = OPLeaf(op, path=leaf_path, parent=container)
                    container._children[op_name] = leaf

            # Recursively load deeper nesting
            nested_children = container_data.get('children', {})
            if nested_children:
                self._load_nested_containers(container, nested_children, container_path)

            parent_container._children[container_name] = container
