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


import numpy as np
import xarray as xr
import pandas as pd
import gcsfs
import datetime
import fsspec
from dask.diagnostics import ProgressBar
from chelsa_cmip6.BioClim import BioClim
from pyesgf.search import SearchConnection
from siphon.catalog import TDSCatalog

def _get_esgf(activity_id, table_id, variable_id, experiment_id,
               source_id, member_id, frequency_id='mon', node='https://esgf.ceda.ac.uk/esg-search'):
    """
    Get CMIP model from ESGF via lazy loading.

    :param activity_id: the activity_id according to CMIP6
    :param table_id: the table id according to CMIP6
    :param experiment_id: the experiment_id according to CMIP6
    :param instituion_id: the instituion_id according to CMIP6
    :param source_id: the source_id according to CMIP6
    :param member_id: the member_id according to CMIP6
    :param frequency_id: the freqency_id according to CMIP6
    :param node: ESGF search node, default: https://esgf.ceda.ac.uk/esg-search

    :return: xarray dataset
    :rtype: xarray
    """
    conn = SearchConnection(node,
                            distrib=True)

    ctx = conn.new_context(
        project=activity_id,
        source_id=source_id,
        table_id=table_id,
        experiment_id=experiment_id,
        variable=variable_id,
        variant_label=member_id,
        frequency=frequency_id)

    result = ctx.search()[0]
    files = result.file_context().search()

    ff = []
    for file in files:
        print(file.opendap_url)
        ff.append(file.opendap_url)

    ds = xr.open_mfdataset(ff, combine='nested', concat_dim='time')

    try:
        ds['time'] = np.sort(ds['time'].values)
    except Exception:
        pass

    return ds


def _get_cmip(activity_id, table_id, variable_id, experiment_id, instituion_id, source_id, member_id):
    """
    Get CMIP model from Google Cloud storage via lazy loading.

    :param activity_id: the activity_id according to CMIP6
    :param table_id: the table id according to CMIP6
    :param experiment_id: the experiment_id according to CMIP6
    :param instituion_id: the instituion_id according to CMIP6
    :param source_id: the source_id according to CMIP6
    :param member_id: the member_id according to CMIP6

    :return: xarray dataset
    :rtype: xarray
    """
    gcs = gcsfs.GCSFileSystem(token='anon')
    df = pd.read_csv('https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv')
    search_string = "activity_id == '" + activity_id + "' & table_id == '" + table_id + "' & variable_id == '" + variable_id + "' & experiment_id == '" + experiment_id + "' & institution_id == '" + instituion_id + "' & source_id == '" + source_id + "' & member_id == '" + member_id + "'"
    df_ta = df.query(search_string)
    # get the path to a specific zarr store (the first one from the dataframe above)
    zstore = df_ta.zstore.values[-1]
    # create a mutable-mapping-style interface to the store
    mapper = gcs.get_mapper(zstore)
    # open it using xarray and zarr
    ds = xr.open_zarr(mapper, consolidated=True)
    try:
        ds['time'] = np.sort(ds['time'].values)
    except Exception:
        pass

    return ds



def _get_cordex(activity_id, region, variable_id, experiment_id,
                instituion_id, source_id, downscaling_id, member_id, version, table_id='day'):
    """
    Get CORDEX model from hub.climate4r.ifca.es via lazy loading.

    :param activity_id: the activity_id according to CMIP6
    :param region: the cordex region, e.g. AFR-22
    :param experiment_id: the experiment_id
    :param instituion_id: the instituion_id
    :param source_id: the source_id
    :param downscaling_id: downscaling model
    :param member_id: the member_id
    :param verion: the version
    :param table_id: the table id

    :return: xarray dataset
    :rtype: xarray
    """

    cat_url = ('https://hub.climate4r.ifca.es/thredds/catalog/files/ESGF/interp025/' + activity_id + '/output/' +
               region + '/' + instituion_id + '/' + source_id + '/' + experiment_id + '/' + member_id + '/' +
               downscaling_id + '/v1/' + table_id + '/' + variable_id + '/' + version + '/catalog.xml')

    cat = TDSCatalog(cat_url)
    ff = []
    for i in range(0, len(cat.datasets)):
        access_urls_l = cat.datasets[i].access_urls
        print(access_urls_l['OpenDAP'])
        ff.append(access_urls_l['OpenDAP'])

    ds = xr.open_mfdataset(ff, combine='nested', concat_dim='time')
    ds = ds.resample(time="MS").mean()

    try:
        ds['time'] = np.sort(ds['time'].values)
    except Exception:
        pass

    return ds


