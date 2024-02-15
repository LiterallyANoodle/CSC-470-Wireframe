#######################################################################################
# Name: Matthew Mahan
# SID: 103 85 109
# Due Date: 2/15/2024
# Assignment Number: 3
# Desc: Program displays basic 3D shapes with flat shading, gouraud shading, and phong shading. 
#######################################################################################

# ****NOTE: This framework defines a world with a single polygon: a pyramid ****
#

import math
import copy
from tkinter import *

# Constants 
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 400
CAMERA_Z_OFFSET = 500

ILLUMINATION_KD = 0.5
ILLUMINATION_KS = 0.5
SPEC_IND = 7.0
AMBIENT_INT = 0.4
DIFFUSE_INT = 0.7

NO_SHADING = 0
FLAT_SHADING = 1
GOURAUD_SHADING = 2
PHONG_SHADING = 3

DEFAULT_OUTLINE = True
BESPOKE_OUTLINE = not DEFAULT_OUTLINE
POLY_FILL = True
ROUNDING = True
SHADING_STYLE = NO_SHADING

L_LIST = [1, 1, -1]
V_LIST = [0, 0, -1]

# point type hint 
Vector3 = list[float, float, float]
Vector2 = list[float, float]

# Polygons type hint
# The polygon type does not actually hold any points in it, but rather references to points in the dictionary that is the object's pointcloud
# This is done to more elegantly prevent point duplication in the pointCloud 
Polygon = list[int]

# Object Class 
class Object:

    polygons: list[Polygon] = []
    pointCloud: list[Vector3] = []
    defaultPointCloud: list[Vector3] = []

    anchorPoint: Vector3 = [0, 0, 0]
    outlineColor: str = "black"
    polyColor: list[str] = None
    shadingOverride: list[int] = None

    def __init__(this, polygons, points, anchorPoint=None):
        this.polygons = polygons
        this.pointCloud = points
        this.defaultPointCloud = copy.deepcopy(points)
        this.polyColor = ['white', '#cccccc', '#999999', '#666666', '#333333', 'black'] # default colors 
        
        this.anchorPoint = anchorPoint
        if anchorPoint == None:
            this.anchorPoint = findAnchorPoint(this)


# Quick and dirty Matrices 
# For sake of convenience, these will ONLY be instantiated when a proper operation is needed 
class Matrix: 

    width: int = None
    height: int = None 
    elements: list[float] = None

    # All matrices intialize to 0
    def __init__(this, width, height):
        this.width = width
        this.height = height
        this.elements = []
        for e in range(width * height):
            this.elements.append(0)

    # get/set element at position i,j 
    # for simplicity, i will indicate how far from the left and j will indicate how far from the top 
    # real math does it the other way, but idc this is more convenient 
    def getElement(this, i: int, j: int) -> float:
        return this.elements[this.width * j + i]
    
    def setElement(this, i: int, j: int, element: float) -> None:
        this.elements[this.width * j + i] = element

    # useful for multiplication 
    def getColumnAsRowVector(this, i: int):
        elements = []
        for j in range(this.height):
            elements.append(this.getElement(i, j))
        return RowVector(elements)
    
    def getRowAsRowVector(this, j: int):
        elements = []
        for i in range(this.width):
            elements.append(this.getElement(i, j))
        return RowVector(elements)

    # matrix math 
        
    # matrix multiplication
    def multiply(left, right):
        
        # the width of Left must equal the height of Right 
        # the resultant matrix will have the height of Left and the width of Right 
        product = Matrix(right.width, left.height)

        for i in range(product.width):
            for j in range(product.height):
                # effectively a dot of the row of Left and the column of Right 
                product.setElement(i, j, left.getRowAsRowVector(j).dot(right.getColumnAsRowVector(i)))

        return product

# Matrix with height 1
# For sake of convenience, these will ONLY be instantiated when a special operation is needed 
class RowVector(Matrix):

    # init from a list (vector)
    def __init__(this, elements):
        super().__init__(len(elements), 1)
        this.height = 1
        this.width = len(elements)
        this.elements = elements

    # vector math 
        
    def add(this, other):

        if this.width != other.width:
            print("Can't add different length vectors.")
            return
        
        sum = [0.0, 0.0, 0.0]
        for i in range(len(this.elements)):
            sum[i] = this.elements[i] + other.elements[i]

        return RowVector(sum)
    
    # dot product 
    def dot(this, other) -> float:

        if this.width != other.width:
            print("Can't dot product different length vectors.")
            return

        product = 0

        for i in range(this.width):
            product += this.getElement(i, 0) * other.getElement(i, 0)

        return product
    
    # cross product 
    def cross(this, other):

        if (this.width != 3) or (other.width != 3):
            print("Can't cross product vectors of length not 3")
            return

        x = (this.getElement(1, 0) * other.getElement(2, 0)) - (this.getElement(2, 0) * other.getElement(1, 0))
        y = (this.getElement(2, 0) * other.getElement(0, 0)) - (this.getElement(0, 0) * other.getElement(2, 0))
        z = (this.getElement(0, 0) * other.getElement(1, 0)) - (this.getElement(1, 0) * other.getElement(0, 0))

        return RowVector([x, y, z])
    
    # get magnitude 
    def magnitude(this) -> float:
        
        sum = 0
        for i in range(this.width):
            sum += this.getElement(i, 0) ** 2

        return sum ** .5 # sqrt
    
    # get normalized vector 
    def normalize(this):

        elements = []

        magnitude = this.magnitude()
        for i in range(this.width):
            elements.append(this.getElement(i, 0) / magnitude)

        return RowVector(elements)

    # make homogenous 
    def homogenize(this):
        elements = copy.deepcopy(this.elements)
        elements.append(1.0)
        return RowVector(elements)
    
    # make not homogenous (for operations)
    def dehomogenize(this):
        elements = copy.deepcopy(this.elements)[:-1] # use slicing to get everything except last element 
        return RowVector(elements)
    
# This is to keep track of an entry in the edge table 
class EdgeEntry:

    edgeVerts = None 
    
    # general endpoints 
    xStart = None
    yStart = None
    yEnd = None 

    # polyfill and zbuffer data 
    dX = None 
    zStart = None
    dZ = None

    # gauroud shading
    gAStart = None
    gDStart = None
    gSStart = None
    gdA = None
    gdD = None 
    gdS = None

    # phong shading 
    pXStart = None
    pYStart = None
    pZStart = None
    pdX = None
    pdY = None
    pdZ = None

    # these fields will be filled out as they are calculated 
    def __init__(this, edgeName) -> None:
        this.edgeVerts = edgeName
        this.xStart = None
        this.yStart = None
        this.yEnd = None
        this.dX = None
        this.zStart = None
        this.dZ = None

#************************************************************************************

