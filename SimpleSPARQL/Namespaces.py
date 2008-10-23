from rdflib import Namespace
import re

class Namespaces() :
	namespaces = {}

	def bind(self, prefix, namespace) :
		if not isinstance(namespace, Namespace) :
			if type(namespace) == str or type(namespace) == unicode :
				if namespace[:1] == '<' and namespace[-1:] == '>' :
					namespace = namespace[1:-1]
			namespace = Namespace(namespace)
		if isinstance(namespace, Namespace) :
			self.namespaces[prefix] = namespace

	def SPARQL_PREFIX(self) :
		str = ''
		for prefix,namespace in self.namespaces.iteritems() :
			str += 'PREFIX %s: <%s> ' % (prefix, namespace)
		return str

	def n3_prefix(self) :
		s = ''
		for prefix,namespace in self.namespaces.iteritems() :
			s += '@prefix %s: <%s> .\n' % (prefix, namespace)
		return str(s)
	n3 = n3_prefix
	
	def matches(self, uri) :
		for prefix in self.namespaces.keys() :
			if re.match(prefix+":([^ .\}]+)", uri) :
				return True
		return False
	
	def __getitem__(self, key) :
		return self.namespaces[key]
	
	def __setitem__(self, key, value) :
		self.bind(key, value)
	
	def __getattr__(self, key) :
		return self[key]

	def __iter__(self) :
		return self.namespaces.__iter__()
	
	def iteritems(self) :
		return self.namespaces.iteritems()




n = Namespaces()	

def globalNamespaces() :
	return n


















