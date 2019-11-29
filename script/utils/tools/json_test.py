import json
from pprint import pprint
from pymatgen.io.vasp.outputs import Vasprun

with open('defect_data.json') as data_file:
	json_data=json.load(data_file)

pprint(json_data["gap"])
pprint(json_data["vbm"])
pprint(json_data["bulk_entry"]["data"]["bulk_path"])
bulk_path=json_data["bulk_entry"]["data"]["bulk_path"]
vr=Vasprun('%s/vasprun.xml'%bulk_path)
print(vr.eigenvalue_band_properties[0])

'''
for i in json_data:
	pprint(i)
json_data["substitution_specie"]='As'
'''