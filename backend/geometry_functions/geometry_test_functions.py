import math
import numpy


def load_js_function_as_string(path_to_js_file):
    with open(path_to_js_file, 'r', encoding='utf-8') as file:
        js_code = file.read()
        return js_code


'''FIND DICTIONRY VALUE IN LIST
This gives the index position in the list
https://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value
'''
def findInList(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

'''DXF GEOMETRY FUNCTIONS'''
def search(lst, key, value):
    listIndex = next((index for (index, d) in enumerate(lst) if d[key] == value), None)
    return listIndex


def dotProduct(vector1, vector2):
    dotproductVal = (vector1[0] * vector2[0]) + (vector1[1] * vector2[1]) + (vector1[2] * vector2[2])
    dotproductVal = abs(dotproductVal)
    #dotproductVal = round(dotproductVal)
    #print(f'Dot Product is: {dotproductVal}')
    return dotproductVal

def find_face_index(faces, face_id):
    return next((i for i, f in enumerate(faces) if f['id'] == face_id), None)

def pointDistance(point1, point2):
    dist = math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)
    #print(f'Distance between points: {dist}')
    return dist


def calculate_thickness(face1, face2):
    o1 = face1['surface']['origin']
    o2 = face2['surface']['origin']
    vec = (o1['x'] - o2['x'], o1['y'] - o2['y'], o1['z'] - o2['z'])
    n = [face1['surface']['normal']['x'], face1['surface']['normal']['y'], face1['surface']['normal']['z']]
    return abs(dotProduct(vec, n))

def are_faces_parallel(face1, face2, tol):
    n1 = face1['surface']['normal']
    n2 = face2['surface']['normal']
    dot = n1['x']*n2['x'] + n1['y']*n2['y'] + n1['z']*n2['z']
    return abs(dot - 1) <= tol

def get_face_edges(faces, face_index):
    edge_list = list()
    edge_list.clear()
    for coedge_data in faces[face_index]['loops']:
        coedges = coedge_data['coedges']
        for edge_data in coedges:
            edgeId = edge_data['edgeId']
            #edgeId = facesList[face_index]['loops']['coedges']['edgeId']
            edge_list.append(edgeId)
    return edge_list

def are_faces_adjacent(qtyFaces, largestFace0_index, largestFace1_index):
    #Get edges of two largest faces
    largestFace0_Edges = get_face_edges(qtyFaces, largestFace0_index)
    largestFace1_Edges = get_face_edges(qtyFaces, largestFace1_index)

    for i in range(len(qtyFaces)):
        if i == largestFace0_index or i == largestFace1_index:
            continue
        test_edge = get_face_edges(qtyFaces,i)
        bool = (any(elem in largestFace0_Edges  for elem in test_edge)) and (any(elem in largestFace1_Edges  for elem in test_edge))
        if bool == False:
            #print('Face is not adjacent')
            return False

        return True

def are_faces_perpendicular(qtyFaces, largestFace0_index, largestFace1_index, tolerance):
    largestFace0_Edges = get_face_edges(qtyFaces, largestFace0_index)
    largestFace1_Edges = get_face_edges(qtyFaces, largestFace1_index)
    #Normal for first largest face
    normal1 = qtyFaces[largestFace0_index]['surface']['normal']
    #print(f"Normal1: {normal1}")
    #Normal for other largest face
    normal2 = qtyFaces[largestFace1_index]['surface']['normal']
    #print(f"Normal2: {normal1}")
    #Get testing normal
    for i in range(len(qtyFaces)):
        if i == largestFace0_index or i == largestFace1_index:
            continue

        if qtyFaces[i]['surface']['type'] == 'PLANE':
            
            test_normal = qtyFaces[i]['surface']['normal']
            i_1 = abs((normal1['x'] * test_normal['x']) + (normal1['y'] * test_normal['y']) + (normal1['z'] * test_normal['z']))
            i_2 = abs((normal2['x'] * test_normal['x']) + (normal2['y'] * test_normal['y']) + (normal2['z'] * test_normal['z']))
            #print(f"Perpendicularity Planar Logging: i_1 = {i_1},  i_2 = {i_2}")
            #Dot product should be = 0
            #if i_1 != ((1-i_1) <= tolerance) and ((1-i_2) <= tolerance) != 0:
            if abs(i_1 - 1) <= tolerance and abs(i_1 - 1) <= tolerance:
                #Faces are NOT perpendicular
                #print('Planes are not Perpendicular')
                return False

        elif qtyFaces[i]['surface']['type'] == 'CYLINDER':
            
            test_normal = {'x': qtyFaces[i]['surface']['axis']['x'], 'y': qtyFaces[i]['surface']['axis']['y'], 'z': qtyFaces[i]['surface']['axis']['z']}
            i_1 = abs((normal1['x'] * test_normal['x']) + (normal1['y'] * test_normal['y']) + (normal1['z'] * test_normal['z']))
            i_2 = abs((normal2['x'] * test_normal['x']) + (normal2['y'] * test_normal['y']) + (normal2['z'] * test_normal['z']))
            #print(f"Perpendicularity Planar Logging: i_1 = {i_1},  i_2 = {i_2}")
            #Dot product should be = 0
            #if i_1 != ((1-i_1) <= tolerance) and ((1-i_2) <= tolerance) != 0:
            #print(abs(i_1 - 1))
            if abs(i_1 - 1) >= tolerance and abs(i_1 - 1) >= tolerance:
                #Faces are NOT perpendicular
                #print('Cylinders are not Perpendicular')
                return False      

        else:
            #test_normal = {'x': facesList[i]['surface']['direction']['x'], 'y': facesList[i]['surface']['direction']['y'], 'z': facesList[i]['surface']['direction']['z']}
            #print(test_normal)
            try:
                #test_normal = facesList[i]['surface']['axis']
                test_normal = {'x': qtyFaces[i]['surface']['direction']['x'], 'y': qtyFaces[i]['surface']['direction']['y'], 'z': qtyFaces[i]['surface']['direction']['z']}
                #print(test_normal)
                
                #Axis needs to be parallel to main surfaces, ie dot product = 1

                i_1 = abs((normal1['x'] * test_normal ['x']) + (normal1['y'] * test_normal['y']) + (normal1['z'] * test_normal['z']))
                i_2 = abs((normal2['x'] * test_normal['x']) + (normal2['y'] * test_normal['y']) + (normal2['z'] * test_normal['z']))
                #print(f"Perpendicularity Axis Logging: i_1 = {i_1},  i_2 = {i_2}")
                #if i_1 != 1 and i_2 != 1:
                if abs(i_1 - 1) >= tolerance and abs(i_1 - 1) >= tolerance:
                    #Axis not parallel to surface normals
                    #print('Sweep Axis is not perpendicular')
                    return False
            except:
            #print('Axis Not Identified')
             return False

    return True

