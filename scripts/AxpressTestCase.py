import unittest

import time, urllib
from rdflib import *
from SimpleSPARQL import *

sparql = SimpleSPARQL("http://localhost:2020/sparql")
sparql.setGraph("http://dwiel.net/axpress/testing")

n = sparql.n
n.bind('string', '<http://dwiel.net/express/string/0.1/>')
n.bind('math', '<http://dwiel.net/express/math/0.1/>')
n.bind('file', '<http://dwiel.net/express/file/0.1/>')
n.bind('glob', '<http://dwiel.net/express/glob/0.1/>')
n.bind('color', '<http://dwiel.net/express/color/0.1/>')
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('call', '<http://dwiel.net/express/call/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')
n.bind('library', '<http://dwiel.net/axpress/library/0.1/>')
n.bind('music', '<http://dwiel.net/axpress/music/0.1/>')
n.bind('music_album', '<http://dwiel.net/axpress/music_album/0.1/>')
n.bind('source', '<http://dwiel.net/axpress/source/0.1/>')
n.bind('lastfm', '<http://dwiel.net/axpress/lastfm/0.1/>')
n.bind('rdfs', '<http://www.w3.org/2000/01/rdf-schema#>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')
n.bind('bound_var', '<http://dwiel.net/axpress/bound_var/0.1/>')
n.bind('flickr', '<http://dwiel.net/axpress/flickr/0.1/>')
n.bind('amos', '<http://dwiel.net/axpress/amos/0.1/>')
a = n.rdfs.type

class AxpressTestCase(unittest.TestCase):
	def setUp(self):
		self.compiler = Compiler(n)
		self.evaluator = Evaluator(n)
		
		import loadTranslations
		loadTranslations.load(self.compiler, n)
		
		#self.parser = MultilineParser(n, sparql = sparql, translator = self.translator)
		self.axpress = Axpress(
			sparql = sparql,
			compiler = self.compiler,
			evaluator = self.evaluator
		)
	
	#def test1(self):
		#def is_num(x):
			#return isinstance(x, (int, long, float))
		
		#bindings_set = self.axpress.read_sparql("""
			#foo[test.x] = x
			#foo[test.y] = y
		#""")
		
		## reduce bindings to those whose x and y values are numbers
		#print 'bindings_set',prettyquery(bindings_set)
		#new_bindings_set = []
		#for bindings in bindings_set :
			#if is_num(bindings['x']) and is_num(bindings['y']) :
				#new_bindings_set.append(bindings)
		#bindings_set = new_bindings_set
		#print 'bindings_set',prettyquery(bindings_set)
		
		#ret = self.axpress.read_translate("""
			#foo[test.x] = x
			#foo[test.y] = y
			#foo[test.sum] = _sum
		#""", reqd_bound_vars = ['sum'], bindings_set = bindings_set)
		#print 'ret',prettyquery(ret)
	
	def test2(self):
		# facts, history, bindings_set = self.parser.translator.
		ret = self.axpress.read_translate("""
			image[file.filename] = "/home/dwiel/pictures/stitt blanket/*.jpg"[glob.glob]
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			thumb[pil.image] = _thumb_image
		""", reqd_bound_vars = ['thumb_image'])
		# print 'ret',prettyquery(ret)
	
	"""
	"""
	
if __name__ == "__main__" :
	unittest.main()


