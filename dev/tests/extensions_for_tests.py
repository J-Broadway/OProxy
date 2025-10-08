# extensions_for_tests.DAT
mp = op('OProxy').MonkePatch
log = op('OProxy').Log

def hello(self, arg=None):
	if arg is None:
		return 'hello world func extension is working'
	else:
		return arg

def callTrueTest(self, arg1):
	 return f'{arg1}'
	
class myClass:
	def __init__(self, args=None):
		print("myClass called from extensions_for_tests")
		if args is not None:
			print('ARGS PASSED THRU WORKING')
	def testFunc(self):
		return 'testFunc called I AM WORKING YAY'

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



