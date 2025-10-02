from TDStoreTools import StorageManager
import TDFunctions as TDF
oproxy = mod('OProxy/oproxy') # import OProxy into extension 

class src: # The name of the extension for accessibility
	"""
	src description
	"""
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.OProxy = oproxy.root(ownerComp) # Container entry point so users can now do parent.src.Opr to access OProxy