#!/usr/bin/env python
from __future__ import division, print_function, unicode_literals

"""
A script with tools for computing formation energies
of charged point defects, supporting multiple correction
schemes.
"""

__author__="SeungJaeYoon"
__copyright__="Copyright 2012, The Materials Project\n2019, pycdt"
__version__="1.0"
#__maintainer__=""
__email__="pingpong9730@yonsei.ac.kr"
__date__="October 7, 2019"

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
import inspect
from utils.setting import input_setting, kpoint_test_setting, tools
from utils.SJchempot import usrchempot
from utils.igor_plot import igor_plt

def generate_input(args):
    print('loading settings and inputs....')
    user_settings=input_setting.incar_user()
    input_path=(os.path.dirname(inspect.getfile(input_setting)))
    input_path_abs=os.path.abspath(input_path)
    job_file_path=input_setting.job_file(input_path)
    vcopt_file_path=input_setting.vcopt_job(input_path)
    mp_id=args.mp_id
    mapi_key=args.mapi_key
    nmax=args.nmax
    oxi_state=args.oxi_state
    oxi_range=args.oxi_range
    antisites=args.antisites
    struct_type=args.struct_type
    include_interstitials=args.include_interstitials
    interstitial_elements=args.interstitial_elements
    if args.struct_file:
        struct_file=args.struct_file
    else:
        struct_file='POSCAR'
    if not struct_file and not mp_id:
        print_error_message("Neither structure, nor Materials Project " \
                            + "ID (MP-ID) provided!")
        return
    if nmax<=0:
        print_error_message("maximal number of atoms per supercell"
            " must be larger than zero!")
        return
    if struct_file:
        cry_struct=mg.Structure.from_file(struct_file)
        conv_struct=SpacegroupAnalyzer(cry_struct).get_conventional_standard_structure()
    # get primitive unit cell
    if mp_id:
        with MPRester(api_key=mapi_key) as mp:
            cry_struct=mp.get_structure_by_material_id(mp_id)

        # transform to conventional unit cell
        conv_struct=SpacegroupAnalyzer( 
                cry_struct).get_conventional_standard_structure()
        make_vasp_dielectric_files(cry_struct, user_settings=settings)
    else:
        pass
    # manually set oxidation states if those were provided
    oxi_state_dict={}
    if oxi_state:
        for i in range(len(oxi_state)):
            oxi_state_dict[oxi_state[i][0]]=int(oxi_state[i][1])

    # manually set oxidation-state ranges if those were provided
    oxi_range_dict={}
    if oxi_range:
        for i in range(len(oxi_range)):
            oxi_range_dict[oxi_range[i][0]]=tuple(
                    [int(oxi_range[i][1]), int(oxi_range[i][2])])
    settings={}
    if args.input_settings_file:
        if os.path.split(args.input_settings_file)[1]=="INCAR":
            settings={"INCAR":{}}
            incar=Incar.from_file(args.input_settings_file)
            settings["INCAR"]=incar
        else:
            settings=loadfn(args.input_settings_file)
    else:
        settings=user_settings
    substitutions={}
    if args.substitutions:
        for i,sub in enumerate(args.substitutions):
            substitutions[sub[0]]=sub[1:]
    else:
        pass
    print('Loading Done!!\nmaking inputs for vasp calculations....')
    make_vasp_dielectric_files(cry_struct,user_settings=settings)
    defect_structs=ChargedDefectsStructures(
	            conv_struct, 
	            max_min_oxi=oxi_range_dict,
	            oxi_states=oxi_state_dict, 
	            antisites_flag=antisites,
	            substitutions=substitutions,
	            include_interstitials=include_interstitials,
	            interstitial_elements=interstitial_elements,
	            cellmax=nmax, 
	            struct_type=struct_type)
    make_vasp_defect_files(defect_structs.defects,
        conv_struct.composition.reduced_formula,
        user_settings=settings)
    dir_name=cry_struct.composition.reduced_formula
    os.chdir(dir_name)
    curr=os.getcwd()
    if os.path.exists('PhaseDiagram'):
        os.system('rm -r PhaseDiagram')
    cpa=UserChemPotInputGenerator(Composition(dir_name))
    cpa.setup_phase_diagram_calculations()
    dir_list=list(filter(os.path.isdir, os.listdir("./")))
    if 'bulk' and 'dielectric' and 'PhaseDiagram' in dir_list:
        dir_list.remove('bulk')
        dir_list.remove('dielectric')
        dir_list.remove('PhaseDiagram')
        os.chdir('PhaseDiagram')
        dir_list_phase=list(filter(os.path.isdir, os.listdir("./")))
        temp_curr=os.getcwd()
        for phase in dir_list_phase:
            os.chdir('%s'%phase)
            os.system('cp ../../bulk/INCAR .')
            input_setting('phase')
            tools.copy_file(vcopt_file_path,'.')
            phase_struct=mg.Structure.from_file('POSCAR')
            dir_name_1=phase_struct.composition.reduced_formula
            make_vasp_dielectric_files(phase_struct,user_settings=settings)
            os.system('mv %s/dielectric/POTCAR .'%dir_name_1)
            os.system('rm -r %s'%dir_name_1)
            os.chdir(temp_curr)
        os.chdir(curr)
        os.chdir('bulk')
        input_setting('bulk')
        tools.copy_file(job_file_path,'.')
        kpoint_test_setting(input_path_abs)
        os.chdir(curr)
        os.chdir('dielectric')
        tools.copy_file(job_file_path,'.')
        input_setting('dielec')
        os.chdir(curr)
        for j in dir_list:
            os.chdir('%s'%j)
            curr_2=os.getcwd()
            dir_list_1=list(filter(os.path.isdir, os.listdir("./")))
            for k in dir_list_1:
                os.chdir('%s'%k)
                tools.copy_file(job_file_path,'.')
                if 'as' in j:
                    substitution_specie=j.split('_')[2]
                    with open('transformation.json') as data_file:
                        json_data=json.load(data_file)
                    json_data["substitution_specie"]=substitution_specie
                    with open('transformation.json', 'w', encoding='utf-8') as make_file:
                        json.dump(json_data, make_file)
                input_setting('defect')
                os.chdir(curr_2)
            os.chdir(curr)
