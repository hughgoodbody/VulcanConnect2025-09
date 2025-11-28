from vulcan_connect.backend.onshape.onshape import Onshape
from vulcan_connect.backend.utils.helpers import parse_url
from vulcan_connect.backend.schema.cls_part_schema import FoundPartsInformation
from vulcan_connect.backend.bodies import get_body_details

#Part studio URL
URL = 'https://cad.onshape.com/documents/c6ebc4e94b0c9444f3e817dd/w/f57e05317e689fbe5993dbea/e/f61f6af9334b0a4792d712f3'
BODY = 'JHD'

documentId, wvmType, wvmId, elementId =  parse_url(URL)
#Get body details
part = FoundPartsInformation()
part.part_details.documentId = documentId
part.part_details.wvmType = wvmType
part.part_details.wvmId = wvmId
part.part_details.elementId = elementId
part.part_details.partId = BODY


get_body_details([part])


#Get tapped holes