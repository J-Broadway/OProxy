# src.dat
from TDStoreTools import StorageManager 
import TDFunctions as TDF
import oproxy		# Import oproxy

class src:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.OProxy = oproxy.opr(ownerComp) # Add to container scope and pass ownerComp
		'''  ^
		The 'O' here needs to be capitalized to be enabled as a 'Promoted' attribute
		(see TouchDesigner extension documentation for more info)
		'''