from CompilationPass import CompilationPass
import copy
import PrettyQuery
prettyquery = PrettyQuery.prettyquery

from SimpleSPARQL import Namespaces
from QueryException import QueryException
from PassUtils import dictrecursiveupdate

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('var', '<http://dwiel.net/express/var/0.1/>')

"""
TODO: allow for the many flag to not throw an error if there are many possible
URIs to bind a write to.
"""

class PassCompleteReads(CompilationPass) :
	def __init__(self, sparql) :
		self.sparql = sparql
	
	def __call__(self, query) :
		"""
		read each read query from the database and replace the query with the result
		"""
		newreads = []
		for i, q in enumerate(query[n.sparql.reads]) :
			try :
				# find all n.sparql.vars and temporarily remove them.  store them in a 
				# path -> varname mapping while inlimbo
				path = q[n.sparql.path]
				del q[n.sparql.path]
				path_to_varname = self.path_to_varname_from_query(q)
				rawret = self.sparql.read_raw(q)
				dictrecursiveupdate(q, rawret)
				self.replace_vars_in_query(q, path_to_varname)
				q[n.sparql.path] = path
				newreads.append(q)
			except QueryException, qe:
				raise QueryException(path + qe.path, qe.message, (n.sparql.reads, i) + qe.path)
		query[n.sparql.reads] = newreads
		
		return query

	def path_to_varname_from_query(self, q, path = ()) :
		"""
		given a query, return a mapping from path to varname.  Also remove n.sparql.vars from query.  path is the path so far.
		"""
		path_to_varname = {}
		if type(q) == dict :
			# if this object doesn't have a subject value, add a missing one so it 
			# gets filled in
			if n.sparql.subject not in q :
				q[n.sparql.subject] = None
			# if this object has a var, put it into the dict and remove it
			if n.sparql.var in q :
				path_to_varname[path] = q[n.sparql.var]
				del q[n.sparql.var]
			# recur
			for k, qi in q.iteritems() :
				path_to_varname.update(self.path_to_varname_from_query(qi, path + (k,)))
		elif type(q) == list :
			# recur
			for i, qi in enumerate(q) :
				path_to_varname.update(self.path_to_varname_from_query(qi, path + (i,)))
		
		return path_to_varname
	
	def replace_vars_in_query(self, q, path_to_varname) :
		"""
		given a query and a map from path to varname, insert (n.sparql.var, varname)
		key value pairs into the query at the given path
		"""
		for path, varname in path_to_varname.iteritems() :
			dictpath(q, path)[n.sparql.var] = varname


















