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
type Point3 = tuple[float, float, float]

# Polygons Class 
# The polygon class does not actually hold any points in it, but rather references to points in the dictionary that is the object's pointcloud
# This is done to more elegantly prevent point duplication in the pointCloud 
class Polygon:
    points: list[int] = []
    def __init__(this, points):
        this.points = points

# Object Class 
class Object:
    polygons: list[Polygon] = []
    pointCloud: list[Point3] = []
    defaultPointCloud: list[Point3] = []
    def __init__(this, polygons, points):
        this.polygons = polygons
        this.pointCloud = points
        this.defaultPointCloud = copy.deepcopy(points)


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
def translate(object, displacement):
    print("translate stub executed.")
    
# This function performs a simple uniform scale of an object assuming the object is
# centered at the origin.  The scalefactor is a scalar.
def scale(object, scalefactor):
    print("scale stub executed.")

# This function performs a rotation of an object about the Z axis (from +X to +Y)
# by 'degrees', assuming the object is centered at the origin.  The rotation is CCW
# in a LHS when viewed from -Z [the location of the viewer in the standard postion]
def rotateZ(object, degrees):
    print("rotateZ stub executed.")
    
# This function performs a rotation of an object about the Y axis (from +Z to +X)
# by 'degrees', assuming the object is centered at the origin.  The rotation is CW
# in a LHS when viewed from +Y looking toward the origin.
def rotateY(object, degrees):
    print("rotateY stub executed.")

# This function performs a rotation of an object about the X axis (from +Y to +Z)
# by 'degrees', assuming the object is centered at the origin.  The rotation is CW
# in a LHS when viewed from +X looking toward the origin.
def rotateX(object, degrees):
    print("rotateX stub executed.")

# The function will draw an object by repeatedly callying drawPoly on each polygon in the object
def drawObject(object):
    print("drawObject stub executed.")

# This function will draw a polygon by repeatedly callying drawLine on each pair of points
# making up the object.  Remember to draw a line between the last point and the first.
def drawPoly(poly):
    print("drawPoly stub executed.")

# Project the 3D endpoints to 2D point using a perspective projection implemented in 'project'
# Convert the projected endpoints to display coordinates via a call to 'convertToDisplayCoordinates'
# draw the actual line using the built-in create_line method
def drawLine(start, end):
    #        window.create_line(startdisplay[0],startdisplay[1],enddisplay[0],enddisplay[1])
    print("drawLine stub executed.")

# This function converts from 3D to 2D (+ depth) using the perspective projection technique.  Note that it
# will return a NEW list of points.  We will not want to keep around the projected points in our object as
# they are only used in rendering
def project(point):
    ps = []
    # some stuff happens
    return ps

# This function converts a 2D point to display coordinates in the tk system.  Note that it will return a
# NEW list of points.  We will not want to keep around the display coordinate points in our object as 
# they are only used in rendering.
def convertToDisplayCoordinates(point):
    displayXY = []
    # some stuff happens
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
def areSimilarPoints(p1: Point3, p2: Point3) -> bool:
    for i in len(p1):
        if p1[i] != p2[2]:
            return False
    return True
        

# **************************************************************************
# Everything below this point implements the interface
def reset(window, object):
    window.delete(ALL)
    resetObject(object)
    drawObject(object)

def larger(window, object):
    window.delete(ALL)
    scale(object.pointCloud, 1.1)
    drawObject(object)

def smaller(window, object):
    window.delete(ALL)
    scale(object.pointCloud, .9)
    drawObject(object)

def forward(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [0,0,5])
    drawObject(object)

def backward(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [0,0,-5])
    drawObject(object)

def left(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [-5,0,0])
    drawObject(object)

def right(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [5,0,0])
    drawObject(object)

def up(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [0,5,0])
    drawObject(object)

def down(window, object):
    window.delete(ALL)
    translate(object.pointCloud, [0,-5,0])
    drawObject(object)

def xPlus(window, object):
    window.delete(ALL)
    rotateX(object.pointCloud, 5)
    drawObject(object)

