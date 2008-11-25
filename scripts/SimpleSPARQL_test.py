import unittest

import SimpleSPARQL
import Namespaces
import datetime

from pprint import pprint

n = Namespaces.globalNamespaces()
n.bind('', '<http://dwiel.net/express/rule/0.1/>')
n.bind('e', '<http://dwiel.net/express/rule/0.1/>')
n.bind('rdf', '<http://www.w3.org/1999/02/22-rdf-syntax-ns#>')
n.bind('schema', '<http://dwiel.net/express/schema/0.1/>')
n.bind('schema_property', '<http://dwiel.net/express/schema_property/0.1/>')
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')

class SimpleSPARQLTestCase(unittest.TestCase):
	def setUp(self):
		self.sparql = SimpleSPARQL.SimpleSPARQL("http://localhost:2020/sparql")
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
	
	def testn3Dictionary1(self):
		assert self.sparql.python_to_n3({"x" : "y", 1 : 2}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
@prefix e: <http://dwiel.net/express/rule/0.1/> .
@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 :new "x"@en "y"@en ; 1 2 .""", 'failed dictionary test 1: ' + self.sparql.python_to_n3({"x" : "y", 1 : 2})

	def testn3Dictionary2(self):
		assert self.sparql.python_to_n3({":x" : "y", 1 : 2}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
@prefix e: <http://dwiel.net/express/rule/0.1/> .
@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 :new 1 2 ; :x "y"@en .""", 'failed dictionary test 2: ' + self.sparql.python_to_n3({":x" : "y", 1 : 2})
 
	def testn3Dictionary3(self):
		assert self.sparql.python_to_n3({":x" : "y", "e:b" : [1, 2, 3]}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
@prefix e: <http://dwiel.net/express/rule/0.1/> .
@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 :new :x "y"@en ; e:b 1, 2, 3 .""", 'failed dictionary test 3'

	def testn3Dictionary4(self):
		assert self.sparql.python_to_n3({"e:b" : [{"e:tag" : ["abc", 'd"ef']}]}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
@prefix e: <http://dwiel.net/express/rule/0.1/> .
@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 :new e:b [ e:tag "abc"@en, 'd"ef'@en ] .""", 'failed dictionary test 4'

	def testn3Dictionary5(self):
		assert self.sparql.python_to_n3({"e:a" : {"e:b" : "b", "e:c" : "c"}}) == """@prefix : <http://dwiel.net/express/rule/0.1/> .
@prefix e: <http://dwiel.net/express/rule/0.1/> .
@prefix sparql: <http://dwiel.net/express/sparql/0.1/> .
@prefix schema_property: <http://dwiel.net/express/schema_property/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://dwiel.net/express/schema/0.1/> .
 :new e:a [ e:b "b"@en ; e:c "c"@en ] .""", 'failed dictionary test 4'

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
		assert self.sparql.python_to_SPARQL_long(query) == '?var2 <http://dwiel.net/express/rule/0.1/friend> ?var1 . ?var2 <http://dwiel.net/express/rule/0.1/url> "url"@en . ', 'test_python_to_SPARQL_long'
	
	def testWrite(self):
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
		self.sparql.write(query)
	
	def testWrite1(self):
		query = {
			n.e.url : 'url',
			n.e.similar : {
				n.sparql.create : n.sparql.unless_exists,
				n.e.similarity : 1.0,
				n.e.similar_to : {
					n.e.url : 'url'
				}
			}
		}
		ret = self.sparq.write(query)



if __name__ == "__main__" :
	unittest.main()

	"""?uri a schema:type .
		?uri schema:property [
			schema_property:default ?b ;
			schema_property:type ?c
		] ."""