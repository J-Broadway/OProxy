## OProxy

Proxy system for TouchDesigner OPs with hierarchical grouping and persistent, DAT‑driven extensions.

.tox file implementaiton coming soon once core functionality is finished.

### Why OProxy?
- **Structure**: Organize operators into named, hierarchical groups you can navigate like attributes (e.g., `opr.chops.filters`), rather than hunting through networks at runtime.
- **Extensibility**: Attach reusable behaviors as persistent extensions defined in DATs. OProxy extracts classes/functions from DATs (via AST) and binds them to your proxies or proxy items.
- **Reliability**: Proxies and extensions survive reloads. Paths and names are refreshed automatically; state is stored using TouchDesigner storage.
- **Ergonomics**: Batch operations over groups of OPs, introspect the tree as ASCII, and keep logic close to your network via extension DATs.

### Core Concepts
- **OP Proxy (item-level)**: A lightweight wrapper around a single `td.OP` that allows custom attributes and methods and can bind persistent behaviors from DATs.
- **OP Container (group-level)**: A list-like collection of `OP_Proxy` items with a name and an addressable path in the hierarchy. Containers can also receive extensions that apply to the group.
- **Hierarchical Storage**: Single persistent store:
  - `OProxies`: detailed structure with OPs, extensions, and children (dict-based OPs with metadata)
- **Persistent, DAT-driven extensions**: Define a class or function at the top level of a DAT; OProxy extracts and binds it. Extensions can be class-wide (on containers) or per-item (on proxies), and can optionally be instantiated/called with arguments.

### Features
- Hierarchical grouping and attribute-style navigation of proxies
- Add/remove/refresh helpers for OP sets and subtrees
- Persistent extensions sourced from DATs (class or function) with optional `call` and `args`
- Auto-refresh of renamed/moved OPs and DATs
- ASCII tree introspection for quick overviews (`full`, `minimal` detail levels)
- Pythonic access to underlying OPs while enabling custom methods/attributes

### Requirements
- TouchDesigner (tested with Python 3.11.1 inside TouchDesigner)
- Project files loaded as DATs; each `.py` DAT begins with a comment of its filename

### Quick Start
Below are conceptual examples you can adapt inside a TouchDesigner project where this extension is installed as a COMP extension.

```python
# Assume 'opr' is the extension instance defined by OProxy (e.g., on a Base COMP)

# 1) Create a top-level group and add OPs
textures = opr._add('textures', [op('/project1/moviefilein1'), op('/project1/moviefilein2')])

# 2) Create a child group under 'textures'
filters = textures._add('filters', [op('/project1/blur1'), op('/project1/level1')])

# 3) Add more operators dynamically
filters._add('more', [op('/project1/edge1')])

# 4) Introspect the structure as an ASCII tree
opr._tree(detail='full')

# 5) Bind a persistent extension from a DAT
# In a DAT (e.g., /project1/EXT_FilterTools), define a top-level class or function:
# class FilterTools:
#     def apply(self, wrapper):
#         wrapper.par.filterwidth = 5

filters._extend(
    attr_name='tools',
    cls='FilterTools',     # or func='some_function'
    dat=op('/project1/EXT_FilterTools'),
    call=True,             # instantiate the class
    args=None
)

# Now call extension behavior on each child via Pythonic access
for wrapped in filters:
    wrapped.tools.apply(wrapped)

# 6) Persisted across reloads: call refresh to re-bind if OPs or DATs moved/renamed
opr._refresh()
```

### API Highlights (selected)
- `opr._add(name: str, op: td.OP | str | List[td.OP | str]) -> OPContainer`: Create or update a named container with OPs. Call on root `opr` or any container.
- `OPContainer._add(name, op)` / `OPContainer._remove(to_remove=None)` / `OPContainer._refresh()`: Manage subtrees and keep storage in sync.
- `OPContainer._extend(attr_name, cls=None, func=None, dat=None, args=None, call=False)`: Attach persistent class/function from a DAT to the container.
- `OP_Proxy._extend(attr_name, cls=None, func=None, dat=None, args=None, call=False)`: Attach persistent class/function from a DAT to a single item.
- `OPContainer._tree(child=None, detail='full', asDict=False)` or `opr._tree(...)`: Print an ASCII representation or retrieve raw storage.

Notes:
- When referencing DATs, define extensions as top-level `class` or `def` (no nesting) so they can be extracted.
- For persistent extensions, prefer passing `dat=op('path/to/dat')`. Non-persistent attachments are supported but won’t survive reloads.

### ASCII Tree Example
```text
<OProxy [INFO]>
root
  ├─ textures
  │  ├─ OPs
  │  │  ├─ /project1/moviefilein1
  │  │  ├─ /project1/moviefilein2
  │  └─ Children: {'filters': {...}}
  └─ filters
     ├─ OPs
     │  ├─ /project1/blur1
     │  ├─ /project1/level1
     └─ Extensions
        ├─ name: tools, cls: FilterTools, call: True
```

### Persistence and Refresh
- Structure is stored using a hierarchical mapping that records OP objects and their initial paths.
- `opr._refresh()` updates stored paths/names when OPs or extension DATs are moved/renamed, then re-applies extensions.

### Limitations
- Extensions must be defined at the top level of a DAT (no nested definitions).
- If a referenced DAT is missing or invalid, binding is skipped and a warning is logged.
- Non-persistent extensions (no `dat`) won’t survive reloads.

### Roadmap Ideas
- Higher-level convenience APIs for common TouchDesigner patterns
- Additional tree views and filtering modes
- More robust conflict resolution and renaming flows

### License
Add your preferred license here.


