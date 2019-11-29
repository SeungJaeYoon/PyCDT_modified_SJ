import matplotlib.pyplot
import numpy
import argparse
import os
import glob
import pymatgen as mg
import json
try:
    import yaml
    use_yaml=True
except:
    use_yaml=False
from collections import defaultdict
from monty.serialization import dumpfn, loadfn
from monty.json import MontyEncoder, MontyDecoder
from pymatgen.ext.matproj import MPRester
from pymatgen.core import Element
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Incar
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.analysis.defects.thermodynamics import DefectPhaseDiagram
from pycdt.core.defects_analyzer import ComputedDefect
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pycdt.core.defectsmaker import ChargedDefectsStructures
from pycdt.utils.vasp import DefectRelaxSet
from pycdt.utils.vasp import make_vasp_defect_files, \
                              make_vasp_dielectric_files
from pycdt.utils.parse_calculations import PostProcess, convert_cd_to_de, SingleDefectParser
from pycdt.utils.log_util import initialize_logging
from pycdt.corrections.finite_size_charge_correction import \
        get_correction_freysoldt, get_correction_kumagai
from pycdt.core.chemical_potentials import UserChemPotInputGenerator
from pymatgen.core.composition import Composition
import pprint
from igor_plot import igor_plt


defect_data_file_name = 'defect_data.json'
corrections_file_name = 'corrections.json'


# parse results to get defect data and correction terms
defect_data = loadfn(defect_data_file_name, cls=MontyDecoder)
defects = defect_data["defects"]
for def_ind in range(len(defects)):
    if type(defects[def_ind]) == ComputedDefect:
        print("Encountered legacy ComputedDefect object. Converting to DefectEntry type for PyCDT v2.0...")
        defects[def_ind] = convert_cd_to_de(defects[def_ind], defect_data["bulk"])

formula = defects[0].bulk_structure.composition.reduced_formula
initialize_logging(filename=formula+"_formation_energy.log")

if os.path.isfile(corrections_file_name):
    correction_data = loadfn(corrections_file_name)  
    for computed_defect in defects:
        corr_key = computed_defect.parameters["defect_path"]
        computed_defect.corrections = correction_data[corr_key]
elif corrections_file_name == "corrections.json":  # Default filename
    print("No corrections file exists! Plotting formation energies regardless...")
    pass # Don"t bother, the user is not worried about corrections
else:
    raise OSError([2, "File not found", corrections_file_name])

# Gap
if True:
    bandgap = 1.5 #defect_data["gap"]
else:
    bandgap = 1.5

vbm = defect_data["vbm"]
mu_range = defect_data["mu_range"]

#doctor up mu_range because of cls Monty Decoder issue with Element
mu_range = {ckey:{Element(k):v for k,v in cdict.items()}
                           for ckey, cdict in mu_range.items()}
dpd = DefectPhaseDiagram( defects, vbm, bandgap, filter_compatible=False)
# plotter = DefectPlotter(dpd)
for region, mu in mu_range.items():
    if region == list(mu_range.keys())[0]:
        da_trans = dpd.transition_level_map
        if use_yaml:
            with open("transition_levels.yaml", "w") as f:
                yaml.dump(da_trans, f)
        print ("============\nDefect Transition Levels (eV):\n===========")
        for dfct_name, trans_lvls in da_trans.items():
            prt_dfct_name = dfct_name.split("@")[0]
            print (prt_dfct_name, trans_lvls)
            ky_vals = sorted(trans_lvls.items(), key=lambda x: x[0])
            for qpair, trans_lvl in ky_vals:
                print ("{}: {}".format(qpair, trans_lvl))

    if True:
        # USER -> note that all settings below can be changed to make plot prettier
        form_en_plot = dpd.plot( mu_elts=mu, xlim=None, ylim=None, ax_fontsize=1.3, lg_fontsize=1.,
                  lg_position=None, fermi_level = None, title=None, saved=False)
        xy=(form_en_plot[1])
        defect_type=(form_en_plot[2])
        index_num=0
        data_set=[]
        for cnt, defnom in enumerate(xy.keys()):
                data_set.append([defect_type[index_num].replace('$','').replace('{','').replace('}',''),xy[defnom][0],xy[defnom][1]])
                index_num+=1
        for dat in data_set:
            with open(dat[0]+"_defect_type_"+region+"_region_defect_form_energy.dat",'w') as form_en_dat_file:
                for x_val,y_val in zip(dat[1],dat[2]):
                    form_en_dat_file.write("%s %s\n"%(x_val,y_val))
        igor_plt(graph_name=region+"_region_defect_form_energy",xy_value=data_set)
        #figure=form_en_plot.figure()

