from SimpleSPARQL import SimpleSPARQL
from Namespaces import Namespaces
from PrettyQuery import prettyquery
from Parser import Parser
from Utils import *

from Bindings import Bindings

from rdflib import URIRef

from itertools import izip
import copy, time, random

class Compiler :
	MAYBE = 'maybe'
	
	def __init__(self, n = None) :
		if n :
			self.n = n
		else :
			self.n = Namespaces()
		self.n.bind('out_lit_var', '<http://dwiel.net/axpress/out_lit_var/0.1/>')
		self.n.bind('out_var', '<http://dwiel.net/axpress/out_var/0.1/>')
		#self.n.bind('tvar', '<http://dwiel.net/axpress/translation/var/0.1/>')
		#self.n.bind('bnode', '<http://dwiel.net/axpress/bnode/0.1/>')
		#self.n.bind('meta', '<http://dwiel.net/axpress/meta/0.1/>')
		
		self.parser = Parser(self.n)

		self.translations = []
		#self.sparql = sparql
		self._next_num = 0
	
	def register_translation(self, translation) :
		n = self.n
		
		# make sure all of the required keys are present
		required = [n.meta.input, n.meta.output, n.meta.function, n.meta.name]
		missing = [key for key in required if key not in translation]
		if missing :
			raise Exception('translation is missing keys: %s' % prettyquery(missing))
		
		if n.meta.constant_vars not in translation :
			translation[n.meta.constant_vars] = []
		
		# parse any string expressions
		translation[n.meta.input] = self.parser.parse_query(translation[n.meta.input])
		translation[n.meta.output] = self.parser.parse_query(translation[n.meta.output])
		
		#print 'registering'
		#print translation[n.meta.name]
		#print prettyquery(translation[n.meta.input])
		#print prettyquery(translation[n.meta.output])
		#print
		
		self.translations.append(translation)
	
	#@logger
	def values_match(self, value, qvalue) :
		if type(value) == URIRef :
			#if is_out_var(value) or is_out_var(qvalue) :
				#print '???',prettyquery(value),prettyquery(qvalue)
			
			if is_var(value) :
				return True
			elif is_meta_var(value) :
				if type(qvalue) == URIRef :
					return is_any_var(qvalue) and not is_lit_var(qvalue)
					# return is_any_var(qvalue) and not is_meta_var(qvalue)
				else :
					return False
			elif is_lit_var(value) :
				if type(qvalue) == URIRef :
					return is_lit_var(qvalue) or not is_any_var(qvalue)
					# return qvalue.find(self.n.var) != 0 and qvalue.find(self.n.lit_var) != 0
				else :
					return True
			elif is_out_lit_var(value) :
				#print 'does this happen?',prettyquery(value),prettyquery(qvalue)
				# not often ... probably only in the if matches(q,v) or (v,q) ...
				if is_lit_var(qvalue) :
					return True
				elif is_any_var(qvalue) :
					return False
				else :
					return True
		if value == qvalue :
			return True
		#return False
	
	def triples_match(self, triple, qtriple) :
		for tv, qv in izip(triple, qtriple) :
			#print 'v',prettyquery(tv),'q',prettyquery(qv)
			if not self.values_match(tv, qv) :
				return False
		return True
	
	def find_triple_match(self, triple, query) :
		for qtriple in query :
			if self.triples_match(triple, qtriple) :
				return True
		return False
	
	def get_binding(self, triple, qtriple) :
		binding = {}
		for t, q in izip(triple, qtriple) :
			if is_any_var(t) and self.values_match(t, q):
				# if the same var is trying to be bound to two different values, 
				# not a valid binding
				if t in binding and binding[var_name(t)] != q :
					return {}
				binding[var_name(t)] = q
			elif t != q :
				return {}
		return binding
	
	def find_bindings_for_triple(self, triple, query) :
		bindings = []
		for qtriple in query :
			binding = self.get_binding(triple, qtriple)
			if binding and binding not in bindings :
				bindings.append(binding)
		
		return bindings
	
	def conflicting_bindings(self, a, b) :
		"""
		a and b are dictionaries.  Returns True if there are keys which are in 
		both a and b, but have different values.  Used in unification
		"""
