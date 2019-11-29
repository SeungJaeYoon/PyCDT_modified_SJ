#!/bin/bash
#SBATCH --nodes=4
#SBATCH -p west2        # Partition Name
#SBATCH --ntasks-per-node=12       # Cores per node
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

t=1 #step num
while (("${t}" < 2))
do

if (("${t}" == 1))
then
	b_2=1
	s=0.6   #start
	e=0.2   #end
	i=-0.1  #interval
	for a in `seq $s $i $e`
	do

	if (("${b_2}" < 10))
	then
        mkdir "${b_2}_${a}_eV"
        sed "s/<a>/$a/g" ./INCAR > "${b_2}_${a}_eV"/INCAR
        cp ./POTCAR ./POSCAR ./vdw_kernel.bindat "${b_2}_${a}_eV"/
		cd "${b_2}_${a}_eV"
	else
	mkdir "${b_2}_${a}_eV"
        sed "s/<a>/$a/g" ./INCAR > "${b_2}_${a}_eV"/INCAR
	cp ./POTCAR ./POSCAR ./vdw_kernel.bindat "${b_2}_${a}_eV"/
        cd "${b_2}_${a}_eV"
	fi

	run_vasp
	echo  `cat OUTCAR | grep "energy without entropy" | tail -1 | awk '{printf "%10.9f", $5}'` >> ../ve.res
	cd ../

	b_2=$(($b_2+1))
	done

	mkdir ________________________done
	cd ../

	t=$(($t+1))
fi

done
