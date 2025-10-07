# oproxy.py - Root entry point for OProxy
from TDStoreTools import StorageManager
from OProxyBaseWrapper import OProxyContainer

# Import utils module for logging functions
utils = mod('utils')
Log = parent.opr.Log 

'''
NOTES FOR LLMs:
- self.OProxies is a DependDict (from TDStoreTools) managed by StorageManager.
- It behaves like a dict but triggers dependency updates on changes.
- AVOID direct assignments like self.OProxies['key'] = value - may not trigger dependencies properly.
- Use DependDict methods:
  - self.OProxies.setItem('key', value) to set values and maintain dependability.
  - self.OProxies.getRaw() to get plain dict without dependencies.
- For full reset, use self._storage.restoreDefault('OProxies') - properly resets to default and syncs dependencies.
- Storage persists automatically via StorageManager.
- Direct prints: print(self.OProxies.getRaw()) shows plain dict.
- Modifying nested structures: Ensure changes use setItem for dependability.
- If modifying collections inside, they may need to be wrapped as DependDict/List/Set for deep dependability.
'''

class root(OProxyContainer):
    """Root OProxy container."""

    def __init__(self, ownerComp):
        super().__init__(ownerComp=ownerComp, path="", parent=None, root=True)

        # Initialize TouchDesigner storage using StorageManager
        # 
        storedItems = [
            {
                'name': 'OProxies',
                'default': {
                            'children': {},
                            'extensions': {},
                            },
                'dependable': True
            }
        ]
        # 'OProxies' gets nested in'rootStorage' since 'root' is the name of the container extension and TD inits storage as '<extension_name>Storage'
        self._storage_manager = StorageManager(self, ownerComp, storedItems)

        # Migrate old storage format to new format if needed
        self._migrate_storage_format()

        # Any root-specific setup here (e.g., logging if needed later)
        self._refresh()  # Load persisted hierarchy from storage
        Log("OProxy root initialized", status='info', process='Init')

    def _migrate_storage_format(self):
        """Migrate old string-based OP storage to new object format."""
        def migrate_container_ops(container_data):
            """Recursively migrate ops in a container and its children."""
            if 'ops' in container_data:
                migrated_ops = {}
                for op_name, op_info in container_data['ops'].items():
                    if isinstance(op_info, str):
                        # Old format: convert string path to object
                        op = td.op(op_info)
                        if op and op.valid:
                            migrated_ops[op_name] = {
                                'path': op_info,
                                'op': op,
                                'extensions': {}
                            }
                        else:
                            Log(f"Could not migrate invalid OP path '{op_info}' for '{op_name}'", status='warning', process='Migration')
                    else:
                        # Already in new format or other structure
                        migrated_ops[op_name] = op_info
                container_data['ops'] = migrated_ops

            # Recursively migrate children containers
            if 'children' in container_data:
                for child_data in container_data['children'].values():
                    migrate_container_ops(child_data)

        # Migrate the root storage
        if hasattr(self, 'OProxies') and 'children' in self.OProxies:
            Log("Checking for storage format migration", status='debug', process='Migration')
            needs_migration = False

            # Check if any ops are stored as strings (old format)
            def check_for_old_format(data):
                nonlocal needs_migration
                if 'ops' in data:
                    for op_info in data['ops'].values():
                        if isinstance(op_info, str):
                            needs_migration = True
                            return
                if 'children' in data:
                    for child_data in data['children'].values():
                        check_for_old_format(child_data)

            check_for_old_format(self.OProxies)

            if needs_migration:
                Log("Migrating storage from old string format to new object format", status='info', process='Migration')
                migrate_container_ops(self.OProxies)
                Log("Storage migration completed", status='info', process='Migration')
            else:
                Log("Storage already in new format, no migration needed", status='debug', process='Migration')

    def _clear(self, flush_logger=True):
        """Clear all stored OProxy data and reload empty hierarchy.

        Args:
            flush_logger (bool): Whether to flush the logger. Defaults to True.
        """
        if flush_logger:
            Log.flush()  # Clear logging state and log files for fresh start

        Log("Starting _clear operation", status='info', process='_clear')

        # Clear root level extensions first
        Log(f"Clearing root extensions: {list(self._extensions.keys())}", status='debug', process='_clear')
        for extension_name in list(self._extensions.keys()):
            try:
                extension = self._extensions[extension_name]
                extension._remove()
                Log(f"Removed root extension '{extension_name}'", status='debug', process='_clear')
            except Exception as e:
                Log(f"Failed to remove root extension '{extension_name}': {e}", status='warning', process='_clear')

        # Restore storage to default
        Log("Restoring OProxies to default empty state", status='debug', process='_clear')
        self._storage_manager.restoreDefault('OProxies')

        # Clear in-memory hierarchy
        Log(f"Clearing in-memory hierarchy with {len(self._children)} containers", status='debug', process='_clear')
        self._children.clear()
        self._extensions.clear()  # Clear any remaining extension references

        Log("Reloading empty hierarchy", status='debug', process='_clear')
        self._refresh()  # Reload from the now-empty storage

        Log("_clear operation completed", status='info', process='_clear')


