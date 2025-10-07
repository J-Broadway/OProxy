
# Class Rename Refactor - Construction Document

## Overview
Refactor class names in OProxy system for better specificity and clarity, prefixing with 'OProxy' to distinguish from TouchDesigner 'OP' terminology.

## Current Classes
- OPBaseWrapper: Abstract base class for wrappers.
- OPContainer: Composite container class.
- OPLeaf: Leaf node for individual OPs.
- OProxyExtension: Extension wrapper (already prefixed, no change).
- root: Subclass of OPContainer for root.

## Proposed Changes
- OPBaseWrapper → OProxyBaseWrapper
- OPContainer → OProxyContainer
- OPLeaf → OProxyLeaf
- root: Update to subclass OProxyContainer.
- File rename: OPBaseWrapper.py → OProxyBaseWrapper.py
- No change to OProxyExtension.

## Implementation Strategy
### Phase 1: File Rename
- Rename OPBaseWrapper.py → OProxyBaseWrapper.py

### Phase 2: Class Renames
- In OProxyBaseWrapper.py:
  - Rename class definitions (OPBaseWrapper → OProxyBaseWrapper, OPContainer → OProxyContainer, OPLeaf → OProxyLeaf).
  - Update internal references (e.g., isinstance checks, super calls).

### Phase 3: Import/Reference Updates
- Update imports and usages in:
  - oproxy.py: Change root to subclass OProxyContainer; update 'from OPBaseWrapper import OPContainer' to 'from OProxyBaseWrapper import OProxyContainer'.
  - OPContainer.py: Update re-export import to 'from OProxyBaseWrapper import OProxyContainer'.
  - utils.py: Update type checks and references to use new class names (OPContainer → OProxyContainer, etc.).
  - oproxyExt.py, src.py: Update if referencing classes.
- Global search/replace for old class names, including in all dev/implemented/* and dev/plans/* files (manual review needed as they contain code examples and references).

### Phase 4: Test Updates
- Update test files (oproxy_tests.py, extend_tests.py, etc.) to use new names.

### Phase 5: Documentation
- Update docs/_extend_docs.md and any other docs.

## Files Affected
- OPBaseWrapper.py (rename to OProxyBaseWrapper.py and update)
- oproxy.py
- OPContainer.py
- utils.py
- dev/tests/* (all test files)
- dev/implemented/* (manual review for code examples)
- dev/plans/* (manual review for code examples)
- docs/*

## Testing
- Run all existing tests after refactor (user will take care of this).

## Potential Concerns
- Missed references: Thorough search needed.
- Performance: Negligible impact.
