from SimpleSPARQL import SimpleSPARQL

sparql = SimpleSPARQL("http://dbpedia.org/sparql")

n = sparql.n
n.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
n.bind('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
n.bind('dbpedia2', 'http://dbpedia.org/property/')

# the area in Km^2 of things labeled England
print sparql.quickread({
	n.rdfs.label : u"England",
	n.dbpedia2.areaKm : None
})[0]

# the types which the Prime Minister of places things labeled England
q = {
	n.rdfs.label : u"England",
	n.dbpedia2.primeMinister : {
		n.rdf.type : None
	}
}
for type in sparql.quickread(q) :
	print type

print 'objs'
for obj in sparql.read(q) :
	print obj
	
print sparql.ask({ n.rdfs.label : u"England", 
                   n.dbpedia2.primeMinister : {
									   n.rdfs.label : u"Tony Blair"
									 }
								 })
print sparql.ask({ n.rdfs.label : "England", 
                   n.dbpedia2.primeMinister : {
									   n.rdfs.label : "Gordon Brown"
									 }
								 })

# and if you could do writes to dbpedia:
obj = {
	n.rdfs.label : "Hello World",
	n.sparql.create : n.sparql.unless_exists
}
#sparql.write(obj)

#    SELECT ?label
#    WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }

#sparql = SimpleSPARQL("http://localhost:2020/sparql")
#sparql.n.bind('feed', '<http://dwiel.net/RSSAggregatorBackend/feed/0.1/>')
#sparql.n.bind('entry', '<http://dwiel.net/RSSAggregatorBackend/entry/0.1/>')
#n = sparql.n

#print sparql.ask({n.feed.url : None})
#print sparql.ask({n.feed.url : 'www.google.com'})

# loop through each object which fits this pattern
# None type values are replaced with single values
# [] type values are replaced with a list of values
#for obj in sparql.read({n.feed.url : None}) :
#	print obj
#	print obj[n.feed.url]
	
# TODO: Throw error: too many values for n.feed.entry (well, if it weren't a bnode)
#for obj in sparql.read({n.feed.url : None, n.feed.entry : None}) :
#	print obj


#for obj in sparql.read({
		#n.feed.url : None,
		#n.feed.entry : {
			#n.entry['title'] : None
		#}
	#}) :
	#print obj[n.feed.url], obj[n.feed.entry][n.entry['title']]

# or

# loop through each value which fits this pattern
#for url in sparql.quickread({n.feed.url : None}) :
#	print url

#results = sparql.doQuery("SELECT ?url WHERE { ?uri feed:url ?url }")
#for raw_url in results['results']['bindings'] :
	#url = raw_url['url']['value']
	

#for x in sparql.find({n.feed.url : None}) :
	#print x