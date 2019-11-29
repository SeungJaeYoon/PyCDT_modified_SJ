from pymatgen.io.vasp.outputs import Vasprun

vr=Vasprun('vasprun.xml')
print(vr.eigenvalue_band_properties)