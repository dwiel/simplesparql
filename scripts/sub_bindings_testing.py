# Translator testing
# this translator assumes the translations available in loadTranslator

import unittest

import time, urllib
from rdflib import *
from SimpleSPARQL import *

sparql = SimpleSPARQL("http://localhost:2020/sparql")
sparql.setGraph("http://dwiel.net/axpress/testing")

n = sparql.n
n.bind('library', '<http://dwiel.net/axpress/library/0.1/>')
n.bind('music', '<http://dwiel.net/axpress/music/0.1/>')
n.bind('music_album', '<http://dwiel.net/axpress/music_album/0.1/>')
n.bind('source', '<http://dwiel.net/axpress/source/0.1/>')
n.bind('lastfm', '<http://dwiel.net/axpress/lastfm/0.1/>')
n.bind('rdfs', '<http://www.w3.org/2000/01/rdf-schema#>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')
n.bind('bound_var', '<http://dwiel.net/axpress/bound_var/0.1/>')

a = n.rdfs.type

cache_sparql = SimpleSPARQL("http://localhost:2020/sparql", graph = "http://dwiel.net/axpress/cache")
cache = Cache(cache_sparql)
translator = Translator(cache)

import loadTranslations
loadTranslations.load(translator, n)

# for easy basic stupid matching type instance
class X():pass
type_instance = type(X())

class PassCompleteReadsTestCase(unittest.TestCase):
	def test1(self) :
		ret = translator.sub_var_bindings_new([
 			[ n.var.uri, n.test.div, n.lit_var.div, ],
		], [
			{
				u'div' : 0.20999999999999999,
				u'sum' : 21,
				u'uri' : n.test.u,
				u'z' : 100,
			},
		])
		ret = [x for x in ret]
		assert ret == [
			[
				[ n.test.u, n.test.div, 0.20999999999999999, ],
			],
		]

	def test2(self) :
		ret = translator.sub_var_bindings_new([
 			[ n.var.uri, n.test.div, n.lit_var.div, ],
			[ n.var.uri, n.test.sum, n.lit_var.sum, ],
		], [
			{
				u'div' : 0.20999999999999999,
				u'sum' : 21,
				u'uri' : n.test.u,
				u'z' : 100,
			},
		])
		ret = [x for x in ret]
		assert ret == [
			[
				[ n.test.u, n.test.div, 0.20999999999999999, ],
				[ n.test.u, n.test.sum, 21, ],
			],
		]

	def test3(self) :
		ret = translator.sub_var_bindings_new([
 			[ n.var.uri, n.test.div, n.lit_var.div, ],
			[ n.var.uri, n.test.sum, n.lit_var.sum, ],
		], [
			{
				u'div' : 0.20999999999999999,
				u'sum' : [1,2],
				u'uri' : n.test.u,
				u'z' : 100,
			},
		])
		ret = [x for x in ret]
		print 'ret',prettyquery(ret)
		assert ret == [
			[
				[ n.test.u, n.test.div, 0.20999999999999999, ],
				[ n.test.u, n.test.sum, 1, ],
			],[
				[ n.test.u, n.test.div, 0.20999999999999999, ],
				[ n.test.u, n.test.sum, 2, ],
			]
		]


if __name__ == "__main__" :
	unittest.main()