def xMinus(window, object):
    window.delete(ALL)
    rotateX(object.pointCloud, -5)
    drawObject(object)

def yPlus(window, object):
    window.delete(ALL)
    rotateY(object.pointCloud, 5)
    drawObject(object)

def yMinus(window, object):
    window.delete(ALL)
    rotateY(object.pointCloud, -5)
    drawObject(object)

def zPlus(window, object):
    window.delete(ALL)
    rotateZ(object.pointCloud, 5)
    drawObject(object)

def zMinus(window, object):
    window.delete(ALL)
    rotateZ(object.pointCloud, -5)
    drawObject(object)

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

    # create the pyramid object from defined data
    Pyramid1 = Object(pyramidPolys, pyramidPoints)

    root = Tk()
    outerframe = Frame(root)
    outerframe.pack()

    w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    drawObject(Pyramid1)
    w.pack()

    controlpanel = Frame(outerframe)
    controlpanel.pack()

    resetcontrols = Frame(controlpanel, height=100, borderwidth=2, relief=RIDGE)
    resetcontrols.pack(side=LEFT)

    resetcontrolslabel = Label(resetcontrols, text="Reset")
    resetcontrolslabel.pack()

    resetButton = Button(resetcontrols, text="Reset", fg="green", command=(lambda : reset(w)))
    resetButton.pack(side=LEFT)

    scalecontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    scalecontrols.pack(side=LEFT)

    scalecontrolslabel = Label(scalecontrols, text="Scale")
    scalecontrolslabel.pack()

    largerButton = Button(scalecontrols, text="Larger", command=(lambda: larger(w)))
    largerButton.pack(side=LEFT)

    smallerButton = Button(scalecontrols, text="Smaller", command=(lambda: smaller(w)))
    smallerButton.pack(side=LEFT)

    translatecontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    translatecontrols.pack(side=LEFT)

    translatecontrolslabel = Label(translatecontrols, text="Translation")
    translatecontrolslabel.pack()

    forwardButton = Button(translatecontrols, text="FW", command=(lambda: forward(w)))
    forwardButton.pack(side=LEFT)

    backwardButton = Button(translatecontrols, text="BK", command=(lambda: backward(w)))
    backwardButton.pack(side=LEFT)

    leftButton = Button(translatecontrols, text="LF", command=(lambda: left(w)))
    leftButton.pack(side=LEFT)

    rightButton = Button(translatecontrols, text="RT", command=(lambda: right(w)))
    rightButton.pack(side=LEFT)

    upButton = Button(translatecontrols, text="UP", command=(lambda: up(w)))
    upButton.pack(side=LEFT)

    downButton = Button(translatecontrols, text="DN", command=(lambda: down(w)))
    downButton.pack(side=LEFT)

    rotationcontrols = Frame(controlpanel, borderwidth=2, relief=RIDGE)
    rotationcontrols.pack(side=LEFT)

    rotationcontrolslabel = Label(rotationcontrols, text="Rotation")
    rotationcontrolslabel.pack()

    xPlusButton = Button(rotationcontrols, text="X+", command=(lambda: xPlus(w)))
    xPlusButton.pack(side=LEFT)

    xMinusButton = Button(rotationcontrols, text="X-", command=(lambda: xMinus(w)))
    xMinusButton.pack(side=LEFT)

    yPlusButton = Button(rotationcontrols, text="Y+", command=(lambda: yPlus(w)))
    yPlusButton.pack(side=LEFT)

    yMinusButton = Button(rotationcontrols, text="Y-", command=(lambda: yMinus(w)))
    yMinusButton.pack(side=LEFT)

    zPlusButton = Button(rotationcontrols, text="Z+", command=(lambda: zPlus(w)))
    zPlusButton.pack(side=LEFT)

    zMinusButton = Button(rotationcontrols, text="Z-", command=(lambda: zMinus(w)))
    zMinusButton.pack(side=LEFT)

    root.mainloop()