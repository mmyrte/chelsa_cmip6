import xarray as xr

import numpy as np
from src.classes import BioClim
from src.classes import GetClim


class ChelsaClimat:
    """chelsa class"""
    def __init__(self, xmin, xmax, ymin, ymax):
        """ Create a set of baseline clims """
        self.tas = chelsaV2(xmin, xmax, ymin, ymax, 'tas').get_chelsa()
        self.tasmax = chelsaV2(xmin, xmax, ymin, ymax, 'tasmax').get_chelsa()
        self.tasmin = chelsaV2(xmin, xmax, ymin, ymax, 'tasmin').get_chelsa()
        self.pr = chelsaV2(xmin, xmax, ymin, ymax, 'pr').get_chelsa()





ch_climat = ChelsaClimat(5.3,10.4,46,47.5)
cm_climat = CmipClimat('ScenarioMIP', 'Amon',
                 'ssp585',
                 'MPI-M', 'MPI-ESM1-2-LR',
                 'r1i1p1f1', '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')


cm_ano_tas = cm_climat.tas.get_anomaly()
cm_ano_tas_inter = interpol(cm_ano_tas,ch_climat.tas).interpolate()

cm_ano_tas_inter = cm_ano_tas_inter.drop('lat')
cm_ano_tas_inter = cm_ano_tas_inter.drop('lon')
cm_ano_tas_inter = cm_ano_tas_inter.drop('height')
cm_ano_tas_inter = cm_ano_tas_inter.drop('lat_bnds')
cm_ano_tas_inter = cm_ano_tas_inter.drop('lon_bnds')
ch_cli_tas = ch_climat.tas.to_dataset(name="tas")
ch_cli_tas = ch_cli_tas.rename({'time': 'month'})
ch_cli_tas = ch_cli_tas.drop('band')

x1 = ch_cli_tas + cm_ano_tas_inter
x1.to_netcdf("/mnt/storage/karger/test.nc")











cube_location1 = '/mnt/storage/karger/W5E5/tasmin_W5E5v1.0_19790101-19801231.nc'
cube_location2 = '/mnt/storage/karger/W5E5/tasmax_W5E5v1.0_19790101-19801231.nc'
cube_location3 = '/mnt/storage/karger/W5E5/tas_W5E5v1.0_19790101-19801231.nc'
cube_location4 = '/mnt/storage/karger/W5E5/pr_W5E5v1.0_19790101-19801231.nc'

cube1 = xr.open_dataset(cube_location1)  # open dataset
cube1 = cube1.chunk({'time': -1}).transpose('time', ...)  # type: xr.DataSet
cube2 = xr.open_dataset(cube_location2)  # open dataset
cube2 = cube2.chunk({'time': -1}).transpose('time', ...)  # type: xr.DataSet
cube3 = xr.open_dataset(cube_location3)  # open dataset
cube3 = cube3.chunk({'time': -1}).transpose('time', ...)  # type: xr.DataSet
cube4 = xr.open_dataset(cube_location4)  # open dataset
cube4 = cube4.chunk({'time': -1}).transpose('time', ...)  # type: xr.DataSet

refps = '1979-01-01'
refpe = '1980-12-31'




ch = chelsaV2(5.3,10.4,46,47.5, 'tas').get_chelsa()



c1 = clim_class(cube4['pr'].load().sel(time=slice(refps,refpe)).groupby("time.month").mean("time"),
                cube3['tas'].load().sel(time=slice(refps,refpe)).groupby("time.month").mean("time"),
                cube2['tasmax'].load().sel(time=slice(refps,refpe)).groupby("time.month").mean("time"),
                cube1['tasmin'].load().sel(time=slice(refps,refpe)).groupby("time.month").mean("time"))

for n in range(1,20):
    a = getattr(c1, 'bio' + str(n))
    a().to_netcdf('/mnt/storage/karger/scratch/bio' + str(n) + '.nc')





cmip_tasmax_ano = cmip_tasmax.get_anomaly()



testme = ch_climat.tasmax.to_dataset(name="tasmax")


ano_inter = interpol(cmip_tasmax_ano, ch)

anox = ano_inter.interpolate()
anox = anox.drop('lat')
anox = anox.drop('lon')
anox = anox.drop('lat_bnds')
anox = anox.drop('lon_bnds')
anox.to_netcdf("/mnt/storage/karger/anox.nc")
testme = testme.drop('band')
anocor = anox + testme
anocor.to_netcdf("/mnt/storage/karger/anocor.nc")




