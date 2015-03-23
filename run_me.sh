#!/bin/bash

echo "[RUN] Running random"
python Simulation.py --strategy random --normalizationperiod 0  --outdir result_random_normperiod0 --steps 10000 
python Simulation.py --strategy random --normalizationperiod 5 --outdir result_random_normperiod5 --steps 10000
python Simulation.py --strategy random --normalizationperiod 10 --outdir result_random_normperiod10 --steps 10000
python Simulation.py --strategy random --normalizationperiod 25 --outdir result_random_normperiod25 --steps 10000
python Simulation.py --strategy random --normalizationperiod 50 --outdir result_random_normperiod50 --steps 10000
python Simulation.py --strategy random --normalizationperiod 100 --outdir result_random_normperiod100 --steps 10000

echo "[RUN] Running load_aware"
python Simulation.py --strategy load_aware --normalizationperiod 0   --outdir result_loadaware_normperiod0 --steps 10000 
python Simulation.py --strategy load_aware --normalizationperiod 5   --outdir result_loadaware_normperiod5 --steps 10000
python Simulation.py --strategy load_aware --normalizationperiod 10  --outdir result_loadaware_normperiod10 --steps 10000
python Simulation.py --strategy load_aware --normalizationperiod 25  --outdir result_loadaware_normperiod25 --steps 10000
python Simulation.py --strategy load_aware --normalizationperiod 50  --outdir result_loadaware_normperiod50 --steps 10000
python Simulation.py --strategy load_aware --normalizationperiod 100 --outdir result_loadaware_normperiod100 --steps 10000

echo "[RUN] Running migration_likelihood"
python Simulation.py --strategy migration_likelihood --normalizationperiod 0   --outdir result_migrationlikelihood_normperiod0 --steps 10000 
python Simulation.py --strategy migration_likelihood --normalizationperiod 5   --outdir result_migrationlikelihood_normperiod5 --steps 10000
python Simulation.py --strategy migration_likelihood --normalizationperiod 10  --outdir result_migrationlikelihood_normperiod10 --steps 10000
python Simulation.py --strategy migration_likelihood --normalizationperiod 25  --outdir result_migrationlikelihood_normperiod25 --steps 10000
python Simulation.py --strategy migration_likelihood --normalizationperiod 50  --outdir result_migrationlikelihood_normperiod50 --steps 10000
python Simulation.py --strategy migration_likelihood --normalizationperiod 100 --outdir result_migrationlikelihood_normperiod100 --steps 10000

echo "[RUN] Running sandpiper"
python Simulation.py --strategy sandpiper --normalizationperiod 0  --outdir sandpiper0 --steps 10000

rm -rf libs/*.pyc