class interpol:
    """
    Spatial interpolation class for xarray datasets
    
    :param ds: an xarray dataset
    :param template: a xarray dataset with the target resolution
    :return: a spatially, to the resoluton of the template, interpolated xarray
    :rtype: xarray
    """
    def __init__(self, ds, template):
        self.ds = ds
        self.template = template

    def interpolate(self):
        res = self.ds.interp(lat=self.template["lat"], lon=self.template["lon"])
        return res


class chelsaV2:
    """ 
    Class to download and clip data from the CHELSA V2.1 normals (climatologies)
    for a specific bounding box delimited by minimum and maximum latitude and longitude
    
    :param xmin: Minimum longitude [Decimal degree]
    :param xmax: Maximum longitude [Decimal degree]
    :param ymin: Minimum latitude [Decimal degree]
    :param ymax: Maximum latitude [Decimal degree]
    :param variable_id: id of the variable that needs to be downloaded (e.g. 'tas')

    """
    def __init__(self, xmin, xmax, ymin, ymax, variable_id):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.variable_id = variable_id

    def _crop_ds_(self, ds):
        """
        clip xarray
        
        :param ds: a xarray to_dataset
        :return: clipped xarray
        :rtype: xarray
        """
        mask_lon = (ds.lon >= self.xmin) & (ds.lon <= self.xmax)
        mask_lat = (ds.lat >= self.ymin) & (ds.lat <= self.ymax)
        cropped_ds = ds.where(mask_lon & mask_lat, drop=True)
        return cropped_ds

    def get_chelsa(self):
        """
        download chelsa
        
        :return: cropped xarray
        :rtype: xarray
        """

        a = []
        for month in range(1, 13):
            url = 'https://os.zhdk.cloud.switch.ch/envicloud/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/ncdf/CHELSA_' + self.variable_id + '_' + '%02d' % (
                month,) + '_1981-2010_V.2.1.nc'
            with fsspec.open(url) as fobj:
                ds = xr.open_dataset(fobj).chunk({'lat': 500, 'lon': 500})
                ds = self._crop_ds_(ds)
                ds.load()
            a.append(ds)

        ds = xr.concat([i for i in a], 'time')

        #ds = self._crop_ds_(xr.concat([i for i in a], 'time'))

        # old version using rasterio
        #a = []
        #for month in range(1, 13):
        #    url = 'https://envicloud.os.zhdk.cloud.switch.ch/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/' + self.variable_id + '/CHELSA_' + self.variable_id + '_' + '%02d' % (month,) + '_1981-2010_V.2.1.tif'
        #    a.append(url)

        #ds = self._crop_ds_(xr.concat([xr.open_rasterio(i) for i in a], 'time'))
        if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
            res = ds.assign(Band1=ds['Band1'] * 0.1)
        if self.variable_id == 'pr':
            res = ds.assign(Band1=ds['Band1'] * 0.01)

        return res


