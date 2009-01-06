import unittest

import rdflib
import SimpleSPARQL
import Namespaces
import datetime
from SimpleSPARQL.PrettyQuery import prettyquery

from pprint import pprint

n = Namespaces.globalNamespaces()
n.bind('', '<http://dwiel.net/express/rule/0.1/>')
n.bind('e', '<http://dwiel.net/express/rule/0.1/>')
n.bind('rdf', '<http://www.w3.org/1999/02/22-rdf-syntax-ns#>')
n.bind('schema', '<http://dwiel.net/express/schema/0.1/>')
n.bind('schema_property', '<http://dwiel.net/express/schema_property/0.1/>')
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')

class SimpleSPARQLTestCase(unittest.TestCase):
	def setUp(self):
		self.sparql = SimpleSPARQL.SimpleSPARQL("http://localhost:2020/sparql")
		self.sparql.setGraph("http://dwiel.net/axpress/testing")
		self.sparql.setNamespaces(n)
		
	def testn3String(self):
		assert self.sparql.python_to_n3("a string") == '"a string"@en', 'incorrect handling of strings'
	
	def testn3Uri(self):
		assert self.sparql.python_to_n3("e:tag") == 'e:tag', 'incorrect handling of uris'
	
	def testn3Int(self):
		assert self.sparql.python_to_n3(100) == '100', 'incorrect handling of ints'
	
	def testn3Float(self):
		assert self.sparql.python_to_n3(3.1415) == '3.1415', 'incorrect handling of floats'
		
	def testn3Datetime(self):
		assert self.sparql.python_to_n3(datetime.datetime(2008, 10, 20, 21, 45, 31)) == '"2008-10-20T21:45:31T"^^xsd:dateTime', 'incorrect handling of floats'	
	
	#def testn3Dictionary1(self):
		#assert self.sparql.python_to_n3({"x" : "y", 1 : 2}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
#@prefix e: <http://dwiel.net/express/rule/0.1/> .
#@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
#@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
#@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
#@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 #:new "x"@en "y"@en ; 1 2 .""", 'failed dictionary test 1: ' + self.sparql.python_to_n3({"x" : "y", 1 : 2})

	#def testn3Dictionary2(self):
		#assert self.sparql.python_to_n3({":x" : "y", 1 : 2}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
#@prefix e: <http://dwiel.net/express/rule/0.1/> .
#@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
#@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
#@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
#@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 #:new 1 2 ; :x "y"@en .""", 'failed dictionary test 2: ' + self.sparql.python_to_n3({":x" : "y", 1 : 2})
 
	#def testn3Dictionary3(self):
		#assert self.sparql.python_to_n3({":x" : "y", "e:b" : [1, 2, 3]}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
#@prefix e: <http://dwiel.net/express/rule/0.1/> .
#@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
#@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
#@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
#@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 #:new :x "y"@en ; e:b 1, 2, 3 .""", 'failed dictionary test 3'

	##def testn3Dictionary4(self):
		##assert self.sparql.python_to_n3({"e:b" : [{"e:tag" : ["abc", 'd"ef']}]}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
##@prefix e: <http://dwiel.net/express/rule/0.1/> .
##@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
##@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
##@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
##@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 ##:new e:b [ e:tag "abc"@en, 'd"ef'@en ] .""", 'failed dictionary test 4'

	#def testn3Dictionary5(self):
		#assert self.sparql.python_to_n3({"e:a" : {"e:b" : "b", "e:c" : "c"}}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
