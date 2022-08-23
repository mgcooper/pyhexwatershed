#this is an example to create a HPC job to run a complete simulation
import sys
from pathlib import Path
from os.path import realpath


from pyhexwatershed.pyhexwatershed_read_model_configuration_file import pyhexwatershed_read_model_configuration_file
from pyhexwatershed.pyhexwatershed_create_template_configuration_file import pyhexwatershed_create_template_configuration_json_file

#setup a few keyword
sMesh_type = 'mpas'
iCase_index = 1
dResolution_meter=5000
sDate='20220308'
iFlag_option = 1 #use a template or read an existing configuration file

sPath = str(Path().resolve())
sPath_bin= str(Path(sPath ) / 'bin')
if iFlag_option ==1:
    sFilename_configuration_in = sPath +  '/tests/configurations/template.json' 
    sWorkspace_data = realpath( sPath +  '/data/susquehanna' )
    oPyhexwatershed = pyhexwatershed_create_template_configuration_json_file(sFilename_configuration_in, sWorkspace_data, sPath_bin, sMesh_type_in=sMesh_type, iCase_index_in = iCase_index, sDate_in = sDate)
    print(oPyhexwatershed.tojson())
else: 
    if iFlag_option == 2:     
        sFilename_configuration_in = realpath( sPath +  '/../configurations/)pyflowline_susquehanna_mpas.json' )
        oPyhexwatershed = pyhexwatershed_read_model_configuration_file(sFilename_configuration_in)     
        print(oPyhexwatershed.tojson())

#create the case
oPyhexwatershed.creat_hpc_job()
#optionally, you can also submit it
oPyhexwatershed.submit_hpc_job()

print('Finished')

