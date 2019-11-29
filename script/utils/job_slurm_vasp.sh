#!/bin/bash
#SBATCH --nodes=4
#SBATCH -p west2        # Partition Name
#SBATCH --ntasks-per-node=12        # Cores per node
##SBATCH --nodelist=n009,n010,n011,n012          # Specific host names
#SBATCH -J vcopt
#SBATCH -o intern_19.%N.%j.out         # STDOUT
#SBATCH -e intern_19.%N.%j.err         # STDERR
##

hostname
date

cd $SLURM_SUBMIT_DIR

function run_vasp(){
mpirun -np $SLURM_NTASKS /TGM/Apps/VASP/bin/5.4.4/NORMAL/vasp_5.4.4_GRP7_NORMAL_20170903.x > stdout.log
}
run_vasp
