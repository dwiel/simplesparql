from SimpleSPARQL import SimpleSPARQL, Namespaces, prettyquery

from rdflib import URIRef

from itertools import izip
import copy, time, random

class Translator :
	def __init__(self, cache) :
		self.n = Namespaces.Namespaces()
		#self.n.bind('var', '<http://dwiel.net/axpress/var/0.1/>')
		#self.n.bind('tvar', '<http://dwiel.net/axpress/translation/var/0.1/>')
		#self.n.bind('bnode', '<http://dwiel.net/axpress/bnode/0.1/>')
		#self.n.bind('meta', '<http://dwiel.net/axpress/meta/0.1/>')
		
		self.cache = cache

		self.translations = []
		#self.sparql = sparql

	def register_translation(self, translation) :
		self.translations.append(translation)
		
	def is_meta_var(self, data) :
		if type(data) == URIRef :
			if data.find(self.n.var) == 0 :
				return True
		return False
	
	def is_var(self, data) :
		if type(data) == URIRef :
			if data.find(self.n.var) == 0 :
				return True
		return False
	
	def meta_var(self, data) :
		if is_meta_var(data) :
			return data[len(self.n.var):]
		return None
	
	def var(self, data) :
		if is_var(data) :
			return data[len(self.n.var):]
		return None
	
	def values_match(self, value, qvalue) :
		# if this is a meta-var, then anything matches
		# TODO: keep track of values of meta-vars to make sure they are consistant
		# throughout.  This will actually require a backtracking search ...
		if type(value) == URIRef :
			if value.find(self.n.var) == 0 :
				return True
			# if this meta value is a variable, see what it is
			if value.find(self.n.var) == 0 :
				if value in self.vars :
					# TODO deal with this some other way
					raise Exception('this var is bound twice ...' + value + ' : '+str(qvalue))
				self.vars[value] = qvalue
				return True
		if value == qvalue :
			return True
	
	def triples_match(self, triple, qtriple) :
		for tv, qv in izip(triple, qtriple) :
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
			if self.is_meta_var(t) :
				# if the same meta_var is trying to be bound to two different values, 
				# not a valid binding
				if t in binding and binding[t] != q :
					return {}
				binding[t] = q
			elif t != q :
				return {}
		return binding
	
	def find_bindings(self, triple, query) :
		# return [x for x in [get_binding(triple, qtriple) for qtriple in query] if x]
		bindings = []
		for qtriple in query :
			binding = self.get_binding(triple, qtriple)
			if binding not in bindings :
				bindings.append(binding)
		return bindings
	
	def conflicting_bindings(self, a, b) :
		"""
		a and b are dictionaries.  Returns True if there are keys which are in 
		both a and b, but have different values
		"""
		for k, v in a.iteritems() :
			if k in b and b[k] != v :
				return True
		return False
	
	def has_already_executed(self, history, translation, binding) :
		return [translation, binding] in history
	
	def register_executed(self, history, translation, binding) :
		history.append(copy.deepcopy([translation, binding]))
		
	def find_meta_vars(self, query) :
		try :
			iter = query.__iter__()
		except AttributeError :
			if type(query) == URIRef :
				if query.find(self.n.var) == 0 :
					return set([query[len(self.n.var):]])
			return set()
		
		vars = set()
		for i in iter :
			vars.update(self.find_meta_vars(i))
		return vars

	def bind_meta_vars(self, translation, query, bindings = []) :
		"""
		input:
			translation : a list of triples (the translation)
			query : a list of triples (the query)
			bindings : a list of possible bindings (dict) thus far
		returns matches, bindings
		matches is True if the query matches the translation
		bindings is a list of bindings for meta_var to value
		"""
		bindings = [{}]
		for ttriple in translation :
			#print 'q',prettyquery(query)
			#print 't',prettyquery(ttriple)
			possible_bindings = self.find_bindings(ttriple, query)
			#print 'p',prettyquery(possible_bindings)
			#print
			new_bindings = []
			# see if any of the next_bindings fit with the existing bindings
			for pbinding in possible_bindings :
				# if there are no values in bindings that already have some other 
				# value in bindings 
				for binding in bindings :
					if not self.conflicting_bindings(binding, pbinding) :
						new_binding = copy.deepcopy(binding)
						#print prettyquery(new_binding)
						#print prettyquery(pbinding)
						#print
						new_binding.update(pbinding)
						if new_binding not in new_bindings :
							new_bindings.append(new_binding)
			bindings = new_bindings
		
		# get a set of all meta_vars
		meta_vars = self.find_meta_vars(translation)
		
		# if there are no meta_vars, this does still match, but there are no bindings
		if len(meta_vars) == 0 :
			return True, []
		
		# keep only the bindings which contain bindings for all of the meta_vars
		bindings = [binding for binding in bindings if len(binding) == len(meta_vars)]
		
		# if there are no bindings (and there are meta_vars), failed to find a match
		if len(bindings) == 0 :
			return False, []
		
		return True, bindings
	
	def testtranslation(self, translation, query) :
		# check that all of the translation inputs match part of the query
		for triple in translation[self.n.meta.input] :
			if not self.find_triple_match(triple, query) :
				return False, None
		
		# find all possible bindings for the meta_vars if any exist
		matches, bindings = self.bind_meta_vars(translation[self.n.meta.input], query)
		
		#print '===>', matches, len(bindings), prettyquery(bindings)
		
		return matches, bindings
	
	def sub_bindings_value(self, value, bindings) :
		if value in bindings :
			return bindings[value]
		return value
	
	def next_bnode(self) :
		return self.n.bnode[str(time.time()).replace('.','') + '_' +  str(random.random()).replace('.','')]
	
	def explode_triple(self, triple) :
		# convert each value to a list of values unless it is already a list
		triple = [type(value) == list and value or [value] for value in triple]
		
		triples = [[i] for i in triple[0]]
		
		new_triples = []
		
		for t in triples :
			for i in triple[1] :
				new_triples.append(t + [i])
		
		triples = new_triples
		new_triples = []
		for t in triples :
			for i in triple[2] :
				new_triples.append(t + [i])
		
		# TODO: only one layer of bnodes for now ...
		# TODO: should these bnodes or vars?
		for t in range(len(new_triples)) :
			for vi in range(3) :
				if type(new_triples[t][vi]) == dict :
					d = new_triples[t][vi]
					b = self.next_bnode()
					new_triples[t][vi] = b
					for k, v in d.iteritems() :
						new_triples.append([b, k, v])
		
		return new_triples
	
	def sub_bindings_triple(self, triple, bindings) :
		triple = [self.sub_bindings_value(value, bindings) for value in triple]
		return self.explode_triple(triple)
	
	def sub_var_bindings(self, output, output_bindings) :
		for bindings in output_bindings :
			for triple in output :
				yield [bound_triple for bound_triple in self.sub_bindings_triple(triple, bindings)]
		
	# the implementation of this depends on the search method.  Start from the end
	# or from the begining?
	# for now, just start from the begining.  Evaluate all functions as they come
	# rather than defering it.
