#!/usr/bin/env python

import xarray as xr
import numpy as np


class quarter_class:
    """ quarters class for monthly climatologies """
    def __init__(self, array1, array2, agg1, agg2, fun1, fun2):
        self.array1 = array1
        self.array2 = array2
        self.agg1 = agg1 #how should array1 be aggregated
        self.agg2 = agg2 #how should array2 be aggregated
        self.fun1 = fun1 #is the min or the max whats need to be found
        self.fun2 = fun2 #function for comparison

    def _create_quarter_(self, xv, fun1):
        #xv = [11, 20, 30, 104, 95, 96, 75, 85, 90, 190, 181, 172]
        monthv = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]
        b1 = []
        for n in range(0,14):
            b1.append(xv[monthv[n]-1])
        a1 = []
        for m in range(1,12):
            if fun1 == 'sum':
                x0 = np.sum([b1[m-1],b1[m],b1[m+1]])
            if fun1 == 'mean':
                x0 = np.mean([b1[m - 1], b1[m], b1[m + 1]])
            a1.append(x0)
        return a1

    def _comp_quarters_(self, a1, a2): # ,array1, array2, agg1, agg2, fun2
        qart1 = self._create_quarter_(a1, self.agg1)
        qart2 = self._create_quarter_(a2, self.agg2)
        if self.fun2 == 'max':
            a1 = np.max(qart1)
        if self.fun2 == 'min':
            a1 = np.min(qart1)
        a = qart2[qart1.index(a1)]
        return a

    def comp_quarters_array(self):
        """Compare quarters"""
        res_arr = xr.apply_ufunc(self._comp_quarters_,  # function to apply
                                 self.array1, self.array2,  # pass arguments.
                                 input_core_dims=[['month'], ['month']],
                                 vectorize=True,
                                 dask='parallelized',  # let dask handle the parallelization
                                 output_dtypes=[np.float32])  # data type of the output(s)
        return res_arr


class BioClim:
    """ climatology class for monthly climatologies """
    def __init__(self, pr, tas, tasmax, tasmin):
        """ Create a set of baseline clims """
        self.tas = tas #.load() #chunk({month: -1}) #rename({'tas': 'var'})
        self.tasmax = tasmax #.load() #.chunk({month: -1}) #rename({'tasmax': 'var'})
        self.tasmin = tasmin #.load() #.chunk({month: -1}) #rename({'tasmin': 'var'})
        self.pr = pr #.load() #chunk({month: -1}) #rename({'pr': 'var'})

    def _mean_(self, x ):
        s = np.sum(x)
        n = len(x)
        mean = s/n
        return mean

    def _diurnalrange_(self, tasmax, tasmin):
        return np.sum(tasmax - tasmin) / 12

    def _sd_(self, x):
        return np.std(x)

    def _max_(self, x):
        return np.max(x)

    def _min_(self, x):
        return np.min(x)

    def _sum_(self, x):
        return np.sum(x)

    def _cv_(self, x):
        sigma = self._sd_(x)
        mu = self._mean_(x)
        cv = sigma/mu
        return cv

    def _bio7_(self, tasmax, tasmin):
        bio5 = self._max_(tasmax)
        bio6 = self._min_(tasmin)
        bio7 = bio5-bio6
        return bio7

    def bio1(self):
        """Create mean annual temperature"""
        res_arr = xr.apply_ufunc(self._mean_,  # function to apply
                                 self.tas['tas'],  # pass arguments.
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32]) #dask='parallelized',  # let dask handle the parallelization
                                  # data type of the output(s)
        res_arr = res_arr.to_dataset(name='bio1')
        return res_arr

    def bio2(self):
        """Create mean diurnal temperature range"""
        res_arr = xr.apply_ufunc(self._diurnalrange_,
                                 self.tasmax['tasmax'], self.tasmin['tasmin'],
                                 input_core_dims=[['month'], ['month']],
                                 vectorize=True,
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio2')
        return res_arr

    def bio3(self):
        """ Create mean annual temperature"""
        res_arr = xr.apply_ufunc(self._diurnalrange_,
                                 self.tasmax['tasmax'], self.tasmin['tasmin'],
                                 input_core_dims=[['month'], ['month']],
                                 vectorize=True,
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio3')
        return res_arr

    def bio4(self):
        """Temperature Seasonality (Standard Deviation) """
        res_arr = xr.apply_ufunc(self._sd_,
                                 self.tas['tas'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio4')
        return res_arr

    def bio5(self):
        """Max Temperature of Warmest Month"""
        res_arr = xr.apply_ufunc(self._max_,
                                 self.tasmax['tasmax'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio5')
        return res_arr

    def bio6(self):
        """Min Temperature of Coldest Month"""
        res_arr = xr.apply_ufunc(self._min_,
                                 self.tasmax['tasmax'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio6')
        return res_arr

    def bio7(self):
        """Annual Temperature Range"""
        res_arr = xr.apply_ufunc(self._bio7_,
                                 self.tasmax['tasmax'], self.tasmin['tasmin'],
                                 input_core_dims=[['month'], ['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio7')
        return res_arr

    def bio8(self):
        """Mean Temperature of Wettest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.tas['tas'], "sum", "mean", "max", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio8')
        return res_arr

    def bio9(self):
        """Mean Temperature of the driest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.tas['tas'], "sum", "mean", "min", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio9')
        return res_arr

    def bio10(self):
        """Mean Temperature of the warmest Quarter"""
        res_arr = quarter_class(self.tas['tas'], self.tasmax['tasmax'], "mean", "mean", "max", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio10')
        return res_arr

    def bio11(self):
        """Mean Temperature of Wettest Quarter"""
        res_arr = quarter_class(self.tas['tas'], self.tasmin['tasmin'], "mean", "mean", "max", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio11')
        return res_arr

    def bio12(self):
        """Annual Precipitation Sum"""
        res_arr = xr.apply_ufunc(self._sum_,
                                 self.pr['pr'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio12')
        return res_arr

    def bio13(self):
        """Precipitation of wettest month"""
        res_arr = xr.apply_ufunc(self._max_,
                                 self.pr['pr'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio13')
        return res_arr

    def bio14(self):
        """Precipitation of driest month"""
        res_arr = xr.apply_ufunc(self._min_,
                                 self.pr['pr'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio14')
        return res_arr

    def bio15(self):
        """Precipitation Seasonality"""
        res_arr = xr.apply_ufunc(self._cv_,
                                 self.pr['pr'],
                                 input_core_dims=[['month']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        res_arr = res_arr.to_dataset(name='bio15')
        return res_arr

    def bio16(self):
        """Precipitation of Wettest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.pr['pr'], "sum", "sum", "max", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio16')
        return res_arr

    def bio17(self):
        """Precipitation of Driest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.pr['pr'], "sum", "sum", "min", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio17')
        return res_arr

    def bio18(self):
        """Precipitation of Warmest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.tasmax['tasmax'], "sum", "mean", "max", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio18')
        return res_arr

    def bio19(self):
        """Precipitation of Coldest Quarter"""
        res_arr = quarter_class(self.pr['pr'], self.tasmin['tasmin'], "sum", "mean", "min", "max").comp_quarters_array()
        res_arr = res_arr.to_dataset(name='bio19')
        return res_arr

