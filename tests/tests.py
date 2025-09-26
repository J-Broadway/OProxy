#tests.dat this test is run first

opr = parent.src.OProxy

# Extension/function definitions for testing

def new_func(self):
	print('test1 working')

def another(self):
	print('test2 working (I should print twice)')
	
class myClass:
	def __init__(self, hey, adding):
		self.hey = hey
		self.adding = adding
	def testing(self):
		return self.hey, self.adding

# Test adding
opr._add('chops', ['test', op('constant2'), op('constant3')])

# Test removing branch
opr.chops._remove()
opr._add('chops', ['test', op('constant2'), op('constant3')]) # re-add

# Test removing item
opr.chops('constant2')._remove()
check = []
for i in opr.chops:
	print(f"Revmoed Testing - {i.name}")
	check.append(i.name)
	if 'constant2' not in check:
		print('IT WORKED AND CONSTNAT 2 WAS NOT FOUND')
	else:
		print('------------------ CHECK IF _remove() IS WORKING')
		
opr._add('chops', ['test', op('constant2'), op('constant3')]) # re-add

# Test adding extension referencing 'new_func' above
opr.chops._extend('test', func='new_func', dat=me, call=False)
opr.chops.test() # should print 'test1 working'


# Test adding another extension with call=false
opr.chops('constant2')._extend('another', func='another', dat=me, call=False)
opr.chops('constant2').another() # should print 'test2 working (I should print twice)'
# Same test as above but with call=True should call the function thus printing another() twice
opr.chops('constant2')._extend('another', func='another', dat=me, call=True)
# Test adding extension by class
opr.chops._extend('test_class', cls='myClass', dat=me, call=False)
initiate = opr.chops.test_class('test3', 'args working')
msg = initiate.testing()
print(msg) # should print ['test3', 'args working']
# Same test as above but with call=True should auto initiate with passed args
opr.chops._extend('test_class', cls='myClass', dat=me, call=True, args=['test4', 'args working'])
myvar = opr.chops.test_class.testing()
print(myvar)


# Add more stuff for tree testing
opr._add('top', ['changed', 'moviefilein2', 'moviefilein3', 'moviefilein4']) # add top container
opr.top('changed')._add('nested', ['changed', 'moviefilein2', 'moviefilein3', 'moviefilein4']) # add 'nested' container specific to 'changed' top
opr.top('changed').nested._add('nest_in_nest', ['changed', 'moviefilein2', 'moviefilein3', 'moviefilein4']) # nest in nest test

# testing tree nested structure
print('Detail="minimal" #############################################################')
opr._tree(detail='minimal')
print('\nDetail="full" #############################################################')
opr._tree()

print('\ntests successful now will run op_proxy_container_tests\n')