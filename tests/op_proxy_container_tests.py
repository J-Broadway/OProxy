# op_proxy_container_tests.dat this test is run second

opr = parent.src.OProxy

# op_proxy_and_OPcontainer_tests
"""testing implementation of Refactor_OPContainer_OP_Proxy.txt"""
opr._tree(detail='minimal')

# Accessing individual parameters
t = opr.top('changed')
print(t.width, t.height, "width & height")

# Check setting params
for op in opr.top:
	print(op.bypass, "<--- should print False") # Should print false
	op.bypass = True

# change back
for op in opr.top:
	print(op.bypass, "<--- should print True") # Should print true
	op.bypass = False


# Testing _add() to individual items
opr.top('changed')._add('tables', ['table1', 'table2', 'table3'])

# Should be accessable
for i in opr.top('changed').tables:
	print(i.name)

opr._tree(detail='minimal')
print('\nNow Full Tree\n')
opr._tree()