# This function resets the pyramid to its original size and location in 3D space
# Note that you have to be careful to update the values in the existing PyramidPointCloud
# structure rather than creating a new structure or just switching a pointer.  In other
# words, you'll need manually update the value of every x, y, and z of every point in
# point cloud (vertex list).
def resetObject(object: Object) -> None:
    for i in range(len(object.pointCloud)):
        for j in range(3):
            object.pointCloud[i][j] = object.defaultPointCloud[i][j]
    # also reset anchorPoint
    object.anchorPoint = findAnchorPoint(object)


# setup object 
# this function just sets the default position and resets the object
def setupObject(object: Object, position: Vector3) -> None:
    setDefaultPosition(object, position)
    resetObject(object)

# This function translates an object by some displacement.  The displacement is a 3D
# vector so the amount of displacement in each dimension can vary.
def translate(object: Object, displacement: Vector3) -> None:
    
    # add the displacement over the position in all dimensions 
    for point in object.pointCloud:
        for dimension in range(len(point)):
            point[dimension] = point[dimension] + displacement[dimension]
    
    # also modify the anchor 
    object.anchorPoint = [a + b for a, b in zip(object.anchorPoint, displacement)]
    
# This function performs a simple uniform scale of an object assuming the object is
# centered at the anchor point.  The scalefactor is a scalar.
def scale(object: Object, scalefactor: int) -> None:

    # scale with anchor displacement 
    for point in object.pointCloud:
        for dimension in range(len(point)):
            point[dimension] = ((point[dimension] - object.anchorPoint[dimension]) * scalefactor) + object.anchorPoint[dimension]

# This function performs a rotation of an object about the Z axis (from +X to +Y)
# by 'degrees', assuming the object is centered at the anchor point.  The rotation is CCW
# in a LHS when viewed from -Z [the location of the viewer in the standard postion]
def rotateZ(object: Object, degrees: float) -> None:

    radians = degrees * (math.pi / 180)
    
    for point in object.pointCloud:
        x = point[0] # have to record the original positions because the object will slowly shrink due to operations affecitng each other
        y = point[1]
        point[0] = ((x - object.anchorPoint[0]) * math.cos(radians) - (y - object.anchorPoint[1]) * math.sin(radians)) + object.anchorPoint[0] # X dimension 
        point[1] = ((x - object.anchorPoint[0]) * math.sin(radians) + (y - object.anchorPoint[1]) * math.cos(radians)) + object.anchorPoint[1] # Y dimension
        # Z is ignored 
    
# This function performs a rotation of an object about the Y axis (from +Z to +X)
# by 'degrees', assuming the object is centered at the anchor point.  The rotation is CW
# in a LHS when viewed from +Y looking toward the origin.
def rotateY(object: Object, degrees: float) -> None:
    
    radians = degrees * (math.pi / 180)

    for point in object.pointCloud:
        x = point[0]
        z = point[2]
        point[0] = ((x - object.anchorPoint[0]) * math.cos(radians) + (z - object.anchorPoint[2]) * math.sin(radians)) + object.anchorPoint[0]
        # Y is ignored 
        point[2] = (-(x - object.anchorPoint[0]) * math.sin(radians) + (z - object.anchorPoint[2]) * math.cos(radians)) + object.anchorPoint[2]

# This function performs a rotation of an object about the X axis (from +Y to +Z)
# by 'degrees', assuming the object is centered at the anchor point.  The rotation is CW
# in a LHS when viewed from +X looking toward the origin.
def rotateX(object: Object, degrees: float) -> None:
    
    radians = degrees * (math.pi / 180)

    for point in object.pointCloud:
        y = point[1]
        z = point[2]
        # X is ignored
        point[1] = ((y - object.anchorPoint[1]) * math.cos(radians) - (z - object.anchorPoint[2]) * math.sin(radians)) + object.anchorPoint[1]
        point[2] = ((y - object.anchorPoint[1]) * math.sin(radians) + (z - object.anchorPoint[2]) * math.cos(radians)) + object.anchorPoint[2]

# The function will draw an object by repeatedly callying drawLine on each line in each polygon in the object
# I decided it's not worth having a separate drawpoly function. Needless cruft in how I have arranged the types. 
# A poly is basically just an object with a single side anyway. 
def drawObject(window, object: Object, zBuffer: Matrix) -> None:
  
    for polyIndex in range(len(object.polygons)):

        poly = object.polygons[polyIndex]

        # check visibility (backface culling)
        if not polyIsVisible(object, poly):
            continue 

        # convert each poly into a set of 3D points
        # this is an ORDERED list
        points3D: list[Vector3] = []
        for p in poly:
            points3D.append(object.pointCloud[p])

        # project the points in this poly into display
        points_projected_plane = project(points3D, CAMERA_Z_OFFSET)
        points_projected_display = projectToDisplayCoordinates(points_projected_plane, CANVAS_WIDTH, CANVAS_HEIGHT)

        # round the coordinates 
        if ROUNDING:
            points_projected_display = roundVectorList(points_projected_display)

        # get surface normal
        # make proper vectors of edges p0 -> p1 and p1 -> p2 
        p0 = object.pointCloud[poly[0]]
        p1 = object.pointCloud[poly[1]]
        p2 = object.pointCloud[poly[2]]

        P = RowVector([a - b for a,b in zip(p1, p0)])
        Q = RowVector([a - b for a,b in zip(p2, p1)])

        # take the cross product of these vectors and normalize 
        N = P.cross(Q).normalize()

        # calculate flat shading once for this poly
        if SHADING_STYLE != NO_SHADING and (SHADING_STYLE == FLAT_SHADING or object.shadingOverride[polyIndex] == FLAT_SHADING):
            L = RowVector(L_LIST).normalize()
            V = RowVector(V_LIST).normalize()
            phong_intensity = phong_illuminate(ILLUMINATION_KD, ILLUMINATION_KS, SPEC_IND, AMBIENT_INT, DIFFUSE_INT, L, V, N)
            phong_color = triColorHex(phong_intensity[0], phong_intensity[1], phong_intensity[2])

        if POLY_FILL or BESPOKE_OUTLINE:
            # fill in this polygon
            colorIndex = object.polygons.index(poly)
            use_color = object.polyColor[colorIndex]
            if SHADING_STYLE != NO_SHADING and (SHADING_STYLE == FLAT_SHADING or object.shadingOverride[polyIndex] == FLAT_SHADING):
                use_color = phong_color
            polyFill(window, points_projected_display, zBuffer, object, poly, N, polyIndex, use_color, object.outlineColor)
    
        # make and draw each pair of points in order --> OUTLINE from tkinter
        if DEFAULT_OUTLINE:
            for p in range(len(points_projected_display) - 1):
                drawLine(window, points_projected_display[p], points_projected_display[p+1], object.outlineColor)
            drawLine(window, points_projected_display[-1], points_projected_display[0], object.outlineColor) # don't forget the last pair of points