def parse_output(args):
    """
    Parses output files from VASP calculations
    Args:
        args (Namespace): contains the parsed command-line arguments for
            this command.
    """
    # initialize variables
    mp_id=args.mp_id
    mapi_key=args.mapi_key
    root_fldr=args.root_fldr
    input_file_name=args.file_name
    formula=os.path.split(os.path.abspath(root_fldr))[-1]
    initialize_logging(filename=formula+"_parser.log") 
    # error-checking;
    if not mp_id:
        print("No Materials Project structure ID provided! "
                            "(proceeding anyway)")
        mp_id=None
        try:
            usrchem=usrchempot(input_file_name)
        except:
            print('No user chemical potential input file!!')
        try:    
            red_formula=usrchem.read_setting_file(False)
            os.chdir('%s'%red_formula)
        except:
            pass
    # parse results to get defect data and correction terms
    defect_data=PostProcess(root_fldr, mp_id, mapi_key).compile_all()
    # need to doctor up chemical potentials for dumpfn due to issue with
    # Element not interpretted by MontyEncoder
    if mp_id==None:
        print("Reading user chemical potential input file...")
        try:          
            defect_data["mu_range"]=usrchem.get_chempot()
        except:
            print('Somethings wrong with user chemical potential input file!!')
    defect_data["mu_range"]={ckey:{k.symbol:v for k,v in cdict.items()}
                               for ckey, cdict in defect_data["mu_range"].items()}
    dumpfn(defect_data, args.defect_data_file_name, cls=MontyEncoder, indent=2)
    with open(args.defect_data_file_name) as data_file:
        json_data=json.load(data_file)
    if True:
        bulk_path=json_data["bulk_entry"]["data"]["bulk_path"]
        vr=Vasprun('%s/vasprun.xml'%bulk_path)
        json_data["gap"]=(vr.eigenvalue_band_properties[0])
        json_data["vbm"]=(vr.eigenvalue_band_properties[2])
    dumpfn(json_data, args.defect_data_file_name, cls=MontyEncoder, indent=2)
    print("\n   Parsing done!   ")
