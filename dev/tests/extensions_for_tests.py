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
	def testFunc():
		return 'testFunc called I AM WORKING YAY'

