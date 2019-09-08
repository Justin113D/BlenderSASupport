import os
import bpy
import mathutils
import struct
import bpy_extras.io_utils

if "bpy" in locals():
    import importlib
    if "enums" in locals():
        importlib.reload(enums)
    if "FileWriter" in locals():
        importlib.reload(FileWriter)

from . import enums, FileWriter

# In sa2's case, the BASIC model format is only used for collisions.

class ColorARGB:
    """4 Channel Color

    takes values from 0.0 - 1.0 as input and converts them to 0 - 255
    """

    __init__(self, c = [0,0,0,0]):
        self.alpha = round(c[0] * 255)
        self.red = round(c[1] * 255)
        self.green = round(c[2] * 255)
        self.blue = round(c[3] * 255)

    __init__(self, a = 0, r = 0, g = 0, b = 0):
        self.alpha = round(a * 255)
        self.red = round(r * 255)
        self.green = round(g * 255)
        self.blue = round(b * 255)

    def write(self, fileW):
        """writes data to file"""
        fileW.wByte(self.alpha)
        fileW.wByte(self.red)
        fileW.wByte(self.green)
        fileW.wByte(self.blue)

class Vector3:
    """Point in 3D Space"""
    __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def write(self, fileW):
        """Writes data to file"""
        fileW.wFloat(self.x)
        fileW.wFloat(self.y)
        fileW.wFloat(self.z)

class UV:
    """A single texture coordinate

    Converts from 0.0 - 1.0 range to 0 - 255 range
    """

    __init__(self, x = 0, y = 0):
        self.x = round(x * 255)
        self.y = round(y * 255)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wShort(self.x)
        fileW.wShort(self.x)

class Material:
    """Material of a mesh"""

    __init__(self,
             name = "col_material", # "collision", the only material that gets created manually
             diffuse = ColorARGB(0,0,0,0), 
             specular = ColorARGB(0,0,0,0),
             exponent = 0,
             textureID = 0,
             materialFlags = 0,
             ):
        self.diffuse = diffuse
        self.specular = specular
        self.exponent = exponent
        self.textureID = textureID
        self.mFlags = materialFlags

    def addFlag(self, flag):
        self.Flag |= flag

    def removeFlag(self, flag):
        self.Flag &= (~flag)

    def write(self, fileW, baseOffset, labels):
        labels[self.name] = baseOffset + fileW.tell()
        self.diffuse.write(fileW)
        self.specular.write(fileW)
        fileW.wFloat(self.exponent)
        fileW.wInt(self.textureID)
        fileW.wUInt(self.mFlags.value)

class PolyVert:

    __init__(self, polyIndex, polyNormal = None, vColor = None, UV = None):
        self.polyIndex = polyIndex
        if polyNormal not None:
            self.polyNormal = polyNormal
        if vColor not None:
            self.vColor = vColor
        if UV not None:
            self.UV = UV

    # todo: making them a strip
    # 1. get distinct array, keep original array and order tho 
    # 2. make index list from original array, which point at distinct array
    # 3. put index list into strippifier
    # 4. create new array using distinct data, by creating an array of the strip array and putting in values of the distinct array

def distinctVertNrm(vertices):
    """returns a list of the vertex-normal-pairs without duplicates"""
    entries = [None] * len(vertices)

    # putting them in pairs first, so that comparing is easier
    for i, v in enumerate(vertices):
        e = [v.co, v.normal]
        entries[i] = e

    distinct = list()

    for vo in vertices:
        found = False
        for vd in distinct:
            if vo == vd:
                found = true
                break
        if not found:
            distinct.append(vo)

    return distinct

def WriteCollision(mesh, baseOffset, labels):
    """ Used for writing sa2 stage collision """
    tFile = FileWriter() # creating temporary file to write to

    dummyMat = Material() # creating dummy material, just to be sure
    dummyMat.write(tFile, baseOffset, labels) # write dummy material
    
    vertnrm = distinctVertNrm(mesh.vertices)

    return tFile.close() # returns all data and closes file

