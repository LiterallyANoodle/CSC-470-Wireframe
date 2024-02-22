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
T_MAX = 999999

ILLUMINATION_KD = 0.5
ILLUMINATION_KS = 0.5
SPEC_IND = 7.0
AMBIENT_INT = 0.4
DIFFUSE_INT = 0.7

AIR_DENSITY = 1.0
GLASS_DENSITY = 2.4
GAMMA_CORRECTION = 2
MAX_RAY_TRACE_DEPTH = 3

SKY_COLOR = [0.5, 0.5, 0.75]

L_LIST = [1, 1, -1]
V_LIST = [0, 0, -1]

# point type hint 
Vector3 = list[float, float, float]
Vector2 = list[float, float]

# primitives
class Primitive:

    # phong model
    Kd: float = None
    Ks: float = None
    spec_ind: int = None

    # pathing model
    local_weight: float = None
    refl_weight: float = None
    refr_weight: float = None

    def __init__(self, Kd: float, Ks: float, spec_ind: int, local_weight: float, refl_weight: float, refr_weight: float):
        self.Kd = Kd
        self.Ks = Ks
        self.spec_ind = spec_ind
        self.local_weight = local_weight
        self.refl_weight = refl_weight
        self.refr_weight = refr_weight

    def intersect(self, start, ray) -> list[float]:
        pass

class Plane(Primitive):
    
    # geometry
    normal: Vector3 = None
    anchor: Vector3 = None

    def __init__(self, normal: Vector3, anchor: Vector3, \
                 Kd: float, Ks: float, spec_ind: int, \
                 local_weight: float, refl_weight: float, refr_weight: float):
        
        super().__init__(Kd, Ks, spec_ind, local_weight, refl_weight, refr_weight)
        self.normal = normal
        self.anchor = anchor

class Sphere(Primitive):

    # geometry
    center: Vector3 = None
    r: float = None

    # Phong model 
    color: Vector3 = None

    # pathing model
    density: float = None

    def __init__(self, center: Vector3, r: float, \
                 color: Vector3, Kd: float, Ks: float, spec_ind: int, \
                 local_weight: float, refl_weight: float, refr_weight: float, density: float):
        
        super().__init__(Ks, Ks, spec_ind, local_weight, refl_weight, refr_weight)
        self.center = center
        self.r = r
        self.color = color
        self.density = density

# ***************************** Functionality ***************************
        
def trace_ray(start, ray, depth, object_list):

    # return black when at bottom
    if depth == 0: return [0,0,0]

    # attempt to intersect with all objects
    tMin = T_MAX
    intersection = None # point where intersect in 3d space
    for object in object_list:
        intersection_dict = object.intersect(start, ray)    # keys: t, vals: 3d point of intersection at t
        intersection_t = intersection_dict.keys()
        if intersection_t != []:
            for t in intersection_t:        
                if t < tMin:
                    tMin = t
                    nearest_object: Primitive = object
                    intersection = intersection_dict[t]

    # return sky color on intersection fail 
    if intersection == None: return SKY_COLOR

    # mix local color
    intensity = nearest_object.get_intensity()
    if in_shadow(nearest_object, intersection): intensity *= 0.25
    local_color = [c*GAMMA_CORRECTION for c in nearest_object.get_color(intersection)]
    local_weight = nearest_object.local_weight

    # mix local color and returned colors
    refl_color = trace_ray(intersection, nearest_object.reflect_ray(), depth-1)
    refr_color = trace_ray(intersection, nearest_object.refract_ray(), depth-1)

    final_color = [nearest_object.local_weight*local_color[c] + \
                   nearest_object.refl_weight*refl_color[c] + \
                   nearest_object.refr_weight*refr_color[c] \
                   for c in range(len(local_color))]
    
    return final_color

# detect shadowing
def in_shadow():
    pass

# The function will draw an object by repeatedly callying drawPoly on each polygon in the object
def drawObject(object):
    print("drawObject stub executed.")

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

# ***************************** Initialize Sphere1 Object ***************************

Sphere1 = Sphere([50, 25, 0], 50, [1.0, 0.0, 0.0], 0.5, 0.5, 8, 0.5, 0.25, 0.25, GLASS_DENSITY)
    

# **************************************************************************
# Everything below this point implements the interface

root = Tk()
outerframe = Frame(root)
outerframe.pack()

w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
object_list = [Sphere1]
drawObject(Sphere1)
w.pack()

controlpanel = Frame(outerframe)
controlpanel.pack()

root.mainloop()