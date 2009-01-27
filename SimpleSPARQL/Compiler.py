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
	
	def values_match(self, value, qvalue) :
		# TODO: keep track of values of meta-vars to make sure they are consistant
		# throughout.  This will actually require a backtracking search ...
		# is this really not taken care of?
		if type(value) == URIRef :
			if value.find(self.n.var) == 0 :
				return True
				#return not is_meta_var(qvalue)
			if is_meta_var(value) :
				if type(qvalue) == URIRef :
					# return qvalue.find(self.n.var) == 0
					return is_var(qvalue) and not is_lit_var(qvalue)
					# return is_var(qvalue) and not is_meta_var(qvalue)
				else :
					return False
			if is_lit_var(value) :
				if type(qvalue) == URIRef :
					# return qvalue.find(self.n.var) != 0
					return is_lit_var(qvalue) or not is_var(qvalue)
					# return qvalue.find(self.n.var) != 0 and qvalue.find(self.n.lit_var) != 0
				else :
					return True
			if is_out_var(value) :
				if is_lit_var(qvalue) :
					return True
				elif is_var(qvalue) :
					return False
				else :
					return True
		if value == qvalue :
			return True
	
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
			if is_var(t) and self.values_match(t, q):
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
		for k, v in a.iteritems() :
			if k in b and b[k] != v :
				if self.values_match(b[k], v) or self.values_match(v, b[k]):
					return self.MAYBE
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
		#print 'translation',prettyquery(translation)
		#print 'q',prettyquery(query)
		bindings = [Bindings()]
		for ttriple in translation :
			possible_bindings = self.find_bindings_for_triple(ttriple, query)
			new_bindings = []
			# see if any of the next_bindings fit with the existing bindings
			for pbinding in possible_bindings :
				# if there are no values in bindings that already have some other 
				# value in bindings 
				for binding in bindings :
					conflicting = self.conflicting_bindings(binding, pbinding)
					if not conflicting :
						# WARNING: this isn't going to copy the values of the bindings!!!
						new_binding = copy.copy(binding)
						#print prettyquery(new_binding)
						#print prettyquery(pbinding)
						#print
						new_binding.update(pbinding)
						if new_binding not in new_bindings :
							new_bindings.append(new_binding)
					elif conflicting == self.MAYBE :
						# WARNING: this isn't going to copy the values of the bindings!!!
						new_binding = Bindings(binding, possible = True)
						#print prettyquery(new_binding)
						#print prettyquery(pbinding)
						#print
						new_binding.update(pbinding)
						if new_binding not in new_bindings :
							new_bindings.append(new_binding)
						print 'maybe ... this will work'
						matches = self.MAYBE
			if len(new_bindings) > 0 :
				bindings = new_bindings
		
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
				print 'no match for',prettyquery(triple)
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
		#print translation[self.n.meta.name]
		return self.find_bindings(query, translation[self.n.meta.input], output_vars)
	
	def next_bnode(self) :
		return self.n.bnode[str(time.time()).replace('.','') + '_' +  str(random.random()).replace('.','')]
	
	def find_paths(self, query, find_vars) :
		for possible_translation in possible_translations :
			something = find_paths(possible_translation, find_vars)
	
	# return all triples which have at least one var
	def find_var_triples(self, query) :
		return [triple for triple in query if any(map(lambda x:is_var(x), triple))]
	
	# return all triples which have at least one var
	def find_specific_var_triples(self, query, vars) :
		return [triple for triple in query if any(map(lambda x:is_var(x) and var_name(x) in vars, triple))]


	def next_num(self) :
		self._next_num += 1
		return self._next_num


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
		
		def bindings_contain_output_var(bindings) :
			# check to see if any of the bindings are with output_variables which
			# don't actually have a value yet
			for var, value in bindings.iteritems() :
				if is_var(value) and var_name(value) in output_vars :
					return True
			return False
		
		for translation in self.translations :
			matches, bindings_set = self.testtranslation(translation, query, output_vars)
			if matches :
				for bindings in bindings_set :
					# not allowed to bind an output variable as a value to the input of a
					# translation
					if bindings_contain_output_var(bindings) :
						continue
					
					if [translation, bindings] not in history :
						print translation[n.meta.name],'matches!!!'
						#print 'history',history
						history.append([translation, copy.copy(bindings)])
						#print '---'
						#print 'bindings',prettyquery(bindings)
						#print 'translation',prettyquery(translation)
						# keep the possible property
						new_bindings = Bindings(possible = bindings.possible)
						# replace the bindings which the translation defines as constant with
						# the exact binding value
						# replace the other bindings which are variables, with variables with
						# the name from the query and the type from the translation ...
						# TODO?: keep the state of each of the variables in the triple set
						# rather than as the namespace so it can be changed and checked 
						# easily.  Also, it should be consistant throughout the query anyway
						new_lit_vars = {}
						for var, value in bindings.iteritems() :
							if var in translation[n.meta.constant_vars] :
								new_bindings[var] = value
							elif is_var(value) :
								new_var = n.lit_var[var_name(value)+'_'+str(self.next_num())]
								new_lit_vars[var_name(value)] = new_var
								new_bindings[var] = new_var
								#new_lit_vars[var_name(value)] = n.lit_var[var_name(value)]
								#new_bindings[var] = n.lit_var[var_name(value)]
						
						input_bindings = bindings
						output_bindings = {}
						
						for var in find_vars(translation[n.meta.output]) :
							if var not in translation[n.meta.constant_vars] :
								output_bindings[var] = n.lit_var[var+'_out_'+str(self.next_num())]
							else :
								output_bindings[var] = input_bindings[var]
						
						print 'input_bindings',prettyquery(input_bindings)
						print 'output_bindings',prettyquery(output_bindings)
						#print 'new_bindings',prettyquery(new_bindings)
						#print 'new_lit_vars',prettyquery(new_lit_vars)
						
						new_triples = sub_var_bindings(translation[n.meta.output], [output_bindings]).next()
						new_query = copy.copy(query)
						#new_triples = sub_var_bindings(translation[n.meta.output], [new_bindings]).next()
						#new_query = sub_var_bindings(query, [new_lit_vars]).next()
						
						new_query.extend(new_triples)
						
						print 'new_query',prettyquery(new_query)
						print 'query',prettyquery(query)
						
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
							#print 'new_triples',prettyquery(new_triples)
							#print 'guarenteed_steps.append(',prettyquery({
								#'input_bindings' : input_bindings,
								#'output_bindings' : output_bindings,
								#'translation' : translation,
								#'new_triples' : new_triples,
								#'new_query' : new_query
								#'guarenteed' : [],
								#'possible' : [],
							#}),')'
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
		if is_var(tv) :
			if is_out_var(tv) :
				if is_lit_var(qv) :
					return {tv : qv}
				elif is_var(qv) :
					return False
				else :
					return {tv : qv}
			if is_out_var(qv) :
				return False
			elif is_lit_var(tv) and is_lit_var(qv) :
				return True
			elif is_var(qv) :
				return var_name(tv) == var_name(qv)
			return False
		else :
			return tv == qv
	
	def find_solution_triples_match(self, triple, qtriple) :
		bindings = {}
		for tv, qv in izip(triple, qtriple) :
			# print prettyquery(tv), prettyquery(qv), self.find_solution_values_match(tv, qv)
			ret = self.find_solution_values_match(tv, qv)
			if not ret :
				return False
			elif isinstance(ret, dict) :
				bindings.update(ret)
		return bindings or True
	
	def find_solution_triple(self, triple, query) :
		for qtriple in query :
			bindings = self.find_solution_triples_match(triple, qtriple)
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
			bindings.update(new_bindings)
		return bindings or True
	
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
		print 'follow_guarenteed'
		print 'query',prettyquery(query)
		#print 'history',prettyquery(history)
		
		compile_node = {
			'guarenteed' : [],
			'possible' : [],
		}
		compile_node_found_solution = False
		
		# recursively search through all possible guarenteed translations
		guarenteed_steps, possible_steps = self.next_translations(query, history, output_vars)
		print 'g p', len(guarenteed_steps), len(possible_steps)
		for step in guarenteed_steps :
			print 'step',prettyquery(step)
			
			# if the new information at this point is enough to fulfil the query, done
			# otherwise, recursively continue searching
			found_solution = False
			print 'var_triples',prettyquery(self.var_triples)
			found_solution = self.find_solution(self.var_triples, step['new_query'])
			print 'matches/found_solution',found_solution
			#print 'original_query',prettyquery(self.original_query)
			#matches, bindings = self.find_bindings(step['new_query'], self.original_query)
			#print 'matches',matches
			#print 'bindings',prettyquery(bindings)
			#if bindings is not None :
				#for binding in bindings :
					##print '... testing ...'
					##print 'self.vars',prettyquery(self.vars)
					##print 'binding',prettyquery(binding)
					#if self.contains_all_bindings(self.vars, binding) :
						#print '-------------------------------------------------'
						#print 'found solution:',prettyquery(binding)
						#found_solution = True
			if found_solution :
				step['solution'] = found_solution
			else :
				print 'recuring'
				child_steps = self.follow_guarenteed(step['new_query'], possible_stack, history, output_vars)
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
		reqd_bound_vars list with self.n.out_var variables of the same name
		@arg query is a query to change
		@arg reqd_bound_vars are variable to change
		"""
		for triple in query :
			for j, value in enumerate(triple) :
				if is_var(value) and var_name(value) in reqd_bound_vars :
					triple[j] = self.n.out_var[var_name(value)]
	
	def compile(self, query, reqd_bound_vars = [], input = [], output = []) :
		if isinstance(query, basestring) :
			query = [line.strip() for line in query.split('\n')]
			query = [line for line in query if line is not ""]
		query = self.parser.parse(query)
		
		self.make_vars_out_vars(query, reqd_bound_vars)
		
		if reqd_bound_vars == [] :
			var_triples = self.find_var_triples(query)
		else :
			var_triples = self.find_specific_var_triples(query, reqd_bound_vars)
			if var_triples == [] :
				raise Exception("Waring, required bound triples were provided, but not found in the query")
		
		print 'var_triples',prettyquery(var_triples)
		bindings = dict([(var, self.n.out_var[var]) for var in reqd_bound_vars])
		print 'bindings',prettyquery(bindings)
		var_triples = [x for x in sub_var_bindings(var_triples, [bindings])][0]
		
		print 'query',prettyquery(query)
		print 'var_triples',prettyquery(var_triples)
		
		# self.original_query = var_triples
		self.original_query = query
		self.var_triples = var_triples
		# print 'var_triples',prettyquery(var_triples)
		# self.vars = find_vars(query)
		self.vars = reqd_bound_vars
		self.vars = [var for var in self.vars if var.find('bnode') is not 0]
		print 'self.vars',prettyquery(self.vars)
		
		possible_stack = []
		history = []
		
		compile_root_node = self.follow_guarenteed(query, possible_stack, history, reqd_bound_vars)
		
		# TODO: make this work
		# self.follow_possible(query, possible_stack)
			
		return compile_root_node
















