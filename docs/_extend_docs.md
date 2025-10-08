# OProxy _extend Feature Documentation

## Overview

The `_extend` method allows you to dynamically add functions, classes, or other callable objects from TouchDesigner DATs to OProxy containers or leaves. This provides a flexible extension system for building modular TouchDesigner projects.

## Basic Usage

```python
# Add a function to a container and chain
container._extend('my_function', func='myFunctionName', dat='my_dat')._extend('another', ...)

# Get the extension object directly
func = container._extend('my_func', func='myFunctionName', dat='my_dat', returnObj=True)
result = func(arg1, arg2)
```

## Parameters

- `attr_name` (str): Name to assign to the extension
- `cls` (str, optional): Class name to extract from the DAT
- `func` (str, optional): Function name to extract from the DAT
- `dat` (str or DAT object): Source DAT containing the code
- `args` (list or tuple, optional): Arguments for initial call when `call=True`
- `call` (bool, optional): Whether to execute immediately and return callable
- `monkey_patch` (bool, optional): Allow overwriting existing attributes
- `returnObj` (bool, optional): If True, returns the extension object instead of self (for chaining). Defaults to False.

## Key Features

### 1. Flexible Callable Types

The `_extend` method supports extending with:
- **Functions**: Standard Python functions
- **Classes**: Instantiated classes or class constructors
- **Other callables**: Any object with `__call__` method

### 2. Optional 'self' Parameter

Extensions can optionally include a `self` parameter:

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

### 3. call=True Feature

When `call=True`, the extension is executed immediately with provided args, but the callable is returned for future use:

```python
# Execute immediately and get callable for later use
test_func = container._extend('test', func='myTestFunc', dat='extensions', args=['initial_arg'], call=True)

# Function was called with 'initial_arg' during extension
# Now test_func is callable for future use
result = test_func('another_arg')
```

This enables patterns like:
```python
# One-liner: extend, call once, and store for reuse
my_tool = container._extend('tool', func='createTool', dat='tools', args=[config], call=True)
my_tool.process(data1)
my_tool.process(data2)
```

## Examples

### Function Extension

```python
# DAT content (extensions_dat):
def calculateAverage(self, values):
    return sum(values) / len(values) if values else 0

# Usage:
container._extend('avg', func='calculateAverage', dat='extensions_dat')
result = container.avg([1, 2, 3, 4, 5])  # Returns 3.0
```

### Class Extension

```python
# DAT content:
class DataProcessor:
    def __init__(self, config):
        self.config = config

    def process(self, data):
        return data * self.config['multiplier']

# Usage:
processor = container._extend('processor', cls='DataProcessor', dat='extensions_dat', args=[{'multiplier': 2}], call=True)
result = processor.process(5)  # Returns 10

# Or for manual instantiation:
my_class = container._extend('my_class', cls='MyClass', dat='extensions_dat')
instance = my_class()  # Instantiate when ready
result = instance.some_method()
```

### Utility Function (no self)

```python
# DAT content:
def formatTimestamp(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

# Usage:
container._extend('format_time', func='formatTimestamp', dat='extensions_dat')
formatted = container.format_time(time.time())
```

## call=True Behavior

The `call=True` parameter provides a convenient way to both initialize and store callable extensions:

1. **Execution**: The extension is called once with provided `args`
2. **Return Value**: Returns the callable extension (not the container)
3. **Storage**: The extension is still accessible via `container.extension_name`

### With Functions

```python
# Extension with self
def setupLogger(self, level):
    self.logger = Logger(level)
    return "Logger initialized"

# call=True usage
logger_func = container._extend('setup_logger', func='setupLogger', dat='extensions', args=['DEBUG'], call=True)
# Function executed with 'DEBUG', logger_func is now callable for reuse
logger_func('INFO')  # Execute again with different level
```

### With Classes

```python
class Counter:
    def __init__(self, start=0):
        self.value = start

    def increment(self):
        self.value += 1
        return self.value

# call=True usage
counter = container._extend('counter', cls='Counter', dat='extensions', args=[10], call=True)
# Counter instantiated with start=10, counter is the instance
current = counter.increment()  # Returns 11
```

## Error Handling

The extension system provides detailed error messages for common issues:

- Missing DAT parameter
- Invalid DAT object
- Function/class not found in DAT
- Signature validation errors
- Execution failures during `call=True`

## Best Practices

1. **Use 'self' for container access**: Include `self` as the first parameter to access container methods and properties
2. **Use call=True for initialization**: When you need to both initialize and store a callable
3. **Name extensions clearly**: Use descriptive names that indicate the extension's purpose
4. **Handle errors**: Check for extension creation failures in production code

## Implementation Details

- Extensions are wrapped in `OProxyExtension` objects for consistent interface
- Functions with 'self' are bound to the container automatically
- Extensions are stored in the container's internal registry for management
- Storage is updated automatically when extensions are added
- mod_AST extracts code blocks and resolves simple undefined variables by prepending their definitions, but this may not work reliably with TouchDesigner-specific functions like mod() due to execution context. For such cases, use wrapper classes as described in best practices.

## API Compatibility

- `call=False` (default): Returns the container, maintains backward compatibility
- `call=True`: Returns the callable extension for flexible usage patterns
- Optional 'self' parameter: Supports both bound and unbound function patterns

## Monkey-Patching Existing Containers/Leaves

Use `monkey_patch=True` with `cls` and `dat` to replace an existing container or leaf with a custom subclass, preserving state.

**Parameters for monkey_patch=True:**
- Only `attr_name`, `cls`, `dat` supported
- `func`, `args`, `call` not allowed

**Example:**
opr._add('items', ['op1', 'op2'])  # Create container
opr._extend('items', cls='CustomContainer', dat='monkey_patches', monkey_patch=True)  # Replace with subclass

**Leaf Example:**
opr.items._extend('op1', cls='CustomLeaf', dat='monkey_patches', monkey_patch=True)

Extensions cannot be monkey-patched; remove and re-extend instead.

See extend_monkey_patch.md for advanced usage and examples.