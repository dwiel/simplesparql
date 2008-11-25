from rdflib import *

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

