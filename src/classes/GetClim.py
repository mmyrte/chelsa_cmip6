#!/usr/bin/env python
#from __future__ import print_function
import requests
import xml.etree.ElementTree as ET
import numpy as np
import xarray as xr
import rasterio
import pandas as pd
import zarr
import gcsfs


def _esgf_search(server="https://esgf-node.llnl.gov/esg-search/search",
                  files_type="OPENDAP", local_node=True, project="CMIP6",
                  verbose=False, format="application%2Fsolr%2Bjson",
                  use_csrf=False, **search):
    client = requests.session()
    payload = search
    payload["project"] = project
    payload["type"] = "File"
    if local_node:
        payload["distrib"] = "false"
    if use_csrf:
        client.get(server)
        if 'csrftoken' in client.cookies:
            # Django 1.6 and up
            csrftoken = client.cookies['csrftoken']
        else:
            # older versions
            csrftoken = client.cookies['csrf']
        payload["csrfmiddlewaretoken"] = csrftoken
    payload["format"] = format
    offset = 0
    numFound = 10000
    all_files = []
    files_type = files_type.upper()
    while offset < numFound:
        payload["offset"] = offset
        url_keys = []
        for k in payload:
            url_keys += ["{}={}".format(k, payload[k])]

        url = "{}/?{}".format(server, "&".join(url_keys))
        print(url)
        r = client.get(url)
        r.raise_for_status()
        resp = r.json()["response"]
        numFound = int(resp["numFound"])
        resp = resp["docs"]
        offset += len(resp)
        for d in resp:
            if verbose:
                for k in d:
                    print("{}: {}".format(k, d[k]))
            url = d["url"]
            for f in d["url"]:
                sp = f.split("|")
                if sp[-1] == files_type:
                    all_files.append(sp[0].split(".html")[0])
    return sorted(all_files)


def _get_cmip(activity_id, table_id, variable_id, experiment_id, instituion_id, source_id, member_id):
    """Get CMIP model from Google"""
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


class interpol:
    """Interpolation class"""
    def __init__(self, ds, template):
        """ Create a set of baseline clims """
        self.ds = ds
        self.template = template

    def interpolate(self):
        res = self.ds.interp(lat=self.template["y"], lon=self.template["x"])
        return res


class chelsaV2:
    """ get and clip CHELSA climatologies """
    def __init__(self, xmin, xmax, ymin, ymax, variable_id):
        """ Create a set of baseline clims """
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.variable_id = variable_id

    def _crop_ds_(self, ds):
        """clip xarray"""
        mask_lon = (ds.x >= self.xmin) & (ds.x <= self.xmax)
        mask_lat = (ds.y >= self.ymin) & (ds.y <= self.ymax)
        cropped_ds = ds.where(mask_lon & mask_lat, drop=True)
        return cropped_ds

    def get_chelsa(self):
        """download chelsa"""
        a = []
        for month in range(1, 13):
            url = 'https://envicloud.os.zhdk.cloud.switch.ch/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/' + self.variable_id + '/CHELSA_' + self.variable_id + '_' + '%02d' % (
                month,) + '_1981-2010_V.2.1.tif'
            a.append(url)

        ds = self._crop_ds_(xr.concat([xr.open_rasterio(i) for i in a], 'time'))
        if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
            res = ds / 10 - 273.15
        if self.variable_id == 'pr':
            res = ds / 100
        return res


class cmip6_clim:
    """ climatology class for monthly climatologies """
    def __init__(self, activity_id, table_id,
                 variable_id, experiment_id,
                 institution_id, source_id,
                 member_id, ref_startdate,
                 ref_enddate, fut_startdate,
                 fut_enddate):
        """ Create a set of baseline clims """
        self.activity_id = activity_id
        self.table_id = table_id
        self.variable_id = variable_id
        self.experiment_id = experiment_id
        self.institution_id = institution_id
        self.source_id = source_id
        self.member_id = member_id
        self.refps = ref_startdate #'1981-01-01'
        self.refpe = ref_enddate #'2010-12-31'
        self.fefps = fut_startdate #'2041-01-01'
        self.fefpe = fut_enddate #'2070-12-31'
        self.future_period = _get_cmip(self.activity_id, self.table_id, self.variable_id, self.experiment_id, self.institution_id, self.source_id, self.member_id).sel(time=slice(self.fefps, self.fefpe)).groupby("time.month").mean("time")
        print("future data loaded... ")
        #self.historical_data = self.get_cmip('CMIP', self.table_id, self.variable_id, 'historical', self.institution_id, self.member_id)
        print("hist data loaded... ")
        self.historical_period = _get_cmip('CMIP', self.table_id, self.variable_id, 'historical', self.institution_id, self.source_id, self.member_id).sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        print("historical period set... ")
        self.reference_period = _get_cmip('CMIP', self.table_id, self.variable_id, 'historical', self.institution_id, self.source_id, self.member_id).sel(time=slice('1981-01-15', '2010-12-15')).groupby("time.month").mean("time")
        print("reference period set... done")

    def get_anomaly(self):
        """Get climatological anomaly"""
        if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
            res = self.future_period - self.reference_period + self.reference_period - self.historical_period# additive anomaly
        if self.variable_id == 'pr':
            res = (self.future_period + 0.001) / (self.reference_period + 0.001) * (self.reference_period + 0.001) / (self.historical_period + 0.001)  # multiplicative anomaly

        res1 = res.assign_coords({"lon": (((res.lon) % 360) - 180)})
        return res1