def compute_corrections(args):
    """
    Computes corrections for the charged point defects
    Supported: Isotropic Freysoldt method, Extended Freysoldt method (Kumagai)

    Args:
        args (Namespace): contains the parsed command-line arguments for
            this command.
    """
    # initialize variables
    defect_data_file_name = args.defect_data_file_name
    corrections_file_name = args.corrections_file_name
    plot_results = args.plot_results
    correction_method = args.correction_method
    # parse results to get defect data and correction terms
    defect_data = loadfn(defect_data_file_name, cls=MontyDecoder)
    if args.epsilon:
        epsilon = args.epsilon
    else:
        epsilon = defect_data["epsilon"]

    defects = defect_data["defects"]
    for def_ind in range(len(defects)):
        if type(defects[def_ind]) == ComputedDefect:
            print("Encountered legacy ComputedDefect object. Converting to DefectEntry type for PyCDT v2.0...")
            defects[def_ind] = convert_cd_to_de(defects[def_ind], defect_data["bulk"])
    corrections = defaultdict(list)
    formula = defects[0].bulk_structure.composition.reduced_formula
    initialize_logging(filename=formula+"_correction.log")
    #loading locpot object now is useful for both corrections
    bulk_obj = None #store either bulk Locpot or Outcar for saving time
    if correction_method == "freysoldt":
        for defect in defects:
            print ("defect_name: {} q={}".format( defect.name, defect.charge))
            print ("-----------------------------------------\n\n")
            def_ent_loader = SingleDefectParser( defect)
            bulk_obj = def_ent_loader.freysoldt_loader(bulk_locpot=bulk_obj)

            plt_title = os.path.join( defect.parameters["defect_path"],
                                      "{}_chg_{}".format(defect.name, defect.charge)) if plot_results else None
            correction = get_correction_freysoldt( def_ent_loader.defect_entry,
                                                   epsilon,
                                                   title=plt_title)
            corr_key = defect.parameters["defect_path"]
            corrections[corr_key] = {"charge_correction": correction}
    elif correction_method == "kumagai":
        for defect in defects:
            print ("defect_name: {} q={}".format( defect.name, defect.charge))
            print ("-----------------------------------------\n\n")
            def_ent_loader = SingleDefectParser( defect)
            bulk_obj = def_ent_loader.kumagai_loader(bulk_outcar=bulk_obj)

            plt_title = os.path.join( defect.parameters["defect_path"],
                                      "{}_chg_{}".format(defect.name, defect.charge)) if plot_results else None
            correction = get_correction_kumagai( def_ent_loader.defect_entry,
                                                 epsilon, title = plt_title)
            corr_key = defect.parameters["defect_path"]
            corrections[corr_key] = {"charge_correction": correction}
    else:
        print ("Invalid correction method: ",correction_method,". Select either " \
               "'freysoldt' or 'kumagai'")

    dumpfn(corrections, corrections_file_name, cls=MontyEncoder, indent=2)


def compute_formation_energies(args):
    """
    Computes transition levels and plots formation energy
    of charged point defects across the band gap

    Args:
        args (Namespace): contains the parsed command-line arguments for
            this command.
    """
    # initialize variables
    defect_data_file_name = args.defect_data_file_name
    corrections_file_name = args.corrections_file_name
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
    if not args.bandgap:
        bandgap = defect_data["gap"]
    else:
        bandgap = args.bandgap
    # VBM
    if not args.vbm:
        vbm = defect_data["vbm"]
    else:
        vbm = args.vbm
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
            form_en_plot_plt=form_en_plot[0]
            xy=form_en_plot[1] # fermi energy data
            defect_type=form_en_plot[2]
            index_num=0
            data_set=[]
            for cnt, defnom in enumerate(xy.keys()):
                data_set.append([defect_type[index_num].replace('$','').replace('{','').replace('}',''),
                    xy[defnom][0],xy[defnom][1]])
                index_num+=1
            for dat in data_set:
                with open(dat[0]+"_defect_type_"+region+"_region_defect_form_energy.dat",'w') as form_en_dat_file:
                    for x_val,y_val in zip(dat[1],dat[2]):
                        form_en_dat_file.write("%s %s\n"%(x_val,y_val))
            igor_plt(graph_name=region+"_region_defect_form_energy",xy_value=data_set,bandgap=bandgap)
            form_en_plot_plt.savefig(
                    region+"_region_defect_form_energy."+args.file_format,
                    bbox_inches="tight")
            print("printed ",region," plot")
parser=argparse.ArgumentParser(description="""
        PyCDT is a script that generates vasp input files, parses vasp output
        files, and computes the formation energy of charged defects.
        This script works based on several sub-commands with their own options.
        To see the options for the sub-commands, type
        "pycdt sub-command -h".""",
        epilog="""
        Authors: {}
        Version: {}
        Last updated: {}""".format(__author__,__version__, __date__))



subparsers=parser.add_subparsers()
struct_string="Input structure. Can accept multiple file formats. " \
    "Supported formats include CIF, POSCAR/CONTCAR, CHGCAR, LOCPOT, "\
    "vasprun.xml, CSSR, Netcdf and pymatgen's JSON serialized structures."
mp_id_string="Materials Project id of the structure.\nFor more info on " \
    "Materials Project, please, visit www.materialsproject.org."
mapi_string="Your Materials Project REST API key.\nFor more info, " \
    "please, visit www.materialsproject.org/open."
