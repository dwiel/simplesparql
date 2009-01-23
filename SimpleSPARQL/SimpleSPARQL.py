"""
SimpleSPARQL provides some high level access to some basic SPARQL queries
TODO: depricate RDFObject and everything associated with it
TODO: connect queries - so we need them?
TODO: make translation into SPARQL standards compliant or warn that it isn't(insert n3 is implementation-specific)
"""

import time, re, copy, datetime, random
from SPARQLWrapper import *
from rdflib import *
from urllib import urlopen, urlencode
from pprint import pprint
from itertools import izip
import pdb

import rdflib.sparql.parser

import Namespaces
from RDFObject import RDFObject
from QueryException import QueryException
from PrettyQuery import prettyquery
from Cache import Cache

# from parseMatchOutput import construct

class SimpleSPARQL (SPARQLWrapper) :
	def __init__(self, baseURI, returnFormat=None, defaultGraph=None, sparul=None, graph=None, n=None):
		SPARQLWrapper.__init__(self, baseURI, returnFormat, defaultGraph)
		if sparul :
			self.setSPARUL(sparul)
		else :
			self.setSPARUL(baseURI.replace('sparql', 'sparul'))
		if n :
			self.n = n
		else :
			self.n = Namespaces.Namespaces()
		self.n.bind('var', '<http://dwiel.net/axpress/var/0.1/>')
		self.n.bind('tvar', '<http://dwiel.net/axpress/translation/var/0.1/>')
		self.n.bind('bnode', '<http://dwiel.net/axpress/bnode/0.1/>')
		self.n.bind('meta', '<http://dwiel.net/axpress/meta/0.1/>')
		#self.n.bind('meta_var', '<http://dwiel.net/axpress/meta_var/0.1/>')
		self.lang = 'en'
		self.debug = False
		self.graph = graph
		self.translations = []