class ChelsaClimat:
    """chelsa class"""
    def __init__(self, xmin, xmax, ymin, ymax):
        """ Create a set of baseline clims """
        self.tas = chelsaV2(xmin, xmax, ymin, ymax, 'tas').get_chelsa()
        self.tasmax = chelsaV2(xmin, xmax, ymin, ymax, 'tasmax').get_chelsa()
        self.tasmin = chelsaV2(xmin, xmax, ymin, ymax, 'tasmin').get_chelsa()
        self.pr = chelsaV2(xmin, xmax, ymin, ymax, 'pr').get_chelsa()


class CmipClimat:
    """ climatology class for monthly cmip 6 climatologies """

    def __init__(self, activity_id, table_id,
                 experiment_id,
                 institution_id, source_id,
                 member_id, ref_startdate,
                 ref_enddate, fut_startdate,
                 fut_enddate):
        """ Create a set of baseline clims """
        self.pr =  cmip6_clim(activity_id, table_id,
                             'pr', experiment_id,
                             institution_id, source_id,
                             member_id, ref_startdate,
                             ref_enddate, fut_startdate,
                             fut_enddate)
        self.tas = cmip6_clim(activity_id, table_id,
                             'tas', experiment_id,
                             institution_id, source_id,
                             member_id, ref_startdate,
                             ref_enddate, fut_startdate,
                             fut_enddate)
        self.tasmax = cmip6_clim(activity_id, table_id,
                             'tasmax', experiment_id,
                             institution_id, source_id,
                             member_id, ref_startdate,
                             ref_enddate, fut_startdate,
                             fut_enddate)
        self.tasmin = cmip6_clim(activity_id, table_id,
                             'tasmin', experiment_id,
                             institution_id, source_id,
                             member_id, ref_startdate,
                             ref_enddate, fut_startdate,
                             fut_enddate)


class AnoCorClim:
    """ climatology class for monthly cmip 6 climatologies """

    def __init__(self, chelsa, cmip):
        """ Create delta change climatologies """
        self.chelsa = chelsa
        self.cmip = cmip

        self.tas_ano = self.cmip.tas.get_anomaly()
        self.tasmax_ano = self.cmip.tasmax.get_anomaly()
        self.tasmin_ano = self.cmip.tasmin.get_anomaly()
        self.pr_ano = self.cmip.pr.get_anomaly()

        self.tas_ano_h = interpol(self.tas_ano, self.chelsa.tas).interpolate()
        self.tasmax_ano_h = interpol(self.tasmax_ano, self.chelsa.tasmax).interpolate()
        self.tasmin_ano_h = interpol(self.tasmin_ano, self.chelsa.tasmin).interpolate()
        self.pr_ano_h = interpol(self.pr_ano, self.chelsa.pr).interpolate()

        self.tas = self.chelsa.tas + self.tas_ano_h
        self.tasmax = self.chelsa.tasmax + self.tasmax_ano_h
        self.tasmin = self.chelsa.tasmin + self.tasmin_ano_h
        self.pr = self.chelsa.pr / self.pr_ano_h


delta_clims = AnoCorClim(ch_climat, cmipx)

import matplotlib.pyplot as plt
x1 = delta_clims.chelsa.tas + delta_clims.tas_ano_h.tas


x1.to_netcdf("/mnt/storage/karger/xx1.nc")

delta_clims.chelsa.tas.to_netcdf("/mnt/storage/karger/xx1.nc")
delta_clims.cmip.tas.to_netcdf("/mnt/storage/karger/xy1.nc")








cmipx = CmipClimat('ScenarioMIP', 'Amon',
                 'ssp585',
                 "MPI-M", "MPI-ESM1-2-LR",
                 "r1i1p1f1", '1981-01-15',
                 '2010-12-15', '2041-01-15',
                 '2070-12-15')