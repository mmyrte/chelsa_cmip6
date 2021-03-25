import xarray as xr
import pyesgf
import numpy as np
from src.classes import BioClim


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





cmip_tas = cmip6_clim('ScenarioMIP', 'Amon',
                 'tas', 'ssp585',
                 "MPI-M", "MPI-ESM1-2-LR",
                 "r1i1p1f1", '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')

cmip_tasmax = cmip6_clim('ScenarioMIP', 'Amon',
                 'tasmax', 'ssp585',
                 "MPI-M", "MPI-ESM1-2-LR",
                 "r1i1p1f1", '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')

cmip_tasmin = cmip6_clim('ScenarioMIP', 'Amon',
                 'tasmin', 'ssp585',
                 "MPI-M", "MPI-ESM1-2-LR",
                 "r1i1p1f1", '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')

cmip_pr = cmip6_clim('ScenarioMIP', 'Amon',
                 'pr', 'ssp585',
                 "MPI-M", "MPI-ESM1-2-LR",
                 "r1i1p1f1", '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')

cmip_tasmax_ano = cmip_tasmax.get_anomaly()



ch = chelsaV2(5.3,10.4,46,47.5, 'tas').get_chelsa()


ano_inter = interpol(cmip_tasmax_ano, ch)






