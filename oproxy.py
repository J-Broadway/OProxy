# oproxy.py - Root entry point for OProxy
from TDStoreTools import StorageManager
from OPBaseWrapper import OPContainer

class root(OPContainer):
    """Root OProxy container."""

    def __init__(self, ownerComp):
        super().__init__(ownerComp=ownerComp, path="", parent=None, root=True)

        # Initialize TouchDesigner storage using StorageManager
        storedItems = [
            {
                'name': 'OProxies',
                'default': {
                            'children': {},
                            'extensions': [],
                            },
                'dependable': True
            }
        ]
        self.storage = StorageManager(self, ownerComp, storedItems)

        # Any root-specific setup here (e.g., logging if needed later)
        print("OProxy root initialized")
        '''
        Notes thus far
        print(self.OProxies) # will print {'children': {}, 'extensions': []} to console
        Usage examples on how to access storage
        self.OProxies['children'] = {'hello': 'world'} # {'OProxies': {'children': {'hello': 'world'}, 'extensions': []}}
        self.OProxies['extensions'] = ['hello', 'extensions'] # Dictionary now {'OProxies': {'children': {'hello': 'world'}, 'extensions': ['hello', 'extensions']}}
        '''

    
