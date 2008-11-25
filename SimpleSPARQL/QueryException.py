

class QueryException(Exception) :
	"""
	An exception which has occured in a Query.  The path information and message 
	can be used to return a meaningful response.
	"""
	def __init__(self, path, message) :
		if type(path) == list :
			path = tuple(path)
		self.path = path
		self.message = message
	
	def __str__(self) :
		return 'error in %s : %s' % (repr(self.path), repr(self.message))
	
	def __eq__(self, other) :
		return self.path == other.path and self.message == other.message
