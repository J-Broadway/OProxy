# _extend() Feature Construction Design

## Overview

The `_extend()` method enables dynamic extension of OProxy containers and leafs with custom methods and classes extracted from TouchDesigner Text DATs. This provides a powerful way to add reusable functionality to proxy objects while maintaining persistence across project sessions.

## Goals

- **Dynamic Extension**: Allow containers and leafs to be extended with functions/classes from DATs
- **Persistence**: Extensions survive project reloads through TouchDesigner storage
- **Type Safety**: Proper validation of DATs, extraction, and binding
- **Developer Control**: Explicit behavior control, no automatic magic
- **Clean Architecture**: Keep core simple, enable advanced patterns through documentation

## Architecture Decisions

### 1. **No Automatic Inheritance**
- **Decision**: Framework does NOT automatically walk parent chains for extensions
- **Rationale**: Keeps core architecture predictable and simple
- **Implementation**: Manual inheritance patterns documented for advanced users

### 2. **Binding Model**
- **Container Extensions**: `self` refers to the OPContainer instance
- **Leaf Extensions**: `self` refers to the OPLeaf instance
- **Consistency**: Same extraction/binding logic for both, different `self` context

### 3. **Storage Structure**
```python
# Root level storage structure
{
    'children': {
        'container_name': {
            'children': {...},  # Nested containers
            'ops': {...},       # OP paths
            'extensions': {     # NEW: Extension storage
                'extension_name': {
                    'cls': 'ClassName' | None,
                    'func': 'funcName' | None,
                    'dat_path': '/path/to/dat',
                    'call': False,
                    'args': None,
                    'monkey_patch': False
                }
            }
        }
    },
    'extensions': {}  # Root-level extensions
}
```

### 4. **Loading Order**
Extensions load AFTER complete container/OP structure:
1. Create containers
2. Load OPs into containers
3. Load nested containers
4. **Load extensions** (new step)

## API Specification

### Method Signature
```python
def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
    """
    Extend the proxy object with an attribute or method from a Text DAT.

    Parameters:
    - attr_name (str): Name for the extension
    - cls (str): Class name to extract from DAT
    - func (str): Function name to extract from DAT
    - dat (DAT): Text DAT containing the extension (required)
    - args (tuple|list): Arguments for instantiation/calling when call=True
    - call (bool): Whether to instantiate/call immediately
    - monkey_patch (bool): Allow overwriting existing attributes

    Returns:
    - self: For method chaining

    Raises:
    - ValueError: Invalid parameters, naming conflicts, extraction failures
    """
```

### Parameter Validation
- **Mutually Exclusive**: `cls` and `func` cannot both be specified
- **Required**: Either `cls` or `func` must be specified when `dat` is provided
- **DAT Validation**: Uses `utils.td_isinstance()` for type checking
- **Call Args**: `args` must be tuple/list when `call=True`

## Implementation Plan

### Phase 1: Core Implementation
1. **Add `_extend()` method to `OPBaseWrapper`** (abstract)
2. **Implement in `OPContainer`** with container binding
3. **Implement in `OPLeaf`** with leaf binding
4. **Add extension storage logic** to `__build_storage_structure()`
5. **Add extension loading logic** to `_refresh()`

### Phase 2: Error Handling & Validation
1. **Naming conflict detection** with `monkey_patch` handling
2. **DAT accessibility validation**
3. **Extraction success validation**
4. **Descriptive error messages**

### Phase 3: Documentation & Testing
1. **Update storage structure** in `utils.py` storage functions
2. **Add comprehensive examples** to documentation
3. **Create test cases** for all scenarios

## Usage Examples

### Function Extensions

#### Container Function Extension
```python
# In extensions DAT
def resize_videos(self, width, height):
    """Resize all videos in container"""
    for op in self:  # self is OPContainer
        op.par.outputresolution = 'custom'
        op.par.resolutionw = width
        op.par.resolutionh = height

# Usage
opr.videos._extend('resize', func='resize_videos', dat=me)
opr.videos.resize(1920, 1080)  # Applies to all videos
```

#### Leaf Function Extension
```python
# In extensions DAT
def custom_pulse(self, duration=1):
    """Create custom pulse on this CHOP"""
    self.par.pulse = True  # self is OPLeaf
    self.par.pulseframes = duration * 60

# Usage
opr.chops('constant1')._extend('pulse', func='custom_pulse', dat=me)
opr.chops('constant1').pulse(2.5)  # Pulse for 2.5 seconds
```

### Class Extensions

#### Container Class Extension
```python
# In extensions DAT
class VideoProcessor:
    def __init__(self, container):
        self.container = container
        self.effects = []

    def add_effect(self, effect_type):
        for video in self.container:
            # Create effect connected to video
            pass

# Usage
opr.videos._extend('processor', cls='VideoProcessor', dat=me)
opr.videos.processor.add_effect('blur')
```