class cmip6_clim:
    """ 
    Climatology class for monthly climatologies for CMIP6 data 
    
    :param activity_id: the activity_id according to CMIP6
    :param table_id: the table id according to CMIP6
    :param experiment_id: the experiment_id according to CMIP6
    :param instituion_id: the instituion_id according to CMIP6
    :param source_id: the source_id according to CMIP6
    :param member_id: the member_id according to CMIP6
    :param ref_startdate: Starting date of the reference_period
    :param ref_enddate: End date of the reference_period
    :param fut_startdate: Start date of the future future_period
    :param fut_enddate: End date of the future_period
    :param use_esgf: Use ESGF node instead of Pangeo
    :param downscaling_id: downscaling model, only used for CORDEX
    :param region: region id, only used for CORDEX
    :param verions: version, only used for CORDEX
    """
    def __init__(self, activity_id, table_id,
                 variable_id, experiment_id,
                 institution_id, source_id,
                 member_id, ref_startdate,
                 ref_enddate, fut_startdate,
                 fut_enddate, use_esgf, downscaling_id=None, region=False, version=None):
        self.activity_id = activity_id
        self.table_id = table_id
        self.variable_id = variable_id
        self.experiment_id = experiment_id
        self.institution_id = institution_id
        self.source_id = source_id
        self.member_id = member_id
        self.refps = ref_startdate
        self.refpe = ref_enddate
        self.fefps = fut_startdate
        self.fefpe = fut_enddate
        self.downscaling_id = downscaling_id
        self.region = region
        self.version = version
        if region:
            self.future_period = _get_cordex(activity_id='CORDEX',
                                             region=self.region,
                                             variable_id=self.variable_id,
                                             experiment_id=self.experiment_id,
                                             instituion_id=self.institution_id,
                                             source_id=self.source_id,
                                             downscaling_id=self.downscaling_id,
                                             member_id=self.member_id,
                                             version=self.version).sel(time=slice(self.fefps, self.fefpe)).groupby("time.month").mean("time")
        if use_esgf:
            self.future_period = _get_esgf('CMIP6',
                                           self.table_id,
                                           self.variable_id,
                                           self.experiment_id,
                                           self.source_id,
                                           self.member_id).sel(time=slice(self.fefps, self.fefpe)).groupby("time.month").mean("time")
        else:
            self.future_period = _get_cmip(self.activity_id,
                                           self.table_id,
                                           self.variable_id,
                                           self.experiment_id,
                                           self.institution_id,
                                           self.source_id,
                                           self.member_id).sel(time=slice(self.fefps, self.fefpe)).groupby("time.month").mean("time")
        #print("future data loaded... ")
        if region:
            self.historical_period = _get_cordex(activity_id='CORDEX',
                                             region=self.region,
                                             variable_id=self.variable_id,
                                             experiment_id=self.experiment_id,
                                             instituion_id=self.institution_id,
                                             source_id=self.source_id,
                                             downscaling_id=self.downscaling_id,
                                             member_id=self.member_id,
                                             version=self.version).sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        if use_esgf:
            self.historical_period = _get_esgf('CMIP6',
                                               self.table_id,
                                               self.variable_id,
                                               'historical',
                                               self.source_id,
                                               self.member_id).sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        else:
            self.historical_period = _get_cmip('CMIP',
                                               self.table_id,
                                               self.variable_id,
                                               'historical',
                                               self.institution_id,
                                               self.source_id,
                                               self.member_id).sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        #print("historical period set... ")
        if region:
            self.reference_period = _get_cordex(activity_id='CORDEX',
                                             region=self.region,
                                             variable_id=self.variable_id,
                                             experiment_id=self.experiment_id,
                                             instituion_id=self.institution_id,
                                             source_id=self.source_id,
                                             downscaling_id=self.downscaling_id,
                                             member_id=self.member_id,
                                             version=self.version).sel(time=slice('1981-01-15', '2010-12-15')).groupby("time.month").mean("time")
        if use_esgf:
            self.reference_period = _get_esgf('CMIP6',
                                              self.table_id,
                                              self.variable_id,
                                              'historical',
                                              self.source_id,
                                              self.member_id).sel(time=slice('1981-01-15', '2010-12-15')).groupby("time.month").mean("time")
        else:
            self.reference_period = _get_cmip('CMIP',
                                              self.table_id,
                                              self.variable_id,
                                              'historical',
                                              self.institution_id,
                                              self.source_id,
                                              self.member_id).sel(time=slice('1981-01-15', '2010-12-15')).groupby("time.month").mean("time")
        #print("reference period set... done")

    def get_anomaly(self, period):
        """
        Get climatological anomaly between the reference and future future_period

        :param period:  either future (futr) or historical (hist)
        :return: anomaly
        :rtype: xarray
        """
        if period == 'futr':
            if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
                res = self.future_period - self.reference_period # additive anomaly
            if self.variable_id == 'pr':
                res = (self.future_period * 86400 + 0.01) / (self.reference_period * 86400 + 0.01)   # multiplicative anomaly

        if period == 'hist':
            if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
                res = self.historical_period - self.reference_period # additive anomaly
            if self.variable_id == 'pr':
                res = (self.historical_period * 86400 + 0.01) / (self.reference_period * 86400 + 0.01)   # multiplicative anomaly

        res1 = res.assign_coords(lon=(((res.lon + 180) % 360) - 180)).sortby('lon') #res1 = res.assign_coords({"lon": (((res.lon) % 360) - 180)}) #bugfix
        return res1


class ChelsaClimat:
    """
    Chelsa data class containing the clipped CHELSA V2.1 climatological normals
    
    :param xmin: Minimum longitude [Decimal degree]
    :param xmax: Maximum longitude [Decimal degree]
    :param ymin: Minimum latitude [Decimal degree]
    :param ymax: Maximum latitude [Decimal degree]
    """
    def __init__(self, xmin, xmax, ymin, ymax):
        for var in ['pr', 'tas', 'tasmax', 'tasmin']:
            print("getting variable: " + var)
            setattr(self, var, chelsaV2(xmin, xmax, ymin, ymax, var).get_chelsa())


