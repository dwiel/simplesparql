from SimpleSPARQL import *

n = Namespaces.globalNamespaces()
n.bind('sparql', '<http://dwiel.net/express/sparql/0.1/>')
n.bind('test', '<http://dwiel.net/express/test/0.1/>')

def prettyquery(query, tabs = '', indent = '  ', namespaces = n) :
	s = prettyquery_helper(query, tabs, indent, namespaces)
	lines = s.split('\n')
	new_lines = []
	for line in lines :
		if line.strip() == '{' and len(new_lines) and new_lines[-1].strip() == '},' :
			new_lines[-1] += ' {'
		elif line.strip() == ',' :
			new_lines[-1] += ','
		else :
			new_lines.append(line)
	if len(new_lines[-1]) == 0 :
		new_lines.pop()
	return '\n'.join(new_lines)

def prettyquery_helper(query, tabs = '', indent = '  ', namespaces = n) :
	"""
	return a pretty string of the query
	"""
	s = ""
	if isinstance(query, dict) :
		s += '{\n'
		prettykeys = [(prettyquery_helper(k, tabs+indent, indent), k) for k in query]
		for prettyk, k in sorted(prettykeys) :
			s += tabs + indent + prettyk + ' : ' + prettyquery_helper(query[k], tabs + indent, indent) + ',\n'
		s += tabs + '}'
	elif isinstance(query, list) :
		if len(query) == 0 :
			s += '[]\n'
		else :
			prettylist = [prettyquery_helper(i, tabs+indent, indent) for i in query]
			if len(query) <= 3 and any(['\n' not in item for item in prettylist]) :
				s += '['
				for item in prettylist :
					s += ' ' + item + ','
				s += ' ]\n'
			else :
				s += '[\n'
				for item in prettylist :
					s += tabs + indent + item + ',\n'
				s += tabs + ']\n'
	elif isinstance(query, tuple) :
		s += '(%s)' % prettyquery_helper(list(query), tabs, indent, namespaces)
	elif isinstance(query, set) :
		s += 'set(%s)' % prettyquery_helper(list(query), tabs, indent, namespaces)
	elif isinstance(query, URIRef) :
		return unicode(namespaces.shortenForN(query))
	elif isinstance(query, Literal) :
		if query.datatype == rdflib.URIRef('http://www.w3.org/2001/XMLSchema#float') or \
		   query.datatype == rdflib.URIRef('http://www.w3.org/2001/XMLSchema#int') :
			return unicode(query.toPython())
		else :
			return repr(unicode(query))
	else :
		s += repr(query)
	
	return s

if __name__ == '__main__' :
	print prettyquery_helper([{
		'xyz' : 1,
		'abc' : 2,
		'g' : 13,
		'i' : 15,
		'r' : 16,
		't' : 17,
		n.sparql.create : n.sparql.unless_exists,
		},{
		'qwe' : 1,
		'rty' : 2
		}])
