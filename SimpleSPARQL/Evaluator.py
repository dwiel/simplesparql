from Utils import var_name, is_var, explode_bindings_set
from PrettyQuery import prettyquery

import copy

class Evaluator :
	"""
	evaluates 'programs' compiled by the compiler
	"""
	def __init__(self, n = None) :
		if n :
			self.n = n
		else :
			self.n = Namespaces()
	
	def evaluate_helper(self, compile_node, incoming_bindings_set, modifiers) :
		"""
		@arg compile_node is the compiled version of the graph traversal
		@returns the result of the query which was compiled
		"""
		
		n = self.n
		#print 'ahhhh!'
		rets = []
		for incoming_bindings in incoming_bindings_set :
			if len(compile_node['guarenteed']) == 0 :
				#return incoming_bindings
				#print 'SOLUTION!!!',prettyquery(compile_node['solution'])
				print 'solution'
				print 'incoming_bindings', prettyquery(incoming_bindings)
				solution = {}
				for var, binding in compile_node['solution'].iteritems() :
					solution[var_name(var)] = incoming_bindings[var_name(binding)]
				rets.append(solution)
			for step in compile_node['guarenteed'] :
				input_bindings = step['input_bindings']
				output_bindings = step['output_bindings']
				
				#print '0 incoming_bindings',prettyquery(incoming_bindings)
				#print '1 input_bindings',prettyquery(input_bindings)
				
				# substitute any values in the incoming bindings into the input_bindings
				new_input_bindings = {}
				for var, value in input_bindings.iteritems() :
					if is_var(value) and var_name(value) in incoming_bindings :
						new_input_bindings[var] = incoming_bindings[var_name(value)]
					else :
						new_input_bindings[var] = input_bindings[var]
				input_bindings = new_input_bindings
				
				#print '1.5 input_bindings',prettyquery(input_bindings)
				
				# call the translation's function
				ret = step['translation'][n.meta.function](input_bindings)
				if ret :
					result_bindings = ret
				else :
					result_bindings = input_bindings
					
				#print '2 result_bindings',prettyquery(result_bindings)
				#print '3 output_bindings',prettyquery(output_bindings)
				
				# bind the values resulting from the function call
				# new_bindings = {}
				new_bindings = copy.copy(incoming_bindings)				
				for var, value in result_bindings.iteritems() :
					if var in output_bindings :
						if is_var(output_bindings[var]) :
							new_bindings[var_name(output_bindings[var])] = value
						else :
							print 'hmm should I do something?',output_bindings[var],value
				
				#print '4 new_bindings',prettyquery(new_bindings)
				new_bindings = explode_bindings_set(new_bindings)
				#print '4.5 new_bindings',prettyquery(new_bindings)
				
				# recur
				rets.extend(self.evaluate_helper(step, new_bindings, modifiers))
				if len(rets) >= modifiers['limit'] :
					return rets[:modifiers['limit']]
		#print 'rets',prettyquery(rets)
		return rets
		
	def evaluate(self, compile_node, incoming_bindings_set = [{}]) :
		modifiers = {}
		if 'limit' in compile_node['modifiers'] :
			modifiers['limit'] = compile_node['modifiers']['limit']
		else :
			# TODO: be more smarter
			modifiers['limit'] = 99999999
		
		return self.evaluate_helper(compile_node, incoming_bindings_set, modifiers)













