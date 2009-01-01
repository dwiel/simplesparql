import time

from PrettyQuery import *
import Namespaces
n = Namespaces.globalNamespaces()
n.bind('cache', '<http://dwiel.net/axpress/cache/0.1/>')

class Cache :
	def __init__(self, sparql) :
		self.sparql = sparql
	
	def call(self, plugin, vars) :
		ret = self.sparql.read([{
			n.cache.plugin : plugin[n.meta.name],
			n.cache.vars : vars,
			n.cache.value : None,
			n.cache.date : None,
		}])
		if ret[n.sparql.status] == n.sparql.ok and \
		   ret[n.sparql.result] and \
			 ret[n.cache.date] + plguin[n.cache.expiration_length] < time.time() :
			return ret[n.cache.value]
		else :
			ret = plugin[n.meta.function](vars)
			# TODO: make this work
			print 'cache write'
			print self.sparql.write([
				[n.bnode.x, n.cache.value, ret],
				[n.bnode.x, n.cache.date, time.time()],
				[n.bnode.x, n.cache.plugin, plugin[n.meta.name]],
				[n.bnode.x, n.cache.vars, vars]
			])
			#self.sparql.write({
				#n.sparql.create : n.sparql.unless_exists,
				#n.cache.value : ret,
				#n.cache.date : time.time(),
				#n.cache.plugin : plugin[n.meta.name],
				#n.cache.vars : vars,
			#})




