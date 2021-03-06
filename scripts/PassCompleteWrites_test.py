import unittest

from SimpleSPARQL import *

n = globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')

class PassCompleteWritesTestCase(unittest.TestCase):
	def setUp(self):
		self.sparql = SimpleSPARQL("http://localhost:2020/sparql")
		self.sparql.setGraph("http://dwiel.net/axpress/testing")
		self.sparql.setNamespaces(n)
		self.p = PassCompleteWrites(self.sparql)
	
	def test1(self):
		q = {
			n.sparql.reads : [{
				n.test.x : '1',
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}],
			n.sparql.writes : []
		}
		try :
			rr = self.p(q)
			assert False, "should not have found a match.  found: " + prettyquery(rr)
		except QueryException, qe :
			assert qe == QueryException((0,), 'no match found')

	def test2(self):
		q = {
			n.sparql.reads : [{
				n.test.x : 1,
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}],
			n.sparql.writes : []
		}
		r = {
			n.sparql.reads : [{
				n.test.x : 1,
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}],
			n.sparql.writes : []
		}
		assert r == self.p(q)

