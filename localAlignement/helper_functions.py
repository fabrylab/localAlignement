import re
import os
from localAlignement.parameters_and_strings import *
import natsort


def search_vectors(folder, regex_x, regex_y):
    files = os.listdir(folder)
    files_x = [f for f in files if re.search(regex_x,f) and any([f.endswith(x) for x in allowed_vf_endings])]
    files_y = [f for f in files if re.search(regex_y,f) and any([f.endswith(x) for x in allowed_vf_endings])]

    # try to identify frame without group
    files_x = {i:x for i,x in enumerate(natsort.natsorted(files_x))}
    files_y = {i:x for i,x in enumerate(natsort.natsorted(files_y))}

    # TODO: add identification with group in regex
    return files_x, files_y




def make_rank_list(values):

    '''
    produce a list containing the corresponding rank of input values. Ties
    get the same rank. This is used for obtaining the correct sort indices
    (frames in the cdb database) for the list of frames.
    Sorting is performed by the natsort package, wich should recognize signs and scientific notation
    '''

    unique_values = set(values)
    unique_values = natsort.natsorted(unique_values, alg=natsort.REAL)
    unique_values_dict = {value: rank for rank, value in enumerate(unique_values)}  # value:rank of the frame
    rank_list = [unique_values_dict[value] for value in values]
    return rank_list, unique_values_dict

def warn_non_unique(sort_id, sort_id_dict, frame_groups):

    unique, counts = np.unique(sort_id, return_counts=True)
    non_unique = unique[np.where(counts > 1)]
    wrong_files = []
    if len(non_unique)>1:
        for n in non_unique:
            frame_group = [i for i, j in sort_id_dict.items() if j == n][0]
            wrong_files.extend([f for f, group in frame_groups.items() if group == frame_group])
        print("more than one file per frame was identfied for the following files:")
        print(wrong_files)