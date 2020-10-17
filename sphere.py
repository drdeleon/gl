import glMath
from gl import color, V3, V4

from numpy import arccos, arctan2, pi

OPAQUE = 0
REFLECTIVE = 1
TRANSPARENT = 2

WHITE = color(1,1,1)

class AmbientLight(object):
    def __init__(self, strength = 0, _color = WHITE):
        self.strength = strength
        self.color = _color

class DirectionalLight(object):
    def __init__(self, direction = V3(0,-1,0), _color = WHITE, intensity = 1):
        self.direction = glMath.normalize(direction)
        self.intensity = intensity
        self.color = _color

class PointLight(object):
    def __init__(self, position = V3(0,0,0), _color = WHITE, intensity = 1):
        self.position = position
        self.intensity = intensity
        self.color = _color

class Material(object):
    """
    Un material es un conjunto de propiedade que determina cómo interactúa la iluminación con una superficie. En raytracing, el color de un pixel es determinado por el material de la superficie que un rayo intersecta.
    """
    def __init__(self, diffuse = WHITE, spec = 0, ior = 1, texture = None, matType = OPAQUE):
        # Diffuse es el color basico de un objeto. Cuando recibe luz, se esparce por igual en todas las direcciones.
        self.diffuse = diffuse
        self.spec = spec

        self.matType = matType
        self.ior = ior
        self.texture = texture

class Intersect(object):
    def __init__(self, distance, point, normal, texCoords, sceneObject):
        self.distance = distance
        self.point = point
        self.normal = normal
        
        self.texCoords = texCoords

        self.sceneObject = sceneObject

class Sphere(object):
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material

    def ray_intersect(self, orig, dir):
        # Formula para un punto en un rayo
        # t es igual a la distancia en el rayo
        # P = O + tD
        # P0 = O + t0 * D
        # P1 = O + t1 * D
        #d va a ser la magnitud de un vector que es
        #perpendicular entre el rayo y el centro de la esfera
        # d > radio, el rayo no intersecta
        #tca es el vector que va del orign al punto perpendicular al centro
        L = glMath.substract(self.center, orig)
        tca = glMath.dot_product(L, dir)
        l = glMath.norm(L) # magnitud de L
        d = (l**2 - tca**2) ** 0.5
        if d > self.radius:
            return None

        # thc es la distancia de P1 al punto perpendicular al centro
        thc = (self.radius ** 2 - d**2) ** 0.5
        t0 = tca - thc
        t1 = tca + thc
        if t0 < 0:
            t0 = t1

        if t0 < 0: # t0 tiene el valor de t1
            return None

        # P = O + tD
        hit = glMath.add(orig, glMath.multiply(t0,list(dir)))
        norm = glMath.substract(hit, self.center)
        norm = glMath.normalize(norm)

        u = 1 - (arctan2( norm[2], norm[0]) / (2 * pi) + 0.5)
        v =  arccos(-norm[1]) / pi

        uvs = [u, v]



        return Intersect(distance = t0,
                         point = hit,
                         normal = norm,
                         texCoords = uvs,
                         sceneObject = self)


class Plane(object):
    def __init__(self, position, normal, material):
        self.position = position
        self.normal = glMath.normalize(normal)
        self.material = material

    def ray_intersect(self, orig, dir):
        # t = (( position - origRayo) dot normal) / (dirRayo dot normal)

        denom = glMath.dot_product(dir, self.normal)

        if abs(denom) > 0.0001:
            t = glMath.dot_product(self.normal, glMath.substract(self.position, orig)) / denom
            if t > 0:
                # P = O + tD
                hit = glMath.add(orig, glMath.multiply(t, list(dir)))

                return Intersect(distance = t,
                                 point = hit,
                                 normal = self.normal,
                                 texCoords = None,
                                 sceneObject = self)

        return None


# Cubos
# AA Bounding Box: axis adjacent Bounding Box
class AABB(object):
    def __init__(self, position, size, material):
        self.position = position
        self.size = size
        self.material = material
        self.planes = []

        halfSizeX = size[0] / 2
        halfSizeY = size[1] / 2
        halfSizeZ = size[2] / 2

        self.planes.append( Plane( glMath.add(position, V3(halfSizeX,0,0)), V3(1,0,0), material))
        self.planes.append( Plane( glMath.add(position, V3(-halfSizeX,0,0)), V3(-1,0,0), material))

        self.planes.append( Plane( glMath.add(position, V3(0,halfSizeY,0)), V3(0,1,0), material))
        self.planes.append( Plane( glMath.add(position, V3(0,-halfSizeY,0)), V3(0,-1,0), material))

        self.planes.append( Plane( glMath.add(position, V3(0,0,halfSizeZ)), V3(0,0,1), material))
        self.planes.append( Plane( glMath.add(position, V3(0,0,-halfSizeZ)), V3(0,0,-1), material))


    def ray_intersect(self, orig, dir):

        epsilon = 0.001

        boundsMin = [0,0,0]
        boundsMax = [0,0,0]

        for i in range(3):
            boundsMin[i] = self.position[i] - (epsilon + self.size[i] / 2)
            boundsMax[i] = self.position[i] + (epsilon + self.size[i] / 2)

        t = float('inf')
        intersect = None

        uvs = None

        for plane in self.planes:
            planeInter = plane.ray_intersect(orig, dir)

            if planeInter is not None:

                # Si estoy dentro del bounding box
                if planeInter.point[0] >= boundsMin[0] and planeInter.point[0] <= boundsMax[0]:
                    if planeInter.point[1] >= boundsMin[1] and planeInter.point[1] <= boundsMax[1]:
                        if planeInter.point[2] >= boundsMin[2] and planeInter.point[2] <= boundsMax[2]:
                            if planeInter.distance < t:
                                t = planeInter.distance
                                intersect = planeInter

                                if abs(plane.normal[0]) > 0:
                                    # mapear uvs para eje x. Uso coordenadas en Y y Z.
                                    u = (planeInter.point [1] - boundsMin[1]) / (boundsMax[1] - boundsMin[1])
                                    v = (planeInter.point [2] - boundsMin[2]) / (boundsMax[2] - boundsMin[2])

                                elif abs(plane.normal[1]) > 0:
                                    # mapear uvs para eje y. Uso coordenadas en X y Z.
                                    u = (planeInter.point [0] - boundsMin[0]) / (boundsMax[0] - boundsMin[0])
                                    v = (planeInter.point [2] - boundsMin[2]) / (boundsMax[2] - boundsMin[2])

                                elif abs(plane.normal[2]) > 0:
                                    # mapear uvs para eje Z. Uso coordenadas en X y Y.
                                    u = (planeInter.point [0] - boundsMin[0]) / (boundsMax[0] - boundsMin[0])
                                    v = (planeInter.point [1] - boundsMin[1]) / (boundsMax[1] - boundsMin[1])

                                uvs = [u, v]

        if intersect is None:
            return None

        return Intersect(distance = intersect.distance,
                         point = intersect.point,
                         normal = intersect.normal,
                         texCoords = uvs,
                         sceneObject = self)