nmax_string="Maximum number of atoms in supercell.\nThe default is" \
    " 128.\nKeep in mind that the number of atoms in the supercell may" \
    " vary from the provided number including the default."
oxi_state_string="Oxidation state for an element.\nTwo arguments" \
    " are expected: the element type for which the oxidation state is" \
    " to be specified and the oxidation state (e.g., --oxi_state As -3)."
oxi_range_string="Oxidation range for an element.\nThree arguments" \
    " are expected: the element type for which the oxidation state range is" \
    " to be specified as well as the lower and the upper limit of the" \
    " range (e.g., --oxi_range As -3 5)."
struct_type_string="Structure type to determine the charge range" \
    " for the defects. Valid options are 'semiconductor' and 'insulator'"\
    " With 'semiconductor' option, the defect charges are determined by"\
    " database approach where defect charges found in literature for"\
    " common semiconductors.\nFor 'insulator' option, a conservative"\
    " approach is used. For cations, the oxidation states of (0, A) are"\
    " considered, where A is the cation oxidation in the compound."\
    " Similarly for anions, (-B, 0) where -B is the oxidation state of"\
    " anion in the compound."
no_antisites_string="Optional flag to indicate that anti-site defects" \
    " should not be generated."
include_interstitials_string="Optional flag to indicate that" \
    " interstitial defects should be generated. If you do not provide" \
    " positional\narguments, intrinsic interstitials are set-up as" \
    " per\ndefault.  Providing positional arguments (elemental\n" \
    "symbols) enables the set-up of specific interstitials."
interstitial_elements_string="Explicit list of elements" \
    " that are to be considered for interstitial generation. " \
    " If no elements are given, intrinsic interstitials" \
    " are considered."
substitutions_string="Substitutional defects (optional) to be generated.\n" \
    " Minimum of two arguments are expected: the element on which the " \
    " substitution is to applied as well as the substitution elements " \
    " (e.g., --sub As P N O)."
input_settings_string="Supply VASP input settings for INCAR, KPOINTS in" \
    " the specified YAML/JSON file."
root_fldr_string="Path (relative or absolute) to directory" \
        " in which data of charged point-defect calculations for" \
        " a particular system are to be found.  Default is the" \
        " current working directory."
chempot_data_file_name_string="Name of input file for chemical potential calculate" \
    " necessary to enter all your calculation entries" \
    " example is in input directory"
defect_data_file_name_string="Name of output file for defect data" \
    " obtained from parsing VASP's files of charged-defect" \
    " calculations in json format.\nDefault is" \
    " \"defect_data.json\"; \"None\" suppresses output."
corrections_file_name_string="Name of output file for data on" \
    " correction terms to formation energies of charged defects" \
    " in json format.\nDefault is \"corrections.json\";" \
    " \"None\" suppresses output."
plot_results_string="Optional flag to indicate that results" \
    " should be plotted."
epsilon_string="Optional: provide a dielectric constant to be" \
    " used in the correction terms of the defect-formation energies.\n" \
    "Only a scalar is accepted.\nIf not provided, the dielectric" \
    " constant is extracted from the corresponding VASP calculation.\n" \
    "Note that this evaluation script expects the dielectric" \
    " constant calculation to have been performed to properly analyze" \
    " the data."
correction_string="Method to be used to compute finite size charge " \
    "correction for the defect-formation energies.\n" \
    "Options are 'freysoldt' and 'kumagai'.\n" \
    "If not provided, Freysoldt method is assumed."
vbm_string="User defined valence band maximum to plot the defect formation " \
    "energies.\nBy default, Materials Project (MP) value or bulk calculated value is " \
    "used.\nHowever, MP vbm could be wrong value for your calculation and bulk vbm " \
    "could be wrong value for defect calculation."
bandgap_string="User defined band gap to plot the defect formation " \
    "energies.\nBy default, Materials Project (MP) bandgap is " \
    "used.\nHowever, MP bandgap could be a severly underpredicted value."
plot_format_string="User defined file format to store the defect formation " \
    "energies plot.\nBy default, 'eps' formation is used.\nSupported" \
    "options are png, eps, jpg."
os_path_abspath_this=os.path.abspath(".")

parser_input_files=subparsers.add_parser(
        "generate_input",
        help="Generates Vasp input files for charged point defects.")
parser_input_files.add_argument("-s", "--structure_file", default=None,
                                dest="struct_file", help=struct_string)
parser_input_files.add_argument("-i", "--mpid", default=None,
                                type=str.lower, dest="mp_id",
                                help=mp_id_string)
