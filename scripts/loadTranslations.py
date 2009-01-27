from SimpleSPARQL import *
import os, random

def load(translator, n) :	
	n.bind('math', '<http://dwiel.net/express/math/0.1/>')
	n.bind('type', '<http://dwiel.net/express/type/0.1/>')
	n.bind('flickr', '<http://dwiel.net/express/flickr/0.1/>')
	n.bind('file', '<http://dwiel.net/express/file/0.1/>')
	n.bind('playlist', '<http://dwiel.net/express/playlist/0.1/>')
	n.bind('image', '<http://dwiel.net/express/image/0.1/>')
	n.bind('pil', '<http://dwiel.net/express/python/pil/0.1/>')
	n.bind('glob', '<http://dwiel.net/express/python/glob/0.1/>')
	n.bind('call', '<http://dwiel.net/express/call/0.1/>')
	
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
##		n.meta.function : sum
	#})

	def sum(vars) :
		print prettyquery(vars)
		vars['sum'] = vars['x'] + vars['y']
	translator.register_translation({
		n.meta.name : 'sum',
		n.meta.input : """
			foo[test.x] = _x
			foo[test.y] = _y
		""",
		n.meta.output : [
			'foo[test.sum] = _sum',
		],
		n.meta.function : sum,
		n.meta.constant_vars : ['foo'],
	})
	"""
	uri[test.sum] = x + y
	uri[test.x] = x
	uri[test.y] = y
	"""
	
	def prod(vars) :
		vars['prod'] = float(vars['sum']) * vars['z']
	translator.register_translation({
		n.meta.name : 'product',
		n.meta.input : [
			'uri[test.sum] = _sum',
			'uri[test.z] = _z',
		],
		n.meta.output : [
			'uri[test.prod] = _prod',
		],
		n.meta.function : prod,
		n.meta.constant_vars : ['uri'],
	})
	
	def div(vars) :
		vars['div'] = float(vars['sum']) / vars['z']
	translator.register_translation({
		n.meta.name : 'division',
		n.meta.input : [
			'uri[test.sum] = _sum',
			'uri[test.z] = _z',
		],
		n.meta.output : [
			'uri[test.div] = _div',
		],
		n.meta.function : div,
		n.meta.constant_vars : ['uri'],
	})

	translator.register_translation({
		n.meta.name : 'rdfs.label => music.artist_name',
		n.meta.input : [
			'artist[rdfs.label] = artist_name',
		],
		n.meta.output : [
			'artist[music.artist_name] = artist_name',
		],
		n.meta.function : lambda x : None,
		n.meta.reversable : True,
		n.meta.scale : 1,
		n.meta.expected_time : 0,
	})
	
	# note: this doesn't actually work ...
	# how could it?
	def is_num(vars) :
		vars['is_num'] = isinstance(vars['x'], (int, long, float))
		print 'is_num:',vars['is_num']
	translator.register_translation({
		n.meta.name : 'is_num',
		n.meta.input : """
			type.is_num(_x) = ?is_num
		""",
		n.meta.output : """
			type.is_num(_x) = _is_num
		""",
		n.meta.function : is_num,
		n.meta.constant_vars : ['x'],
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
		url = 'http://ws.audioscrobbler.com/2.0/artist/%s/similar.txt' % urllib.quote(vars['artist_name'])
		f = urllib.urlopen(url)
		
		lasttime = vars['getlastime']()
		while lasttime + 1 < time.time() :
			# sleep a little
			pass
		
		vars['setlasttime'](time.time())
		
		outputs = []
		for line in f :
			tokens = line.strip().split(',')
			outputs.append({
				'similarity_measure' : float(tokens[0]),
				'mbid' : tokens[1],
				'name' : tokens[2],
			})
		return outputs[:10]
		print 'vars',prettyquery(outputs[:10])
		
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
			'artist[music.artist_name] = _artist_name',
		],
		n.meta.output : [
			'artist[lastfm.similar_to] = _similar_artist',
			'_similar_artist[lastfm.similarity_measure] = _similarity_measure',
			'_similar_artist[lastfm.mbid] = _mbid',
			'_similar_artist[lastfm.name] = _name',
		],
		n.meta.function : lastfmsimilar,
		n.meta.scale : 100,
		n.meta.expected_time : 1,
		n.cache.expiration_length : 2678400, # 1 month in seconds
		n.meta.constant_vars : ['artist'],
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
	# and a query which uses it like this:
	"""
	music.artist_name(artist) = 'Lavender Diamond'
	music.artist(album) = lastfm.similar_to(artist)
	music.playable(album) = True
	"""
	
	def flickr_make_url(photo) :
		# 'http://farm{farm-id}.static.flickr.com/{server-id}/{id}_{secret}.jpg'
		# 'http://farm{farm-id}.static.flickr.com/{server-id}/{id}_{secret}_[mstb].jpg'
		return 'http://farm%s.static.flickr.com/%s/%s_%s_%s.jpg' % \
						(photo.attrib['farm'], photo.attrib['server'], photo.attrib['id'], photo.attrib['secret'], 'b')
	
	def flickr_photos_search(vars) :
		import flickrapi
		flickr = flickrapi.FlickrAPI('91a5290443e54ec0ff7bcd26328963cd', format='etree')
		photos = flickr.photos_search(tags=[vars['tag']])
		urls = []
		for photo in photos.find('photos').findall('photo') :
			urls.append(flickr_make_url(photo))
		vars['url'] = urls
		
	translator.register_translation({
		n.meta.name : 'flickr photos search',
		n.meta.input : [
			'image[flickr.tag] = _tag',
#			'image[flickr.tag] ?= tag', # TODO: ?= means optionally equal to
#			'optional(image[flickr.tag] = tag)',
#			'optional(image[flickr.user_id] = user_id)',
#			...
		],
		n.meta.output : [
			'image[file.url] = _url',
		],
		n.meta.function : flickr_photos_search,
		n.cache.expiration_length : 2678400,
		n.meta.requires : 'flickrapi', # TODO: make this work
		n.meta.constant_vars : ['image'],
	})
	
	def load_image(vars) :
		from PIL import Image
		im = Image.open(vars['filename'])
		im.load() # force the data to be loaded (Image.open is lazy)
		vars['pil_image'] = im
	translator.register_translation({
		n.meta.name : 'load image',
		n.meta.input : [
			'image[file.filename] = _filename'
		],
		n.meta.output : [
			'image[pil.image] = _pil_image'
		],
		n.meta.function : load_image,
		n.meta.constant_vars : ['image'],
	})
		
	def image_thumbnail(vars) :
		from PIL import Image
		im = vars['pil_image']
		# print 'im',prettyquery(im)
		im.thumbnail((int(vars['x']), int(vars['y'])), Image.ANTIALIAS)
		vars['thumb_image'] = im
	translator.register_translation({
		n.meta.name : 'image thumbnail',
		n.meta.input : [
			'image[pil.image] = _pil_image',
			'thumb = image.thumbnail(image, _x, _y)',
		],
		n.meta.output : [
			'thumb[pil.image] = _thumb_image',
		],
		n.meta.function : image_thumbnail,
		n.meta.constant_vars : ['image', 'thumb'],
	})






	def playlist_enuque(vars):
		pass
	translator.register_translation({
		n.meta.name : 'playlist enqueue',
		n.meta.input : [
			'playlist.enqueue(playlist.playlist, album) = True',
			'album[music.track] = track',
			'track[file.url] = url',
			'track[music.title] = title',
			'track[music.track_number] = track_number',
		],
		n.meta.output : [
		],
		n.meta.function : playlist_enuque,
		n.meta.side_effect : True,
	})
	
	
	
	
	
	## how to express a SQL query in this language?
	## this is going to require more thinking ...
	## the SQL query schema might be useful here
	## so might some kind of macros ... wow
	#def foo(vars):
		#pass
	#translator.register_translation({
		#n.meta.name : 'sql_where',
		#n.meta.input : [
			#'sql[sql.connection] = connection',
			#'sql[sql.select] = col_name',
			#'sql[sql.select_from] = table_name',
			#'sql[sql.where] = col_name'
		#],
		#n.meta.output : [
		#],
		#n.meta.function : foo,
	#})
	
	
	
	
	
	"""
	"/home/dwiel/*.jpg[glob.glob] = "/home/dwiel/abc.jpg"
	
	if the input pattern is *anything* (var or literal) then the above is actually
	a query to finish out that list of globs.  Is that what we want?
	
	what if _ only matches a variable or missing value
	
	then the above just makes a statement, its not a query
	
	but then you also sometime want a literal or a variable, anything will do
		as in a uri/object name you don't care about
	
	types of variables:
		literal or variable  name   =>  var.name
		only a literal       _name  =>  lit_var.name   (this just means bound - could be a bnode)
		only a variable      ?name  =>  meta_var.name
	
	will we inevitably find more types of variables we want?
		maybe only accepts a literal of type string
		could be done with:
	
	isupper(var) = bool =>
	isupper(var) = bool
	def foo(vars) :
		if vars['var'].isupper() :
			vars['bool'] = True
		else :
			vars['bool'] = False
		
	
	how else could this kind of matching be done?
	
	The 'type' information could also be infered from the function and the variables it uses.
	That might be [impossibly] hard to detect...
	
	The 'type' information could also just be another meta data line:
		n.meta.input_variable_type : {
			'filename' : 'variable',
			'pattern' : 'literal'
		},
		n.meta.output_variable_type : {
			'filename' : 'literal',
			'pattern' : 'literal'
		},
	
	for now, the prefix on the variable name makes sense.  It would be easy to add
	a meta-data like above to the translation syntax
	"""
	
	
	def glob_glob(vars):
		import glob
		vars['out_filename'] = glob.glob(vars['pattern'])
	translator.register_translation({
		n.meta.name : 'glob glob',
		# This doesn't work!
		#n.meta.input : [
			#'_pattern[glob.glob] = ?filename'
		#],
		#n.meta.output : [
			#'_pattern[glob.glob] = _out_filename'
		#],
		# this does ?
		n.meta.input : [
			'glob[glob.glob] = _pattern'
		],
		n.meta.output : [
			'glob[file.filename] = _out_filename'
		],
		n.meta.function : glob_glob,
		n.meta.constant_vars : ['glob'],
	})
	
	
	def glob_glob(vars):
		import glob
		vars['out_filename'] = glob.glob(vars['pattern'])
	translator.register_translation({
		n.meta.name : 'glob glob',
		n.meta.input : [
			'glob.glob(_pattern) = foo[file.filename]'
		],
		n.meta.output : [
			'foo[file.filename] = _out_filename'
		],
		n.meta.function : glob_glob,
		n.meta.constant_vars : ['glob'],
	})
	#def foo(vars):
		#pass
	#translator.register_translation({
		#n.meta.name : '',
		#n.meta.input : """
		#""",
		#n.meta.output : """
		#""",
		#n.meta.function : foo,
		#n.meta.constant_vars : [],
	#})


	def download_tmp_file(vars):
		#TODO don't depend on wget ...
		vars['filename'] = 'axpress.tmp%s' % str(random.random()).replace('.','')
		os.system('wget %s -O %s' % (vars['url'], vars['filename']))
	translator.register_translation({
		n.meta.name : 'download_tmp_file',
		n.meta.input : """
			file[file.url] = _url
		""",
		n.meta.output : """
			file[file.filename] = _filename
		""",
		n.meta.function : download_tmp_file,
		n.meta.constant_vars : ['file'],
	})
	



"""







new_final_bindings [
  [
    [ n.var.image, n.file.filename, '/home/dwiel/AMOSvid/1065/20080821_083129.jpg', ],
    [ n.var.bnode1, n.call.arg1, n.var.image, ],
    [ n.var.bnode1, n.call.arg2, 4, ],
    [ n.var.bnode1, n.call.arg3, 4, ],
    [ n.var.bnode1, n.image.thumbnail, n.var.thumb, ],
    [ n.var.image, n.pil.image, <PIL.JpegImagePlugin.JpegImageFile instance at 0x837d8cc>, ],
    [ n.var.thumb, n.pil.image, <PIL.JpegImagePlugin.JpegImageFile instance at 0x837d8cc>, ],
  ],
]

applying image thumbnail
binding {
  n.var._ : n.var.thumb,
  n.var.bnode1 : n.var.bnode1,
  n.var.image : <PIL.JpegImagePlugin.JpegImageFile instance at 0x837d8cc>,
  n.var.thumb : n.var.thumb,
  n.var.x : 4,
  n.var.y : 4,
}





"""
