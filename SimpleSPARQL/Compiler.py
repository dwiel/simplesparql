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
		#self.n.bind('var', '<http://dwiel.net/axpress/var/0.1/>')
		#self.n.bind('tvar', '<http://dwiel.net/axpress/translation/var/0.1/>')
		#self.n.bind('bnode', '<http://dwiel.net/axpress/bnode/0.1/>')
		#self.n.bind('meta', '<http://dwiel.net/axpress/meta/0.1/>')
		
		self.parser = Parser(self.n)

		self.translations = []
		#self.sparql = sparql
	
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
					return is_var(qvalue)
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
		# return [x for x in [get_binding(triple, qtriple) for qtriple in query] if x]
		bindings = []
		for qtriple in query :
			binding = self.get_binding(triple, qtriple)
			if binding and binding not in bindings :
				bindings.append(binding)
		
#		bindings = [binding for binding in bindings if binding]
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
		@arg bindings is a list of possible bindings (dict) thus far
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
	
	def find_bindings(self, data, pattern) :
		"""
		@arg pattern is the pattern whose variables are attempting to be matched
		@arg data is the set of triples whose values are attempting to matched to
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
	
	def testtranslation(self, translation, query) :
		"""
		@returns matches, bindings
			matches is True iff the translation is guarenteed to match the query.  It 
				is self.MAYBE if the translation might match the query and False if it
				is guarenteed to not match the query.
			bindings is the set of bindings which allow this translation to match the
				query
		"""
		return self.find_bindings(query, translation[self.n.meta.input])
	
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

	def apply_translation_binding(self, translation, bindings, history) :
		"""
		apply a translation to a set of bindings if it hasn't already been applied
		before.
		@return a set of triplelists which are to be added to the query for
		the next iteration of search.
		"""
		n = self.n
		translation_bindings = []
		for binding in bindings :
			# print 'history',prettyquery([[t[0][n.meta.name], t[1]] for t in history]),
			# print 'now',prettyquery([translation[n.meta.name], binding]),
			if [translation, binding] not in history :
				#print 'applying',translation[n.meta.name]
				#print 'binding',prettyquery(binding)
				history.append([translation, copy.copy(binding)])
				
				# instead of calling the function, just replace all of the bindings with
				# new output vars
				# or maybe, rather than that, only replace the output bindings which are
				# constant with whatever they were bound to. OK
				
				# the only bindings to replace 
				print 'binding',prettyquery(binding)
				print 'constants',prettyquery(translation[n.meta.constant_vars])
				output_bindings = Bindings(possible = binding.possible)
				for var, value in binding.iteritems() :
					if var in translation[n.meta.constant_vars] :
						output_bindings[var] = value
				print 'output_bindings',prettyquery(output_bindings)
				
				output_bindings_list = [output_bindings]
				
				outtriple_sets = sub_var_bindings(translation[n.meta.output], output_bindings_list)
				
				#outtriple_sets = [x for x in outtriple_sets]
				#print 'outtriple_sets',prettyquery(outtriple_sets)
				translation_bindings.extend(outtriple_sets)
		print 'translation_bindings',prettyquery(translation_bindings)
		return translation_bindings
	
	def read_translations_helper(self, query, var_triples, bound_var_triples = [], history = []) :
		n = self.n		
		
		# updated once at the end of each iteration.  This will have more than one
		# set of bindings if one translation has multiple possible bindings or if
		# a translation binds a variable to a list (not a tuple) of values
		final_bindings = [query]
		
		translation_list = []
		
		found_match = True
		while found_match :
#			print '--- new iteration ---'
			all_new_final_bindings = []
			for query in final_bindings :
				new_final_bindings = [query]
				all_bindings  = [(translation, self.testtranslation(translation, query)) for translation in self.translations]
				found_match = False
				for (translation, (matches, bindings)) in all_bindings :
					if matches :
						this_translation_bindings = self.apply_translation_binding(translation, bindings, history)
#						print 'translation', translation[n.meta.name]
#						print 'this_translation_bindings', prettyquery(this_translation_bindings),
						# 'multiply' each new binding with each previously existing binding
						if len(this_translation_bindings) != 0 :
							#print translation[n.meta.name], len(this_translation_bindings), prettyquery(this_translation_bindings),
							found_match = True
							
							print 'bindings', translation[n.meta.name], prettyquery(this_translation_bindings)
							translation_list.append([translation[n.meta.name], this_translation_bindings])
							
							tmp_new_final_bindings = []
							for binding in new_final_bindings :
								for new_binding in this_translation_bindings :
									tmp_new_final_bindings.append(binding + new_binding)
							new_final_bindings = tmp_new_final_bindings
							#print 'new_final_bindings',prettyquery(new_final_bindings)
							
				all_new_final_bindings.extend(new_final_bindings)
			
			final_bindings = all_new_final_bindings
			#print 'final_bindings', prettyquery(final_bindings)
		
		# print 'final_bindings',prettyquery(final_bindings),
		return [final_bindings, translation_list]
		#exit()
	
	def compile(self, query, find_vars = [], input = [], output = []) :
		if find_vars == [] :
			var_triples = self.find_var_triples(query)
		else :
			var_triples = self.find_specific_var_triples(query, find_vars)
		
		query = self.parser.parse_query(query)
		
		#print '----------------------------------------------'
		#print 'parsed query'
		#print prettyquery(query)
		#print '/'
		#print
		
		return self.read_translations_helper(query, var_triples, [], [])




	# new code





	def next_translations(self, query, history) :
		"""
		@returns the set of next guarenteed_steps and possible_steps.
			Ensures that this set of translation and bindings haven't already been 
			searched.....
		"""
		n = self.n
		
		guarenteed_steps = []
		possible_steps = []
		
		for translation in self.translations :
			matches, bindings_set = self.testtranslation(translation, query)
			if matches :
				print translation[n.meta.name],'matches!!!'
				for bindings in bindings_set :
					if [translation, bindings] not in history :
						history.append([translation, copy.copy(bindings)])
						#print '---'
						#print 'bindings',prettyquery(bindings)
						#print 'translation',prettyquery(translation)
						# keep the possible property
						const_bindings = Bindings(possible = bindings.possible)
						# replace only bindings which the translation defines as constant
						for var, value in bindings.iteritems() :
							if var in translation[n.meta.constant_vars] :
								const_bindings[var] = value
						
						#print 'const_bindings',prettyquery(const_bindings)
						triple_sets = sub_var_bindings(translation[n.meta.output], [const_bindings])
												
						if matches == self.MAYBE :
							for new_triples in triple_sets :
								#print 'new_triples',prettyquery(new_triples)
								
								possible_steps.append({
									'query' : query,
									'bindings' : bindings,
									'translation' : translation[n.meta.name],
									'new_triples' : new_triples,
									'guarenteed' : [],
									'possible' : [],
								})
						elif matches == True :
							for new_triples in triple_sets :
								#print 'new_triples',prettyquery(new_triples)
								
								guarenteed_steps.append({
									'bindings' : bindings,
									'translation' : translation[n.meta.name],
									'new_triples' : new_triples,
									'guarenteed' : [],
									'possible' : [],
								})
		
		return guarenteed_steps, possible_steps
	
	def follow_step(self, query, step) :
		"""
		@returns a compile_step, which is all of the information required to easily
		follow this step in the path later without doing any pattern matching
		"""
		n = self.n
		
		print 'query', prettyquery(query)
		print 'step', prettyquery(step)
		
		bindings = step['bindings']
		translation = step['translation']
		#print 'bindings',prettyquery(bindings)
		#print 'constants',prettyquery(translation[n.meta.constant_vars])
		#print 'output_bindings',prettyquery(output_bindings)
		
		translation_step = {
			'next_query' : {},
			'input_bindings' : {},
			'output_bindings' : {},
		}
		
		return translation_step
	
	def contains_all_bindings(self, required, obtained) :
		for key in required :
			if key not in obtained :
				print '1not',key
				return False
			elif not self.values_match(self.n.lit_var[key], obtained[key]) :
				print '3not',key
				return False
		return True
	
	def follow_guarenteed(self, query, possible_stack, history) :
		"""
		follow guarenteed translations and add possible translations to the 
			possible_stack
		@arg query is the query to start from
		@arg possible_stack is a list which is filled in with next next possible 
			translations to follow after the guarenteed translations have already been
			followed completely
		@return the compiled guarenteed path (see thoughts for more info on this 
			structure)
		"""
		print 'follow_guarenteed',prettyquery(query)
		print 'history',prettyquery(history)
		
		compile_node = {
			'guarenteed' : [],
			'possible' : [],
		}
		compile_node_found_solution = False
		
		# recursively search through all possible guarenteed translations
		guarenteed_steps, possible_steps = self.next_translations(query, history)
		print len(guarenteed_steps), len(possible_steps)
		for step in guarenteed_steps :
			print 'step',prettyquery(step)
			
			new_query = copy.copy(query)
			new_query.extend(step['new_triples'])
			
			print 'new_query',prettyquery(new_query)
			
			# if the new information at this point is enough to fulfil the query, done
			# otherwise, recursively continue searching
			found_solution = False
			print 'original_query',prettyquery(self.original_query)
			matches, bindings = self.find_bindings(new_query, self.original_query)
			print 'matches',matches
			print 'bindings',prettyquery(bindings)
			if bindings is not None :
				for binding in bindings :
					#print '... testing ...'
					#print 'self.vars',prettyquery(self.vars)
					#print 'binding',prettyquery(binding)
					if self.contains_all_bindings(self.vars, binding) :
						print '-------------------------------------------------'
						print 'found solution:',prettyquery(binding)
						found_solution = True
			if not found_solution :
				child_steps = self.follow_guarenteed(new_query, possible_stack, history)
				if child_steps :
					found_solution = True
					step['guarenteed'].append(child_steps)
			
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
		
		
	
	def new_compile(self, query, reqd_bound_vars = [], input = [], output = []) :
		if isinstance(query, basestring) :
			query = [line.strip() for line in query.split('\n')]
			query = [line for line in query if line is not ""]
		query = self.parser.parse(query)
		
		if reqd_bound_vars == [] :
			var_triples = self.find_var_triples(query)
		else :
			var_triples = self.find_specific_var_triples(query, reqd_bound_vars)
		
		print 'var_triples',prettyquery(var_triples)
		bindings = dict([(var, self.n.lit_var[var]) for var in reqd_bound_vars])
		print 'bindings',prettyquery(bindings)
		var_triples = [x for x in sub_var_bindings(var_triples, [bindings])][0]
		
		print 'query',prettyquery(query)
		print 'var_triples',prettyquery(var_triples)
		
		self.original_query = var_triples
		# print 'var_triples',prettyquery(var_triples)
		# self.vars = find_vars(query)
		self.vars = reqd_bound_vars
		self.vars = [var for var in self.vars if var.find('bnode') is not 0]
		print 'self.vars',prettyquery(self.vars)
		
		possible_stack = []
		history = []
		
		compile_root_node = self.follow_guarenteed(query, possible_stack, history)
		
		# TODO: make this work
		# self.follow_possible(query, possible_stack)
			
		return compile_root_node
