class CmipClimat:
    """ 
    Climatology data class for monthly cmip 6 climatological normals
    
    :param activity_id: the activity_id according to CMIP6
    :param table_id: the table id according to CMIP6
    :param experiment_id: the experiment_id according to CMIP6
    :param instituion_id: the instituion_id according to CMIP6
    :param source_id: the source_id according to CMIP6
    :param member_id: the member_id according to CMIP6
    :param ref_startdate: Starting date of the reference_period
    :param ref_enddate: End date of the reference_period
    :param fut_startdate: Start date of the future future_period
    :param fut_enddate: End date of the future_period
    :param use_esgf: Use ESGF node instead of Pangeo
    :param region: cordex region, only used for CORDEX
    :param downscaling_id: downscaling model, only used for CORDEX
    :param version: version, only used for CORDEX
    """
    def __init__(self, activity_id, table_id,
                 experiment_id,
                 institution_id, source_id,
                 member_id, ref_startdate,
                 ref_enddate, fut_startdate,
                 fut_enddate, use_esgf, region, downscaling_id, version):
        for var in ['pr', 'tas', 'tasmax', 'tasmin']:
            setattr(self, var, cmip6_clim(activity_id, table_id,
                             var, experiment_id,
                             institution_id, source_id,
                             member_id, ref_startdate,
                             ref_enddate, fut_startdate,
                             fut_enddate, use_esgf, region, downscaling_id, version))


class DeltaChangeClim:
    """
    Delta change method class
    
    :param ChelsaClimat: A Chelsa data class containing the clipped CHELSA V2.1 climatological normals 
    :param CmipClimat: A Climatology data class for monthly cmip 6 climatological normals
    :param refps: Starting date of the reference_period
    :param refpe: End date of the reference_period
    :param refps: Start date of the future future_period
    :param fefpe: End date of the future_period
    :param output: bollean: should the output be saved as a file, defaults to False
    """
    def __init__(self, ChelsaClimat, CmipClimat, refps, refpe, fefps, fefpe, output=False):
        self.output = output
        self.refps = refps
        self.refpe = refpe
        self.fefps = fefps
        self.fefpe = fefpe
        self.hist_year = np.mean([int(datetime.datetime.strptime(refps, '%Y-%m-%d').year), 
                                 int(datetime.datetime.strptime(refpe, '%Y-%m-%d').year)]).__round__()
        self.futr_year = np.mean([int(datetime.datetime.strptime(fefps, '%Y-%m-%d').year), 
                                 int(datetime.datetime.strptime(fefpe, '%Y-%m-%d').year)]).__round__()

        for per in ['futr', 'hist']:
            #setattr(self, str(per + '_pr'), getattr(ChelsaClimat, 'pr').to_dataset(name='pr').rename({'time': 'month'}).drop('band') * interpol(
            #        getattr(CmipClimat, 'pr').get_anomaly(per), getattr(ChelsaClimat, 'pr')).interpolate())
            setattr(self, str(per + '_pr'), getattr(ChelsaClimat, 'pr').rename({'time': 'month', 'Band1': 'pr'}) * interpol(
                    getattr(CmipClimat, 'pr').get_anomaly(per), getattr(ChelsaClimat, 'pr')).interpolate())
            for var in ['tas', 'tasmax', 'tasmin']:
                #setattr(self, str(per + '_' + var), getattr(ChelsaClimat, var).to_dataset(name=var).rename({'time': 'month'}).drop('band') + interpol(
                #        getattr(CmipClimat, var).get_anomaly(per), getattr(ChelsaClimat, var)).interpolate())
                setattr(self, str(per + '_' + var), getattr(ChelsaClimat, var).rename({'time': 'month', 'Band1': var}) + interpol(
                        getattr(CmipClimat, var).get_anomaly(per), getattr(ChelsaClimat, var)).interpolate())

        for var in ['tas', 'tasmax', 'tasmin', 'pr']:
            getattr(self, str('futr_' + var))['month'] = [datetime.datetime(self.futr_year, month, 15) for month in getattr(self, str(per + '_' + var))['month'].values]
            getattr(self, str('hist_' + var))['month'] = [datetime.datetime(self.hist_year, month, 15) for month in getattr(self, str(per + '_' + var))['month'].values]

        if output:
            print('saving files to :' + output)
            for var in ['hist_tas', 'hist_tasmax', 'hist_tasmin',
                        'hist_pr']:
                getattr(self, var).to_netcdf(self.output
                                             + 'CHELSA_'
                                             + CmipClimat.tas.institution_id
                                             + '_' + CmipClimat.tas.source_id
                                             + '_' + var.replace('hist_', '')
                                             + '_' + CmipClimat.tas.experiment_id
                                             + '_' + CmipClimat.tas.member_id
                                             + '_' + CmipClimat.tas.refps
                                             + '_' + CmipClimat.tas.refpe
                                             + '.nc')
            for var in ['futr_tas', 'futr_tasmax',
                        'futr_tasmin', 'futr_pr']:
                getattr(self, var).to_netcdf(self.output
                                             + 'CHELSA_'
                                             + CmipClimat.tas.institution_id
                                             + '_' + CmipClimat.tas.source_id
                                             + '_' + var.replace('futr_', '')
                                             + '_' + CmipClimat.tas.experiment_id
                                             + '_' + CmipClimat.tas.member_id
                                             + '_' + CmipClimat.tas.fefps
                                             + '_' + CmipClimat.tas.fefpe
                                             + '.nc')


