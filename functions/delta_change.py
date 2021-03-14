#! /usr/bin/env python

# This script creates delta change based
# high resolution climatologies and bio climatic
# variables for a choosen time period
# author: Dirk N. Karger, dirk.karger@wsl.ch

# ***************************************
# import modules
# ***************************************

import saga_api, sys, os, argparse, datetime, os.path, cdsapi, psutil, shutil
process = psutil.Process(os.getpid())


