# src.dat
from TDStoreTools import StorageManager 
import TDFunctions as TDF
import oproxy		# Import oproxy

class src:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.Opr = oproxy.opr(ownerComp) # Add to container scope and pass ownerComp