# _extend() Feature Construction Design

## Overview

The `_extend()` method enables dynamic extension of OProxy containers and leafs with custom methods and classes extracted from TouchDesigner Text DATs. This provides a powerful way to add reusable functionality to proxy objects while maintaining persistence across project sessions.

**Current Status**: Partially implemented. Storage architecture, refresh system, and extension placeholders are complete. Core `_extend()` method implementation pending.

## Goals

- **Dynamic Extension**: Allow containers and leafs to be extended with functions/classes from DATs
- **Persistence**: Extensions survive project reloads through TouchDesigner storage
- **Type Safety**: Proper validation of DATs, extraction, and binding
- **Developer Control**: Explicit behavior control, no automatic magic
- **Clean Architecture**: Keep core simple, enable advanced patterns through documentation

## Recent Changes (Post-Plan Implementation)

### Storage Architecture Refactor ✅ COMPLETED
- **Updated storage structure** from flat OP paths to nested OP objects
- **Added extension storage** at both container and leaf levels
- **Implemented OP name change detection** using stored OP objects
- **Enhanced `utils.store()` and `utils.remove()`** for new structure

### Refresh System Refactor ✅ COMPLETED
- **Polymorphic `_refresh()`** implementation across all wrapper types
- **Branch-specific refresh** capability (not just root-only)
- **Automatic OP name change detection** during refresh
- **Extension placeholder infrastructure** ready for `_extend()` integration

### _add() Method Enhancement ✅ COMPLETED
- **Incremental container building** - add OPs to existing containers
- **Enhanced validation** with reserved name protection
- **Better error handling** and logging

### Current Architecture Foundation ✅ COMPLETED
- **`OProxyExtension` placeholder class** in `OPBaseWrapper.py`
- **`_extensions` attributes** added to `OPContainer` and `OPLeaf`
- **Storage structure ready** for extension metadata
- **Refresh hooks ready** for extension re-application

## Architecture Decisions

### 1. **Factory Template Pattern**
- **Decision**: All extensions inherit from `OProxyExtension` factory template
- **Rationale**: Solves serialization issues, provides consistent interface, enables type checking
- **Benefits**: No need to serialize complex Python objects, automatic metadata tracking, consistent API

### 2. **No Automatic Inheritance**
- **Decision**: Framework does NOT automatically walk parent chains for extensions
- **Rationale**: Keeps core architecture predictable and simple
- **Implementation**: Manual inheritance patterns documented for advanced users

### 3. **Binding Model**
- **Container Extensions**: `self` refers to the OPContainer instance
- **Leaf Extensions**: `self` refers to the OPLeaf instance
- **Consistency**: Same extraction/binding logic for both, different `self` context

### 4. **OProxyExtension Factory Template**

**Current Implementation**: Placeholder class exists in `OPBaseWrapper.py`. Full factory template implementation pending.