def chelsa_cmip6(source_id, institution_id, table_id, activity_id, experiment_id, member_id, 
                 refps, refpe, fefps, fefpe, xmin, xmax, ymin, ymax, output, use_esgf=False, region=None,
                 downscaling_id=False, version=None):
    """ 
    Calculate chelsa cmip 6 climatological normals and bioclimatic variables
    
    :param activity_id: the activity_id according to CMIP6
    :param table_id: the table id according to CMIP6
    :param experiment_id: the experiment_id according to CMIP6
    :param instituion_id: the instituion_id according to CMIP6
    :param source_id: the source_id according to CMIP6
    :param member_id: the member_id according to CMIP6
    :param refps: Starting date of the reference_period
    :param refpe: End date of the reference_period
    :param fefps: Start date of the future future_period
    :param fefpe: End date of the future_period
    :param xmin: Minimum longitude [Decimal degree]
    :param xmax: Maximum longitude [Decimal degree]
    :param ymin: Minimum latitude [Decimal degree]
    :param ymax: Maximum latitude [Decimal degree]
    :param output: output directory, string
    :param use_esgf: bollean, Use ESGF node instead of Pangeo, default=False
    :param region: CORDEX region, only used for CORDEX
    :param downscaling_id: downscaling model, only used for CORDEX
    :param version: version id, only used for CORDEX
    """
    print('start downloading CMIP data:')
    with ProgressBar():
        cm_climat = CmipClimat(activity_id, table_id,
                               experiment_id,
                               institution_id, source_id,
                               member_id, refps,
                               refpe, fefps,
                               fefpe, use_esgf, region, downscaling_id, version)

    print('start downloading CHELSA data (depending on your internet speed this might take a while...)')
    ch_climat = ChelsaClimat(xmin, xmax, ymin, ymax)

    print('applying delta change:')
    with ProgressBar():
        dc = DeltaChangeClim(ch_climat, cm_climat, refps,
                             refpe, fefps,
                             fefpe, output)

    print('start building climatologies data:')
    with ProgressBar():
        biohist = BioClim(dc.hist_pr, dc.hist_tas, dc.hist_tasmax, dc.hist_tasmin)
        biofutr = BioClim(dc.futr_pr, dc.futr_tas, dc.futr_tasmax, dc.futr_tasmin)

    print('saving bioclims:')
    for n in range(1, 20):
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, 'bio' + str(n))().to_netcdf(name)

    for n in ['gdd']:
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_'  + str(n) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.refps + '_' + cm_climat.tas.refpe + '.nc'
        getattr(biohist, str(n))().to_netcdf(name)

    for n in range(1, 20):
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str('bio' + str(n)) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, 'bio' + str(n))().to_netcdf(name)

    for n in ['gdd']:
        name = output + 'CHELSA' + '_' + cm_climat.tas.institution_id + '_' \
               + cm_climat.tas.source_id + '_' + str(n) + '_' \
               + cm_climat.tas.experiment_id + '_' + cm_climat.tas.member_id \
               + '_' + cm_climat.tas.fefps + '_' + cm_climat.tas.fefpe + '.nc'
        getattr(biofutr, str(n))().to_netcdf(name)










