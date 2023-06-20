#!/usr/bin/env python

#This file is part of chelsa_cmip6.
#
#chelsa_cmip6 is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#chelsa_cmip6 is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with chelsa_cmip6.  If not, see <https://www.gnu.org/licenses/>.


from src.chelsa_cmip6.BioClim import BioClim
from src.chelsa_cmip6.GetClim import ChelsaClimat
from src.chelsa_cmip6.GetClim import CmipClimat
from src.chelsa_cmip6.GetClim import DeltaChangeClim




ds1 = _get_esgf('CMIP6',table_id="Amon",
                variable_id="tas",
                experiment_id="ssp585",
                source_id="MPI-ESM1-2-LR",
                member_id="r1i1p1f1")


def main():
    print('starting downloading CMIP data:')
    cm_climat = CmipClimat('ScenarioMIP', 'Amon',
                     'ssp585',
                     'MPI-M', 'MPI-ESM1-2-LR',
                     'r1i1p1f1', '1981-01-15',
                     '2010-12-15', '2041-01-15',
                     '2070-12-15', use_esgf=True)

    print('starting downloading CHELSA data:')
    ch_climat = ChelsaClimat(5.3, 10.4, 46, 47.5)

    print('starting building climatologies data:')
    dc = DeltaChangeClim(ch_climat, cm_climat, '1981-01-15',
                     '2010-12-15', '2041-01-15',
                     '2070-12-15', '/mnt/storage/karger/')

    print('saving bioclims:')
    biohist = BioClim(dc.hist_pr, dc.hist_tas, dc.hist_tasmax, dc.hist_tasmin)
    biofutr = BioClim(dc.futr_pr, dc.futr_tas, dc.futr_tasmax, dc.futr_tasmin)

    for n in range(1, 20):
        name = '/home/karger/' + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, 'bio' + str(n))().to_netcdf(name)

    for n in ['gdd']:
        name = '/home/karger/' + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_'  + str(n) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, str(n))().to_netcdf(name)

    for n in range(1, 20):
        name = '/home/karger/' + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, 'bio' + str(n))().to_netcdf(name)

    for n in ['gdd']:
        name = '/home/karger/' + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str(n) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, str(n))().to_netcdf(name)


if __name__ == '__main__':
    main()

