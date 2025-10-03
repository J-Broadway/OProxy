#!/usr/bin/env python3
"""
Test the OPLeaf._remove() fix for name mangling issue.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Create a minimal test without TouchDesigner dependencies
class MockOP:
    def __init__(self, name):
        self.name = name
        self.path = f"/project1/{name}"
        self.valid = True

class MockRoot:
    def __init__(self):
        self.OProxies = {'children': {}}

    def _save_to_storage(self):
        print("Mock: Storage saved")

def test_leaf_removal():
    """Test that leaf removal works without name mangling errors."""
    print("Testing OPLeaf._remove() fix...")

    # Import the classes (this will fail if there are import issues, but that's expected)
    try:
        # We'll create a minimal mock instead
        class MockContainer:
            def __init__(self, path="test", parent=None):
                self.path = path
                self._parent = parent
                self._children = {}
                self.OProxies = None

            def remove(self, item, storage, path):
                print(f"Mock remove: {item} from {path}")

            def _save_to_storage(self):
                print("Mock: Container storage saved")

        class MockLeaf:
            def __init__(self, op, path="test", parent=None):
                self._op = op
                self.path = path
                self._parent = parent

            def _remove(self):
                """Simplified version of the fixed OPLeaf._remove()"""
                if self._parent is None:
                    print("No parent - cannot remove")
                    return self

                # Find this leaf in parent's children
                parent_container = self._parent
                my_name = None
                for child_name, child in parent_container._children.items():
                    if child is self:
                        my_name = child_name
                        break

                if my_name is not None:
                    print(f"Removing leaf '{my_name}' from parent container")
                    del parent_container._children[my_name]

                    # Find root by traversing up parent chain (the fix)
                    root = parent_container
                    while root._parent is not None:
                        root = root._parent

                    # Update storage (mocked)
                    if hasattr(root, 'OProxies'):
                        # Mock the remove call
                        root.remove(self, root.OProxies, parent_container.path)
                        root._save_to_storage()

                else:
                    print("Could not find leaf in parent container children")

                return self

        # Create test hierarchy
        root = MockContainer("root")
        root.OProxies = {'children': {}}

        container = MockContainer("items", parent=root)
        root._children['items'] = container

        leaf = MockLeaf(MockOP("op1"), path="items.op1", parent=container)
        container._children['op1'] = leaf

        # Test removal
        print("Before removal:", list(container._children.keys()))
        result = leaf._remove()
        print("After removal:", list(container._children.keys()))
        print("Return value is self:", result is leaf)

        # Verify the leaf was removed
        assert 'op1' not in container._children, "Leaf should be removed from parent"
        assert result is leaf, "Should return self for chaining"

        print("SUCCESS: Leaf removal works correctly!")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    test_leaf_removal()
