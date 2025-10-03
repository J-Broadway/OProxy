# Test script to verify new storage structure works correctly
import td
opr = parent.src.OProxy

print("=== Testing New Storage Structure ===")

# Clear any existing test data
try:
    opr._remove(['test_storage'])
except:
    pass

# Create test container with OPs
print("1. Creating test container with OPs...")
opr._add('test_storage', ['constant1', 'constant2'])

# Check that OPs were added
print(f"   Container length: {len(opr.test_storage)}")
print(f"   OPs: {[op.name for op in opr.test_storage]}")

# Force storage save
print("2. Saving to storage...")
opr._save_to_storage()

# Check storage structure
print("3. Checking storage structure...")
storage = opr.OProxies
print(f"   Storage keys: {list(storage.keys())}")

if 'children' in storage and 'test_storage' in storage['children']:
    container_data = storage['children']['test_storage']
    print(f"   Container keys: {list(container_data.keys())}")

    if 'ops' in container_data:
        ops_data = container_data['ops']
        print(f"   OPs structure: {ops_data}")

        # Verify new nested structure
        for op_name, op_info in ops_data.items():
            if isinstance(op_info, dict) and 'path' in op_info and 'extensions' in op_info:
                print(f"   ✓ {op_name}: New nested structure (path: {op_info['path']}, extensions: {op_info['extensions']})")
            else:
                print(f"   ✗ {op_name}: Still old structure - {op_info}")

# Test refresh (reload from storage)
print("4. Testing refresh from storage...")
opr._refresh()

# Verify OPs still exist after refresh
print(f"   After refresh - Container length: {len(opr.test_storage)}")
print(f"   After refresh - OPs: {[op.name for op in opr.test_storage]}")

# Clean up
print("5. Cleaning up...")
opr._remove(['test_storage'])

print("=== Storage Structure Test Complete ===")


