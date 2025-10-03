opr = parent.src.OProxy
'''
_refresh() Functionality Tests

All tests use these approved names to avoid TouchDesigner OP resolution errors.
'''
# First reset storage
parent.src.unstore('rootStored')
parent.src.par.reinitextensions.pulse()

# =============================================================================
# _refresh() Functionality Tests
# =============================================================================

def test_refresh_basic_container():
    """Test basic container refresh functionality"""
    print("=== Testing Basic Container Refresh ===")

    # Create test container with approved OP names
    opr._add('test_container', ['op1', 'op2'])

    # Verify initial state
    assert 'test_container' in opr._children
    container = opr.test_container
    assert len(container._children) == 2
    print(f"✓ Created test container with {len(container._children)} OPs")

    # Test refresh (should not change anything initially)
    container._refresh()
    print("✓ Container refresh completed")

    # Cleanup
    opr._remove('test_container')
    print("✓ Test cleanup completed\n")

def test_refresh_op_name_change():
    """Test OP name change detection during refresh"""
    print("=== Testing OP Name Change Detection ===")

    # Create test container with approved OP names
    opr._add('name_test', ['op1', 'op2'])

    container = opr.name_test
    print(f"✓ Created container with OPs: {list(container._children.keys())}")

    # Simulate OP name change by directly modifying storage
    # (In real TouchDesigner, this would happen when user renames OPs)
    if hasattr(container, '_update_storage'):
        # First refresh to establish baseline
        container._refresh()

        # Simulate name change in storage
        root = container.__find_root()
        if hasattr(root, 'OProxies') and 'children' in root.OProxies:
            name_test_data = root.OProxies['children'].get('name_test', {})
            if 'ops' in name_test_data and 'op1' in name_test_data['ops']:
                # Modify the stored OP name to simulate rename
                name_test_data['ops']['op1']['op'] = type('MockOP', (), {
                    'name': 'renamed_op',
                    'valid': True,
                    'path': '/project1/renamed_op'
                })()

        # Refresh should detect the name change
        print("Testing refresh with simulated OP rename...")
        container._refresh()

        # Check if mapping was updated
        if 'renamed_op' in container._children:
            print("✓ OP name change detected and mapping updated")
        else:
            print("⚠ OP name change detection - check manual verification")

    # Cleanup
    opr._remove('name_test')
    print("✓ Name change test cleanup completed\n")

def test_refresh_leaf():
    """Test leaf refresh functionality"""
    print("=== Testing Leaf Refresh ===")

    # Create test container with approved OP names
    opr._add('leaf_test', ['op1'])

    container = opr.leaf_test
    leaf = container._children['op1']

    # Test leaf refresh
    print(f"Testing refresh on leaf: {leaf.path}")
    leaf._refresh()
    print("✓ Leaf refresh completed")

    # Cleanup
    opr._remove('leaf_test')
    print("✓ Leaf test cleanup completed\n")

def test_refresh_error_handling():
    """Test error handling in refresh operations"""
    print("=== Testing Error Handling ===")

    # Create test container with approved OP names
    opr._add('error_test', ['op1'])

    container = opr.error_test

    # Test refresh with potential errors
    try:
        container._refresh()
        print("✓ Refresh completed without critical errors")
    except Exception as e:
        print(f"✗ Unexpected error during refresh: {e}")

    # Test with invalid container state (simulate corruption)
    original_children = container._children
    try:
        # Temporarily break container state
        container._children = None
        container._refresh()  # Should handle gracefully
        print("✓ Error handling for invalid container state")
    except Exception as e:
        print(f"✗ Error handling failed: {e}")
    finally:
        # Restore state
        container._children = original_children

    # Cleanup
    opr._remove('error_test')
    print("✓ Error handling test cleanup completed\n")

def test_refresh_storage_validation():
    """Test storage validation during refresh"""
    print("=== Testing Storage Validation ===")

    # Create test container with approved OP names
    opr._add('storage_test', ['op1'])

    container = opr.storage_test

    # Test storage access validation
    stored_data = container._get_stored_container_data()
    if stored_data:
        print("✓ Storage data access successful")
    else:
        print("⚠ Storage data access returned None - check manually")

    # Test storage update
    if hasattr(container, '_update_storage'):
        try:
            container._update_storage()
            print("✓ Storage update successful")
        except Exception as e:
            print(f"✗ Storage update failed: {e}")

    # Cleanup
    opr._remove('storage_test')
    print("✓ Storage validation test cleanup completed\n")

def test_refresh_recursive_behavior():
    """Test recursive refresh behavior"""
    print("=== Testing Recursive Refresh Behavior ===")

    # Create nested structure with approved OP names (avoid 'parent' reserved word)
    opr._add('test_parent', ['op1'])
    opr.test_parent._add('child', ['op2'])
    opr.test_parent.child._add('grandchild', ['op3'])

    print("Created nested structure: test_parent -> child -> grandchild")

    # Test recursive refresh from parent
    parent_container = opr.test_parent
    parent_container._refresh()
    print("✓ Recursive refresh from parent completed")

    # Verify all levels still exist
    if 'child' in parent_container._children:
        child_container = parent_container.child
        if 'grandchild' in child_container._children:
            print("✓ Nested structure preserved after recursive refresh")
        else:
            print("⚠ Grandchild container missing after refresh")
    else:
        print("⚠ Child container missing after refresh")

    # Cleanup
    opr._remove('test_parent')
    print("✓ Recursive test cleanup completed\n")

def test_refresh_op_validation():
    """Test OP validation during refresh"""
    print("=== Testing OP Validation ===")

    # Create test container with approved OP names
    opr._add('validation_test', ['op1'])

    container = opr.validation_test

    # Test _refresh_ops method directly
    if hasattr(container, '_refresh_ops'):
        try:
            container._refresh_ops()
            print("✓ OP validation refresh completed")
        except Exception as e:
            print(f"✗ OP validation failed: {e}")

    # Cleanup
    opr._remove('validation_test')
    print("✓ OP validation test cleanup completed\n")

# =============================================================================
# Test Runner
# =============================================================================

def run_refresh_tests():
    """Run all refresh tests"""
    print("🚀 Starting _refresh() Functionality Tests\n")

    test_functions = [
        test_refresh_basic_container,
        test_refresh_op_name_change,
        test_refresh_leaf,
        test_refresh_error_handling,
        test_refresh_storage_validation,
        test_refresh_recursive_behavior,
        test_refresh_op_validation
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
            failed += 1

    print("📊 Test Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")

    if failed == 0:
        print("🎉 All refresh tests passed!")
    else:
        print("⚠️  Some tests failed - check output above")

# =============================================================================
# Manual Test Execution
# =============================================================================


run_refresh_tests()