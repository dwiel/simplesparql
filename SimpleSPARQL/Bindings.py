"""
"""

class Bindings(dict) :
	def __init__(self, otherdict = None, possible = None) :
		if otherdict :
			if type(otherdict) == Bindings :
				self.possible = otherdict.possible
			super(Bindings, self).__init__(otherdict)
		if possible :
			self.possible = True
		else :
			self.possible = False










