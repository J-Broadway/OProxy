
# _extend() Monkey-Patch Enhancement - Construction Document

## Overview
Add monkey_patch support to _extend() for overwriting existing containers with custom subclasses, enabling custom behaviors like in the example.

## Current Behavior
- _extend() raises error if attr_name exists unless monkey_patch=True (for extensions).
- No support for subclassing/replacing existing OProxyContainer instances.

## Proposed Behavior
opr._add('items', mvs)  # Creates OProxyContainer 'items'
opr._extend('items', cls='OverwriteItems', dat='extensions_for_tests', monkey_patch=True)  # Replaces with OverwriteItems subclass, preserving state.

### Monkey-Patching Other Types
- **OProxyLeaf**: Supported—replaces with custom OProxyLeaf subclass, migrating _op and extensions. Useful for per-OP customizations.

**Leaf Example:**

**End Goal:** Add custom_info() to a specific leaf returning OP details, without affecting others.

**Usage:**
```python
opr._add('items', ['op1', 'op2'])  # Create container with leaves
opr.items._extend('op1', monkey_patch=True, cls='CustomLeaf', dat='monkeyPatches')  # Target specific leaf to patch

info = opr.items('op1').custom_info()  # Works on patched leaf: Returns {'name': 'op1', 'type': ..., 'path': ...}
opr.items('op2').custom_info()  # Error: Not patched, no such method
```

**monkeyPatches.DAT:**
```python
mp = op('OProxy').MonkeyPatch
log = op('OProxy').Log  # optional

class CustomLeaf(mp.OProxyLeaf):
    """Custom leaf with added method."""

    def __getattr__(self, name):
        return super().__getattr__(name)  # Delegate to parent

    def custom_info(self):
        # Return dict of OP info
        return {
            'name': self._op.name,
            'type': self._op.type,
            'path': self._op.path
        }
```

- **OProxyExtension**: Not supported—raises NotImplementedError: "Monkey-patching extensions not supported; remove and re-extend instead." Extensions are dynamic wrappers; patching risks breaking delegation.

## Usage Examples

### Resolution Method Addition

**End Goal:**  
Add a `resolution()` function that returns a TOP's resolution for every OProxyLeaf in an OProxyContainer, accessible directly on leaves.

**Usage Example of End Goal:**  
```python
res = opr.media('op1').resolution()  # Can call on individual OProxyLeaf
print(res)  # Returns (width, height)

for leaf in opr.media:
    res = leaf.resolution()  # One monkey patch extends all OProxyLeafs
    print(res)
```

**How To Do It:**  
```python
mvs = ['op1','op2','op3']  # Define list of OPs to be added to OProxyContainer
opr._add('media', mvs)  # Create OProxyContainer for OPs
opr._extend('media', monkey_patch=True, cls='ResolutionMP', dat='monkeyPatches')  # Target item to monkey patch with the class from monkeyPatches DAT
```

**monkeyPatches.DAT**
```python
mp = op('OProxy').MonkeyPatch  # Import helpers
log = op('OProxy').Log  # (optional) Import OPLogger for logging

class ResolutionMP(mp.OProxyContainer):
    """Monkey-patched container that adds resolution() to leaves."""

    def __call__(self, identifier, **kwargs):
        # Call parent's __call__ to get the original OProxyLeaf
        leaf = super().__call__(identifier, **kwargs)

        # Create a proxy wrapper to add custom methods to the leaf
        class ResolutionProxy:
            def __init__(self, inner_leaf):
                self._inner = inner_leaf  # Store the original leaf

            def __getattr__(self, name):
                # Delegate all other attribute access to the original leaf
                return getattr(self._inner, name)

            def resolution(self):
                # Custom method: Check if the OP is a TOP, then return resolution
                if not self._inner.op.isTOP:
                    log("Not a TOP operator", status='error')
                    raise ValueError("resolution() only for TOPs")
                return (self._inner.op.width, self._inner.op.height)

        # Return the proxy instead of the raw leaf
        return ResolutionProxy(leaf)
```

### Intercepting Attribute Access on Leaves

**End Goal:**  
Intercept access to 'par' on any leaf in the container, perform actions before/after (e.g., log), and return the original attribute.

