import os 
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from SJchempot import usrchempot

chem=usrchempot()
print(chem.get_chempot())