# Fill in polygons function
# points come into the function pre-projected as proj
def polyFill(window, proj: list[Vector3], zBuffer: Matrix, object: Object, poly: Polygon, surfN: RowVector, polyIndex: int, polyColor='blue', objColor='black') -> None:

    # create edge table 
    edgeTable = computeEdgeTable(proj, object, poly, surfN)

    if edgeTable == []:
        return

    # determine all the start and end Y values for the whole poly
    firstY = edgeTable[0].yStart
    lastY = edgeTable[-1].yEnd

    # prepare indeces for scanning 
    i = 0
    j = 1
    next = 2

    # prepare x and z vaues of the first line that will be painted 
    edgeIX = edgeTable[i].xStart
    edgeJX = edgeTable[j].xStart
    edgeIZ = edgeTable[i].zStart
    edgeJZ = edgeTable[j].zStart
    # gouraud 
    edgeIGA = edgeTable[i].gAStart
    edgeJGA = edgeTable[j].gAStart
    edgeIGD = edgeTable[i].gDStart
    edgeJGD = edgeTable[j].gDStart
    edgeIGS = edgeTable[i].gSStart
    edgeJGS = edgeTable[j].gSStart
    # phong 
    edgeIPX = edgeTable[i].pXStart
    edgeJPX = edgeTable[j].pXStart
    edgeIPY = edgeTable[i].pYStart
    edgeJPY = edgeTable[j].pYStart
    edgeIPZ = edgeTable[i].pZStart
    edgeJPZ = edgeTable[j].pZStart

    # do painting loop 
    for y in range(int(firstY), int(lastY)): 

        # ensure stay on screen. update values and leave.
        if y not in range(0, CANVAS_HEIGHT):

            # update x and z values 
            edgeIX += edgeTable[i].dX
            edgeJX += edgeTable[j].dX
            edgeIZ += edgeTable[i].dZ
            edgeJZ += edgeTable[j].dZ
            if SHADING_STYLE != NO_SHADING:
                # gouraud 
                edgeIGA += edgeTable[i].gdA
                edgeJGA += edgeTable[j].gdA
                edgeIGD += edgeTable[i].gdD
                edgeJGD += edgeTable[j].gdD
                edgeIGS += edgeTable[i].gdS
                edgeJGS += edgeTable[j].gdS
                # phong 
                edgeIPX += edgeTable[i].pdX
                edgeJPX += edgeTable[j].pdX
                edgeIPY += edgeTable[i].pdY
                edgeJPY += edgeTable[j].pdY
                edgeIPZ += edgeTable[i].pdZ
                edgeJPZ += edgeTable[j].pdZ

            # reached the bottom of an edge, swap out
            if y >= edgeTable[i].yEnd and y < lastY:
                i = next
                edgeIX = edgeTable[i].xStart
                edgeIZ = edgeTable[i].zStart
                if SHADING_STYLE != NO_SHADING:
                    # gouraud
                    edgeIGA = edgeTable[i].gAStart
                    edgeIGD = edgeTable[i].gDStart
                    edgeIGS = edgeTable[i].gSStart
                    # phong
                    edgeIPX = edgeTable[i].pXStart
                    edgeIPY = edgeTable[i].pYStart
                    edgeIPZ = edgeTable[i].pZStart
                next += 1
            if y >= edgeTable[j].yEnd and y < lastY: 
                j = next
                edgeJX = edgeTable[j].xStart
                edgeJZ = edgeTable[j].zStart
                if SHADING_STYLE != NO_SHADING:
                    # gouraud 
                    edgeJGA = edgeTable[j].gAStart
                    edgeJGD = edgeTable[j].gDStart
                    edgeJGS = edgeTable[j].gSStart
                    # phong 
                    edgeJPX = edgeTable[j].pXStart
                    edgeJPY = edgeTable[j].pYStart
                    edgeJPZ = edgeTable[j].pZStart
                next += 1

            continue

        # find the leftness 
        if edgeIX < edgeJX:
            leftX = edgeIX
            rightX = edgeJX
            leftZ = edgeIZ
            rightZ = edgeJZ
            if SHADING_STYLE != NO_SHADING:
                # gouraud
                leftGA = edgeIGA
                rightGA = edgeJGA
                leftGD = edgeIGD
                rightGD = edgeJGD
                leftGS = edgeIGS
                rightGS = edgeJGS
                # phong 
                leftPX = edgeIPX
                rightPX = edgeJPX
                leftPY = edgeIPY
                rightPY = edgeJPY
                leftPZ = edgeIPZ
                rightPZ = edgeJPZ
        else: 
            leftX = edgeJX
            rightX = edgeIX
            leftZ = edgeJZ
            rightZ = edgeIZ
            if SHADING_STYLE != NO_SHADING:
                # gouraud 
                leftGA = edgeJGA
                rightGA = edgeIGA
                leftGD = edgeJGD
                rightGD = edgeIGD
                leftGS = edgeJGS
                rightGS = edgeIGS
                # phong 
                leftPX = edgeJPX
                rightPX = edgeIPX
                leftPY = edgeJPY
                rightPY = edgeIPY
                leftPZ = edgeJPZ
                rightPZ = edgeIPZ

        # initial z 
        z = leftZ
        if SHADING_STYLE != NO_SHADING:
            # initial gouraud intensity 
            GA = leftGA
            GD = leftGD
            GS = leftGS
            # inital phong normal
            PX = leftPX
            PY = leftPY
            PZ = leftPZ

        # compute dZ for this fill line
        if rightZ - leftZ != 0:
            dZFill = (rightZ - leftZ) / (rightX - leftX)
        else:
            dZFill = 0

        if SHADING_STYLE != NO_SHADING:
            # compute gouraud ambient for this fill line 
            if rightGA - leftGA != 0:
                dGAFill = (rightGA - leftGA) / (rightX - leftX)
            else:
                dGAFill = 0
            # compute gouraud diffuse for this fill line 
            if rightGD - leftGD != 0:
                dGDFill = (rightGD - leftGD) / (rightX - leftX)
            else:
                dGDFill = 0
            # compute gouraud specular for this fill line 
            if rightGS - leftGS != 0:
                dGSFill = (rightGS - leftGS) / (rightX - leftX)
            else:
                dGSFill = 0

            # compute phong X component for this fill line
            if rightPX - leftPX != 0:
                dPXFill = (rightPX - leftPX) / (rightX - leftX)
            else:
                dPXFill = 0
            # compute phong Y component for this fill line
            if rightPY - leftPY != 0:
                dPYFill = (rightPY - leftPY) / (rightX - leftX)
            else:
                dPYFill = 0
            # compute phong Z component for this fill line
            if rightPZ - leftPZ != 0:
                dPZFill = (rightPZ - leftPZ) / (rightX - leftX)
            else:
                dPZFill = 0

        # paint the line 
        # includes a little extra code to make the lines nice 
        for x in range(int(leftX), int(rightX)+1): # up to and including
            if x not in range(0, CANVAS_WIDTH): # ensure stay on screen
                z += dZFill
                if SHADING_STYLE != NO_SHADING:
                    GA += dGAFill
                    GD += dGDFill
                    GS += dGSFill
                    PX += dPXFill
                    PY += dPYFill
                    PZ += dPZFill
                continue

            if zBuffer.getElement(x, y) > z: # Z Buffer Check
                if POLY_FILL:
                    use_color = polyColor
                    if SHADING_STYLE == GOURAUD_SHADING and object.shadingOverride[polyIndex] != FLAT_SHADING: # gouraud check
                        use_color = triColorHex(GA, GD, GS)
                    if SHADING_STYLE == PHONG_SHADING and object.shadingOverride[polyIndex] != FLAT_SHADING:
                        L = RowVector(L_LIST).normalize()
                        V = RowVector(V_LIST).normalize()
                        N = RowVector([PX, PY, PZ]).normalize()
                        phong_ambient, phong_diffuse, phong_specular = phong_illuminate(ILLUMINATION_KD, ILLUMINATION_KS, SPEC_IND, AMBIENT_INT, DIFFUSE_INT, L, V, N)
                        use_color = triColorHex(phong_ambient, phong_diffuse, phong_specular)
                    drawPixel(window, x, y, use_color)

                if BESPOKE_OUTLINE:
                    if (x == int(leftX) or x == int(rightX) or y == int(firstY) or y == int(lastY)):
                        drawPixel(window, x, y, objColor)          

                zBuffer.setElement(x, y, z)

            z += dZFill
            if SHADING_STYLE != NO_SHADING:
                GA += dGAFill
                GD += dGDFill
                GS += dGSFill
                PX += dPXFill
                PY += dPYFill
                PZ += dPZFill

        # update x and z values 
        edgeIX += edgeTable[i].dX
        edgeJX += edgeTable[j].dX
        edgeIZ += edgeTable[i].dZ
        edgeJZ += edgeTable[j].dZ
        if SHADING_STYLE != NO_SHADING:
            # gouraud 
            edgeIGA += edgeTable[i].gdA
            edgeJGA += edgeTable[j].gdA
            edgeIGD += edgeTable[i].gdD
            edgeJGD += edgeTable[j].gdD
            edgeIGS += edgeTable[i].gdS
            edgeJGS += edgeTable[j].gdS
            # phong 
            edgeIPX += edgeTable[i].pdX
            edgeJPX += edgeTable[j].pdX
            edgeIPY += edgeTable[i].pdY
            edgeJPY += edgeTable[j].pdY
            edgeIPZ += edgeTable[i].pdZ
            edgeJPZ += edgeTable[j].pdZ

        # reached the bottom of an edge, swap out
        if y >= edgeTable[i].yEnd and y < lastY:
            i = next
            edgeIX = edgeTable[i].xStart
            edgeIZ = edgeTable[i].zStart
            if SHADING_STYLE != NO_SHADING:
                # gouraud
                edgeIGA = edgeTable[i].gAStart
                edgeIGD = edgeTable[i].gDStart
                edgeIGS = edgeTable[i].gSStart
                # phong
                edgeIPX = edgeTable[i].pXStart
                edgeIPY = edgeTable[i].pYStart
                edgeIPZ = edgeTable[i].pZStart
            next += 1
        if y >= edgeTable[j].yEnd and y < lastY: 
            j = next
            edgeJX = edgeTable[j].xStart
            edgeJZ = edgeTable[j].zStart
            if SHADING_STYLE != NO_SHADING:
                # gouraud 
                edgeJGA = edgeTable[j].gAStart
                edgeJGD = edgeTable[j].gDStart
                edgeJGS = edgeTable[j].gSStart
                # phong 
                edgeJPX = edgeTable[j].pXStart
                edgeJPY = edgeTable[j].pYStart
                edgeJPZ = edgeTable[j].pZStart
            next += 1

