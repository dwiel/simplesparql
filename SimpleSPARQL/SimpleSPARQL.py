"""
SimpleSPARQL provides some high level access to some basic SPARQL queries
TODO: clean up parts of code left from axpress (update_uri)
TODO: factor out redundant code
TODO: return errors inside the return dictionary rather than with an exception
TODO: connect queries
TODO: make standards compliant or warn (insert n3 is implementation-specific)
"""

import time, re, copy, datetime
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

# from parseMatchOutput import construct

class SimpleSPARQL (SPARQLWrapper) :
	def __init__(self, baseURI, returnFormat=None, defaultGraph=None, sparul=None):
		SPARQLWrapper.__init__(self, baseURI, returnFormat, defaultGraph)
		if sparul :
			self.setSPARUL(sparul)
		else :
			self.setSPARUL(baseURI.replace('sparql', 'sparul'))
		self.n = Namespaces.Namespaces()
		self.n.bind('var', '<http://dwiel.net/axpress/var/0.1/>')
		self.n.bind('meta', '<http://dwiel.net/axpress/meta/0.1/>')
		#self.n.bind('meta_var', '<http://dwiel.net/axpress/meta_var/0.1/>')
		self.lang = 'en'
		self.debug = False
		self.graph = None
		self.plugins = []
	
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
		#query = query.replace("\\n",' ')
		#query = query.replace("\n",' ')
		# print "QUERY x ",query
		query_type = self._parseQueryType(query)
		if query_type == "DELETE" or query_type == "INSERT" :
			sparql = self.sparul
			sparql.setMethod("POST")
			sparql.setQueryParam("request")
		else :
			sparql = self
			
		if type(query) == unicode :
			query = query.encode('utf-8')
		#query = query.replace('\n', ' ')
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		# print "query", query
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
				# print bindings
				pattern.construct(c, bindings)
				yield RDFObject(c, self.n.e['uri'], self)

	def doShortQueryURI(self, query) :
		return self.doQueryURI("""SELECT DISTINCT ?uri WHERE { %s . }""" % self.wrapGraph(query))
	
	def doQueryNumber(self, query) :
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
		src_pattern = self.wrapGraph("%s ?s ?o" % src.n3())
		dest_pattern = self.wrapGraph("%s ?s ?o" % dest.n3())
		ret = self.doQuery("""
		INSERT { %s }
		WHERE { %s }
		DELETE { %s }
		WHERE { %s }
		""" % (dest_pattern, src_pattern, src_pattern, src_pattern))

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
			print type(data),'not supported as n3'
	
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
		@arg triples is a list of triples which is altered to include all triples
		@arg explicit_vars is a dict which is altered to include paths to exp vars
		@arg implicit_vars is a dict which is altered to include paths to imp vars
		@arg given_vars is a list which is altered to include paths to all 
			variables, includes the parameters with constant values which are 
			being used to describe the data.
		@return SPARQL Literal or variable to refer to this part of the query.
			triples, explicit_vars and implicit_vars are filled.
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
			pass
		
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
		#print 'bindings:',bindings
		#print 'vars'
		#for v,p in vars.iteritems() :
			#print '  ',v,p
		#print 'var:',var
		#print 'var_path:', var_path
		#print ','.join(vars.keys())
		#for binding_set in bindings :
			#print ','.join(map(lambda x:binding_set[x]['value'], vars.keys()))
		
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
			# some ideas ...
			#ret = {}
			#fake_root = []
			#for i, ele in enumerate(path[:-1]) :
				#if ele == list :
					#fake_root[0] = []
				#else :
					#fake_root[0] = {}
			#fake_root[path[-1]] = call
		else :
			root_var = root_subject[1:]
			path = vars[root_var]
		
		return self.verify_restrictions_helper(bindings, vars, [], root_var, explicit_vars.keys())
	
	def read(self, query) :
		query = copy.deepcopy(query)
		n = self.n
		try :
			return {
				n.sparql.status : n.sparql.ok,
				n.sparql.result : self.read_raw(query)
			}
		except QueryException, qe :
			q = query
			for ele in qe.path :
				q = q[ele]
			q[n.sparql.error_inside] = '.'
			return {
				n.sparql.status : n.sparql.error,
				n.sparql.query : query,
				n.sparql.error_path : qe.path,
				n.sparql.error_message : qe.message,
			}
	
	def read_raw(self, query) :
		# parse out SPARQL
		# explicit_vars
		# implicit_vars
		n = self.n

		modifiers = []
		# extract basic keywords if the are present
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
		#print 'triples'
		for triple in triples :
			#print triple
			triples_str += "%s %s %s . " % triple
		#print
		
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
		# print results
		# need to enforce restrictions on number of results implied by the query (
		# None vs. [] vs. {})
		# in the order that the implicit and explicit vars occur in the query tree
		# count how many results there are.
		
		#print 'given_vars', given_vars
		#print 'explicit_vars', explicit_vars
		
		# n.bind('test', '<http://example/test>')
		
		#sumplugin = {}
		#sumplugin['inputs'] = [[n.test.x], [n.test.y]]
		#sumplugin['outputs'] = [[n.test.sum]]
		#sumplugin['function'] = lambda q: {n.test.sum : q[n.test.x] + q[n.test.y]}
		
		#def testplugin(plugin, given_vars, explicit_vars) :
			## all plugin inputs must have given values in the query
			## TODO: is there a special case with lists being ok in some cases?
			#for input in plugin['inputs'] :
				#if input not in given_vars :
					#return False
			## all missing values in the query must have output values by the plugin
			## this could be only some of the values, which are filled in and then 
			##   passed on to the database to check
			## This code shouldn't get too in depth as it will probably be replaced
			##   when converted to find combinations of plugins to complete a query
			#for missing in explicit_vars.values() :
				#if missing[-1] == list :
					#if missing not in plugin['outputs'] and missing[0:-1] not in plugin['outputs'] :
						#return False
				#else :
					#if missing not in plugin['outputs'] :
						#return False
			#return True
		
		#if testplugin(sumplugin, given_vars, explicit_vars) :
			#return sumplugin['function'](query)
		
		# start with vars whose path is [] or [list]
		verification = self.verify_restrictions(results, explicit_vars, implicit_vars, root_subject)
		# print 'verification:',verification
		
		return verification
		# return SPARQL, triples, explicit_vars, implicit_vars
		# return SPARQL, explicit_vars, implicit_vars

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
			# query = self.python_to_SPARQL(query)
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
			ret += '%s %s %s . ' % (root, k_str, v_str)
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
		
	def write(self, query) :
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
			insert_str_uri = self.wrapGraph(insert_str_uri)
			where = self.wrapGraph(where)
			# print 'insert_str_uri',insert_str_uri
			if create == sparql.unless_exists :
				insert_str_bnode = self.python_to_SPARQL_long(insert, self._bnodeVar())
				if not self.ask("%s %s" % (where, insert_str_bnode)) :
					if self.debug :
						print "INSERT { %s } WHERE { %s }" % (insert_str_uri, where)
					else :
						self.doQuery("INSERT { %s } WHERE { %s }" % (insert_str_uri, where))
			elif create == sparql.unconditional :
				if self.debug :
					print "INSERT { %s } WHERE { %s }" % (insert_str_uri, where)
				else :
					self.doQuery("INSERT { %s } WHERE { %s }" % (insert_str_uri, where))
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
		self.doQuery("INSERT { %s }" % self.wrapGraph(triple))

	def register_plugin(self, plugin) :
		self.plugins.append(plugin)
		
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
	
	def has_already_executed(self, history, sumplugin, binding) :
		return [sumplugin, binding] in history
	
	def register_executed(self, history, sumplugin, binding) :
		history.append(copy.deepcopy([sumplugin, binding]))
		
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
	
	def testplugin(self, plugin, query) :
		# check that all of the plugin inputs match part of the query
		for triple in plugin[self.n.meta.input] :
			if not self.find_triple_match(triple, query) :
				return False, None
		
		# find all possible bindings for the meta_vars if any exist
		matches, bindings = self.bind_meta_vars(plugin[self.n.meta.input], query)
		
		#print '===>', matches, len(bindings), prettyquery(bindings)
		
		return matches, bindings
	
	def sub_bindings_value(self, value, bindings) :
		if value in bindings :
			return bindings[value]
		return value
	
	def sub_bindings_triple(self, triple, bindings) :
		return [self.sub_bindings_value(value, bindings) for value in triple]
	
	def sub_var_bindings(self, output, output_bindings) :
		for bindings in output_bindings :
			yield [self.sub_bindings_triple(triple, bindings) for triple in output]
		
	# the implementation of this depends on the search method.  Start from the end
	# or from the begining?
	# for now, just start from the begining.  Evaluate all functions as they come
	# rather than defering it.
	def eval_plugins(self, query, history = []) :
		n = self.n
		
		for sumplugin in self.plugins :
			self.vars = {}
			matches, bindings = self.testplugin(sumplugin, query)
			if matches :
				for binding in bindings :
					if not self.has_already_executed(history, sumplugin, binding) :
						#print '(sumplugin, binding)',prettyquery([sumplugin, binding]),
						self.register_executed(history, sumplugin, binding)
						self.vars = binding
						# print 'testplugin!', prettyquery(self.vars)
						#self.vars = dict([(var[len(n.var):], v) for var, v in self.vars.iteritems()])
						
						output_bindings = sumplugin[n.meta.function](self.vars)
						if output_bindings == None :
							output_bindings = self.vars
						if type(output_bindings) == dict :
							output_bindings = [output_bindings]
						
						#print 'self.vars',prettyquery(self.vars)
						#print 'output_bindings',prettyquery(output_bindings),
						#print 'sumplugin[n.meta.output]',prettyquery(sumplugin[n.meta.output]),
						output = self.sub_var_bindings(sumplugin[n.meta.output], output_bindings)
						output = [x for x in output]
						output = output[0]
						#print 'output',prettyquery(output),
						output = self.sub_var_bindings(output, [self.vars])
						#print 'output',prettyquery(output),
						#print
						print 'name',sumplugin[n.meta.name]
						yield output
	
	def find_paths(self, query, find_vars) :
		for possible_translation in possible_translations :
			something = find_paths(possible_translation, find_vars)
	
	# return all triples which have at least one var
	def find_var_triples(self, query) :
		return [triple for triple in query if any(map(lambda x:self.is_var(x), triple))]
	
	def read_plugins_helper(self, query, var_triples, bound_var_triples = [], history = []) :
		# try a bredth first search:
		nexts = []
		for outtriple_sets in self.eval_plugins(query, history) :
			for outtriple_set in outtriple_sets :
				new_var_triples = [var_triple for var_triple in var_triples if not self.find_triple_match(var_triple, outtriple_set)]
				
				new_bound_var_triples = copy.deepcopy(bound_var_triples)
				new_bound_var_triples.extend(outtriple_set)
				
				if len(new_var_triples) == 0 :
					yield new_bound_var_triples
				else :
					new_query = copy.deepcopy(query)
					new_query.extend(outtriple_set)
					nexts.append(self.read_plugins_helper(new_query, new_var_triples, new_bound_var_triples))
		
		for next in nexts :
			for result in next :
				yield result
		
		## for now, just do a depth first search through all possible states (after
		## evaluating them
		#for outtriple_sets in self.eval_plugins(query) :
			#for outtriple_set in outtriple_sets :
				##print 'outtriple_set',prettyquery(outtriple_set),
				##print 'var_triples',prettyquery(var_triples),
				#new_var_triples = [var_triple for var_triple in var_triples if not self.find_triple_match(var_triple, outtriple_set)]
				##print prettyquery(new_var_triples),
				
				#new_query = copy.deepcopy(query)
				#new_query.extend(outtriple_set)
				##print 'new_query',prettyquery(new_query)
				##print 'len(new_var_triples)', len(new_var_triples)
				
				#if len(new_var_triples) == 0 :
					#yield new_query
				#else :
					#for result in self.read_plugins_helper(new_query, new_var_triples) :
						#yield result
	
	def read_plugins(self, query, find_vars = []) :
		vars = self.find_vars(query)
		if find_vars == [] :
			find_vars = vars
		
		var_triples = self.find_var_triples(query)
		
		return self.read_plugins_helper(query, var_triples)
		
		# look for all possible routes through the plugins to see which paths
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
	
	def py_to_SPARQL(self, object) :
		if type(object) == URIRef :
			if object.find(self.n.var) != -1 :
				return '?'+object[len(self.n.var):]
		return self.python_to_n3(object)

	def new_read(self, query, expected_vars = []) :
		vars = self.find_vars(query)
		
		query_str = ""
		for triple in query :
			triple = [self.py_to_SPARQL(x) for x in triple]
			triple_str = "%s %s %s .\n" % tuple(triple)
			query_str += triple_str
		
		ret = self.doQuery("SELECT * WHERE { %s }" % self.wrapGraph(query_str))
		# TODO: extract out the result bindings
		return ret




























