import numpy as np
import random
import logging

class MigrationManager:

	def __init__(self, outdir, strategy, physical_machines, virtual_machines,
		normalization_period, target_utilization=0.75, target_relocation=1.1,
		window_size = 10):
		random.seed(100) # set the random nymber generator to a fixed sequence
		self.strategy = strategy
		# setup loggers
		self.setup_logger('PMloads', outdir, r'PMloads.csv')
		self.PMloads = logging.getLogger('PMloads')
		self.setup_logger('PMsetpoints', outdir, r'PMsetpoints.csv')
		self.PMsetpoints = logging.getLogger('PMsetpoints')
		self.setup_logger('PMrelocationthresholds', outdir, r'PMrelocationthresholds.csv')
		self.PMrelocationthresholds = logging.getLogger('PMrelocationthresholds')
		self.setup_logger('PMioi', outdir, r'PMioi.csv')
		self.PMioi = logging.getLogger('PMioi')
		self.setup_logger('PMwoi', outdir, r'PMwoi.csv')
		self.PMwoi = logging.getLogger('PMwoi')
		self.setup_logger('VMmigrations', outdir, r'VMmigrations.csv')
		self.VMmigrations = logging.getLogger('VMmigrations')
		self.setup_logger('VMloads', outdir, r'VMloads.csv')
		self.VMloads = logging.getLogger('VMloads')
		self.setup_logger('MMmigrations', outdir, r'MMmigrations.csv')
		self.MMmigrations = logging.getLogger('MMmigrations')
		# end setup loggers
		np.seterr('ignore')
		self.total_migrations = 0
		self.pms = physical_machines
		self.vms = virtual_machines
		self.num_pms = len(self.pms)
		self.num_vms = len(self.vms)
		self.normalization_period = normalization_period
		if self.num_pms < 1:
			print("[MM]: Error, define at least one physical machine")
			exit(-1)
		self.location = np.zeros((self.num_vms, self.num_pms))
		self.location[:,0] = 1 # initial placement: all on pm0
		[x.place_on_pm(0) for x in self.vms] # redundant
		self.utilization_set_points = np.array([x.get_cores() for x in self.pms])
		self.utilization_set_points *= target_utilization # 0.75 or parameter
		self.relocation_thresholds = np.array([x.get_cores() for x in self.pms])
		self.relocation_thresholds *= target_relocation # 1.1 or parameter
		self.integrated_overload_index = np.zeros(self.num_pms)
		self.window_overload_matrix = np.zeros((self.num_pms, window_size))
		self.window_overload_index = np.zeros(self.num_pms)
		# sandpiper
		self.sandpiper_n = 5
		self.sandpiper_k = 3
		self.sandpiper_migrate = np.zeros(self.sandpiper_n)
		self.muloads = np.zeros(self.num_pms)
		self.sumx = np.zeros(self.num_pms)
		self.sumx2 = np.zeros(self.num_pms)
		self.sigmaloads = np.zeros(self.num_pms)

	def setup_logger(self, logger_name, outdir, log_file, level=logging.INFO):
		l = logging.getLogger(logger_name)
		formatter = logging.Formatter('%(message)s') # %(asctime)s : 
		fileHandler = logging.FileHandler(outdir+'/'+log_file, mode='w')
		fileHandler.setFormatter(formatter)
		l.setLevel(level)
		l.addHandler(fileHandler)

	def execute(self, time_index):
		self.time_index = time_index
		self.loads = np.array([x.get_actual_load() for x in self.vms])
		self.volumes = np.array([x.get_volume_actual() for x in self.vms])
		self.total_load = np.sum(self.loads)
		self.physical_load_matrix = self.location.transpose() * self.loads
		self.physical_load_vector = np.sum(self.physical_load_matrix, axis=1)
		self.physical_volume_matrix = self.location.transpose() * self.volumes
		self.physical_volume_vector = np.sum(self.physical_volume_matrix, axis=1)
		self.physical_load_error = self.physical_load_vector - self.utilization_set_points
		self.physical_load_error_normalized = np.divide(self.physical_load_error, self.physical_load_vector)
		integration = np.maximum(np.zeros((1, self.num_pms)), self.physical_load_error_normalized)
		self.integrated_overload_index = self.integrated_overload_index + integration
		self.window_overload_matrix[:,1:] = self.window_overload_matrix[:,0:-1]
		self.window_overload_matrix[:,0] = self.physical_load_error
		self.window_overload_index = np.sum(self.window_overload_matrix, axis=1)
		
		# select migration strategy
		# "random load_aware migration_likelihood sandpiper"
		if self.strategy == 'random':
			self.decide_migration_random()
		elif self.strategy == 'load_aware':
			self.decide_migration_loadaware()
		elif self.strategy == 'migration_likelihood':
			self.decide_migration_migrationlikelihood()
		elif self.strategy == 'migration_likelihood_woi':
			self.decide_migration_migrationlikelihood_woi()
		elif self.strategy == 'sandpiper':
			self.decide_migration_sandpiper()

		self.log()

		# select if load normalization active
		if (self.normalization_period != 0):
			if time_index % self.normalization_period == 0:
				padding = 1.1
				capacities = np.array([float(x.get_cores()) for x in self.pms])
				capacity_sum = np.sum(capacities)
				rescaling = np.divide(capacities, capacity_sum) 
				self.utilization_set_points = np.sum(self.physical_load_vector) * padding * rescaling
				self.utilization_set_points = np.minimum(self.utilization_set_points, np.array([x.get_cores() for x in self.pms]))
				self.utilization_set_points = np.maximum(self.utilization_set_points, np.ones(self.num_pms))

	def log(self):
		self.PMloads.info('%s', ', '.join(map(str, list(self.physical_load_vector))))
		self.PMsetpoints.info('%s', ', '.join(map(str, list(self.utilization_set_points))))
		self.PMrelocationthresholds.info('%s', ', '.join(map(str, list(self.relocation_thresholds))))
		self.PMioi.info('%s', ', '.join(map(str, self.integrated_overload_index[0].tolist())))
		self.PMwoi.info('%s', ', '.join(map(str, list(self.window_overload_index))))
		self.VMloads.info('%s', ', '.join(map(str, list(self.loads))))
		self.VMmigrations.info('%s', ', '.join(map(str, [x.get_migrations() for x in self.vms])))	

	def migrate(self, vm, source, destination):
		self.total_migrations += 1
		self.location[vm, source] = 0
		self.location[vm, destination] = 1
		self.vms[vm].perform_migration(self.pms[destination])
		self.vms[vm].place_on_pm(destination)
		self.MMmigrations.info('%s, %s, %s, %s, %s'%
			(format(self.total_migrations, '04'),
			format(self.time_index, '04'), \
			format(vm, '02'), \
			format(source, '02'), \
			format(destination, '02')))
		# print("[%s at time %s] vm %d (migrated %s times) from %d to %d"%
		# 	(format(self.total_migrations, '04'), \
		# 		format(self.time_index, '04'), \
		# 		vm, format(self.vms[vm].migrations, '03'), source, destination))

	def decide_migration_random(self):
		migrate_me_maybe = (self.integrated_overload_index > self.relocation_thresholds)[0]
		if np.sum(migrate_me_maybe) > 0:
			indexes = np.array(np.where(migrate_me_maybe)).tolist()[0] # potential migration sources
			pm_source = random.choice(indexes)
			set_of_vms = (self.location[:, pm_source] == 1).transpose()
			vm_set_migration = np.array(np.where(set_of_vms)).tolist()[0]
			vm_migrate = random.choice(vm_set_migration)
			# avoiding to select the source machine as destination by using nan
			saving_load_pm_source = self.physical_load_vector[pm_source]
			self.physical_load_vector[pm_source] = np.nan
			pm_destination = np.nanargmin(self.physical_load_vector)
			self.physical_load_vector[pm_source] = saving_load_pm_source
			self.migrate(vm_migrate, pm_source, pm_destination)
			self.integrated_overload_index[0,pm_source] = 0

	def decide_migration_sandpiper(self):
		epsilon = 0.001
		# ar predictor
		self.muloads = np.divide(self.muloads * self.time_index + self.physical_load_vector, self.time_index+1)
		self.sumx += self.physical_load_vector
		self.sumx2 += (self.physical_load_vector)**2
		second_term = (np.multiply(self.sumx,self.sumx) / self.time_index)
		if self.time_index>1:
			self.sigmaloads = (self.sumx2 - second_term) / (self.time_index-1)
		y = self.muloads + self.sigmaloads * (self.physical_load_vector - self.muloads)

		migrate_me_maybe = np.zeros(self.num_pms)
		for i in range(0, self.num_pms):
			vms_in = (self.location[:, i] == 1).transpose()
			vm_set_in = np.array(np.where(vms_in)).tolist()[0]
			nominal_loads = [self.vms[vm_set_in[x]].get_nominal_load() for x in range(0,len(vm_set_in))]
			migrate_me_maybe[i] = (np.sum(nominal_loads) > self.utilization_set_points[i])
		self.sandpiper_migrate[1:self.sandpiper_n-1] = self.sandpiper_migrate[0:self.sandpiper_n-2]
		if np.sum(migrate_me_maybe) > 0:
			self.sandpiper_migrate[0] = int(1)
		else:
			self.sandpiper_migrate[0] = int(0)
		is_y_more = y > self.utilization_set_points
		if np.sum(self.sandpiper_migrate) >= self.sandpiper_k and np.any(is_y_more):
			indexes = np.array(np.where(migrate_me_maybe)).tolist()[0] # potential migration sources
			pm_source = random.choice(indexes)
			set_of_vms = (self.location[:, pm_source] == 1).transpose()
			vm_set_migration = np.array(np.where(set_of_vms)).tolist()[0]
			volume_to_size_ratio = [self.vms[x].get_volume_to_size_ratio() for x in vm_set_migration]
			vm_migrate = vm_set_migration[np.nanargmax(volume_to_size_ratio)]

			sandpiper_core_comp = np.zeros(self.num_pms)
			sandpiper_mem_comp = np.zeros(self.num_pms)
			volume_pm_sandpiper = np.zeros(self.num_pms)
			for i in range(0, self.num_pms):
				vms_in = (self.location[:, i] == 1).transpose()
				vm_set_in = np.array(np.where(vms_in)).tolist()[0]
				nominal_loads = [self.vms[vm_set_in[x]].get_nominal_load() for x in range(0,len(vm_set_in))]
				nominal_memories = [self.vms[vm_set_in[x]].get_nominal_memory() for x in range(0,len(vm_set_in))]
				sandpiper_core_comp[i] = float(self.pms[i].get_cores()) / \
				  max(float(self.pms[i].get_cores()) - sum(nominal_loads), epsilon)
				sandpiper_mem_comp[i] = float(self.pms[i].get_memory()) / \
				  max(float(self.pms[i].get_memory()) - sum(nominal_memories), epsilon)
				volume_pm_sandpiper[i] = sandpiper_core_comp[i] * sandpiper_mem_comp[i]

			pm_destination = np.nanargmin(volume_pm_sandpiper)
			self.migrate(vm_migrate, pm_source, pm_destination)
			self.integrated_overload_index[0,pm_source] = 0
			self.sandpiper_migrate = np.zeros(self.sandpiper_n)

	def decide_migration_loadaware(self):
		migrate_me_maybe = (self.integrated_overload_index > self.relocation_thresholds)[0]
		if np.sum(migrate_me_maybe) > 0:
			indexes = np.array(np.where(migrate_me_maybe)).tolist()[0] # potential migration sources
			pm_source = random.choice(indexes)
			set_of_vms = (self.location[:, pm_source] == 1).transpose()
			vm_set_migration = np.array(np.where(set_of_vms)).tolist()[0]

			volumes = np.array([x.get_volume() for x in self.pms])
			available_volume_per_pm = volumes - self.physical_volume_vector
			aware_matrix = np.zeros((self.num_vms, self.num_pms))
			for col in range(0,self.num_pms):
				aware_matrix[:, col] = available_volume_per_pm[col]
			for row in range(0,self.num_vms):
				if row in vm_set_migration:
					vol_to_remove = self.volumes[row]
				else:
					vol_to_remove = np.inf
				aware_matrix[row, :] = aware_matrix[row, :] - vol_to_remove
			aware_matrix[:, pm_source] = np.nan
			aware_matrix[aware_matrix<0] = np.nan

			if not np.isnan(aware_matrix).all():
				argmaxidx = np.nanargmax(aware_matrix)
				coordinates = np.unravel_index(argmaxidx, (self.num_vms, self.num_pms))
				vm_migrate = coordinates[0]
				pm_destination = coordinates[1]
				self.migrate(vm_migrate, pm_source, pm_destination)
				self.integrated_overload_index[0,pm_source] = 0

	def decide_migration_migrationlikelihood(self):
		migrate_me_maybe = (self.integrated_overload_index > self.relocation_thresholds)[0]
		if np.sum(migrate_me_maybe) > 0:
			indexes = np.array(np.where(migrate_me_maybe)).tolist()[0] # potential migration sources
			set_of_vms = list()
			for i in indexes:
				partial = (self.location[:, i] == 1).transpose()
				newly_found = np.array(np.where(partial)).tolist()
				set_of_vms += newly_found[0]
			set_of_vms = sorted(set_of_vms)
			pms = [x.get_pm() for x in self.vms]
			pm_volumes = np.array([x.get_volume() for x in self.pms])
			vm_volumes = np.array([x.get_volume_actual() for x in self.vms])
			vm_migrations = np.array([x.get_migrations() for x in self.vms])
			available_volume_per_pm = pm_volumes - self.physical_volume_vector
			available_capacity = [available_volume_per_pm[x.get_pm()] for x in self.vms]
			plan_coefficients = np.array([x.plan.get_coefficient() for x in self.vms])
			minimize_me = -1.0/plan_coefficients * (vm_volumes + available_capacity) + plan_coefficients * 10*vm_migrations
			vm_migrate = np.nanargmin(minimize_me)
			pm_source = self.vms[vm_migrate].get_pm()
			# avoiding to select the source machine as destination by using nan
			available_volume_per_pm[pm_source] = np.nan
			pm_destination = np.nanargmax(available_volume_per_pm)
			self.migrate(vm_migrate, pm_source, pm_destination)
			self.integrated_overload_index[0,pm_source] = 0

	def decide_migration_migrationlikelihood_woi(self):
		migrate_me_maybe = (self.window_overload_index > self.relocation_thresholds)[0]
		if np.sum(migrate_me_maybe) > 0:
			indexes = np.array(np.where(migrate_me_maybe)).tolist()[0] # potential migration sources
			set_of_vms = list()
			for i in indexes:
				partial = (self.location[:, i] == 1).transpose()
				newly_found = np.array(np.where(partial)).tolist()
				set_of_vms += newly_found[0]
			set_of_vms = sorted(set_of_vms)
			pms = [x.get_pm() for x in self.vms]
			pm_volumes = np.array([x.get_volume() for x in self.pms])
			vm_volumes = np.array([x.get_volume_actual() for x in self.vms])
			vm_migrations = np.array([x.get_migrations() for x in self.vms])
			available_volume_per_pm = pm_volumes - self.physical_volume_vector
			available_capacity = [available_volume_per_pm[x.get_pm()] for x in self.vms]
			plan_coefficients = np.array([x.plan.get_coefficient() for x in self.vms])
			minimize_me = -1.0/plan_coefficients * (vm_volumes + available_capacity) + plan_coefficients * vm_migrations
			vm_migrate = np.nanargmin(minimize_me)
			pm_source = self.vms[vm_migrate].get_pm()
			# avoiding to select the source machine as destination by using nan
			saving_load_pm_source = self.physical_load_vector[pm_source]
			self.physical_load_vector[pm_source] = np.nan
			pm_destination = np.nanargmax(available_volume_per_pm)
			self.physical_load_vector[pm_source] = saving_load_pm_source
			self.migrate(vm_migrate, pm_source, pm_destination)
			self.integrated_overload_index[0,pm_source] = 0
			