import libs.Plan as Plan
import random
import math

class VirtualMachine:

	def __init__(self, pm_initial, plan='basic', load_nominal=4.0, memory_nominal = 1.0):
		random.seed(100) # set the random nymber generator to a fixed sequence
		if load_nominal > 0:
			self.load_nominal = load_nominal
		else:
			print("[VM]: The virtual machine needs to have a positive nominal load")
			exit(-1)
		self.plan = Plan.Plan(plan)
		self.memory_nominal = memory_nominal
		self.memory_actual = 0
		self.load_actual = 0
		self.migrations = 0
		self.pm_id = 0
		self.volume_nominal = load_nominal * memory_nominal
		self.volume_actual = 0
		self.volume_nominal_sandpiper = 0
		self.compute_volume_sandpiper(pm_initial)

	def compute_volume_sandpiper(self, pm):
		epsilon = 0.001
		saturated_diff_cpu = (pm.get_cores() - self.load_nominal)
		saturated_diff_cpu = max(saturated_diff_cpu, epsilon)
		saturated_diff_mem = (pm.get_memory() - self.memory_nominal)
		saturated_diff_mem = max(saturated_diff_mem, epsilon)
		self.volume_nominal_sandpiper = \
		  pm.get_cores() / saturated_diff_cpu * \
		  pm.get_memory() / saturated_diff_mem

	def execute(self):
		#self.load_actual = random.uniform(0.5*self.load_nominal, self.load_nominal)
		self.load_actual = max(random.gauss(0.75*self.load_nominal, math.sqrt(0.25)),1e-2)
		self.memory_actual = self.memory_nominal
		self.volume_actual = self.load_actual * self.memory_actual

	def get_actual_load(self):
		return self.load_actual

	def get_nominal_load(self):
		return self.load_nominal

	def get_nominal_memory(self):
		return self.memory_nominal

	def perform_migration(self, pm_destination):
		self.compute_volume_sandpiper(pm_destination)
		self.migrations += 1

	def get_migrations(self):
		return self.migrations

	def place_on_pm(self, pm):
		self.pm_id = pm

	def get_pm(self):
		return self.pm_id

	def get_volume_actual(self, option='normal'):
		return self.volume_actual

	def get_volume_nominal(self, option='normal'):
		if option == 'sandpiper':
			return self.volume_nominal_sandpiper
		else:
			return self.volume_nominal

	def get_volume_to_size_ratio(self):
		return self.volume_nominal_sandpiper / self.memory_nominal
