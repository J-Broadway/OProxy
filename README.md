# OProxy

OProxy is an operator proxy system for TouchDesigner that provides a hierarchical container pattern for organizing and managing operators. It enables dynamic extension of containers and leaves with custom functionality from Text DATs.

## Overview

OProxy uses the Composite Design Pattern to create a tree structure of containers and leaves:
- **Containers**: Organize operators and sub-containers hierarchically
- **Leaves**: Proxy individual TouchDesigner operators
- **Extensions**: Dynamically add custom methods/classes from DATs

All hierarchy and extensions persist across project sessions via TouchDesigner storage.

## Setup

OProxy is used alongside TouchDesigner extensions. Create an extension file (e.g., `src.py`) in your component:

```python
from TDStoreTools import StorageManager 
import TDFunctions as TDF
oproxy = mod('OProxy/oproxy')

class src:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.OProxy = oproxy.root(ownerComp)
```

Access OProxy from any DAT in the component:

```python
opr = parent.src.OProxy
```

## Main Functions

### `_add(name, op, returnObj=False)`

Add operators to a container. Creates a new container if it doesn't exist, or adds to an existing container.

**Parameters:**
- `name` (str): Container name
- `op`: Single operator name (str) or list of operator names
- `returnObj` (bool): If True, returns the container; otherwise returns self for chaining

**Examples:**

```python
# Create new container with operators
opr._add('Media', ['moviefilein1', 'moviefilein2'])

# Add more operators to existing container
opr._add('Media', ['moviefilein3', 'moviefilein4'])

# Add single operator
opr._add('Media', 'moviefilein5')

# Nested containers
opr._add('effects', ['blur1', 'level1'])
opr.effects._add('advanced', ['glow1', 'sharpen1'])
```

### `_remove(name=None)`

Remove containers, leaves, or extensions.

**Usage:**
- `container._remove()` - Remove this container from its parent
- `container._remove('child')` - Remove named child
- `container._remove(['child1', 'child2'])` - Remove multiple children
- `extension._remove()` - Remove this extension

**Examples:**

```python
# Remove a child container
opr._remove('Media')

# Remove multiple children
opr._remove(['effects', 'advanced'])

# Remove self from parent
opr.effects._remove()
```

### `_tree(indent="")`

**Note:** This method has not been implemented yet.

### `_refresh(target=None)`

Refresh container and all descendants. Rebuilds the hierarchy from storage and reapplies extensions/monkey patches.

**Parameters:**
- `target` (optional): Specific container/leaf to refresh

**Example:**

```python
# Refresh entire hierarchy from root
opr._refresh()

# Refresh specific branch
opr.effects._refresh()
```

### `_storage(keys=None, as_dict=False)`

Access storage data for the container hierarchy.

**Parameters:**
- `keys` (optional): Specific storage keys to retrieve
- `as_dict` (bool): Return as plain dict instead of DependDict

**Example:**

```python
# Get all storage data
storage = opr._storage()

# Get specific keys
children = opr._storage(keys=['children'])

# Get as plain dict
data = opr._storage(as_dict=True)
```

### `_clear(flush_logger=True)`

Clear all stored OProxy data and reload empty hierarchy. Only works on root containers.

**Parameters:**
- `flush_logger` (bool): Whether to flush the logger

**Example:**

```python
opr._clear()  # Clears entire hierarchy
```

## Accessing Operators

### By Name (Function Call)

```python
opr.video('moviefilein1')
```

### By Index

```python
opr.video[0]  # First operator in container
```

### Iteration

```python
# Iterate over all operators in container
for op in opr.video:
    print(op.path)
    op.par.file = '/path/to/video.mov'
```

### Setting Parameters

```python
# Set parameter on specific operator
opr.video('moviefilein1').par.file = '/path/to/video.mov'

# Set parameter on all operators in container
for op in opr.video:
    op.par.playmode = 0
```

## `_extend()` - Dynamic Extensions

The `_extend()` method allows you to dynamically add functions, classes, or other callable objects from TouchDesigner Text DATs to containers or leaves.

### Basic Syntax

```python
container._extend(attr_name, func='functionName', dat='dat_name')
container._extend(attr_name, cls='ClassName', dat='dat_name')
```

### Parameters

- `attr_name` (str): Name to assign to the extension (defaults to func/cls name if not provided)
- `cls` (str, optional): Class name to extract from the DAT
- `func` (str, optional): Function name to extract from the DAT
- `dat` (str or DAT object): Source DAT containing the code (required)
- `args` (list/tuple, optional): Arguments for initial call when `call=True`
- `call` (bool): If True, execute immediately and return callable (default: False)
- `monkey_patch` (bool): Allow overwriting existing attributes (default: False)
- `returnObj` (bool): If True, returns the extension object instead of self (default: False)

### Function Extensions

**DAT content (`extensions_dat`):**
```python
def calculateAverage(self, values):
    return sum(values) / len(values) if values else 0
```

