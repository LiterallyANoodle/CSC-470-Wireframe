#######################################################################################
# Name: Matthew Mahan
# SID: 103 85 109
# Due Date: 1/9/2024
# Assignment Number: 1
# Desc: Program displays simple wireframes of primitive objects made of polygons with options for basic transformations.
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

DEFAULT_OUTLINE = True
BESPOKE_OUTLINE = not DEFAULT_OUTLINE
POLY_FILL = True
ROUNDING = True

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
    
class EdgeEntry:

    edgeName = None 
    
    xStart = None
    yStart = None
    yEnd = None 
    dX = None 
    zStart = None
    dZ = None

    # these fields will be filled out as they are calculated 
    def __init__(this, edgeName) -> None:
        this.edgeName = edgeName
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
  
    for poly in object.polygons:

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
        points_projected_display = projectToDisplayCoordinates(points_projected_plane, window.winfo_reqwidth(), window.winfo_reqheight())

        # round the coordinates 
        if ROUNDING:
            points_projected_display = roundVectorList(points_projected_display)

        if POLY_FILL or BESPOKE_OUTLINE:
            # fill in this polygon
            colorIndex = object.polygons.index(poly)
            polyFill(window, points_projected_display, zBuffer, object.polyColor[colorIndex], object.outlineColor)
    
        # make and draw each pair of points in order --> OUTLINE from tkinter
        if DEFAULT_OUTLINE:
            for p in range(len(points_projected_display) - 1):
                drawLine(window, points_projected_display[p], points_projected_display[p+1], object.outlineColor)
            drawLine(window, points_projected_display[-1], points_projected_display[0], object.outlineColor) # don't forget the last pair of points

# Fill in polygons function
# points come into the function pre-projected as proj
def polyFill(window, proj: list[Vector3], zBuffer: Matrix, polyColor='blue', objColor='black') -> None:

    # create edge table 
    edgeTable = computeEdgeTable(proj)

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

    # do painting loop 
    for y in range(int(firstY), int(lastY)): 

        # find the leftness 
        if edgeIX < edgeJX:
            leftX = edgeIX
            rightX = edgeJX
            leftZ = edgeIZ
            rightZ = edgeJZ
        else: 
            leftX = edgeJX
            rightX = edgeIX
            leftZ = edgeJZ
            rightZ = edgeIZ

        # initial z 
        z = leftZ

        # compute dZ for this fill line
        if rightZ - leftZ != 0:
            dZFill = (rightZ - leftZ) / (rightX - leftX)
        else:
            dZFill = 0

        # paint the line 
        for x in range(int(leftX), int(rightX)+1): # up to and including
            if zBuffer.getElement(x, y) > z: # Z Buffer Check
                if POLY_FILL:
                    drawPixel(window, x, y, polyColor)
                if BESPOKE_OUTLINE:
                    if (x == int(leftX) or x == int(rightX) or y == int(firstY) or y == int(lastY)):
                        drawPixel(window, x, y, objColor)          
                zBuffer.setElement(x, y, z)
            z += dZFill

        # update x and z values 
        edgeIX += edgeTable[i].dX
        edgeJX += edgeTable[j].dX
        edgeIZ += edgeTable[i].dZ
        edgeJZ += edgeTable[j].dZ

        # reached the bottom of an edge, swap out
        if y >= edgeTable[i].yEnd and y < lastY:
            i = next
            edgeIX = edgeTable[i].xStart
            edgeIZ = edgeTable[i].zStart
            next += 1
        if y >= edgeTable[j].yEnd and y < lastY: 
            j = next
            edgeJX = edgeTable[j].xStart
            edgeJZ = edgeTable[j].zStart
            next += 1

# helper to get the edge table constants
def computeEdgeTable(verts: list[Vector3]) -> list[EdgeEntry]:
    
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

        # fill in all statically calculated data 
        entry.xStart = e[0][0]
        entry.yStart = e[0][1]
        entry.yEnd = e[1][1]
        entry.dX = (e[1][0] - e[0][0]) / (e[1][1] - e[0][1]) # run over rise 
        entry.zStart = e[0][2]
        entry.dZ = (e[1][2] - e[0][2]) / (e[1][1] - e[0][1]) # the cooler run over rise

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

# Linear interpolation 
# Returns a list of numbers that are linearly evenly spaced out 
# The length of the list is determined by the number of steps requested
# Because no libraries may be imported, we cannot use time to make this framerate independent. "steps" is effectively how many frames it should take, which will be very fast.
def lerp(start: float, end: float, steps: int) -> list[float]:

    intermediates = []

    stepSize = (end - start) / steps
    
    for step in range(steps):
        intermediates.append(step * stepSize + start)
    # manually append the final state to ensure there's no floating point rounding error shenannigans
    intermediates.append(float(end))

    return intermediates

