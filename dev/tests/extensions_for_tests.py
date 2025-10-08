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

class mpWrapper:
	'''Use a wrapper class so top level imports can be defined for all classes'''
	mp 				= mod('OProxy/MonkeyPatch') # Loaed helpers for monkey patching
	log 			= mod('OProxy/MonkeyPatch').log
	td_isinstance	= mod('OProxy/utils').td_isinstance

	class OProxyContainer(mp.OProxyContainer):
		"""Monkey-patched container that adds both resolution() and custom .par() method behavior on leaves."""

		def __call__(self, identifier, **kwargs):
			# Call parent's __call__ to get the original OProxyLeaf
			leaf = super().__call__(identifier, **kwargs)

			# Define the custom par accessor locally
			class CustomParAccessor:
				"""Custom parameter accessor that supports method-style calls."""

				def __init__(self, leaf):
					self._leaf = leaf

				def __call__(self, customFlag=False, **kwargs):
					"""Called when doing .par(customFlag=True)"""
					if customFlag:
						log(f"Custom flag activated for {self._leaf._op.name}")
						# Implement your custom mp.logic here

					# Return the actual TouchDesigner par object for chaining
					return self._leaf._op.par

				def __getattr__(self, name):
					"""Allow direct attribute access like .par.width"""
					return getattr(self._leaf._op.par, name)

			# Create a proxy wrapper that combines both functionalities
			class CustomProxy:
				def __init__(self, inner_leaf):
					self._inner = inner_leaf

				def __getattr__(self, name):
					if name == 'par':
						# Return a custom par object that can be called with parameters
						return CustomParAccessor(self._inner)
					# Delegate all other attribute access to the original leaf
					return getattr(self._inner, name)

				def resolution(self):
					# Custom method: Check if the OP is a TOP, then return resolution
					if not td_isinstance(self._inner._op, 'top'):
						log("Not a TOP operator", status='error')
						raise ValueError("resolution() only for TOPs")
					return [self._inner._op.width, self._inner._op.height]

			# Return the proxy instead of the raw leaf
			return CustomProxy(leaf)

	class helloWorld(mp.OProxyLeaf):
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)

		def helloWorld(self):
			info = {
				'name': self._op.name,
				'path': self._op.path,
				'parent_path': self._op.parent().path if self._op.parent() else None,
				'op_type': self._op.OPType,
				'new_data_updated': 'hello world'
			}
			return info