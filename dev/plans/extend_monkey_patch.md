
# _extend() Monkey-Patch Enhancement - Construction Document

## Overview
Add monkey_patch support to _extend() for overwriting existing containers with custom subclasses, enabling custom behaviors like in the example.

## Current Behavior
- _extend() raises error if attr_name exists unless monkey_patch=True (for extensions).
- No support for subclassing/replacing existing OProxyContainer instances.

## Proposed Behavior
opr._add('items', mvs)  # Creates OProxyContainer 'items'
opr._extend('items', cls='OverwriteItems', dat='extensions_for_tests', monkey_patch=True)  # Replaces with OverwriteItems subclass, preserving state.

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

## Potential Concerns
- Deep state copying.
- Extension migration.
- Infinite recursion if not careful.
