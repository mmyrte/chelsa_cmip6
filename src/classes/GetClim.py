#!/usr/bin/env python
#from __future__ import print_function
import requests
import xml.etree.ElementTree as ET
import numpy
import xarray as xr
import rasterio


def _esgf_search_(server="https://esgf-node.llnl.gov/esg-search/search",
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


class get_cmip6:
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

    def _calc_anomaly_(self, hist_c, fut_c):
        if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
            res = hist_c - fut_c  # additive anomaly
        if self.variable_id == 'pr':
            res = (hist_c + 0.001) / (fut_c + 0.001)  # multiplicative anomaly
        return res


    def get_cmip(self, x):
        """Get CMIP model from ESGF"""
        result = _esgf_search_(activity_id=self.activity_id,
                               table_id=self.table_id,
                               variable_id=self.variable_id,
                               experiment_id=self.experiment_id,
                               institution_id=self.institution_id,
                               source_id=self.source_id,
                               member_id=self.member_id)
        files_to_open = result
        ds = xr.open_mfdataset(files_to_open, combine='by_coords')
        return ds

    def get_anomaly(self):
        """Get climatological anomaly"""
        sspx = self.get_cmip(self.experiment_id).sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        refp = self.get_cmip('historical').sel(time=slice('1981-01-01', '2010-12-31')).groupby("time.month").mean("time")
        hist = self.get_cmip('historical').sel(time=slice(self.refps, self.refpe)).groupby("time.month").mean("time")
        ano1 = self._calc_anomaly_(hist, refp)
        ano2 = self._calc_anomaly_(sspx, refp)
        if self.variable_id == "tas" or self.variable_id == 'tasmin' or self.variable_id == 'tasmax':
            res = ano1 - ano2  # additive anomaly
        if self.variable_id == 'pr':
            res = (ano1 + 0.001) / (ano2 + 0.001)  # multiplicative anomaly
        return res







cmip = get_cmip6('CMIP', 'Amon',
                 'tas', 'historical',
                 "NCAR", "CESM2",
                 "r10i1p1f1", '1981-01-01',
                 '2010-12-31', '2041-01-01',
                 '2070-12-31')

cmip_ano = cmip.get_anomaly()


ch = chelsaV2(5.3,10.4,46,47.5, 'tas').get_chelsa()

ano_inter = interpol(cmip_ano,ch).interpolate()
ano_inter.load().to_netcdf("/mnt/storage/karger/tas1.nc")


















def get_cmip():
    """Get CMIP model from ESGF"""
    result = _esgf_search_(activity_id='CMIP', table_id='Amon',
                 variable_id='tas', experiment_id='historical',
                 institution_id="NCAR", source_id="CESM2",
                 member_id="r10i1p1f1")
    files_to_open = result
    ds = xr.open_mfdataset(files_to_open, combine='by_coords')
    return ds


result = _esgf_search_(activity_id='CMIP', table_id='Amon',
                     variable_id='tas', experiment_id='historical',
                     institution_id="NCAR", source_id="CESM2",
                     member_id="r10i1p1f1")

files_to_open = result
ds = xr.open_mfdataset(files_to_open, combine='by_coords')





    variable_id = 'tas'
    def get_chelsa():
        a = []
        for month in range(1,13):
            url = 'https://envicloud.os.zhdk.cloud.switch.ch/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/' + variable_id + '/CHELSA_' + variable_id + '_' + '%02d' % (month,) + '_1981-2010_V.2.1.tif'
            a.append(url)

        ds = xr.concat([xr.open_rasterio(i) for i in a],'time')
        return ds




ch = get_chelsa()





