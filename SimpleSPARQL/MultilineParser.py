import Namespaces
import Parser
from Utils import sub_var_bindings, find_vars, debug
import re
from PrettyQuery import prettyquery

"""
multiline is a way to allow reading and writing to multiple 'places' without
requiring the compiler to figure out where they are

after parsing a multiline query:
	compile query as far as possible
		
	figure out which objects need to be copied to protect from side-effects
"""

re_where_at = re.compile('^(\w+)\s+(\w+)\s*:$')
def fn_where_at(g) :
	pass


"""

just need to implement this where the query is a parsed all at once with a 
multiline re matcher.  add the part which figures out how big it is, but around
ne with no restriction on new lines in the re.compile.  The part which is 
matched is the part which is returned right now by fn(lines) => re.match('\n'.join(line))

"""

"""
where sparql:
#	image[tag.tag] = ['AMOS', 1065]
	image[file.filename] = "/home/dwiel/AMOSvid/1065/*.jpg"[glob.glob]
where translate:
	thumb = image.thumbnail(image, 4, 4, image.antialias)
	thumb_image = thumb[pil.image]
write sparql:
	image[amos.thumb] = thumb
	thumb[pil.image] = thumb_image

each of the sub_queries:
	if it is a read, need to find all possible sets of values each of the 
		variables could contain
	plug each of the existing bindings into the next sub-query
"""
	

class Translator() :
	def __init__(self, re, fn, bound_vars, is_read) :
		self.re = re
		self.fn = fn
		self.bound_vars = bound_vars
		self.is_read = is_read

class MultilineParser() :
	def __init__(self, n = None, axpress = None, sparql = None) :
		if n == None :
			n = Namespaces.Namespaces()
		
		self.n = n
		
		self.axpress = axpress
		self.sparql = sparql
		
		self.parser = Parser.Parser()
		self.translators = [
			Translator(self.re_nop, self.fn_nop, self.bound_vars_nop, True),
			Translator(self.re_read_sparql, self.fn_read_sparql, self.bound_vars_general, True),
			Translator(self.re_write_sparql, self.fn_write_sparql, self.bound_vars_general, False),
			Translator(self.re_read_translations, self.fn_read_translations, self.bound_vars_general, True),
			Translator(self.re_write_translations, self.fn_write_translations, self.bound_vars_general, False),
		]

	#def string_to_multiline(self, string) :
		#lines = string.split('\n')
		#while lines[0].strip() == '' :
			#lines = lines[1:]
		
		#while lines[-1].strip() == '' :
			#lines = lines[:-1]
		
		#return lines
	
	#def string_to_triples(self, string) :
		#lines = self.string_to_multiline(string)
		#return self.parser.parse_query(lines, reset_bnodes = False)
	
	re_nop = re.compile('^$', re.MULTILINE | re.S)
	def fn_nop(g, bindings, reqd_bound_vars):
		print 'nop'
		return bindings
	def bound_vars_nop(g):
		return []
	
	re_read_sparql = re.compile('^read sparql(.*)', re.MULTILINE | re.S)
	def fn_read_sparql(self, g, query, bindings_set, reqd_bound_vars) :
		# this does the read, it doesn't connect to logic behind it. (connecting it
		# with the rest of the query
		#triples = self.parser.parse(g.group(1), reset_bnodes = False)
		ret = self.sparql.read( query )
		ret = [x for x in ret]
		print 'sparql read(', g.group(1),') =',prettyquery(ret)
		#return self.sparql.read(g.group(1))
		return ret
	def bound_vars_general(self, g):
		triples = self.parser.parse(g.group(1), reset_bnodes = False)
		return find_vars(triples), triples
	
	re_write_sparql = re.compile('^write sparql(.*)', re.MULTILINE | re.S)
	def fn_write_sparql(self, g, query, bindings_set, reqd_bound_vars) :
		#triples = self.parser.parse(g.group(1))
		debug('write sparql')
		debug('query', query)
		debug('bindings_set', bindings_set)
		#for triples in sub_var_bindings(query, bindings_set) :
		#	self.sparql.write(triples)
		self.axpress.write_sparql(query, bindings_set)
		return bindings_set
	
	re_read_translations = re.compile('^read translate(.*)', re.MULTILINE | re.S)
	def fn_read_translations(self, g, query, bindings_set, reqd_bound_vars) :
		#reqd_bound_vars = ['thumb_image']
		#triples = self.string_to_triples(g.group(1))
		bindings_set = self.axpress.read_translate(query, bindings_set = bindings_set, reqd_bound_vars = reqd_bound_vars)
		#print 'translations read(', g.group(1),') =',prettyquery(bindings_set)
		return bindings_set
	
	re_write_translations = re.compile('^write translate(.*)', re.MULTILINE | re.S)
	def fn_write_translations(self, g, query, bindings_set, reqd_bound_vars) :
		#return self.translator_default.write(g.group(1))
		print 'translations write(', g.group(1),')'
		return bindings_set
	
	def parse(self, query) :
		subquery_lines = []		
		method = ''
		
		lines = query.split('\n')
		while lines[0].strip() == '' :
			lines = lines[1:]
		
		while lines[-1].strip() == '' :
			lines = lines[:-1]
		
		def get_therest(position) :
			original_numspaces = len(lines[position]) - len(lines[position].lstrip())
			position += 1
			while position < len(lines) and \
						original_numspaces < len(lines[position]) and \
						lines[position][original_numspaces] in ['\t', ' '] :
				#print ':',repr(lines[position][original_numspaces])
				position += 1
			return position
		
		i = 0
		cur_position = 0
		compiled = []
		while cur_position is not len(lines) :
			end_position = get_therest(cur_position)
			these_lines = lines[cur_position:end_position]
			these_lines = [line.strip() for line in these_lines]
			sub_query = '\n'.join(these_lines)
			
			for translator in self.translators :
				g = translator.re.match(sub_query)
				if g is not None :
					bound_vars, query = translator.bound_vars(g)
					compiled.append((translator, g, bound_vars, query))
					continue
			
			cur_position = end_position
		
		#debug('compiled',compiled)
		
		reads = []
		writes = []
		new_compiled = []
		all_bound_vars = set()
		for translator, g, bound_vars, query in reversed(compiled) :
			reqd_bound_vars = bound_vars.intersection(all_bound_vars)
			all_bound_vars.update(bound_vars)
			new_compiled.append((translator, g, bound_vars, query, reqd_bound_vars))
			#if translator.is_read :
				#reads.append((translator, g, bound_vars, reqd_bound_vars))
			#else :
				#writes.append((translator, g, bound_vars, reqd_bound_vars))
		compiled = reversed(new_compiled)
		
		compiled = list(compiled)
		#debug('compiled',compiled)
		#debug('reads',reads)
		#debug('writes',writes)
		
		bindings_set = [{}]
		for translator, g, bound_vars, query, reqd_bound_vars in compiled :			
			print 'translator',translator
			print 'g',g
			print 'bound_vars', bound_vars
			print 'reqd_bound_vars', reqd_bound_vars
			bindings_set = translator.fn(g, query, bindings_set, reqd_bound_vars)
			print 'bindings_set',prettyquery(bindings_set)
		
		return 'hello'


















































"""
TODO:

the way multiline is parsed, it is impossible to determine which variables in
one query are going to need to be bound in future queries.  Fix this.










"""
