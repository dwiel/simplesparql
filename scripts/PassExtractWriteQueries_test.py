import unittest

from SimpleSPARQL import *

n = globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')

class PassExtractWriteQueriesTestCase(unittest.TestCase):
	def setUp(self):
		self.p = PassExtractWriteQueries()
	
	def test1(self):
		q = [{
			'x' : '1',
			n.sparql.var : 'autovar1'
		}]
		r = {
			n.sparql.reads : [{
				'x' : '1',
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}],
			n.sparql.writes : []
		}
		assert self.p(q) == r, prettyquery(self.p(q))
		
	def test2(self):
		q = [{
			'x' : '1',
			'y' : [
				{
					'a' : '1',
					n.sparql.var : 'autovar2'
				},
				{
					'b' : '2',
					n.sparql.var : 'autovar3'
				},
			],
			n.sparql.var : 'autovar1'
		}]
		r = {
			n.sparql.reads : [{
				'x' : '1',
				'y' : [
					{
						'a' : '1',
						n.sparql.var : 'autovar2'
					},
					{
						'b' : '2',
						n.sparql.var : 'autovar3'
					},
				],
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}],
			n.sparql.writes : []
		}
		assert self.p(q) == r, prettyquery(self.p(q))
	
	def test3(self):
		q = [{
			'x' : 1,
			'y' : 2,
			n.sparql.create : n.sparql.unless_exists,
			n.sparql.var : 'autovar1'
		}]
		r = {
			n.sparql.reads : [],
			n.sparql.writes : [{
				'x' : 1,
				'y' : 2,
				n.sparql.create : n.sparql.unless_exists,
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
			}]
		}
		assert self.p(q) == r, prettyquery(self.p(q))
	
	def test4(self):
		q = [{
			n.sparql.var : 'autovar1',
			'a' : 10,
			'b' : {
				n.sparql.var : 'autovar2',
				'x' : 1,
				'y' : 2,
				n.sparql.create : n.sparql.unless_exists
			}
		}]
		r = {
			n.sparql.reads : [{
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
				'a' : 10,
				'b' : None
			}],
			n.sparql.writes : [{
				n.sparql.var : 'autovar2',
				n.sparql.path : (0, 'b'),
				'x' : 1,
				'y' : 2,
				n.sparql.create : n.sparql.unless_exists,
#				n.sparql.subject : 'autovar1',
#				n.sparql.predicate : 'b',
			}]
		}
		assert self.p(q) == r, prettyquery(self.p(q))

	def test5(self):
		q = [{
			n.sparql.var : 'autovar1',
			'a' : 10,
			'b' : [{
				n.sparql.create : n.sparql.unless_exists,
				n.sparql.var : 'autovar2',
				'x' : 1,
				'y' : 2,
			},{
				n.sparql.create : n.sparql.unless_exists,
				n.sparql.var : 'autovar3',
				'x' : 10,
				'y' : 20,
			}]
		}]
		r = {
			n.sparql.reads : [{
				n.sparql.var : 'autovar1',
				n.sparql.path : (0,),
				'a' : 10,
				'b' : None
			}],
			n.sparql.writes : [{
				n.sparql.create : n.sparql.unless_exists,
				n.sparql.var : 'autovar2',
				n.sparql.path : (0, 'b', 0),
				'x' : 1,
				'y' : 2,
#				n.sparql.subject : 'autovar1',
#				n.sparql.predicate : 'b',
			},{
				n.sparql.create : n.sparql.unless_exists,
				n.sparql.var : 'autovar3',
				n.sparql.path : (0, 'b', 1),
				'x' : 10,
				'y' : 20,
#				n.sparql.subject : 'autovar1',
#				n.sparql.predicate : 'b',
			}]
		}
		assert self.p(q) == r, prettyquery(self.p(q))

if __name__ == "__main__" :
	unittest.main()
