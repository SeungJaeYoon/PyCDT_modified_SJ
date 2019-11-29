import os
# User setting for INCAR with standardized way
user_setting={'POTCAR':{'functional': 'PBE'},
'INCAR': {'ENCUT': 500, 'GGA': 'PE', 'LASPH': 'T', 'PREC': 'Accurate', 'NELM': 100,
'LCHARG': 'F', 'NSW': 150, 'ALGO': 'Normal', 'LAECHG': 'F', 'LREAL': 'F', 'LORBIT': 10,
'LVTOT': 'T', 'ADDGRID': 'T', 'ISPIN': 1, 'LWAVE': 'F', 'SIGMA': 0.01, 'ICHARG': 0, 
'ISYM': 2, 'POTIM': 0.125, 'IBRION': 2, 'KSPACING': 0.3,'KGAMMA': 'T','LVHAR': 'T',
'defects':{'EDIFF': 1E-5, 'ISPIN': 2, 'ISYM': 0},
'bulk':{'EDIFF': 1E-5,'IBRION':-1,'NSW':0},
'dielectric':{'EDIFF': 1e-6, 'IBRION': 8,'NSW': 1, 'POTIM': 0.05, 'ISMEAR': 0}
 }}
# unuseful INCAR tag for bulk and defect calculation, standardized way
unuseful_tag_bulk=['MAGMOM','NPAR','NELM','LAECHG','ISPIN','ISYM','ALGO','ICHARG','EDIFFG']
# unuseful INCAR tag for bulk and defect calculation, standardized way
unuseful_tag_defect=['MAGMOM','NPAR','NELM','LAECHG','ALGO','ICHARG','EDIFFG']
# unuseful INCAR tag for dielectric calculation, standardized way
unuseful_tag_dielec=['MAGMOM','LAECHG','ISPIN','ISYM','ALGO','ICHARG','ISIF']
unuseful_tag_phase=['MAGMOM','NPAR','NELM','LAECHG','ISPIN','ISYM','ALGO','ICHARG','EDIFFG','LVHAR','LVTOT']
# kpoint test INCAR setting: KGAMMA=T if gamma grid meshing, KGAMMA=F, if Monk horst pack grid meshing
kpoint_test_INCAR_setting={'IBRION': -1,'NSW': 0}
class input_setting:
	def __init__(self,type_):
		if type_=='dielec':
			self.tags=self.incar_tag_for_dielec()
		elif type_=='bulk':
			self.tags=self.incar_tag_for_bulk()
		elif type_=='defect':
			self.tags=self.incar_tag_for_defect()
		elif type_=='phase':
			self.tags=self.incar_tag_for_phase()
		else:
			print('Wrong argument for class input_setting!!')
			exit(0)
		self.lines=None
		self.find_tag()
		self.modify_INCAR()
	def incar_user():
		# return user settings for INCAR
		return user_setting
	def incar_tag_for_dielec(self):
		# return unuseful tags of INCAR for dielectric calculations
		return unuseful_tag_dielec
	def incar_tag_for_bulk(self):
        # return unuseful tags for bulk calculation incar
		return unuseful_tag_bulk
	def incar_tag_for_defect(self):
        # return unuseful tags for defect calculation incar
		return unuseful_tag_defect
	def incar_tag_for_phase(self):
		return unuseful_tag_phase
	def vcopt_job(path):
		job_path=path
		sh_file_name='vcopt.sh'
		return os.path.abspath(job_path+'/'+sh_file_name)
	def job_file(path):
		job_path=path
		file_list=os.listdir(job_path)
		sh_file=[file for file in file_list if file.endswith(".sh")]
		sh_file_name='job_slurm_vasp.sh'
		if len(sh_file)>=1:
			return os.path.abspath(job_path+'/'+sh_file_name)
		else:
			print('Oops, put job bash file in folder!!')
			exit(0)
	def find_tag(self):
		f=open('INCAR','r')
		lines=f.readlines()
		for i in range(len(lines)):
			for j in self.tags:
				if j in lines[i]:
					lines[i]=''
			if 'True' in lines[i]:
				lines[i]=lines[i].replace('True','T')
			elif 'False' in lines[i]:
				lines[i]=lines[i].replace('False','F')
		self.lines=lines
		f.close()
		return
	def modify_INCAR(self):
		if os.path.exists('INCAR'):
			os.system('rm INCAR')
		f=open('INCAR','w')
		for i in self.lines:
			f.write(i)
		f.close()
		if os.path.exists('KPOINTS'):
			os.system('rm KPOINTS')
class kpoint_test_setting:
	def __init__(self,path):
		self.path=path
		self.generate_input()
	def job_file(self):
		job_path=self.path
		file_list=os.listdir(job_path)
		sh_file=[file for file in file_list if file.endswith(".sh")]
		sh_file_name='kpoint_test.sh'
		if len(sh_file)>=1:
			return os.path.abspath(job_path+'/'+sh_file_name)
		else:
			print('Oops, put job bash file in folder!!')
			exit(0)
	def generate_input(self):
		if os.path.exists('1_kpoint_test'):
			os.system('rm -r 1_kpoint_test')
		os.system('mkdir 1_kpoint_test')
		os.chdir('1_kpoint_test')
		os.system('cp ../INCAR ../POTCAR ../POSCAR .')
		self.saving_INCAR_file()
		job=self.job_file()
		os.system('cp %s .'%job)
	def modify_INCAR_file(self):
		f=open('INCAR','r')
		lines=f.readlines()
		for i in range(len(lines)):
			if 'IBRION' in lines[i]:
				lines[i]='IBRION = %s\n'%kpoint_test_INCAR_setting['IBRION']
			elif 'NSW' in lines[i]:
				lines[i]='NSW = %s\n'%kpoint_test_INCAR_setting['NSW']
			elif 'KSPACING' in lines[i]:
				lines[i]='KSPACING = <a>\n'
			elif 'LVHAR' in lines[i]:
				lines[i]=''
			elif 'LVTOT' in lines[i]:
				lines[i]=''
		f.close()
		return lines
	def saving_INCAR_file(self):
		temp=self.modify_INCAR_file()
		f=open('INCAR','w')
		for i in temp:
			f.write(i)
		f.close()
class tools:	
	def copy_file(x,y):
		try:
			if os.path.exists('%s'%x):
				os.system("cp %s %s"%(x,y))
			else:
				print('Oops some files does not exists!!')
		except:
			print('Oops some files does not exists!!')