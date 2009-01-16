# Compiler testing
# this compiler assumes the translations available in loadTranslator

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
compiler = Compiler(cache)

import loadTranslations
loadTranslations.load(compiler, n)

# for easy basic stupid matching type instance
class X():pass
type_instance = type(X())

class PassCompleteReadsTestCase(unittest.TestCase):
	#def test1(self) :
		#ret = compiler.read_translations([
			#'test.u[test.x] = 1',
			#'test.u[test.x] = 10',
			#'test.u[test.y] = 2',
			#'test.u[test.y] = 20',
			#'test.u[test.z] = 100',
			#'test.u[test.div] = div',
		#])
		#print prettyquery(ret)
		#assert ret == [
			#[
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 10, ],
				#[ n.test.u, n.test.y, 2, ],
				#[ n.test.u, n.test.y, 20, ],
				#[ n.test.u, n.test.z, 100, ],
				#[ n.test.u, n.test.div, n.var.div, ],
				#[ n.test.u, n.test.sum, 3, ],
				#[ n.test.u, n.test.prod, 300, ],
				#[ n.test.u, n.test.div, 0.029999999999999999, ],
			#], [
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 10, ],
				#[ n.test.u, n.test.y, 2, ],
				#[ n.test.u, n.test.y, 20, ],
				#[ n.test.u, n.test.z, 100, ],
				#[ n.test.u, n.test.div, n.var.div, ],
				#[ n.test.u, n.test.sum, 12, ],
				#[ n.test.u, n.test.prod, 1200, ],
				#[ n.test.u, n.test.div, 0.12, ],
			#], [
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 10, ],
				#[ n.test.u, n.test.y, 2, ],
				#[ n.test.u, n.test.y, 20, ],
				#[ n.test.u, n.test.z, 100, ],
				#[ n.test.u, n.test.div, n.var.div, ],
				#[ n.test.u, n.test.sum, 21, ],
				#[ n.test.u, n.test.prod, 2100, ],
				#[ n.test.u, n.test.div, 0.20999999999999999, ],
			#], [
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 10, ],
				#[ n.test.u, n.test.y, 2, ],
				#[ n.test.u, n.test.y, 20, ],
				#[ n.test.u, n.test.z, 100, ],
				#[ n.test.u, n.test.div, n.var.div, ],
				#[ n.test.u, n.test.sum, 30, ],
				#[ n.test.u, n.test.prod, 3000, ],
				#[ n.test.u, n.test.div, 0.29999999999999999, ],
			#],
		#]

	#def test2(self):
		#ret = compiler.read_translations([
			#'test.u[test.x] = 1',
			#'test.u[test.x] = 2',
			#'test.u[test.y] = 10',
			#'test.u[test.sum] = sum',
		#])
		#assert ret == [
			#[
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 2, ],
				#[ n.test.u, n.test.y, 10, ],
				#[ n.test.u, n.test.sum, n.var.sum, ],
				#[ n.test.u, n.test.sum, 11, ],
			#],
			#[
				#[ n.test.u, n.test.x, 1, ],
				#[ n.test.u, n.test.x, 2, ],
				#[ n.test.u, n.test.y, 10, ],
				#[ n.test.u, n.test.sum, n.var.sum, ],
				#[ n.test.u, n.test.sum, 12, ],
			#],
		#]
	
	#def test3(self):
		#ret = compiler.read_translations([
			#'image[file.filename] = "/home/dwiel/AMOSvid/1065/20080821_083129.jpg"',
			#'thumb = image.thumbnail(image, 4, 4)'
		#])
		#print 'retret',prettyquery(ret)
		#ret[0][5][2] = type(ret[0][5][2])
		#ret[0][6][2] = type(ret[0][6][2])
		#assert ret == [
			#[
				#[ n.var.image, n.file.filename, '/home/dwiel/AMOSvid/1065/20080821_083129.jpg', ],
				#[ n.var.bnode1, n.call.arg1, n.var.image, ],
				#[ n.var.bnode1, n.call.arg2, 4, ],
				#[ n.var.bnode1, n.call.arg3, 4, ],
				#[ n.var.bnode1, n.image.thumbnail, n.var.thumb, ],
				#[ n.var.image, n.pil.image, type_instance, ],
				#[ n.var.thumb, n.pil.image, type_instance, ],
			#],
		#]
	
	## this case should be seperated from activity on my hard drive
	#def test_glob_glob(self):
		#ret = compiler.read_translations([
			#'"/home/dwiel/AMOSvid/*.py"[glob.glob] = filename'
		#])
		#assert ret == [
			#[
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, n.var.filename, ],
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, '/home/dwiel/AMOSvid/generate_thumbnail_images.py', ],
			#],
			#[
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, n.var.filename, ],
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, '/home/dwiel/AMOSvid/imagevid.py', ],
			#],
			#[
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, n.var.filename, ],
				#[ '/home/dwiel/AMOSvid/*.py', n.glob.glob, '/home/dwiel/AMOSvid/find_closest_thumnail.py', ],
			#],
		#]
	
	def test_compile1(self):
		# in this case the compiler should come up with the paths required to 
		# evalutate it, but not actually evaluate it
		ret = compiler.compile([
			'test.u[test.x] = 1',
			'test.u[test.x] = 10',
			'test.u[test.y] = 2',
			'test.u[test.y] = 20',
			'test.u[test.z] = 100',
			'test.u[test.div] = div',
		], input = [], output = ['div'])
		print 'ret',prettyquery(ret)
	
	#def test_compile2(self):
		#ret = compiler.compile([
			#'test.u[test.x] = x',
			#'test.u[test.x] = 10',
			#'test.u[test.y] = 2',
			#'test.u[test.y] = 20',
			#'test.u[test.z] = 100',
			#'test.u[test.div] = div',
		#], input = ['x'], output = ['div'])
		#print 'ret',prettyquery(ret)


if __name__ == "__main__" :
	unittest.main()
