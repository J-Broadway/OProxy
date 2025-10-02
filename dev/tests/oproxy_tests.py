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



print('All tests completed successfully!')