#### Leaf Class Extension
```python
# In extensions DAT
class AudioAnalyzer:
    def __init__(self, leaf):
        self.leaf = leaf

    def get_fft(self):
        # FFT analysis for this audio input
        pass

# Usage
opr.audio('mic_input')._extend('analyzer', cls='AudioAnalyzer', dat=me)
data = opr.audio('mic_input').analyzer.get_fft()
```

### Call Parameter Behavior

#### call=False (Default)
```python
# Function stored but not called
opr.chops._extend('setup', func='setup_chops', dat=me)  # Not called
opr.chops.setup()  # User calls explicitly
```

#### call=True with Function
```python
# Function called immediately during extension
opr.chops._extend('init', func='initialize_chops', dat=me, call=True)  # Called now
# Extension also stored for future reloads
```

#### call=True with Class
```python
# Class instantiated immediately
opr.chops._extend('manager', cls='ChopManager', dat=me, args=['param'], call=True)
# manager is now instantiated and ready to use
result = opr.chops.manager.some_method()
```

### Error Handling Examples

#### Naming Conflicts
```python
# Conflict detected
try:
    opr.chops._extend('name', func='some_func', dat=me)  # 'name' exists
except ValueError as e:
    print(e)  # "Name 'name' conflicts with existing method. To overwrite, use monkey_patch=True. See documentation for proper usage and potential side effects."

# Force overwrite
opr.chops._extend('name', func='some_func', dat=me, monkey_patch=True)
```

#### Invalid Parameters
```python
# Both cls and func specified
opr.chops._extend('bad', cls='MyClass', func='myFunc', dat=me)  # ValueError

# Neither cls nor func specified
opr.chops._extend('bad', dat=me)  # ValueError

# Invalid DAT
opr.chops._extend('bad', func='func', dat='invalid_path')  # ValueError
```

## Advanced Patterns (Documented, Not Built-in)

### Manual Inheritance
```python
def inherited_resize(self, width, height):
    """Manual inheritance pattern"""
    # Check self first
    if hasattr(self, 'my_resize'):
        return self.my_resize(width, height)

    # Check parent
    if self._parent and hasattr(self._parent, 'resize'):
        return self._parent.resize(width, height)

    # Default behavior
    for op in self:
        op.par.resolutionw = width
```

### Extension Dependencies
```python
def advanced_effect(self):
    """Depends on other extensions"""
    if not hasattr(self, 'basic_setup'):
        self._extend('basic_setup', func='setup_func', dat=me)
        self.basic_setup()  # Initialize dependency

    # Now use the dependency
    # ...
```

## Storage & Persistence

### Extension Storage Logic
- Extensions stored alongside containers in TouchDesigner storage
- Storage happens automatically after successful extension
- Extensions reload during `_refresh()` after structure is built

### Storage Update Flow
```python
def _extend(self, ...):
    # Extract and validate
    # Bind to object
    # Store in self.__dict__ with special prefix
    # Update TouchDesigner storage
    # Return self
```

### Reload Flow
```python
def _refresh(self):
    # Build container structure
    # Build OP structure
    # Load extensions from storage
    # Re-apply extensions to objects
```

## Error Handling & Validation

### Comprehensive Validation
1. **Parameter Validation**: Mutual exclusivity, required fields
2. **DAT Validation**: Path resolution, type checking
3. **Extraction Validation**: AST parsing success, object existence
4. **Binding Validation**: Object is callable/instantiable
5. **Naming Validation**: Conflicts with existing attributes

### Error Message Standards
- **Clear**: Explain what went wrong
- **Actionable**: Suggest how to fix
- **Contextual**: Include relevant object names/paths

## Future Considerations

### Phase 2 Features (Post-V1)
- `_remove_extension()` method
- Extension metadata (description, version, author)
- Extension marketplace/sharing
- Extension dependency declarations
- Extension performance profiling

### Architecture Extensions
- Extension caching for performance
- Extension validation at load time
- Extension migration/update system

## Implementation Checklist

### Core Implementation
- [ ] Add `_extend()` to `OPBaseWrapper` (abstract)
- [ ] Implement `_extend()` in `OPContainer`
- [ ] Implement `_extend()` in `OPLeaf`
- [ ] Update `__build_storage_structure()` for extensions
- [ ] Update `_refresh()` for extension loading
- [ ] Update `utils.py` storage functions

### Validation & Error Handling
- [ ] Parameter validation logic
- [ ] DAT validation with `td_isinstance()`
- [ ] Naming conflict detection
- [ ] Descriptive error messages
- [ ] Extraction error handling

### Testing & Documentation
- [ ] Unit tests for all scenarios
- [ ] Integration tests with storage
- [ ] Usage examples in documentation
- [ ] Advanced patterns documentation
- [ ] Error handling examples

## Conclusion

The `_extend()` feature provides a powerful yet clean way to extend OProxy objects with reusable functionality. By keeping automatic inheritance out of the core and providing comprehensive validation, the feature maintains architectural simplicity while enabling advanced usage patterns through documentation and examples.

The design balances flexibility, safety, and maintainability, making it suitable for both simple extensions and complex, reusable component systems.
