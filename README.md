chelsa_cmip6
-----------
This package contains functions to creates monthly high-resolution 
climatologies for min-, max-, and mean temperature, precipitation rate 
and bioclimatic variables from anomalies and using CHELSA V2.1 as 
baseline high resolution climatology. Only works for GCMs for
hich tas, tasmax, tasmin, and pr are available. It is part of the
CHELSA Project: (CHELSA, <https://www.chelsa-climate.org/>).




COPYRIGHT
---------
(C) 2021 Dirk Nikolaus Karger



LICENSE
-------
chelsa_cmip6 is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

chelsa_cmip6 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with chelsa_cmip6. If not, see <http://www.gnu.org/licenses/>.



REQUIREMENTS
------------
ISIMIP3BASD is written in Python 3. It has been tested to run well with the
following Python release and package versions.
- python 3.6.5 
- xarray 0.16.2
- requests 2.25.1
- numpy 1.19.5
- rasterio 1.2.1
- pandas 1.1.5
- zarr 2.6.1
- gcsfs 0.7.2
- datetime 3.9.2



HOW TO USE
----------
The chelsa_cmip6 module provides functions to create monthly climatologies from climate
simulation data from CMIP6 using climate observation data from CHELSA V.2.1
at a 0.0083333° grid resolution for a given area of choice.

The GetClim module contains classes and functions to connect to CMIP6 data
via the Google cloud storage and read the data into xarrays. It also creates
monthly climatologies using the delta change anomaly correction method for a given 
time period. 

The BioClim module contains classes calculating various bioclimatic parameters
from climatological data (see: https://chelsa-climate.org/bioclim).

The delta change method applied is relatively insensitive towards individual model 
bias of the GCM as it only uses the difference (ratio) for a given variable between
a reference period and a future period. In case of temperature an additive delta change 
is applied. In case of precipitation a multiplicative delta change is applied by 
adding a constant of 0.001 kg*m**-1*day to both the reference and the future data
to avoid division by zero. 

The code only runs for CMIP6 models for which all needed variables tas, tasmax, tasmin, pr,
are available for both the reference and the future period.

The standard reference period is 1981-01-01 - 2010-12-31. If another reference period is 
chosen, the code conducts a delta change for this period as well. Best practice would be to 
choose the standard reference period.

EXAMPLE: You can use the program by running the following command in the terminal:
python3 chelsa_cmip6.py --activity_id 'ScenarioMIP' --table_id 'Amon' --experiment_id 'ssp585' --institution_id 'MPI-M' --source_id 'MPI-ESM1-2-LR' --member_id 'r1i1p1f1' --refps '1981-01-15' --refpe '2010-12-15' --fefps '2041-01-15' --fefpe '2070-12-15' --output '<your_output_directory>'


The output consist of netCDF4 files.


CONTACT
-------
<dirk.karger@wsl.ch>



AUTHOR
------
Dirk Nikolaus Karger
Swiss Federal Research Institute WSL
Zürcherstrasse 111
8903 Birmensdorf 
Switzerland