def find_longest_edge(qtyFaces, edges, largestFace0_index):
    edgeLengthFinal = 0
    longestLinear = 0
    longestNonLinear = 0
    linearEdgeFlag = 0
    largestFace0_Edges = get_face_edges(qtyFaces, largestFace0_index)
    for a in largestFace0_Edges:
        #print(f"Longest Edges: = {largestFace0_Edges}")
        #print(f"Integer: = {a}")
        #print(f"Testing Edge: = {a}")
        longestEdgeIndex = search(edges, "id", a)
        if str(edges[longestEdgeIndex]['curve']['type']) == 'LINE':
            edgeLength = (edges[longestEdgeIndex]['geometry']['length'])
            if edgeLength >= longestLinear:
                longestLinear = edgeLength
                linearEdgeFlag = 1
                longestLinearEdgeID = a
        else:
            edgeLength = (edges[longestEdgeIndex]['geometry']['length'])
            if edgeLength >= longestNonLinear:
                longestNonLinear = edgeLength
                longestNonLinearEdgeId = a
        if linearEdgeFlag == 1:
            longestEdgeID = longestLinearEdgeID
        else:
            longestEdgeID = longestNonLinearEdgeId
            #print(f"Edge ID: {longestEdgeID} = {edgeLengthFinal}")
    return longestEdgeID

def compute_view_matrix(edges, facesList, longestEdgeID, largestFace0_index):
    viewMatrix = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]

    longestEdgeIndex = search(edges, "id", longestEdgeID)

    #x = 0,1,2
    viewMatrix[0] = edges[longestEdgeIndex]['geometry']['startVector']['x']                 #longestEdgeIndex['edges']['geometry']['startVector'][0]
    viewMatrix[1] = edges[longestEdgeIndex]['geometry']['startVector']['y']
    viewMatrix[2] = edges[longestEdgeIndex]['geometry']['startVector']['z']

    #y = 4,5,6
    '''Use numpy to find the cross product of x axis (startVector) and the face normal to give y axis'''
    yAxis = numpy.cross([edges[longestEdgeIndex]['geometry']['startVector']['x'], edges[longestEdgeIndex]['geometry']['startVector']['y'], edges[longestEdgeIndex]['geometry']['startVector']['z']],
                        [facesList[largestFace0_index]['surface']['normal']['x'], facesList[largestFace0_index]['surface']['normal']['y'], facesList[largestFace0_index]['surface']['normal']['z']])
        
    viewMatrix[4] = -yAxis[0]
    viewMatrix[5] = -yAxis[1]
    viewMatrix[6] = -yAxis[2]


    #z = 8,9,10 - Normal
    viewMatrix[8] = facesList[largestFace0_index]['surface']['normal']['x']
    viewMatrix[9] = facesList[largestFace0_index]['surface']['normal']['y']
    viewMatrix[10] = facesList[largestFace0_index]['surface']['normal']['z']

    #Transform = 12,13,14 - Face origin - World origin
    viewMatrix[12] = facesList[largestFace0_index]['surface']['origin']['x'] - 0
    viewMatrix[13] = facesList[largestFace0_index]['surface']['origin']['y'] - 0
    viewMatrix[14] = facesList[largestFace0_index]['surface']['origin']['z'] - 0

    #print(f"View Matrix: {viewMatrix}")
    return viewMatrix

def undersize_holes(edges):        
    smallest = None
    for edge in edges:
        if edge.get('curve', {}).get('type') == "CIRCLE":
            diameter = edge.get('radius', 0) * 2
            if smallest is None or diameter < smallest:
                smallest = diameter
    return smallest

