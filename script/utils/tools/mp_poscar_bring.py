#!/usr/bin/env python
from __future__ import division, print_function, unicode_literals
import argparse
import os
import glob
import pymatgen as mg
try:
    import yaml
    use_yaml = True
except:
    use_yaml = False

from collections import defaultdict

from monty.serialization import dumpfn, loadfn
from monty.json import MontyEncoder, MontyDecoder


from pymatgen.ext.matproj import MPRester
from pymatgen.core import Element
from pymatgen.core.structure import Structure
from pymatgen.io.vasp.inputs import Incar, Potcar, Poscar
from pymatgen.analysis.defects.thermodynamics import DefectPhaseDiagram

from pycdt.core.defects_analyzer import ComputedDefect
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pycdt.core.defectsmaker import DefectChargerInsulator
from pycdt.core.defectsmaker import ChargedDefectsStructures
from pycdt.utils.vasp import DefectRelaxSet, PotcarMod
from pycdt.utils.vasp import make_vasp_defect_files, \
                              make_vasp_dielectric_files
from pycdt.utils.parse_calculations import PostProcess, convert_cd_to_de, SingleDefectParser
from pycdt.utils.log_util import initialize_logging
from pycdt.corrections.finite_size_charge_correction import \
        get_correction_freysoldt, get_correction_kumagai
from pymatgen.core.composition import Composition


parser = argparse.ArgumentParser(description='mp_id')
parser.add_argument('mp_id',type=str,help='mp id for system')
args = parser.parse_args()
mp_id=args.mp_id
with MPRester(api_key='hndGWo3ZFWECLd4hIEF') as mp:
            cry_struct = mp.get_structure_by_material_id(mp_id)

poscar=Poscar(cry_struct)
poscar.write_file('POSCAR')