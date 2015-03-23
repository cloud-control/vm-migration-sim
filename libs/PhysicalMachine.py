class PhysicalMachine:

	def __init__(self, cores=16, memory=100):
		if memory > 0:
			self.memory = memory
		else:
			print("[PM]: The physical machine needs to have some memory")
			exit(-1)
		if cores > 0:
			self.cores = cores
		else:
			print("[PM]: The physical machine needs to have some cores")
			exit(-1)

	def get_cores(self):
		return self.cores

	def get_memory(self):
		return self.memory

	def get_volume(self):
		return self.cores* self.memory
