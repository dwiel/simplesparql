

class Axpress() :
	def __init__(self, sparql, translator) :
		self.sparql = sparql
		self.translator = translator
	
	def read_translate(self, query) :
		return None
	
	def write_translate(self, query) :
		pass
	
	def read_sparql(self, query) :
		# this does the read, it doesn't connect to logic behind it. (connecting it
		# with the rest of the query
		ret = self.sparql.read( g.group(1) )
		ret = [x for x in ret]
		print 'sparql read(', g.group(1),') =',prettyquery(ret)
		return ret

	
	def write_sparql(self, query) :
		pass