```python
class OProxyExtension(OPBaseWrapper):
    """
    Factory template for all OProxy extensions. Provides consistent interface,
    delegation to extracted objects, and metadata tracking.

    Extensions will be able to be removed independently of their parent containers/leafs.
    """

    def __init__(self, actual_obj, parent, source_dat=None, metadata=None):
        """
        Initialize extension with extracted object and metadata.

        Args:
            actual_obj: The extracted class/function from AST module
            parent: Parent container or leaf this extension belongs to
            source_dat: Original DAT object where extension was defined
            metadata: Extension metadata (cls, func, dat_path, etc.)
        """
        super().__init__(path="", parent=parent)
        self._actual = actual_obj  # The extracted class/function
        self._source_dat = source_dat
        self._metadata = metadata or {}

        # Dynamically copy attributes from actual object for delegation
        self._copy_attributes_from_actual()

    def _copy_attributes_from_actual(self):
        """Copy non-private attributes from the actual object to enable delegation."""
        for attr_name in dir(self._actual):
            if not attr_name.startswith('_') and not hasattr(self, attr_name):
                try:
                    attr = getattr(self._actual, attr_name)
                    setattr(self, attr_name, attr)
                except (AttributeError, TypeError):
                    # Skip attributes that can't be copied
                    pass

    def __getattr__(self, name):
        """Delegate attribute access to the actual object."""
        if name.startswith('_'):
            # Don't delegate private attributes
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        try:
            return getattr(self._actual, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __call__(self, *args, **kwargs):
        """Allow calling if the actual object is callable."""
        if callable(self._actual):
            return self._actual(*args, **kwargs)
        else:
            raise TypeError(f"'{self.__class__.__name__}' object is not callable")

    @property
    def extension_info(self):
        """Access metadata about this extension."""
        return {
            'source_dat': self._source_dat,
            'parent': self._parent,
            'metadata': self._metadata,
            'actual_type': type(self._actual).__name__,
            'is_callable': callable(self._actual)
        }

    def _remove(self):
        """
        Remove this extension from its parent and clean up storage.

        Implementation will:
        - Remove extension from parent's _extensions registry
        - Remove extension attribute from parent object
        - Clean up extension data from storage
        - Update storage persistence
        """
        if self._parent:
            # Remove from parent's extension registry
            if hasattr(self._parent, '_extensions') and hasattr(self, '_extension_name'):
                if self._extension_name in self._parent._extensions:
                    del self._parent._extensions[self._extension_name]

            # Remove extension attribute from parent
            if hasattr(self._parent, self._extension_name):
                delattr(self._parent, self._extension_name)

            # Clean up storage (will call parent's storage update)
            if hasattr(self._parent, '_update_storage'):
                self._parent._update_storage()

        Log(f"Extension '{getattr(self, '_extension_name', 'unknown')}' removed successfully", status='info', process='_remove')
        return self
```

### 5. **Module Integration**

**AST Extraction Module**: Uses `mod_AST.py` with the `Main()` function for extracting classes and functions from Text DATs.

```python
# In OPBaseWrapper.py context:
mod_ast = mod('mod_AST')  # Import the AST extraction module
actual_obj = mod_ast.Main(cls=cls, func=func, op=dat, log=self.Log)
```

### 6. **Extension Attachment Logic**

**How Extensions Get Applied to Parent Objects:**

```python
def _extend(self, attr_name, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False):
    # ... validation and extraction ...

    # Create extension wrapper
    extension = OProxyExtension(actual_obj, self, dat, metadata)

    # Store extension name for removal purposes
    extension._extension_name = attr_name

    # Apply extension to parent object (make it accessible)
    setattr(self, attr_name, extension)

    # Store in internal registry for management
    self._extensions[attr_name] = extension

    # Update storage with extension metadata
    self._update_storage()

    return self
```

**Accessibility**: Extensions become accessible as attributes on their parent:
```python
opr.container._extend('my_func', func='my_function', dat=me)
opr.container.my_func()  # Accessible as attribute
```

### 7. **Storage Structure**

**Current Implementation**: Storage structure updated and implemented in `utils.py` and `OPBaseWrapper.py`.

```python
# Current storage structure with nested OP objects and extension support
{
    'OProxies': {
        'children': {
            'container_name': {
                'children': {...},  # Nested containers
                'ops': {             # ✅ IMPLEMENTED: Nested OP objects
                    'op_name': {
                        'path': '/project/path/to/op',
                        'op': <OP object>,    # Raw OP for name change detection
                        'extensions': {       # Extension metadata storage ready
                            'extension_name': {
                                'cls': 'ClassName' | None,
                                'func': 'funcName' | None,
                                'dat_path': '/path/to/dat',
                                'call': False,
                                'args': None,
                                'monkey_patch': False,
                                'created_at': 1640995200.0
                            }
                        }
                    }
                },
                'extensions': {}     # Container-level extensions
            }
        },
        'extensions': {}  # Root-level extension metadata
    }
}
```

### 8. **Storage Update Strategy**

**Recommendation**: Use existing `_update_storage()` method for extension updates.

The current `_update_storage()` method works well for extensions because:
- It rebuilds the complete storage structure including extension metadata
- Extensions are stored in the `_extensions` attribute which gets included in storage
- No need for a separate `_update_storage_extension()` method - the existing method handles it

**Extension Storage Flow**:
1. Extension is added to `self._extensions[attr_name]`
2. `self._update_storage()` is called
3. Storage rebuild includes all extensions in the `_extensions` dict
4. Extensions persist across project reloads

