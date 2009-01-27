import Parser
from Utils import sub_var_bindings, find_vars, UniqueURIGenerator
from PrettyQuery import prettyquery

class Axpress() :
	def __init__(self, sparql, compiler, evaluator) :
		self.sparql = sparql
		# self.translator = translator
		self.compiler = compiler
		self.evaluator = evaluator
		self.parser = Parser.Parser(sparql.n)
	
	def read_translate(self, query, bindings_set = [{}], reqd_bound_vars = []) :
		query_triples = self.parser.parse(query)
		ret_evals = []
		for triples in sub_var_bindings(query_triples, bindings_set) :
			ret_comp = self.compiler.compile(triples, reqd_bound_vars)
			ret_eval = self.evaluator.evaluate(ret_comp)
			ret_evals.extend(ret_eval)
		return ret_evals
	
	def write_translate(self, query, bindings_set = [{}]) :
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

	def write_sparql(self, query, bindings_set = [{}]) :
		query_triples = self.parser.parse(query)
		for triples in sub_var_bindings(query_triples, bindings_set) :
			missing_vars = find_vars(triples)
			if len(missing_vars) is not 0 :
				urigen = UniqueURIGenerator()
				new_bindings = [dict([(var, urigen()) for var in missing_vars])]
				triples = sub_var_bindings(triples, new_bindings).next()
			self.sparql.write(triples)















