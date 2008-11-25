from CompilationPass import CompilationPass
import copy

from SimpleSPARQL import Namespaces

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('var', '<http://dwiel.net/express/var/0.1/>')

class PassAssignVariableNumber(CompilationPass) :
	"""
	add a variable number to each dictionary.  Variable number is stored in
	n.sparql.var as a string
	"""
	def __call__(self, query) :
		self.var = 1
		return self.do(copy.deepcopy(query))
	
	def do(self, query) :
		if type(query) == dict :
			if n.sparql.connect in query and n.sparql.value in query :
				return query
			if n.sparql.subject not in query :
				query[n.sparql.subject] = '?autovar%d' % self.var
			self.var += 1
			for k in query :
				query[k] = self.do(query[k])
		elif type(query) == list :
			query = [self.do(i) for i in query]
		
		return query