# helper to get the edge table constants
def computeEdgeTable(verts: list[Vector3], object: Object, poly: Polygon, surfN: RowVector) -> list[EdgeEntry]:
    
    # make edges from each neighbor, but in such a way that all edges flow from the top to the bottom
    # this way, we can compare the data in the edge table for sorting instead of the individual edges
    # this checking also guarantees that in horizonal edges, the leftmost vert is the first vert (due to clockwise definition)
    # we also do checking for horizontal edges here to prevent them entering the table
    edges = []
    for i in range(len(verts) - 1):
        if verts[i][1] != verts[i+1][1]:
            if verts[i][1] <= verts[i+1][1]:
                edges.append([verts[i], verts[i+1]])
            else:
                edges.append([verts[i+1], verts[i]])
    if verts[-1][1] != verts[0][1]:
        if verts[-1][1] <= verts[0][1]:
            edges.append([verts[-1], verts[0]])
        else:
            edges.append([verts[0], verts[-1]])

    # since our shape is convex we can guarantee that the next point down is the point to swap at 
    # therefore we can just sort edges now and make our edge entries
    edges.sort(key=lambda edge: edge[0][1])
    edgeTable = []
    for e in edges:
        entry = EdgeEntry(e)

        if SHADING_STYLE != NO_SHADING:
            projCloud = projectToDisplayCoordinates(project(object.pointCloud, CAMERA_Z_OFFSET), CANVAS_WIDTH, CANVAS_HEIGHT) 
            roundProjCloud = roundVectorList(projCloud)

            vert0_normal = RowVector([0.0, 0.0, 0.0])
            # find all polys that make use of this vertex and (conditionally) add their normals
            # manual search due to rounding...
            for i in range(len(roundProjCloud)):
                if areSimilarPoints(e[0], roundProjCloud[i]):
                    vertInd = i
                    break
            for p in range(len(object.polygons)):
                if vertInd in object.polygons[p] and object.shadingOverride[p] != FLAT_SHADING:
                    vert0_normal = vert0_normal.add(surfaceNormal(object, object.polygons[p]))
            vert0_normal = vert0_normal.normalize()

            vert1_normal = RowVector([0.0, 0.0, 0.0])
            # find all polys that make use of this vertex and (conditionally) add their normals
            # manual search due to rounding...
            for i in range(len(roundProjCloud)):
                if areSimilarPoints(e[1], roundProjCloud[i]):
                    vertInd = i
                    break
            for p in range(len(object.polygons)):
                if vertInd in object.polygons[p] and object.shadingOverride[p] != FLAT_SHADING:
                    vert1_normal = vert1_normal.add(surfaceNormal(object, object.polygons[p]))
            vert1_normal = vert1_normal.normalize()

            L = RowVector(L_LIST).normalize()
            V = RowVector(V_LIST).normalize()

        # fill in all statically calculated data - position and zbuf
        entry.xStart = e[0][0]
        entry.yStart = e[0][1]
        entry.yEnd = e[1][1]
        entry.dX = (e[1][0] - e[0][0]) / (e[1][1] - e[0][1]) # run over rise 
        entry.zStart = e[0][2]
        entry.dZ = (e[1][2] - e[0][2]) / (e[1][1] - e[0][1]) # the cooler run over rise
        
        if SHADING_STYLE != NO_SHADING:
            # fill in static data - gouraud shading
            vert0_ambient, vert0_diffuse, vert0_specular = phong_illuminate(ILLUMINATION_KD, ILLUMINATION_KS, SPEC_IND, AMBIENT_INT, DIFFUSE_INT, L, V, vert0_normal)
            vert1_ambient, vert1_diffuse, vert1_specular = phong_illuminate(ILLUMINATION_KD, ILLUMINATION_KS, SPEC_IND, AMBIENT_INT, DIFFUSE_INT, L, V, vert1_normal)
            entry.gAStart = vert0_ambient
            entry.gDStart = vert0_diffuse
            entry.gSStart = vert0_specular
            entry.gdA = ((vert1_ambient) - entry.gAStart) / (e[1][1] - e[0][1])
            entry.gdD = ((vert1_diffuse) - entry.gDStart) / (e[1][1] - e[0][1])
            entry.gdS = ((vert1_specular) - entry.gSStart) / (e[1][1] - e[0][1])

            # fill in the static data - phong shading
            entry.pXStart = vert0_normal.getElement(0, 0)
            entry.pYStart = vert0_normal.getElement(1, 0)
            entry.pZStart = vert0_normal.getElement(2, 0)
            entry.pdX = ((vert1_normal.getElement(0, 0)) - entry.pXStart) / (e[1][1] - e[0][1])
            entry.pdY = ((vert1_normal.getElement(1, 0)) - entry.pYStart) / (e[1][1] - e[0][1])
            entry.pdZ = ((vert1_normal.getElement(2, 0)) - entry.pZStart) / (e[1][1] - e[0][1])

        edgeTable.append(entry)

    return edgeTable
    

