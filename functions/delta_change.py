#! /usr/bin/env python

######################################################################
# This script creates delta change based
# high resolution climatologies and bio climatic
# variables for a choosen time period
# author: Dirk N. Karger, dirk.karger@wsl.ch
######################################################################


######################################################################
# Import modules
######################################################################

import saga_api, requests, sys, os, argparse, datetime, os.path, cdsapi, psutil, shutil
from osgeo import gdal
process = psutil.Process(os.getpid())

######################################################################
# Get the command line arguments
######################################################################
ap = argparse.ArgumentParser(
    description='''# This python script creates monthly high-resolution 
    for min-, max-, and mean temperature, and precipitation rate 
    variables from anomalies and using CHELSA V2.1 as 
    baseline high resolution climatology. 
    Dependencies for ubuntu_18.04:
    libwxgtk3.0-dev libtiff5-dev libgdal-dev libproj-dev 
    libexpat-dev wx-common libogdi3.2-dev unixodbc-dev
    g++ libpcre3 libpcre3-dev wget swig-4.0.1 python2.7-dev 
    software-properties-common gdal-bin python-gdal 
    python2.7-gdal libnetcdf-dev libgdal-dev
    python-pip cdsapi saga_gis-7.6.0
    All dependencies are resolved in the chelsa_V2.1.cont singularity container
    Tested with: singularity version 3.3.0-809.g78ec427cc
    ''',
    epilog='''author: Dirk N. Karger, dirk.karger@wsl.ch, Version 2.1'''
)
######################################################################
# Parse Arguemnts
######################################################################
debugging = 0 #turn local debugging on/off
if debugging == 1:
    source1     = 'GFDL-ESM4'
    table1      = 'Amon'
    activity1   = 'ScenarioMIP'
    ssp1        = 'ssp585'
    member1     = 'r1i1p1f1'
    refps       = '1981-01-01'
    refpe       = '2010-12-31'
    fefps       = '2041-01-01'
    fefpe       = '2070-12-31'
    tmp = '/home/karger/scratch/'
    ymin = 46.0
    ymax = 47.5
    xmin = 5.3
    xmax = 10.4
    outpath = tmp