### 9. **Loading Order**
Extensions load AFTER complete container/OP structure:
1. Create containers
2. Load OPs into containers
3. Load nested containers
4. **Load extensions**: Re-extract objects from DATs and wrap in `OProxyExtension` factory template

### 10. **Type Checking & Introspection**
All extensions inherit from `OProxyExtension`, enabling:
```python
opr.media._extend('myExtension', cls='MyClass', dat=me)
type(opr.media.myExtension)  # -> <class 'OProxyExtension'>
isinstance(opr.media.myExtension, OProxyExtension)  # -> True

# Check parent relationships
opr.media.myExtension._parent  # -> media container

# Access extension metadata
info = opr.media.myExtension.extension_info
print(f"From DAT: {info['source_dat'].path}")
print(f"Created at: {info['metadata']['created_at']}")
print(f"Callable: {info['is_callable']}")
```

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

### Extension Removal Strategy

**Individual Extension Removal**: Extensions can be removed independently using `extension._remove()`.

```python
# Add extension
opr.container._extend('my_func', func='my_function', dat=me)

# Remove extension individually
opr.container.my_func._remove()  # Removes just this extension

# Extension is no longer accessible
# opr.container.my_func  # -> AttributeError
```

**Type Checking in _remove()**: The `_remove()` method checks object type to handle different removal scenarios:

```python
def _remove(self, name=None):
    # Case 1: _remove() on extension - remove this extension
    if isinstance(self, OProxyExtension):
        return self._remove_extension()

    # Case 2: _remove() on container/leaf - remove self or named child
    # ... existing container/leaf removal logic ...
```

**Extension Cleanup During Parent Removal**: When containers or leaves are removed, their extensions are automatically cleaned up.

### Performance Considerations

**Simple Approach**: Keep refresh simple without lazy loading.

**Rationale**: 
- TouchDesigner projects typically don't have 50+ extensions per container
- Refresh performance is acceptable for typical use cases
- Complexity of lazy loading outweighs benefits for most projects
- Focus on correctness over micro-optimizations

**If Performance Issues Arise**: Can implement lazy loading or selective refresh later if needed.

### Circular Dependency Prevention

**Scenario**: Extensions that reference each other during refresh.

```python
# Mock example - NOT recommended, but shows the problem:
# Extension A in DAT1
def extension_a(self):
    if hasattr(self, 'extension_b'):  # References extension_b
        return self.extension_b()

# Extension B in DAT2
def extension_b(self):
    if hasattr(self, 'extension_a'):  # References extension_a
        return self.extension_a()

# During refresh:
# 1. Load extension_a -> sees extension_b doesn't exist yet -> OK
# 2. Load extension_b -> sees extension_a exists -> calls it
# 3. Result: Potential infinite recursion or inconsistent state
```

**Prevention**: Extensions should not reference other extensions during definition. Use explicit method calls instead:

```python
# Good: Check at runtime, not definition time
def extension_a(self):
    # Don't reference other extensions in the function body during refresh
    # Instead, call other methods explicitly when needed
    pass
```

**Implementation**: No special prevention logic needed - document this as a best practice.

## Implementation Plan

### Phase 1: Foundation (✅ COMPLETED)
1. ✅ **Storage architecture refactor** - Nested OP objects with extension support
2. ✅ **Refresh system refactor** - Polymorphic refresh with extension placeholders
3. ✅ **OProxyExtension placeholder class** - Base class structure ready
4. ✅ **Extension attributes** - `_extensions` added to `OPContainer` and `OPLeaf`
5. ✅ **Storage structure updates** - Extension metadata storage ready

### Phase 2: Core Implementation (🚧 PENDING)
1. **Create `OProxyExtension` factory template class** (replace placeholder)
2. **Add `_extend()` method to `OPBaseWrapper`** (abstract)
3. **Implement in `OPContainer`** with container binding and `OProxyExtension` wrapping
4. **Implement in `OPLeaf`** with leaf binding and `OProxyExtension` wrapping
5. **Add extension storage logic** to `__build_storage_structure()` (metadata only)
6. **Add extension loading logic** to `_refresh()` (re-extract and re-wrap)

### Phase 3: Error Handling & Validation (🚧 PENDING)
1. **Naming conflict detection** with `monkey_patch` handling
2. **DAT accessibility validation**
3. **Extraction success validation**
4. **Descriptive error messages**

