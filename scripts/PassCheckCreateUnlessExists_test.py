import unittest

from SimpleSPARQL import *

n = globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')

class PassCheckCreateUnlessExistsTestCase(unittest.TestCase):
	def setUp(self):
		self.sparql = SimpleSPARQL("http://localhost:2020/sparql")
		self.sparql.setGraph("http://dwiel.net/axpress/testing")
		self.sparql.setNamespaces(n)
		self.p = PassCheckCreateUnlessExists(self.sparql)
	
	def test1(self):
		q = {
			sparql:reads : [
			],
			sparql:writes : [
				{
					sparql:create : sparql:unless_exists,
					sparql:path : (0,),
					test:x : 1,
				},
			],
		}
		r = {
			sparql:reads : [ ],
			sparql:writes : [
				{
					sparql:create : sparql:existed,
					sparql:path : (0,),
					sparql:subject : test:object1,
					test:x : 1,
				},
			],
		}


		print prettyquery(q)
		self.p(q)

if __name__ == "__main__" :
	unittest.main()





















