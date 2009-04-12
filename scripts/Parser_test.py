# -*- coding: utf-8 -*-
import unittest

from SimpleSPARQL import *

n = globalNamespaces()
n.bind('', '<http://dwiel.net/express//0.1/>')
n.bind('string', '<http://dwiel.net/express/string/0.1/>')
n.bind('math', '<http://dwiel.net/express/math/0.1/>')
n.bind('file', '<http://dwiel.net/express/file/0.1/>')
n.bind('glob', '<http://dwiel.net/express/glob/0.1/>')
n.bind('color', '<http://dwiel.net/express/color/0.1/>')
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('image', '<http://dwiel.net/express/image/0.1/>')
n.bind('pil', '<http://dwiel.net/express/python/pil/0.1/>')
n.bind('glob', '<http://dwiel.net/express/python/glob/0.1/>')
n.bind('call', '<http://dwiel.net/express/call/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')
n.bind('flickr', '<http://dwiel.net/express/flickr/0.1/>')

class PassCompleteReadsTestCase(unittest.TestCase):
	def setUp(self):
		self.parser = Parser(n)
	
	def test1(self):
		assert self.parser.parse_expression("image[flickr.tag] = 'sunset'") == [[n.var.image, n.flickr.tag, 'sunset']]
	
	def test2(self):
		assert self.parser.parse_expression("image[flickr:tag] = 1.5") == [[n.var.image, n.flickr.tag, 1.5]]
	
	def test3(self):
		assert self.parser.parse_expression("image[flickr:tag] = 4 * 9") == [[n.var.image, n.flickr.tag, 4 * 9]]

	def test4(self):
		assert self.parser.parse_expression("image[flickr.tag] = tag") == [[n.var.image, n.flickr.tag, n.var.tag]]
	
	def test5(self):
		assert self.parser.parse_expression("tag = image[flickr.tag]") == [[n.var.image, n.flickr.tag, n.var.tag]]
	
	def test6(self):
		assert self.parser.parse_expression("image1[flickr.tag] = image2[flickr.tag]") == [
			[n.var.image1, n.flickr.tag, n.var.bnode1],
			[n.var.image2, n.flickr.tag, n.var.bnode1],
		]
	
	def test7(self):
		assert self.parser.parse_expression("tag = image[flickr.tag][string.upper]") == [
			[n.var.image, n.flickr.tag, n.var.bnode1],
			[n.var.bnode1, n.string['upper'], n.var.tag],
		]
	
	def test8(self):
		assert self.parser.parse_expression("""
			color.distance{
				color.rgb : 1,
				color.rgb : 2,
			} = distance""") == [
			[n.var.bnode1, n.color.rgb, 1],
			[n.var.bnode1, n.color.rgb, 2],
			[n.var.bnode1, n.color.distance, n.var.distance],
		]
	
	def test9(self):
		assert self.parser.parse_expression("""
			math.sum(1, 2) = sum""") == [
			[n.var.bnode1, n.call.arg1, 1],
			[n.var.bnode1, n.call.arg2, 2],
			[n.var.bnode1, n.math.sum, n.var.sum],
		]
	
	#def test10(self):
		#assert self.parser.parse_expression("""
			#color.distance{
				#color.rgb : something[color],
				#color.rgb : 2,
			#} = distance""") == [
			#[n.var.something, n.var.color, n.var.bnode2],
			#[n.var.bnode1, n.color.rgb, n.var.bnode2],
			#[n.var.bnode1, n.color.rgb, 2],
			#[n.var.bnode1, n.color.distance, n.var.distance],
		#]
	
	def test11(self):
		assert self.parser.parse_expression("image[flickr.tag] = x") == [[n.var.image, n.flickr.tag, n.var.x]]

	def test12(self):
		assert self.parser.parse_expression("image[flickr:tag] = True") == [[n.var.image, n.flickr.tag, True]]
	
	def test13(self):
		assert self.parser.parse_expression("image[flickr.tag] = image_tag") == [[n.var.image, n.flickr.tag, n.var.image_tag]]
		
	def test14(self):
		assert self.parser.parse_expression('image[file.filename] = "/home/dwiel/AMOSvid/1065/20080821_083129.jpg"') == [[n.var.image, n.file.filename, "/home/dwiel/AMOSvid/1065/20080821_083129.jpg"]]
		
	def test15(self):
		assert self.parser.parse_expression('image[file.filename] = "home/dwiel/AMOSvid/1065/*.jpg"[glob.glob]') == [
			[n.var.image, n.file.filename, n.var.bnode1],
			["home/dwiel/AMOSvid/1065/*.jpg", n.glob.glob, n.var.bnode1],
		]
	
	def test16(self):
		assert self.parser.parse_expression('_pattern[glob.glob] = ?filename') == [
			[n.lit_var.pattern, n.glob.glob, n.meta_var.filename],
		]
	
	def test17(self):
		query = """uri[test.result] = '<script type="text/javascript" src="external.js"></script>'"""
		assert self.parser.parse_query(query) == [
			[ n.var.uri, n.test.result, '<script type="text/javascript" src="external.js"></script>', ],
		]
		
	def test18(self):
		query = """test.func("xyz()", 'abc = 123') = "what's um, the deal?" """
		assert self.parser.parse_query(query) == [
			[ n.var.bnode1, n.call.arg1, 'xyz()', ],
			[ n.var.bnode1, n.call.arg2, 'abc = 123', ],
			[ n.var.bnode1, n.test.func, "what's um, the deal?", ],
		]
	
	def test19(self):
		query = """test.func('''xyz() + 'what?' and "what?" ''', 'abc = 123') = "what's um, the deal?" """
		assert self.parser.parse_query(query) == [
			[ n.var.bnode1, n.call.arg1, 'xyz() + \'what?\' and "what?" ', ],
			[ n.var.bnode1, n.call.arg2, 'abc = 123', ],
			[ n.var.bnode1, n.test.func, "what's um, the deal?", ],
		]
	
	def test_parseQuery1(self):
		query = [
			'uri[test.sum] = sum',
		]
		assert self.parser.parse_query(query) == [
			[n.var.uri, n.test.sum, n.var.sum],
		]
	
	def test_parseQuery2(self):
		query = [
			'uri[test.sum] = sum',
			'uri[test.x] = uri2[test.x]',
			[n.var.uri, n.test.x, 1],
		]
		assert self.parser.parse_query(query) == [
			[n.var.uri, n.test.sum, n.var.sum],
			[n.var.uri, n.test.x, n.var.bnode1],
			[n.var.uri2, n.test.x, n.var.bnode1],
			[n.var.uri, n.test.x, 1],
		]
	
	def test_parseQuery3(self):
		query = [
			'image[file.filename] = "/home/dwiel/pictures/stitt blanket/*.jpg"[glob.glob]',
			'thumb = image.thumbnail(image, 4, 4, image.antialias)',
			'thumb_image = thumb[pil.image]',
		]
		ret = self.parser.parse_query(query)
		assert ret == [
			[ n.var.image, n.file.filename, n.var.bnode1, ],
			[ '/home/dwiel/pictures/stitt blanket/*.jpg', n.glob.glob, n.var.bnode1, ],
			[ n.var.bnode2, n.call.arg1, n.var.image, ],
			[ n.var.bnode2, n.call.arg2, 4, ],
			[ n.var.bnode2, n.call.arg3, 4, ],
			[ n.var.bnode2, n.call.arg4, n.image.antialias, ],
			[ n.var.bnode2, n.image.thumbnail, n.var.thumb, ],
			[ n.var.thumb, n.pil.image, n.var.thumb_image, ],
		]
	
	def test_parseQuery4(self):
		query = """
			uri[test.sum] = sum
			uri[test.x] = uri2[test.x]
			uri[test.x] = 1
		"""
		assert self.parser.parse_query(query) == [
			[n.var.uri, n.test.sum, n.var.sum],
			[n.var.uri, n.test.x, n.var.bnode1],
			[n.var.uri2, n.test.x, n.var.bnode1],
			[n.var.uri, n.test.x, 1],
		]
	
	def test_parseKeyword(self):
		query = """
			count[file.count] = _count
		"""
		assert self.parser.parse_query(query) == [
			[n.var['count'], n.file['count'], n.lit_var['count']],
		]
	
	def test_parseBrokenQuery(self):
		query = """
			note[e.tag] _tag
		"""
		p('parsed',self.parser.parse_query(query))
	
	def test_emptyNamespace(self):
		query = """
			note[:tag] = _tag
		"""
		
		assert self.parser.parse_query(query) == [
			[n.var['note'], n['']['tag'], n.lit_var['tag']],
		]
	
	def test_emptyNamespace2(self):
		query = """
			note[.tag] = _tag
		"""
		
		assert self.parser.parse_query(query) == [
			[n.var['note'], n['']['tag'], n.lit_var['tag']],
		]
	
if __name__ == "__main__" :
	unittest.main()


#print parse("image[image.average_color] = color")
#print parse("distance = color.distance(color.red, color)")
#print parse("sparql.order_ascending = color.distance(color.red, image[image.average_color])")