### Phase 4: Documentation & Testing (🚧 PENDING)
1. **Add comprehensive examples** to documentation
2. **Create test cases** for all scenarios
3. **Integration testing** with TouchDesigner DAT extraction

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
- **Only metadata stored** in TouchDesigner storage (not actual objects)
- Extensions automatically inherit `OProxyExtension` factory template on reload
- Storage happens automatically after successful extension
- Extensions reload during `_refresh()` by re-extracting from DATs and re-wrapping

### Storage Update Flow
```python
def _extend(self, ...):
    # Extract actual object from DAT
    actual_obj = ast_mod.Main(cls=cls, func=func, op=dat)

    # Create metadata for serialization
    metadata = {
        'cls': cls, 'func': func, 'dat_path': dat.path,
        'args': args, 'call': call, 'created_at': time.time()
    }

    # Wrap in factory template
    extension = OProxyExtension(actual_obj, self, dat, metadata)

    # Store extension and update storage with metadata only
    self._extensions[attr_name] = extension
    self._update_storage()  # Use existing storage update method
    return self
```

### Reload Flow
```python
def _refresh(self):
    # Build container structure
    # Build OP structure

    # Load extensions from storage metadata
    for ext_name, metadata in stored_extensions.items():
        try:
            # Re-extract the actual object
            actual_obj = mod_ast.Main(
                cls=metadata['cls'],
                func=metadata['func'],
                op=metadata['dat_path'],
                log=self.Log
            )

            # Re-wrap in factory template (automatic inheritance!)
            extension = OProxyExtension(actual_obj, self,
                                      source_dat=metadata['dat_path'],
                                      metadata=metadata)

            # Store extension name for removal purposes
            extension._extension_name = ext_name

            # Apply to parent object
            setattr(self, ext_name, extension)

            # Store in registry
            self._extensions[ext_name] = extension

        except Exception as e:
            Log(f"Failed to reload extension '{ext_name}': {e}", status='warning', process='_refresh')
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

### Foundation Infrastructure (✅ COMPLETED)
- [x] Storage architecture refactor for extension support
- [x] Refresh system polymorphic implementation
- [x] OProxyExtension placeholder class structure
- [x] Extension attributes (_extensions) on containers and leaves
- [x] Storage structure updates for nested OP objects
- [x] Extension metadata storage preparation

### Core Implementation (🚧 PENDING)
- [ ] Create `OProxyExtension` factory template class (replace placeholder)
- [ ] Add `_extend()` to `OPBaseWrapper` (abstract)
- [ ] Implement `_extend()` in `OPContainer` with `OProxyExtension` wrapping
- [ ] Implement `_extend()` in `OPLeaf` with `OProxyExtension` wrapping
- [ ] Update `__build_storage_structure()` for extension metadata storage
- [ ] Update `_refresh()` for extension reloading (re-extract + re-wrap)

### Validation & Error Handling (🚧 PENDING)
- [ ] Parameter validation logic
- [ ] DAT validation with `td_isinstance()`
- [ ] Naming conflict detection
- [ ] Descriptive error messages
- [ ] Extraction error handling

### Testing & Documentation (🚧 PENDING)
- [ ] Unit tests for all scenarios
- [ ] Integration tests with storage
- [ ] Usage examples in documentation
- [ ] Advanced patterns documentation
- [ ] Error handling examples

## Deprecated Code Note

**OP_Proxy._extend()**: The old `_extend()` implementation in `OP_Proxy.py` is deprecated. It was designed for the original proxy system and is not compatible with the new `OPBaseWrapper` architecture. The new implementation will be in `OPBaseWrapper` with separate implementations in `OPContainer` and `OPLeaf`.

## Conclusion

The `_extend()` feature provides a powerful yet clean way to extend OProxy objects with reusable functionality. The `OProxyExtension` factory template pattern elegantly solves serialization issues by storing only metadata while ensuring all extensions automatically inherit consistent interfaces and type-checking capabilities.

By keeping automatic inheritance out of the core, providing comprehensive validation, and using the factory template approach, the feature maintains architectural simplicity while enabling advanced usage patterns through documentation and examples.

The design balances flexibility, safety, and maintainability, making it suitable for both simple extensions and complex, reusable component systems while providing robust type checking and introspection capabilities.
