# OPBaseWrapper.py - Composite Pattern for OProxy
from abc import ABC, abstractmethod
import td
from utils import td_isinstance

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
    def _remove(self, name):
        """Remove a child by name."""
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

    def _remove(self, name):
        raise NotImplementedError("Cannot remove from a leaf")

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

    def _add(self, name, op):
        '''
        Looking for this usage:
        opr = parent.src.OProxy
        opr._add('Media', ['moviefilein1', 'moviefilein2'])

        # Now this should be accessible
        opr.Media should be accessible and contain the OPs 'moviefilein1' and 'moviefilein2'

        We need to create a new OPContainer based on 'name'
        We need to make sure existing OPContainer item doesn't already exist if does just print 'already exists' and do nothing
        Use td_isinstance() from utils for OP type checking

        Because OProxy is a dynamic based of the composite design pattern the idea is now that opr.Media
        will also be an OPContainer that inherits all the OPBaseWrapper methods and properties
        So user can do opr.Media._add('moviefilein3', 'moviefilein4') and so on...
        '''
        print(f"DEBUG _add: Adding container '{name}' to path '{self.path}'")

        # Check if container already exists
        if name in self._children:
            print(f"DEBUG _add: Container '{name}' already exists - skipping")
            return

        # Normalize op parameter to list of OP objects
        if not isinstance(op, (list, tuple)):
            op_list = [op]
            print(f"DEBUG _add: Single OP provided, converted to list: {op}")
        else:
            op_list = op
            print(f"DEBUG _add: List of OPs provided, count: {len(op_list)}")

        # Validate and convert all OPs
        validated_ops = []
        for i, op_item in enumerate(op_list):
            print(f"DEBUG _add: Validating OP {i+1}/{len(op_list)}: {op_item}")
            validated_op = td_isinstance(op_item, 'op')
            validated_ops.append(validated_op)
            print(f"DEBUG _add: Validated OP: {validated_op.name} (path: {validated_op.path})")

        # Create new container with proper path
        child_path = f"{self.path}.{name}" if self.path else name
        print(f"DEBUG _add: Creating container with path '{child_path}'")
        container = OPContainer(path=child_path, parent=self)

        # Add validated OPs as leaves to the container
        print(f"DEBUG _add: Adding {len(validated_ops)} OPs as leaves to container '{name}'")
        for validated_op in validated_ops:
            leaf_path = f"{child_path}.{validated_op.name}"
            print(f"DEBUG _add: Creating leaf for OP '{validated_op.name}' with path '{leaf_path}'")
            leaf = OPLeaf(validated_op, path=leaf_path, parent=container)
            container._children[validated_op.name] = leaf

        # Add container to this container's children
        print(f"DEBUG _add: Adding container '{name}' to parent children dict")
        self._children[name] = container

        print(f"DEBUG _add: Successfully added container '{name}' with {len(validated_ops)} OPs")

        # Storage persistence will be added later
        # if self.is_root:
        #     self.__save_to_storage()

    def _remove(self, name):
        if name in self._children:
            del self._children[name]
            if self.is_root:
                self.__save_to_storage()
        return self

    def _tree(self, indent=""):
        lines = [f"{indent}Container: {self.path or 'root'}"]
        for name, child in self._children.items():
            lines.append(child._tree(indent + "  "))
        return "\n".join(lines)

    def __getattr__(self, name):
        if name in self._children:
            return self._children[name]
        if len(self._children) == 1:  # Delegate to single child
            return getattr(list(self._children.values())[0], name)
        # Delegate to all children (return list of results)
        return [getattr(child, name) for child in self._children.values()]

    def __setattr__(self, name, value):
        if name.startswith('_') or name in ('_children', '_ownerComp'):
            super().__setattr__(name, value)
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
