#######################################################################################
# Name: Matthew Mahan
# SID: 103 85 109
# Due Date: 2/27/2024
# Assignment Number: 4
# Desc: Program displays a scene rendered using ray tracing techniques. 
#######################################################################################

# ****NOTE: This framework defines a world with a single polygon: a pyramid ****
#

import math
import copy
from tkinter import *

CANVAS_WIDTH = 400
CANVAS_HEIGHT = 400
CAMERA_Z_OFFSET = 500

ILLUMINATION_KD = 0.5
ILLUMINATION_KS = 0.5
SPEC_IND = 7.0
AMBIENT_INT = 0.4
DIFFUSE_INT = 0.7

L_LIST = [1, 1, -1]
V_LIST = [0, 0, -1]

# point type hint 
Vector3 = list[float, float, float]
Vector2 = list[float, float]

# primitives
class Plane:
    
    # geometry
    normal: Vector3 = None
    anchor: Vector3 = None

    # phong model
    Kd: float = None
    Ks: float = None
    spec_ind: int = None

    # pathing model
    local_weight: float = None
    refl_weight: float = None

    def __init__(self, normal: Vector3, anchor: Vector3, \
                 Kd: float, Ks: float, spec_ind: int, \
                 local_weight: float, refl_weight: float):
        
        self.normal = normal
        self.anchor = anchor
        self.Kd = Kd
        self.Ks = Ks
        self.spec_ind = spec_ind
        self.local_weight = local_weight
        self.refl_weight = refl_weight

class Sphere:

    # geometry
    center: Vector3 = None
    r: float = None

    # Phong model 
    color: Vector3 = None
    Kd: float = None
    Ks: float = None
    spec_ind: int = None

    # pathing model
    local_weight: float = None
    refl_weight: float = None 
    density: float = None

    def __init__(self, center: Vector3, r: float, \
                 color: Vector3, Kd: float, Ks: float, spec_ind: int, \
                 local_weight: float, refl_weight: float):
        
        self.center = center
        self.r = r
        self.color = color
        self.Kd = Kd
        self.Ks = Ks
        self.spec_ind = spec_ind
        self.local_weight = local_weight
        self.refl_weight = refl_weight

# ***************************** Initialize Sphere1 Object ***************************

Sphere1 = 0

#************************************************************************************

# The function will draw an object by repeatedly callying drawPoly on each polygon in the object
def drawObject(object):
    print("drawObject stub executed.")

# This function will draw a polygon by repeatedly callying drawLine on each pair of points
# making up the object.  Remember to draw a line between the last point and the first.
def drawPoly(poly):
    print("drawPoly stub executed.")

# This function converts from 3D to 2D (+ depth) using the perspective projection technique.  Note that it
# will return a NEW list of points.  We will not want to keep around the projected points in our object as
# they are only used in rendering
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
def projectToDisplayCoordinates(points: list[Vector2], width: int, height: int) -> list[Vector3]:
    
    displayXYZ = []

    for point in points:
        x_proj = (width / 2) + point[0]
        y_proj = (height / 2) - point[1]
        displayXYZ.append([x_proj, y_proj, point[2]]) # leave z in unaffected 

    return displayXYZ
    

# **************************************************************************
# Everything below this point implements the interface

root = Tk()
outerframe = Frame(root)
outerframe.pack()

w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
drawObject(Sphere1)
w.pack()

controlpanel = Frame(outerframe)
controlpanel.pack()

root.mainloop()