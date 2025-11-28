import os
import json
from backend.onshape.onshape import Onshape

#Get hole table for part
#Already have a view matrix, but might need to get another to figure the coordinates out with relation to the dxf

def get_tapped_holes():

    holeList = [ { "coords" : [ { "x" : -0.039137858897447586 , 
                            "y" : 0.033607516437768936 , 
                            "z" : 0 } , 
                            { "x" : -0.039137858897447586 , 
                             "y" : 0.033607516437768936 , 
                             "z" : 0.025 } ] , 
                             "tapSize" : "M6x1.00" } , 
                             { "coords" : [ { 
                                 "x" : 0.05381455644965172 , 
                                 "y" : -0.03020421229302883 , 
                                 "z" : 0 } , 
                                 { "x" : 0.05381455644965172 , 
                                  "y" : -0.03020421229302883 , 
                                  "z" : 0.025 } ] , 
                                  "tapSize" : "M12x1.75" } ]
    
    return holeList
