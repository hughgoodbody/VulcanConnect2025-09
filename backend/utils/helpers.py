# Helper utilities
from urllib.parse import urlparse
from config.settings import API_VERSION


def parse_url(url):
    parsed_url = list(filter(None, urlparse(url).path.split('/'))) 
    #print(parsed_url[1], parsed_url[2], parsed_url[3], parsed_url[5])   
    return parsed_url[1], parsed_url[2], parsed_url[3], parsed_url[5]   #documentId, wvmType, wvmId, elementId


'''Get body bounding box'''
def get_body_bounding_box(onshape, did, wvm, wvmid, eid, partid, configid):
    url = f'/api/{API_VERSION}/parts/d/{did}/{wvm}/{wvmid}/e/{eid}/partid/{partid}/boundingboxes'
    query = {'configuration': configid}
    return onshape.request('get', url, query=query).json()

'''Update part metadata''' #Pass in a dictionary of properties
def update_metadata(onshape, did, wvm, wvmid, eid, pid, configid, iden, propertyDict):
    url = f'/api/{API_VERSION}/metadata/d/{did}/{wvm}/{wvmid}/e/{eid}/{iden}/{pid}'
    query = {'configuration': configid}
    body = propertyDict
    return onshape.request('post', url, query=query, body=body).json()

'''Function to find the extreme points in a view's bodyData'''
def find_extreme_points(view_data):
    extreme_points = {
        'min_point': [float('inf'), float('inf'), float('inf')],
        'min_point_uniqueId': None,
        'max_point': [-float('inf'), -float('inf'), -float('inf')],
        'max_point_uniqueId': None
    }

    for item in view_data['bodyData']:
        if 'data' in item:
            if item['type'] in ['line', 'circularArc', 'ellipticalArc']:
                points = [item['data']['start'], item['data']['end']]
            else:
                continue

            for point in points:
                # Check for min point
                if point < extreme_points['min_point']:
                    extreme_points['min_point'] = point
                    extreme_points['min_point_uniqueId'] = item['uniqueId']

                # Check for max point
                if point > extreme_points['max_point']:
                    extreme_points['max_point'] = point
                    extreme_points['max_point_uniqueId'] = item['uniqueId']

    return extreme_points

'''Get named views'''
def get_named_views(onshape, did, eid):
    url = f'/api/{API_VERSION}/partstudios/d/{did}/e/{eid}/namedViews'
    return onshape.request('get', url).json()


'''Get STEP URL'''
def get_step_url(onshape, docid, wvm_type, wv, elementId, configId, partId):
    url = f'/api/{API_VERSION}/partstudios/d/{docid}/{wvm_type}/{wv}/e/{elementId}/translations'
    body = {
        'formatName': 'STEP',
        'storeInDocument': False,
        'partIds': partId,
        'configuration': configId
    }
    return onshape.request('post', url, body=body).json()['href']