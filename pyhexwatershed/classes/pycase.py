import os, stat
from abc import ABCMeta, abstractmethod
import datetime
import json
from shutil import copy2
import subprocess

from json import JSONEncoder

from pathlib import Path
from osgeo import gdal, ogr, osr, gdalconst
import numpy as np

from pyflowline.classes.pycase import flowlinecase
from pyflowline.pyflowline_read_model_configuration_file import pyflowline_read_model_configuration_file

from pyhexwatershed.algorithm.auxiliary.gdal_function import obtain_raster_metadata_geotiff, reproject_coordinates

pDate = datetime.datetime.today()
sDate_default = "{:04d}".format(pDate.year) + "{:02d}".format(pDate.month) + "{:02d}".format(pDate.day)


class CaseClassEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.float32):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, list):
            pass  
        if isinstance(obj, flowlinecase):
            return obj.sWorkspace_output 
            
        return JSONEncoder.default(self, obj)

class hexwatershedcase(object):
    __metaclass__ = ABCMeta  
    iFlag_resample_method=2 
    iFlag_flowline=1
    iFlag_global = 0
    iFlag_multiple_outlet = 0
    iFlag_elevation_profile = 0
    iFlag_stream_burning_topology=1
    iFlag_create_mesh= 1
    iFlag_simplification= 0
    iFlag_intersect= 0
    iFlag_merge_reach=1
    iMesh_type=4   
    iFlag_save_mesh = 0 

    iFlag_use_mesh_dem=0
    nOutlet=1  
    dResolution_degree=0.0
    dResolution_meter=0.0
    dThreshold_small_river=0.0
    dLongitude_left = -180
    dLongitude_right = 180
    dLatitude_bot = -90
    dLatitude_top = 90
    sFilename_dem=''  
    sFilename_model_configuration=''
    sFilename_mesh_info=''
    sFilename_flowline_info=''
    sFilename_basins=''
    
 
    sWorkspace_model_region=''    
    sWorkspace_bin=''
    
    sRegion=''
    sModel=''
    iMesh_type ='hexagon'

    sCase=''
    sDate=''    

    sFilename_spatial_reference=''
    sFilename_hexwatershed=''
    pPyFlowline = None
    sWorkspace_output_pyflowline=''
    sWorkspace_output_hexwatershed=''
    aBasin = list()


    def __init__(self, aConfig_in):
        print('HexWatershed compset is being initialized')
        self.sFilename_model_configuration    = aConfig_in[ 'sFilename_model_configuration']

        if 'sWorkspace_data' in aConfig_in:
            self.sWorkspace_data = aConfig_in[ 'sWorkspace_data']
        
        if 'sWorkspace_output' in aConfig_in:
            self.sWorkspace_output    = aConfig_in[ 'sWorkspace_output']

        if 'sWorkspace_project' in aConfig_in:
            self.sWorkspace_project= aConfig_in[ 'sWorkspace_project']

        if 'sWorkspace_bin' in aConfig_in:
            self.sWorkspace_bin= aConfig_in[ 'sWorkspace_bin']

        if 'sRegion' in aConfig_in:
            self.sRegion               = aConfig_in[ 'sRegion']

        if 'sModel' in aConfig_in:
            self.sModel                = aConfig_in[ 'sModel']
        
        #required with default variables

        if 'iFlag_resample_method' in aConfig_in:
            self.iFlag_resample_method       = int(aConfig_in[ 'iFlag_resample_method'])

        if 'iFlag_flowline' in aConfig_in:
            self.iFlag_flowline             = int(aConfig_in[ 'iFlag_flowline'])

        if 'iFlag_create_mesh' in aConfig_in:
            self.iFlag_create_mesh             = int(aConfig_in[ 'iFlag_create_mesh'])

        if 'iFlag_simplification' in aConfig_in:
            self.iFlag_simplification             = int(aConfig_in[ 'iFlag_simplification'])

        if 'iFlag_intersect' in aConfig_in:
            self.iFlag_intersect             = int(aConfig_in[ 'iFlag_intersect'])

        if 'iFlag_global' in aConfig_in:
            self.iFlag_global             = int(aConfig_in[ 'iFlag_global'])

        if 'iFlag_multiple_outlet' in aConfig_in:
            self.iFlag_multiple_outlet             = int(aConfig_in[ 'iFlag_multiple_outlet'])    

        if 'iFlag_use_mesh_dem' in aConfig_in:
            self.iFlag_use_mesh_dem             = int(aConfig_in[ 'iFlag_use_mesh_dem'])

        if 'iFlag_stream_burning_topology' in aConfig_in:
            self.iFlag_stream_burning_topology       = int(aConfig_in[ 'iFlag_stream_burning_topology'])

        if 'iFlag_save_mesh' in aConfig_in:
            self.iFlag_save_mesh             = int(aConfig_in[ 'iFlag_save_mesh'])

        #optional
        if 'iFlag_save_elevation' in aConfig_in:
            self.iFlag_save_elevation  = int(aConfig_in[ 'iFlag_save_elevation'])

        if 'iFlag_elevation_profile' in aConfig_in:
            self.iFlag_elevation_profile  = int(aConfig_in[ 'iFlag_elevation_profile'])

        if 'nOutlet' in aConfig_in:
            self.nOutlet             = int(aConfig_in[ 'nOutlet'])

        if 'dMissing_value_dem' in aConfig_in:
            self.dMissing_value_dem             = float(aConfig_in[ 'dMissing_value_dem'])

        if 'dBreach_threshold' in aConfig_in:
            self.dBreach_threshold             = float(aConfig_in[ 'dBreach_threshold'])

        if 'dAccumulation_threshold' in aConfig_in:
            self.dAccumulation_threshold             = float(aConfig_in[ 'dAccumulation_threshold'])
        
        if 'sFilename_spatial_reference' in aConfig_in:
            self.sFilename_spatial_reference = aConfig_in['sFilename_spatial_reference']

        if 'sFilename_dem' in aConfig_in:
            self.sFilename_dem = aConfig_in['sFilename_dem']

        if 'sFilename_mesh_netcdf' in aConfig_in:
            self.sFilename_mesh_netcdf = aConfig_in['sFilename_mesh_netcdf']

        if 'iCase_index' in aConfig_in:
            iCase_index = int(aConfig_in['iCase_index'])
        else:
            iCase_index = 1
        
       
        
        sDate   = aConfig_in[ 'sDate']
        if sDate is not None:
            self.sDate= sDate
        else:
            self.sDate = sDate_default

        sCase_index = "{:03d}".format( iCase_index )
        self.iCase_index =   iCase_index
        sCase = self.sModel  + self.sDate + sCase_index
        self.sCase = sCase

        sPath = str(Path(self.sWorkspace_output)  /  sCase)
        self.sWorkspace_output = sPath
        Path(sPath).mkdir(parents=True, exist_ok=True)

        
        if 'sMesh_type' in aConfig_in:
            self.sMesh_type =  aConfig_in['sMesh_type']
        else:
            self.sMesh_type = 'hexagon'
        
        sMesh_type = self.sMesh_type
        if sMesh_type =='hexagon': #hexagon
            self.iMesh_type = 1
        else:
            if sMesh_type =='square': #sqaure
                self.iMesh_type = 2
            else:
                if sMesh_type =='latlon': #latlon
                    self.iMesh_type = 3
                else:
                    if sMesh_type =='mpas': #mpas
                        self.iMesh_type = 4
                    else:
                        if sMesh_type =='tin': #tin
                            self.iMesh_type = 5
                        else:
                            print('Unsupported mesh type?')
                            
        if 'dResolution_degree' in aConfig_in:
            self.dResolution_degree = float(aConfig_in['dResolution_degree']) 

        if 'dResolution_meter' in aConfig_in:
            self.dResolution_meter = float(aConfig_in['dResolution_meter']) 
        else:
            print('Please specify resolution.')

        if 'dLongitude_left' in aConfig_in:
            self.dLongitude_left = float(aConfig_in['dLongitude_left']) 

        if 'dLongitude_right' in aConfig_in:
            self.dLongitude_right = float(aConfig_in['dLongitude_right']) 

        if 'dLatitude_bot' in aConfig_in:
            self.dLatitude_bot = float(aConfig_in['dLatitude_bot']) 

        if 'dLatitude_top' in aConfig_in:
            self.dLatitude_top = float(aConfig_in['dLatitude_top']) 

        if 'sJob' in aConfig_in:
            self.sJob =  aConfig_in['sJob'] 

        if 'sFilename_hexwatershed' in aConfig_in:
            self.sFilename_hexwatershed= aConfig_in['sFilename_hexwatershed'] 

        if 'sWorkspace_bin' in aConfig_in:
            self.sWorkspace_bin = aConfig_in['sWorkspace_bin']
        else:
            print('The path to the hexwatershed binary is not specified.')
        
                
        if 'sFilename_basins' in aConfig_in:
            self.sFilename_basins = aConfig_in['sFilename_basins']
        else:
            self.sFilename_basins = ''              

        sPath = str(Path(self.sWorkspace_output)   / 'hexwatershed')
        self.sWorkspace_output_hexwatershed = sPath
        Path(sPath).mkdir(parents=True, exist_ok=True)

        sPath = str(Path(self.sWorkspace_output)   / 'pyflowline')
        self.sWorkspace_output_pyflowline = sPath
        Path(sPath).mkdir(parents=True, exist_ok=True)

        self.sFilename_elevation = os.path.join(str(Path(self.sWorkspace_output_pyflowline)  ) , sMesh_type + "_elevation.json" )
        self.sFilename_mesh = os.path.join(str(Path(self.sWorkspace_output_pyflowline)  ) , sMesh_type + ".json" )
        self.sFilename_mesh_info  =  os.path.join(str(Path(self.sWorkspace_output_pyflowline)  ) , sMesh_type + "_mesh_info.json"  ) 
        
        
        return    

    def tojson(self):

        aSkip = ['aBasin']      

        obj = self.__dict__.copy()
        for sKey in aSkip:
            obj.pop(sKey, None)
            pass

        sJson = json.dumps(obj,\
            sort_keys=True, \
            indent = 4, \
            ensure_ascii=True, \
            cls=CaseClassEncoder)

        return sJson

    def export_config_to_json(self):  

        self.pPyFlowline.export_basin_config_to_json()

        self.sFilename_model_configuration = os.path.join(self.sWorkspace_output, 'configuration.json')
        self.sFilename_basins = self.pPyFlowline.sFilename_basins

        #save the configuration to a new file, which has the full path
        
        sFilename_configuration = self.sFilename_model_configuration

        aSkip = [ 'aBasin', \
                'aFlowline_simplified','aFlowline_conceptual','aCellID_outlet',
                'aCell' ]

        obj = self.__dict__.copy()
        for sKey in aSkip:
            obj.pop(sKey, None)
            pass
        with open(sFilename_configuration, 'w', encoding='utf-8') as f:
            json.dump(obj, f,sort_keys=True, \
                ensure_ascii=False, \
                indent=4, cls=CaseClassEncoder)        
   
        return
     
    def setup(self):
        self.pPyFlowline.setup()

        sFilename_hexwatershed = os.path.join(str(Path(self.sWorkspace_bin)  ) ,  self.sFilename_hexwatershed )
        #copy the binary file
        sFilename_new = os.path.join(str(Path(self.sWorkspace_output_hexwatershed)  ) ,  "hexwatershed" )
        copy2(sFilename_hexwatershed, sFilename_new)

        os.chmod(sFilename_new, stat.S_IRWXU )


        return
    
    def run_pyflowline(self):

        self.pPyFlowline.run()

        return
    
    def run_hexwatershed(self):
        #run the model using bash
        self.generate_bash_script()
        os.chdir(self.sWorkspace_output_hexwatershed)
        
        sCommand = "./run.sh"
        print(sCommand)
        p = subprocess.Popen(sCommand, shell= True)
        p.wait()

        return
    
    def assign_elevation_to_cells(self, sFilename_dem_in):
        iMesh_type=self.iMesh_type
        aCell_in=self.pPyFlowline.aCell
        aCell_mid=list()

        ncell = len(aCell_in)
        
        #pDriver_shapefile = ogr.GetDriverByName('ESRI Shapefile')
        pDriver_json = ogr.GetDriverByName('GeoJSON')
        pDriver_memory = gdal.GetDriverByName('MEM')

        sFilename_shapefile_cut = "/vsimem/tmp_polygon.json"

        pSrs = osr.SpatialReference()  
        pSrs.ImportFromEPSG(4326)    # WGS84 lat/lon
        pDataset_elevation = gdal.Open(sFilename_dem_in, gdal.GA_ReadOnly)

        dPixelWidth, dOriginX, dOriginY, \
            nrow, ncolumn, pSpatialRef_target, pProjection, pGeotransform = obtain_raster_metadata_geotiff(sFilename_dem_in)

        transform = osr.CoordinateTransformation(pSrs, pSpatialRef_target) 

        #get raster extent 
        dX_left=dOriginX
        dX_right = dOriginX + ncolumn * dPixelWidth
        dY_top = dOriginY
        dY_bot = dOriginY - nrow * dPixelWidth
        if iMesh_type == 4: #mpas mesh
            for i in range( ncell):
                pCell=  aCell_in[i]
                lCellID = pCell.lCellID
                dLongitude_center = pCell.dLongitude_center
                dLatitude_center = pCell.dLatitude_center
                nVertex = pCell.nVertex

                ring = ogr.Geometry(ogr.wkbLinearRing)
                for j in range(nVertex):
                    x1 = pCell.aVertex[j].dLongitude
                    y1 = pCell.aVertex[j].dLatitude
                    x1,y1 = reproject_coordinates(x1,y1,pSrs,pSpatialRef_target)
                    ring.AddPoint(x1, y1)                
                    pass        
                x1 = pCell.aVertex[0].dLongitude
                y1 = pCell.aVertex[0].dLatitude
                x1,y1 = reproject_coordinates(x1,y1,pSrs,pSpatialRef_target)    
                ring.AddPoint(x1, y1)        
                pPolygon = ogr.Geometry(ogr.wkbPolygon)
                pPolygon.AddGeometry(ring)
                #pPolygon.AssignSpatialReference(pSrs)
                if os.path.exists(sFilename_shapefile_cut):   
                    os.remove(sFilename_shapefile_cut)

                pDataset3 = pDriver_json.CreateDataSource(sFilename_shapefile_cut)
                pLayerOut3 = pDataset3.CreateLayer('cell', pSpatialRef_target, ogr.wkbPolygon)    
                pLayerDefn3 = pLayerOut3.GetLayerDefn()
                pFeatureOut3 = ogr.Feature(pLayerDefn3)
                pFeatureOut3.SetGeometry(pPolygon)  
                pLayerOut3.CreateFeature(pFeatureOut3)    
                pDataset3.FlushCache()
                minX, maxX, minY, maxY = pPolygon.GetEnvelope()
                iNewWidth = int( (maxX - minX) / abs(dPixelWidth)  )
                iNewHeigh = int( (maxY - minY) / abs(dPixelWidth) )
                newGeoTransform = (minX, dPixelWidth, 0,    maxY, 0, -dPixelWidth)  

                if minX > dX_right or maxX < dX_left \
                    or minY > dY_top or maxY < dY_bot:
                    #print(lCellID)
                    continue
                else:         
                    pDataset_clip = pDriver_memory.Create('', iNewWidth, iNewHeigh, 1, gdalconst.GDT_Float32)
                    pDataset_clip.SetGeoTransform( newGeoTransform )
                    pDataset_clip.SetProjection( pProjection)   
                    pWrapOption = gdal.WarpOptions( cropToCutline=True,cutlineDSName = sFilename_shapefile_cut , \
                            width=iNewWidth,   \
                                height=iNewHeigh,      \
                                    dstSRS=pProjection , format = 'MEM' )
                    pDataset_clip = gdal.Warp('',pDataset_elevation, options=pWrapOption)
                    pBand = pDataset_clip.GetRasterBand( 1 )
                    dMissing_value = pBand.GetNoDataValue()
                    aData_out = pBand.ReadAsArray(0,0,iNewWidth, iNewHeigh)

                    aElevation = aData_out[np.where(aData_out !=dMissing_value)]                

                    if(len(aElevation) >0 and np.mean(aElevation)!=-9999):
                        #pFeature2.SetGeometry(pPolygon)
                        #pFeature2.SetField("id", lCellID)
                        dElevation =  float(np.mean(aElevation) )  
                        #pFeature2.SetField("elev",  dElevation )
                        #pLayer2.CreateFeature(pFeature2)    
                        pCell.dElevation =    dElevation  
                        pCell.dz = dElevation  
                        aCell_mid.append(pCell)
                    else:
                        #pFeature2.SetField("elev", -9999.0)
                        pCell.dElevation=-9999.0
                        pass

        #pDataset_out2.FlushCache()

        #update neighbor
        ncell = len(aCell_mid)
        aCellID  = list()
        for i in range(ncell):
            pCell = aCell_mid[i]
            lCellID = pCell.lCellID
            aCellID.append(lCellID)

        aCell_out=list()
        for i in range(ncell):
            pCell = aCell_mid[i]
            aNeighbor = pCell.aNeighbor
            nNeighbor = pCell.nNeighbor
            aNeighbor_new = list()
            nNeighbor_new = 0 
            for j in range(nNeighbor):
                lNeighbor = int(aNeighbor[j])
                if lNeighbor in aCellID:
                    nNeighbor_new = nNeighbor_new +1 
                    aNeighbor_new.append(lNeighbor)

            pCell.nNeighbor= len(aNeighbor_new)
            pCell.aNeighbor = aNeighbor_new
            aCell_out.append(pCell)

        return aCell_out
    
    def generate_bash_script(self):

       
        sName  = 'configuration.json'
        sFilename_configuration  =  os.path.join( self.sWorkspace_output,  sName )

        os.chdir(self.sWorkspace_output_hexwatershed)
        #writen normal run script
        sFilename_bash = os.path.join(str(Path(self.sWorkspace_output_hexwatershed)  ) ,  "run.sh" )
        ofs = open(sFilename_bash, 'w')
        sLine = '#!/bin/bash\n'
        ofs.write(sLine)
        
        
        sLine = 'module load gcc/8.1.0' + '\n'
        ofs.write(sLine)
        sLine = 'cd ' + self.sWorkspace_output_hexwatershed+ '\n'
        ofs.write(sLine)
        sLine = './hexwatershed ' + sFilename_configuration + '\n'
        ofs.write(sLine)
        ofs.close()



        os.chmod(sFilename_bash, stat.S_IRWXU )

        
        return
    
    def analyze(self):
        return

    def export(self):
        
        self.pyhexwatershed_save_elevation()
        self.pyhexwatershed_save_slope()
        self.pyhexwatershed_save_flow_direction()
        
        
        return

    def pyhexwatershed_save_flow_direction(self):

        sFilename_json = os.path.join(self.sWorkspace_output_hexwatershed ,   'hexwatershed.json')

        sFilename_geojson = os.path.join(self.sWorkspace_output_hexwatershed ,   'flow_direction.json')
        if os.path.exists(sFilename_geojson):
            os.remove(sFilename_geojson)
        pDriver_geojson = ogr.GetDriverByName('GeoJSON')
        pDataset = pDriver_geojson.CreateDataSource(sFilename_geojson)

    
        pSrs = osr.SpatialReference()  
        pSrs.ImportFromEPSG(4326)    # WGS84 lat/lon

        pLayer = pDataset.CreateLayer('flowdir', pSrs, ogr.wkbLineString)
        # Add one attribute
        pLayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger64)) #long type for high resolution
        pFac_field = ogr.FieldDefn('fac', ogr.OFTReal)
        pFac_field.SetWidth(20)
        pFac_field.SetPrecision(2)
        pLayer.CreateField(pFac_field) #long type for high resolution

        pLayerDefn = pLayer.GetLayerDefn()
        pFeature = ogr.Feature(pLayerDefn)


        with open(sFilename_json) as json_file:
            data = json.load(json_file)  

            #print(type(data))

            ncell = len(data)
            lID =0 
            for i in range(ncell):
                pcell = data[i]
                lCellID = int(pcell['lCellID'])
                lCellID_downslope = int(pcell['lCellID_downslope'])
                x_start=float(pcell['dLongitude_center_degree'])
                y_start=float(pcell['dLatitude_center_degree'])
                dfac = float(pcell['DrainageArea'])
                for j in range(ncell):
                    pcell2 = data[j]
                    lCellID2 = int(pcell2['lCellID'])
                    if lCellID2 == lCellID_downslope:
                        x_end=float(pcell2['dLongitude_center_degree'])
                        y_end=float(pcell2['dLatitude_center_degree'])

                        pLine = ogr.Geometry(ogr.wkbLineString)
                        pLine.AddPoint(x_start, y_start)
                        pLine.AddPoint(x_end, y_end)
                        pFeature.SetGeometry(pLine)
                        pFeature.SetField("id", lID)
                        pFeature.SetField("fac", dfac)

                        pLayer.CreateFeature(pFeature)
                        lID =lID +1
                        break


            pDataset = pLayer = pFeature  = None      
        pass

    def pyhexwatershed_save_slope(self):

        sFilename_json = os.path.join(self.sWorkspace_output_hexwatershed ,   'hexwatershed.json')

        sFilename_geojson = os.path.join(self.sWorkspace_output_hexwatershed ,   'slope.json')
        if os.path.exists(sFilename_geojson):
            os.remove(sFilename_geojson)

        pDriver_geojson = ogr.GetDriverByName('GeoJSON')
        pDataset = pDriver_geojson.CreateDataSource(sFilename_geojson)
        
    
        pSrs = osr.SpatialReference()  
        pSrs.ImportFromEPSG(4326)    # WGS84 lat/lon

        pLayer = pDataset.CreateLayer('slp', pSrs, geom_type=ogr.wkbPolygon)
        # Add one attribute
        pLayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger64)) #long type for high resolution       
        pFac_field = ogr.FieldDefn('fac', ogr.OFTReal)
        pFac_field.SetWidth(20)
        pFac_field.SetPrecision(2)
        pLayer.CreateField(pFac_field) #long type for high resolution

        pSlp_field = ogr.FieldDefn('slpb', ogr.OFTReal)
        pSlp_field.SetWidth(20)
        pSlp_field.SetPrecision(8)
        pLayer.CreateField(pSlp_field) #long type for high resolution

        pSlp_field = ogr.FieldDefn('slpp', ogr.OFTReal)
        pSlp_field.SetWidth(20)
        pSlp_field.SetPrecision(8)
        pLayer.CreateField(pSlp_field) #long type for high resolution

        pLayerDefn = pLayer.GetLayerDefn()
        pFeature = ogr.Feature(pLayerDefn)

        with open(sFilename_json) as json_file:
            data = json.load(json_file)  
            ncell = len(data)
            lID =0 
            for i in range(ncell):
                pcell = data[i]
                lCellID = int(pcell['lCellID'])
                lCellID_downslope = int(pcell['lCellID_downslope'])
                x_start=float(pcell['dLongitude_center_degree'])
                y_start=float(pcell['dLatitude_center_degree'])
                dfac = float(pcell['DrainageArea'])
                dslpb = float(pcell['dSlope_between'])
                dslpp = float(pcell['dSlope_profile'])
                vVertex = pcell['vVertex']
                nvertex = len(vVertex)
                pPolygon = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)

                for j in range(nvertex):
                    x = vVertex[j]['dLongitude_degree']
                    y = vVertex[j]['dLatitude_degree']
                    ring.AddPoint(x, y)

                x = vVertex[0]['dLongitude_degree']
                y = vVertex[0]['dLatitude_degree']
                ring.AddPoint(x, y)
                pPolygon.AddGeometry(ring)
                pFeature.SetGeometry(pPolygon)
                pFeature.SetField("id", lCellID)                
                pFeature.SetField("fac", dfac)
                pFeature.SetField("slpb", dslpb)
                pFeature.SetField("slpp", dslpp)
                pLayer.CreateFeature(pFeature)




            pDataset = pLayer = pFeature  = None      
        pass        
    
    def pyhexwatershed_save_elevation(self):

        sFilename_json = os.path.join(self.sWorkspace_output_hexwatershed ,   'hexwatershed.json')

        sFilename_geojson = os.path.join(self.sWorkspace_output_hexwatershed ,   'elevation.json')
        if os.path.exists(sFilename_geojson):
            os.remove(sFilename_geojson)

        pDriver_geojson = ogr.GetDriverByName('GeoJSON')
        pDataset = pDriver_geojson.CreateDataSource(sFilename_geojson)
        
    
        pSrs = osr.SpatialReference()  
        pSrs.ImportFromEPSG(4326)    # WGS84 lat/lon

        pLayer = pDataset.CreateLayer('ele', pSrs, geom_type=ogr.wkbPolygon)
        # Add one attribute
        pLayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger64)) #long type for high resolution       
        pFac_field = ogr.FieldDefn('fac', ogr.OFTReal)
        pFac_field.SetWidth(20)
        pFac_field.SetPrecision(2)
        pLayer.CreateField(pFac_field) #long type for high resolution

        pSlp_field = ogr.FieldDefn('elev', ogr.OFTReal)
        pSlp_field.SetWidth(20)
        pSlp_field.SetPrecision(8)
        pLayer.CreateField(pSlp_field) #long type for high resolution

        pSlp_field = ogr.FieldDefn('elep', ogr.OFTReal)
        pSlp_field.SetWidth(20)
        pSlp_field.SetPrecision(8)
        pLayer.CreateField(pSlp_field) #long type for high resolution

        pLayerDefn = pLayer.GetLayerDefn()
        pFeature = ogr.Feature(pLayerDefn)

        with open(sFilename_json) as json_file:
            data = json.load(json_file)  
            ncell = len(data)
            lID =0 
            for i in range(ncell):
                pcell = data[i]
                lCellID = int(pcell['lCellID'])
                lCellID_downslope = int(pcell['lCellID_downslope'])
                x_start=float(pcell['dLongitude_center_degree'])
                y_start=float(pcell['dLatitude_center_degree'])
                dfac = float(pcell['DrainageArea'])
                dElev = float(pcell['Elevation'])
                dElep = float(pcell['Elevation_profile'])
                vVertex = pcell['vVertex']
                nvertex = len(vVertex)
                pPolygon = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)

                for j in range(nvertex):
                    x = vVertex[j]['dLongitude_degree']
                    y = vVertex[j]['dLatitude_degree']
                    ring.AddPoint(x, y)

                x = vVertex[0]['dLongitude_degree']
                y = vVertex[0]['dLatitude_degree']
                ring.AddPoint(x, y)
                pPolygon.AddGeometry(ring)
                pFeature.SetGeometry(pPolygon)
                pFeature.SetField("id", lCellID)                
                pFeature.SetField("fac", dfac)
                pFeature.SetField("elev", dElev)
                pFeature.SetField("elep", dElep)
                pLayer.CreateFeature(pFeature)




            pDataset = pLayer = pFeature  = None      
        pass        
    
    def create_hpc_job(self):
        """create a HPC job for this simulation
        """

        os.chdir(self.sWorkspace_output)
        #writen normal run script
        sFilename_job = os.path.join(str(Path(self.sWorkspace_output)  ) ,  "submit.job" )
        ofs = open(sFilename_job, 'w')
        sLine = '#!/bin/bash\n'
        ofs.write(sLine)
        sLine = '#SBATCH -A ESMD\n'
        ofs.write(sLine)
        sLine = '#SBATCH --job-name=hex' + self.sCase + '\n'
        ofs.write(sLine)
        sLine = '#SBATCH -t 1:00:00' + '\n'
        ofs.write(sLine)
        sLine = '#SBATCH --nodes=1' + '\n'
        ofs.write(sLine)
        sLine = '#SBATCH --ntasks-per-node=1' + '\n'
        ofs.write(sLine)
        sLine = '#SBATCH --partition=short' + '\n'
        ofs.write(sLine)
        sLine = '#SBATCH -o stdout.out\n'
        ofs.write(sLine)
        sLine = '#SBATCH -e stderr.err\n'
        ofs.write(sLine)
        sLine = '#SBATCH --mail-type=ALL\n'
        #ofs.write(sLine)
        sLine = '#SBATCH --mail-user=chang.liao@pnnl.gov\n'
        ofs.write(sLine)
        sLine = 'cd $SLURM_SUBMIT_DIR\n'
        ofs.write(sLine)
        sLine = 'module purge\n'
        ofs.write(sLine)
        sLine = 'module load gcc/8.1.0' + '\n'
        ofs.write(sLine)
        sLine = 'module load anaconda3/2019.03' + '\n'
        ofs.write(sLine)
        sLine = 'source /share/apps/anaconda3/2019.03/etc/profile.d/conda.sh' + '\n'
        ofs.write(sLine)
        sLine = './hexwatershed ' + '.ini' + '\n'
        ofs.write(sLine)
        ofs.close()

        #run pyflowline script
        sFilename_pyflowline = os.path.join(str(Path(self.sWorkspace_output_pyflowline)) , "run_pyflowline.sh" )
        ofs_pyflowline = open(sFilename_pyflowline, 'w')

        sLine = '#!/bin/bash\n'
        ofs_pyflowline.write(sLine)

        sLine = 'echo "Started to prepare python scripts"\n'
        ofs_pyflowline.write(sLine)
        sLine = 'module load anaconda3/2019.03' + '\n'
        ofs_pyflowline.write(sLine)
        sLine = 'source /share/apps/anaconda3/2019.03/etc/profile.d/conda.sh' + '\n'
        ofs_pyflowline.write(sLine)
        sLine = 'conda activate hexwatershedenv' + '\n'
        ofs_pyflowline.write(sLine)

        sLine = 'cat << EOF > run_hexwatershed.py' + '\n' 
        ofs_pyflowline.write(sLine)    
        sLine = '#!/qfs/people/liao313/.conda/envs/hexwatershedenv/bin/' + 'python3' + '\n' 
        ofs_pyflowline.write(sLine) 

        sLine = 'from pyhexwatershed.pyhexwatershed_read_model_configuration_file import pyhexwatershed_read_model_configuration_file' + '\n'
        ofs_pyflowline.write(sLine)
         
        sLine = 'sFilename_configuration_in = ' + '"' + self.sFilename_model_configuration + '"\n'
        ofs_pyflowline.write(sLine)
        sLine = 'oPyhexwatershed = pyhexwatershed_read_model_configuration_file(sFilename_configuration_in,' + \
            'iCase_index_in='+ str(self.iCase_index) + ',' +  'sMesh_type_in="'+ str(self.sMesh_type) +'"' \
           + ')'  +   '\n'   
        ofs_pyflowline.write(sLine)

        sLine = 'oPyhexwatershed.pPyFlowline.aBasin[0].dLatitude_outlet_degree=39.4620'
        ofs_pyflowline.write(sLine)
        sLine = 'oPyhexwatershed.pPyFlowline.aBasin[0].dLongitude_outlet_degree=-76.0093'
        ofs_pyflowline.write(sLine)
        
        sLine = 'oPyhexwatershed.pPyflowline.setup()' + '\n'   
        ofs_pyflowline.write(sLine)
        sLine = 'oPyhexwatershed.pPyflowline.run()' + '\n'   
        ofs_pyflowline.write(sLine)
        sLine = 'oPyhexwatershed.pPyflowline.analyze()' + '\n'   
        ofs_pyflowline.write(sLine)
        sLine = 'oPyhexwatershed.pPyflowline.export()' + '\n'   
        ofs_pyflowline.write(sLine)
        sLine = 'EOF\n'
        ofs_pyflowline.write(sLine)
        sLine = 'chmod 755 ' + 'run_hexwatershed.py' + '\n'   
        ofs_pyflowline.write(sLine)


        sLine = './run_hexwatershed.py'
        ofs_pyflowline.write(sLine)
        ofs_pyflowline.close()
        os.chmod(sFilename_pyflowline, stat.S_IREAD | stat.S_IWRITE | stat.S_IXUSR)
  
     
        return

    def submit_hpc_job(self):
        #this is not fully recommended as it may affect the environment variable

        return