
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
### Phase 1: Code Updates
- In OProxyBaseWrapper.py (after rename):
  - Rename class definitions.
  - Update internal references (e.g., isinstance checks, super calls).
- Update imports and usages in:
  - oproxy.py: Change root to subclass OProxyContainer; update 'from OPBaseWrapper import OPContainer' to 'from OProxyBaseWrapper import OProxyContainer'.
  - OPContainer.py: Update re-export import to 'from OProxyBaseWrapper import OProxyContainer'.
  - utils.py: Update type checks and references to OPContainer/OProxyContainer.
  - oproxyExt.py, src.py: Update if referencing classes.
- Global search/replace for old class names, including in all dev/implemented/* and dev/plans/* files (manual review needed as they contain code examples and references).

### Phase 2: Test Updates
- Update test files (oproxy_tests.py, extend_tests.py, etc.) to use new names.
- Add tests for backwards compatibility if providing aliases.

### Phase 3: Documentation
- Update docs/_extend_docs.md and any other docs.
- Add deprecation warnings in code for old names (e.g., OPContainer = OProxyContainer).

## Files Affected
- OPBaseWrapper.py (rename and update)
- oproxy.py
- dev/tests/* (all test files)
- docs/*
- Any other files importing these classes (use grep to find).

## Testing
- Run all existing tests after refactor.
- Add tests verifying new names work as expected.
- Test deprecation warnings if implemented.

## Potential Concerns
- Breaking changes: Any external code using old names will fail.
- Missed references: Thorough search needed.
- Performance: Negligible impact.
