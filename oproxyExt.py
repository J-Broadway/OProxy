from TDStoreTools import StorageManager
import TDFunctions as TDF
OPLogger = mod('OPLogger/OPLogger')

class oproxyExt:
	"""
	oproxyExt description
	"""
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp 
		self.Log = OPLogger.root(ownerComp) 