**Usage Example of End Goal:**  
```python
# Access triggers before/after actions but returns original
print(opr.items('op1').par.name)  # Logs: "Before accessing par on op1" ... returns 'op1' ... "After accessing par on op1"
```

**How To Do It:**  
```python
mvs = ['op1','op2']  # OPs to add
opr._add('items', mvs)  # Create container
opr._extend('items', monkey_patch=True, cls='InterceptParContainer', dat='monkeyPatches')  # Patch container
```

**monkeyPatches.DAT**  
```python
mp = op('OProxy').MonkeyPatch
log = op('OProxy').Log  # optional for logging

class InterceptParContainer(mp.OProxyContainer):
    """Container that intercepts 'par' access on leaves."""

    def __call__(self, identifier, **kwargs):
        leaf = super().__call__(identifier, **kwargs)
        
        class InterceptProxy:
            def __init__(self, inner_leaf):
                self._inner = inner_leaf

            def __getattr__(self, name):
                if name == 'par':
                    log(f"Before accessing {name} on {self._inner._op.name}", status='debug')
                    attr = getattr(self._inner, name)
                    log(f"After accessing {name} on {self._inner._op.name}", status='debug')
                    return attr
                return getattr(self._inner, name)

        return InterceptProxy(leaf)
```

## Implementation Strategy
### Core Logic
In OProxyContainer._extend():
- If monkey_patch and existing is OProxyContainer:
  - Validate cls subclasses OProxyContainer.
  - Instantiate new with old state (_children, _path, _parent, etc.).
  - Copy children, re-parent.
  - Migrate extensions.
  - Replace in parent's _children.

### Validation
- Ensure cls is OProxyContainer subclass.
- Handle state migration carefully.

### Testing
Add to extend_tests.py: Create container, monkey-patch, verify custom behavior and state preservation.

### Parameter Handling with monkey_patch=True
When monkey_patch=True, only the following parameters are supported:
- attr_name: Name of the existing container to patch
- cls: Class name to extract from DAT (must subclass OProxyContainer)
- dat: Text DAT containing the subclass code

Unsupported parameters (e.g., func, args, call, returnObj) will raise NotImplementedError with message: "'parameter_name' not supported when monkey_patch=True". Note: func is unsupported as only class-based subclassing (via cls) is allowed for container monkey-patching.

All other parameters (e.g., args, call, returnObj) will raise NotImplementedError with message: "'parameter_name' not supported when monkey_patch=True"

This keeps the API focused on container subclass replacement without callable/instantiation options, which don't apply here.

## Potential Concerns
- Deep state copying.
- Extension migration.
- Infinite recursion if not careful.

### Re-attachment Behavior
Re-applying _extend with monkey_patch=True to the same container (e.g., after subclass changes) automatically re-migrates current state to a new instance of the subclass—no special process needed.

Note that when monkey patch code changes _refresh() is required for changes to take effect.

However, risks include:
- Extension conflicts if subclass changes affect migrated extensions
- Potential side effects from re-initialization
- Incompatibility if new subclass lacks attributes expected by migrated state

Test thoroughly for side effects; re-apply only with compatible subclasses.

## Needed Documentation

### Key Internal Functions for Advanced Users
Based on OProxy codebase (primarily OProxyContainer/OProxyBaseWrapper), these are most valuable for monkey-patching. Use with caution—direct calls can break state if mishandled. Access via self (e.g., self._refresh()).

- **_add(name, op=None, returnObj=False)**: Adds OPs/sub-containers to hierarchy. Crucial for dynamic structure building.
- **_remove(name=None)**: Removes self/child/extension. Essential for cleanup/unloading.
- **_refresh(target=None)**: Refreshes container state (e.g., re-validates OPs, extensions). Key for syncing after changes.
- **_extend(attr_name=None, cls=None, func=None, dat=None, args=None, call=False, monkey_patch=False, returnObj=False)**: Adds extensions from DATs. Vital for injecting custom behaviors.
- **_tree()**: Returns hierarchy string. Useful for debugging/logging custom states.
- **_clear(flush_logger=True)**: Clears all data (root only). Handy for reset in custom workflows.
- **_find_root()**: Traverses to root container. Important for global ops (e.g., storage access).