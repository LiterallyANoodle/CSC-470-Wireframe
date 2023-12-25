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
CAMERA_Z_OFFSET = -500

# point type hint 
type Vector3 = list[float, float, float]
type Vector2 = list[float, float]

# Polygons type hint
# The polygon type does not actually hold any points in it, but rather references to points in the dictionary that is the object's pointcloud
# This is done to more elegantly prevent point duplication in the pointCloud 
type Polygon = list[int]

# Object Class 
class Object:

    polygons: list[Polygon] = []
    pointCloud: list[Vector3] = []
    defaultPointCloud: list[Vector3] = []

    anchorPoint: Vector3 = [0, 0, 0]

    def __init__(this, polygons, points, anchorPoint=None):
        this.polygons = polygons
        this.pointCloud = points
        this.defaultPointCloud = copy.deepcopy(points)
        
        this.anchorPoint = anchorPoint
        if anchorPoint == None:
            this.anchorPoint = findAnchorPoint(this)


#************************************************************************************

# This function resets the pyramid to its original size and location in 3D space
# Note that you have to be careful to update the values in the existing PyramidPointCloud
# structure rather than creating a new structure or just switching a pointer.  In other
# words, you'll need manually update the value of every x, y, and z of every point in
# point cloud (vertex list).
def resetObject(object):
    for i in range(len(object.pointCloud)):
        for j in range(3):
            object.pointCloud[i][j] = object.defaultPointCloud[i][j]


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
def rotateY(object, degrees):
    
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
def rotateX(object, degrees):
    
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
def drawObject(window, object: Object) -> None:

    for poly in object.polygons:
        # create each pair of points to be drawn as a line a
        pairs = []
        for i in range(len(poly) - 1):
            pairs.append([object.pointCloud[poly[i]], object.pointCloud[poly[i+1]]]) 
        # get the last connection
        pairs.append([object.pointCloud[poly[-1]], object.pointCloud[poly[0]]])

        for pair in pairs:
            points_proj_2d = project(pair, CAMERA_Z_OFFSET)
            drawLine(window, points_proj_2d[0], points_proj_2d[1])


# Project the 3D endpoints to 2D point using a perspective projection implemented in 'project'
# Convert the projected endpoints to display coordinates via a call to 'convertToDisplayCoordinates'
# draw the actual line using the built-in create_line method
def drawLine(window, start: Vector2, end: Vector2) -> None:
    
    start_proj, end_proj = projectToDisplayCoordinates([start, end], window.winfo_reqwidth(), window.winfo_reqheight())

    window.create_line(start_proj[0], start_proj[1], end_proj[0], end_proj[1])

# This function converts from 3D to 2D (+ depth) using the perspective projection technique.  Note that it
# will return a NEW list of points.  We will not want to keep around the projected points in our object as
# they are only used in rendering
# Assumes the viewer is at (0, 0, -distance), looking up the Z axis 
def project(points: list[Vector3], distance: float) -> list[Vector2]:
    
    ps = []
    
    for point in points:
        x_proj = distance * (point[0] / (distance + point[2]))
        y_proj = distance * (point[1] / (distance + point[2]))
        ps.append((x_proj, y_proj))

    return ps

# This function converts a 2D point to display coordinates in the tk system.  Note that it will return a
# NEW list of points.  We will not want to keep around the display coordinate points in our object as 
# they are only used in rendering.
# Assumes the center of the canvas is the origin of the original coordinates 
def projectToDisplayCoordinates(points: list[Vector2], width: int, height: int) -> list[Vector2]:
    
    displayXY = []

    for point in points:
        x_proj = (width / 2) + point[0]
        y_proj = (height / 2) - point[1]
        displayXY.append((x_proj, y_proj))

    return displayXY

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

# **************************************************************************
# Everything below this point implements the interface
def reset(window, object):
    window.delete(ALL)
    resetObject(object)
    drawObject(window, object)

def larger(window, object):
    window.delete(ALL)
    scale(object, 1.1)
    drawObject(window, object)

def smaller(window, object):
    window.delete(ALL)
    scale(object, .9)
    drawObject(window, object)

def forward(window, object):
    window.delete(ALL)
    translate(object, [0,0,5])
    drawObject(window, object)

def backward(window, object):
    window.delete(ALL)
    translate(object, [0,0,-5])
    drawObject(window, object)

def left(window, object):
    window.delete(ALL)
    translate(object, [-5,0,0])
    drawObject(window, object)

def right(window, object):
    window.delete(ALL)
    translate(object, [5,0,0])
    drawObject(window, object)

def up(window, object):
    window.delete(ALL)
    translate(object, [0,5,0])
    drawObject(window, object)

def down(window, object):
    window.delete(ALL)
    translate(object, [0,-5,0])
    drawObject(window, object)

def xPlus(window, object):
    window.delete(ALL)
    rotateX(object, 5)
    drawObject(window, object)

def xMinus(window, object):
    window.delete(ALL)
    rotateX(object, -5)
    drawObject(window, object)

def yPlus(window, object):
    window.delete(ALL)
    rotateY(object, 5)
    drawObject(window, object)

def yMinus(window, object):
    window.delete(ALL)
    rotateY(object, -5)
    drawObject(window, object)

def zPlus(window, object):
    window.delete(ALL)
    rotateZ(object, 5)
    drawObject(window, object)

def zMinus(window, object):
    window.delete(ALL)
    rotateZ(object, -5)
    drawObject(window, object)

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

    pyramidPolys = [frontpoly, rightpoly, backpoly, leftpoly, bottompoly]

    # create the tetrahedron object from defined data
    Pyramid1 = Object(pyramidPolys, pyramidPoints)

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

    # begin main instrucions 
    root = Tk()
    outerframe = Frame(root)
    outerframe.pack()

    object_group = [Tetrahedron1, Pyramid1]
    selected_object = Pyramid1

    w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
    for obj in object_group:
        drawObject(w, obj)
    w.pack()

    controlpanel = Frame(outerframe)
    controlpanel.pack()

    resetcontrols = Frame(controlpanel, height=100, borderwidth=2, relief=RIDGE)
    resetcontrols.pack(side=LEFT)

    resetcontrolslabel = Label(resetcontrols, text="Reset")
    resetcontrolslabel.pack()

    resetButton = Button(resetcontrols, text="Reset", fg="green", command=(lambda: reset(w, selected_object)))
    resetButton.pack(side=LEFT)

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