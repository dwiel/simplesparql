from CompilationPass import CompilationPass
#from PrettyQuery import prettyquery
import PrettyQuery
prettyquery = PrettyQuery.prettyquery

import copy

from SimpleSPARQL import Namespaces

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('var', '<http://dwiel.net/express/var/0.1/>')

class PassExtractWriteQueries(CompilationPass) :
	"""
	move all write directives and key value pairs which are to be written to 
  write directives in the root.  If a read object becomes completely disconnected 
  in this process, make the root a list of distinct obejcts
  * move each write object into a list at the root.  Keep track of the subject 
    variable name
	"""
	def __call__(self, query) :
		self.reads = []
		self.writes = []
		
		self.missing_subject_var = 0
		self.do(query, False, ())
		
		return {
			n.sparql.reads : self.reads,
			n.sparql.writes : self.writes
		}
	
	def next_missing_subject_var(self) :
		self.missing_subject_var += 1
		return '?autovar_missing_subject%d' % self.missing_subject_var
	
	def do(self, query, inread, path) :
		"""
		A read query will only be added to the reads list if inread is False
		path is the current path in the query
		"""
		if type(query) == list :
			query = [self.do(copy.copy(x), inread, path + (i,)) for i, x in enumerate(query)]
			if None in query :
				query = [x for x in query if x is not None]
				if query == [] :
					query = None
				else :
					# find a subquery with no subject and set it to None:
					found = False
					for q in query :
						if n.sparql.subject not in q :
							q[n.sparql.subject] = None
							found = True
							break
						elif q[n.sparql.subject] == None :
							found = True
							break
					if not found :
						# create a new query object to find the subjects
						query.append({
							n.sparql.subject : None,
							n.sparql.var : self.next_missing_subject_var()
						})
		elif type(query) == dict :
			if n.sparql.create in query :
				# disconnect sub-queries
				for k in query :
					v = query[k]
					if type(v) == dict :
						self.do(v, False, path + (k,))
						query[k] = None
					elif type(v) == list :
						query[k] = [self.do(x, False, path + (k,)) for x in query]
				# move query to writes
				query[n.sparql.path] = path
				self.writes.append(query)
				return None
			else :
				for k in query :
					query[k] = self.do(query[k], True, path + (k,))
				
				if not inread :
					query[n.sparql.path] = path
					self.reads.append(query)
		
		return query





