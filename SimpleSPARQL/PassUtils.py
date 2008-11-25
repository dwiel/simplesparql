"""
PassUtils
"""

def dictmask(src, mask) :
	"""
	for all keys in mask, check to see if they are in source.  If they are, remove
	them and add then to the return dict.  The following line does nothing to x no
	matter the contents of x or list (as long as x is a dictionary and list is a 
	list):
	x.update(dict_mask(x, list))
	"""
	ret = {}
	for k in mask :
		if k in src :
			ret[k] = src[k]
			del src[k]
	return ret

def querypath(query, path) :
	for ele in path :
		query = query[ele]
	return query

def dictrecursiveupdate(x, new) :
	"""
	same as x.update(new) except that if the value of both x and new are a dict, 
	the subx is updated with the subnew, rather than subx being replaced by subnew
	If both subvalues are lists, do subx.extend(subnew)
	"""
	for k, v in new.iteritems() :
		if k in x :
			if type(x[k]) == dict and type(v) == dict :
				dictrecursiveupdate(x[k], v)
			elif type(x[k]) == list and type(v) == list :
				x[k].extend(v)
			else :
				x[k] = v
		else :
			x[k] = v