import math
from ezdxf.gfxattribs import GfxAttribs

def detailTapping(hole, msp):
  xtapinfo = 'M6 x 1.75 - H6 THRU'
  holeDimeter = round((hole.dxf.radius * 2),1)
  ## FIND CENTRE OF CIRCLE ##
  holeCentre = hole.dxf.center
  holeXcoordinate = holeCentre[0]         
  holeYcoordinate = holeCentre[1]
  tapDim = msp.add_radius_dim(center=(holeCentre[0], holeCentre[1]), radius=hole.dxf.radius, angle=45, text=" "+xtapinfo, dimstyle="EZ_RADIUS", override={"dimtad": 1, "dimtoh": 1,}, dxfattribs={"layer": "Hole_Tapping"}).render()

def dimensionPrincipal(msp):
  longestLine = {"Line Object" : 'empty', "Line Length" : 0}
  linesQuery = msp.query('LINE')
  #Get longest horizontal line
  for line in linesQuery:
    lineLength = (line.dxf.end - line.dxf.start)
    lineLength = math.sqrt(((line.dxf.end[0] - line.dxf.start[0])**2) + ((line.dxf.end[1] - line.dxf.start[1])**2))
    
    if lineLength > longestLine['Line Length'] :
      longestLine['Line Object'] = line
      longestLine['Line Length'] = lineLength

  #Dimension 
  alignedDim = msp.add_aligned_dim(p1=longestLine['Line Object'].dxf.start, p2=longestLine['Line Object'].dxf.end, distance=-1, override={"dimtad":4}, dxfattribs={"layer": "Dimensions"}).render()

  #Get longest vertical line

  #Dimension line

def lineLength(startPoint, endPoint):
  length = math.sqrt(((endPoint[0] - startPoint[0])**2) + ((endPoint[1] - startPoint[1])**2))

def dimensionBoundingBox(msp, xboundingBox, xtextHeight):
  secondHorizontalPoint = (xboundingBox.extmax[0], xboundingBox.extmin[1])
  secondVerticalPoint = (xboundingBox.extmin[0], xboundingBox.extmax[1])

  #Dimension lines using the dimension function - these do not show up when addaed to a block entity
  #horizDim = msp.add_linear_dim(base=(3,2), p1=xboundingBox.extmin, p2=xboundingBox.extmax, override={"dimclrt":1, "dimclrd":1, "dimclre":1, "dimtad":4}, dxfattribs={"layer": "Dimensions"}).render()
  #horizDim = msp.add_aligned_dim(p1=xboundingBox.extmin, p2=secondHorizontalPoint, distance=-2, override={"dimtxt":xtextHeight,"dimclrt":1, "dimclrd":1, "dimclre":1, "dimtad":4}, dxfattribs={"layer": "Dimensions"}).render()
  #vertDim = msp.add_aligned_dim(p1=xboundingBox.extmin, p2=secondVerticalPoint, distance=2, override={"dimtxt":xtextHeight, "dimclrt":1, "dimclrd":1, "dimclre":1, "dimtad":1}, dxfattribs={"layer": "Dimensions"}).render()

  #Create manual dimension lines and values
  s = 6 #Spacing between dimension line and model
  attribs = GfxAttribs(layer='Dimensions')
  hStart = (xboundingBox.extmin[0], (xboundingBox.extmin[1] - s))
  hEnd = (xboundingBox.extmax[0], (xboundingBox.extmin[1] - s))
  vStart = (xboundingBox.extmin[0] - s, (xboundingBox.extmin[1])) 
  vEnd = (xboundingBox.extmin[0] - s, xboundingBox.extmax[1])
  horizLine = msp.add_line((hStart), (hEnd), dxfattribs=attribs)
  vertLine = msp.add_line((vStart), (vEnd), dxfattribs=attribs)
  #Add horizontal oblique ends
  msp.add_line(((xboundingBox.extmin[0]-5), (xboundingBox.extmin[1]-5-s)), ((xboundingBox.extmin[0]+5), (xboundingBox.extmin[1]+5-s)), dxfattribs=attribs)
  msp.add_line(((xboundingBox.extmax[0]-5), (xboundingBox.extmin[1]-5-s)), ((xboundingBox.extmax[0]+5), (xboundingBox.extmin[1]+5-s)), dxfattribs=attribs)
  #Add vertical oblique ends
  msp.add_line(((xboundingBox.extmin[0]-5-s), (xboundingBox.extmin[1]-5)), ((xboundingBox.extmin[0]+5-s), (xboundingBox.extmin[1]+5)), dxfattribs=attribs)
  msp.add_line(((xboundingBox.extmin[0]-5-s), (xboundingBox.extmax[1]-5)), ((xboundingBox.extmin[0]+5-s), (xboundingBox.extmax[1]+5)), dxfattribs=attribs)
  
  horizLength = math.ceil(abs(xboundingBox.extmax[0] - xboundingBox.extmin[0]))
  vertLength = math.ceil(abs(xboundingBox.extmax[1] - xboundingBox.extmin[1]))
  hDimPos = (xboundingBox.extmin[0]+(horizLength/2), (xboundingBox.extmin[1]-(xtextHeight+2)))
  vDimPos = (xboundingBox.extmin[0]-((xtextHeight/2))-(s+2)), (xboundingBox.extmin[1]+(vertLength/2)) 
  text = msp.add_text(horizLength).set_placement(hDimPos)
  text.dxf.height = xtextHeight
  text.dxf.layer = 'Dimensions'
  text.dxf.halign = 4
  text = msp.add_text(vertLength).set_placement(vDimPos)
  text.dxf.height = xtextHeight
  text.dxf.rotation = 90
  text.dxf.layer = 'Dimensions'
  #text.dxf.valign = 0
  text.dxf.halign = 4


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


def pointDistance(point1, point2):
    dist = math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)
    #print(f'Distance between points: {dist}')
    return dist



'''
import os
import shutil
testdir=os.listdir("/tmp")
print(testdir)
for item in testdir:
    if item.endswith(".zip"):
        os.remove(item)
    if item.startswith("tmp", 0, 3):
      #os.remove(os.path.join('/tmp', item))
      shutil.rmtree(os.path.join('/tmp', item), ignore_errors=True) 
      #os.rmdir(os.path.join('/tmp', item))
      os.listdir('/tmp')
'''        
