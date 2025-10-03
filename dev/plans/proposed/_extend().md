def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
	"""
	Extend the proxy class with an attribute or method using ast_mod for DAT-based extraction.
	'cls' or 'func' specifies the class or function name to extract from 'dat'; if neither, 'value' is used directly.
	'args' is a tuple/list of positional arguments for instantiation/calling when call=True.
	
	**Parameters:**
	- `attr_name` (str): Extension name if left blank will default to name passed to either func or cls)
	- `cls` (str): Class name to extract (optional)
	- `func` (str): Function name to extract (optional)
	- `dat` (DAT): Text DAT containing extension (REQUIRED)
	- `args` (tuple|list): Arguments for instantiation/calling (optional)
	- `call` (bool): Whether to instantiate/call immediately
	- `monkey_patch`: Placeholder arg for future
	"""
	
# Example Usage

```python
ops = ['moviefilein1','moviefilein2','moviefilein3']
opr._add('videos', ops)

# Can define function in same DAT where _extend() is called thanks to mod_AST()
def resize_videos(self, width, height):
	for op in self: # self is OPContainer, can iterate over OPLeaves
		self.par.outputresolution = 'custom' # Set to 'custom' so resolution can actually be changed
		self.par.resolutionw = self.width
		self.par.resolutionh = self.height

# Apply extensions to videos container (dat parameter required for persistence)
opr.videos._extend('resize', func='resize_videos', dat=me)

# Can now use extension
opr.videos.resize()
```

### Extension Classes

```python
# myExtensions.dat
class myClass:
	def __init__(self, hey, adding):
		self.hey = hey
		self.adding = adding
	def testing(self):
		return self.hey, self.adding 

def new_func(self):
	print('test1 working')

def another(self):
	print('another function ran!')
	
def func_with_args(self, one, two):
	print(self.one, self.two)
```

```py
# somewhereelse.dat
chops = ['constant1','constant2','constant3']
opr._add('chops', chops)

# Extend via function with call=False
opr.chops._extend('test', func='new_func', dat='myExtensions', call=False)
opr.chops.test() # should print 'test1 working'

# Extend leaf with function with call=false # does current architecture allow for this sort of extension?
myVar = opr.chops('constant2')._extend('another', func='another', dat='myExtensions', call=False)
opr.chops('constant2').another() # should print 'another function ran!'
myVar() # should be effectively the same as opr.chops('constant2').another() thus printing 'another function ran!'

# Using call=True will call the function during _extend()
myVar = opr.chops('constant2')._extend('another', func='another', dat='myExtensions', call=True) # prints 'another function ran!' since call=True
myVar # effectively the same as above

# If extending by func and call=True and function expects args, args must be provided
opr.chops._extend('example', func='func_with_args', dat='myExtensions', args=['hello','world'], call=True) # Should print 'helloworld'
# If call=True and function expects args and args not provided raise error.
# However if call=False (which is the default) and function expects arguments no error should be raised since function call is delgated to user responsibility (see below example)
sup = opr.chops._extend('example', func='func_with_args', dat='myExtensions') # function not called
sup(hello, world) # user calls with args
opr.chops.example(hello, world) # effectively the same as above

# Extend OPContainer by class with call=False
opr.chops._extend('test_class', cls='myClass', dat='myExtensions', call=False)
initiate = opr.chops.test_class('test3', 'args working') # must manually initiate since call=False
msg = initiate.testing()
print(msg) # should print ['test3', 'args working']

# With classes when call=True should auto initiate with passed args
myVar = opr.chops._extend('test_class', cls='myClass', dat=me, call=True, args=['test4', 'args working'])
msg = myVar.test_class.testing() # can access now
print(msg) # should print [self.hey, self.adding]
```

# Important Information
- 'call' arg is crucially important as False/True directly relates to how functions/classes are called/initiated
- For 'dat' arg we should be able to use utils.td_isinstance() to check if type DAT. User should be able to define extensions in the same DAT using dat=me thanks to mod_AST
- cls and func cannot be used in the same _extend() it must be either one or the other
- Naming conflicts: if opr._extend('name') but opr.name already exists and monkey_patch=False raise an error stating that 'name' already exists, to overwrite use monkey_patch=True, refer to documentation for proper usage.
- Does the current codebase architecture allow for _extend() to work on OPLeafs?

# Proposed storage structure for _extend()
```
'extensions': {
    'attr_name': {
        'cls': 'ClassName',  # or None
        'func': 'funcName',  # or None  
        'dat_path': '/path/to/dat',
        'call': False,
        'args': None,
        'monkey_patch': False
    }
}
```