# Project the 3D endpoints to 2D point using a perspective projection implemented in 'project'
# Convert the projected endpoints to display coordinates via a call to 'convertToDisplayCoordinates'
# draw the actual line using the built-in create_line method
def drawLine(window, start: Vector3, end: Vector3, color="black") -> None:
    window.create_line(start[0], start[1], end[0], end[1], fill=color)

# Accounts for create_line requiring special parameters
def drawPixel(window, x, y, color="blue") -> None:
    window.create_line(x, y, x+1, y, fill=color)

# This function converts from 3D to 2D (+ depth) using the perspective projection technique.  Note that it
# will return a NEW list of points.  We will not want to keep around the projected points in our object as
# they are only used in rendering
# Assumes the viewer is at (0, 0, -distance), looking up the Z axis 
def project(points: list[Vector3], distance: float) -> list[Vector3]:
    
    ps = []
    
    for point in points:
        x_proj = distance * (point[0] / (distance + point[2]))
        y_proj = distance * (point[1] / (distance + point[2]))
        z_proj = distance * (point[2] / (distance + point[2]))
        ps.append([x_proj, y_proj, z_proj])

    return ps

# This function converts a 2D point to display coordinates in the tk system.  Note that it will return a
# NEW list of points.  We will not want to keep around the display coordinate points in our object as 
# they are only used in rendering.
# Assumes the center of the canvas is the origin of the original coordinates 
def projectToDisplayCoordinates(points: list[Vector2], width: int, height: int) -> list[Vector3]:
    
    displayXYZ = []

    for point in points:
        x_proj = (width / 2) + point[0]
        y_proj = (height / 2) - point[1]
        displayXYZ.append([x_proj, y_proj, point[2]]) # leave z in unaffected 

    return displayXYZ

# Check if two points occupy the same space 
# Useful for determining possible duplicate points in an object 
def areSimilarPoints(p1: Vector3, p2: Vector3) -> bool:
    for i in range(len(p1)):
        if p1[i] != p2[i]:
            return False
    return True

# a bounding box is defined by a pair of points 
# one point lies at the minimum of all dimensions of the object
# the other point lies at the maximum of all dimensions of the object 
# returns [maxVector3, minVector3]
def findBoundingBox(object: Object) -> list[Vector3]:
    max3 = [-9999, -9999, -9999] # start at "negative infinity"
    min3 = [9999, 9999, 9999] # start at "positive infinity"
    for point in object.pointCloud:
        for dimension in range(len(point)):
            # check max 
            if point[dimension] > max3[dimension]:
                max3[dimension] = point[dimension]
            # check min
            if point[dimension] < min3[dimension]:
                min3[dimension] = point[dimension]

    return [max3, min3]

# find the center of an object by the bounding box 
def findAnchorPoint(object: Object) -> Vector3:
    bounding_box = findBoundingBox(object)
    anchor_point = [0, 0, 0]
    for dimension in range(len(anchor_point)):
        max_dim = bounding_box[0][dimension]
        min_dim = bounding_box[1][dimension]
        anchor_point[dimension] = (max_dim + min_dim) / 2

    return anchor_point

# makes a vector negative in all dimensions
def negativeVector3(point: Vector3) -> Vector3:
    inverted = [0, 0, 0]
    for dimension in range(len(point)):
        inverted[dimension] = -point[dimension]
    return inverted

# helper for rounding vector coordinates
def roundVectorList(points: list) -> list:

    roundedList = []
    for p in points:
        roundedPoint = []
        for i in p:
            roundedPoint.append(float(round(i)))
        roundedList.append(roundedPoint)

    return roundedList

# sets the default position to the new location 
def setDefaultPosition(object: Object, position: Vector3) -> None:

    # get a copy of the current state so that we don't change the actual current position and orientation
    currentPointCloud = copy.deepcopy(object.pointCloud)
    currentAnchorPoint = copy.deepcopy(object.anchorPoint)

    # resetObject(object) # return object to original size/orientation so current modifications don't mess with new position
    translate(object, negativeVector3(object.anchorPoint)) # return to origin so current default position doesn't affect the new one
    translate(object, position) # go to the new default position 
    # set defaults 
    for i in range(len(object.defaultPointCloud)):
        for j in range(len(object.defaultPointCloud[i])):
            object.defaultPointCloud[i][j] = object.pointCloud[i][j]

    # return to how it was 
    object.pointCloud = currentPointCloud
    object.anchorPoint = currentAnchorPoint

# changes the selection, marked with red
def selectObject(index=0) -> None:
    global selected_object
    global selected_object_group

    if selected_object == None:
        selected_object = selected_object_group[0]

    selected_object.outlineColor = "black"
    selected_object = selected_object_group[index]
    selected_object.outlineColor = "red"

# resets everything and then draws the new frame
def drawAllObjects(window, object_group) -> None:

    # reset everything 
    window.delete(ALL)

    # reset zbuf
    zBuffer = Matrix(CANVAS_WIDTH, CANVAS_HEIGHT)
    for i in range(len(zBuffer.elements)):
        zBuffer.elements[i] = CAMERA_Z_OFFSET

    # draw
    for obj in object_group:
        drawObject(window, obj, zBuffer)

