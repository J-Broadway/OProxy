opr = parent.src.OProxy
''' Notes for LLM
	Please do not edit unless explicitly asked
'''

# _add tests
opr._add('items', ['op1','op2','op3']) # Create OPContainer Item

# Test container length
print('OPContainer Length:', len(opr.items))

# Test iteration over items
print('Iterating through OPs:')
for i in opr.items:
	print(f'  OP name: {i.name}')

# Test setting parameters on all items
print('Setting playmode to 0 on all OPs...')
for i in opr.items:
	i.par.playmode = 0

# Test getting parameters from all items
print('Current playmode values (should be locked):')
for i in opr.items:
	print(f'  {i.name}.par.playmode is {i.par.playmode}')

# Bring back to default
print('Resetting playmode to 2...')
for i in opr.items:
	i.par.playmode = 2

# Test individual access by name (function call syntax)
print('Access by name:')
print(f"opr.items('op1').width = {opr.items('op1').width}")

# Test individual access by index
print('Access by index:')
print(f"opr.items[1].height = {opr.items[1].height}")

# Test error handling for non-existent OP
try:
    opr.items('nonexistent')
    print('ERROR: Should have raised KeyError')
except KeyError as e:
    print(f'Correctly caught KeyError: {e}')

# Test string representation
print('Container representation:')
print(opr.items)

# Test nested containers and storage persistence
print('\n=== Testing nested containers and storage ===')

# Create nested structure
opr._add('level1', ['op1','op2'])
opr.level1._add('level2', ['op3','op4'])
opr.level1.level2._add('level3', ['op5','op6'])

print('Created nested structure: opr.level1.level2.level3')

# Can we access?
for i in opr.level1.level2.level3:
	print(i.name)

# Test access to deeply nested containers
print('Accessing nested containers:')
print(f'  Level 1 has {len(opr.level1)} OPs')
print(f'  Level 2 has {len(opr.level1.level2)} OPs')
print(f'  Level 3 has {len(opr.level1.level2.level3)} OPs')

# Test iteration through nested OPs
print('Iterating through level 3 OPs:')
for i in opr.level1.level2.level3:
    print(f'  {i.name}')

print('Nested container tests completed!')

# Test _remove functionality
print('\n=== Testing _remove functionality ===\n')
opr._add('more_items', ['op1','op2','op3'])
opr._add('even_more_items', ['op1','op2','op3'])
opr._add('omg_even_more_items', ['op1','op2','op3'])

opr._remove('items') # single removal
opr.more_items._remove() # remove like this
opr._remove(['even_more_items','omg_even_more_items']) # list removal


print('All _remove tests completed successfully!')
print('Dictionary contents:', parent.src.OProxy.OProxies)

#### PLEASE NEW TESTS UNDER HERE ####

# Test new _add functionality: adding to existing containers
print('\n=== Testing Enhanced _add Functionality ===\n')

# Test 1: Create new container (existing behavior)
print('Test 1: Creating new container with initial OPs')
opr._add('test_group', ['op1', 'op2'])
print(f'Created test_group with {len(opr.test_group)} OPs')
print(f'OPs in test_group: {[op.name for op in opr.test_group]}')

# Test 2: Add single OP to existing container (new behavior)
print('\nTest 2: Adding single OP to existing container')
opr._add('test_group', 'op3')
print(f'After adding op3: {len(opr.test_group)} OPs')
print(f'OPs in test_group: {[op.name for op in opr.test_group]}')

# Test 3: Add multiple OPs to existing container (new behavior)
print('\nTest 3: Adding multiple OPs to existing container')
opr._add('test_group', ['op4', 'op5'])
print(f'After adding op4, op5: {len(opr.test_group)} OPs')
print(f'OPs in test_group: {[op.name for op in opr.test_group]}')

# Test 4: Attempt to add duplicate OPs (should skip with logging)
print('\nTest 4: Testing duplicate OP handling')
opr._add('test_group', ['op1', 'op6'])  # op1 is duplicate, op6 is new
print(f'After adding duplicates: {len(opr.test_group)} OPs')
print(f'OPs in test_group: {[op.name for op in opr.test_group]}')

# Test 5: Create another new container to test mixed usage
print('\nTest 5: Creating second container')
opr._add('media_group', ['op1', 'op2'])
print(f'Created media_group with {len(opr.media_group)} OPs')

# Test 6: Add to media_group
print('\nTest 6: Adding to media_group')
opr._add('media_group', ['op3', 'op4'])
print(f'media_group now has {len(opr.media_group)} OPs')

# Test 7: Test validation - reserved names
print('\nTest 7: Testing name validation (reserved names)')
try:
    opr._add('_add', ['op1'])  # Should fail
    print('ERROR: Should have failed for reserved name _add')
except ValueError as e:
    print(f'Correctly caught ValueError for reserved name: {e}')

try:
    opr._add('path', ['op1'])  # Should fail
    print('ERROR: Should have failed for reserved name path')
except ValueError as e:
    print(f'Correctly caught ValueError for reserved name: {e}')

try:
    opr._add('__str__', ['op1'])  # Should fail
    print('ERROR: Should have failed for magic method __str__')
except ValueError as e:
    print(f'Correctly caught ValueError for magic method: {e}')

# Test 8: Test validation - conflicting with existing OP
print('\nTest 8: Testing name conflicts with existing OPs')
opr._add('single_op', 'op1')  # Creates container with one OP
try:
    opr._add('single_op', 'op2')  # Should fail - name conflicts with existing OP
    print('ERROR: Should have failed for name conflict with existing OP')
except ValueError as e:
    print(f'Correctly caught ValueError for name conflict: {e}')

# Test 9: Test that adding to non-existent sub-containers works
print('\nTest 9: Adding to existing sub-containers')
opr._add('nested_test', ['op1'])
opr.nested_test._add('sub_group', ['op2'])  # Creates sub-container
opr.nested_test._add('sub_group', ['op3'])  # Adds to existing sub-container
print(f'nested_test.sub_group has {len(opr.nested_test.sub_group)} OPs')

# Test 10: Clean up test containers
print('\nTest 10: Cleaning up test containers')
opr._remove(['test_group', 'media_group', 'single_op', 'nested_test'])
print('Test containers removed')

print('\n=== Enhanced _add Functionality Tests Completed Successfully! ===')

print('All tests completed successfully!')