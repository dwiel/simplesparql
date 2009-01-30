import Parser, Evaluator, MultilineParser
from Utils import sub_var_bindings, find_vars, UniqueURIGenerator, debug, is_any_var, var_name
from PrettyQuery import prettyquery

import time

class Axpress() :
	def __init__(self, sparql, compiler, evaluator = None, multiline_parser = None) :
		self.sparql = sparql
		self.n = sparql.n
		# self.translator = translator
		self.compiler = compiler
		if evaluator == None :
			evaluator = Evaluator.Evaluator(self.n)
		self.evaluator = evaluator
		self.parser = Parser.Parser(self.n)
		self.urigen = UniqueURIGenerator()
		if multiline_parser == None :
			multiline_parser = MultilineParser.MultilineParser(self.n, self)
		self.multiline_parser = multiline_parser
		
	def do(self, query) :
		return self.multiline_parser.parse(query)
	
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
	
	def sanitize_vars(self, triples) :
		for triple in triples :
			for j, value in enumerate(triple) :
				print 'v',prettyquery(value)
				if is_any_var(value) :
					print "HERE"
					triple[j] = self.n.var[var_name(value)]
	
	def read_sparql(self, query, bindings_set = [{}]) :
		"""
		read from the sparql database
		@arg query the query in one long string, a list of string or triples_set
		@return a sets of bindings
		"""
		results = []
		query_triples = self.parser.parse(query)
		for triples in sub_var_bindings(query_triples, bindings_set) :
			print 'triples',prettyquery(triples)
			self.sanitize_vars(triples)
			print 'triples',prettyquery(triples)
			results.extend(self.sparql.read(triples))
		return results

	def write_sparql(self, query, bindings_set = [{}]) :
		"""
		write triples into sparql database.
		NOTE: any URI which is_var will be converted to a fresh bnode URI
		"""
		query_triples = self.parser.parse(query)
		for triples in sub_var_bindings(query_triples, bindings_set) :
			missing_vars = find_vars(triples)
			if len(missing_vars) is not 0 :
				new_bindings = [dict([(var, self.urigen()) for var in missing_vars])]
				triples = sub_var_bindings(triples, new_bindings).next()
			self.sparql.write(triples)















