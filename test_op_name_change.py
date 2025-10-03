# Test script to verify OP name change detection and storage refactoring
import td

def test_op_name_change_detection():
    """Test that _refresh() can detect OP name changes and properly re-attach OPLeaf objects"""
    print("=== Testing OP Name Change Detection ===")

    # Get the OProxy root
    opr = parent.src.OProxy

    # Clean up any existing test data
    try:
        opr._remove(['test_name_change'])
    except:
        pass

    # Create test container with OPs
    print("1. Creating test container with OPs...")
    opr._add('test_name_change', ['constant1', 'constant2'])

    # Check that OPs were added
    print(f"   Container length: {len(opr.test_name_change)}")
    print(f"   OPs: {[op.name for op in opr.test_name_change]}")

    # Force storage save
    print("2. Saving to storage...")
    opr._save_to_storage()

    # Check storage structure includes OP objects
    print("3. Checking storage structure includes OP objects...")
    storage = opr.OProxies
    if 'children' in storage and 'test_name_change' in storage['children']:
        container_data = storage['children']['test_name_change']
        if 'ops' in container_data:
            ops_data = container_data['ops']
            print(f"   OPs structure: {list(ops_data.keys())}")

            # Verify new structure with OP objects
            for op_name, op_info in ops_data.items():
                if isinstance(op_info, dict) and 'path' in op_info and 'op' in op_info and 'extensions' in op_info:
                    stored_op = op_info['op']
                    print(f"   ✓ {op_name}: New structure (path: {op_info['path']}, op: {stored_op}, extensions: {op_info['extensions']})")
                    print(f"      Stored OP name: {stored_op.name}, valid: {stored_op.valid}")
                else:
                    print(f"   ✗ {op_name}: Still old structure - {op_info}")

    # Now simulate name change by renaming one of the OPs
    print("4. Simulating OP name change...")
    test_op = opr.test_name_change.constant1._op  # Get the actual TD OP object
    original_name = test_op.name
    new_name = "renamed_constant1"

    print(f"   Renaming '{original_name}' to '{new_name}'...")
    test_op.name = new_name

    # Verify the OP name actually changed
    print(f"   OP name after rename: {test_op.name}")

    # Now call refresh and see if it detects the name change
    print("5. Calling _refresh() to detect name changes...")
    opr._refresh()

    # Check if the container now has the renamed OP
    print("6. Checking if refresh detected name change...")
    print(f"   Container children: {list(opr.test_name_change._children.keys())}")

    # Check if we can access the OP by its new name
    if hasattr(opr.test_name_change, new_name):
        print(f"   ✓ OP accessible by new name '{new_name}'")
        print(f"      OP path: {opr.test_name_change[new_name]._op.path}")
    else:
        print(f"   ✗ OP not accessible by new name '{new_name}'")

    # Check if old name still exists (it shouldn't)
    if hasattr(opr.test_name_change, original_name):
        print(f"   ✗ Old name '{original_name}' still exists")
    else:
        print(f"   ✓ Old name '{original_name}' properly removed")

    # Clean up
    print("7. Cleaning up...")
    opr._remove(['test_name_change'])

    print("=== OP Name Change Detection Test Complete ===")

# Run the test
test_op_name_change_detection()
