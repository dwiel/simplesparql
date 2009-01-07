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


ret = translator.read_translations([
	[n.test.u, n.test.x, 1],
#	'test.u[test.x] = 1',
	[n.test.u, n.test.x, 10],	
	[n.test.u, n.test.y, 2],
	[n.test.u, n.test.y, 20],
#	[n.test.u, n.test.sum, n.var.sum],
	[n.test.u, n.test.z, 100],
	[n.test.u, n.test.div, n.var.div],
#	'test.u[test.div] = div',
#	[n.test.u, n.test.prod, n.var.prod],
])

# make a list from the returned generator
ret = [[y for y in x] for x in ret]
print prettyquery(ret)

exit()







ret = translator.read_translations([
#	[n.var.album, n.music.playable, True],
	[n.var.album, n.music.artist, n.var.similar_artist],
	[n.var.artist, n.lastfm.similar_to, n.var.similar_artist],
	[n.var.artist, n.rdfs.label, 'Lavender Diamond']
], [n.var.album])

alt_query = """
	artist[rdfs.label] = 'Lavender Diamond'
	artist[lastfm.similar_to] = similar_artist
	album[music.artist] = similar_artist
	album[music.playable] = True
"""

""" or
	artist = {
		rdfs.label : 'Lavendar Diamond',
		lastfm.similar_to : similar_artist
	}
	album = {
		music.artist : similar_artist,
		music.playable : True
	}
"""

#{
	#n.rdfs.label : 'Lave',
	#n.lastfm.similar_to : [{
		#n.music.album : {
			#n.music.playable : True,
			#n.sparql.subject : None,
		#}
	#}]
#}

# make a list from the returned generator
ret = [[y for y in x] for x in ret]
print prettyquery(ret)

#self.sparql.write({
				#n.sparql.create : n.sparql.unless_exists,
				#n.cache.value : ret,
				#n.cache.date : time.time(),
				#n.cache.plugin : plugin[n.meta.name],
				#n.cache.vars : vars,
			#})

print '---------------'
print 'new-read'
print sparql.new_read([
	[n.tvar.x, n.cache.plugin, 'name'],
	[n.tvar.x, n.cache.vars, {
		n.var.xyz : 1,
		n.var.abc : 2,
	}],
	[n.tvar.x, n.cache.value, None],
	[n.tvar.x, n.cache.date, None],
])
print

#sparql.new_read([{
	#n.cache.plugin : plugin[n.meta.name],
	#n.cache.vars : vars,
	#n.cache.value : None,
	#n.cache.date : None,
#}])

#sparql.write([
	#[n.bnode.x, n.cache.value, 1],
	#[n.bnode.x, n.cache.date, time.time()],
	#[n.bnode.x, n.cache.plugin, 'plugin name'],
	#[n.bnode.x, n.cache.vars, {
		#n.var.xyz : 1,
		#n.var.abc : 2,
	#}],
#])

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

sparql.register_translation({
	n.meta.input : [
		[n.meta_var.album, n.music.album_name, n.var.album_name],
	],
	n.meta.output : [
		[n.var.album, n.music.album_name, n.var.album_name],
	],
	n.meta.function : foo
})

ret = sparql.eval_translations([
	[n.test.x, n.music.album_name, "Beat Romantic"]
])

ret = [x for x in ret]
print prettyquery(ret)
exit()

ret = sparql.eval_translations([
	[n.test.x, n.music.album_name, "Beat Romantic"]
])

ret = [x for x in ret]
print prettyquery(ret)

#ret = sparql.read_translations([
	#[n.test.x, n.music.album_name, "Beat Romantic"],
	#[n.var.album, n.music.album_name, n.var.album_name],
#])

#ret = [x for x in ret]
#print ret
#print SimpleSPARQL.prettyquery(ret)





#print sparql.new_read([
	#[n.var.x, n.test.x, 1]
#], n.var.x)

