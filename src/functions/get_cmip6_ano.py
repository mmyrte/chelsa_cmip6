#! /usr/bin/env python

######################################################################
# This function downloads data from CMIP6
# and automatically creates anomalies from it
######################################################################


######################################################################
# Import modules
######################################################################

import intake
import pandas as pd
import xarray as xr
import argparse

######################################################################
# Get the command line arguments
######################################################################
ap = argparse.ArgumentParser(
    description='''# This python script creates monthly anomalies 
    for min-, max-, and mean temperature, and precipitation rate. 
    The output directory needs the following. It automatically 
    gets CMIP6 data from the google cloud storage from pangeo
    and intakes it ("https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json")
    The script only works with models available at pangeo.
    Dependencies for ubuntu_20.08:
    xarray 16.02
    intake 0.6.1
    intake-esm 2020.12.18    
    All dependencies are resolved in the ubuntu_py_cmip6.cont singularity container
    Tested with: singularity version 3.3.0-809.g78ec427cc
    ''',
    epilog='''author: Dirk N. Karger, dirk.karger@wsl.ch, Version 2.1'''
)
######################################################################
# Parse Arguemnts
######################################################################
debugging = 1 #turn local debugging on/off
if debugging == 1:
    source1     = 'GFDL-ESM4'
    table1      = 'Amon'
    activity1   = 'ScenarioMIP'
    ssp1        = 'ssp585'
    member1     = 'r1i1p1f1'
    refps       = '1981-01-01'
    refpe       = '2010-12-31'
    fefps       = '2041-01-01'
    fefpe       = '2070-12-31'
    tmp = '/home/karger/scratch/'

if debugging != 1:
    ap.add_argument('-s','--source', type=str, help="Source model (GCM), e.g. GFDL-ESM4, string")
    ap.add_argument('-t','--table', type=str, help="table id, e.g. Amon, string")
    ap.add_argument('-a','--activity', type=str,  help="activity id, e.g. ScenarioMIP, string")
    ap.add_argument('-e','--experiment', type=str, help="experiment id, e.g. ssp585, string")
    ap.add_argument('-m','--member', type=str,  help="ensemble member, e.g. r1i1p1f1, string")
    ap.add_argument('-rs','--refps', type=str, help="reference period start, e.g. 1981-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-re','--refpe', type=str, help="reference period end, e.g. 2010-12-31, date format YYYY-MM-DD, string")
    ap.add_argument('-fs','--fefps', type=str, help="anomaly period start, e.g. 2041-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-fe','--fefpe', type=str, help="anomaly period end, e.g. 2070-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-tm','--tmp', type=str, help="directory for temporary files, string")
    args = ap.parse_args()
    print(args)
    source1   = args.source
    table1    = args.table
    activity1 = args.activity
    ssp1      = args.experiment
    member1   = args.member
    refps     = args.refps
    refpe     = args.refpe
    fefps     = args.fefps
    fefpe     = args.fefpe
    tmp       = args.tmp

######################################################################
# Define Functions
######################################################################

def calc_anomaly(hist_c,fut_c,var):
    if var == "tas" or var == 'tasmin' or var == 'tasmax':
        res = hist_c-fut_c # additive anomaly
    if var == 'pr':
        res = (hist_c+0.001)/(fut_c+0.001) # multiplicative anomaly
    return res

######################################################################
# read the CMIP 6 catalogue and get data
######################################################################
if __name__ == '__main__':
    url = "https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json" #set url
    df_esm = intake.open_esm_datastore(url) # open the catalog
    vars = ['tas', 'tasmax', 'tasmin', 'pr'] # vector of required variables
    for var1 in vars:
        model = df_esm.search(activity_id=activity1,
                                experiment_id=ssp1,
                                variable_id=var1,
                                source_id=source1,
                                member_id=member1,
                                table_id=table1
                               )
        model_cat = model.to_dataset_dict() # create dataset dictionary
        hist = df_esm.search(activity_id='CMIP',
                                experiment_id='historical',
                                variable_id=var1,
                                source_id=source1,
                                member_id=member1,
                                table_id=table1
                               )
        hist_cat = hist.to_dataset_dict() # create dataset dictionary
        key_model, value = list(model_cat.items())[0] # get key of the model run
        model_ds = model_cat[key_model]
        key_hist, value = list(hist_cat.items())[0] # get key of the hist run
        hist_ds = hist_cat[key_hist]
        hist_monthly_avr = hist_ds.sel(time=slice(refps,refpe)).groupby("time.month").mean("time") # select time and get montly climatologies
        fut_monthly_avr  = model_ds.sel(time=slice(fefps,fefpe)).groupby("time.month").mean("time") # select time and get montly climatologies
        ano1 = calc_anomaly(hist_monthly_avr,fut_monthly_avr,var1) # calculate anomaly
        name1 = tmp + var1 + 'ano_tmp.nc' #set tmp name
        ano1.to_netcdf(path= name1) #save to ncdf in tmp










