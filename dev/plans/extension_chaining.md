# Extension Chaining Implementation Plan

## Overview

Enable extensions to be extended (extensions-on-extensions) to provide maximum flexibility for composable OProxy systems. This allows developers to build hierarchical extension structures where extensions can have their own extensions.

## Current State Analysis

### Storage Structure (Current)
```python
{
    'OProxies': {
        'children': {
            'container_name': {
                'children': {...},
                'ops': {
                    'op_name': {
                        'path': '/path/to/op',
                        'op': <OP_OBJECT>,
                        'extensions': {  # Flat extension metadata
                            'ext_name': {
                                'cls': 'ClassName',
                                'func': 'funcName',
                                'dat_path': '/path/to/dat',
                                'args': None,
                                'call': False
                            }
                        }
                    }
                },
                'extensions': {...}  # Container extensions (also flat)
            }
        },
        'extensions': {...}  # Root extensions (flat)
    }
}
```

### Method Return Values (Current)
- **OPContainer._extend()**: Returns `extension` object (inconsistent)
- **OPLeaf._extend()**: Returns `self` (consistent)
- **OProxyExtension._extend()**: Raises `NotImplementedError`

### Chaining Behavior (Current)
- `_extend()` chaining: Inconsistent (container returns extension, leaf returns self)
- `_add()` chaining: Not supported (returns `None`)

## Proposed Changes

### 1. Storage Structure (Proposed)
Extensions become hierarchical containers that can hold their own extensions:

```python
{
    'OProxies': {
        'children': {
            'container_name': {
                'children': {...},
                'ops': {
                    'op_name': {
                        'path': '/path/to/op',
                        'op': <OP_OBJECT>,
                        'extensions': {  # Now hierarchical
                            'ext_name': {
                                'metadata': {  # Extension's own metadata
                                    'cls': 'ClassName',
                                    'func': 'funcName',
                                    'dat_path': '/path/to/dat',
                                    'args': None,
                                    'call': False
                                },
                                'extensions': {  # Extensions can have extensions
                                    'sub_ext': {
                                        'metadata': {...},
                                        'extensions': {...}
                                    }
                                }
                            }
                        }
                    }
                },
                'extensions': {  # Container extensions also hierarchical
                    'container_ext': {
                        'metadata': {...},
                        'extensions': {...}
                    }
                }
            }
        },
        'extensions': {  # Root extensions hierarchical
            'root_ext': {
                'metadata': {...},
                'extensions': {...}
            }
        }
    }
}
```

### 2. Method Return Values (Proposed)
All extension methods return `self` for consistent chaining:

- **OPContainer._extend()**: Change from `return extension` to `return self`
- **OPLeaf._extend()**: Keep `return self` (already correct)
- **OProxyExtension._extend()**: Implement to return `self`

### 3. OProxyExtension Changes
- Initialize `self._extensions = {}` in `__init__`
- Implement `_extend()` method (remove `NotImplementedError`)
- Update `_refresh_extensions()` to handle nested extensions

### 4. Method Conflict Resolution

- Raise AttributeError on name conflicts in nested extensions.

- Suggest using monkey_patch=True to overwrite (not yet implemented, planned for future).

## Implementation Phases

### Phase 1: Storage Migration
1. **Update storage structure** to support hierarchical extensions ✅
2. **Create migration logic** to convert flat extension storage to hierarchical (if needed)
3. **Update `__build_storage_structure()`** to build nested extension structures ✅

### Phase 2: OProxyExtension Refactor
1. **Initialize `_extensions`** in `OProxyExtension.__init__()`

1. **Initialize `self.parent`** reference in `OProxyExtension.__init__()` for hierarchy traversal.

2. **Implement `_extend()`** method in `OProxyExtension` with circular dependency checks, depth limits (default max_depth=10), and raise if exceeded.
3. **Update `_refresh_extensions()`** for recursive extension loading: Traverse nested 'extensions' dicts, load each level recursively.
4. **Update `_remove()`** to handle nested extension cleanup: Recursively remove child extensions before removing self, clean storage cascade.

### Phase 3: Path Navigation Updates
1. **Update `_get_storage_branch()`** to handle extension paths like `container.extensions.ext1.extensions.ext2`
2. **Update path resolution** for deeply nested extensions
3. **Test path navigation** with various nesting levels

### Phase 4: Method Chaining Consistency
1. **Fix OPContainer._extend()** to return `self` instead of `extension`
2. **Verify OProxyExtension._extend()** returns `self`

## API Examples (After Implementation)

### Basic Extension Chaining
```python
opr = parent.src.OProxy

# Chain on same parent
opr._extend(cls='Logger', dat=me)._extend(cls='Timer', dat=me)

# Extend extensions
opr._extend(cls='Logger', dat=me)
opr.Logger._extend(func='logWithTimestamp', dat=me)
opr.Logger._extend(cls='Formatter', dat=me)

# Deep nesting
opr.Logger.Formatter._extend(func='jsonFormat', dat=me)
```

### Usage Examples
```python
# Access nested extensions
opr.Logger.logWithTimestamp('message')
opr.Logger.Formatter.jsonFormat(data)

# Chain multiple extensions
opr._extend(cls='Utils', dat=me)._extend(cls='Math', dat=me)._extend(cls='Stats', dat=me)

# Mix containers and extensions
opr.containers._extend(cls='Helper', dat=me)
opr.containers.Helper._extend(func='validate', dat=me)
```

## Migration Strategy

### Storage Migration
- No migration strategy since current dev is the only dev using OPRoxy

### API Compatibility
- Existing code continues to work unchanged
- New chaining capabilities are additive
- Extension access patterns remain the same

## Benefits

1. **Composability**: Build complex, modular extension systems
2. **Flexibility**: Organize extensions in hierarchical structures
3. **Consistency**: Same interface across all OProxy objects
4. **Backwards Compatible**: Existing code unaffected
5. **Chainable**: All modification methods support fluent interfaces

## Potential Concerns

1. **Storage Complexity**: More complex nested storage structure
2. **Path Resolution**: More complex path navigation for deep nesting
3. **Debugging**: More complex debugging with nested extension structures

5. **Circular Dependencies**: Detect and prevent circular extension chains (e.g., A extends B extends A) to avoid infinite recursion.

6. **Depth Limits**: Implement maximum nesting depth to prevent stack overflows in deep hierarchies.

## Success Criteria

- ✅ Extensions can be extended arbitrarily deep
- ✅ All `_extend()` methods return `self` for chaining
- ✅ Storage persists nested extension hierarchies
- ✅ Existing code continues to work
- ✅ Extension removal cleans up nested structures
- ✅ Path resolution works for deeply nested extensions

## Future Enhancements

1. **Dynamic Access Patterns** (Implement later)

   - Add get_extension(path: str) for runtime dot-path access (e.g., opr.get_extension('Logger.Formatter').method()).

   - Add find_extensions_by_cls(cls_name: str, recursive=True) for querying nested matches.

   - Include placeholder methods in relevant classes (e.g., OProxyExtension) with docstrings explaining future implementation intent.

## Docs

Update _extend_docs.md with nesting guidelines after implementation.