#	def eval_translations(self, query, history = []) :
	
	def find_paths(self, query, find_vars) :
		for possible_translation in possible_translations :
			something = find_paths(possible_translation, find_vars)
	
	# return all triples which have at least one var
	def find_var_triples(self, query) :
		return [triple for triple in query if any(map(lambda x:self.is_var(x), triple))]
	
	# return all triples which have at least one var
	def find_specific_var_triples(self, query, vars) :
		return [triple for triple in query if any(map(lambda x:x in vars, triple))]
	
	def read_translations_helper(self, query, var_triples, bound_var_triples = [], history = []) :
		n = self.n
		# try a bredth first search:
		nexts = []
		for translation in self.translations :
			self.vars = {}
			matches, bindings = self.testtranslation(translation, query)
			if matches :
				for binding in bindings :
					if not self.has_already_executed(history, translation, binding) :
						new_history = copy.deepcopy(history)
						self.register_executed(new_history, translation, binding)
						self.vars = binding
						
						# if this translation expects to be cached, use a cache
						if n.cache.expiration_length in translation :
							output_bindings = self.cache.call(translation, self.vars)
						else : 
							output_bindings = translation[n.meta.function](self.vars)
						
						if output_bindings == None :
							output_bindings = self.vars
						if type(output_bindings) == dict :
							output_bindingss = [output_bindings]
						
						print 'translation[n.meta.output]', prettyquery(translation[n.meta.output]),
						print 'output_bindingss', prettyquery(output_bindingss),
						output = self.sub_var_bindings(translation[n.meta.output], output_bindingss)
						output = [x for x in output]
						output = output[0] # if there are multiple sets of bindings for a given just use the first one for now
						print 'output',prettyquery(output),
						output = self.sub_var_bindings(output, [self.vars])
						print 'name',translation[n.meta.name]
						
						outtriple_sets = output
						
						for outtriple_set in outtriple_sets :
							new_var_triples = [var_triple for var_triple in var_triples if not self.find_triple_match(var_triple, outtriple_set)]
							
							new_bound_var_triples = copy.deepcopy(bound_var_triples)
							new_bound_var_triples.extend(outtriple_set)
							
							if len(new_var_triples) == 0 :
								yield new_bound_var_triples
							else :
								new_query = copy.deepcopy(query)
								new_query.extend(outtriple_set)
								nexts.append(self.read_translations_helper(new_query, new_var_triples, new_bound_var_triples, new_history))
		
		for next in nexts :
			for result in next :
				yield result
	
	def read_translations(self, query, find_vars = []) :
		if find_vars == [] :
			var_triples = self.find_var_triples(query)
		else :
			var_triples = self.find_specific_var_triples(query, find_vars)
		
		return self.read_translations_helper(query, var_triples, [], [])
		
		# look for all possible routes through the translations to see which paths
		#   might provide an output
		#		* how to deal with cycles?
		#		* how to deal with translations which result in nearly anything (aka possible paths explode to be every possible translation permuted infinite times)
		# paths = self.find_paths(query, find_vars)
		# evaluate those
		# 
		# evaluate all possible routes
		# 
		# look for all possible bindings of these vars
		# iterate through every possible translation of this query
		#   if this translation matches the output
		#			add the bindings to the bindings
		
		#return bindings
		return []
		
