# OProxy - Dynamic Metaprogrammatic Proxy System for TouchDesigner

OProxy is a powerful extension system for TouchDesigner that enables dynamic, hierarchical management of operators through a hybrid Proxy-Container pattern. It allows you to create intelligent wrappers that can simultaneously function as proxies for individual operators and containers for managing multiple operators.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Extension System](#extension-system)
6. [Error Handling](#error-handling)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)

## Quick Start

OProxy is designed to be used alongside [TouchDesigner Extensions](https://docs.derivative.ca/Extensions). This allows you to create reusable components that can manage operators dynamically.

### 1. Create a TouchDesigner Extension

1. **Create a Container Operator** in your TouchDesigner project
2. **Set the Container as Parent Shortcut** - Click container -> *Common* Tab -> Parent Shortcut
3. **Create Extension** and Edit its respective textDAT
4. **Import OProxy** and add it to container scope.

```python
# myExtension.dat
from TDStoreTools import StorageManager 
import TDFunctions as TDF
import oproxy		# Import oproxy

class myExtension:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.OProxy = oproxy.opr(ownerComp) # Add to container scope and pass ownerComp
		'''  ^
		The 'O' here needs to be capitalized to be enabled as a 'Promoted' attribute
		(see TouchDesigner extension documentation for more info)
		'''
```

### 2. Access OProxy from Any Text DAT

Once your extension is set up, you can access OProxy from any Text DAT within the container:

```python
# In any Text DAT within the container
opr = parent.shortcut.Oproxy # note capitalized 'O'
```

### 3. Create Your First Proxy

```python
# Create a container for video processing operators
opr._add('video', ['moviefilein1', 'moviefilein2'])

# Access individual operators as proxies
opr.video('moviefilein1').par.file = '/path/to/video.mov'
opr.video('moviefilein2').par.file = '/path/to/another.mov'

# Access all operators in the container
for op in opr.video:
    print(f"Video OP: {op.path}")
```

### 4. Add Extensions

```python
# Create a DAT with extension functions
# In a Text DAT named 'VideoExtensions':
def resize_video(self, width, height):
    self.par.width = width
    self.par.height = height

def set_playback_speed(self, speed):
    self.par.playrate = speed

# Apply extensions to video container (dat parameter required for persistence)
opr.video._extend('resize', func='resize_video', dat=op('VideoExtensions'))
opr.video._extend('speed', func='set_playback_speed', dat=op('VideoExtensions'))

# Use extensions
for op in opr.video:
    op.resize(1920, 1080)
    op.speed(1.5)
```

### 5. Refresh After Changes

**Important:** If operator names change or extensions are modified, you must refresh:

```python
# Refresh entire tree
opr._refresh()

# Refresh specific branch only
opr.video._refresh()  # Only refreshes the 'video' branch
```

**Note:** `_refresh()` works recursively - calling `opr.Media._refresh()` will only refresh the 'Media' branch of the object hierarchy.

## Core Concepts

### Hybrid Proxy-Container Pattern

OProxy uses a hybrid design where containers automatically switch behavior based on their contents:

- **Single Operator**: Acts as a proxy, delegating all operations to the wrapped operator
- **Multiple Operators**: Acts as a container, managing collections of operators
- **Empty Container**: Acts as a container, ready to receive operators

### Key Benefits

1. **Dynamic Behavior**: Same object can be both proxy and container
2. **Persistent Extensions**: Extensions survive project reloads
3. **Hierarchical Organization**: Create nested structures of operators
4. **Metaprogrammatic**: Extend functionality at runtime
5. **TouchDesigner Native**: (Attempts to) Seamlessly integrate with TouchDesigner's operator system. # Please note may be buggy since I context/vibe coded this

## Basic Usage

### Creating Containers

```python
# Single operator container (acts as proxy)
opr._add('camera', 'moviefilein1')

# Multiple operator container (acts as container)
opr._add('effects', ['blur1', 'level1', 'edge1'])

# Nested containers
opr.effects._add('advanced', ['glow1', 'sharpen1'])
```

### Accessing Operators

```python
# Access as proxy (single operator)
opr.camera.par.file = '/path/to/camera.mov'
opr.camera.play()

# Access as container (multiple operators)
for effect in opr.effects:
    effect.par.active = True

# Access nested containers
for advanced_effect in opr.effects.advanced:
    advanced_effect.par.amount = 0.5
```

### Managing Operators

```python
# Add operators to existing containers
opr.effects._add('more', ['noise1', 'distort1'])

# Remove operators
opr.effects._remove(['blur1', 'level1'])

```

## Advanced Features

### Hierarchical Organization

```python
# Create a complex video processing pipeline
opr._add('pipeline', ['moviefilein1'])

# Add input processing
opr.pipeline._add('input', ['moviefilein1', 'moviefilein2'])

# Add effects processing
opr.pipeline._add('effects', ['blur1', 'level1'])

# Add output processing
opr.pipeline._add('output', ['moviefileout1'])

# Access nested structure
opr.pipeline.input('moviefilein1').par.file = '/input1.mov'
opr.pipeline.effects('blur1').par.amount = 0.3
```

### Dynamic Operator Management

```python
# Create empty container
opr._add('dynamic', [])

# Add operators dynamically
opr.dynamic._add('chops', ['chop1', 'chop2'])
opr.dynamic._add('dats', ['table1', 'table2'])

# Access by type
for chop in opr.dynamic.chops:
    chop.par.active = True

for dat in opr.dynamic.dats:
    dat.par.active = True
```

### Mixed Operator Types

```python
# Create container with different operator types
opr._add('mixed', ['moviefilein1', 'chop1', 'table1'])

# Access by type (all operators respond to common attributes)
for op in opr.mixed:
    print(f"Operator: {op.name}, Type: {op.type}")

# Type-specific operations
opr.mixed('moviefilein1').par.file = '/video.mov'
opr.mixed('chop1').par.active = True
opr.mixed('table1').par.active = True
```

## Extension System

### Creating Extensions

Extensions allow you to add custom functionality to operators. Create a Text DAT with your extension functions:

**Important:** The `dat` parameter must be set for extensions to persist across project reloads. If you modify an extension DAT, you must call `opr._refresh()` to reload the changes.

```python
# In Text DAT named 'OperatorExtensions':
def auto_play(self):
    """Automatically start playback"""
    self.play()

def set_dimensions(self, width, height):
    """Set operator dimensions"""
    if hasattr(self, 'par'):
        if hasattr(self.par, 'width'):
            self.par.width = width
        if hasattr(self.par, 'height'):
            self.par.height = height

def log_info(self):
    """Log operator information"""
    print(f"Operator: {self.name}, Type: {self.type}, Path: {self.path}")
```

### Applying Extensions

```python
# Apply to single operator
opr.camera._extend('auto_play', func='auto_play', dat=op('OperatorExtensions'))

# Apply to container (all operators)
opr.effects._extend('dimensions', func='set_dimensions', dat=op('OperatorExtensions'))

# Apply with parameters
opr.video._extend('resize', func='set_dimensions', dat=op('OperatorExtensions'), 
                       args=(1920, 1080), call=True) # call=True will execute the function at the time this line is run. Set call=False (default) if you just want to extend.

# Use extensions
opr.camera.auto_play()
opr.effects.dimensions(1280, 720)
```

### Extension Classes

```python
# In Text DAT named 'VideoProcessor':
class VideoProcessor:
    def __init__(self):
        self.processed_frames = 0
    
    def process_frame(self, op):
        """Process a single frame"""
        self.processed_frames += 1
        print(f"Processed frame {self.processed_frames} from {op.name}")
    
    def get_stats(self):
        """Get processing statistics"""
        return f"Processed {self.processed_frames} frames"

# Apply class extension
opr.video._extend('processor', cls='VideoProcessor', dat=op('VideoProcessor'), 
                       call=True)

# Use class extension
for op in opr.video:
    op.processor.process_frame(op)
    
print(opr.video.processor.get_stats())
```

## Error Handling

### Common TouchDesigner Errors

```python
# Invalid OP path
try:
    opr._add('invalid', 'nonexistent_op')
except ValueError as e:
    print(f"OP not found: {e}")

# Missing DAT for extensions
try:
    opr.video._extend('missing', func='nonexistent', dat=op('MissingDAT'))
except ValueError as e:
    print(f"DAT not found: {e}")

# Invalid operator type
try:
    opr._add('invalid', 123)  # Not a string or OP
except TypeError as e:
    print(f"Invalid operator type: {e}")
```

### Extension Errors

```python
# Extension function not found in DAT
try:
    opr.video._extend('missing', func='nonexistent_func', dat=op('Extensions'))
except ValueError as e:
    print(f"Extension function not found: {e}")

# Extension execution error
try:
    opr.video.broken_extension()
except Exception as e:
    print(f"Extension error: {e}")
```

### Storage Errors

```python
# Check if extension will persist
if hasattr(opr.video, '_dictPath'):
    print("Extensions will persist")
else:
    print("Extensions will not persist - use _add() to create containers")
```

## API Reference

### Core Methods

#### `opr._add(name, op)`
Creates or updates a container with operators.

**Parameters:**
- `name` (str): Container name
- `op` (str|OP|list): Operator(s) to add

**Returns:** OPContainer instance

**Example:**
```python
# Single operator
container = opr._add('video', 'moviefilein1')

# Multiple operators
container = opr._add('effects', ['blur1', 'level1'])

# Nested container
child = container._add('advanced', ['glow1'])
```

#### `opr._remove(path, to_remove=None)`
Removes operators or containers.

**Parameters:**
- `path` (str): Path to container
- `to_remove` (str|OP|list): Specific operators to remove (optional)

**Example:**
```python
# Remove specific operators
opr.effects._remove(['blur1', 'level1'])

# Remove entire container
opr._remove('effects')
```

#### `opr._refresh()`
Refreshes the proxy tree and re-applies extensions.

**Example:**
```python
# After moving/renaming operators
opr._refresh()
```

#### `opr._tree(child=None, detail='full', asDict=False)`
Displays the proxy tree structure.

**Parameters:**
- `child` (str): Specific child to display (optional)
- `detail` (str): 'full' or 'minimal'
- `asDict` (bool): Return as dictionary instead of printing

**Example:**
```python
# Display full tree
opr._tree()

# Display minimal tree
opr._tree(detail='minimal')

# Display specific child
opr._tree(child='effects')
```

### Extension Methods

#### `container._extend(attr_name, cls=None, func=None, dat=None, args=None, call=False)`
Adds extensions to containers.

**Parameters:**
- `attr_name` (str): Extension name
- `cls` (str): Class name to extract (optional)
- `func` (str): Function name to extract (optional)
- `dat` (DAT): Text DAT containing extension (optional)
- `args` (tuple|list): Arguments for instantiation/calling (optional)
- `call` (bool): Whether to instantiate/call immediately

**Example:**
```python
# Function extension
container._extend('resize', func='resize_video', dat=op('Extensions'))

# Class extension
container._extend('processor', cls='VideoProcessor', dat=op('Extensions'), call=True)

# Extension with arguments
container._extend('resize', func='resize_video', dat=op('Extensions'), 
                  args=(1920, 1080), call=True)
```

