import Parser, Evaluator, MultilineParser
from Utils import sub_var_bindings, sub_var_bindings_set, find_vars, UniqueURIGenerator, debug, is_any_var, var_name, explode_bindings_set, p, is_lit_var
from PrettyQuery import prettyquery

import time, copy

class Axpress() :
	def __init__(self, sparql, compiler, evaluator = None, multiline_parser = None, options = ['time']) :
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
		self.options = options
		
	def do(self, query, bindings_set = [{}], options = None) :
		if options is None :
			options = self.options
		return self.multiline_parser.parse(query, bindings_set, self.options)
	
	def read_translate(self, query, bindings_set = [{}], reqd_bound_vars = []) :
		query_triples = self.parser.parse(query)
		ret_evals = []
		bindings_set = explode_bindings_set(bindings_set)
		if len(reqd_bound_vars) == 0 :
			reqd_bound_vars = find_vars(query_triples, is_lit_var)
			if len(reqd_bound_vars) == 0 :
				p('Warning: no required bound variables.  Are there any _vars?')
		
		#for triples in sub_var_bindings_set(query_triples, bindings_set) :
		for bindings in bindings_set :
			#p('bindings',bindings)
			#p('reqd_bound_vars',reqd_bound_vars)
			new_reqd_bound_vars = []
			provided_bindings = []
			for var in reqd_bound_vars :
				if var in bindings :
					provided_bindings.append(var)
				else :
					new_reqd_bound_vars.append(var)
			reqd_bound_vars = new_reqd_bound_vars
			
			#p('reqd_bound_vars',reqd_bound_vars)
			#p('provided_bindings',provided_bindings)
			triples = sub_var_bindings(query_triples, bindings)
			begin_compile = time.time()
			ret_comp = self.compiler.compile(triples, reqd_bound_vars)
			end_compile = time.time()
			#p('ret_comp',ret_comp)
			if 'time' in self.options :
				print 'compile time:',end_compile-begin_compile
			if ret_comp == False :
				raise Exception("Couldn't compile ... sorry I don't have more here")
			begin_eval = time.time()
			#for i in range(100) :
			ret_eval = self.evaluator.evaluate(ret_comp)
			end_eval = time.time()
			if 'time' in self.options :
				print 'eval time:',end_eval-begin_eval
			for ret in ret_eval :
				for var in provided_bindings :
					ret[var] = bindings[var]
			#p('ret_eval',ret_eval)
			ret_evals.extend(ret_eval)
			
		return ret_evals
	
	def write_translate(self, query, bindings_set = [{}]) :
		# TODO: figure out what this even means!
		p('write_translate')
		p('query',query)
		p('bindings_set',bindings_set)
		pass
	
	def read_sparql(self, query, bindings_set = [{}], keep_old_bindings = False) :
		"""
		read from the sparql database
		@arg query the query in one long string, a list of string or triples_set
		@arg bindings_set is a set of bindings to apply on the way in
		@arg keep_old_bindings if True will keep variable bound in the incoming 
		bindings_set in the new bindings_set
		@return a new set of bindings
		"""
		results = []
		query_triples = self.parser.parse(query)
		#p('query_triples',query_triples)
		#for triples in sub_var_bindings_set(query_triples, bindings_set) :
		for bindings in explode_bindings_set(bindings_set) :
			triples = sub_var_bindings(query_triples, bindings)
			#self.sanitize_vars(triples)
			read_bindings_set = self.sparql.read(triples, outvarnamespace = self.n.lit_var)
			if keep_old_bindings :
				#p('bindings',bindings)
				#p('read_bindings_set',read_bindings_set)
				for read_bindings in read_bindings_set :
					new_bindings = copy.copy(bindings)
					new_bindings.update(read_bindings)
					results.append(new_bindings)
			else :
				results.extend(read_bindings_set)
		return results

	def write_sparql(self, query, bindings_set = [{}]) :
		"""
		write triples into sparql database.
		NOTE: any URI which is_var will be converted to a fresh bnode URI
		"""
		query_triples = self.parser.parse(query)
		bindings_set = explode_bindings_set(bindings_set)
		for bindings in bindings_set :
			triples = sub_var_bindings(query_triples, bindings)
			missing_vars = find_vars(triples)
			if len(missing_vars) is not 0 :
				new_bindings = dict([(var, self.urigen()) for var in missing_vars])
				triples = sub_var_bindings(triples, new_bindings)
				bindings.update(new_bindings)
			self.sparql.write(triples)
		return bindings_set
	
	def write_sparql_delete(self, query, bindings_set = [{}]) :
		"""
		delete triples from sparql database.
		NOTE: any URI which is_var will be converted to a fresh bnode URI
		"""
		query_triples = self.parser.parse(query)
		bindings_set = explode_bindings_set(bindings_set)
		for triples in sub_var_bindings_set(query_triples, bindings_set) :
			# replace any kind of var with a 'standard' var for SimpleSPARQL
			for triple in triples :
				for i, v in enumerate(triple) :
					if is_any_var(v) :
						triple[i] = self.n.var[var_name(v)]
			self.sparql.delete(triples)

	def python(self, query, bindings_set = [{}]) :
		new_bindings_set = []
		for bindings in bindings_set :
			# TODO don't allow people to break in!  Not sure how good this is ...
			bindings['__builtins__'] = None
			exec query in bindings
			del bindings['__builtins__']
			new_bindings_set.extend(explode_bindings_set(bindings))
		return new_bindings_set
	