#		self.cache = Cache(SimpleSPARQL(self.baseURI, defaultGraph))
	
	def setSPARUL(self, baseURI, returnFormat=None, defaultGraph=None):
		self.sparul = SPARQLWrapper(baseURI, returnFormat, defaultGraph)
	
	def setNamespaces(self, n):
		self.n = n
	
	def setDebug(self, _debug):
		self.debug = _debug
	
	def setGraph(self, graph) :
		self.graph = graph
	
	def wrapGraph(self, query) :
		"""
		if self.graph has a value, wrap the query in a GRAPH clause to specify where
		the data should come from
		"""
		if self.graph :
			return " GRAPH <%s> { %s } " % (self.graph, query)
		else :
			return query
	
	# from parseMatchOutput
	# returns a GraphPattern
	def parseConstruct(self, construct_str) :
		where = rdflib.sparql.parser._buildQueryArgs(self.n.SPARQL_PREFIX()+str(" WHERE { %s }" % construct_str))
		return where['where'][0]
	
	def doQuery(self, query) :
		"""Execute a SPARQL/SPARUL query and return the result.  The set of prefixes
		in self.n namespaces will be prepended to the query.
		if the query is an ASK returns true or false
		if the query is a SELECT: returns JSON of the bindings
		"""
		try :
			query = self.n.SPARQL_PREFIX() + query
		except:
			pass
		
		query_type = self._parseQueryType(query)
		if query_type == "DELETE" or query_type == "INSERT" :
			sparql = self.sparul
			sparql.setMethod("POST")
			sparql.setQueryParam("request")
		else :
			sparql = self
			
		if type(query) == unicode :
			query = query.encode('utf-8')
		
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		
		if query_type == "SELECT" :
			return sparql.query().convert()
		elif query_type == "ASK" :
			try :
				return sparql.query().convert()['boolean']
			except Exception, e:
				print query
				raise e
		else :
			return sparql.query()
	
	def doQueryURI(self, query, construct_str = None) :
		"""
		depricated ?
		"""
		g = self.doQuery(query)
		for rawbindings in g['results']['bindings'] :
			if construct_str == None :
				uri = rawbindings['uri']['value']
				if rawbindings['uri']['type'] == 'bnode' :
					raise Exception("can not convert a BNode into an RDFObject")
				n3 = self.describe(uri)
				yield RDFObject(n3, uri, self)
			else :
				c = Graph()
				pattern = self.parseConstruct(construct_str)
				bindings = {}
				for key,value in rawbindings.iteritems() :
					bindings['?'+key] = Literal(value['value'])
				
				pattern.construct(c, bindings)
				yield RDFObject(c, self.n.e['uri'], self)

	def doShortQueryURI(self, query) :
		return self.doQueryURI("""SELECT DISTINCT ?uri WHERE { %s . }""" % self.wrapGraph(query))
	
	def doQueryNumber(self, query) :
		"""
		@arg query - SPARQL query with a single number expected to be returned
		@return the single number returned from the query
		"""
		qr = self.doQuery(query)
		datatype = qr['results']['bindings'][0]['.1']['datatype']
		value = qr['results']['bindings'][0]['.1']['value']
		if datatype == u'http://www.w3.org/2001/XMLSchema#integer' :
			return int(value)
		# TODO case where the datatype is a floating point value
		# TODO case where query is not COUNT ? I dunno if its covered
		return value

	def describe(self, uri) :
		self.setQuery("DESCRIBE <"+uri+">")
		self.setReturnFormat(JSON)
		q = self.query()
		return q.convert()
		
	def describe_dict(self, uri) :
		return RDFObject(self.describe(uri), uri)
		
	# for now, this constructs a uri based on the number of seconds since the
	# epoch
	def get_uri(self):
		postfix = str(time.time()).replace('.','')
		return self.n.e['rule'+postfix]
	
	# replace all occurances of :new with a new unique uri
	def replace_uri(self, src, dest):
		src_pattern = "%s ?s ?o" % src.n3()
		dest_pattern = "%s ?s ?o" % dest.n3()
		ret = self.doQuery("""
		INSERT INTO <%s> { %s }
		WHERE { %s }
		DELETE FROM <%s> { %s }
		WHERE { %s }
		""" % (self.graph, dest_pattern, src_pattern, self.graph, src_pattern, src_pattern))

	def SPARQL_PREFIX(self) :
		str = ''
		for prefix,namespace in self.namespaces.iteritems() :
			str += 'PREFIX %s: <%s> ' % (prefix, namespace)
		return str
	
	def flatten(self, seq):
		res = []
		for item in seq:
			if (isinstance(item, (tuple, list))):
				res.extend(self.flatten(item))
			else:
				res.append(item)
		return res
	
	def python_to_n3_helper(self, data, long_format = False, path = [], bound_vars = {}) :
		# constants
		if type(data) == int or type(data) == float :
			return unicode(data)
		elif type(data) == str or type(data) == unicode:
			if type(data) == str :
				data = unicode(data)
			if self.n.matches(data) :
				return data
			else :
				data = data.replace('\\', '\\\\')
				data = data.replace('\n', '\\n')
				data = data.replace('"', '\\"')
				data = data.replace("'", "\\'")
				if '"' not in data :
					return u'"'+data+u'"@'+self.lang
				if "'" not in data :
					return u"'"+data+u"'@"+self.lang
				if '"""' not in data :
					return u'"""'+data+u'"""@'+self.lang
				if "'''" not in data :
					return u"'''"+data+u"'''@"+self.lang
				raise Exception("can't figure out how to put this in quotes...")
		elif type(data) == datetime.datetime :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % (data.year, data.month, data.day, data.hour, data.minute, data.second)
		elif type(data) == time.struct_time :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % data[0:6]
		elif type(data) == rdflib.URIRef :
			return data.n3()
		# resulting in vars:
		elif data == [] :
			self.variable += 1
			varname = u'?var' + unicode(self.variable)
			bound_vars[varname[1:]] = self.flatten([path, list])
			return varname
		elif data == None :
			self.variable += 1
			varname = u'?var' + unicode(self.variable)
			bound_vars[varname[1:]] = path
			return varname
		# complex queries
		elif type(data) == dict :
			key_value_pairs = [(self.python_to_n3_helper(key, long_format, path, bound_vars), self.python_to_n3_helper(value, long_format, self.flatten([path, key]), bound_vars)) for (key, value) in data.iteritems()]
			key_value_pairs_str = map(lambda (p):p[0]+u' '+p[1], key_value_pairs)
			return u'[ ' + u' ; '.join(key_value_pairs_str) + u' ]'
		elif type(data) == list and len(data) == 1 and type(data[0]) == dict :
			# TODO: what does this case mean?
			pass
		elif type(data) == list :
			return u', '.join(map(lambda x:self.python_to_n3_helper(x, long_format, self.flatten([path, list]), bound_vars), data))
		else :
			print type(data),'not supported as n3', data
	
	remove_square_brackets_from_dict = re.compile('\[ (.*) \]')
	def python_to_n3(self, data, object_uri = ":new", long_format = False) :
		"""
		converts a python object to n3 format.
		if data is a dictionary, an object is formed with the uri <i>object_uri</i>
		if data is a number or datetime, it is converted to the appropriate Literal
		if data is a string, and is a valid uri, it will be considered one
			otherwise it will be considered a string
		"""
		if type(data) == dict :
			dict_str = self.python_to_n3_helper(data, long_format)
			dict_str = self.remove_square_brackets_from_dict.sub('\\1', dict_str)
			return '%s %s %s .' % (self.n.n3_prefix(), object_uri, dict_str)
		else :
			return self.python_to_n3_helper(data, long_format)

	def python_to_SPARQL_helper(self, data, variable, bound_vars) :
		key_value_pairs = [(self.python_to_n3_helper(key, bound_vars = bound_vars), self.python_to_n3_helper(value, False, [key], bound_vars)) for (key, value) in data.iteritems()]
		key_value_pairs_str = map(lambda (p):p[0]+u' '+p[1], key_value_pairs)
		return (u' . ' + variable.n3() + u' ').join(key_value_pairs_str)

	def _reset_SPARQL_variables(self) :
		self.variable = 0

	def python_to_SPARQL(self, data, variable = Variable('uri'), bound_vars = {}) :
		if type(data) != dict :
			raise Exception("data must be a dictionary")
		
		self._reset_SPARQL_variables()
		return u"%s %s" %(variable.n3(), self.python_to_SPARQL_helper(data, variable, bound_vars))

	def find(self, data) :
		return self.doShortQueryURI(self.python_to_SPARQL(data, Variable("uri")))
	
	def _dict_key_list_set(self, obj, ls, value) :
		for key in ls[:-1] :
			obj = obj[key]
		obj[ls[-1]] = value
	
	def _reset_var(self) :
		self.variable = 0
	
	def _new_var(self, bound_vars, path) :
		self.variable += 1
		varname = u'?var' + unicode(self.variable)
		bound_vars[varname[1:]] = path
		return varname
	
	def read_parse_helper(self, query, path, triples, explicit_vars, implicit_vars, given_vars) :
		"""
		@arg path is a list (like xpath) of where in the query we are
		@arg triples is a list of triples which is appended through the query walk
		@arg explicit_vars is a dict which is appended to include paths to exp vars
			an explicit variable is a variable in the query which is explicitly asked
			for. (x : None)
		@arg implicit_vars is a dict which is appended to include paths to imp vars
			an implicit variable is a variable which is required to build the SPARQL
			but which does not need to be returned back to the user
		@arg given_vars is a list which is appended to include paths to all 
			variables, including the parameters with constant values which are 
			being used to describe the data.
		@return SPARQL Literal or variable to refer to this part of the query.
		@side-effect triples, explicit_vars and implicit_vars are appended to.
		"""
		# constants
		if type(query) == int or type(query) == float :
			return unicode(query)
		elif type(query) == str or type(query) == unicode:
			if type(query) == str :
				query = unicode(query)
			if self.n.matches(query) :
				return query
			else :
				query = query.replace('\\', '\\\\')
				query = query.replace('\n', '\\n')
				if '"' not in query :
					return u'"'+query+u'"@'+self.lang
				if "'" not in query :
					return u"'"+query+u"'@"+self.lang
				if '"""' not in query :
					return u'"""'+query+u'"""@'+self.lang
				if "'''" not in query :
					return u"'''"+query+u"'''@"+self.lang
				raise Exception("can't figure out how to put this in quotes...")
		elif type(query) == datetime.datetime :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % (query.year, query.month, query.day, query.hour, query.minute, query.second)
		elif type(query) == time.struct_time :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % query[0:6]
		elif type(query) == rdflib.URIRef :
			return query.n3()
		elif type(query) == rdflib.Literal :
			if query.datatype == None :
				# this is a string
				return query.n3()+'@'+self.lang
			else :
				return query.n3()
		
		# cases resulting in explicit variables
		elif query == None :
			return self._new_var(explicit_vars, path)
		elif query == [] :
			path = copy.copy(path)
			path.append(list)
			return self._new_var(explicit_vars, path)
		
		elif type(query) == list and len(query) == 1 and type(query[0]) == dict :
			path = copy.copy(path)
			path.append(list)
			return self.read_parse_helper(query[0], path, triples, explicit_vars, implicit_vars, given_vars)
		
		# a list of only dicts length > 1 (length > 1 known because not the above case)
		elif type(query) == list and all([type(i) == dict for i in query]) :
			# TODO !!!
			# should this match any of these object or all of these?
			# should maybe not require that the type of all objects in the list are 
			# dicts.
			# An any clause requires optional subqueries to be implemented
			raise Exception('ambiguous case not yet implemented (dont have a list of more than one item)')
		
		# complex queries
		elif type(query) == dict :
			if self.n.sparql.subject in query :
				subject = query[self.n.sparql.subject]
				if isinstance(subject, URIRef) :
					subject = subject.n3()
				del query[self.n.sparql.subject]
				if subject == None :
					subject = self._new_var(explicit_vars, path)
			else :
				subject = self._new_var(implicit_vars, path)
			for key, value in query.iteritems() :
				# print 'k',key,'v',value
				path2 = copy.copy(path)
				nk = self.read_parse_helper(key, path, triples, explicit_vars, implicit_vars, given_vars)
				path2.append(key)
				nv = self.read_parse_helper(value, path2, triples, explicit_vars, implicit_vars, given_vars)
				# print '---', nk, nv, type(nk), type(nv)
				# if the new value is not a uri or a variable, then its a given value
				if len(nv) != 0 and nv[0] != '<' and nv[0] != '?' :
					given_vars.append(copy.copy(path2))
				pair = (nk, nv)
				#print 'dict', pair
				triples.append((subject, nk, nv))
			return subject
		
		# else ...
		else :
			raise Exception("unkown data type: %s" % str(type(query)))
	
	def verify_restrictions_helper(self, bindings, vars, path, var, explicit_vars) :
		"""
		bindings: raw values returned from SPARQL query
		vars: dict from variable name to path in query
		path: current path
		var: current var we're filling in
		explicit_vars: variables whose values were asked for by the query.  (Some
			variables are generated by the compiler in order to translate the query
			into SPARQL)
		"""
		# is path2 one deeper than path1?
		def one_deeper(p1, p2) :
			if len(p2) <= len(p1) :
				return False
			if p2[:len(p1)] != p1 :
				return False
			if len(p2[len(p1):]) == 1 :
				return True
			if len(p2[len(p1):]) == 2 and p2[-1] == list :
				return True
			return False
		
		def value_from_path(path) :
			if len(path) == 0 :
				return
			if path[-1] == list :
				if len(path) == 1 :
					return
				return path[-2]
			else :
				return path[-1]
		
		# this is used where a binding needs to be the key of a hash.  Convert it to
		#   a tuple which is hashable
		def tuple_binding(binding) :
			if 'datatype' in binding :
				return (binding['type'], binding['value'], binding['datatype'])
			else :
				return (binding['type'], binding['value'])
		
		# see tuple_binding
		def untuple_binding(binding_tuple) :
			if len(binding_tuple) == 2 :
				return {'type' : binding_tuple[0], 'value' : binding_tuple[1]}
			else :
				return {'type' : binding_tuple[0], 'value' : binding_tuple[1], 'datatype' : binding_tuple[2]}
		
		# if we got not values back, just return None or [] depending on the path
		if bindings == [{}] :
			if path == [list] :
				return []
			else :
				return None
	
		var_path = vars[var]
		
		# var_values is the set of all values this variable takes in the bindings
		var_values = set()
		for binding_set in bindings :
			binding = binding_set[var]
			var_values.add(tuple_binding(binding))
		
		# if there are too many or two few values returned from the query, raise an 
		#  Exception
		if len(var_path) == 0 or var_path[-1] != list :
			if len(var_values) == 0 :
				raise QueryException(var_path, 'no match found')
				# return 'missing value'
			elif len(var_values) > 1 :
				raise QueryException(var_path, 'too many values')
				# return 'too many values'
		
		# recur ...
		
		# now move to the new path
		path = var_path
		
		# look for vars which are one level deeper than the one we are at ...
		next_vars = []
		for v, p in vars.iteritems() :
			# if this path is one node deeper than the current path
			if one_deeper(path, p) :
				next_vars.append(v)
				# print 'v,p:',v, p
			
		result_queries = {}
		# find the new subset of bindings we are looking at
		# for each value of this variable, generate a subset of bindings to check 
		for binding_tuple in var_values :
			# print 'binding',binding
			binding = untuple_binding(binding_tuple)
			new_bindings = []
			for binding_set in bindings :
				if binding_set[var] == binding :
					# print '  bs', ','.join(map(lambda x:binding_set[x]['value'], vars.keys()))
					new_bindings.append(binding_set)
			
			result_query = {}
			
			# result_query['subject'] = binding
			
			# for each next_var
			for next_var in next_vars :
				# print '=> recur', next_var
				result_query[value_from_path(vars[next_var])] = self.verify_restrictions_helper(new_bindings, vars, path, next_var, explicit_vars)
				# print 'ret',ret
			
			if var in explicit_vars :
				if binding['type'] == 'bnode' :
					raise Exception('can not bind a bnode to a variable, sorry')
				elif binding['type'] == 'uri' :
					result_query[self.n.sparql.subject] = URIRef(binding['value'])
				else :
					result_query[self.n.sparql.subject] = binding
			
			result_queries[tuple_binding(binding)] = result_query
		
		# print 'result_query', result_queries
		
		results = []
		for result in var_values :
			type = result[0]
			value = result[1]
			if len(result) == 3 :
				datatype = result[2]
			else :
				datatype = None
			
			if type == 'literal':
				results.append(Literal(value))
			elif type == 'typed-literal' :
				if datatype == u'http://www.w3.org/2001/XMLSchema#decimal' :
					results.append(Literal(float(value)))
				elif datatype == u'http://www.w3.org/2001/XMLSchema#integer' :
					results.append(Literal(int(value)))
				else :
					raise Exception("I haven't seen this data type before: %s" % datatype)
			else :
				results.append(result_queries[result])
		
		if len(var_path) == 0 or path[-1] != list :
			results = results[0]
		
		# print results
		return results
	
	def verify_restrictions(self, results, explicit_vars, implicit_vars, root_subject) :
		bindings = results['results']['bindings']
		
		vars = {}
		vars.update(explicit_vars)
		vars.update(implicit_vars)
		
		if root_subject[0] != '?' :
			# if the root_subject is already known, look for the variable with the next_vars
			#   next shortest path
			#			path
			#			for var, path in vars.iteritems() :
			# TODO: run the test case and notice that the result is just 1 rather than
			#  building the full query out.  Need to somehow build it out.  It might
			#  be better to coax the helper to do this for us, it might be better to
			#  do it here ...
			result = {}
			
			def is_path_subset(pathsm, pathlg) :
				if len(pathsm) > len(pathlg) :
					return False
				if pathsm == pathlg[:len(pathsm)] :
					return True
				return False
			
			# find the variables whose paths are not subpaths of any others.  These
			# are the variable which need to be called and 'built' here.  The rest
			# will be built recursively by verify_restrictions_helper.
			
			root_vars = copy.deepcopy(vars)
			# loop through each var in order from longest path to shortest
			vars_list = sorted(vars.iteritems(), lambda x,y: len(y[1])-len(x[1]))
			for i, (root_vari, pathi) in enumerate(vars_list[:-1]) :
				for j, (root_varj, pathj) in enumerate(vars_list[i+1:]) :
					if is_path_subset(pathj, pathi) :
						if root_vari in root_vars :
							del root_vars[root_vari]
						continue
			
			for root_var, path in root_vars.iteritems() :
				this_root = result
				if path[-1] == list :
					end_ele_i = -2
				else :
					end_ele_i = -1
				if len(path) > 1 :
					for ele in path[:end_ele_i] :
						if ele == list :
							continue
						if ele not in this_root :
							this_root[ele] = {}
						this_root = this_root[ele]
				end_ele = path[end_ele_i]
				ret = self.verify_restrictions_helper(bindings, vars, [], root_var, explicit_vars.keys())
				this_root[end_ele] = ret
			
			return result
		else :
			root_var = root_subject[1:]
			path = vars[root_var]
		
		return self.verify_restrictions_helper(bindings, vars, [], root_var, explicit_vars.keys())
	
	def read(self, query) :
		if type(query) == list and type(query[0]) == list :
			return self.new_read(query)
		query = copy.deepcopy(query)
		n = self.n
		# try a raw_read which returns exceptions.  If it works, return a status ok;
		# if it doesn't catch the exception and return the infromation associated 
		# with that.
		try :
			return {
				n.sparql.status : n.sparql.ok,
				n.sparql.result : self.read_raw(query)
			}
		except QueryException, qe :
			q = query
			for ele in qe.path :
				if ele is list :
					q = q[0]
				elif ele is not None :
					q = q[ele]
			q[n.sparql.error_inside] = '.'
			return {
				n.sparql.status : n.sparql.error,
				n.sparql.query : query,
				n.sparql.error_path : qe.path,
				n.sparql.error_message : qe.message,
			}
	
	def read_raw(self, query) :
		n = self.n

		modifiers = []
		# interpret basic keywords modifiers if they are present and then remove 
		# them from the query
		if type(query) == list :
			rootquery = query[0]
		else :
			rootquery = query
		if n.sparql.limit in rootquery :
			modifiers.append("LIMIT %d" % rootquery[n.sparql.limit])
			del rootquery[n.sparql.limit]
		if n.sparql.offset in rootquery :
			modifiers.append("OFFSET %d" % rootquery[n.sparql.offset])
			del rootquery[n.sparql.offset]
		if n.sparql.sort in rootquery :
			sort_path = rootquery[n.sparql.sort]
			if type(sort_path) != list :
				sort_path = [sort_path]
			if type(query) == list :
				sort_path.insert(0, list)
			del rootquery[n.sparql.sort]
		else :
			sort_path = None
		
		self._reset_var()
		triples = []
		explicit_vars = {}
		implicit_vars = {}
		given_vars = []
		root_subject = self.read_parse_helper(query, [], triples, explicit_vars, implicit_vars, given_vars)
		
		triples_str = ""
		for triple in triples :
			triples_str += "%s %s %s . " % triple
		
		def find_var_from_path(explicit_vars, sort_path) :
			for var, path in explicit_vars.iteritems() :
				if sort_path == path :
					return var
			return None
		
		if sort_path :
			sort_var = find_var_from_path(explicit_vars, sort_path)
			if sort_var :
				modifiers.insert(0, 'ORDER BY ?%s' % sort_var)
			else :
				print sort_path
				print explicit_vars
				raise Exception('sort path not valid')
		
		SPARQL = "SELECT DISTINCT * WHERE { %s } %s" % (self.wrapGraph(triples_str), ' '.join(modifiers))
		results = self.doQuery(SPARQL)
		
		# start with vars whose path is [] or [list]
		verification = self.verify_restrictions(results, explicit_vars, implicit_vars, root_subject)
		# print 'verification:',verification
		
		return verification

	def read_old(self, data) :
		bound_vars = {}
		results = self.doQuery("SELECT DISTINCT * WHERE { %s }" % self.wrapGraph(self.python_to_SPARQL(data, Variable("uri"), bound_vars)))
		# print bound_vars
		# print results
		objs = []
		for rawbindings in results['results']['bindings'] :
			obj = copy.copy(data)
			# print rawbindings
			for key, value in rawbindings.iteritems() :
				if key != u'uri' :
					if value['type'] == 'bnode' :
						raise Exception("can not bind a bnode to a variable")
					self._dict_key_list_set(obj, bound_vars[key], value['value'])
			objs.append(obj)
		return objs
	
	def quickread(self, data) :
		results = self.doQuery("SELECT DISTINCT * WHERE { %s }" % self.wrapGraph(self.python_to_SPARQL(data, Variable("uri"))))
		values = []
		for rawbindings in results['results']['bindings'] :
			for key, value in rawbindings.iteritems() :
				if key != u'uri' :
					if value['type'] == 'bnode' :
						raise Exception("can not bind a bnode to a variable")
					values.append(value['value'])
		return values

	def ask(self, query) :
		if type(query) == dict :
			triples = []
			self.read_parse_helper(query, [], triples, {}, {}, [])
			query = ""
			for triple in triples :
				query += "%s %s %s . " % triple
		return self.doQuery("ASK { %s }" % self.wrapGraph(query))
	
	# remove dicts with pairs like n.sparql.create : n.sparql.unless_exists with a
	# n.sparql.var : 1
	# bound_vars is an integer of where the variables should start being bound to
	def _preprocess_query_helper(self, query, bound_vars, inserts, deletes) :
		sparql = self.n.sparql
		if type(query) == dict :
			newquery = {}
			for k, v in query.iteritems() :
				if k == sparql.create :
					return None, copy.copy(query), None
				if k == sparql.delete :
					return None, None, copy.copy(query)
				if type(v) == dict :
					v2, insert, delete = self._preprocess_query_helper(v, bound_vars, inserts, deletes)
					# if the value of this pair was a write (create/connect)
					if insert :
						if sparql.var not in newquery :
							var = bound_vars[0]
							bound_vars[0] += 1
						else :
							var = newquery[sparql.var]
						
						newquery[sparql.var] = var
						insert[sparql.subject] = var
						insert[sparql.predicate] = k
						inserts.append(insert)
					if delete :
						if sparql.var not in newquery :
							var = bound_vars[0]
							bound_vars[0] += 1
						else :
							var = newquery[sparql.var]
						
						newquery[sparql.var] = var
						delete[sparql.subject] = var
						delete[sparql.predicate] = k
						deletes.append(delete)
					if v2 is not None :
						newquery[k] = v2
				elif type(v) == list :
					for vi in v :
						vi2, insert, delete = self._preprocess_query_helper(vi, bound_vars, inserts, deletes)
						# if the value of this pair was a write (create/connect)
						if insert :
							if sparql.var not in newquery :
								var = bound_vars[0]
								bound_vars[0] += 1
							else :
								var = newquery[sparql.var]
							
							newquery[sparql.var] = var
							insert[sparql.subject] = var
							insert[sparql.predicate] = k
							inserts.append(insert)
						if delete :
							if sparql.var not in newquery :
								var = bound_vars[0]
								bound_vars[0] += 1
							else :
								var = newquery[sparql.var]
							
							newquery[sparql.var] = var
							delete[sparql.subject] = var
							delete[sparql.predicate] = k
							deletes.append(delete)
						if vi2 is not None :
							if k not in newquery :
								newquery[k] = []
							newquery[k].append(vi2)
				else :
					newquery[k] = v
			return newquery, None, None
		elif type(query) == list :
			return [self._preprocess_query_helper(queryi, bound_vars, inserts, deletes) for queryi in query]
	
	def _preprocess_query(self, query) :
		"""put n.sparql.var : # pairs in all dicts whose root need to have a 
		variable name.  Move all inserts/creates/writes into a list of 
		n.sparql.insert in the root of the query.  Each insert has the original dict
		to write plus, a n.sparql.subject : # which is the root variable and an 
		n.sparql.predicate which is the predicate of the tripe to add (where the
		rest of the dictionary describes the object of the triple
		"""
		sparql = self.n.sparql
		if type(query) is not dict and type(query) is not list:
			raise Exception('query must be a dictionary or a list')
		
		inserts = []
		deletes = []
		bound_vars = [1]
		query, insert, delete = self._preprocess_query_helper(query, bound_vars, inserts, deletes)
		if insert :
			query = {}
			var = bound_vars[0]
			bound_vars[0] += 1
			
			query[sparql.var] = var
			insert[sparql.subject] = None
			insert[sparql.predicate] = None
			inserts.append(insert)
		if delete :
			query = {}
			var = bound_vars[0]
			bound_vars[0] += 1
			
			query[sparql.var] = var
			delete[sparql.subject] = None
			delete[sparql.predicate] = None
			deletes.append(delete)
		
		# print 'deletes:',deletes
		
		# this happens when the root object is a create
		#if query is None and _ is not None :
			#query = _
		
		query[sparql.insert] = inserts
		query[sparql.delete] = deletes
		
		return query
	
	def _bnodeVar(self) :
		var = 0
		while True :
			var += 1
			yield URIRef('_:b'+str(var))
			
	def _uriVar(self) :
		while True :
			postfix = str(time.time()).replace('.','')
			yield self.n.sparql['bnode'+postfix].n3()
	
	def python_to_SPARQL_long_helper(self, query, var) :
		def append_pair(root, k, v) :
			ret = ""
			k_str, k_extra = self.python_to_SPARQL_long_helper(k, var)
			v_str, v_extra = self.python_to_SPARQL_long_helper(v, var)
			ret += '%s %s %s .\n' % (root, k_str, v_str)
			ret += k_extra
			ret += v_extra 
			return ret
		
		ret = ""		
		if type(query) == dict :
			if self.n.sparql.var in query :
				root = '?var'+str(query[self.n.sparql.var])
			else :
				root = var.next()
			
			for k, v in query.iteritems() :
				if k == self.n.sparql.var :
					continue
				if k == self.n.sparql.any :
					k = var.next()
				if v == self.n.sparql.any :
					v = var.next()
				if type(k) == list :
					if type(v) == list :
						for ki in k :
							for vi in v :
								ret += append_pair(root, ki, vi)
					else :
						for ki in k :
							ret += append_pair(root, ki, v)
				else :
					if type(v) == list :
						for vi in v :
							ret += append_pair(root, k, vi)
					else :
						ret += append_pair(root, k, v)
			
			return root, ret
		else :
			# print 'recur',type(query),query,self.python_to_n3(query)
			return self.python_to_n3(query), ""
	
	def python_to_SPARQL_long(self, query, var = None) :
		"""convert a python object into SPARQL format.  (this version doesn't use
		blank nodes, which is useful if you want to be able to append to or refer
		to the dictionaries converted
		"""
		if var == None :
			var = self._bnodeVar()
		return self.python_to_SPARQL_long_helper(query, var)[1]
	
	def _extract_where(self, query) :
		"""given a query in the form described in _preprocess_query, return a WHERE
		clause to be used in the final SPARQL queries"""
		query = copy.copy(query)
		
		# discard the insert information
		if self.n.sparql.insert in query :
			del query[self.n.sparql.insert]
		
		# discard the delete information
		if self.n.sparql.delete in query :
			del query[self.n.sparql.delete]
		
		# build the where clause with outlined variables
		return self.python_to_SPARQL_long(query)
	
	def _extract_inserts(self, query) :
		"""given a query in the form describes in _preprocess_query, return a set of
		insert clauses to be used in the final SPARQL queries"""
		sparql = self.n.sparql
		
		# because the loop below alter's the contents of each insert
		query = copy.copy(query)
		
		# grab the insert list
		inserts = query[sparql.insert]
		
		new_inserts = []
		for insert in inserts :
			if sparql.create in insert :
				var = insert[sparql.subject]
				predicate = insert[sparql.predicate]
				
				del insert[sparql.subject]
				del insert[sparql.predicate]
				
				if predicate is None :
					new_inserts.append(insert)
				else :
					new_inserts.append({
						sparql.var : var,
						predicate : insert,
					})
		return new_inserts
	
	def _extract_deletes(self, query) :
		"""given a query in the form described in _preprocess_query, return a set of
		insert clauses to be used in the final SPARQL queries"""
		sparql = self.n.sparql
		
		# because the loop below alter's the contents of each insert
		query = copy.copy(query)
		
		# grab the insert list
		deletes = query[sparql.delete]
		
		new_deletes = []
		for delete in deletes :
			if sparql.delete in delete :
				var = delete[sparql.subject]
				predicate = delete[sparql.predicate]
				
				del delete[sparql.subject]
				del delete[sparql.predicate]
				
				if predicate is None :
					new_deletes.append(delete)
				else :
					new_deletes.append({
						sparql.var : var,
						predicate : delete,
					})
		return new_deletes
	
	def write(self, query, where = None, varnamespace = None) :
		"""
		writes query expressed in jsparql
		@arg query is query expressed in jsparql.  Can either be in object or 
			triplelist form.  If in triplelist form, query is the insert and the
			second argument where is the where clause
		@arg where is the where clause of a triplelist format query.  Not used if
			query is an object format.
		@arg varnamespace is the namespace to use to identify a variable in the case
			that the triplelist form is used
		"""
		
		# if this is a list of lists, then it is a jsparql query
		if type(query) == list and type(query[0]) == list :
			return self.write_tripleslist(query, where, varnamespace)
		
		sparql = self.n.sparql
		
		query = self._preprocess_query(query)
		where = self._extract_where(query)
		inserts = self._extract_inserts(query)
		deletes = self._extract_deletes(query)
		
		# print 'deletes'
		# pprint(deletes)
		
		print 'query'
		pprint(query)
		print 'where'
		pprint(where)
		print 'inserts'
		pprint(inserts)
		print 'deletes'
		pprint(deletes)
		
		if where is not "" and not self.ask(where) :
			ret = { 'error' : 'where clause not found', 'where' : where, 'query' : query}
			return ret
		
		"""
		create : unless_exists
			insert to matches which don't already have insert
		create : unconditional
			insert to all matches regardless
		create : [only_once, unconditional]
			if matches > 1 : do nothing
			if matches == 1 : unconditional
		create : [only_once, unless_exists]
			if matches > 1 : do nothing
			if matches == 1 : unless_exists
		
		connect : same as above
			# TODO
		"""
		
		for insert in inserts :
			# create: the type of insert.  Either unless_exists, only_once or both
			# special case where create in root node
			if sparql.create in insert :
				create = insert[sparql.create]
				del insert[sparql.create]
			else :
				# find the predicate (key) and extract and remove sparql.create from it
				for key in insert.keys() :
					if key != sparql.var :
						create = insert[key][sparql.create]
						del insert[key][sparql.create]
			
			#print 'create',create
			#print 'where',where
			#print 'insert',insert
			
			if type(create) == list :
				if sparql.only_once in create :
					count = self.doQueryNumber("""
						SELECT COUNT(DISTINCT %s)
						WHERE { %s }
					""" % ('?var'+insert[sparql.var], self.wrapGraph(where)))
					if count != 1 :
						#print 'count not 1:', count
						# TODO: somehow pass this on to the return structure
						continue
					create.remove(sparql.only_once)
					create = create[0]
			
			insert_str_uri = self.python_to_SPARQL_long(insert, self._uriVar())
			#insert_str_uri = self.wrapGraph(insert_str_uri)
			where = self.wrapGraph(where)
			if create == sparql.unless_exists :
				insert_str_bnode = self.python_to_SPARQL_long(insert, self._bnodeVar())
				if not self.ask("%s %s" % (where, insert_str_bnode)) :
					if self.debug :
						print "INSERT INTO <%s> { %s } WHERE { %s }" % (self.graph, insert_str_uri, where)
					else :
						self.doQuery("INSERT INTO <%s> { %s } WHERE { %s }" % (self.graph, insert_str_uri, where))
			elif create == sparql.unconditional :
				if self.debug :
					print "INSERT INTO <%s> { %s } WHERE { %s }" % (self.graph, insert_str_uri, where)
				else :
					self.doQuery("INSERT INTO <%s> { %s } WHERE { %s }" % (self.graph, insert_str_uri, where))
			else :
				raise Exception("unkown create clause: " + create)
		
		for delete in deletes :
			# pprint(delete)
			
			del delete[sparql.delete]
			
			delete_str_uri = self.python_to_SPARQL_long(delete, self._bnodeVar())
			
			print 'delete_str_uri',delete_str_uri
			# delete_str_uri = self.wrapGraph(delete_str_uri)
			# where = delete_str_uri + ' ' + where
			# where = self.wrapGraph(where)
			# self.doQuery("DELETE { %s } WHERE { %s }" % (delete_str_uri, where))
		
		return {'result' : 'ok', 'query' : query}
	
	def write_tripleslist(self, query, where, varnamespace) :
		self._reset_SPARQL_variables()
		self.reset_py_to_SPARQL_bnode()
		query_str = self.triplelist_to_sparql(query, varnamespace)
		if where :
			where_str = self.triplelist_to_sparql(where, varnamespace)
		else :
			where_str = ''
		
		sparql_str = "INSERT INTO <%s> { %s } WHERE { %s }" % (self.graph, query_str, where_str)
		print
		print
		print 'write'
		print sparql_str
		print
		print
		return self.doQuery(sparql_str)
	
	def insert(self, data, language = 'N3') :
		"""this isn't supported by all sparul endpoints.  converts data to N3 and 
		then sends to the sparul address with insert and lang parameters
		"""
		if language == 'N3' :
			if type(data) == dict :
				data = python_to_n3(data)
				language = 'N3'
		#print 'data',data
		f = urlopen(self.sparul.baseURI, urlencode({'insert' : data, 'lang' : language}))
		# self.update_new_uri()
	
	def n3(self, data) :
		t = type(data)
		if t == URIRef :
			return data.n3()
		elif t == Literal :
			return data.n3()
		elif t == set or t == list or t == tuple :
			data = list(data)
			n3data = map(self.n3, data)
			return ', '.join(n3data)
		elif t == str or t == unicode :
			return '"%s"' % data
		else :
			return data.__str__()
	
	def insert_triple(self, subject, pred, object) :
		subject = self.n3(subject)
		pred = self.n3(pred)
		object = self.n3(object)
		triple = " %s %s %s " % (subject, pred, object)
		self.doQuery("INSERT INTO <%s> { %s }" % (self.graph, triple))
		
	def find_vars(self, query) :
		try :
			iter = query.__iter__()
		except AttributeError :
			if type(query) == URIRef :
				if query.find(self.n.var) == 0 :
					return set([query[len(self.n.var):]])
			return set()
		
		vars = set()
		for i in iter :
			vars.update(self.find_vars(i))
		return vars
	
	def next_bnode(self) :
		return self.n.bnode[str(time.time()).replace('.','') + '_' +  str(random.random()).replace('.','')]
	
	def _uribnodeVar(self) :
		var = 0
		while True :
			yield self.next_bnode().n3()
	
	def triplelist_value_to_sparql(self, object, extra_triple_strs, varnamespace = None) :
		"""
		@arg object is the python object to convert to sparql
		@arg extra_triple_strs is a list which is appended to if the object is a
			dict which needs to use more triples to express in sparql
		"""
		if varnamespace == None :
			varnamespace = self.n.var
		if type(object) == URIRef :
			if object.find(varnamespace) != -1 :
				return '?'+object[len(varnamespace):]
			elif object.find(self.n.bnode) != -1 :
				varname = object[len(self.n.bnode):]
				if varname in self.py_to_SPARQL_bnode :
					return self.py_to_SPARQL_bnode[varname].n3()
				else :
					bnode = self.next_bnode()
					self.py_to_SPARQL_bnode[varname] = bnode
					return bnode.n3()
		elif type(object) == dict :
			root, triples = self.python_to_SPARQL_long_helper(object, self._uribnodeVar())
			extra_triple_strs.append(triples)
			return root
		
		return self.python_to_n3(object)
	
	def reset_py_to_SPARQL_bnode(self) :
		self.py_to_SPARQL_bnode = {}
	
	def triplelist_to_sparql(self, query, varnamespace = None) :
		# todo: shouldn't have proxy functions like this
		return self.jsparql_to_sparql(query)
	
	def jsparql_to_sparql(self, query, varnamespace = None) :
		if type(query) == list and type(query[0]) == list :
			query_str = ""
			for triple in query :
				extra_triple_strs = []
				triple = [self.triplelist_value_to_sparql(x, extra_triple_strs, varnamespace) for x in triple]
				triple_str = "%s %s %s .\n" % tuple(triple)
				query_str += triple_str + ' .\n'.join(extra_triple_strs)
			return query_str

	def new_read(self, query, expected_vars = [], varnamespace = None) :
		# TODO: extract out the result bindings as in self.read
		# TODO: allow object notation as root query.
		#   TODO: depricate read, and others
		#   TODO: more cleaning
		# TODO: figure out some way to avoid having resets everywhere.  Should this
		#   be some other class to do each translation?
		if varnamespace == None :
			varnamespace = self.n.var
		self.reset_py_to_SPARQL_bnode()
		self._reset_SPARQL_variables()
		query_str = self.triplelist_to_sparql(query, varnamespace)
		print 'query_str',query_str
		ret = self.doQuery("SELECT * WHERE { %s }" % self.wrapGraph(query_str))
		for binding in ret['results']['bindings'] :
			newbinding = {}
			for var, value in binding.iteritems() :
				if value['type'] == 'typed-literal' :
					if value['datatype'] == 'http://www.w3.org/2001/XMLSchema#integer' :
						newbinding[var] = int(value['value'])
					elif value['datatype'] == 'http://www.w3.org/2001/XMLSchema#decimal' :
						newbinding[var] = float(value['value'])
				elif value['type'] == 'literal' :
					newbinding[var] = value['value']
				elif value['type'] == 'uri' :
					newbinding[var] = URIRef(value['value'])
				elif value['type'] == 'bnode' :
					raise Exception('cant do bnodes')
			
			yield newbinding
		
		#return ret