#@prefix e: <http://dwiel.net/express/rule/0.1/> .
#@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
#@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
#@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
#@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 #:new e:a [ e:b "b"@en ; e:c "c"@en ] .""", 'failed dictionary test 4'

	#def testSPARQLDictionary1(self):
		#print '---'
		#print self.sparql.python_to_SPARQL({'e:x' : 1, 'abc' : 'def'})

	def testSPARQLDictionary2(self):
		for rdfo in self.sparql.find(
			{
				'rdf:type' : 'schema:type', 
				'schema:property' : {
					'schema_property:default' : None,
					'schema_property:type' : None,
				}
			}
		) :
			print rdfo.root
	
	#def testWriteDictionary(self):
		#self.sparql.write({
			#n.feed.url : entry.content[0].base,
			#n.feed.entry : {
				#n.sparql.connect : n.sparql.insert,
				#n.entry['title'] : entry.title,
				#n.entry.date : entry.updated_parsed,
				#n.entry.content : entry.content[0].value
			#}
		#})
	
	def test_preprocess_query1(self):
		query = {
			n.e.url : 'url',
			n.e.entry : [{
				n.sparql.create : n.sparql.unless_exists,
				n.e['title'] : 'title',
				n.e.date : 'date',
				n.e.content : 'content'
			}],
			n.e.friend : {
				n.e.entry : {
					n.sparql.create : n.sparql.unless_exists,
					n.e['title'] : 'title2',
					n.e.date : 'date2',
					n.e.content : 'content2'
				}
			}
		}
		transformed = self.sparql._preprocess_query(query)
		assert transformed == {
			n.e.url : 'url',
			n.e.friend : {
				n.sparql.var : 1
			},
			n.sparql.var : 2,
			n.sparql.insert : [{
				n.sparql.subject : 1,
				n.sparql.predicate : n.e.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.e['title'] : 'title2',
				n.e.date : 'date2',
				n.e.content : 'content2'
			},{
				n.sparql.subject : 2,
				n.sparql.predicate : n.e.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.e['title'] : 'title',
				n.e.date : 'date',
				n.e.content : 'content'
			}],
			n.sparql.delete : []
		}, 'bad transformation'
		
	def test_preprocess_query2(self):
		query = {
			n.e.url : 'url',
			n.e.entry : {
				n.sparql.create : n.sparql.unless_exists,
				n.e['title'] : 'title',
				n.e.date : 'date',
				n.e.content : 'content'
			}
		}
		transformed = self.sparql._preprocess_query(query)
		assert transformed == {
			n.e.url : 'url',
			n.sparql.var : 1,
			n.sparql.insert : [{
				n.sparql.subject : 1,
				n.sparql.predicate : n.e.entry,
				n.sparql.create : n.sparql.unless_exists,
				n.e['title'] : 'title',
				n.e.date : 'date',
				n.e.content : 'content'
			}],
			n.sparql.delete : []
		}, 'bad transformation'
	
	def test_python_to_SPARQL_long(self):
		query = {
			n.e.url : 'url',
			n.e.friend : {
				n.sparql.var : 1
			},
			n.sparql.var : 2
		}
		assert self.sparql.python_to_SPARQL_long(query) == '?var2 <http://dwiel.net/express/rule/0.1/friend> ?var1 .\n?var2 <http://dwiel.net/express/rule/0.1/url> "url"@en .\n', 'test_python_to_SPARQL_long'
	
	#def testWrite(self):
		#query = {
			#n.e.url : 'url',
			#n.e.entry : [{
				#n.sparql.create : n.sparql.unless_exists,
				#n.e['title'] : 'title',
				#n.e.date : 'date',
				#n.e.content : 'content'
			#}],
			#n.e.friend : {
				#n.e.entry : {
					#n.sparql.create : n.sparql.unless_exists,
					#n.e['title'] : 'title2',
					#n.e.date : 'date2',
					#n.e.content : 'content2'
				#}
			#}
		#}
		#self.sparql.write(query)
	
	#def testWrite1(self):
		#query = {
			#n.e.url : 'url',
			#n.e.similar : {
				#n.sparql.create : n.sparql.unless_exists,
				#n.e.similarity : 1.0,
				#n.e.similar_to : {
					#n.e.url : 'url'
				#}
			#}
		#}
		#ret = self.sparql.write(query)
	
	def testRead1(self) :
		query = {
			n.test.x : 1
		}
		result = {
			n.sparql.error_message : 'too many values',
			n.sparql.error_path : (),
			n.sparql.query : {
				n.test.x : 1,
				n.sparql.error_inside : '.',
			},
			n.sparql.status : n.sparql.error,
		}
		assert result == self.sparql.read(query)

	def testRead2(self) :
		query = [
			{
				n.test.x : 1
			}
		]
		result = {
			n.sparql.result : [
				{
				}, {
				},
			],
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead3(self) :
		query = [
			{
				n.test.x : 1,
				n.sparql.subject : None
			}
		]
		result = {
			n.sparql.result : [
				{
					n.sparql.subject : n.test.object1,
				}, {
					n.sparql.subject : n.test.object2,
				},
			],
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead4(self) :
		query = [
			{
				n.test.x : None,
				n.sparql.subject : None
			}
		]
		result = {
			n.sparql.result : [
				{
					n.sparql.subject : n.test.object5,
					n.test.x : rdflib.Literal(5),
				}, {
					n.sparql.subject : n.test.object1,
					n.test.x : rdflib.Literal(1),
				}, {
					n.sparql.subject : n.test.object2,
					n.test.x : rdflib.Literal(1),
				}, 
			],
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead5(self) :
		query = [
			{
				n.test.x : 2,
				n.sparql.subject : None
			}
		]
		result = {
			n.sparql.result : [],
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead6(self) :
		query = {
			n.test.x : 2,
			n.sparql.subject : None
		}
		result = {
			n.sparql.error_message : 'no match found',
			n.sparql.error_path : (),
			n.sparql.query : {
				n.sparql.error_inside : '.',
				n.test.x : 2,
			},
			n.sparql.status : n.sparql.error,
		}
		assert result == self.sparql.read(query)
	
	def testRead7(self) :
		query = {
			n.test.x : 5,
			n.test.y : {
				n.test.y : {
					n.test.a : None,
				}
			}
		}
		result = {
			n.sparql.result : {
				n.test.y : {
					n.test.y : {
						n.test.a : 21,
					},
				},
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead8(self) :
		query = {
			n.test.x : None,
			n.sparql.subject : n.test.object1
		}
		result = {
			n.sparql.result : {
				n.test.x : 1,
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)

	def testRead9(self) :
		query = {
			n.test.x : None,
			n.test.y : None,
			n.sparql.subject : n.test.object1
		}
		result = {
			n.sparql.result : {
				n.test.x : 1,
				n.test.y : 2,
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)

	def testRead10(self) :
		query = {
			n.test.x : None,
			n.test.y : {
				n.test.a : None,
			},
			n.sparql.subject : n.test.object2
		}
		result = {
			n.sparql.result : {
				n.test.x : 1,
				n.test.y : {
					n.test.a : 21,
				},
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)

	def testRead11(self) :
		query = {
			n.test.x : 5,
			n.test.y : {
				n.test.y : {
					n.test.a : None,
				}
			},
			n.sparql.subject : n.test.object5,
		}
		result = {
			n.sparql.result : {
				n.test.y : {
					n.test.y : {
						n.test.a : 21,
					},
				},
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)

	def testRead12(self) :
		query = {
			n.test.x : 5,
			n.test.y : [{
				n.test.y : {
					n.test.a : None,
				}
			}],
			n.sparql.subject : n.test.object5,
		}
		result = {
			n.sparql.result : {
				n.test.y : [{
					n.test.y : {
						n.test.a : 21,
					},
				}],
			},
			n.sparql.status : n.sparql.ok,
		}
		assert result == self.sparql.read(query)
	
	def testRead13(self) :
		#query = [
			#{
				#n.sparql.subject : None,
				#None : 21
			#}
		#]
		assert True == False
	
	def testRead14(self) :
		# TODO: allow n.sparql.any as the predicate
		query = [
			{
				n.test.x : None,
				n.sparql.subject : None,
				n.sparql.any : None
			}
		]
		result = {}
		ret = self.sparql.read(query)
		print prettyquery(ret)
		assert result == ret
	
	# is this query for things with w:100 AND w:200 or w:100 OR w:200 ?
	# If it does have only one of the above meanings, how do you express the other one?
	# choose a default meaning
	# if n.sparql.and or n.sparql.or appear as the first item in the list, they are all that operator
	# example:
	# [100,n.sparql.and, [n.sparql.or, 101, 102, 103]] : 100 and (101 or 102 or 03)
	#def testRead13(self) :
		#query = {
			#n.test.x : 12,
			#n.test.w : [ 100, 200 ],
		#}
		#print prettyquery(self.sparql.read(query))
		
if __name__ == "__main__" :
	unittest.main()

	"""?uri a schema:type .
		?uri schema:property [
			schema_property:default ?b ;
			schema_property:type ?c
		] ."""