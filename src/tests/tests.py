#!/usr/bin/env python

import xarray as xr
import numpy as np
from src.classes import BioClim
from src.classes import GetClim
import datetime

def main():
    ch_climat = ChelsaClimat(5.3,10.4,46,47.5)
    cm_climat = CmipClimat('ScenarioMIP', 'Amon',
                     'ssp585',
                     'MPI-M', 'MPI-ESM1-2-LR',
                     'r1i1p1f1', '1981-01-15',
                     '2010-12-15', '2041-01-15',
                     '2070-12-15')

    dc = DeltaChangeClim(ch_climat, cm_climat,'1981-01-15',
                     '2010-12-15', '2041-01-15',
                     '2070-12-15', '/mnt/storage/karger/')

    biohist = BioClim(dc.hist_pr, dc.hist_tas, dc.hist_tasmax, dc.hist_tasmin)
    biofutr = BioClim(dc.futr_pr, dc.futr_tas, dc.futr_tasmax, dc.futr_tasmin)

    for n in range(1, 20):
        name = '/mnt/storage/karger/' + 'CHELSA'+ '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id+ '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, 'bio' + str(n))().to_netcdf(name)
    for n in range(1, 20):
        name = '/mnt/storage/karger/' + 'CHELSA'+ '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id+ '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, 'bio' + str(n))().to_netcdf(name)


if __name__ == '__main__':
    main()

