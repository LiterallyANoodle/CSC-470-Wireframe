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
CAMERA_POSITION = [0, 0, -CAMERA_Z_OFFSET]
T_MAX = 999999
HORIZON = 2000

AMBIENT_INT = 0.7
AIR_DENSITY = 1.0
GLASS_DENSITY = 2.4
GAMMA_CORRECTION = 2
MAX_RAY_TRACE_DEPTH = 4
LIGHT_INTENSITY = 1

SKY_COLOR = [0.7, 0.5, 1.0]
LIGHT_POSITION = [500, 500, 0]

# point type hint 
Vector3 = list[float, float, float]
Vector2 = list[float, float]

# primitives
# This is an abstract class
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
        print("Attempted to use Primitive Interface method.")
        return None
    
    def get_intensity(self, intersection, light, ray) -> float:
        print("Attempted to use Primitive Interface method.")
        return None
    
    def get_color(self, intersection) -> Vector3:
        print("Attempted to use Primitive Interface method.")
        return None
    
    def reflect_ray(self, ray, intersection) -> Vector3:
        print("Attempted to use Primitive Interface method.")
        return None

class Plane(Primitive):
    
    # geometry
    normal: Vector3 = None
    anchor: Vector3 = None

    # pathing model 
    # colors: list[Vector3] = [[1, 1, 1], [0.75, 0.10, 0.75]] # white and purple
    colors: list[Vector3] = [[1, 1, 1], [1.0, 0.0, 0.0]] # white and red
    checker_size: int = 100

    # constructor
    def __init__(self, normal: Vector3, anchor: Vector3, \
                 Kd: float, Ks: float, spec_ind: int, \
                 local_weight: float, refl_weight: float, refr_weight: float):
        
        super().__init__(Kd, Ks, spec_ind, local_weight, refl_weight, refr_weight)
        self.normal = normalize(normal)
        self.anchor = anchor

    # methods
    def intersect(self, start, ray) -> list[float]:
        [X1, Y1, Z1] = start
        [i, j, k] = ray
        D = dot(self.normal, self.anchor)
        numerator = -(dot(self.normal, start) - D)
        denominator = dot(self.normal, ray)
        if denominator == 0:
            return None
        t = numerator / denominator
        intersection = [X1 + i*t, Y1 + j*t, Z1 + k*t]
        if t < 0.001 or intersection[2] > HORIZON:  # ignore self, clipping planes
            return None
        return { t: intersection }
    
    def get_intensity(self, intersection, light_position, ray) -> float:
        
        distance = vector_distance(intersection, light_position)
        normal = normalize(self.normal)
        to_light = normalize(vector_sub(light_position, intersection))
        reflection = normalize(vector_reflect(normal, to_light))

        ambient = AMBIENT_INT * self.Kd
        diffuse = (LIGHT_INTENSITY * self.Kd * dot(normal, to_light)) / distance ** 2 # TODO: Check if realism is fine here
        specular = LIGHT_INTENSITY * self.Ks * (dot(reflection, normalize(vector_negate(ray))) ** self.spec_ind)

        return ambient + diffuse + specular
    
    def get_color(self, intersection) -> Vector3:
        [x, _, z] = intersection
        quotient_x = int(x // self.checker_size)  # in this house, we use modular arithmetic!
        quotient_z = int(z // self.checker_size)
        color_index = (quotient_x + quotient_z) % len(self.colors)
        return self.colors[color_index]
    
    def reflect_ray(self, ray, intersection) -> Vector3:
        return normalize(vector_reflect(normalize(self.normal), normalize(vector_negate(ray))))

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

    def intersect(self, start, ray) -> list[float]:
        [X1, Y1, Z1] = start
        [i, j, k] = ray
        [l, m, n] = self.center
        a = i**2 + j**2 + k**2
        b = dot(ray, vector_sub(start, self.center)) * 2
        c = (l**2 + m**2 + n**2) + \
            (X1**2 + Y1**2 + Z1**2) + \
            (2 * dot(vector_negate(self.center), start)) + \
            (-self.r ** 2)
        discriminant = (b**2) - (4 * a * c)
        if discriminant < 0:
            return None
        t0 = (-b + (discriminant ** 0.5)) / (2 * a)
        t1 = (-b - (discriminant ** 0.5)) / (2 * a)
        t = min(t0, t1)
        intersection = [ X1 + i*t, Y1 + j*t, Z1 + k*t ]
        if t < 0.001 or intersection[2] > HORIZON:  # ignore self, clipping planes
            return None
        return { t: intersection }
    
    def get_intensity(self, intersection, light_position, ray) -> float:
        
        distance = vector_distance(intersection, light_position)
        normal = normalize(vector_sub(intersection, self.center))
        to_light = normalize(vector_sub(light_position, intersection))
        reflection = vector_reflect(normal, to_light)
        NdotL = dot(normal, to_light)
        RdotV = dot(reflection, normalize(vector_negate(ray)))
        
        if NdotL < 0: NdotL = 0
        if RdotV < 0: RdotV = 0

        ambient = AMBIENT_INT * self.Kd
        diffuse = (LIGHT_INTENSITY * self.Kd * NdotL) / distance ** 2 # TODO: Check if realism is fine here
        specular = LIGHT_INTENSITY * self.Ks * (RdotV ** self.spec_ind)

        return ambient + diffuse + specular
    
    def get_color(self, intersection) -> Vector3:
        return self.color
    
    def reflect_ray(self, ray, intersection) -> Vector3:
        return normalize(vector_reflect(normalize(vector_sub(intersection, self.center)), normalize(vector_negate(ray))))

# ***************************** Functionality ***************************
        
def trace_ray(start: Vector3, ray: Vector3, depth: int, object_list: list[Primitive], light: Vector3) -> Vector3:

    # return black when at bottom
    if depth == 0: return [0,0,0]

    # attempt to intersect with all objects
    tMin = T_MAX
    intersection = None # point where intersect in 3d space
    for object in object_list:
        intersection_dict: dict = object.intersect(start, ray)    # keys: t, vals: 3d point of intersection at t
        if intersection_dict == None:
            continue
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
    intensity = nearest_object.get_intensity(intersection, light, ray)
    if in_shadow(nearest_object, intersection, object_list, light): intensity *= 0.25
    local_color = [c*GAMMA_CORRECTION*intensity for c in nearest_object.get_color(intersection)]

    # mix local color and returned colors
    refl_color = trace_ray(intersection, nearest_object.reflect_ray(ray, intersection), depth-1, object_list, light)
    # refr_color = trace_ray(intersection, nearest_object.refract_ray(ray), depth-1)

    final_color = [nearest_object.local_weight*local_color[c] + \
                   nearest_object.refl_weight*refl_color[c]  \
                #    nearest_object.refr_weight*refr_color[c] \
                   for c in range(len(local_color))]
    
    return final_color

# detect shadowing
def in_shadow(start_object: Primitive, start_point: Vector3, object_list: list[Primitive], light: Vector3) -> bool:
    ray = compute_unit_vector(start_point, light)
    for object in object_list:
        if object == start_object:
            continue
        if object.intersect(start_point, ray) != None:
            return True
    return False

def clamp(input: float, small: float, big: float) -> float:
    if input < small:
        return small
    elif input > big:
        return big
    else:
        return input

def RGB_hex(color: Vector3):
    color = [clamp(c, 0.0, 1.0) for c in color]
    # using floor instead of rounding because in previous assignments, rounding caused some strange banding
    RGB = [math.floor(c * 255) for c in color] 
    color_hexes = [f'{c:0>2x}'.format() for c in RGB]
    color_str = f'#{color_hexes[0]}{color_hexes[1]}{color_hexes[2]}'
    return color_str

def normalize(v: Vector3):
    mag = sum([c ** 2 for c in v]) ** 0.5
    return [c / mag for c in v]

def dot(v1: Vector3, v2: Vector3) -> float:
    return sum([c1 * c2 for c1, c2 in zip(v1, v2)])

def scalar_multiply(v: Vector3, s: float) -> Vector3:
    return [(c * s) for c in v]

def vector_add(v1: Vector3, v2: Vector3) -> Vector3:
    return [c1 + c2 for c1,c2 in zip(v1, v2)]

def vector_sub(v1: Vector3, v2: Vector3) -> Vector3:
    return [c1 - c2 for c1,c2 in zip(v1, v2)]

def vector_negate(v: Vector3) -> Vector3:
    return [-c for c in v]

def vector_distance(v1: Vector3, v2: Vector3) -> Vector3:
    return sum([(c2 - c1) ** 2 for c1, c2 in zip(v1, v2)]) ** 0.5

def vector_reflect(N, L) -> Vector3:
    N = normalize(N)
    L = normalize(L)
    two_cos_phi = 2 * dot(N, L)
    if two_cos_phi == 0:
        R = [-l for l in L]
    elif two_cos_phi > 0:
        R = [n - (l / two_cos_phi) for n,l in zip(N, L)]
    else:
        R = [-n + (l / two_cos_phi) for n,l in zip(N, L)]
    return normalize(R)

def compute_unit_vector(start, end):
    return normalize(vector_sub(end, start))

def render_image(w, light, object_list) -> None:

    illumination_saturation_counter = 0

    top = round(CANVAS_HEIGHT/2)
    bottom = round(-CANVAS_HEIGHT/2)
    left = round(-CANVAS_WIDTH/2)
    right = round(CANVAS_WIDTH/2)
    for y in range(top, bottom, -1):
        for x in range(left, right):
            ray = compute_unit_vector(CAMERA_POSITION, [x, y, 0]) # TODO: Check that this is correct to normalize
            color = trace_ray(CAMERA_POSITION, ray, MAX_RAY_TRACE_DEPTH, object_list, light)
            w.create_line(right+x, top-y, right+x+1, top-y, fill=RGB_hex(color))
    oversaturation = illumination_saturation_counter / (CANVAS_WIDTH*CANVAS_HEIGHT) * 100
    print(f"{illumination_saturation_counter} pixel color values were oversaturated: {oversaturation}%")

# ***************************** Initialize Objects ***************************

Plane1 = Plane([0,1,0], [0, -200, 0], 0.5, 0.5, 8, 0.5, 0.5, 0.25)
Sphere1 = Sphere([100, 0, 500], 200, \
                 color=[0.15, 0.55, 0.75], \
                 Kd=0.5, Ks=0.5, spec_ind=8, \
                 local_weight=0.3, refl_weight=0.7, refr_weight=0.25, density=GLASS_DENSITY)
Sphere2 = Sphere([-200, -100, 300], 100, \
                 color=[0.95, 0.50, 0.45], \
                 Kd=0.5, Ks=0.5, spec_ind=3, \
                 local_weight=0.85, refl_weight=0.15, refr_weight=0.25, density=GLASS_DENSITY)
Sphere3 = Sphere([0, -125, 100], 75, \
                 color=[0.45, 0.95, 0.55], \
                 Kd=0.5, Ks=0.5, spec_ind=3, \
                 local_weight=0.45, refl_weight=0.55, refr_weight=0.25, density=GLASS_DENSITY)

# **************************************************************************
# Everything below this point implements the interface

root = Tk()
outerframe = Frame(root)
outerframe.pack()

w = Canvas(outerframe, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
object_list = [Plane1, Sphere1, Sphere2, Sphere3]
w.pack()

controlpanel = Frame(outerframe)
controlpanel.pack()

render_image(w, LIGHT_POSITION, object_list)

root.mainloop()