"""

		fragment {
			uri : {
				n.feed.entry : {
					n.sparql.create : n.sparql.unless_exists,
					n.entry['title'] : entry.title,
					n.entry.date : entry.updated_parsed,
					n.entry.content : entry.content[0].value
				}
			}
		}
		
		"%s feed:entry [
		   entry:title 'title' ;
			 entry:date 123 ;
			 entry:content 'blah blah' 
		 ]
		" % uri
		
		query = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : {
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			}
		}
		WHERE = "?uri feed:url 'url' ."
		INSERT = "?uri feed:entry [
								entry:title 'title' ;
								entry:date 'date' ;
								entry:content 'content'
							] ."
		
		if not query("ASK { %s %s }" % (WHERE, INSERT)) :
			do("INSERT { %s	} WHERE {	%s	}" % (INSERT, WHERE))
		
		query = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : [{
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			},{
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			}]
		}
		WHERE = "?var1 feed:url 'url' ."
		INSERT = ["?var1 feed:entry [
									entry:title 'title' ;
									entry:date 'date' ;
									entry:content 'content'
								] .",
							"?var1 feed:entry [
									entry:title 'title2' ;
									entry:date 'date2' ;
									entry:content 'content2'
								] ."]
		
		query = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : {
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			},
			n.feed.somethingelse : {
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			}
		}
		BASE = {
			n.feed.url : entry.content[0].base,
			n.sparql.var : 1,
			n.sparql.insert : [{
				n.sparql.predicate : n.feed.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			}, {
				n.sparql.predicate : n.feed.somethingelse,
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			}
		}
		WHERE = "?uri feed:url 'url' ."
		INSERT = ["?uri feed:entry [
									entry:title 'title' ;
									entry:date 'date' ;
									entry:content 'content'
								] .",
							"?uri feed:somethingelse [
									entry:title 'title2' ;
									entry:date 'date2' ;
									entry:content 'content2'
								] ."]
		
		query = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : {
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			},
			n.feed.friend : {
				n.feed.entry : {
					n.sparql.create : n.sparql.unless_exists,
					n.entry['title'] : entry2.title,
					n.entry.date : entry2.updated_parsed,
					n.entry.content : entry2.content[0].value
				}
			}
		}
		BASE = {
			n.feed.url : entry.content[0].base,
			n.feed.friend : {
				n.sparql.var 2
			},
			n.sparql.var : 1,
			n.sparql.insert : [{
				n.sparql.subject : 1,
				n.sparql.predicate : n.feed.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			},{
				n.sparql.subject : 2,
				n.sparql.predicate : n.feed.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			}]
		}
		WHERE = "?var1 feed:url 'url' .
						 ?var1 feed:friend ?var2 ."
		INSERT = ["?var1 feed:entry [
									entry:title 'title' ;
									entry:date 'date' ;
									entry:content 'content'
								] .",
							"?var2 feed:entry [
									entry:title 'title2' ;
									entry:date 'date2' ;
									entry:content 'content2'
								] ."]
		
		query = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : [{
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			},{
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			}]
		}
		BASE = {
			n.feed.url : entry.content[0].base,
			n.feed.entry : {
				n.entry['title'] : entry2.title,
				n.entry.date : entry2.updated_parsed,
				n.entry.content : entry2.content[0].value
			},
			n.sparql.var : 1,
			n.sparql.insert : {
				n.sparql.predicate : n.feed.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.entry['title'] : entry.title,
				n.entry.date : entry.updated_parsed,
				n.entry.content : entry.content[0].value
			}
		}
		WHERE = "?var1 feed:url 'url' .
						 ?var1 feed:entry [
								entry:title 'title2' ;
								entry:date 'date2' ;
								entry:content 'content2'
							] ."
		INSERT = "?var1 feed:entry [
								entry:title 'title' ;
								entry:date 'date' ;
								entry:content 'content'
							] ."
		
		# in an object with a child1 insert a new object 
		fragment = {
			n.e.child1 : {
				n.e.child2 : {
					n.sparql.create : n.sparql.unless_exists,
					n.e.prop : 123
				}
			}
		}
		"SELECT DISTINCT ?uri
		WHERE {
			?var1 e:child ?uri .
		}"
		
		fragment = {
			n.e.child1 : {
				n.e.child2 : {
					n.sparql.create : n.sparql.unless_exists,
					n.e.prop : 123
				},
				n.e.prop 456
			}
		}
		"SELECT DISTINCT ?uri
		WHERE {
			?var1 e:child ?uri .
			?uri e:prop 456 .
		}"
		"INSERT {
			?uri e:child2 
		} WHERE {
		}"
		# problem is that ?uri might be a bnode ... what then? then you really need
		# SPARUL, yeah, so ... oh yeah ... but ... can not insert a blank node with
		# Jena SPARUL ... god damn it
		fragment = {
			n.schema.property : {
				n.schema_property.type : None,
				n.schema_property.type : None
				n.schema.test : {
					n.sparql.connect : n.sparql.insert,
					n.sparql.value : 'this is a test'
				}
			},
			n.rdf.type : n.schema.type
		}
		"INSERT {
			?uri schema:test 'this is a test' .
		} WHERE {
			?x schema:property ?uri .
				?uri schema_property:type ?var1 ;
				schema_property:default ?var2 .
			?x rdf:type schema:type .
		}"

		
		print self.sparql.write(fragment)

"""














