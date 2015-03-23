#!/bin/bash

echo "[RUN] Running random"
python Simulation.py --strategy random --normalizationperiod 0  --outdir result_random_normperiod0 --steps 10000 

echo "[RUN] Running load_aware"
python Simulation.py --strategy load_aware --normalizationperiod 0   --outdir result_loadaware_normperiod0 --steps 10000 
python Simulation.py --strategy load_aware --normalizationperiod 5   --outdir result_loadaware_normperiod5 --steps 10000

echo "[RUN] Running migration_likelihood"
python Simulation.py --strategy migration_likelihood --normalizationperiod 5   --outdir result_migrationlikelihood_normperiod5 --steps 10000
python Simulation.py --strategy migration_likelihood_woi --normalizationperiod 5   --outdir result_migrationlikelihoodwoi_normperiod5 --steps 10000

echo "[RUN] Running sandpiper"
python Simulation.py --strategy sandpiper --normalizationperiod 0  --outdir sandpiper0 --steps 10000

rm -rf libs/*.pyc
