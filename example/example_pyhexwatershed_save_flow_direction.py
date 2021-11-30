from pyhexwatershed.operation.postprocess.save.pyhexwatershed_save_flow_direction import pyhexwatershed_save_flow_direction
from pyhexwatershed.case.pyhexwatershed_read_model_configuration_file import pyhexwatershed_read_model_configuration_file

sFilename_configuration_in = '/qfs/people/liao313/workspace/python/pyhexwatershed/pyhexwatershed/config/hexwatershed_susquehanna_mpas.json'
#sFilename_configuration_in = '/qfs/people/liao313/workspace/python/pyhexwatershed/pyhexwatershed/config/hexwatershed_icom_mpas.json'

oModel = pyhexwatershed_read_model_configuration_file(sFilename_configuration_in)

pyhexwatershed_save_flow_direction(oModel)

print("Finished")