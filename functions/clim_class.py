import xarray as xr
import numpy as np

cube_location = '/mnt/storage/karger/W5E5/tasmin_W5E5v1.0_19790101-19801231.nc'

cube = xr.open_dataset(cube_location)  # open dataset
cube = cube.chunk({'time': -1}).transpose('time', ...)  # type: xr.DataSet

def fcn_of_desire(var1):
    # note that in this example var1, var2 are of type ndarray(time, )
    # the fuction must return a ndarray of shape ndarray(time, )
    # perform an arbitary function on the arrays
    # make sure to return a ndarray of shape (time, )
    return np.sum(var1)

variables = [cube['air_temperature_2m'], cube['radiation_era5']]  # DataArrays of shape (time, lat, lon)

res_arr = xr.apply_ufunc(fcn_of_desire,  # function to apply
                         cube['tasmin'],  # pass arguments.
                         input_core_dims=[['time']],
                         # the core dimensions* needed to apply the funciton, in other words, the dimensions we apply the function across
                         #output_core_dims=[['time']],  # the core dimensions* that will come out
                         vectorize=True,
                         # vectorize the function: https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html
                         dask='parallelized',  # let dask handle the parallelization
                         output_dtypes=[np.float32])  # data type of the output(s)

res_arr.to_netcdf("/mnt/storage/karger/scratch/testi.nc") #save to ncdf in tmp

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
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',  # let dask handle the parallelization
                                 output_dtypes=[np.float32])  # data type of the output(s)
        return res_arr



c2=quarter_class(c1.tas, c1.tas, "mean", "sum", "max", "max")



class clim_class:
    """ climatology class for monthly climatologies """
    def __init__(self, pr, tas, tasmax, tasmin):
        """ Create a set of baseline clims """
        self.tas = tas
        self.tasmax = tasmax
        self.tasmin = tasmin
        self.pr = pr
    def _mean_(self, x ):
        s = np.sum(x)
        n = len(x)
        mean = s/n
        return mean
    def _diurnalrange_(self, tasmax, tasmin):
        return np.sum(self.tasmin-self.tasmax)/np.bincount(self.tasmin)
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
                                 self.tas,  # pass arguments.
                                 input_core_dims=[['time']],
                                 vectorize=True,
                                 dask='parallelized',  # let dask handle the parallelization
                                 output_dtypes=[np.float32])  # data type of the output(s)
        return res_arr
    def bio2(self):
        """Create mean diurnal temperature range"""
        res_arr = xr.apply_ufunc(self._diurnalrange_,
                                 self.tasmax, self.tasmin,
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio3(self):
        """ Create mean annual temperature"""
        res_arr = xr.apply_ufunc(self._diurnalrange_,
                                 self.tasmax, self.tasmin,
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio4(self):
        """Temperature Seasonality (Standard Deviation) """
        res_arr = xr.apply_ufunc(self._sd_,
                                 self.tas,
                                 input_core_dims=[['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio5(self):
        """Max Temperature of Warmest Month"""
        res_arr = xr.apply_ufunc(self._max_,
                                 self.tasmax,
                                 input_core_dims=[['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio6(self):
        """Min Temperature of Coldest Month"""
        res_arr = xr.apply_ufunc(self._min_,
                                 self.tasmax,
                                 input_core_dims=[['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio7(self):
        """Annual Temperature Range"""
        res_arr = xr.apply_ufunc(self._bio7_,
                                 self.tasmax, self.tasmin,
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio12(self):
        """Annual Precipitation Sum"""
        res_arr = xr.apply_ufunc(self._sum_,
                                 self.pr,
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr
    def bio15(self):
        """Precipitation Seasonality"""
        res_arr = xr.apply_ufunc(self._sum_,
                                 self.pr,
                                 input_core_dims=[['time'], ['time']],
                                 vectorize=True,
                                 dask='parallelized',
                                 output_dtypes=[np.float32])
        return res_arr


c1 = clim_class(cube['tasmin'],cube['tasmin'],cube['tasmin'],cube['tasmin'])



def _create_quarter_(xv, fun):
    # xv = [11, 20, 30, 104, 95, 96, 75, 85, 90, 190, 181, 172]
    monthv = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]
    b1 = []
    for n in range(0, 14):
        b1.append(xv[monthv[n] - 1])
    a1 = []
    for m in range(1, 12):
        if fun == 'sum':
            x0 = np.sum([b1[m - 1], b1[m], b1[m + 1]])
        if fun == 'mean':
            x0 = np.mean([b1[m - 1], b1[m], b1[m + 1]])
        a1.append(x0)
    return a1


def _comp_quarters_(self, array1, array2, agg1, agg2, fun):
qart1 = _create_quarter_(array1, agg1)
qart2 = _create_quarter_(array2, agg2)
    if fun == 'max':
        a1 = np.max(qart1)
    if fun == 'min':
        a1 = np.min(qart1)
    a = qart2[qart1.index(a1)]
    return a