# backface culling 
def polyIsVisible(object: Object, poly: Polygon) -> bool:
    
    # make proper vectors of edges p0 -> p1 and p1 -> p2 
    p0 = object.pointCloud[poly[0]]
    p1 = object.pointCloud[poly[1]]
    p2 = object.pointCloud[poly[2]]

    P = RowVector([a - b for a,b in zip(p1, p0)])
    Q = RowVector([a - b for a,b in zip(p2, p1)])

    # take the cross product of these vectors and normalize 
    N = P.cross(Q).normalize()

    # now take the dot of N against a point in the plane 
    D = N.dot(RowVector(p0))

    # find the difference for visibility 
    vis = N.dot(RowVector([0, 0, -CAMERA_Z_OFFSET])) - D

    return (vis > 0)

# clamp values
def clamp(input, low, high):
    if input < low:
        return low
    if input > high:
        return high
    return input

# 20 spheres calcs

# illumination reflection vector R
def reflect(N: RowVector, L: RowVector) -> RowVector:
    R = []
    N = N.normalize()
    L = L.normalize()
    twoCosPhi = 2 * (N.getElement(0, 0) * L.getElement(0, 0) + \
                     N.getElement(1, 0) * L.getElement(1, 0) + \
                     N.getElement(2, 0) * L.getElement(2, 0))
    
    if twoCosPhi == 0:
        for i in range(3):
            R.append(-L.getElement(i, 0))
    elif twoCosPhi > 0: 
        for i in range(3):
            R.append(N.getElement(i, 0) - (L.getElement(i, 0) / twoCosPhi))
    else:
        for i in range(3):
            R.append(-N.getElement(i, 0) + (L.getElement(i, 0) / twoCosPhi))

    R = RowVector(R)

    return R.normalize()

# phong illumination from notes (render sphere)
def phong_illuminate(Kd: float, Ks: float, specIndex: float, Ia: float, Ip: float, L: RowVector, V: RowVector, N: RowVector) -> list[float]:
    
    # Normalize incoming vectors 
    L = L.normalize()
    V = V.normalize()
    N = N.normalize()

    ambient = Ia * Kd 

    NdotL = N.dot(L)

    if NdotL < 0:
        NdotL = 0

    diffuse = Ip * Kd * NdotL
    R = reflect(N, L)
    RdotV = R.dot(V)

    if RdotV < 0:
        RdotV = 0

    specular = Ip * Ks * RdotV ** specIndex

    return [ambient, diffuse, specular]

def surfaceNormal(object: Object, poly: Polygon) -> RowVector:
    # make proper vectors of edges p0 -> p1 and p1 -> p2 
    p0 = object.pointCloud[poly[0]]
    p1 = object.pointCloud[poly[1]]
    p2 = object.pointCloud[poly[2]]

    P = RowVector([a - b for a,b in zip(p1, p0)])
    Q = RowVector([a - b for a,b in zip(p2, p1)])

    # take the cross product of these vectors and normalize 
    N = P.cross(Q).normalize()

    return N

# color manipulations 
def triColorHex(ambient, diffuse, specular) -> str:
    combinedColorCode = colorHexCode(ambient + diffuse + specular)
    specularColorCode = colorHexCode(specular)
    colorString = f'#{specularColorCode}{combinedColorCode}{specularColorCode}'
    return colorString

def colorHexCode(intensity) -> str:
    hexString = str(hex(round(255 * intensity)))
    if hexString[0] == '-': # can't be negative
        print("Illumination is negative. Did you check for negative NdotL?")
        trimmedHexStr = '00'
    else:
        trimmedHexStr = hexString[2:]
        if len(trimmedHexStr) == 1:
            trimmedHexStr = f'0{trimmedHexStr}'

    return trimmedHexStr

# a bunch of functions for keyboard controls.....
# arrows for object selections
# numbers for mode selections 
def leftPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w 
    selectObject((selected_object_group.index(selected_object) - 1) % len(selected_object_group))
    drawAllObjects(w, selected_object_group)

def rightPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    selectObject((selected_object_group.index(selected_object) + 1) % len(selected_object_group))
    drawAllObjects(w, selected_object_group)

def onePressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE
    global SHADING_STYLE

    selected_object_group = object_group1
    SHADING_STYLE = NO_SHADING
    POLY_FILL = False
    if DEFAULT_OUTLINE:
        BESPOKE_OUTLINE = False
    elif BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = False
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, selected_object_group)

def twoPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE
    global SHADING_STYLE

    selected_object_group = object_group1
    SHADING_STYLE = NO_SHADING
    POLY_FILL = True
    if DEFAULT_OUTLINE:
        BESPOKE_OUTLINE = False
    elif BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = False
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, selected_object_group)

def threePressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE
    global SHADING_STYLE

    selected_object_group = object_group1
    SHADING_STYLE = NO_SHADING
    POLY_FILL = True
    DEFAULT_OUTLINE = False
    BESPOKE_OUTLINE = False
    drawAllObjects(w, selected_object_group)

def fourPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global SHADING_STYLE
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    SHADING_STYLE = FLAT_SHADING
    POLY_FILL = True
    DEFAULT_OUTLINE = False
    BESPOKE_OUTLINE = False
    selected_object_group = object_group2
    drawAllObjects(w, selected_object_group)

def fivePressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global SHADING_STYLE
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    SHADING_STYLE = GOURAUD_SHADING
    POLY_FILL = True
    DEFAULT_OUTLINE = False
    BESPOKE_OUTLINE = False
    selected_object_group = object_group2
    drawAllObjects(w, selected_object_group)

def sixPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global SHADING_STYLE
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    SHADING_STYLE = PHONG_SHADING
    POLY_FILL = True
    DEFAULT_OUTLINE = False
    BESPOKE_OUTLINE = False
    selected_object_group = object_group2
    drawAllObjects(w, selected_object_group)

# swap outline styles
def sevenPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    if DEFAULT_OUTLINE or BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = not DEFAULT_OUTLINE
        BESPOKE_OUTLINE = not DEFAULT_OUTLINE
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, selected_object_group)

# swap to oct wireframe
def eightPressed(event) -> None:
    global selected_object
    global selected_object_group
    global w
    global object_group1
    global object_group2
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    selected_object_group = object_group2
    POLY_FILL = False
    if DEFAULT_OUTLINE:
        BESPOKE_OUTLINE = False
    elif BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = False
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, selected_object_group)


# **************************************************************************
# Everything below this point implements the interface
def reset(window, object):
    global selected_object_group
    window.delete(ALL)
    for obj in selected_object_group:
        resetObject(obj)
    drawAllObjects(window, selected_object_group)

def setPosition(window, object):
    global selected_object_group
    window.delete(ALL)
    setDefaultPosition(object, object.anchorPoint)
    drawAllObjects(window, selected_object_group)

def larger(window, object):
    global selected_object_group
    window.delete(ALL)
    scale(object, 1.1)
    drawAllObjects(window, selected_object_group)

