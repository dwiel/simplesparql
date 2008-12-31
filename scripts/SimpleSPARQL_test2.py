import time
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






#def foo(vars) :
	#vars[n.var.sum] = vars[n.var.x] + vars[n.var.y]
#sparql.register_translation({
	#n.meta.name : 'sum',
	#n.meta.input : [
		#[n.var.uri, n.test.x, n.var.x],
		#[n.var.uri, n.test.y, n.var.y],
	#],
	#n.meta.output : [
		#[n.var.uri, n.test.sum, n.var.sum],
	#],
	#n.meta.function : foo
#})

#def foo2(vars) :
	#vars[n.var.prod] = vars[n.var.sum] * vars[n.var.z]
#sparql.register_translation({
	#n.meta.name : 'product',
	#n.meta.input : [
		#[n.var.uri, n.test.sum, n.var.sum],
		#[n.var.uri, n.test.z, n.var.z],
	#],
	#n.meta.output : [
		#[n.var.uri, n.test.prod, n.var.prod],
	#],
	#n.meta.function : foo2
#})

#def div(vars) :
	#vars[n.var.div] = float(vars[n.var.sum]) / vars[n.var.z]
#sparql.register_translation({
	#n.meta.name : 'division',
	#n.meta.input : [
		#[n.var.uri, n.test.sum, n.var.sum],
		#[n.var.uri, n.test.z, n.var.z],
	#],
	#n.meta.output : [
		#[n.var.uri, n.test.div, n.var.div],
	#],
	#n.meta.function : div
#})

#ret = sparql.read_translations([
	#[n.test.u, n.test.x, 1],
	#[n.test.u, n.test.y, 2],
	#[n.test.u, n.test.z, 100],
	#[n.test.u, n.test.div, n.var.div],
	#[n.test.u, n.test.prod, n.var.prod],
#])

## make a list from the returned generator
#ret = [[y for y in x] for x in ret]
#print ret
#print SimpleSPARQL.prettyquery(ret)

#exit()
















sparql.register_translation({
	n.meta.name : 'rdfs.label => music.artist_name',
	n.meta.input : [
		[n.var.artist, n.rdfs.label, n.var.artist_name],
	],
	n.meta.output : [
		[n.var.artist, n.music.artist_name, n.var.artist_name],
	],
	n.meta.function : lambda x : None,
	n.meta.reversable : True,
	n.meta.scale : 1,
	n.meta.expected_time : 0,
})
	
# WARNING: the output of this transformation does not always result in > 1 
# set of bindings.  (If the artist is not in lastfm - or if there is no inet?)
def lastfmsimilar(vars) :
	# vars[n.var.similar_artist] = lastfm.Artist(vars[n.var.artist_name]).getSimilar()
	# vars[n.var.similar_artist] = ['Taken By Trees', 'Viva Voce', 'New Buffalo']
	#artsts = []
	#url = 'http://ws.audioscrobbler.com/2.0/artist/%s/similar.txt' % artist_name
	#f = urllib.urlopen(url)
	#for line in f :
		#tokens = line.strip().split(',')
		#artist.append({
			#n.lastfm.similarity_measure : float(tokens[0]),
			#n.lastfm.mbid : tokens[1],
			#n.lastfm.name : tokens[2],
		#})
	#vars[n.var.similar_artist] = artists
	vars[n.var.similar_artist] = [
		{
			n.lastfm.name : 'Taken By Trees',
			n.lastfm.similarity_measure : 100,
			n.lastfm.mbid : '924392349239429urjf834',
		},
		{
			n.lastfm.name : 'Viva Voce',
			n.lastfm.similarity_measure : 96,
			n.lastfm.mbid : '88r328394nc3jr43jdmmnn',
		}
	]

sparql.register_translation({
	n.meta.name : 'last.fm similar artists',
	n.meta.input : [
		[n.var.artist, n.music.artist_name, n.var.artist_name],
	],
	n.meta.output : [
		[n.var.artist, n.lastfm.similar_to, n.var.similar_artist],
		[n.var.similar_artist, n.lastfm.artist_name, n.var.similar_artist]
	],
	n.meta.function : lastfmsimilar,
	n.meta.scale : 100,
	n.meta.expected_time : 1,
	n.cache.expiration_length : 2629743 # 1 month in seconds
})

#input : [
	#[var.x, is, '%person%s %relationship%']
#],
#output : [
	#[var.y, name, '%person%']
	#[var.y, freebase.%relationship%, var.x]
	#[var.x, name, var.name]
#],

	


#read([
	#[var.x, is, 'george bushs daughter'],
	#[var.x, name, var.name]
#], [var.name])




ret = sparql.read_translations([
#	[n.var.album, n.music.playable, True],
	[n.var.album, n.music.artist, n.var.similar_artist],
	[n.var.artist, n.lastfm.similar_to, n.var.similar_artist],
	[n.var.artist, n.rdfs.label, 'Lavender Diamond']
], [n.var.album])

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
print ret
print SimpleSPARQL.prettyquery(ret)

#self.sparql.write({
				#n.sparql.create : n.sparql.unless_exists,
				#n.cache.value : ret,
				#n.cache.date : time.time(),
				#n.cache.plugin : plugin[n.meta.name],
				#n.cache.vars : vars,
			#})

#sparql.write([
	#[n.bnode.x, n.cache.value, 1],
	#[n.bnode.x, n.cache.date, time.time()],
	#[n.bnode.x, n.cache.plugin, 'plugin name'],
	#[n.bnode.x, n.cache.vars, vars],
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
print SimpleSPARQL.prettyquery(ret)
exit()

ret = sparql.eval_translations([
	[n.test.x, n.music.album_name, "Beat Romantic"]
])

ret = [x for x in ret]
print SimpleSPARQL.prettyquery(ret)

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