"""

the provides data structure could be quite complex or quite simple.  Extra 
complexity can be added with extra details and requirements about the input and
output types.  For now, simply define them as inputs or outputs.  Later these
could get more interesting.

last.fm plugin provides :
	{
		n.lastfm.artist : n.transform.input,
		n.lastfm.number_of_listeners : n.transform.output,
		n.lastfm.number_of_listens : n.transform.output,
		n.lastfm.similar_artist : [{
			n.lastfm.artist : n.transform.output,
			n.lastfm.similarity_measure : n.transform.output
		}]
		...
		n.transform.guarenteed_output : False
	}
	
	inputs:
		[n.lastm.artist]
	outputs:
		[n.lastfm.number_of_listeners]
		[n.lastfm.number_of_listens]
		[n.lastfm.similar_artist, list, n.lastfm.artist]
		[n.lastfm.similar_artist, list, n.lastfm.similarity_measure]
	
query:
	{
		n.lastfm.artist : 'The New Pornographers',
		n.lastfm.similar_artist : [{
			n.lastfm.artist : None
		}],
		n.x.prop : []
	}
	
	inputs (provided) : (given_vars)
		[n.lastfm.artist]
	outputs (missing) : (explicit_vars)
		[n.lastfm.similar_artist, list, n.lastfm.artist]
		[n.x.prop, list]
		


to determine if a query matches the plugin :
	for all input variables required by the plugin, the query must provide a value
	for all missing values in the query, the plguin must provide an output (of the
		correct type.  Possible types :
			literal, list of literals, object, list of objects
		if the query expects a list, just one is fine
		if the plugin expects a list, just one is fine
	
NOTE: extra speed might be possible by using a heuristic which keeps track of 
	which values are most descriminatory.  If a plugin requires multiple inputs
	to be provided, some might provide more descriminatory power than the others.
NOTE: extra speed might also be possible through some kind of hashing of the 
	variables.  The basic algorithm is an attempt to match two sets of lists from
	both the query and the output.  Could build a decision tree where each branch
	is a test about the query having a specific input or output.  The decision 
	tree could be organized in such a way that more often query/plugin matches
	require the fewest number of branches.

NOTE: social: keep track of which plugin inputs and outputs are commonly paired
	(given life)


"""