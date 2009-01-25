import Parser
from Utils import sub_var_bindings
from PrettyQuery import prettyquery

class Axpress() :
	def __init__(self, sparql, compiler) :
		self.sparql = sparql
		# self.translator = translator
		self.compiler = compiler
		self.parser = Parser.Parser(sparql.n)
	
	def read_translate(self, query, bindings_set = [{}], reqd_bound_vars = []) :
		query_triples = self.parser.parse(query)
		rets = []
		for triples in sub_var_bindings(query_triples, bindings_set) :
			rets.append(self.compiler.new_compile(triples, reqd_bound_vars))
		return rets
	
	def write_translate(self, query) :
		pass
	
	def read_sparql(self, query, bindings_set = [{}]) :
		"""
		read from the sparql database
		@arg query the query in one long string, a list of string or triples_set
		@return a generator yielding sets of bindings
		"""
		query_triples = self.parser.parse(query)
		for triples in sub_var_bindings(query_triples, bindings_set) :
			print 'triples',prettyquery(triples)
			for result in self.sparql.read(triples) :
				yield result

	def write_sparql(self, query) :
		pass