parser_input_files.add_argument("-k",  "--mapi_key", default=None,
                                dest="mapi_key", help=mapi_string)
parser_input_files.add_argument("-n", "--nmax", type=int, default=80,
                                dest="nmax", help=nmax_string)
parser_input_files.add_argument("-or", "--oxi_range", action="append",
                                type=str, nargs=3, dest="oxi_range",
                                help=oxi_range_string)
parser_input_files.add_argument("-os", "--oxi_state", action="append",
                                type=str, nargs=2, dest="oxi_state",
                                help=oxi_state_string)
parser_input_files.add_argument("-t", "--type", default="semiconductor",
                                type=str, dest="struct_type",
                                help=struct_type_string)
parser_input_files.add_argument("-noa", "--no_antisites",
                                action="store_false", dest="antisites",
                                help=no_antisites_string)
parser_input_files.add_argument("-ii", "--include_interstitials",
                                action="store_true",
                                dest="include_interstitials",
                                help=include_interstitials_string)
parser_input_files.add_argument("interstitial_elements", type=str,
                                default=[], nargs="*", \
                                help=interstitial_elements_string)
parser_input_files.add_argument("--sub", action="append", type=str,
                                nargs="+", dest="substitutions",\
                                help=substitutions_string)
parser_input_files.add_argument("-is", "--input_settings_file",
                                type=str, default=None,
                                dest="input_settings_file",
                                help=input_settings_string)
parser_input_files.set_defaults(func=generate_input)
parser_vasp_output=subparsers.add_parser(
            "parse_output",
            help="Parses VASP output for calculation of formation energies of"
                " charged point defects.")
parser_vasp_output.add_argument("-i", "--mpid", type=str.lower,
                                dest="mp_id", help=mp_id_string)
parser_vasp_output.add_argument("-k", "--mapi_key", default=None,
                                dest="mapi_key", help=mapi_string)
parser_vasp_output.add_argument("-d", "--directory",
                                default=os_path_abspath_this,
                                dest="root_fldr",
                                help=root_fldr_string)
parser_vasp_output.add_argument("-c", "--input_file_name",
                                default="chempot_setting.txt",
                                dest="file_name",
                                help=chempot_data_file_name_string)
parser_vasp_output.add_argument("-o", "--output_file_name",
                                default="defect_data.json",
                                dest="defect_data_file_name",
                                help=defect_data_file_name_string)
parser_vasp_output.set_defaults(func=parse_output)

parser_compute_corrections = subparsers.add_parser(
        "compute_corrections",
        help="Computes correction for finite size supercell error "
        "associated with charged point defects.")
parser_compute_corrections.add_argument("-i", "--input_file_name",
                                        default="defect_data.json",
                                        dest="defect_data_file_name",
                                        help=defect_data_file_name_string)
parser_compute_corrections.add_argument("-o", "--output_file_name",
                                        default="corrections.json",
                                        dest="corrections_file_name",
                                        help=corrections_file_name_string)
parser_compute_corrections.add_argument("-p", "--plot_results",
                                        action="store_true",
                                        dest="plot_results",
                                        help=plot_results_string)
parser_compute_corrections.add_argument("-e",  "--epsilon", type=float, 
                                        default=None, dest="epsilon",
                                        help=epsilon_string)
parser_compute_corrections.add_argument("-c", "--correction_method",
                                        type=str, default="freysoldt",
                                        dest="correction_method",
                                        help=correction_string)
parser_compute_corrections.set_defaults(func=compute_corrections)

parser_compute_energies = subparsers.add_parser(
        "compute_formation_energies",
        help="Computes formation energies of charged point defects from "
        "the parsed VASP output.")
parser_compute_energies.add_argument("-i", "--input_file_name",
                                     default="defect_data.json",
                                     dest="defect_data_file_name",
                                     help=defect_data_file_name_string)
parser_compute_energies.add_argument("-c", "--corrections_file_name",
                                     default="corrections.json",
                                     dest="corrections_file_name",
                                     help=corrections_file_name_string)
parser_compute_energies.add_argument("-vb", "--vbm",
                                     type=float, default=0, dest="vbm",
                                     help=vbm_string)
parser_compute_energies.add_argument("-bg", "--bandgap",
                                     type=float, default=0, dest="bandgap",
                                     help=bandgap_string)
parser_compute_energies.add_argument("-f", "--format", default="eps",
                                     dest="file_format",
                                     help=plot_format_string)
parser_compute_energies.set_defaults(func = compute_formation_energies)

args=parser.parse_args()
args.func(args)