# Check if two points occupy the same space 
# Useful for determining possible duplicate points in an object 
def areSimilarPoints(p1: Vector3, p2: Vector3) -> bool:
    for i in len(p1):
        if p1[i] != p2[2]:
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

def selectObject(index=0) -> None:
    global selected_object
    global object_group

    if selected_object == None:
        selected_object = object_group[0]

    selected_object.outlineColor = "black"
    selected_object = object_group[index]
    selected_object.outlineColor = "red"

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

def leftPressed(event) -> None:
    global selected_object
    global object_group
    global w 
    selectObject((object_group.index(selected_object) - 1) % len(object_group))
    drawAllObjects(w, object_group)

def rightPressed(event) -> None:
    global selected_object
    global object_group
    global w
    selectObject((object_group.index(selected_object) + 1) % len(object_group))
    drawAllObjects(w, object_group)

def onePressed(event) -> None:
    global selected_object
    global object_group
    global w
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    POLY_FILL = False
    if DEFAULT_OUTLINE:
        BESPOKE_OUTLINE = False
    elif BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = False
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, object_group)

def twoPressed(event) -> None:
    global selected_object
    global object_group
    global w
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    POLY_FILL = True
    if DEFAULT_OUTLINE:
        BESPOKE_OUTLINE = False
    elif BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = False
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, object_group)

def threePressed(event) -> None:
    global selected_object
    global object_group
    global w
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    POLY_FILL = True
    DEFAULT_OUTLINE = False
    BESPOKE_OUTLINE = False
    drawAllObjects(w, object_group)

def fourPressed(event) -> None:
    global selected_object
    global object_group
    global w
    global POLY_FILL
    global DEFAULT_OUTLINE
    global BESPOKE_OUTLINE

    if DEFAULT_OUTLINE or BESPOKE_OUTLINE:
        DEFAULT_OUTLINE = not DEFAULT_OUTLINE
        BESPOKE_OUTLINE = not DEFAULT_OUTLINE
    else:
        DEFAULT_OUTLINE = True
    drawAllObjects(w, object_group)


# **************************************************************************
# Everything below this point implements the interface
def reset(window, object):
    global object_group
    window.delete(ALL)
    for obj in object_group:
        resetObject(obj)
    drawAllObjects(window, object_group)

def setPosition(window, object):
    global object_group
    window.delete(ALL)
    setDefaultPosition(object, object.anchorPoint)
    drawAllObjects(window, object_group)

def larger(window, object):
    global object_group
    window.delete(ALL)
    scale(object, 1.1)
    drawAllObjects(window, object_group)

def smaller(window, object):
    global object_group
    window.delete(ALL)
    scale(object, .9)
    drawAllObjects(window, object_group)

def forward(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [0,0,5])
    drawAllObjects(window, object_group)

def backward(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [0,0,-5])
    drawAllObjects(window, object_group)

def left(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [-5,0,0])
    drawAllObjects(window, object_group)

def right(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [5,0,0])
    drawAllObjects(window, object_group)

def up(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [0,5,0])
    drawAllObjects(window, object_group)

def down(window, object):
    global object_group
    window.delete(ALL)
    translate(object, [0,-5,0])
    drawAllObjects(window, object_group)

def xPlus(window, object):
    global object_group
    window.delete(ALL)
    rotateX(object, 5)
    drawAllObjects(window, object_group)

def xMinus(window, object):
    global object_group
    window.delete(ALL)
    rotateX(object, -5)
    drawAllObjects(window, object_group)

def yPlus(window, object):
    global object_group
    window.delete(ALL)
    rotateY(object, 5)
    drawAllObjects(window, object_group)

def yMinus(window, object):
    global object_group
    window.delete(ALL)
    rotateY(object, -5)
    drawAllObjects(window, object_group)

def zPlus(window, object):
    global object_group
    window.delete(ALL)
    rotateZ(object, 5)
    drawAllObjects(window, object_group)

def zMinus(window, object):
    global object_group
    window.delete(ALL)
    rotateZ(object, -5)
    drawAllObjects(window, object_group)

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

    # ***************************** begin main instrucions *****************************
    root = Tk()
    outerframe = Frame(root)
    outerframe.pack()

    object_group = [Tetrahedron1, Pyramid1, Cube1, Cube2]
    selected_object = None
    selectObject() # by default selects the 0th object to start

    w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
    drawAllObjects(w, object_group)
    w.pack()

    # keyboard input 
    root.bind("<Left>", leftPressed)
    root.bind("<Right>", rightPressed)
    root.bind("1", onePressed)
    root.bind("2", twoPressed)
    root.bind("3", threePressed)
    root.bind("4", fourPressed)

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