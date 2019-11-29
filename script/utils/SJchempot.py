from pycdt.utils.parse_calculations import PostProcess, convert_cd_to_de, SingleDefectParser
from pycdt.core.chemical_potentials import MPChemPotAnalyzer
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from pymatgen.core.composition import Composition
from pymatgen.entries.computed_entries import ComputedEntry
import os

class usrchempot:
	def __init__(self,path='chempot_setting.txt'):
		self.path=path
		self.entry_list=None
		self.target_bulk=None
		self.read_setting_file()
		self.get_chempot()
	def read_setting_file(self,type_=True):
		entry_list=[]
		f=open('%s'%self.path,'r')
		lines=f.readlines()
		line_num=0
		phase_num=0
		for line in lines:
			if '#' in line:
				pass
			else:
				if line_num==0:
					line=line.replace('\n','')
					target_bulk=line
					line_num+=1
				else:
					line=line.replace('\n','')
					line=line.split()
					entry_list.append(self.usr_entry('phase%s'%phase_num,line[0],float(line[1]),float(line[2]),'PBE','paw','GGA'))
				phase_num+=1
		f.close()
		self.entry_list=entry_list
		self.target_bulk=target_bulk
		if type_:
			return entry_list
		else:
			return Composition(target_bulk)
	def usr_entry(self,entry_id,composition,energy,correction,functional,pot_type,run_type):
		form=Composition(composition)
		elements=list(form)
		atoms=[]
		for x in elements:
			x=str(x)
			atoms.append(x)
		labels=[]
		atoms.reverse()
		potcar_symbol=[]
		for atom in atoms:
			labels.append(str(atom))
			potcar_symbol.append('%s %s'%(functional,atom))
		pseudo_potential={'functional': functional, 'labels': labels, 'pot_type': pot_type}
		parameters={'potcar_symbols': potcar_symbol, 'oxide_type': None,
		'pseudo_potential': pseudo_potential,
		'run_type': run_type, 'is_hubbards': False, 'hubbards': {} }
		data={'oxide_type': None}
		my_entry={'entry_id': entry_id, 'composition': composition, 'energy': energy, 'correction': correction,'parameters': parameters, 'data': data}
		my_entry=ComputedEntry(**my_entry)
		return my_entry
	def get_chempot(self):
		target_bulk=Composition(self.target_bulk)
		pd=PhaseDiagram(self.entry_list)
		return pd.get_all_chempots(target_bulk)