if debugging != 1:
    ap.add_argument('-s','--source', type=str, help="Source model (GCM), e.g. GFDL-ESM4, string")
    ap.add_argument('-t','--table', type=str, help="table id, e.g. Amon, string")
    ap.add_argument('-a','--activity', type=str,  help="activity id, e.g. ScenarioMIP, string")
    ap.add_argument('-e','--experiment', type=str, help="experiment id, e.g. ssp585, string")
    ap.add_argument('-m','--member', type=str,  help="ensemble member, e.g. r1i1p1f1, string")
    ap.add_argument('-rs','--refps', type=str, help="reference period start, e.g. 1981-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-re','--refpe', type=str, help="reference period end, e.g. 2010-12-31, date format YYYY-MM-DD, string")
    ap.add_argument('-fs','--fefps', type=str, help="anomaly period start, e.g. 2041-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-fe','--fefpe', type=str, help="anomaly period end, e.g. 2070-01-01, date format YYYY-MM-DD, string")
    ap.add_argument('-tm','--tmp', type=str, help="directory for temporary files, string")
    ap.add_argument('-op','--outpath', type=str, help="directory for output files, string")
    ap.add_argument('-xm', '--xmin', type=float, help="western boundary of the extent, WGS84 lat. lon., float")
    ap.add_argument('-xx', '--xmax', type=float, help="eastern boundary of the extent, WGS84 lat. lon., float")
    ap.add_argument('-ym', '--ymin', type=float, help="southern boundary of the extent, WGS84 lat. lon., float")
    ap.add_argument('-yx', '--ymax', type=float, help="northern boundary of the extent, WGS84 lat. lon., float")
    args = ap.parse_args()
    print(args)
    source1   = args.source
    table1    = args.table
    activity1 = args.activity
    ssp1      = args.experiment
    member1   = args.member
    refps     = args.refps
    refpe     = args.refpe
    fefps     = args.fefps
    fefpe     = args.fefpe
    tmp       = args.tmp
    outpath   = args.outpath
    ymin = args.ymin
    ymax = args.ymax
    xmin = args.xmin
    xmax = args.xmax

######################################################################
# Define Functions
######################################################################

def Load_Tool_Libraries(Verbose):
    saga_api.SG_UI_Msg_Lock(True)
    if os.name == 'nt':    # Windows
        os.environ['PATH'] = os.environ['PATH'] + ';' + os.environ['SAGA_32'] + '/dll'
        saga_api.SG_Get_Tool_Library_Manager().Add_Directory(os.environ['SAGA_32' ] + '/tools', False)
    else:                  # Linux
        saga_api.SG_Get_Tool_Library_Manager().Add_Directory('/usr/local/lib/saga/', False)        # Or set the Tool directory like this!
    saga_api.SG_UI_Msg_Lock(False)
    if Verbose == True:
                print 'Python - Version ' + sys.version
                print saga_api.SAGA_API_Get_Version()
                print 'number of loaded libraries: ' + str(saga_api.SG_Get_Tool_Library_Manager().Get_Count())
                print
    return saga_api.SG_Get_Tool_Library_Manager().Get_Count()

def load_sagadata(path_to_sagadata):
    saga_api.SG_Set_History_Depth(0)    # History will not be created
    saga_api_dataobject = 0             # initial value
    # CSG_Grid -> Grid
    if any(s in path_to_sagadata for s in (".sgrd", ".sg-grd", "sg-grd-z")):
        saga_api_dataobject = saga_api.SG_Get_Data_Manager().Add_Grid(unicode(path_to_sagadata))
    # CSG_Grids -> Grid Collection
    if any(s in path_to_sagadata for s in ("sg-gds", "sg-gds-z")):
        saga_api_dataobject = saga_api.SG_Get_Data_Manager().Add_Grids(unicode(path_to_sagadata))
    # CSG_Table -> Table
    if any(s in path_to_sagadata for s in (".txt", ".csv", ".dbf")):
        saga_api_dataobject = saga_api.SG_Get_Data_Manager().Add_Table(unicode(path_to_sagadata))
    # CSG_Shapes -> Shapefile
    if '.shp' in path_to_sagadata:
        saga_api_dataobject = saga_api.SG_Get_Data_Manager().Add_Shapes(unicode(path_to_sagadata))
    # CSG_PointCloud -> Point Cloud
    if any(s in path_to_sagadata for s in (".spc", ".sg-pts", ".sg-pts-z")):
        saga_api_dataobject = saga_api.SG_Get_Data_Manager().Add_PointCloud(unicode(path_to_sagadata))
    if saga_api_dataobject == None or saga_api_dataobject.is_Valid() == 0:
        print 'ERROR: loading [' + path_to_sagadata + ']'
        return 0
    print 'File: [' + path_to_sagadata + '] has been loaded'
    return saga_api_dataobject

def import_ncdf(ncdffile):
    #_____________________________________
    # Create a new instance of tool 'Import NetCDF'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('io_gdal', '6')
    if Tool == None:
        print 'Failed to create tool: Import NetCDF'
        return False
    Parm = Tool.Get_Parameters()
    Parm('FILE').Set_Value(ncdffile)
    Parm('SAVE_FILE').Set_Value(False)
    Parm('SAVE_PATH').Set_Value('')
    Parm('TRANSFORM').Set_Value(True)
    Parm('RESAMPLING').Set_Value('Nearest Neighbour')
    print 'Executing tool: ' + Tool.Get_Name().c_str()
    if Tool.Execute() == False:
        print 'failed'
        return False
    print 'okay'
    #_____________________________________
    output = Tool.Get_Parameter(saga_api.CSG_String('GRIDS')).asGridList()
    return output

def change_latlong360(obj,direction):
    #_____________________________________
    # Create a new instance of tool 'Change Longitudinal Range for Grids'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('pj_proj4', '13')
    if Tool == None:
        print('Failed to create tool: Change Longitudinal Range for Grids')
        return False

    Tool.Get_Parameters().Reset_Grid_System()

    Tool.Get_Parameter('INPUT').asList().Add_Item(obj.asGrid())
    Tool.Set_Parameter('DIRECTION', direction)
    Tool.Set_Parameter('PATCH', True)

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')

    List = Tool.Get_Parameter(saga_api.CSG_String('OUTPUT')).asGridList().Get_Grid(0)

    return List

def set_2_latlong(obj):
    #_____________________________________
    # Create a new instance of tool 'Set Coordinate Reference System'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('pj_proj4', '0')
    if Tool == None:
        print('Failed to create tool: Set Coordinate Reference System')
        return False

    Tool.Set_Parameter('CRS_METHOS', 0)
    Tool.Set_Parameter('CRS_PROJ4', '+proj=longlat +datum=WGS84 +no_defs ')
    Tool.Set_Parameter('CRS_FILE', '')
    Tool.Set_Parameter('CRS_EPSG', 4326)
    Tool.Set_Parameter('CRS_EPSG_AUTH', 'EPSG')
    Tool.Set_Parameter('PRECISE', False)
    Tool.Get_Parameter('GRIDS').asList().Add_Item(obj.asGrid())

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')

    return True

def gridvalues_to_points(obj):
    #_____________________________________
    # Create a new instance of tool 'Grid Values to Points'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('shapes_grid', '3')
    if Tool == None:
        print('Failed to create tool: Grid Values to Points')
        return False

    Tool.Get_Parameters().Reset_Grid_System()

    Tool.Get_Parameter('GRIDS').asList().Add_Item(obj.asGrid())
    Tool.Set_Parameter('POLYGONS', 'Shapes input, optional')
    Tool.Set_Parameter('NODATA', True)
    Tool.Set_Parameter('TYPE', 'nodes')

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')

    Data = Tool.Get_Parameter(saga_api.CSG_String('SHAPES')).asShapes()

    return Data

def multilevel_B_spline(shape, template):
    #_____________________________________
    # Create a new instance of tool 'Multilevel B-Spline'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('grid_spline', '4')
    if Tool == None:
        print('Failed to create tool: Multilevel B-Spline')
        return False

    Tool.Set_Parameter('SHAPES', shape)
    Tool.Set_Parameter('FIELD', 4)
    Tool.Set_Parameter('TARGET_DEFINITION', 'user defined')
    Tool.Set_Parameter('TARGET_USER_SIZE', template.Get_Cellsize())
    Tool.Set_Parameter('TARGET_USER_XMIN', template.Get_XMin())
    Tool.Set_Parameter('TARGET_USER_XMAX', template.Get_XMax())
    Tool.Set_Parameter('TARGET_USER_YMIN', template.Get_YMin())
    Tool.Set_Parameter('TARGET_USER_YMAX', template.Get_YMax())
    Tool.Set_Parameter('TARGET_USER_COLS', template.Get_NX())
    Tool.Set_Parameter('TARGET_USER_ROWS', template.Get_NY())
    Tool.Set_Parameter('TARGET_USER_FITS', 'nodes')
    Tool.Set_Parameter('METHOD', 'no')
    Tool.Set_Parameter('EPSILON', 0.000100)
    Tool.Set_Parameter('LEVEL_MAX', 14)

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')

    Parm = Tool.Get_Parameters()
    Data  = Parm('TARGET_OUT_GRID').asGrid()

    return Data

def export_geotiff(obj,outputfile):
    #_____________________________________
    # Create a new instance of tool 'Export GeoTIFF'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('io_gdal', '2')
    if Tool == None:
        print 'Failed to create tool: Export GeoTIFF'
        return False

    Parm = Tool.Get_Parameters()
    Parm.Reset_Grid_System()
    Parm('GRIDS').asList().Add_Item(obj)
    Parm('FILE').Set_Value(outputfile)
    Parm('OPTIONS').Set_Value('COMPRESS=DEFLATE PREDICTOR=2')

    print 'Executing tool: ' + Tool.Get_Name().c_str()
    if Tool.Execute() == False:
        print 'failed'
        return False
    print 'okay - geotiff created'

    #_____________________________________
    # remove this tool instance, if you don't need it anymore
    saga_api.SG_Get_Tool_Library_Manager().Delete_Tool(Tool)

    return True

def grid_calculatorX(obj1,xobj2,equ):
    #_____________________________________
    # Create a new instance of tool 'Grid Calculator'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('grid_calculus', '1')
    if Tool == None:
        print('Failed to create tool: Grid Calculator')
        return False

    Tool.Get_Parameters().Reset_Grid_System()

    Tool.Set_Parameter('RESAMPLING', 'B-Spline Interpolation')
    Tool.Set_Parameter('FORMULA', equ)
    Tool.Set_Parameter('NAME', 'Calculation')
    Tool.Set_Parameter('FNAME', False)
    Tool.Set_Parameter('USE_NODATA', False)
    Tool.Set_Parameter('TYPE', 7)
    Tool.Get_Parameter('GRIDS').asList().Add_Item(obj1.asGrid())
    Tool.Get_Parameter('XGRIDS').asList().Add_Item(xobj2.asGrid())

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')

    Data = Tool.Get_Parameter('RESULT').asGrid()

    return Data

def clip_grid(obj,xmin,xmax,ymin,ymax):
    #_____________________________________
    # Create a new instance of tool 'Clip Grids'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('grid_tools', '31')
    if Tool == None:
        print('Failed to create tool: Clip Grids')
        return False

    Tool.Get_Parameters().Reset_Grid_System()

    Tool.Get_Parameter('GRIDS').asList().Add_Item(obj.asGrid())
    Tool.Set_Parameter('EXTENT', 0)
    #Tool.Set_Parameter('GRIDSYSTEM', saga_api.CSG_Grid_System(0.000000, 0.000000, 0.000000, 0, 0))
    Tool.Set_Parameter('INTERIOR', False)
    Tool.Set_Parameter('XMIN', xmin)
    Tool.Set_Parameter('XMAX', xmax)
    Tool.Set_Parameter('YMIN', ymin)
    Tool.Set_Parameter('YMAX', ymax)
    Tool.Set_Parameter('BUFFER', 0.000000)

    print('Executing tool: ' + Tool.Get_Name().c_str())
    if Tool.Execute() == False:
        print('failed')
        return False
    print('okay')
    res = Tool.Get_Parameter(saga_api.CSG_String('CLIPPED')).asGridList()
    #res = Tool.Get_Parameter('CLIPPED').asList.asGrid()
    return res

def import_gdal(File):
    #_____________________________________
    # Create a new instance of tool 'Import Raster'
    Tool = saga_api.SG_Get_Tool_Library_Manager().Create_Tool('io_gdal', '0')
    if Tool == None:
        print 'Failed to create tool: Import Raster'
        return False

    Parm = Tool.Get_Parameters()
    Parm('FILES').Set_Value(File)
    Parm('MULTIPLE').Set_Value('automatic')
    Parm('TRANSFORM').Set_Value(False)
    Parm('RESAMPLING').Set_Value('Nearest Neighbour')

    print 'Executing tool: ' + Tool.Get_Name().c_str()
    if Tool.Execute() == False:
        print 'failed'
        return False
    print 'okay'

    #_____________________________________
    output = Tool.Get_Parameter(saga_api.CSG_String('GRIDS')).asGridList().Get_Grid(0)
    # _____________________________________

    return output

######################################################################
# Script
######################################################################

if __name__ == '__main__':
    saga_api.SG_Get_Data_Manager().Delete_All()  # make sure the data manager is empty
    Load_Tool_Libraries(True)
    vars = ['tas' , 'tasmax' , 'tasmin' , 'pr']
    dicto = {}
    for var in vars:
        for n in range(2,14):
            month=n-1
            ano = import_ncdf(tmp + var + 'ano_tmp.nc')
            ano_n = ano.asGridList().Get_Grid(n)
            ano_3 = change_latlong360(ano_n,0)
            ano_p = gridvalues_to_points(ano_3)
            url = 'https://envicloud.os.zhdk.cloud.switch.ch/chelsa/chelsa_V2/GLOBAL/climatologies/1981-2010/'+var+'/CHELSA_'+var+'_'+'%02d' % (month,)+'_1981-2010_V.2.1.tif'
            chfiles = requests.get(url, allow_redirects=True)
            open(tmp + 'tmp1.tif', 'wb').write(chfiles.content)
            g1 = import_gdal(tmp+'tmp1.tif')
            g1c = clip_grid(g1,xmin,xmax,ymin,ymax)
            # delta change method
            if var == 'tas' or var == 'tasmax' or var == 'tasmin':
                bias = multilevel_B_spline(ano_p,g1c.Get_Grid(0))
                bcor = grid_calculatorX(g1c.Get_Grid(0), bias, 'a-b')
            if var == 'pr':
                bias = multilevel_B_spline(ano_p, g1c.Get_Grid(0))
                bcor = grid_calculatorX(g1c.Get_Grid(0), bias, 'a/b')
            name1 = outpath + 'CHELSA_CMIP6_' + activity1 + '_' + ssp1 + '_' + member1 + '_' + table1 + '_' + var +'_' + '%02d' % (month,) + '_' + fefps + '_' + fefpe +  '.tif'
            export_geotiff(bcor,name1)
            dicto["grid{0}".format(n)] = bcor
            os.remove(tmp + 'tmp1.tif')
            saga_api.SG_Get_Data_Manager().Delete_All()














