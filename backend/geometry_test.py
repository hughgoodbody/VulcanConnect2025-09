from backend.geometry_functions import geometry_test_functions as functions

'''Due to multiple options of List, Variable and Boolean configurations, configurations need to be encoded so the correct
configuration is addressed'''

def geometry_test(parts_to_test):
    TEST_NORMAL = 0
    TOLERANCE = 0.0001
    TOLERANCE2 = 0.00000001
    PERIMETER = 0
    for part in parts_to_test:
        #Test for planar faces
        planarFaces = [i for i in part['Geometry Info']['Faces'] if i['surface']['type'] == 'PLANE']
        if len(planarFaces) <2:
            print('No Planar Faces Found')            
            return False
        
        # Step 1: Find largest two planar faces
        print('Finding Largest Faces...')
        area_sorted_indices = sorted(
            range(len(planarFaces)), 
            key=lambda i: planarFaces[i]['area'], 
            reverse=True
        )

        top_face = planarFaces[area_sorted_indices[0]]
        second_face = planarFaces[area_sorted_indices[1]]

        # Step 2: Check equal area within tolerance
        print('Checking area...')
        if abs(top_face['area'] - second_face['area']) > TOLERANCE:            
            return False
        
        # Step 3: Check parallelism
        print('Checking parallelism...')
        if not functions.are_faces_parallel(top_face, second_face, TOLERANCE2):
            return False

        # Step 4: Check part thickness
        print('Checking Thickness...')
        part_thickness = functions.calculate_thickness(top_face, second_face)
        if part_thickness > part['Misc']['Max Thickness'] / 1000:
            return False    

        # Step 5: Get main face indices in original face list
        face_id_1 = top_face['id']
        face_id_2 = second_face['id']
        idx1 = functions.find_face_index(planarFaces, face_id_1)
        idx2 = functions.find_face_index(planarFaces, face_id_2)

         # Step 6: Adjacency/perpendicularity checks
        print('Sheet metal check...')
        if part['Sheet Metal'].get('Sheet Metal', False):
            adjacent = perpendicular = True
            part['Operations']['Operations'] = 'B'
        else:
            print('Checking adjacency and perpendicularity...')
            adjacent = functions.are_faces_adjacent(planarFaces, idx1, idx2)
            perpendicular = functions.are_faces_perpendicular(planarFaces, idx1, idx2, TOLERANCE2)
            
        if (adjacent and perpendicular):
            #Get perimeter of edge list
            print('Getting perimeter...')
            perimeter = 0
            for i in part['Geometry Info']['Edges']:
                perimeter = perimeter + (i['geometry']['length'])
            print('Getting longest edge...')    
            longestEdge = functions.find_longest_edge(planarFaces, part['Geometry Info']['Edges'], idx1)
            print('Getting view matrix...')
            viewMatrix = functions.compute_view_matrix(part['Geometry Info']['Edges'], planarFaces, longestEdge, idx1)
        

        #MAYBE ALL THIS SHOULD BE INDENTED UNDER ADJACENT AND PERP!!!!, otherwise return FALSE???


        #Look for undersize holes
        undersize_hole = functions.undersize_holes(part['Geometry Info']['Edges'])
        if  undersize_hole:
            part['Geometry Info']['Has Undersize Holes'] = True
            part['Geometry Info']['Undersize Ratio'] = undersize_hole / part_thickness
        else: 
            part['Geometry Info']['Has Undersize Holes'] = False
            part['Geometry Info']['Undersize Ratio'] = None 
        
        
        #Update the part details with new information
        print('Updating data...')
        part['Geometry Info']['View Matrix'] = viewMatrix    
        part['Geometry Info']['Longest Edge'] = longestEdge 
        part['Geometry Info']['Thickness'] = part_thickness
        part['Geometry Info']['BoxMinCorner'] = planarFaces[idx1]['box']['minCorner']
        part['Geometry Info']['BoxMaxCorner'] = planarFaces[idx1]['box']['maxCorner']
        part['Geometry Info']['Edge Perimeter'] = perimeter 
        part['Geometry Info']['Description'] = str(part_thickness*1000) + 'mm Laser Plate'
        part['Geometry Info']['Normal'] = planarFaces[idx1]['surface']['normal']
        part['Geometry Info']['Origin'] = planarFaces[idx1]['surface']['origin']
        part['Geometry Info']['Area'] = planarFaces[idx1]['area']
        part['Geometry Info']['Face'] = face_id_1
        print('OK TO PROCESS AS DXF')
    return 
