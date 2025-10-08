# extensions_for_tests.DAT
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

class Wrapper:
	'''Use a wrapper class so top level imports can be defined for all classes'''

	mp = mod('OProxy/MonkeyPatch')
	log = op('OProxy').Log
	td_isinstance = mod('OProxy/utils').td_isinstance

	class ResolutionMP(mp.OProxyContainer):
		"""Monkey-patched container that adds resolution() to leaves."""

		def __call__(self, identifier, **kwargs):
			# Call parent's __call__ to get the original OProxyLeaf
			leaf = super().__call__(identifier, **kwargs)
			log(f"ResolutionMP.__call__ returning ResolutionProxy wrapping leaf of type {type(leaf)} with path '{leaf.path}'")

			# Create a proxy wrapper to add custom methods to the leaf
			class ResolutionProxy:
				def __init__(self, leaf):
					self._leaf = leaf  # Store the original leaf
					log(f"ResolutionProxy created wrapping leaf of type {type(leaf)} with path '{leaf.path}'")

				def __getattr__(self, name):
					log(f"ResolutionProxy.__getattr__ called for '{name}' on leaf type {type(self._leaf)}")
					# Delegate all other attribute access to the original leaf
					return getattr(self._leaf, name)

				def resolution(self):
					# Custom method: Check if the OP is a TOP, then return resolution
					if not td_isinstance(self._leaf._op, 'top'):
						log("Not a TOP operator", status='error')
						raise ValueError("resolution() only for TOPs")
					return (self._leaf._op.width, self._leaf._op.height)

			# Return the proxy instead of the raw leaf
			return ResolutionProxy(leaf)

	class helloWorld(mp.OProxyLeaf):
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			log(f"helloWorld leaf created for OP '{self._op.name}' at path '{self.path}'")

		def helloWorld(self):
			log(f"helloWorld() called on leaf for OP '{self._op.name}'")
			info = {
				'name': self._op.name,
				'path': self._op.path,
				'parent_path': self._op.parent().path if self._op.parent() else None,
				'op_type': self._op.OPType,
				'new_data': 'hello world'
			}
			return info