from SimpleSPARQL import *
import os

def load(translator, n) :	
	n.bind('math', '<http://dwiel.net/express/math/0.1/>')
	
	## TODO: allow a 'function' to accept a variable number of arguments?
	#def sum(vars) :
		#if type(vars[n.var.number1]) == int and type(vars[n.var.number2]) == int :
			#vars[n.var.sum] = vars[n.var.number1] + vars[n.var.number2]
		#else :
			#raise Exception('cant add things that arent numbers .........')
	#translator.register_translation({
		#n.meta.name : 'sum',
		#n.meta.input : [
			#[n.var.uri, n.var.any, n.var.number1],
			#[n.var.uri, n.var.any, n.var.number2],
		#],
		#n.meta.output : [
			#[n.var.uri, n.math.sum, n.var.sum]
		#],
		#n.meta.function : sum
	#})

	def sum(vars) :
		vars[n.var.sum] = vars[n.var.x] + vars[n.var.y]
	translator.register_translation({
		n.meta.name : 'sum',
		n.meta.input : [
			[n.var.uri, n.test.x, n.var.x],
			[n.var.uri, n.test.y, n.var.y],
			#'uri = {
			#	test.x : x,
			#	test.y : y,
			#}'
		],
		n.meta.output : [
			[n.var.uri, n.test.sum, n.var.sum],
			#'uri[test.sum] = sum'
		],
		n.meta.function : sum
	})
	"""
	uri[test.sum] = x + y
	uri[test.x] = x
	uri[test.y] = y
	"""
	
	def prod(vars) :
		vars[n.var.prod] = vars[n.var.sum] * vars[n.var.z]
	translator.register_translation({
		n.meta.name : 'product',
		n.meta.input : [
			[n.var.uri, n.test.sum, n.var.sum],
			[n.var.uri, n.test.z, n.var.z],
		],
		n.meta.output : [
			[n.var.uri, n.test.prod, n.var.prod],
		],
		n.meta.function : prod
	})
	
	def div(vars) :
		vars[n.var.div] = float(vars[n.var.sum]) / vars[n.var.z]
	translator.register_translation({
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

	translator.register_translation({
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
	
		
	# these compilations could translate into direct hashes writen to memory/disk
	# these should basically be able to act like globally (or not) referencable
	# garbage collected variables.
	#   garbage collection would require some way to define when somethign expires
	def pre(vars) :
		vars['getlastime'] = sparql.compile_single_number([
			{
				n.hash.namespace : n.lastfm,
				n.hash.key : 'lastfm-lasttime',
				n.hash.value : None
			}
		])
		
		vars['setlasttime'] = sparql.compile_write([
			{
				n.hash.namespace : n.lastfm,
				n.hash.key : 'lastfm-lasttime',
				n.hash.value : None,
			}
		])
		
	# WARNING: the output of this transformation does not always result in > 1 
	# set of bindings.  (If the artist is not in lastfm - or if there is no inet?)
	def lastfmsimilar(vars) :
	#	vars[n.var.similar_artist] = lastfm.Artist(vars[n.var.artist_name]).getSimilar()
	#	vars[n.var.similar_artist] = ['Taken By Trees', 'Viva Voce', 'New Buffalo']
		artists = []
		url = 'http://ws.audioscrobbler.com/2.0/artist/%s/similar.txt' % urllib.quote(vars[n.var.artist_name])
		f = urllib.urlopen(url)
		
		lasttime = vars['getlastime']()
		while lasttime + 1 < time.time() :
			# sleep a little
			pass
		
		vars['setlasttime'](time.time())
		
		for line in f :
			tokens = line.strip().split(',')
			artists.append({
				n.lastfm.similarity_measure : float(tokens[0]),
				n.lastfm.mbid : tokens[1],
				n.lastfm.name : tokens[2],
			})
		vars[n.var.similar_artist] = artists[:10]
		print 'vars',prettyquery(vars)
		
		#vars[n.var.similar_artist] = [
			#{
				#n.lastfm.name : 'Taken By Trees',
				#n.lastfm.similarity_measure : 100,
				#n.lastfm.mbid : '924392349239429urjf834',
			#},
			#{
				#n.lastfm.name : 'Viva Voce',
				#n.lastfm.similarity_measure : 96,
				#n.lastfm.mbid : '88r328394nc3jr43jdmmnn',
			#}
		#]
	translator.register_translation({
		n.meta.name : 'last.fm similar artists',
		n.meta.input : [
			#'artist[music.artist_name] = artist_name',
			[n.var.artist, n.music.artist_name, n.var.artist_name],
		],
		n.meta.output : [
			#'artist[lastfm.similar_to] = similar_artist',
			[n.var.artist, n.lastfm.similar_to, n.var.similar_artist],
		],
		n.meta.function : lastfmsimilar,
		n.meta.scale : 100,
		n.meta.expected_time : 1,
		n.cache.expiration_length : 2678400, # 1 month in seconds
	})
	"""
	artist[music.artist_name] = artist_name
	artist[lastfm.similar_to] = similar_artist
	similar_artist = #lastfmsimilar
	"""
	# could be compiled to:
	"""
	music.artist_name(artist) :- artist_name
	lastfm.similar_to(artist) :- similar_artist
	python_call(lastfmsimilar, artist_name, similar_artist)
	"""
	# and a query which uses this:
	"""
	music.artist_name(artist) = 'Lavender Diamond'
	music.artist(album) = lastfm.similar_to(artist)
	music.playable(album) = True
	"""
	
	def flickr_make_url(photo) :
		# 'http://farm{farm-id}.static.flickr.com/{server-id}/{id}_{secret}.jpg'
		# 'http://farm{farm-id}.static.flickr.com/{server-id}/{id}_{secret}_[mstb].jpg'
		return 'http://farm%s.static.flickr.com/%s/%s_%s_%s.jpg' % \
		        (photo.farm, photo.server, photo.id, photo.secret, 'b')
	
	def flickr_photos_search(vars) :
		import flickrapi
		flickr = flickrapi.FlickrAPI('91a5290443e54ec0ff7bcd26328963cd', format='etree')
		photos = flickr.photos_search(tags=['sunset'])
		urls = []
		for photo in photos.find('photos').findall('photo') :
			urls.append(flickr_make_url(photo))
		vars[n.file.url] = urls
		
	translator.register_translation({
		n.meta.name : 'flickr photos search',
		n.meta.input : [
			'photo[flickr.tag] ?= tag', # TODO: ?= means optionally equal to
			'optional(photo[flickr.tag] = tag)',
			'optional(photo[flickr.user_id] = user_id)',
#			...
		],
		n.meta.output : [
			'photo[file.url] = url',
		],
		n.meta.function : flickr_photos_search,
		n.cache.expiration_length : 2678400,
		n.meta.requires : 'flickrapi' # TODO: make this work
	})






