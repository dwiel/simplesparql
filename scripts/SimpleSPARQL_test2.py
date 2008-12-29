from rdflib import *
import SimpleSPARQL

sparql = SimpleSPARQL.SimpleSPARQL("http://localhost:2020/sparql")
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






def foo(vars) :
	vars[n.var.sum] = vars[n.var.x] + vars[n.var.y]
sparql.register_plugin({
	n.meta.name : 'sum',
	n.meta.input : [
		[n.var.uri, n.test.x, n.var.x],
		[n.var.uri, n.test.y, n.var.y],
	],
	n.meta.output : [
		[n.var.uri, n.test.sum, n.var.sum],
	],
	n.meta.function : foo
})

def foo2(vars) :
	vars[n.var.prod] = vars[n.var.sum] * vars[n.var.z]
sparql.register_plugin({
	n.meta.name : 'product',
	n.meta.input : [
		[n.var.uri, n.test.sum, n.var.sum],
		[n.var.uri, n.test.z, n.var.z],
	],
	n.meta.output : [
		[n.var.uri, n.test.prod, n.var.prod],
	],
	n.meta.function : foo2
})

def div(vars) :
	vars[n.var.div] = float(vars[n.var.sum]) / vars[n.var.z]
sparql.register_plugin({
	n.meta.name : 'division',
	n.meta.input : [
		[n.var.uri, n.test.sum, n.var.sum],
		[n.var.uri, n.test.z, n.var.z],
	],
	n.meta.output : [
		[n.var.uri, n.test.div, n.var.div],
	],
	n.meta.function : div
})

ret = sparql.read_plugins([
	[n.test.u, n.test.x, 1],
	[n.test.u, n.test.y, 2],
	[n.test.u, n.test.z, 100],
	[n.test.u, n.test.div, n.var.div],
	[n.test.u, n.test.prod, n.var.prod],
])

# make a list from the returned generator
ret = [[y for y in x] for x in ret]
print ret
print SimpleSPARQL.prettyquery(ret)

exit()
























mylibrary = URIRef('http://localhost/library')

#sparql.new_read([
	#[mylibrary, n.library.contains, n.var.x],
	#[n.var.x, a, n.music.playable],
	#[n.var.x, n.music.source, n.var.source],
	#[n.var.source, n.source.average_latency, n.var.latency],
	#[n.var.x, n.music.artist, n.var.artist],
	#[n.var.artist, n.lastfm.number_of_listeners, n.var.listeners],
	#[n.sparql.sort, n.var.listeners, n.var.latency],
#])

# generate a URI given an album name
def foo(vars) :
	print 'vars',vars
	vars[n.var.album] = n.music_album[vars['album_name']]

sparql.register_plugin({
	n.meta.input : [
		[n.meta_var.album, n.music.album_name, n.var.album_name],
	],
	n.meta.output : [
		[n.var.album, n.music.album_name, n.var.album_name],
	],
	n.meta.function : foo
})

ret = sparql.eval_plugins([
	[n.test.x, n.music.album_name, "Beat Romantic"]
])

ret = [x for x in ret]
print SimpleSPARQL.prettyquery(ret)
exit()

ret = sparql.eval_plugins([
	[n.test.x, n.music.album_name, "Beat Romantic"]
])

ret = [x for x in ret]
print SimpleSPARQL.prettyquery(ret)

#ret = sparql.read_plugins([
	#[n.test.x, n.music.album_name, "Beat Romantic"],
	#[n.var.album, n.music.album_name, n.var.album_name],
#])

#ret = [x for x in ret]
#print ret
#print SimpleSPARQL.prettyquery(ret)





#print sparql.new_read([
	#[n.var.x, n.test.x, 1]
#], n.var.x)

