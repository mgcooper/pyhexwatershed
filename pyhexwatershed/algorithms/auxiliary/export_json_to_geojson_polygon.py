import os
import json
from osgeo import gdal, ogr, osr, gdalconst

def export_json_to_geojson_polygon(sFilename_json_in,
                                    sFilename_geojson_out,
                                    aVariable_json_in,
                                    aVariable_geojson_out,
                                    aVariable_type_out):

    """
    export a hexwatershed json to geojson polygon

    Args:
        sFilename_json_in (_type_): _description_
        sFilename_geojson_out (_type_): _description_
        aVariable_in (_type_): _description_
    """
    
    if os.path.exists(sFilename_geojson_out):
        os.remove(sFilename_geojson_out)

    pDriver_geojson = ogr.GetDriverByName('GeoJSON')
    pDataset = pDriver_geojson.CreateDataSource(sFilename_geojson_out)           
    pSrs = osr.SpatialReference()  
    pSrs.ImportFromEPSG(4326)    # WGS84 lat/lon
    pLayer = pDataset.CreateLayer('hexwatershed', pSrs, geom_type=ogr.wkbPolygon)
    #Add basic attributes cellid 
    pLayer.CreateField(ogr.FieldDefn('cellid', ogr.OFTInteger64)) #long type for high resolution         
    nField_in = len(aVariable_json_in)
    nField_out = len(aVariable_geojson_out)
    if nField_in != nField_out:
        print("Error: the field number of input and output are not the same")
        return

    for i in range(nField_out):
        sVariable = aVariable_geojson_out[i].lower()
        iVariable_type = aVariable_type_out[i]
        if iVariable_type == 1: #integer
            pField = ogr.FieldDefn(sVariable, ogr.OFTInteger)
            pField.SetWidth(10)
        else: #float
            pField = ogr.FieldDefn(sVariable, ogr.OFTReal)
            pField.SetWidth(20)
            pField.SetPrecision(8)
            pass

        pLayer.CreateField(pField) #long type for high resolution     

    pLayerDefn = pLayer.GetLayerDefn()
    pFeature = ogr.Feature(pLayerDefn)
    with open(sFilename_json_in) as json_file:
        data = json.load(json_file)  
        ncell = len(data)
        #lID = 0 
        for i in range(ncell):
            pcell = data[i]
            lCellID = int(pcell['lCellID'])
            #lCellID_downslope = int(pcell['lCellID_downslope'])
            #x_start=float(pcell['dLongitude_center_degree'])
            #y_start=float(pcell['dLatitude_center_degree'])            
            vVertex = pcell['vVertex']
            nvertex = len(vVertex)
            pPolygon = ogr.Geometry(ogr.wkbPolygon)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for j in range(nvertex):
                x = vVertex[j]['dLongitude_degree']
                y = vVertex[j]['dLatitude_degree']
                ring.AddPoint(x, y)
                pass
            
            x = vVertex[0]['dLongitude_degree']
            y = vVertex[0]['dLatitude_degree']
            ring.AddPoint(x, y)
            pPolygon.AddGeometry(ring)
            pFeature.SetGeometry(pPolygon)
            pFeature.SetField("cellid", lCellID)                                    
            for k in range(nField_out):
                iDataType = aVariable_type_out[k]
                if iDataType == 1:
                    dValue = int(pcell[aVariable_json_in[k]])   
                else:                     
                    dValue = float(pcell[aVariable_json_in[k]])

                pFeature.SetField(aVariable_geojson_out[k], dValue)    

            pLayer.CreateFeature(pFeature)
        pDataset = pLayer = pFeature  = None      
    pass   