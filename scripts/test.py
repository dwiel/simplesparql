from SimpleSPARQL import *

n = globalNamespaces()
n.bind('', '<http://dwiel.net/express/rule/0.1/>')
n.bind('e', '<http://dwiel.net/express/rule/0.1/>')
n.bind('rdf', '<http://www.w3.org/1999/02/22-rdf-syntax-ns#>')
n.bind('rdfs', '<http://www.w3.org/2000/01/rdf-schema#>')
n.bind('schema', '<http://dwiel.net/express/schema/0.1/>')
n.bind('schema_property', '<http://dwiel.net/express/schema_property/0.1/>')
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('s', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('feed', '<http://dwiel.net/RSSAggregatorBackend/feed/0.1/>')
n.bind('entry', '<http://dwiel.net/RSSAggregatorBackend/entry/0.1/>')
# n.bind('test', '<http://example/test>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')
n.bind('amarok', '<http://amarok.kde.org/rdfs/amarok/0.1/>')
n.bind('mbartist', '<http://musicbrainz.org/mm-2.1/artist/>')
n.bind('lastfm', '<http://dwiel.net/lastfm/0.1/>')

sparql = SimpleSPARQL("http://localhost:2020/sparql")
sparql.setGraph("http://dwiel.net/axpress/testing")
sparql.setNamespaces(n)
sparql.setDebug(True)

url = "http://albany.craigslist.org/art/index.rss"

q = {
	n.test.x : 1,
	n.test.y : [
		{
			n.sparql.subject : None,
			n.test.b : 2,
		},{
			n.sparql.subject : None,
			n.test.a : 21,
		},
	],
}

print prettyquery(sparql.read(q))
exit()

# n.s.connect : n.s.unless_exists
# insert the triple (?var test:y 2) if it doesn't already have a value
q = {
	n.test.x : 1,
	n.test.y : {
		n.s.connect : n.s.unless_exists,
		n.s.value : 2
	}
}

# if_empty : set value only if one does not already exist
# update : set value even if one already exists

# n.s.connect : n.s.update
# insert the triple (?var test:y 2) and remove the old value if there is one
q = {
	n.test.x : 1,
	n.test.y : {
		n.s.connect : n.s.update,
		n.s.value : 2
	}
}

# for a non unique property :
# unless_exists : add value to set unless it already exists
# force : add value to set even if it already exists
# if_empty : add value to set only if none yet exist

q = {
	n.test.x : 1,
	n.test.y : [{
		n.s.connect : n.s.unless_exists,
		n.s.value : 2
	}]
}




#### connecting objects
# find all object with n.test.x : 2 and link them to the root object through
# n.test.y.
"""q = {
	n.test.x : 1,
	n.test.y : [{
		n.s.connect : ,
		n.s.value : {
			n.test.x : 2
		}
	}]
}"""
# shorthand
"""q = {
	n.test.x : 1,
	n.test.y : [{
		n.s.create : ,
		n.test.x : 2
	}]
}"""

"""
create :
  one of: [force, unless_exists, unless_connected]
    force : always create it
    unless_exists : create it unless it already exists (then just link to it)
    unless_connected : create it unless one is already connected (then do nothing)
      this is only applicable if this is a subquery to a connect
  optionaly: many (not implemented yet due to safety concerns)
    many : if used, allows multiple objects to match the pattern and be inserted
  optionaly one of: [insert, overwrite, ensure_unique]
    insert (default) : insert even if something is already there
    overwrite : overwrite any values currently there
    ensure_unique : insert unless something is already there

connect :
  optionaly: many (not implemented yet due to safety concerns)
    many : if used, allows multiple objects to match the pattern and be inserted
  one of: [insert, overwrite, ensure_unique]
    insert : insert even if something is already there
    overwrite : overwrite any values currently there
    ensure_unique : insert unless something else is already there

Notes: 
* when thinking about how these might get caught by plugins, consider paths which
  in a read would have a list in them.  In the write, the list may not be there
* the create and connect clauses only apply to the triples in that dictionary.
  if in an object with a create clause another object is referenced as the 
  value of a property, then that nested object will not be created.  It will
  found in the graph and connected.

General Algorithm:
+ build the triples of the where clause.
+ for each where clause, find the subject and make sure there is only one, 
    if that is what the query specifies
    * note that doing it this way requires that the subject not be a bnode.
      One way to get around that limitation would be to first check to see 
      that there are the correct # of subjects and then if it is a bnode, 
      re-locate the subject in the where query of the final insert
+ check to see if inserted objects already exist or if there are already 
  values there.  This can be started by the above process.  Each property 
  being changed (connect) can be pulled with an optional value.
+ write insert query referencing subjects found earlier

defns:
object: a set of triples with one subject.  each dictionary in a query defines
  an object. (except for a connect, value dictionary)

The Passes:
+ if the query is a dictionary and not a list, wrap it in a list
+ assign each object a variable number (not objects which are connect, value)
+ move all write directives and key value pairs which are to be written to 
  write directives in the root.  If a read object becomes completely disconnected 
  in this process, make the root a list of distinct obejcts
  * move each write object into a list at the root.  Keep track of the subject 
    variable name
+ create new root object for each query with the parameters query and variables.
  query is the old root without the variables
  variables is a dictionary mapping variable name to path in the query
+ replace each query with the result of reading that query
+ ensure that the number of results from each read matches 
+ for each write object which is create : unless_exists, try to find an 
  existing object that matches.  If there is only one, replace that write
  query with n.s.subject : that_uri. also deal with many option
+ for each write object which is create : unless_connected, try to find out if
  an object like this is already connected. also deal with many option
+ for each connect : overwrite, delete any triple previous connected
+ for each connect : ensure_unique, 
+ write queries
"""


q = {
	n.test.x : 1,
	n.test.y : [{
		n.s.create : n.s.unless_exists,
		n.test.x : 2
	}]
}

# if it is, then how do you set n.test.y to a list with only one thing x:2 no
# matter if there is something already there?
{
	n.test.x : 1,
	n.test.y : [{
		n.s.connect : n.s.delete,
		None : None
	}]
}
{
	n.test.x : 1,
	n.test.y : [{
		n.s.create : n.s.unless_exists,
		n.test.x : 2
	}]
}

# find var1: artist_id 9834
#   make sure there is only one
# find var2: artist with label Bad Plus and an mbartist.id 
#   make sure there is only one
# from var1 property similar_artists, create an object with a 
#   similarity_constant and artist var2
q = {
	n.amarok.artist_id : 9834,
	n.lastfm.similar_artists : {
		n.s.create : n.s.unless_connected,
		n.lastfm.similarity_constant : 1.325,
		n.lastfm.artist : {
			n.s.connect : n.s.insert,
			n.rdfs.label : 'Bad Plus',
			n.mbartist.id : None
		}
	}
}

# same as above, but will link to all bands with the name 'Bad Plus' and a 
# musicbrainz artist id (doesn't really make sence in this context)
q = {
	n.amarok.artist_id : 9834,
	n.lastfm.similar_artists : {
		n.s.create : n.s.unless_connected,
		n.lastfm.similarity_constant : 1.325,
		n.lastfm.artist : {
			n.s.connect : [n.s.insert, n.s.many],
			n.rdfs.label : 'Bad Plus',
			n.mbartist.id : None
		}
	}
}

"""
this query isn't possible in one SPARQL ...
"""
"""insert = [(var1, similar_artists, uri1),
					(uri1, similarity_constant, 1.325),
				  (bnode1, artist, [] ...),
				 ]"""
where = [	(var1, artist_id, 9834),
				]
					
	

q = {
	n.test.x : 1,
	n.test.y : 1,
	n.s.create : n.s.unless_exists
}

sparql.write(q)


exit()



q = [{
	n.feed.url : None,
	n.feed.entry : [{
		n.entry['title'] : None,
	}],
	n.sparql.sort : n.feed.url,
	n.sparql.limit : 10,
	n.sparql.subject : None
}]

q = {
	n.test.x : 1,
	n.test.y : 2,
	n.test.sum : None
}

q = [{
	None : "The Books",
	n.sparql.subject : None
}]

q = [{
	
}]

print sparql.read(q)

exit()










q = [{
  n.feed.url : None,
  n.feed.entry : [{
    n.sparql.delete : n.sparql.delete,
  }]
}]

print sparql.write(q)

exit()

q = {
#	n.sparql.create : n.sparql.unless_exists,
	n.sparql.delete : n.sparql.delete,
	n.sparql.any : n.sparql.any,
	n.feed.url : 'test url\nnewline'
}

ret = sparql.write(q)
print ret
print

exit()

# possible ways you'd want to delete something:
# delete only the triples specified
# delete all triples connected to the root object

# delete all triples matching ?var feed:url 'test url'
q = {
	n.feed.url : 'test url',
	n.sparql.delete : n.sparql.delete,
}

# delete: ?var feed:url 'test url' . ?var ?x ?y
q = {
	n.feed.url : 'test url',
	n.sparql.any : n.sparql.any,
	n.sparql.delete : n.sparql.delete,
}

# delete: ?var feed:url 'test url' . ?var ?x ?y . ?y ?z ?w
q = {
	n.feed.url : 'test url',
	n.sparql.any : [n.sparql.any, {n.sparql.any : n.sparql.any}],
	n.sparql.delete : n.sparql.delete,
}


q = [
	{
		n.feed.url : None
	}
]

ret = sparql.read_parse(q)
#print ret
print [str(o[n.feed.url]) for o in ret]
print

exit()

q = [
	{
		n.feed.entry : [{
			n.entry['title'] : []
		}]
	}
]

ret = sparql.read_parse(q)
print ret
print ret[0][n.feed.entry][0][n.entry['title']]
print ret[0][n.feed.entry][1][n.entry['title']]
print ret[0][n.feed.entry][2][n.entry['title']]

# ret, triples, exp, imp = sparql.read_parse(q)
#print 'read_parse', ret
#print 'triples', triples
#print 'exp', exp
#print 'imp', imp
