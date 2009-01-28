import Parser
from Utils import sub_var_bindings, find_vars, UniqueURIGenerator
from PrettyQuery import prettyquery

import time

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
			begin_compile = time.time()
			ret_comp = self.compiler.compile(triples, reqd_bound_vars)
			end_compile = time.time()
			if ret_comp == False :
				raise Exception("Couldn't compile ... sorry I don't have more here")
			begin_eval = time.time()
			ret_eval = self.evaluator.evaluate(ret_comp)
			end_eval = time.time()
			ret_evals.extend(ret_eval)
			
			print 'compile time:',end_compile-begin_compile
			print 'eval time:',end_eval-begin_eval
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















