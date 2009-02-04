from Namespaces import Namespaces
from PrettyQuery import prettyquery

from rdflib import URIRef

import time, copy

n = Namespaces()
n.bind('var', '<http://dwiel.net/express/var/0.1/>')
n.bind('meta_var', '<http://dwiel.net/express/meta_var/0.1/>')
n.bind('lit_var', '<http://dwiel.net/express/lit_var/0.1/>')
n.bind('out_var', '<http://dwiel.net/express/out_var/0.1/>')
n.bind('out_lit_var', '<http://dwiel.net/express/out_lit_var/0.1/>')
n.bind('bnode', '<http://dwiel.net/axpress/bnode/0.1/>')

def is_any_var(data) :
	if type(data) == URIRef :
		if data.find(n.var) == 0 :
			return True
		elif data.find(n.meta_var) == 0 :
			return True
		elif data.find(n.lit_var) == 0 :
			return True
		elif data.find(n.out_var) == 0 :
			return True
		elif data.find(n.out_lit_var) == 0 :
			return True
	return False

def is_var(data) :
	if type(data) == URIRef :
		if data.find(n.var) == 0 :
			return True
	return False

def is_meta_var(data) :
	if type(data) == URIRef :
		if data.find(n.meta_var) == 0 :
			return True
	return False

def is_lit_var(data) :
	if type(data) == URIRef :
		if data.find(n.lit_var) == 0 :
			return True
	return False	

def is_out_var(data) :
	if type(data) == URIRef :
		if data.find(n.out_var) == 0 :
			return True
	return False
	
def is_out_lit_var(data) :
	if type(data) == URIRef :
		if data.find(n.out_lit_var) == 0 :
			return True
	return False

def var_name(uri) :
	if uri.find(n.var) == 0 :
		return uri[len(n.var):]
	elif uri.find(n.meta_var) == 0 :
		return uri[len(n.meta_var):]
	elif uri.find(n.lit_var) == 0 :
		return uri[len(n.lit_var):]
	elif uri.find(n.out_var) == 0 :
		return uri[len(n.out_var):]
	elif uri.find(n.out_lit_var) == 0 :
		return uri[len(n.out_lit_var):]
	else :
		raise Exception('data is not a variable' % str(uri))

def var_type(uri) :
	if uri.find(n.var) == 0 :
		return n.var
	elif uri.find(n.meta_var) == 0 :
		return n.meta_var
	elif uri.find(n.lit_var) == 0 :
		return n.lit_var
	elif uri.find(n.out_var) == 0 :
		return n.out_var
	elif uri.find(n.out_lit_var) == 0 :
		return n.out_lit_var
	else :
		raise Exception('data is not a variable' % str(uri))

def var(data) :
	if is_any_var(data) :
		return data[len(n.var):]
	return None

def sub_bindings_value(value, bindings) :
	if is_any_var(value) and var_name(value) in bindings :
		return bindings[var_name(value)]
	return value
	
def sub_bindings_triple(triple, bindings) :
	return [sub_bindings_value(value, bindings) for value in triple]

def explode_binding(bindings) :
	list_of_new_bindings = [{}]
	for var, value in bindings.iteritems() :
		if type(value) == list :
			# each value in the list of values is a new set of bindings
			new_list_of_new_bindings = []
			for v in value :
				for new_bindings in list_of_new_bindings :
					tmp_new_bindings = copy.copy(new_bindings)
					tmp_new_bindings[var] = v
					new_list_of_new_bindings.append(tmp_new_bindings)
			list_of_new_bindings = new_list_of_new_bindings
		elif type(value) == tuple :
			# each value in the tuple of values is simultaneous
			for new_bindings in list_of_new_bindings :
				# TODO: this is like the explode from before ... need a Bindings class
				# if there are to actually be mutliple values for each variable/key
				new_bindings[var] = value
		else :
			for new_bindings in list_of_new_bindings :
				new_bindings[var] = value
	return list_of_new_bindings

