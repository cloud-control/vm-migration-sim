import sys

class Plan:
	plan_types = {'gold': 1, 'silver': 2, 'bronze': 3, 'basic': 4}

	def __init__(self, plan='basic'):
		if plan in self.plan_types:
			self.plan = plan
		else:
			print("[Plan]: %s, unavailable"%plan)
			exit(-1)
	
	def get_coefficient(self):
		if self.plan == 'gold':
			return 2.0
		elif self.plan == 'silver':
			return 1.5
		elif self.plan == 'bronze':
			return 1.2
		else:
			return 1.0