import copy, cPickle
from SimpleSPARQL import *

n = globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')

sparql = SimpleSPARQL("http://localhost:2020/sparql")
sparql.setGraph("http://dwiel.net/axpress/testing")
sparql.setNamespaces(n)

# passes = [PassWrapInList(), PassAssignVariableNumber(), PassExtractWriteQueries(), PassCompleteReads(sparql), PassCheckCreateUnlessExists(sparql)]
passes = [PassExtractWriteQueries(), PassCompleteReads(sparql), PassCheckCreateUnlessExists(sparql)]

class PassTest() :
	"""
	this is a testing framework build specifically for testing simplesparql.  The
	main idea is to be able to run a query, manually check that the output at each
	pass in the compiler is correct and then commit it to memory.  When the tests
	are run again in the future, all of the previous tests will be checked against
	the history to see if they are the same as when they were initially run.
	Managing all of the queries and the intermediate steps after each pass was
	becoming too combersome to do by hand.
	"""
	
	def __init__(self) :
		self.history = cPickle.load(open('history', 'rb'))
		self.failcount = 0
		self.successcount = 0

	def __del__(self) :
		self.printstats()
		cPickle.dump(self.history, open('history', 'wb'), -1)
	
	def printstats(self):
		print 'failures:',self.failcount
		print 'successes:',self.successcount
	
	def do(self, q, debug = True) :
		stages = {}
		origq = copy.deepcopy(q)
		if debug :
			print 'query', prettyquery(q)
		for p in passes :
			try :
				q = p(q)
			except QueryException, qe :
				oqp = origq
				qp = q
				print 'oqp',prettyquery(oqp)
				print 'qe.path',qe.path
				print 'qe.message',qe.message
				for ele in qe.path :
					oqp = oqp[ele]
				
				if qe.debug_path :
					debug_path = qe.debug_path
				else :
					debug_path = qe.path
				for ele in debug_path :
					qp = qp[ele]
				
				qp[n.sparql.error_inside] = '.'
				oqp[n.sparql.error_inside] = '.'
				q = {
					n.sparql.status : n.sparql.error,
					n.sparql.debug : q,
					n.sparql.query : origq,
					n.sparql.error_path : qe.path,
					n.sparql.error_message : qe.message,
					n.sparql.error_in_pass : p.__class__.__name__,
				}
				stages[p.__class__.__name__] = copy.deepcopy(q)
				if debug :
					print p.__class__.__name__, prettyquery(q)
				return stages
			stages[p.__class__.__name__] = copy.deepcopy(q)
			if debug :
				print p.__class__.__name__, prettyquery(q)
		
		return stages
	
	def test(self, i, q, debug = False, save = False) :
		"""
		i : unique integer id for this test
		q : the query
		debug : show debug information (the output at each pass)
		save : commit this version of the query and the output from each pass to the
			history
		"""
		if save == False :
			if i in self.history :
				stages = self.do(q, debug)
				if stages != self.history[i] :
					self.failcount += 1
					print "FAIL", i
					for stage in stages :
						if stages[stage] != self.history[i][stage] :
							print 'ERROR in:',stage
							print 'stages'
							print prettyquery(stages[stage])
							print 'history'
							print prettyquery(self.history[i][stage])
							print
							print '-'*80
				else :
					self.successcount += 1
#					print 'SUCCESS'
			else :
				stages = self.do(q, True)
		else :
			self.history[i] = self.do(q, debug)

pt = PassTest()

q = {
	n.test.x : 1,
	n.sparql.create : n.sparql.unless_exists
}

pt.test(1, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_exists,
			n.test.a : 1,
		}, {
			n.test.b : 2,
		},
	],
}

pt.test(2, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_exists,
			n.test.a : 999,
		}, {
			n.test.b : 2,
		},
	],
}

pt.test(3, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_connected,
			n.test.a : 999,
		}, {
			n.test.b : 2,
		},
	],
}

pt.test(4, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_connected,
			n.test.a : 21,
		}, {
			n.test.b : 2,
		},
	],
}

pt.test(5, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_connected,
			n.test.a : 22,
		}, {
			n.test.b : 2,
		},
	],
}

pt.test(6, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_connected,
			n.test.a : 22,
		}, {
			n.test.b : 2,
		}, {
			n.sparql.create : n.sparql.unless_connected,
			n.test.a : 21,
		},
	],
}

pt.test(7, q)

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.create : n.sparql.unless_exists,
			n.test.a : 22,
		}, {
			n.test.b : 2,
		}, {
			n.sparql.create : n.sparql.unless_exists,
			n.test.a : 21,
		},
	],
}

pt.test(8, q)

# note that this creates the x:1 but tries to find the x:22
q = {
	n.test.x : 1,
	n.test.y : {
		n.test.x : 22
	},
	n.sparql.create : n.sparql.unless_exists
}

pt.test(9, q)

# note that this creates the x:1 but tries to find the x:22
q = {
	n.test.x : 1,
	n.test.y : {
		n.test.x : 22,
		n.sparql.create : n.sparql.unless_exists,
	},
	n.sparql.create : n.sparql.unless_exists
}

pt.test(10, q)

# note that this creates the x:1 but tries to find the x:22
q = {
	n.test.x : 1,
	n.test.w : 2,
	n.test.y : {
		n.test.x : 22,
		n.sparql.create : n.sparql.unless_exists,
	},
	n.sparql.create : n.sparql.unless_exists
}

pt.test(11, q)

# note that this creates the x:1 but tries to find the x:22
q = {
	n.test.x : 1,
	n.test.w : 3.14,
	n.test.y : {
		n.test.x : 1,
		n.test.w : 3.14,
		n.sparql.create : n.sparql.force,
	},
	n.sparql.create : n.sparql.unless_exists
}

pt.test(12, q)

# two queries in a row!
# is the first query evaluated before the second?  Or do they happen at the same
#   time?
q = [
	{
		n.test.x : 1,
		n.test.w : 2,
		n.sparql.create : n.sparql.unless_exists
	},{
		n.test.x : 1,
		n.test.w : 2,
		n.test.y : {
			n.test.x : 22,
			n.sparql.create : n.sparql.unless_exists,
		},
		n.sparql.create : n.sparql.unless_exists
	}
]

#pt.test(13, q)

# does this create two 100s? or just one?
q = {
	n.test.x : 1,
	n.test.w : [
		{
			n.test.x : 100,
			n.sparql.create : n.sparql.unless_exists,
		}, {
			n.test.x : 100,
			n.sparql.create : n.sparql.unless_exists,
		}
	]
}

pt.test(14, q)

q = {
	n.test.x : 12,
	n.test.w : [ 100, 200 ],
	n.sparql.create : n.sparql.unless_exists,
}

#pt.test(15, q)

exit()



print 'failures:',failcount