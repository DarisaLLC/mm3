#!/usr/bin/python
from __future__ import print_function
def warning(*objs):
    print(time.strftime("%H:%M:%S Warning:", time.localtime()), *objs, file=sys.stderr)
def information(*objs):
    print(time.strftime("%H:%M:%S", time.localtime()), *objs, file=sys.stdout)

# import modules
import sys
import os
import time
import inspect
import getopt
import yaml
from pprint import pprint # for human readable file output
try:
    import cPickle as pickle
except:
    import pickle
import numpy as np
from scipy.io import savemat

# user modules
# realpath() will make your script run, even if you symlink it
cmd_folder = os.path.realpath(os.path.abspath(
                          os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# This makes python look for modules in ./external_lib
cmd_subfolder = os.path.realpath(os.path.abspath(
                             os.path.join(os.path.split(inspect.getfile(
                             inspect.currentframe()))[0], "external_lib")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import mm3_helpers as mm3

# when using this script as a function and not as a library the following will execute
if __name__ == "__main__":
    # hardcoded parameters

    # get switches and parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:],"f:o:s:")
        # switches which may be overwritten
        specify_fovs = False
        user_spec_fovs = []
        start_with_fov = -1
        param_file_path = ''
    except getopt.GetoptError:
        warning('No arguments detected (-f -s -o).')

    for opt, arg in opts:
        if opt == '-o':
            try:
                specify_fovs = True
                for fov_to_proc in arg.split(","):
                    user_spec_fovs.append(int(fov_to_proc))
            except:
                warning("Couldn't convert argument to an integer:",arg)
                raise ValueError
        if opt == '-s':
            try:
                start_with_fov = int(arg)
            except:
                warning("Couldn't convert argument to an integer:",arg)
                raise ValueError
        if opt == '-f':
            param_file_path = arg # parameter file path

    # Load the project parameters file
    if len(param_file_path) == 0:
        raise ValueError("A parameter file must be specified (-f <filename>).")
    information ('Loading experiment parameters.')
    p = mm3.init_mm3_helpers(param_file_path) # loads and returns

    # load specs file
    try:
        with open(p['ana_dir'] + '/specs.pkl', 'r') as specs_file:
            specs = pickle.load(specs_file)
    except:
        warning('Could not load specs file.')
        raise ValueError

    # make list of FOVs to process (keys of channel_mask file)
    fov_id_list = sorted([fov_id for fov_id in specs.keys()])

    # remove fovs if the user specified so
    if specify_fovs:
        fov_id_list[:] = [fov for fov in fov_id_list if fov in user_spec_fovs]
    if start_with_fov > 0:
        fov_id_list[:] = [fov for fov in fov_id_list if fov_id >= start_with_fov]

    information("Processing %d FOVs." % len(fov_id_list))

    # load cell data dict
    with open(p['cell_dir'] + 'complete_cells.pkl', 'r') as cell_file:
        Complete_Cells = pickle.load(cell_file)

    # create dictionary which organizes cells by fov and peak_id
    Cells_by_peak = mm3.organize_cells_by_channel(Complete_Cells, specs)

    # for each set of cells in one fov/peak, compute the fluorescence
    for fov_id in fov_id_list:
        for peak_id, Cells in Cells_by_peak[fov_id].items():
            mm3.find_cell_intensities(fov_id, peak_id, Cells)

    # save the data out again
    # Just the complete cells, those with mother and daugther
    with open(p['cell_dir']+ '/complete_cells_fl.pkl', 'wb') as cell_file:
        pickle.dump(Complete_Cells, cell_file)