def smaller(window, object):
    global selected_object_group
    window.delete(ALL)
    scale(object, .9)
    drawAllObjects(window, selected_object_group)

def forward(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [0,0,5])
    drawAllObjects(window, selected_object_group)

def backward(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [0,0,-5])
    drawAllObjects(window, selected_object_group)

def left(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [-5,0,0])
    drawAllObjects(window, selected_object_group)

def right(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [5,0,0])
    drawAllObjects(window, selected_object_group)

def up(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [0,5,0])
    drawAllObjects(window, selected_object_group)

def down(window, object):
    global selected_object_group
    window.delete(ALL)
    translate(object, [0,-5,0])
    drawAllObjects(window, selected_object_group)

def xPlus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateX(object, 5)
    drawAllObjects(window, selected_object_group)

def xMinus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateX(object, -5)
    drawAllObjects(window, selected_object_group)

def yPlus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateY(object, 5)
    drawAllObjects(window, selected_object_group)

def yMinus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateY(object, -5)
    drawAllObjects(window, selected_object_group)

def zPlus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateZ(object, 5)
    drawAllObjects(window, selected_object_group)

def zMinus(window, object):
    global selected_object_group
    window.delete(ALL)
    rotateZ(object, -5)
    drawAllObjects(window, selected_object_group)

