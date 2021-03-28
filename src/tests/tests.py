#!/usr/bin/env python

import xarray as xr
import numpy as np
from src.classes import BioClim
from src.classes import GetClim


if __name__ == '__main__':
    ch_climat = ChelsaClimat(5.3,10.4,46,47.5)
    cm_climat = CmipClimat('ScenarioMIP', 'Amon',
                     'ssp585',
                     'MPI-M', 'MPI-ESM1-2-LR',
                     'r1i1p1f1', '1981-01-15',
                     '2010-12-15', '2041-01-15',
                     '2070-12-15')

    dc = DeltaChangeClim(ch_climat, cm_climat, '/mnt/storage/karger/')
    biohist = BioClim(dc.hist_tas, dc.hist_tasmax, dc.hist_tasmin, dc.hist_pr)
    biofutr = BioClim(dc.futr_tas, dc.futr_tasmax, dc.futr_tasmin, dc.futr_pr)

    for n in range(1, 19):
        getattr(biohist, 'bio' + str(n)).to_netcdf('/mnt/storage/karger/'
                                     + 'CHELSA_'
                                     + cm_climat.tas.institution_id
                                     + '_' + cm_climat.tas.source_id
                                     + '_' + str('bio' + n)
                                     + '_' + cm_climat.tas.experiment_id
                                     + '_' + cm_climat.tas.member_id
                                     + '_' + cm_climat.tas.refps
                                     + '_' + cm_climat.tas.refpe
                                     + '.nc')


























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


class ChelsaClimat:
    """chelsa class"""
    def __init__(self, xmin, xmax, ymin, ymax):
        """ Create a set of baseline clims """
        self.tas = chelsaV2(xmin, xmax, ymin, ymax, 'tas').get_chelsa()
        self.tasmax = chelsaV2(xmin, xmax, ymin, ymax, 'tasmax').get_chelsa()
        self.tasmin = chelsaV2(xmin, xmax, ymin, ymax, 'tasmin').get_chelsa()
        self.pr = chelsaV2(xmin, xmax, ymin, ymax, 'pr').get_chelsa()


class DeltaChangeClim:
    """Delta change class"""
    def __init__(self, ChelsaClimat, CmipClimat, output=False):
        """ Create a set of baseline clims """
        self.output = output
        self.hist_tas = ChelsaClimat.tas.to_dataset(name='tas').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tas.get_anomaly('hist'), ChelsaClimat.tas).interpolate()
        self.hist_tasmin = ChelsaClimat.tasmin.to_dataset(name='tasmin').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tasmin.get_anomaly('hist'), ChelsaClimat.tasmin).interpolate()
        self.hist_tasmax = ChelsaClimat.tasmax.to_dataset(name='tasmax').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tasmax.get_anomaly('hist'), ChelsaClimat.tasmax).interpolate()
        self.hist_pr = ChelsaClimat.pr.to_dataset(name='pr').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.pr.get_anomaly('hist'), ChelsaClimat.pr).interpolate()
        self.futr_tas = ChelsaClimat.tas.to_dataset(name='tas').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tas.get_anomaly('future'), ChelsaClimat.tas).interpolate()
        self.futr_tasmin = ChelsaClimat.tasmin.to_dataset(name='tasmin').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tasmin.get_anomaly('future'), ChelsaClimat.tasmin).interpolate()
        self.futr_tasmax = ChelsaClimat.tasmax.to_dataset(name='tasmax').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.tasmax.get_anomaly('future'), ChelsaClimat.tasmax).interpolate()
        self.futr_pr = ChelsaClimat.pr.to_dataset(name='pr').rename({'time': 'month'}).drop('band') - interpol(
            CmipClimat.pr.get_anomaly('future'), ChelsaClimat.pr).interpolate()
        if output:
            print('saving files to :' + output)
            for var in ['hist_tas', 'hist_tasmax', 'hist_tasmin',
                        'hist_pr']:
                self.getattr(self, var).to_netcdf(self.output
                                                  + 'CHELSA_'
                                                  + CmipClimat.tas.institution_id
                                                  + '_' + CmipClimat.tas.source_id
                                                  + '_' + CmipClimat.tas.experiment_id
                                                  + '_' + CmipClimat.tas.member_id
                                                  + '_' + CmipClimat.tas.refps
                                                  + '_' + CmipClimat.tas.refpe
                                                  + '.nc')
            for var in ['futr_tas', 'futr_tasmax',
                        'futr_tasmin', 'futr_pr']:
                self.getattr(self, var).to_netcdf(self.output
                                                  + 'CHELSA_'
                                                  + CmipClimat.tas.institution_id
                                                  + '_' + CmipClimat.tas.source_id
                                                  + '_' + CmipClimat.tas.experiment_id
                                                  + '_' + CmipClimat.tas.member_id
                                                  + '_' + CmipClimat.tas.refps
                                                  + '_' + CmipClimat.tas.refpe
                                                  + '.nc')




