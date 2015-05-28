# simplesparql
SimpleSPARQL allows queries to SPARQL endpoints in a very simple language similar to MQL [1]. The query language is designed specifically for python and uses python dictionaries in the same way as MQL.

## Example Code:

```

>>> from SimpleSPARQL import SimpleSPARQL
>>> sparql = SimpleSPARQL("http://dbpedia.org/sparql")
>>> n = sparql.n
>>> n.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
>>> n.bind('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
>>> n.bind('dbpedia2', 'http://dbpedia.org/property/')

>>> # the area in Km^2 of things labeled England
>>> print sparql.quickread({
>>>                           n.rdfs.label : u"England",
>>>                           n.dbpedia2.areaKm : None
>>>                        })[0]
130395

>>> # The Prime Minister of England's types
>>> q = {
>>>		n.rdfs.label : u"England",
>>>		n.dbpedia2.primeMinister : {
>>>			n.rdf.type : None
>>>		}
>>> 	}
>>> for type in sparql.quickread(q) :
>>>	print type
http://xmlns.com/foaf/0.1/Person
http://dbpedia.org/class/yago/PrimeMinistersOfTheUnitedKingdom
http://dbpedia.org/class/yago/ChancellorsOfTheExchequerOfTheUnitedKingdom
http://dbpedia.org/class/yago/LeadersOfTheBritishLabourParty
http://dbpedia.org/class/yago/AcademicsOfTheUniversityOfEdinburgh
http://dbpedia.org/class/yago/RectorsOfTheUniversityOfEdinburgh
http://dbpedia.org/class/yago/PeopleFromGlasgow
http://dbpedia.org/class/yago/AcademicsOfTheOpenUniversity
...

>>> for obj in sparql.read(q) :
>>>	print obj
{
	rdflib.URIRef('http://dbpedia.org/property/primeMinister'):{
		rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'): u'http://dbpedia.org/ontology/OfficeHolder#Class'
	},
	rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'): u'England'
}
{
	rdflib.URIRef('http://dbpedia.org/property/primeMinister'):{
		rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'): u'http://dbpedia.org/ontology/OfficeHolder#Class'
	},
	rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'): u'England'
}
{
	rdflib.URIRef('http://dbpedia.org/property/primeMinister'):{
		rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'): u'http://dbpedia.org/ontology/OfficeHolder#Class'
	},
	rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'): u'England'
}
...
	
>>> print sparql.ask({ n.rdfs.label : u"England", 
                       n.dbpedia2.primeMinister : { n.rdfs.label : u"Tony Blair" }
                     })
False

>>> # and if you could do writes to dbpedia:
>>> obj = {
>>>		n.rdfs.label : "Hello World",
>>>		n.sparql.create : n.sparql.unless_exists
>>>       }
>>> sparql.write(obj)

```

 [1] http://www.freebase.com/view/en/documentation