**Usage:**
```python
opr._extend('avg', func='calculateAverage', dat='extensions_dat')
result = opr.avg([1, 2, 3, 4, 5])  # Returns 3.0
```

### Class Extensions

**DAT content:**
```python
class DataProcessor:
    def __init__(self, config):
        self.config = config
    
    def process(self, data):
        return data * self.config['multiplier']
```

**Usage:**
```python
# Instantiate immediately with call=True
processor = opr._extend('processor', cls='DataProcessor', dat='extensions_dat', 
                        args=[{'multiplier': 2}], call=True)
result = processor.process(5)  # Returns 10

# Or extend without instantiation
MyClass = opr._extend('my_class', cls='MyClass', dat='extensions_dat')
instance = MyClass()  # Instantiate when ready
```

### Optional 'self' Parameter

Extensions can optionally include a `self` parameter to access container methods:

**With 'self' (recommended for container access):**
```python
def myFunction(self, arg1, arg2):
    # 'self' refers to the container
    self.some_container_method()
    return arg1 + arg2
```

**Without 'self' (utility functions):**
```python
def utilityFunction(arg1, arg2):
    # Cannot access container methods
    return arg1 + arg2
```

### Chaining Extensions

```python
opr._extend('func1', func='func1', dat='ext_dat') \
    ._extend('func2', func='func2', dat='ext_dat') \
    ._extend('func3', func='func3', dat='ext_dat')
```

### Using `call=True`

When `call=True`, the extension is executed immediately with provided args, but the callable is returned for future use:

```python
# Execute immediately and get callable for later use
test_func = opr._extend('test', func='myTestFunc', dat='extensions', 
                        args=['initial_arg'], call=True)

# Function was called with 'initial_arg' during extension
# Now test_func is callable for future use
result = test_func('another_arg')
```

**With classes:**
```python
class Counter:
    def __init__(self, start=0):
        self.value = start
    
    def increment(self):
        self.value += 1
        return self.value

# call=True usage
counter = opr._extend('counter', cls='Counter', dat='extensions', 
                      args=[10], call=True)
# Counter instantiated with start=10, counter is the instance
current = counter.increment()  # Returns 11
```

### Using `returnObj=True`

Get the extension object directly instead of the container:

```python
func = opr._extend('my_func', func='myFunctionName', dat='my_dat', returnObj=True)
result = func(arg1, arg2)
```

### Monkey Patching

Use `monkey_patch=True` to replace existing containers or leaves with custom subclasses:

```python
# Create container
opr._add('items', ['op1', 'op2'])

# Replace with custom subclass
opr._extend('items', cls='CustomContainer', dat='monkey_patches', monkey_patch=True)

# For leaves
opr.items._extend('op1', cls='CustomLeaf', dat='monkey_patches', monkey_patch=True)
```

**Note:** Extensions cannot be monkey-patched; remove and re-extend instead.

### Extension Chaining

Extensions can extend other extensions:

```python
opr._extend('base', func='baseFunc', dat='ext_dat')
opr.base._extend('nested', func='nestedFunc', dat='ext_dat')
```

## Complete Example

```python
# Setup (in extension file)
opr = parent.src.OProxy

# Create containers
opr._add('video', ['moviefilein1', 'moviefilein2'])
opr._add('effects', ['blur1', 'level1'])
opr.effects._add('advanced', ['glow1'])

# Extend with custom functionality
opr._extend('processVideo', func='processVideo', dat='video_utils')
opr.effects._extend('applyBlur', func='applyBlur', dat='effect_utils')

# Use extensions
opr.processVideo(opr.video[0])
opr.effects.applyBlur(5.0)

# Access operators
for op in opr.video:
    print(op.path)
    op.par.file = '/path/to/video.mov'

# View hierarchy
print(opr._tree())
```

## Error Handling

OProxy provides detailed error messages for:
- Missing DAT parameter
- Invalid DAT object
- Function/class not found in DAT
- Signature validation errors
- Execution failures during `call=True`
- Naming conflicts (use `monkey_patch=True` to overwrite)

## Best Practices

1. **Use 'self' for container access**: Include `self` as the first parameter to access container methods
2. **Use `call=True` for initialization**: When you need to both initialize and store a callable
3. **Name extensions clearly**: Use descriptive names that indicate purpose
4. **Handle errors**: Check for extension creation failures in production code
5. **Organize hierarchically**: Use nested containers to organize related operators

## Storage

OProxy automatically persists:
- Container hierarchy
- Operator references
- Extensions and their metadata
- Monkey patch information

Storage uses TouchDesigner's StorageManager and persists across project sessions.

## Architecture

OProxy follows the Composite Design Pattern:
- `OProxyBaseWrapper`: Abstract base class
- `OProxyContainer`: Composite - contains children
- `OProxyLeaf`: Leaf - proxies single operator
- `OProxyExtension`: Extension wrapper for dynamic functionality

All components support the same interface (`_add`, `_remove`, `_tree`, `_refresh`, `_extend`).

