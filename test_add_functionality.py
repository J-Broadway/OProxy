#!/usr/bin/env python3
"""
Simple test script to validate _add method functionality without TouchDesigner dependencies.
Tests the basic logic flow and method signatures by inspecting source code.
"""

import sys
import os
import inspect
import ast

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def check_method_exists(filename, method_name):
    """Check if a method exists in the source file"""
    with open(filename, 'r') as f:
        content = f.read()

    # Simple check - method definition exists
    method_def = f"def {method_name}("
    return method_def in content

def check_method_calls(filename, method_name, expected_calls):
    """Check if a method calls other expected methods"""
    with open(filename, 'r') as f:
        content = f.read()

    # Find all method definitions
    lines = content.split('\n')
    method_starts = []
    for i, line in enumerate(lines):
        if line.strip().startswith(f"def {method_name}("):
            method_starts.append(i)

    if not method_starts:
        return False

    # Check each method definition (skip abstract ones)
    for method_start in method_starts:
        method_lines = []
        base_indent = len(lines[method_start]) - len(lines[method_start].lstrip())

        for i in range(method_start + 1, len(lines)):
            line = lines[i]
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
            if line.strip().startswith(('def ', 'class ')) and current_indent <= base_indent:
                break
            method_lines.append(line)

        method_content = '\n'.join(method_lines)

        # Skip abstract methods (contain just 'pass')
        if method_content.strip() == 'pass':
            continue

        # Check for expected calls in this implementation
        all_calls_found = True
        for call in expected_calls:
            if call not in method_content:
                all_calls_found = False
                break

        if all_calls_found:
            return True

    return False

def test_validation_function():
    """Test the _validate_child_name function exists and has proper structure"""
    print("Testing _validate_child_name function...")

    if not check_method_exists('OPBaseWrapper.py', '_validate_child_name'):
        print("FAIL: _validate_child_name method not found")
        return False

    print("PASS: _validate_child_name method exists")
    return True

def test_add_init_method():
    """Test that _add_init method exists"""
    print("Testing _add_init method...")

    if not check_method_exists('OPBaseWrapper.py', '_add_init'):
        print("FAIL: _add_init method not found")
        return False

    print("PASS: _add_init method exists")
    return True

def test_add_insert_method():
    """Test that _add_insert method exists"""
    print("Testing _add_insert method...")

    if not check_method_exists('OPBaseWrapper.py', '_add_insert'):
        print("FAIL: _add_insert method not found")
        return False

    print("PASS: _add_insert method exists")
    return True

def test_main_add_refactored():
    """Test that main _add method has been refactored to use init/insert"""
    print("Testing main _add method refactoring...")

    if not check_method_exists('OPBaseWrapper.py', '_add'):
        print("FAIL: _add method not found")
        return False

    # Check that _add calls _add_init and _add_insert
    expected_calls = ['self._add_init(', 'self._add_insert(']
    if not check_method_calls('OPBaseWrapper.py', '_add', expected_calls):
        print("FAIL: _add method doesn't call _add_init and _add_insert")
        return False

    print("PASS: _add method appears to be properly refactored")
    return True

def test_docstring_updated():
    """Test that the _add method has a comprehensive docstring"""
    print("Testing _add method docstring...")

    with open('OPBaseWrapper.py', 'r') as f:
        content = f.read()

    # Find the concrete _add method (not the abstract one)
    lines = content.split('\n')
    in_concrete_method = False
    docstring_found = False

    for i, line in enumerate(lines):
        if line.strip().startswith('def _add(self, name, op):'):
            # Check if this is the concrete implementation (not abstract)
            # Look ahead to see if it has a docstring and real implementation
            for j in range(i + 1, min(i + 20, len(lines))):
                check_line = lines[j].strip()
                if check_line.startswith('"""') or check_line.startswith("'''"):
                    docstring_found = True
                    break
                elif check_line == 'pass':
                    # This is the abstract method
                    break
                elif check_line and not check_line.startswith('#'):
                    # Found actual implementation code
                    in_concrete_method = True

            if in_concrete_method and docstring_found:
                print("PASS: _add method has docstring")
                return True

    if not in_concrete_method:
        print("FAIL: Could not find concrete _add method implementation")
    elif not docstring_found:
        print("FAIL: _add method implementation has no docstring")
    else:
        print("FAIL: Could not verify docstring")

    return False

def main():
    """Run all tests"""
    print("Running OProxy _add enhancement tests...\n")

    tests = [
        test_validation_function,
        test_add_init_method,
        test_add_insert_method,
        test_main_add_refactored,
        test_docstring_updated
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"FAIL: Test failed with exception: {e}\n")

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tests passed! Implementation looks good.")
        return 0
    else:
        print("ERROR: Some tests failed. Please review the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
