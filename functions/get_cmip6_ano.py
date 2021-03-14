
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

######################################################################
# Define Functions
######################################################################

def calc_anomalie(hist_c,fut_c,var):
    if var == "tas" or var == 'tasmin' or var == 'tasmax':
        res = hist_c-fut_c
    if var == 'pr':
        res = (hist_c+0.001)/(fut_c+0.001)
    return res

######################################################################
# Parse Arguemnts
######################################################################

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

######################################################################
# read the CMIP 6 catalogue and get data
######################################################################
url = "https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json"# open the catalog
df_esm = intake.open_esm_datastore(url)
vars = ['tas', 'tasmax', 'tasmin', 'pr']/
for var1 in vars:
    model = df_esm.search(activity_id=activity1,
                            experiment_id=ssp1,
                            variable_id=var1,
                            source_id=source1,
                            member_id=member1,
                            table_id=table1
                           )
    model_cat = model.to_dataset_dict()
    hist = df_esm.search(activity_id='CMIP', #activity1,
                            experiment_id='historical',
                            variable_id=var1,
                            source_id=source1,
                            member_id=member1,
                            table_id=table1
                           )
    hist_cat = hist.to_dataset_dict()
    key_model, value = list(model_cat.items())[0]
    model_ds = model_cat[key_model]
    key_hist, value = list(hist_cat.items())[0]
    hist_ds = hist_cat[key_hist]
    hist_monthly_avr = hist_ds.sel(time=slice(refps,refpe)).groupby("time.month").mean("time")
    fut_monthly_avr  = model_ds.sel(time=slice(fefps,fefpe)).groupby("time.month").mean("time")
    ano1 = calc_anomalie(hist_monthly_avr,fut_monthly_avr,var1)
    name1 = tmp + var1 + 'ano_tmp.nc'
    ano1.to_netcdf(path= name1)










