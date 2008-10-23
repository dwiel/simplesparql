from SimpleSPARQL import SimpleSPARQL

sparql = SimpleSPARQL("http://localhost:2020/sparql")
sparql.n.bind('feed', '<http://dwiel.net/RSSAggregatorBackend/feed/0.1/>')
sparql.n.bind('entry', '<http://dwiel.net/RSSAggregatorBackend/entry/0.1/>')
n = sparql.n

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


for obj in sparql.read({
		n.feed.url : None,
		n.feed.entry : {
			n.entry['title'] : None
		}
	}) :
	print obj[n.feed.url], obj[n.feed.entry][n.entry['title']]

# or

# loop through each value which fits this pattern
#for url in sparql.quickread({n.feed.url : None}) :
#	print url

#results = sparql.doQuery("SELECT ?url WHERE { ?uri feed:url ?url }")
#for raw_url in results['results']['bindings'] :
	#url = raw_url['url']['value']
	

#for x in sparql.find({n.feed.url : None}) :
	#print x