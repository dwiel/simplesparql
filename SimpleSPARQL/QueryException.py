

class QueryException(Exception) :
	"""
	An exception which has occured in a Query.  The path information and message 
	can be used to return a meaningful response.
	"""
	def __init__(self, path, message, debug_path = None) :
		if type(path) == list :
			path = tuple(path)
		self.path = path
		self.message = message
		self.debug_path = debug_path
	
	def __str__(self) :
		if self.debug_path :
			return 'error in %s (debug: %s): %s' % (repr(self.path), repr(self.debug_path), repr(self.message))
		else :
			return 'error in %s : %s' % (repr(self.path), repr(self.message))
	
	def __eq__(self, other) :
		return self.path == other.path and self.message == other.message and self.debug_path == other.debug_path
