from CompilationPass import CompilationPass

class PassWrapInList(CompilationPass) :
	"""
	Wrap the query in a list.  This doesn't change the meaning of the query, but
	removes a special case.
	"""
	def __call__(self, query) :
		if type(query) != list :
			return [query]
		return query
