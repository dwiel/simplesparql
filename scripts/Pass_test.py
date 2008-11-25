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
		print 'query', prettyquery(q)
		for p in passes :
			try :
				q = p(q)
			except QueryException, qe :
				oqp = origq
				qp = q
				for ele in qe.path :
					qp = qp[ele]
					oqp = oqp[ele]
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
		if save == False :
			if i in self.history :
				stages = self.do(q, debug)
				if stages != self.history[i] :
					self.failcount += 1
					print "FAIL"
				else :
					self.successcount += 1
					print 'SUCCESS'
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

exit()

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

do(q)

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

do(q)

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

do(q)

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

do(q)


print 'failures:',failcount