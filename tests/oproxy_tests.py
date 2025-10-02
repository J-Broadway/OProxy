opr = parent.src.OProxy

# _add tests

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
print('Current playmode values:')
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

print('All tests completed successfully!')