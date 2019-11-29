#!/bin/bash
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8      # Cores per node
#SBATCH --partition=west         # Partition Name
##SBATCH --nodelist=n009,n010,n011,n012          # Specific host names
#SBATCH --job-name=vc_opt
#SBATCH --time=90-12:34          # Runtime: Day-HH:MM
#SBATCH -o test.%N.%j.out         # STDOUT
#SBATCH -e test.%N.%j.err         # STDERR
##
hostname
date
cd $SLURM_SUBMIT_DIR
function run_vasp(){
mpirun -np $SLURM_NTASKS /TGM/Apps/VASP/bin/5.4.4/NORMAL/vasp_5.4.4_GRP7_NORMAL_20170903.x > stdout.log
}
b_3=1
while (("${b_3}" < 4)) # 3 iteration of vcopt
do
        mkdir "${b_3}_try"
        cp POSCAR INCAR POTCAR vd* "${b_3}_try"/
        cp "$(($b_3-1))_try"/CONTCAR "${b_3}_try"/POSCAR
        cd "${b_3}_try"
        run_vasp
        cd ../
        b_3=$(($b_3+1))
done
mkdir ___done