import re
import os
from localAlignement.parameters_and_strings import *
from natsort import natsorted
def search_vectors(folder, regex_x, regex_y):
    files = os.listdir(folder)
    files_x = [f for f in files if re.search(regex_x,f) and any([f.endswith(x) for x in allowed_vf_endings])]
    files_y = [f for f in files if re.search(regex_y,f) and any([f.endswith(x) for x in allowed_vf_endings])]

    # try to identify frame without group
    files_x = {i:x for i,x in enumerate(natsorted(files_x))}
    files_y = {i:x for i,x in enumerate(natsorted(files_y))}

    # TODO: add identification with group in regex
    return files_x, files_y