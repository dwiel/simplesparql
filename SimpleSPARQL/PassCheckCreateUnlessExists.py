from CompilationPass import CompilationPass
import copy
import PrettyQuery
prettyquery = PrettyQuery.prettyquery

from SimpleSPARQL import Namespaces
from QueryException import QueryException
from PassUtils import dictmask

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('var', '<http://dwiel.net/express/var/0.1/>')

class PassCheckCreateUnlessExists(CompilationPass) :
	def __init__(self, sparql) :
		self.sparql = sparql
		
	def __call__(self, query) :
		for i, q in enumerate(query[n.sparql.writes]) :
			# if this is a create unless_exists query
			if n.sparql.create in q and q[n.sparql.create] == n.sparql.unless_exists :
				diff = dictmask(q, [n.sparql.create, n.sparql.var, n.sparql.path])
				if n.sparql.subject not in q :
					q[n.sparql.subject] = None
				res = self.sparql.read(q)
				if res[n.sparql.status] == n.sparql.ok :
					# it already exists, connect to the existing instead
					# aka: set n.sparql.subject to the existing subject
					q.update(res[n.sparql.result])
					diff[n.sparql.create] = n.sparql.existed
				elif res[n.sparql.error_message] == 'no match found' :
					# del q[n.sparql.error_inside]
					diff[n.sparql.create] = n.sparql.create
					# it doesn't yet exist, create it, then connect to it
				elif res[n.sparql.error_message] == 'too many values' :
					# del q[n.sparql.error_inside]
					# diff[n.sparql.create] = n.sparql.many_exist
					raise QueryException(diff[n.sparql.path] + res[n.sparql.error_path], 'many exist', (n.sparql.writes, i) + res[n.sparql.error_path])
				else :
					raise QueryException(res[n.sparql.error_path], res[n.sparql.error_message])
				q.update(diff)
			# if this is a create unless_connected query
			elif n.sparql.create in q and q[n.sparql.create] == n.sparql.unless_connected :
				# TODO: harder for many ... do later
				# TODO: assuming not many, get URI of parent object and predicate
				#       connecting it to this new object.
				
				# find the predicate from the path
				if len(q[n.sparql.path]) == 0 :
					raise QueryException(q[n.sparql.path], 'can not create unless_connected unless the created object has a parent object in the query')
				elif type(q[n.sparql.path][-1]) == int :
					if len(q[n.sparql.path]) == 1 :
						raise QueryException(q[n.sparql.path], 'can not create unless_connected unless the created object has a parent object in the query')
					else :
						predicate = q[n.sparql.path][-2]
						predicate_i = -2
				else :
					predicate = q[n.sparql.path][-1]
					predicate_i = -1
				
				# find the subject/parent from the path.  The subject of the dict after 
				#  following the path leading up to the predicate
				parent = self.findpath(query, q[n.sparql.path][:predicate_i])[n.sparql.subject]
				
				diff = dictmask(q, [n.sparql.create, n.sparql.var, n.sparql.path])
				q = {n.sparql.subject : parent, predicate : q}
				if n.sparql.subject not in q[predicate] :
					q[predicate][n.sparql.subject] = None
				res = self.sparql.read(q)
				if res[n.sparql.status] == n.sparql.ok :
					diff[n.sparql.create] = n.sparql.connect
					diff[n.sparql.subject] = res[n.sparql.result][predicate][n.sparql.subject]
					# it already exists, connect to the existing instead
				else :
					diff[n.sparql.create] = n.sparql.create
					# it doesn't yet exist, create it, then connect to it
				q = q[predicate]
				q.update(diff)
			elif n.sparql.create in q and q[n.sparql.create] == n.sparql.force :
				q[n.sparql.create] = n.sparql.create
		
		return query
				
	def pathinquery(self, q, path) :
		for ele in path :
			if ele in q :
				q = q[ele]
			else :
				return None
		return q
	
	def findpath(self, query, path) :
		for q in query[n.sparql.reads] :
			# make sure the query path isn't longer than the search path
			if len(q[n.sparql.path]) >= len(path) :
				# if the search path starts with the query path
				if path[:len(q[n.sparql.path])] == q[n.sparql.path] :
					value = self.pathinquery(q, path[len(q[n.sparql.path]):])
					if value :
						return value
		raise Exception('couldnt find path %s in query %s' % (repr(path), prettyquery(query)))
					
				




