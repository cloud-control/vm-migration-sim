import argparse
import os
import errno

import libs.VirtualMachine as vm
import libs.PhysicalMachine as pm
import libs.MigrationManager as mm

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise

def main():

	parser = argparse.ArgumentParser( \
		description='VM migration simulator', \
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	migrationAlgorithms = ("random load_aware migration_likelihood sandpiper").split()
	parser.add_argument('--strategy',
		help = 'Migration algorithms: ' + ' '.join(migrationAlgorithms),
		default = migrationAlgorithms[0])
	parser.add_argument('--normalizationperiod',
		type = int,
		help = 'Load normalization: 0 if inactive, 10 for every ten steps',
		default = 0)
	parser.add_argument('--outdir',
		help = 'Destination folder for results and logs',
		default = 'results')
	parser.add_argument('--steps',
		type = int,
		help = 'Simulation steps',
		default = 500)
	args = parser.parse_args()
	strategy = args.strategy
	if strategy not in migrationAlgorithms:
		print "Unsupported migration algorithm %s"%format(strategy)
		parser.print_help()
		quit()
	mkdir_p(args.outdir)

	# ---------------------------------------------------------------------------
	# simulation: defining data center
	pm0 = pm.PhysicalMachine(8) # number of cores
	pm1 = pm.PhysicalMachine(8)
	pm2 = pm.PhysicalMachine(8)
	physical_machines = [pm0, pm1, pm2]

	vm0 = vm.VirtualMachine(physical_machines[0],'gold', 2) # plan and nominal load
	vm1 = vm.VirtualMachine(physical_machines[0],'gold', 2)
	vm2 = vm.VirtualMachine(physical_machines[0],'silver', 2)
	vm3 = vm.VirtualMachine(physical_machines[0],'silver', 4)
	vm4 = vm.VirtualMachine(physical_machines[0],'silver', 4)
	vm5 = vm.VirtualMachine(physical_machines[0],'basic', 4)
	vm6 = vm.VirtualMachine(physical_machines[0],'basic', 4)
	vm7 = vm.VirtualMachine(physical_machines[0],'basic', 4)
	virtual_machines = [vm0, vm1, vm2, vm3, vm4, vm5, vm6, vm7]
	# ---------------------------------------------------------------------------

	migration_manager = mm.MigrationManager(args.outdir, args.strategy, physical_machines, \
		virtual_machines, args.normalizationperiod)

	for i in range(0, args.steps):
		# generate actual loads (random number, method defined in VirtualMachine)
		[x.execute() for x in virtual_machines]
		migration_manager.execute(i)

if __name__ == "__main__":
    main()