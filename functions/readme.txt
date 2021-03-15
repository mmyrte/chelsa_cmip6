chelsa_downscale_cmip6.sh version 1.0
(c) Dirk Nikolaus Karger
contact dirk.karger@wsl.ch

This script creates monthly anomalies
for min-, max-, and mean temperature, and precipitation rate.
fhe output directory needs the following. It automatically
gets CMIP6 data from the google cloud storage from pangeo. It calls
two python scripts. Dependencies are resolvedn in ubuntu_py_cmip6.cont
and chelsa_V2.1.cont. Tested with: singularity version 3.3.0-809.g78ec427cc
and intakes it ("https://raw.githubusercontent.com/NCAR/intake-esm-datastore/master/catalogs/pangeo-cmip6.json")
The script only works with models available at pangeo.

# chelsa_downscale_cmip6.sh takes the following arguments
# the output directory and the base of the temporary directory need to exist
Source model (GCM), e.g. GFDL-ESM4, string
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
Example parameters:
MODEL=GFDL-ESM4
TABLE=Amon
ACTIVITY=ScenarioMIP
SSP=ssp585
MEMBER=r1i1p1f1
REFPS=1981-01-01
REFPE=2010-12-31
FEFPS=2041-01-01
FEFPE=2070-12-31
TEMP=/home/$USER/scratch/
OUTPUT=/home/$USER/output/
YMIN=46.0
YMAX=47.5
XMIN=5.3
XMAX=10.4

# You can run the script in the following way for example
bash chelsa_downscale_cmip6.sh GFDL-ESM4 Amon ScenarioMIP ssp585 r1i1p1f1 1981-01-01 2010-12-31 2041-01-01 2070-12-31 /home/$USER/scratch/ /home/$USER/output/ 46.0 47.5 5.3 10.4