def explode_bindings_set(bindings_set) :
	if isinstance(bindings_set, dict) :
		bindings_set = [bindings_set]
	
	# explode the bindings_set which have multiple values into multiple
	# bindings
	new_bindings_set = []
	for bindings in bindings_set :
		#print 'bindings',prettyquery(bindings)
		new_bindings_set.extend(explode_binding(bindings))
	
	return new_bindings_set
	
def new_explode_bindings_set(bindings_set) :
	if isinstance(bindings_set, dict) :
		bindings_set = [bindings_set]
	
	# explode the bindings_set which have multiple values into multiple
	# bindings
	new_bindings_set = []
	for bindings in bindings_set :
		new_bindings = explode_binding(bindings)
		if len(new_bindings) == 1 :
			new_bindings_set.extend(new_bindings)
		else :
			new_bindings_set.append(new_bindings)
	return new_bindings_set
	
def sub_var_bindings(triples, bindings_set) :
	"""
	Substitutes each of the bindings into the set of triples.  bindings_set may
		look like:
		[
			{
				'varname' : [1, 2, 3]
			}
		]
		which is equivelent to:
		[	{ 'varname' : 1 },
			{ 'varname' : 2 },
			{ 'varname' : 3 } ]
		which is why this function takes in a set of bindings and returns a set of
		triple_sets rather than just doing one at a time.
	@arg triples is the set of triples to substitute the bindings into
	@arg bindings_set is the set of bindings to substitute into the triples
	@return a generator of triple_sets with bindings substituted in.
	"""
	
	#print 'triples',prettyquery(triples)
	#print 'bindings',prettyquery(bindings_set)
	
	bindings_set = explode_bindings_set(bindings_set)
	
	for bindings in bindings_set :
		new_triples = []
		for triple in triples :
			new_triples.append([bound_triple for bound_triple in sub_bindings_triple(triple, bindings)])
		yield new_triples



def find_vars(query, is_a_var = is_any_var) :
	"""
	given a query, find the set of names of all vars, meta_vars and lit_vars
	"""
	try :
		iter = query.__iter__()
	except AttributeError :
		if is_a_var(query) :
			return set([var_name(query)])
		return set()
	
	vars = set()
	for i in iter :
		vars.update(find_vars(i, is_a_var))
	return vars







class UniqueURIGenerator() :
	def __init__(self, namespace = n.bnode, prefix = 'bnode') :
		self.namespace = namespace
		self.prefix = prefix
		self.i = 0
	
	def __call__(self, namespace = None, prefix = None) :
		if namespace == None :
			namespace = self.namespace
		if prefix == None :
			prefix = self.prefix
		
		# incase multiple calls happen in the same time.time()
		self.i += 1
		
		postfix = str(time.time()).replace('.','')
		return namespace[prefix+postfix+str(self.i)]
	



import string

# Load dictionary of entities (HTML 2.0 only...)
#from htmlentitydefs import entitydefs
# Here you could easily add more entities if needed...
entitydefs = {
	'gt' : '>',
	'lt' : '<',
}

def html_encode(s):
	s = string.replace(s,"&","&amp;")  # replace "&" first
	
	#runs one replace for each entity except "&"
	for (ent,char) in entitydefs.items():
		if char != "&": 
			s = string.replace(s,char,"&"+ent+";")
	return s

spaces = ''

def p(*args) :
	print '%s%s' % (spaces, ' '.join([prettyquery(arg) for arg in args]))

def debug(name, obj=None) :
	name = name.replace(' ','_')
	print '%s<%s>%s</%s>' % (spaces, name, html_encode(prettyquery(obj)), name)

def logger(f, name=None):
	if name is None:
		name = f.func_name
	def wrapped(*args, **kwargs):
		global spaces
		print '%s<%s>' % (spaces, name)
		spaces += ' '
		#print '\targs:%s' % prettyquery(args)
		#print '\tkwargs:%s' % prettyquery(kwargs)
		#logger.fhwr.write("***"+name+" "+str(f)+"\n"\
						#+str(args)+str(kwargs)+"\n\n")
		result = f(*args, **kwargs)
		#print '\nret:%s' % prettyquery(result)
		spaces = spaces[:-1]
		print '%s</%s>' % (spaces, name)
		return result
	wrapped.__doc__ = f.__doc__
	return wrapped













