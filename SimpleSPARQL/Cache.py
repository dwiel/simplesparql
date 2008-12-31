import time

import Namespaces
n = Namespaces.globalNamespaces()

class Cache :
	def __init__(self, sparql) :
		self.sparql = sparql
	
	def call(self, plugin, vars) :
		#ret = sparql.read([
			#[n.var.cache_entry, n.cache.value, n.var.value],
			#[n.var.cache_entry, n.cache.date, n.var.date],
			#[n.var.cache_entry, n.cache.plugin, plugin[n.meta.name]],
			#[n.var.cache_entry, n.cache.vars, n.var.bindings],
		#] + [[n.var.bindings, k, v] for k, v in var.iteritems()])
		## or
		ret = sparql.read({
			n.cache.plugin : plugin[n.meta.name],
			n.cache.vars : vars,
			n.cache.value : None,
			n.cache.date : None,
		})
		if ret and ret[n.cache.date] + plguin[n.cache.expiration_length] < time.time() :
			return ret[n.cache.value]
		else :
			ret = plugin[n.meta.function](vars)
			sparql.write({
				n.sparql.create : n.sparql.unless_exists,
				n.cache.value : ret,
				n.cache.date : time.time(),
				n.cache.plugin : plugin[n.meta.name],
				n.cache.vars : vars,
			})



