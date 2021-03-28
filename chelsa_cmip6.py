#!/usr/bin/env python

from classes.BioClim import quarter_class
from classes.BioClim import BioClim
from classes.GetClim import _get_cmip
from classes.GetClim import interpol
from classes.GetClim import chelsaV2
from classes.GetClim import cmip6_clim
from classes.GetClim import ChelsaClimat
from classes.GetClim import CmipClimat
from classes.GetClim import DeltaChangeClim
import argparse

ap = argparse.ArgumentParser(
    description='''# This script creates monthly high-resolution 
    for min-, max-, and mean temperature, precipitation rate 
    and bioclimatic variables from anomalies and using CHELSA V2.1 as 
    baseline high resolution climatology. Only works for GCMs for
    which tas, tasmax, tasmin, and pr are available.
    ''',
    epilog='''author: Dirk N. Karger, dirk.karger@wsl.ch, Version 1.1'''
)
ap.add_argument('-s', '--source_id', type=str,
                help="Source model (GCM), e.g. MPI-ESM1-2-LR, string")
ap.add_argument('-i', '--institution_id', type=str,
                help="Institution ID, e.g. MPI-M, string")
ap.add_argument('-t', '--table_id', type=str,
                help="table id, e.g. Amon, string")
ap.add_argument('-a', '--activity_id', type=str,
                help="activity id, e.g. ScenarioMIP, string")
ap.add_argument('-e', '--experiment_id', type=str,
                help="experiment id, e.g. ssp585, string")
ap.add_argument('-m', '--member_id', type=str,
                help="ensemble member, e.g. r1i1p1f1, string")
ap.add_argument('-rs', '--refps', type=str,
                help="reference period start, e.g. 1981-01-01, date format YYYY-MM-DD, string")
ap.add_argument('-re', '--refpe', type=str,
                help="reference period end, e.g. 2010-12-31, date format YYYY-MM-DD, string")
ap.add_argument('-fs', '--fefps', type=str,
                help="anomaly period start, e.g. 2041-01-01, date format YYYY-MM-DD, string")
ap.add_argument('-fe', '--fefpe', type=str,
                help="anomaly period end, e.g. 2070-01-01, date format YYYY-MM-DD, string")
ap.add_argument('-o', '--output', type=str,
                help="output directory, needs to exist, string")

args = ap.parse_args()
print("Downscaling:")
print(args)

source_id = args.source_id
institution_id = args.institution_id
table_id = args.table_id
activity_id = args.activity_id
experiment_id = args.experiment_id
member_id = args.member_id
refps = args.refps
refpe = args.refpe
fefps = args.fefps
fefpe = args.fefpe
output = args.output

def main():
    print('starting downloading CMIP data:')
    cm_climat = CmipClimat(source_id, table_id,
                           experiment_id,
                           institution_id, source_id,
                           member_id, refps,
                           refpe, fefps,
                           fefpe)

    print('starting downloading CHELSA data:')
    ch_climat = ChelsaClimat(5.3, 10.4, 46, 47.5)

    dc = DeltaChangeClim(ch_climat, cm_climat, refps,
                         refpe, fefps,
                         fefpe, output)

    print('starting building climatologies data:')
    biohist = BioClim(dc.hist_pr, dc.hist_tas, dc.hist_tasmax, dc.hist_tasmin)
    biofutr = BioClim(dc.futr_pr, dc.futr_tas, dc.futr_tasmax, dc.futr_tasmin)

    print('saving bioclims:')
    for n in range(1, 20):
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, 'bio' + str(n))().to_netcdf(name)
    for n in range(1, 20):
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, 'bio' + str(n))().to_netcdf(name)


if __name__ == '__main__':
    main()

