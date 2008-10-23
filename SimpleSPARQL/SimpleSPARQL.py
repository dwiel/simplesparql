"""
SimpleSPARQL provides some high level access to some basic SPARQL queries
TODO: clean up parts of code left from axpress (update_uri)
"""

import time, re, copy, datetime
from SPARQLWrapper import *
from rdflib import *
from urllib import urlopen, urlencode

import rdflib
import rdflib.sparql.parser

import Namespaces

# from parseMatchOutput import construct

class SimpleSPARQL (SPARQLWrapper) :
	def __init__(self, baseURI, returnFormat=None, defaultGraph=None, sparul=None):
		SPARQLWrapper.__init__(self, baseURI, returnFormat, defaultGraph)
		if sparul :
			self.setSPARUL(sparul)
		else :
			self.setSPARUL(baseURI.replace('sparql', 'sparul'))
		self.n = Namespaces.Namespaces()
	
	def setSPARUL(self, baseURI, returnFormat=None, defaultGraph=None):
		self.sparul = SPARQLWrapper(baseURI, returnFormat, defaultGraph)
	
	def setNamespaces(self, n):
		self.n = n
	
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
		query = query.replace("\\n",' ')
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
		query = query.replace('\n', '\\n')
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)
		# print "query", query
		if query_type == "SELECT" :
			return sparql.query().convert()
		elif query_type == "ASK" :
			return sparql.query().convert()['boolean']
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
				print bindings
				pattern.construct(c, bindings)
				yield RDFObject(c, self.n.e['uri'], self)

	def doShortQueryURI(self, query) :
		return self.doQueryURI("""SELECT DISTINCT ?uri WHERE { %s . }""" % query)
	
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
		ret = self.doQuery("""
		INSERT { %s ?s ?o }
		WHERE { %s ?s ?o }
		DELETE { %s ?s ?o }
		WHERE { %s ?s ?o }
		""" % (dest.n3(), src.n3(), src.n3(), src.n3()))

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
		if type(data) == int or type(data) == float :
			return unicode(data)
		elif type(data) == str or type(data) == unicode:
			if type(data) == str :
				data = unicode(data)
			if self.n.matches(data) :
				return data
			else :
				if '"' not in data :
					return u'"'+data+u'"'
				if "'" not in data :
					return u"'"+data+u"'"
				if '"""' not in data :
					return u'"""'+data+u'"""'
				if "'''" not in data :
					return u"'''"+data+u"'''"
				raise Exception("can't figure out how to put this in quotes...")
		elif type(data) == dict :
			key_value_pairs = [(self.python_to_n3_helper(key, long_format, path, bound_vars), self.python_to_n3_helper(value, long_format, self.flatten([path, key]), bound_vars)) for (key, value) in data.iteritems()]
			key_value_pairs_str = map(lambda (p):p[0]+u' '+p[1], key_value_pairs)
			return u'[ ' + u' ; '.join(key_value_pairs_str) + u' ]'
		elif data == [] :
			self.variable += 1
			varname = u'?var' + unicode(self.variable)
			bound_vars[varname[1:]] = self.flatten([path, list])
			return varname			
		elif type(data) == list :
			return u', '.join(map(lambda x:self.python_to_n3_helper(x, long_format, self.flatten([path, list]), bound_vars), data))
		elif type(data) == datetime.datetime :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % (data.year, data.month, data.day, data.hour, data.minute, data.second)
		elif type(data) == time.struct_time :
			return u'"%d-%d-%dT%d:%d:%dT"^^xsd:dateTime' % data[0:6]
		elif type(data) == rdflib.URIRef :
			return data.n3()
		elif data == None :
			self.variable += 1
			varname = u'?var' + unicode(self.variable)
			bound_vars[varname[1:]] = path
			return varname
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
	
	def read(self, data) :
		bound_vars = {}
		results = self.doQuery("SELECT * WHERE { %s }" % self.python_to_SPARQL(data, Variable("uri"), bound_vars))
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
		results = self.doQuery("SELECT * WHERE { %s }" % self.python_to_SPARQL(data, Variable("uri")))
		for rawbindings in results['results']['bindings'] :
			for key, value in rawbindings.iteritems() :
				if key != u'uri' :
					if value['type'] == 'bnode' :
						raise Exception("can not bind a bnode to a variable")
					yield value['value']

	def ask(self, query) :
		if type(query) == dict :
			query = self.python_to_SPARQL(query)
		return self.doQuery("ASK { %s }" % query)
	
	# remove dicts with pairs like n.sparql.create : n.sparql.unless_exists with a
	# n.sparql.var : 1
	# bound_vars is an integer of where the variables should start being bound to
	def _preprocess_query_helper(self, query, bound_vars, inserts) :
		sparql = self.n.sparql
		if type(query) == dict :
			newquery = {}
			for k, v in query.iteritems() :
				if k == sparql.create :
					return None, copy.copy(query)
				if type(v) == dict :
					v2, insert = self._preprocess_query_helper(v, bound_vars, inserts)
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
					if v2 is not None :
						newquery[k] = v2
				elif type(v) == list :
					for vi in v :
						vi2, insert = self._preprocess_query_helper(vi, bound_vars, inserts)
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
						if vi2 is not None :
							if k not in newquery :
								newquery[k] = []
							newquery[k].append(vi2)
				else :
					newquery[k] = v
			return newquery, None
		elif type(query) == list :
			return [self._preprocess_query_helper(queryi, bound_vars, inserts) for queryi in query]
	
	def _preprocess_query(self, query) :
		"""put n.sparql.var : # pairs in all dicts whose root need to have a 
		variable name.  Move all inserts/creates/writes into a list of 
		n.sparql.insert in the root of the query.  Each insert has the original dict
		to write plus, a n.sparql.subject : # which is the root variable and an 
		n.sparql.predicate which is the predicate of the tripe to add (where the
		rest of the dictionary describes the object of the triple
		"""
		sparql = self.n.sparql
		if type(query) is not dict :
			raise Exception('query must be a dictionary')
		
		inserts = []
		bound_vars = [1]
		query, insert = self._preprocess_query_helper(query, bound_vars, inserts)
		if insert :
			query = {}
			var = bound_vars[0]
			bound_vars[0] += 1
			
			query[sparql.var] = var
			insert[sparql.subject] = None
			insert[sparql.predicate] = None
			inserts.append(insert)
			
		# this happens when the root object is a create
		#if query is None and _ is not None :
			#query = _
		
		query[sparql.insert] = inserts
		
		return query
	
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
				root = '_:b'+str(var[0])
				var[0] += 1
			
			for k, v in query.iteritems() :
				if k == self.n.sparql.var :
					continue
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
			return self.python_to_n3(query), ""
	
	def python_to_SPARQL_long(self, query) :
		"""convert a python object into SPARQL format.  (this version doesn't use
		blank nodes, which is useful if you want to be able to append to or refer
		to the dictionaries converted
		"""
		return self.python_to_SPARQL_long_helper(query, [1])[1]
	
	def _extract_where(self, query) :
		"""given a query in the form described in _preprocess_query, return a WHERE
		clause to be used in the final SPARQL queries"""
		query = copy.copy(query)
		
		# discard the insert information
		if self.n.sparql.insert in query :
			del query[self.n.sparql.insert]
		
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
	
	def write(self, query) :
		sparql = self.n.sparql
		
		query = self._preprocess_query(query)
		where = self._extract_where(query)
		inserts = self._extract_inserts(query)
		
		#print 'where', where
		#print 'inserts', inserts
		
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
					""" % ('?var'+insert[sparql.var], where))
					if count != 1 :
						#print 'count not 1:', count
						# TODO: somehow pass this on to the return structure
						continue
					create.remove(sparql.only_once)
					create = create[0]
			
			insert_str = self.python_to_SPARQL_long(insert)
			# print 'insert_str',insert_str
			if create == sparql.unless_exists :
				if not self.ask("%s %s" % (where, insert_str)) :
					print 'do',self.doQuery("INSERT { %s } WHERE { %s }" % (insert_str, where))
			elif create == sparql.unconditional :
				print 'do',self.doQuery("INSERT { %s } WHERE { %s }" % (insert_str, where))
			else :
				raise Exception("unkown create clause: " + create)
		
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
		self.update_new_uri()
	
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
		self.doQuery("INSERT { %s %s %s }" % (subject, pred, object))

### TODO: assess viability of changing this to inherit from rdflib.Graph
class RDFObject :
	# g - graph with uri described in it
	# uri - cna be a uri or a bnode
	def __init__(self, g = None, uri = None, sparql = None) :
		self.sparql = sparql
		# newg keeps track of new triples so they can be saved later
		self.newg = ConjunctiveGraph()
		self.delkey = []
		if g == None :
			self.d = {}
			return
		elif type(g) == dict :
			self.g = ConjunctiveGraph()
			self.d = g
			if uri is not None :
				if type(uri) == unicode :
					uri = URIRef(uri)
				self.root = uri
			return
		else :
			self.d = {}
		# self.g = g
		self.g = ConjunctiveGraph()
		self.g += g
		if type(uri) == unicode :
			uri = URIRef(uri)
		self.root = uri
		for (p, o) in g.predicate_objects(uri) :
			if type(o) == BNode :
				o_dict = RDFObject(g, o)
			else :
				o_dict = o
			if not p in self.d :
				self.d[p] = [o_dict]
			else :
				self.d[p].append(o_dict)
	
	def __getitem__(self, key) :
		if key not in self.d :
			return []
		else :
			return self.d[key]
	
	"""
	type(key) == str
	type(value) == str, number, rdfo
	rdfo[key] = value =>
		self.__dict__[key] = [value]
	"""
	def __setitem__(self, key, value) :
		if type(value) == str or \
		   type(value) == int or \
			 type(value) == unicode or \
			 type(value) == float :
			self.newg.add((self.root, key, Literal(value)))
			self.g.add((self.root, key, Literal(value)))
			self.d[key] = [value]
		elif type(value) == list :
			for v in value :
				self.newg.add((self.root, key, Literal(v)))
				self.g.add((self.root, key, Literal(v)))
			self.d[key] = value
		elif type(value) == dict :
			bnode = BNode()
			for k,v in value.iteritems() :
				self.newg.add((bnode, k, Literal(v)))
				self.g.add((bnode, k, Literal(v)))
			self.newg.add((self.root, key, bnode))
			self.g.add((self.root, key, bnode))
			self.d[key] = [RDFObject(self.g, bnode)]
	
	def __delitem__(self, key) :
		self.delkey.append(key)
		del self.d[key]
	
	# TODO:
	# call transforms.attr(self) and return the result (assuming attr isn't a real
	# attribute like save, to_dict or g
	#def __getattr__(self, attr) :
		#print '__getattr__',attr
		#return RDFObject.__class__.__getattr__(self,attr)
	
	def save(self) :
		if self.sparql :
			for (s,p,o) in self.newg :
				self.sparql.insert_triple(s,p,o)
			self.newg = Graph()
		# TODO: write deletes out of self.delkey
	
	"""
	like [key], but if there are multiple values, will only return the first
	"""
	def __call__(self, key) :
		if key not in self.d :
			return None
		else :
			return self.d[key][0]
	
	def __iter__(self) :
		return self.d.__iter__()
	
	def iteritems(self) :
		return self.d.iteritems()
	
	def __str__(self) :
		return str(self.d)
	
	def to_dict(self) :
		d = {}
		for _k,_v in self.iteritems() :
			if type(_k) == URIRef :
				k = str(_k)
			else :
				k = _k
			
			if type(_v) == RDFObject :
				v = _v.to_dict()
			else :
				v = _v
				
			d[k] = v
		return d
	
	def ConnectedGraphURI(self, uri) :
		newg = ConjunctiveGraph()
		print type(uri), uri
		for p, o in self.g.predicate_objects(uri):
			print type(p), p
			print type(o), o
			newg.add((uri, p, o))
		return newg
	
	# returns a graph which only contains triples which are part of the object
	# defined by self.root 
	def ConnectedGraphRoot(self):
		return self.ConnectedGraphURI(self.root)

	def ConnectedGraphRootRDFObject(self):
		return RDFObject(self.ConnectedGraphRoot(), self.root, self.sparql)
	
	def ConnectedGraphURIRDFObject(self, uri):
		return RDFObject(self.ConnectedGraphURI(uri), uri, self.sparql)
	

class RDFObject2(ConjunctiveGraph):
	def __init__(self, g = None, uri = None, sparql = None):
		ConjunctiveGraph.__init__(self)
		self += g
		self.root = uri
		self.sparql = sparql
	
	def setRoot(uri):
		self.root = uri
	
	def __call__(self, key) :
		return self.objects(self.root, key)[0]

	def __getitem__(self, key) :
		return self.objects(self.root, key)
	
	def __setitem__(self, key, value) :
		self.add(self.root, key, value)
	
	def __delitem__(self, key) :
		self.remove(self.root, key, None)
	
	def iteritems(self) :
		return self.predicate_objects(self.root)





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