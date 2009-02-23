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
n.bind('library', '<http://dwiel.net/axpress/library/0.1/>')
n.bind('music', '<http://dwiel.net/axpress/music/0.1/>')
n.bind('music_album', '<http://dwiel.net/axpress/music_album/0.1/>')
n.bind('source', '<http://dwiel.net/axpress/source/0.1/>')
n.bind('lastfm', '<http://dwiel.net/axpress/lastfm/0.1/>')
n.bind('rdfs', '<http://www.w3.org/2000/01/rdf-schema#>')
n.bind('bound_var', '<http://dwiel.net/axpress/bound_var/0.1/>')
n.bind('flickr', '<http://dwiel.net/axpress/flickr/0.1/>')
n.bind('amos', '<http://dwiel.net/axpress/amos/0.1/>')
a = n.rdfs.type

# for easy basic stupid matching type instance
class X():pass
type_instance = type(X())

class AxpressTestCase(unittest.TestCase):
	def setUp(self):
		self.compiler = Compiler(n)
		self.evaluator = Evaluator(n)
		
		loadTranslations(self.compiler, n)
		
		#self.parser = MultilineParser(n, sparql = sparql, translator = self.translator)
		self.axpress = Axpress(
			sparql = sparql,
			compiler = self.compiler,
			evaluator = self.evaluator
		)	
	
	def testIncomingBindings(self):
		def is_num(x):
			return isinstance(x, (int, long, float))
		
		bindings_set = self.axpress.read_sparql("""
			foo[test.x] = x
			foo[test.y] = y
		""")
		
		# reduce bindings to those whose x and y values are numbers
		# I'd like this functionality to exist, but I don't think this is the right
		# way to get at it, or think about it.  For one, the type should take care
		# of most of this kind of thing - though I know that it shouldn't be relied
		# on ...
		#bindings_set = [x for x in bindings_set]
		#print 'bindings_set',prettyquery(bindings_set)
		new_bindings_set = []
		for bindings in bindings_set :
			if is_num(bindings['x']) and is_num(bindings['y']) :
				new_bindings_set.append(bindings)
		bindings_set = new_bindings_set
		#print 'bindings_set',prettyquery(bindings_set)
		
		ret = self.axpress.read_translate("""
			foo[test.x] = x
			foo[test.y] = y
			foo[test.sum] = _sum
		""", reqd_bound_vars = ['sum'], bindings_set = bindings_set)
		#p('ret',ret)
		assert ret == [
			{
				u'sum' : 3,
			},
		]
	
	def testTranslationReturnsMultipleValues(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			thumb[pil.image] = _thumb_image
		""", reqd_bound_vars = ['thumb_image', 'thumb'])
		#print 'ret2',prettyquery(ret)
		for i, bindings in enumerate(ret) :
			ret[i]['thumb_image'] = type(bindings['thumb_image'])
		#ret = [{'thumb_image' : type(bindings['thumb_image'])} for bindings in ret]
		assert ret == [
			{
				'thumb' : n.out_var.thumb,
				'thumb_image' : type_instance,
			}, {
				'thumb' : n.out_var.thumb,
				'thumb_image' : type_instance,
			}
		]
	
	def testQueryLimitLessThanAvailable(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			thumb[pil.image] = _thumb_image
			query.query[query.limit] = 1
		""", reqd_bound_vars = ['thumb_image'])
		#print 'ret test2_1',prettyquery(ret)
		ret = [{'thumb_image' : type(bindings['thumb_image'])} for bindings in ret]
		assert ret == [
			{
				'thumb_image' : type_instance,
			}
		]
	
	def testQueryLimitSameAsAvailable(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			thumb[pil.image] = _thumb_image
			query.query[query.limit] = 2
		""", reqd_bound_vars = ['thumb_image'])
		#print 'ret2_2',prettyquery(ret)
		ret = [{'thumb_image' : type(bindings['thumb_image'])} for bindings in ret]
		assert ret == [
			{
				'thumb_image' : type_instance,
			}, {
				'thumb_image' : type_instance,
			}
		]
	
	def testQueryLimitMoreThanAvailable(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			thumb[pil.image] = _thumb_image
			query.query[query.limit] = 3
		""", reqd_bound_vars = ['thumb_image'])
		#print 'ret2_3',prettyquery(ret)
		ret = [{'thumb_image' : type(bindings['thumb_image'])} for bindings in ret]
		assert ret == [
			{
				'thumb_image' : type_instance,
			}, {
				'thumb_image' : type_instance,
			}
		]
	
	# warning this test requires the internet and will ping flickr.  Don't do alot
	#def test3(self) :
		#ret = self.axpress.read_translate("""
			#image[flickr.tag] = 'floor'
			#image[file.url] = _url
		#""", reqd_bound_vars = ['url'])
		#print 'ret',prettyquery(ret)
	
	# warning this test requires the internet and will ping flickr.  Don't do alot
	#def test4(self) :
		#ret = self.axpress.read_translate("""
			#image[flickr.tag] = 'wall'
			#thumb = image.thumbnail(image, 4, 4, image.antialias)
			#thumb[pil.image] = _thumb_image
			#query.query[query.limit] = 1
		#""", reqd_bound_vars = ['thumb_image'])
		#print 'ret',prettyquery(ret)
	
	def test5(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			image[file.filename] = _filename
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			pixel = image.pixel(thumb, 0, 0)
			pixel[pil.color] = _thumb_pixel_color
		""", reqd_bound_vars = ['filename','thumb_pixel_color'])
		# print 'ret5',prettyquery(ret)
		assert ret == [
			{
				u'filename' : '/home/dwiel/pictures/stitt blanket/00002.jpg',
				u'thumb_pixel_color' : (141, 130, 100),
			}, {
				u'filename' : '/home/dwiel/pictures/stitt blanket/00001.jpg',
				u'thumb_pixel_color' : (94, 48, 67),
			},
		]
	
	def test6(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/pictures/stitt blanket/*.jpg"
			image[file.filename] = _filename
			thumb = image.thumbnail(image, 4, 4, image.antialias)
			pixel = image.pixel(thumb, 0, 0)
			dist[type.number] = color.distance(color.red, pixel)
			dist[type.number] = _distance
		""", reqd_bound_vars = ['filename','distance'])
		#print 'ret6',prettyquery(ret)
		assert ret == [
			{
				u'distance' : 39896,
				u'filename' : '/home/dwiel/pictures/stitt blanket/00002.jpg',
			}, {
				u'distance' : 32714,
				u'filename' : '/home/dwiel/pictures/stitt blanket/00001.jpg',
			},
		]

	def test7(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = "/home/dwiel/AMOSvid/*.jpg"
			thumb = image.thumbnail(image, 1, 1)
			pix = image.pixel(thumb, 0, 0)
			pix[pil.color] = _color
			image[file.filename] = _filename
		""")
		#print 'ret7',prettyquery(ret)
		assert len(ret) == 2
		assert ret == [
			{
				u'color' : ( 71, 43, 85, ),
				u'filename' : '/home/dwiel/AMOSvid/20080804_080127.jpg',
			}, {
				u'color' : ( 58, 25, 47, ),
				u'filename' : '/home/dwiel/AMOSvid/20080804_083127.jpg',
			},
		]

	
	def testBasicExample(self):
		ret = self.axpress.read_translate("""
			foo[test.x] = 1
			foo[test.y] = 10
			foo[test.sum] = _sum
		""")
		#p('ret8',ret)
		assert ret == [{'sum' : 11}]

	def testMultipleNonDependentPaths(self):
		ret = self.axpress.read_translate("""
			image[file.filename] = "/home/dwiel/AMOSvid/20080804_080127.jpg"
			pix = image.pixel(image, 0, 0)
			pix[pil.color] = _color
			image[html.height] = 200
			image[html.width] = 300
			image[html.html] = _html
		""")
		#p('ret9',ret)
		assert ret ==  [
			{
				u'color' : ( 249, 255, 237, ),
				u'html' : '<img src="/home/AMOSvid/20080804_080127.jpg" width="300" height="200"/>',
			},
		]

	## only works when amarok is playing music
	#def testAmarok(self):
		#ret = self.axpress.read_translate("""
 			#amarok.amarok[amarok.artist] = artist
			#artist[music.artist_name] = _name
		#""")
		##p('ret10',ret)
		#assert len(ret) == 1 and len(ret[0]) == 1 and 'name' in ret[0] and isinstance(ret[0]['name'], basestring)

	def testTranslationReturnsListOfBindings(self):
		ret = self.axpress.read_translate("""
			qartist[music.artist_name] = 'Neil Young'
			qartist[lastfm.similar_to] = qsimilar_artist
			qsimilar_artist[lastfm.name] = _name
		""")
		#p('ret11',ret)
		assert len(ret) == 10
		for bindings in ret :
			assert len(bindings) == 1
			assert 'name' in bindings
			assert isinstance(bindings['name'], basestring)

	## only works when amarok is playing music
	#def testTranslationReturnsListOfBindings2(self):
		#ret = self.axpress.read_translate("""
			#amarok.amarok[amarok.artist] = artist
			#artist[lastfm.similar_to] = similar_artist
			#similar_artist[lastfm.name] = _name
		#""")
		##p('ret12',ret)
		#assert len(ret) == 10
		#for bindings in ret :
			#assert len(bindings) == 1
			#assert 'name' in bindings
			#assert isinstance(bindings['name'], basestring)
	
	def testNoBindingsFromTranslation(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = '/no/files/here/*.jpg'
			image[file.filename] = _filename
		""")
		assert len(ret) == 0

	def testNoBindingsFromTranslation2(self):
		ret = self.axpress.read_translate("""
			foo[test.no_bindings_input] = "input string"
			foo[test.no_bindings_output] = _output
		""")
		assert len(ret) == 0
	
	def testGeneral(self):
		ret = self.axpress.read_translate("""
			image[glob.glob] = '/home/dwiel/AMOSvid/1065/*.png'
			image[file.filename] = _filename
		""")
		p('testGeneral',ret)

	def testIncomingOutgoingBindings(self):
		ret = self.axpress.read_translate("""
			foo[test.x] = x
			foo[test.y] = y
			foo[test.sum] = _sum
		""", bindings_set = [{'x' : 1, 'y' : 2}], reqd_bound_vars=['x', 'sum'])
		#p('ret',ret)
		assert ret == [
			{
				u'x' : 1,
				u'sum' : 3,
			},
		]
	
	def testIncomingOutgoingBindings2(self):
		ret = self.axpress.read_translate("""
			foo[test.x] = _x
			foo[test.y] = y
			foo[test.sum] = _sum
		""", bindings_set = [{'x' : 1, 'y' : 2}])
		p('ret',ret)
		assert ret == [
			{
				u'x' : 1,
				u'sum' : 3,
			},
		]

	
	
	
	
if __name__ == "__main__" :
	#print '<root>'
	unittest.main()
	#print '</root>'


