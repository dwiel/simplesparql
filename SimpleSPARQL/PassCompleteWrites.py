from CompilationPass import CompilationPass
import copy
import PrettyQuery
prettyquery = PrettyQuery.prettyquery

from SimpleSPARQL import Namespaces
from QueryException import QueryException
from PassUtils import dictrecursiveupdate

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('var', '<http://dwiel.net/express/var/0.1/>')

class PassCompleteWrites(CompilationPass) :
	def __init__(self, sparql) :
		self.sparql = sparql
	
	def __call__(self, query) :
		"""
		write each read query to the database and fill in any missing values
		"""
		
		for write in query[n.sparql.writes] :
			if n.sparql.create in write and write[n.sparql.write] == n.sparql.create :
				pass
				# write this object to the graph
			if n.sparql.create in write and write[n.sparql.write] == n.sparql.connect :
				pass
				# connect the object up ...
		
		pass