if __name__ == "__main__":

    # ***************************** Initialize Pyramid Object ***************************
    # Definition  of the five underlying points
    apex = [0,50,100]
    base1 = [50,-50,50]
    base2 = [50,-50,150]
    base3 = [-50,-50,150]
    base4 = [-50,-50,50]

    pyramidPoints = [apex, base1, base2, base3, base4]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    frontpoly = [0, 1, 4]
    rightpoly = [0, 2, 1]
    backpoly = [0, 3, 2]
    leftpoly = [0, 4, 3]
    bottompoly = [1, 2, 3, 4]

    pyramidPolys = [bottompoly, frontpoly, rightpoly, backpoly, leftpoly]
    pyramidPolyColors = ['black', 'red', 'green', 'blue', 'yellow']

    # create the tetrahedron object from defined data
    Pyramid1 = Object(pyramidPolys, pyramidPoints)
    Pyramid1.polyColor = pyramidPolyColors

    # give a default position away from the origin 
    setupObject(Pyramid1, [0, 0, 0])

    # ***************************** Initialize Tetrahedron Object ***************************
    # Definition  of the five underlying points
    tetra1_apex = [0,50,100]
    tetra1_base_right = [50,-50,50]
    tetra1_base_left = [-50,-50,50]
    tetra1_base_back = [0,-50,150]

    tetra1_points = [tetra1_apex, tetra1_base_right, tetra1_base_left, tetra1_base_back]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    tetra1_front_poly = [0, 1, 2]
    tetra1_right_poly = [0, 3, 1]
    tetra1_left_poly = [0, 2, 3]
    tetra1_bottom_poly = [2, 1, 3]

    tetra1_polys = [tetra1_front_poly, tetra1_right_poly, tetra1_left_poly, tetra1_bottom_poly]

    # create the tetrahedron object from defined data
    Tetrahedron1 = Object(tetra1_polys, tetra1_points)

    # give a default position away from the origin 
    setupObject(Tetrahedron1, [80, -80, 10])

    # ***************************** Initialize Cube1 Object ***************************
    # Definition  of the five underlying points
    cube1_front_bottom_left = [-40, -40, -40]
    cube1_front_bottom_right = [40, -40, -40]
    cube1_front_top_left = [-40, 40, -40]
    cube1_front_top_right = [40, 40, -40]
    cube1_back_bottom_left = [-40, -40, 40]
    cube1_back_bottom_right = [40, -40, 40]
    cube1_back_top_left = [-40, 40, 40]
    cube1_back_top_right = [40, 40, 40]

    cube1_points = [cube1_front_bottom_left, cube1_front_bottom_right, cube1_front_top_left, cube1_front_top_right, \
                    cube1_back_bottom_left, cube1_back_bottom_right, cube1_back_top_left, cube1_back_top_right]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    cube1_front_poly = [0, 2, 3, 1]
    cube1_right_poly = [1, 3, 7, 5]
    cube1_back_poly = [5, 7, 6, 4]
    cube1_left_poly = [4, 6, 2, 0]
    cube1_top_poly = [2, 6, 7, 3]
    cube1_bottom_poly = [4, 0, 1, 5]

    cube1_polys = [cube1_top_poly, cube1_front_poly, cube1_right_poly, cube1_back_poly, cube1_left_poly, cube1_bottom_poly]

    # create the tetrahedron object from defined data
    Cube1 = Object(cube1_polys, cube1_points)

    # give a default position away from the origin 
    setupObject(Cube1, [80, 60, 50])

    # ***************************** Initialize Cube2 Object ***************************
    # Definition  of the five underlying points
    cube2_front_bottom_left = [-40, -40, -40]
    cube2_front_bottom_right = [40, -40, -40]
    cube2_front_top_left = [-40, 40, -40]
    cube2_front_top_right = [40, 40, -40]
    cube2_back_bottom_left = [-40, -40, 40]
    cube2_back_bottom_right = [40, -40, 40]
    cube2_back_top_left = [-40, 40, 40]
    cube2_back_top_right = [40, 40, 40]

    cube2_points = [cube2_front_bottom_left, cube2_front_bottom_right, cube2_front_top_left, cube2_front_top_right, \
                    cube2_back_bottom_left, cube2_back_bottom_right, cube2_back_top_left, cube2_back_top_right]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    cube2_front_poly = [0, 2, 3, 1]
    cube2_right_poly = [1, 3, 7, 5]
    cube2_back_poly = [5, 7, 6, 4]
    cube2_left_poly = [4, 6, 2, 0]
    cube2_top_poly = [2, 6, 7, 3]
    cube2_bottom_poly = [4, 0, 1, 5]

    cube2_polys = [cube2_top_poly, cube2_front_poly, cube2_right_poly, cube2_back_poly, cube2_left_poly, cube2_bottom_poly]

    # create the tetrahedron object from defined data
    Cube2 = Object(cube2_polys, cube2_points)

    # give a default position away from the origin 
    setupObject(Cube2, [-80, 60, 50])

    # ***************************** Initialize TestPoly1 Object ***************************
    # Definition  of the five underlying points
    testpoly1_top = [0, 100, 0]
    testpoly1_left = [-100, 0, 0]
    testpoly1_right = [100, 0, 0]

    testpoly1_points = [testpoly1_top, testpoly1_right, testpoly1_left]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    testpoly1_front = [0, 1, 2]

    testpoly1_polys = [testpoly1_front]

    # create the tetrahedron object from defined data
    TestPoly1 = Object(testpoly1_polys, testpoly1_points)

    # give a default position away from the origin 
    setupObject(TestPoly1, [0,0,0])

    # ***************************** Initialize Oct Object ***************************
    # Definition  of the five underlying points
    oct_front_0 = [-50.0, 120.7107, 50.0]
    oct_front_1 = [50.0, 120.7107, 50.0]
    oct_front_2 = [120.7107, 50.0, 50.0]
    oct_front_3 = [120.7107, -50.0, 50.0]
    oct_front_4 = [50.0, -120.7107, 50.0]
    oct_front_5 = [-50.0, -120.7107, 50.0]
    oct_front_6 = [-120.7107, -50.0, 50.0]
    oct_front_7 = [-120.7107, 50.0, 50.0]

    oct_back_0 = [-50.0, 120.7107, 450.0]
    oct_back_1 = [50.0, 120.7107, 450.0]
    oct_back_2 = [120.7107, 50.0, 450.0]
    oct_back_3 = [120.7107, -50.0, 450.0]
    oct_back_4 = [50.0, -120.7107, 450.0]
    oct_back_5 = [-50.0, -120.7107, 450.0]
    oct_back_6 = [-120.7107, -50.0, 450.0]
    oct_back_7 = [-120.7107, 50.0, 450.0]

    oct_points = [oct_front_0, oct_front_1, oct_front_2, oct_front_3, oct_front_4, oct_front_5, oct_front_6, oct_front_7, \
                  oct_back_0, oct_back_1, oct_back_2, oct_back_3, oct_back_4, oct_back_5, oct_back_6, oct_back_7]

    # Definition of the five polygon faces using the meaningful point names
    # Polys are defined in clockwise order when viewed from the outside
    oct_poly_0 = [0, 8, 9, 1]
    oct_poly_1 = [1, 9, 10, 2]
    oct_poly_2 = [2, 10, 11, 3]
    oct_poly_3 = [3, 11, 12, 4]
    oct_poly_4 = [4, 12, 13, 5]
    oct_poly_5 = [5, 13, 14, 6]
    oct_poly_6 = [6, 14, 15, 7]
    oct_poly_7 = [7, 15, 8, 0]

    oct_poly_8 = [0, 1, 2, 3, 4, 5, 6, 7]
    oct_poly_9 = [15, 14, 13, 12, 11, 10, 9, 8]

    oct_polys = [oct_poly_0, oct_poly_1, oct_poly_2, oct_poly_3, oct_poly_4, \
                 oct_poly_5, oct_poly_6, oct_poly_7, oct_poly_8, oct_poly_9]

    # create the tetrahedron object from defined data
    Oct = Object(oct_polys, oct_points)
    Oct.polyColor = ['#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00', '#00FF00']
    Oct.shadingOverride = [None, None, None, None, None, None, None, None, FLAT_SHADING, FLAT_SHADING]

    # give a default position away from the origin 
    setupObject(Oct, [0,0,100])

    # ***************************** begin main instrucions *****************************
    root = Tk()
    outerframe = Frame(root)
    outerframe.pack()

    object_group1 = [Tetrahedron1, Pyramid1, Cube1, Cube2]
    object_group2 = [Oct]
    selected_object_group = object_group2
    selected_object = None
    selectObject() # by default selects the 0th object to start

    w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
    drawAllObjects(w, selected_object_group)
    w.pack()

    # keyboard input 
    root.bind("<Left>", leftPressed)
    root.bind("<Right>", rightPressed)
    root.bind("1", onePressed)
    root.bind("2", twoPressed)
    root.bind("3", threePressed)
    root.bind("4", fourPressed)
    root.bind("5", fivePressed)
    root.bind("6", sixPressed)
    root.bind("7", sevenPressed)
    root.bind("8", eightPressed)

    controlpanel = Frame(outerframe)
    controlpanel.pack()

    resetcontrols = Frame(controlpanel, height=100, borderwidth=2, relief=RIDGE)
    resetcontrols.pack(side=LEFT)

    resetcontrolslabel = Label(resetcontrols, text="Reset")
    resetcontrolslabel.pack()

    resetButton = Button(resetcontrols, text="Reset", fg="green", command=(lambda: reset(w, selected_object)))
    resetButton.pack(side=LEFT)

    setPositionButton = Button(resetcontrols, text="Set Default Position", command=(lambda: setPosition(w, selected_object)))
    setPositionButton.pack(side=LEFT)

    scalecontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    scalecontrols.pack(side=LEFT)

    scalecontrolslabel = Label(scalecontrols, text="Scale")
    scalecontrolslabel.pack()

    largerButton = Button(scalecontrols, text="Larger", command=(lambda: larger(w, selected_object)))
    largerButton.pack(side=LEFT)

    smallerButton = Button(scalecontrols, text="Smaller", command=(lambda: smaller(w, selected_object)))
    smallerButton.pack(side=LEFT)

    translatecontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    translatecontrols.pack(side=LEFT)

    translatecontrolslabel = Label(translatecontrols, text="Translation")
    translatecontrolslabel.pack()

    forwardButton = Button(translatecontrols, text="FW", command=(lambda: forward(w, selected_object)))
    forwardButton.pack(side=LEFT)

    backwardButton = Button(translatecontrols, text="BK", command=(lambda: backward(w, selected_object)))
    backwardButton.pack(side=LEFT)

    leftButton = Button(translatecontrols, text="LF", command=(lambda: left(w, selected_object)))
    leftButton.pack(side=LEFT)

    rightButton = Button(translatecontrols, text="RT", command=(lambda: right(w, selected_object)))
    rightButton.pack(side=LEFT)

    upButton = Button(translatecontrols, text="UP", command=(lambda: up(w, selected_object)))
    upButton.pack(side=LEFT)

    downButton = Button(translatecontrols, text="DN", command=(lambda: down(w, selected_object)))
    downButton.pack(side=LEFT)

    rotationcontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    rotationcontrols.pack(side=LEFT)

    rotationcontrolslabel = Label(rotationcontrols, text="Rotation")
    rotationcontrolslabel.pack()

    xPlusButton = Button(rotationcontrols, text="X+", command=(lambda: xPlus(w, selected_object)))
    xPlusButton.pack(side=LEFT)

    xMinusButton = Button(rotationcontrols, text="X-", command=(lambda: xMinus(w, selected_object)))
    xMinusButton.pack(side=LEFT)

    yPlusButton = Button(rotationcontrols, text="Y+", command=(lambda: yPlus(w, selected_object)))
    yPlusButton.pack(side=LEFT)

    yMinusButton = Button(rotationcontrols, text="Y-", command=(lambda: yMinus(w, selected_object)))
    yMinusButton.pack(side=LEFT)

    zPlusButton = Button(rotationcontrols, text="Z+", command=(lambda: zPlus(w, selected_object)))
    zPlusButton.pack(side=LEFT)

    zMinusButton = Button(rotationcontrols, text="Z-", command=(lambda: zMinus(w, selected_object)))
    zMinusButton.pack(side=LEFT)    

    root.mainloop()