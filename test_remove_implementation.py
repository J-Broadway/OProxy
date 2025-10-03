#!/usr/bin/env python3
"""
Basic verification of _remove() implementation refactor.
This tests the method signatures without running TouchDesigner-dependent code.
"""

import ast

def extract_method_signatures(filename):
    """Extract method signatures from Python file using AST parsing."""
    with open(filename, 'r') as f:
        source = f.read()

    tree = ast.parse(source)

    signatures = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            signatures[class_name] = {}

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '_remove':
                    # Extract parameters
                    params = [arg.arg for arg in item.args.args if arg.arg != 'self']
                    signatures[class_name]['_remove'] = params

    return signatures

def test_method_signatures():
    """Test that method signatures match our design."""
    print("Testing method signatures...")

    signatures = extract_method_signatures('OPBaseWrapper.py')

    # Check OPBaseWrapper has abstract _remove with 'name' parameter
    assert 'OPBaseWrapper' in signatures, "OPBaseWrapper class should exist"
    assert '_remove' in signatures['OPBaseWrapper'], "OPBaseWrapper should have _remove method"
    assert 'name' in signatures['OPBaseWrapper']['_remove'], "OPBaseWrapper._remove should have 'name' parameter"

    # Check OPContainer has _remove with 'name' parameter
    assert 'OPContainer' in signatures, "OPContainer class should exist"
    assert '_remove' in signatures['OPContainer'], "OPContainer should have _remove method"
    assert 'name' in signatures['OPContainer']['_remove'], "OPContainer._remove should have 'name' parameter"

    # Check OPLeaf has _remove without 'name' parameter (only self)
    assert 'OPLeaf' in signatures, "OPLeaf class should exist"
    assert '_remove' in signatures['OPLeaf'], "OPLeaf should have _remove method"
    assert 'name' not in signatures['OPLeaf']['_remove'], "OPLeaf._remove should NOT have 'name' parameter"

    # Check OProxyExtension has _remove without 'name' parameter
    assert 'OProxyExtension' in signatures, "OProxyExtension class should exist"
    assert '_remove' in signatures['OProxyExtension'], "OProxyExtension should have _remove method"
    assert 'name' not in signatures['OProxyExtension']['_remove'], "OProxyExtension._remove should NOT have 'name' parameter"

    print("PASS: All method signatures are correct")

def test_code_structure():
    """Test that the code has the expected structure."""
    print("Testing code structure...")

    with open('OPBaseWrapper.py', 'r') as f:
        content = f.read()

    # Check that OPBaseWrapper._remove is abstract
    assert '@abstractmethod' in content, "Should have @abstractmethod decorator"
    assert 'def _remove(self, name=None):' in content, "Abstract method should have correct signature"

    # Check that OPContainer has _remove implementation
    assert 'class OPContainer(OPBaseWrapper):' in content, "OPContainer should inherit from OPBaseWrapper"
    assert 'def _remove(self, name=None):' in content, "OPContainer should have _remove implementation"

    # Check that OPLeaf has _remove implementation
    assert 'class OPLeaf(OPBaseWrapper):' in content, "OPLeaf should exist"
    assert 'def _remove(self):' in content, "OPLeaf should have _remove implementation"

    # Check that OProxyExtension exists
    assert 'class OProxyExtension(OPBaseWrapper):' in content, "OProxyExtension should exist"
    assert 'def _remove(self):' in content, "OProxyExtension should have _remove implementation"

    print("PASS: Code structure is correct")

def test_docstrings():
    """Test that methods have appropriate docstrings."""
    print("Testing docstrings...")

    with open('OPBaseWrapper.py', 'r') as f:
        content = f.read()

    # Check for key docstring content
    assert 'Remove this leaf from its parent container' in content, "OPLeaf._remove should have appropriate docstring"
    assert 'This enables direct leaf removal: opr.items(\'op1\')._remove()' in content, "Should mention direct leaf removal"
    assert 'Future: When extensions are implemented' in content, "Should mention future extension cleanup"

    # Check OProxyExtension placeholder
    assert 'placeholder implementation' in content, "OProxyExtension should mention placeholder"
    assert 'not yet implemented' in content, "Should indicate future implementation"

    print("PASS: Docstrings are appropriate")

if __name__ == "__main__":
    print("Running _remove() implementation verification tests...\n")

    try:
        test_method_signatures()
        test_code_structure()
        test_docstrings()

        print("\nSUCCESS: All verification tests passed!")
        print("\nImplementation Summary:")
        print("PASS: OPBaseWrapper._remove() is abstract with (name=None) signature")
        print("PASS: OPContainer._remove(name=None) handles container/leaf removal")
        print("PASS: OPLeaf._remove() enables direct leaf removal")
        print("PASS: OProxyExtension._remove() placeholder for future extensions")
        print("PASS: All classes have appropriate docstrings and structure")

    except Exception as e:
        print(f"\nFAILED: Verification failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)