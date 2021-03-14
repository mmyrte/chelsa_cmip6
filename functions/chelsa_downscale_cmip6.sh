#!/bin/bash
MODEL=$1
TABLE=$2
ACTIVITY=$3
SSP=$4
MEMBER=$5
REFPS=$6
REFPE=$7
FEFPS=$8
FEFPE=$9
TEMP=$10
OUTPUT=$11
YMIN=$12
YMAX=$13
XMIN=$14
XMAX=$15
if [ -z "$1" ]
then
echo 'chelsa_downscale_cmip6.sh version 1.0
    (c) Dirk Nikolaus Karger
    This script creates monthly anomalies
    for min-, max-, and mean temperature, and precipitation rate.
    The output directory needs the following. It automatically
    gets CMIP6 data from the google cloud storage from pangeo. It calls
    two python scripts. Dependencies are resolvedn in ubuntu_py_cmip6.cont
    and chelsa_V2.1.cont. Tested with: singularity version 3.3.0-809.g78ec427cc
    and intakes it ("https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json")
    The script only works with models available at pangeo.
    Use the following way: chelsa_downscale_cmip6.sh Source model (GCM), e.g. GFDL-ESM4, string
    table id, e.g. Amon, string
    activity id, e.g. ScenarioMIP, string
    experiment id, e.g. ssp585, string
    ensemble member, e.g. r1i1p1f1, string
    reference period start, e.g. 1981-01-01, date format YYYY-MM-DD, string
    reference period end, e.g. 2010-12-31, date format YYYY-MM-DD, string
    anomaly period start, e.g. 2041-01-01, date format YYYY-MM-DD, string
    anomaly period end, e.g. 2070-01-01, date format YYYY-MM-DD, string
    directory for temporary files, string
    directory for output files, string
    western boundary of the extent, WGS84 lat. lon., float
    eastern boundary of the extent, WGS84 lat. lon., float
    southern boundary of the extent, WGS84 lat. lon., float
    northern boundary of the extent, WGS84 lat. lon., float'
exit 1
fi
mkdir -p $TEMP
singularity -exec ubuntu_py_cmip6.cont python3 get_cmip6_ano.py --source $MODEL --table $TABLE --activity $ACTIVITY --ssp $SSP --member $MEMBER --refps $REFPS --refpe $REFPE --fefps $FEFPS --fefpe $FEFPE --tmp = $TEMP
singularity -exec chelsa_V2.1.cont python get_cmip6_ano.py --source $MODEL --table $TABLE --activity $ACTIVITY --ssp $SSP --member $MEMBER --refps $REFPS --refpe $REFPE --fefps $FEFPS --fefpe $FEFPE --tmp = $TEMP --outpath $OUTPUT --ymin $YMIN --ymax $YMAX --xmin $XMIN --xmax $XMAX
rm -r $TEMP