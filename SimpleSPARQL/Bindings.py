"""
"""

class Bindings(dict) :
	def __init__(self, otherdict = None, possible = None, matches_reqd_fact = None) :
		if otherdict :
			if type(otherdict) == Bindings :
				self.possible = otherdict.possible
				self.matches_reqd_fact = otherdict.matches_reqd_fact
			super(Bindings, self).__init__(otherdict)
		
		if possible :
			self.possible = True
		else :
			self.possible = False
		
		if matches_reqd_fact :
			self.matches_reqd_fact = True
		else :
			self.matches_reqd_fact = False

	def update(self, other) :
		if other.matches_reqd_fact :
			self.matches_reqd_fact = True
		super(Bindings, self).update(other)








