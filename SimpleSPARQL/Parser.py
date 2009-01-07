import Namespaces
import re

re_lhs_rhs = re.compile('(.+)\s*=\s*(.+)')
re_obj_prop = re.compile('(\w+)\[(\w+)\.(\w+)\]')

re_equals = re.compile('(.+)\s*=\s*(.+)')
re_prop = re.compile('(.+)\[(.+)\]')
re_dict = re.compile('(.+){(.+)}')
re_dict_pair = re.compile('\s*([^,:\.]*[:\.]*[^,:\.]*)\s*:\s*([^,:\.]*[:\.]*[^,:\.]*)\s*,')
re_call = re.compile('(.+)\((.*)\)')
re_call_params = re.compile('([^,]+),')
re_uri = re.compile('(\D.+)[\.:](.+)')

class Expression() :
	def __init__(self, exp, missing = None) :
		self.exp = exp
		# a list of indicies into exp where the missing value is
		self.missing = missing
	
	def put(self, value) :
		#print 'self.exp',self.exp
		#print 'self.missing',self.missing
		#print 'value',value
		ele = self.exp
		for i in self.missing[:-1] :
			ele = ele[i]
		ele[self.missing[-1]] = value
		self.missing = None
	
	def triplelist(self) :
		if isinstance(self.exp, list) and not isinstance(self.exp[0], list) :
			return [self.exp]
		else :
			return self.exp
	
	def merge(self, other) :
		#self.exp = self.triplelist()
		#self.exp.extend(other.triplelist())
		self.exp = self.triplelist()
		other.exp = other.triplelist()
		if self.missing :
			if other.missing :
				raise Exception('cant merge two Expressions with missing values')
		else :
			# correct for the case where other was just a triple to start
			if other.missing :
				if len(other.missing) == 1 :
					other.missing = [0] + other.missing
				self.missing = [len(self.exp) + other.missing[0], other.missing[1]]
		self.exp.extend(other.exp)
		print 'missing',self.missing
		print 'exp',self.exp
	
	def __str__(self) :
		return '<Expression %s>' % str((self.exp, self.missing))
	
	def __repr__(self) :
		return str(self.exp)

class Parser() :
	def __init__(self, n = None) :
		if n == None :
			n = Namespaces.Namespaces()
		
		self.n = n
		self.var = 0

	def parse_expression(self, expression) :
		self.reset_bnode()
		print
		print '---------------------'
		print 'expression',expression
		exp = self.parse_expression_new(expression)
		print 'exp',exp
		code = '[\n%s\n]' % ',\n'.join([
			'[%s]' % ', '.join(triple) for triple in exp.triplelist()
		])
		print 'code',code
		return eval(code, {'n' : self.n}, {})
	
	def parse_query(self, query) :
		return [isinstance(expression, basestring) and self.parse_expression(expression) or expression for expression in query]
	
	def reset_bnode(self) :
		self.var = 0
	
	def next_bnode(self) :
		self.var += 1
		return 'n.var.bnode%s' % self.var
	
	def parse_expression_new(self, expression) :
		expression = expression.replace('\n', '')
		expression = expression.strip()
		print expression
		g = re_equals.match(expression)
		if g is not None :
			lhs = self.parse_expression_new(g.group(1))
			rhs = self.parse_expression_new(g.group(2))
			
			print '='
			print 'lhs',lhs
			print 'rhs',rhs
			print '-[]'
			if isinstance(lhs, Expression) :
				if isinstance(rhs, Expression) :
					bnode = self.next_bnode()
					lhs.put(bnode)
					rhs.put(bnode)
					lhs.merge(rhs)
					return lhs
				else :
					lhs.put(rhs)
					return lhs
			else :
				if isinstance(rhs, Expression) :
					rhs.put(lhs)
					return rhs
				else :
					return None
		
		g = re_prop.match(expression)
		if g is not None :
			obj = self.parse_expression_new(g.group(1))
			prop = self.parse_expression_new(g.group(2))
			
			print '[]'
			print 'obj',obj
			print 'prop',prop
			print '-[]'
			if isinstance(obj, Expression) :
				if isinstance(prop, Expression) :
					return None
				else :
					bnode = self.next_bnode()
					obj.put(bnode)
					obj.merge(Expression([bnode, prop, None], [2]))
					return obj
			else :
				if isinstance(prop, Expression) :
					return None
				else :
					return Expression([obj, prop, None], [2])
		
		g = re_dict.match(expression)
		if g is not None :
			obj = g.group(1).strip()
			inside = g.group(2).strip() + ','
			
			obj = self.parse_expression_new(obj)	
			
			print 'obj',obj
			print 'inside',inside
			
			pairs = re_dict_pair.findall(inside)
			if pairs is not [] :
				# if we are here, this is a valid dict
				bnode = self.next_bnode()
				triples = []
				for pair in pairs :
					l = self.parse_expression_new(pair[0])
					r = self.parse_expression_new(pair[1])
					triples.append([bnode, l, r])
				triples.append([bnode, obj, None])
				return Expression(triples, [len(triples)-1, 2])
			else :
				raise Exception('bad dictionary %s' % expression)
		
		g = re_call.match(expression)
		if g is not None :
			obj = self.parse_expression_new(g.group(1))
			params = g.group(2) + ','
			
			params = re_call_params.findall(params)
			
			params = [self.parse_expression_new(param) for param in params]
			
			bnode = self.next_bnode()
			triples = []
			for i, param in enumerate(params) :
				triples.append([bnode, 'n.call.arg%d' % (i+1), param])
			triples.append([bnode, obj, None])
			return Expression(triples, [len(triples)-1, 2])
		
		g = re_uri.match(expression)
		if g is not None :
			namespace = g.group(1).strip()
			value = g.group(2).strip()
			print 'uri(%s, %s)' % (namespace, value)
			return 'n.%s.%s' % (namespace, value)
		
		if expression[0].isalpha() and expression[1:].isalnum() :
			print 'var(%s)' % expression
			return 'n.var.%s' % expression
		
		return expression
		
		print
		



"""
value : var | literal | var[prop] | prop(value)
expression : value = value

'var[prop] = ?' := [var, prop, ?]
'? = var[prop]' := [var, prop, ?]
'prop(var) = ?' := [var, prop, ?]
'var1[prop1] = var2[prop2]' := [[var1, prop1, x], [var2, prop2, x]]
'fn{prop1 : val1, prop2 : val2} = ?' := [
	[x, prop1, val1],
	[x, prop2, val2],
	[x, fn, ?]
]

value:
	string, int, bool, var, etc
	'value[value]' := [value, value, ?]
expressions:
'value1[value2] = value3' := [value1, value2, value3]
'value1(value2) = value3' := [value2, value1, value3]

"""