#		print 'a',prettyquery(a)
#		print 'b',prettyquery(b)
		for k, v in a.iteritems() :
			if k in b and b[k] != v :
				if self.values_match(b[k], v) or self.values_match(v, b[k]):
					#print 'maybe',prettyquery(b[k]), prettyquery(v)
					#return self.MAYBE
					return True
				return True
		return False
	
	def has_already_executed(self, history, translation, binding) :
		return [translation, binding] in history
	
	def register_executed(self, history, translation, binding) :
		history.append([translation, copy.copy(binding)])
		
	def bind_vars(self, translation, query) :
		"""
		@arg translation is a list of triples (the translation)
		@arg query is a list of triples (the query)
		@returns matches, bindings
			matches is True if the query matches the translation
			bindings is a list of bindings for var to value
		"""
		bindings = []
		matches = True
		#debug('translation',translation)
		#print 'q',prettyquery(query)
		bindings = [Bindings()]
		for ttriple in translation :
			possible_bindings = self.find_bindings_for_triple(ttriple, query)
			new_bindings = []
			# see if any of the next_bindings fit with the existing bindings
			found_binding = False
			for pbinding in possible_bindings :
				# if there are no values in bindings that already have some other 
				# value in bindings 
				for binding in bindings :
					#debug('ttriple',ttriple)
					conflicting = self.conflicting_bindings(binding, pbinding)
					#debug('binding',binding)
					#debug('pbinding',pbinding)
					#debug('conflicting',conflicting)
					if not conflicting :
						# WARNING: this isn't going to copy the values of the bindings!!!
						new_binding = copy.copy(binding)
						#print prettyquery(new_binding)
						#print prettyquery(pbinding)
						#print
						new_binding.update(pbinding)
						if new_binding not in new_bindings :
							#debug('new_binding',new_binding)
							new_bindings.append(new_binding)
							found_binding = True
					elif conflicting == self.MAYBE :
						# WARNING: this isn't going to copy the values of the bindings!!!
						new_binding = Bindings(binding, possible = True)
						#print prettyquery(new_binding)
						#print prettyquery(pbinding)
						#print
						new_binding.update(pbinding)
						if new_binding not in new_bindings :
							#debug('maybe_new_binding',new_binding)
							new_bindings.append(new_binding)
							found_binding = True
						#debug('maybe ... this will work')
						matches = self.MAYBE
			#debug('found_binding',found_binding)
			if not found_binding :
				return False, []
			if len(new_bindings) > 0 :
				bindings = new_bindings
		
		#debug('bindings',bindings)
		
		# get a set of all vars
		vars = find_vars(translation)
		
		# if there are no vars, this does still match, but there are no bindings
		if len(vars) == 0 :
			return matches, []
		
		# keep only the bindings which contain bindings for all of the vars
		bindings = [binding for binding in bindings if len(binding) == len(vars)]
		
		# if there are no bindings (and there are vars), failed to find a match
		if len(bindings) == 0 :
			return False, []
		
		#debug('matches',matches)
		#debug('bindings',bindings)
		
		return matches, bindings
	
	def find_bindings(self, data, pattern, output_vars = []) :
		"""
		@arg data is the set of triples whose values are attempting to matched to
		@arg pattern is the pattern whose variables are attempting to be matched
		@arg output_vars are variables which are not allowed to be bound to a 
			literal variable in the pattern
		@return matches, set_of_bindings
			matches is True iff the query matched the set of data
			set_of_bindings is the set of bindings which matched the data
		"""
		# print 'testing', translation[self.n.meta.name]
		# check that all of the translation inputs match part of the query
		for triple in pattern :
			if not self.find_triple_match(triple, data) :
				return False, None
		
		# find all possible bindings for the vars if any exist
		matches, bindings_set = self.bind_vars(pattern, data)
		return matches, bindings_set
	
	def testtranslation(self, translation, query, output_vars) :
		"""
		@returns matches, bindings
			matches is True iff the translation is guarenteed to match the query.  It 
				is self.MAYBE if the translation might match the query and False if it
				is guarenteed to not match the query.
			bindings is the set of bindings which allow this translation to match the
				query
		"""
		#debug('testing',translation[self.n.meta.name])
		return self.find_bindings(query, translation[self.n.meta.input], output_vars)
	
	def next_bnode(self) :
		return self.n.bnode[str(time.time()).replace('.','') + '_' +  str(random.random()).replace('.','')]
	
	def find_paths(self, query, find_vars) :
		for possible_translation in possible_translations :
			something = find_paths(possible_translation, find_vars)
	
	# return all triples which have at least one var
	def find_var_triples(self, query, is_a_var = is_any_var) :
		return [triple for triple in query if any(map(lambda x:is_a_var(x), triple))]
	
	# return all triples which have at least one var
	def find_specific_var_triples(self, query, vars) :
		return [triple for triple in query if any(map(lambda x:is_any_var(x) and var_name(x) in vars, triple))]


	def next_num(self) :
		self._next_num += 1
		return self._next_num

	#@logger
	def next_translations(self, query, history, output_vars) :
		"""
		@arg query the query in triples set form
		@arg history the history of steps already followed
		@arg output_vars is a set of variables which are not allowed to be bound as
			an input to a translation
		@returns the set of next guarenteed_steps and possible_steps.
			Ensures that this set of translation and bindings haven't already been 
			searched.....
		"""
		n = self.n
		
		guarenteed_steps = []
		possible_steps = []
		
		#debug('output_vars',output_vars)
		
		def bindings_contain_output_var(bindings) :
			# check to see if any of the bindings are with output_variables which
			# don't actually have a value yet
			for var, value in bindings.iteritems() :
				#if is_any_var(value) and var_name(value) in output_vars :
				if (is_lit_var(value) or is_out_lit_var(value)) and var_name(value) in output_vars :
					print 'bcov',prettyquery(value),prettyquery(output_vars)
					return True
			return False
		
		for translation in self.translations :
			matches, bindings_set = self.testtranslation(translation, query, output_vars)
			#debug('match %s' % translation[n.meta.name], matches)
			#debug('bindings_set', bindings_set)
			if matches :
				for bindings in bindings_set :
					# not allowed to bind an output variable as a value to the input of a
					# translation
					if bindings_contain_output_var(bindings) :
						continue
					
					#print '---'
					#print 'bindings',prettyquery(bindings)
					#print 'translation',prettyquery(translation)
					# keep the possible property
					new_bindings = Bindings(possible = bindings.possible)
					# replace the bindings which the translation defines as constant with
					# the exact binding value
					#print '???',prettyquery(value),prettyquery(q
					# replace the other bindings which are variables, with variables with
					# the name from the query and the type from the translation ...
					# TODO?: keep the state of each of the variables in the triple set
					# rather than as the namespace so it can be changed and checked 
					# easily.  Also, it should be consistant throughout the query anyway
					new_lit_vars = {}
					for var, value in bindings.iteritems() :
						if var in translation[n.meta.constant_vars] :
							new_bindings[var] = value
						elif is_any_var(value) :
							new_var = n.lit_var[var_name(value)+'_'+str(self.next_num())]
							new_lit_vars[var_name(value)] = new_var
							new_bindings[var] = new_var
					
					#input_bindings = dict([(var, binding) for (var, binding) in bindings.iteritems() if not is_var(binding)])
					input_bindings = bindings
					output_bindings = {}
					
					for var in find_vars(translation[n.meta.output]) :
						if var not in translation[n.meta.constant_vars] :
							output_bindings[var] = n.lit_var[var+'_out_'+str(self.next_num())]
						else :
							output_bindings[var] = input_bindings[var]
					
					#debug('input_bindings',input_bindings)
					#debug('output_bindings',output_bindings)
					#print 'new_bindings',prettyquery(new_bindings)
					#print 'new_lit_vars',prettyquery(new_lit_vars)
					
					new_triples = sub_var_bindings(translation[n.meta.output], [output_bindings]).next()
					new_query = copy.copy(query)
					
					new_query.extend(new_triples)
					
					#debug('new_query',new_query)
					#debug('query',query)
					
					# print 'new_query',prettyquery(new_query)
											
					if matches == self.MAYBE :
						#print 'new_triples',prettyquery(new_triples)
						possible_steps.append({
							'query' : query,
							'input_bindings' : input_bindings,
							'output_bindings' : output_bindings,
							'translation' : translation,
							'new_triples' : new_triples,
							'new_query' : new_query,
							'guarenteed' : [],
							'possible' : [],
						})
					elif matches == True :
						guarenteed_steps.append({
							'input_bindings' : input_bindings,
							'output_bindings' : output_bindings,
							'translation' : translation,
							'new_triples' : new_triples,
							'new_query' : new_query,
							'guarenteed' : [],
							'possible' : [],
						})
		
		return guarenteed_steps, possible_steps
	
	def contains_all_bindings(self, required, obtained) :
		for key in required :
			if key not in obtained :
				return False
			elif not self.values_match(self.n.lit_var[key], obtained[key]) :
				return False
		return True
		
	def find_solution_values_match(self, tv, qv) :
		"""
		does the pattern (value) in tv match the value of qv?
		"""
		if is_any_var(tv) :
			if is_out_lit_var(tv) :
				# if the pattern is an out_lit_var, qv must be a lit_var or a literal
				if is_lit_var(qv) :
					return {tv : qv}
				elif is_any_var(qv) :
					return False
				else :
					return {tv : qv}
			elif is_out_var(tv) :
				# not sure if this is really right ...
				if is_any_var(qv) :
					if var_name(tv) == var_name(qv) :
						#print '! ! !',prettyquery(tv),prettyquery(qv)
						return {tv : qv}
				#print '? ? ?',prettyquery(tv),prettyquery(qv)
				return False
			elif is_out_lit_var(qv) :
				raise Exception("Does this really happen?")
				return False
			elif is_lit_var(tv) and is_lit_var(qv) :
				return True
			elif is_any_var(qv) :
				return var_name(tv) == var_name(qv)
			return False
		else :
			return tv == qv
	
	def find_solution_triples_match(self, triple, qtriple) :
		"""
		does the pattern in triple match the qtriple?
		"""
		bindings = {}
		for tv, qv in izip(triple, qtriple) :
			#p(tv, qv, self.find_solution_values_match(tv, qv))
			ret = self.find_solution_values_match(tv, qv)
			if not ret :
				return False
			elif isinstance(ret, dict) :
				bindings.update(ret)
		return bindings or True
	
	def find_solution_triple(self, triple, query) :
		"""
		does the pattern defined in triple have a match in query?
		"""
		for qtriple in query :
			bindings = self.find_solution_triples_match(triple, qtriple)
			#p(triple)
			#p(qtriple)
			#p(bindings)
			#p()
			if bindings :
				return bindings or True
		return False
		
	def find_solution(self, var_triples, query) :
		"""
		returns True if a solution for var_triples can be found in query
		@arg var_triples is the set of triples which need to be bound in query for
			a solution to exist
		@arg query is the query to find a solution satisfying var_triples in
		@returns True iff a solution exists
		"""
		bindings = {}
		for triple in var_triples :
			new_bindings = self.find_solution_triple(triple, query)
			if not new_bindings :
				return False
			#if isinstance(new_bindings, dict) :
				#bindings.update(new_bindings)
			bindings.update(new_bindings)
		return bindings or True
	
	@logger
	def follow_guarenteed(self, query, possible_stack, history, output_vars) :
		"""
		follow guarenteed translations and add possible translations to the 
			possible_stack
		@arg query is the query to start from
		@arg possible_stack is a list which is filled in with next next possible 
			translations to follow after the guarenteed translations have already been
			followed completely
		@arg output_vars is a set of variables which are not allowed to be bound as
			an input to a translation
		@return the compiled guarenteed path (see thoughts for more info on this 
			structure)
		"""
		#debug('fg query',query)
		#print 'history',prettyquery(history)
		
		compile_node = {
			'guarenteed' : [],
			'possible' : [],
		}
		compile_node_found_solution = False
		
		# recursively search through all possible guarenteed translations
		guarenteed_steps, possible_steps = self.next_translations(query, history, output_vars)
		#debug('len_guarenteed_steps',len(guarenteed_steps))
		#debug('guarenteed_steps',guarenteed_steps)
		#debug('possible_steps',possible_steps)
		for step in guarenteed_steps :
			debug('?match',step['translation'][n.meta.name])
			if [step['translation'], step['input_bindings']] not in history :
				debug('+match',step['translation'][n.meta.name])
				#print 'history',history
				# if there is only one next step, don't worry about copying the history
				if len(guarenteed_steps) > 1 :
					new_history = copy.copy(history)
				else :
					new_history = history
				new_history.append([step['translation'], copy.copy(step['input_bindings'])])
				#debug('step',step)
				#debug('step',step['translation'][self.n.meta.name])
				
				# if the new information at this point is enough to fulfil the query, done
				# otherwise, recursively continue searching
				#debug('var_triples',self.var_triples)
				#debug('step',step.keys())
				debug('step',step['translation'][self.n.meta.name])
				debug("step['new_query']",step['new_query'])
				found_solution = self.find_solution(self.var_triples, step['new_query'])
				debug('found_solution',found_solution)
				if found_solution :
					step['solution'] = found_solution
					#debug('solution', step['solution'])
				else :
					child_steps = self.follow_guarenteed(step['new_query'], possible_stack, new_history, output_vars)
					if child_steps :
						found_solution = True
						step['guarenteed'].extend(child_steps['guarenteed'])
						step['possible'].extend(child_steps['possible'])
				
				if found_solution :
					compile_node['guarenteed'].append(step)
					compile_node_found_solution = True
		
		# don't follow the possible translations yet, just add then to a stack to
		# follow once all guarenteed translations have been found
		for step in possible_steps:
			possible_stack.append({
				'root' : compile_node,
				'step' : step,
				'query' : query,
			})
		
		if compile_node_found_solution == False :
			return False
		else :
			return compile_node
	
	def follow_possible(self, query, possible_stack) :
		"""
		
		"""
		#for translation in possible_stack :
			#compile_node = 
			## next_query, input_bindings, output_bindings
			#translation_step = self.follow_translation(query, translation)
			#compile_node['guarenteed'].append(translation_step)
		
		
	def make_vars_out_vars(self, query, reqd_bound_vars) :
		"""
		replaces all instances of variables in query whose name is in the 
		reqd_bound_vars list with self.n.out_lit_var variables of the same name
		@arg query is a query to change
		@arg reqd_bound_vars are variable to change
		"""
		for triple in query :
			for j, value in enumerate(triple) :
				if is_lit_var(value) and var_name(value) in reqd_bound_vars :
					triple[j] = self.n.out_lit_var[var_name(value)]
				elif is_any_var(value) and var_name(value) in reqd_bound_vars :
					triple[j] = self.n.out_var[var_name(value)]
	
	def extract_query_modifiers(self, query) :
		modifiers = {}
		new_query = []
		for triple in query :
			modified = False
			if triple[0] == self.n.query.query :
				if triple[1] == self.n.query.limit :
					modifiers.update({'limit' : int(triple[2])})
					modified = True
			
			if not modified :
				new_query.append(triple)
		new_query
		
		return new_query, modifiers
	
	def compile(self, query, reqd_bound_vars = [], input = [], output = []) :
		if isinstance(query, basestring) :
			query = [line.strip() for line in query.split('\n')]
			query = [line for line in query if line is not ""]
		query = self.parser.parse(query)
		
		query, modifiers = self.extract_query_modifiers(query)
		
		if len(reqd_bound_vars) == 0 :
			#var_triples = self.find_var_triples(query, is_lit_var)
			reqd_bound_vars = find_vars(query, is_lit_var)
			print 'new reqd_bound_vars',reqd_bound_vars
		
		self.make_vars_out_vars(query, reqd_bound_vars)
		
		debug('query',query)
		
		var_triples = self.find_specific_var_triples(query, reqd_bound_vars)
		if var_triples == [] :
			raise Exception("Waring, required bound triples were provided, but not found in the query")
		
		# replace all reqd_bound_vars with out vars ... I think this is already done
		# above.  I'm going to leave it incase there is some other thing going on
		debug('var_triples',var_triples)
		#bindings = dict([(var, self.n.out_lit_var[var]) for var in reqd_bound_vars])
		#debug('bindings',bindings)
		#var_triples = [x for x in sub_var_bindings(var_triples, [bindings])][0]
		#debug('var_triples',var_triples)
		
		#debug('query',query)
		#debug('var_triples',var_triples)
		
		self.original_query = query
		self.var_triples = var_triples
		# print 'var_triples',prettyquery(var_triples)
		self.vars = reqd_bound_vars
		self.vars = [var for var in self.vars if var.find('bnode') is not 0]
		#debug('self.vars',self.vars)
		
		possible_stack = []
		history = []
		
		compile_root_node = self.follow_guarenteed(query, possible_stack, history, reqd_bound_vars)
		
		p('compile_root_node',compile_root_node)
		#@logger
		def print_compiled(node, l = []) :
			for step in node['guarenteed'] :
				#p('\\',step['translation'][n.meta.name])
				instruction = [
					step['translation'][n.meta.name], {
						'input_bindings' : step['input_bindings'],
						'output_bindings' : step['output_bindings'],
					}
				]
				print_compiled(step, l + [instruction])
				#p('/',step['translation'][n.meta.name])
			if not node['guarenteed'] :
				p(l+[node['solution']])
		print_compiled(compile_root_node)
		
		
		# prune any paths which are not necessary:
		def mark_unnecessary_translations_helper(node) :
			"""
			returns variables which need to be bound for the children (next) 
			translations to be able to work.  If a translation doesn't provide any of
			those variables as output, than it is unecessary.
			correlary: if a translation provides an output binding that is never used
			remove it.
			"""
			if 'solution' in node :
				required_variables = set(node['solution'].values())
			else :
				required_variables = set()
			
			for step in node['guarenteed'] :
				required_variables.update(mark_unnecessary_translations_helper(step))
			
			for var, binding in node['output_bindings'].items() :
				if binding not in required_variables :
					del node['output_bindings'][var]
			
			if node['output_bindings'] :
				node['input_bindings'] = dict([(var, binding) for (var, binding) in node['input_bindings'].iteritems() if not is_var(binding)])
				required_variables.update(node['input_bindings'].values())
			
			return required_variables
		
		for node in compile_root_node['guarenteed'] :
			p('---')
			mark_unnecessary_translations_helper(node)
			
		p('///')
		print_compiled(compile_root_node)
		
		def remove_unnecessary_translations(node) :
			"""
			returns a list to replace
			"""
			node['guarenteed'] = [step for step in node['guarenteed'] if step['output_bindings']]
			for step in node['guarenteed'] :
				remove_unnecessary_translations(step)
			
		remove_unnecessary_translations(compile_root_node)
		
		print_compiled(compile_root_node)
		
		#p(compile_root_node['guarenteed'][0]['translation'][n.meta.name])
		
		# TODO: make this work
		# self.follow_possible(query, possible_stack)
		
		if compile_root_node :
			compile_root_node['modifiers'] = modifiers
		
		#debug('modifiers',modifiers)
			
		return compile_root_node
















