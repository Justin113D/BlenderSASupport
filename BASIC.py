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
    if "Strippifier" in locals():
        importlib.reload(Strippifier)

from . import enums, FileWriter, Strippifier

# note: In sa2's case, the BASIC model format is only used for collisions.

class ColorARGB:
    """4 Channel Color

    takes values from 0.0 - 1.0 as input and converts them to 0 - 255
    """

    alpha = 0
    red = 0
    green = 0
    blue = 0

    def __init__(self, c = [0,0,0,0]):
        self.alpha = round(c[0] * 255)
        self.red = round(c[1] * 255)
        self.green = round(c[2] * 255)
        self.blue = round(c[3] * 255)

    def __init__(self, a = 0, r = 0, g = 0, b = 0):
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

    x = 0
    y = 0
    z = 0

    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def distanceFromCenter(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z)**(0.5)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wFloat(self.x)
        fileW.wFloat(self.y)
        fileW.wFloat(self.z)

class UV:
    """A single texture coordinate

    Converts from 0.0 - 1.0 range to 0 - 255 range
    """

    x = 0
    y = 0

    def __init__(self, x = 0, y = 0):
        self.x = round(x * 255)
        self.y = round(y * 255)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wShort(self.x)
        fileW.wShort(self.x)

class Material:
    """Material of a mesh"""

    diffuse = ColorARGB()
    specular = ColorARGB()
    exponent = 0
    textureID = 0
    materialFlags = 0

    def __init__(self,
             diffuse = ColorARGB(), 
             specular = ColorARGB(),
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

    def write(self, fileW):
        self.diffuse.write(fileW)
        self.specular.write(fileW)
        fileW.wFloat(self.exponent)
        fileW.wInt(self.textureID)
        fileW.wUInt(self.mFlags.value)

class PolyVert:
    """Face loops of a mesh
    
    an array/list represents a single mesh
    """

    polyIndex = 0
    polyNormal = Vector3()
    vColor = ColorARGB()
    uv = UV()

    def __init__(self, polyIndex, polyNormal = None, vColor = None, uv = None):
        self.polyIndex = polyIndex
        # polynormals are basically not needed 99% of the time
        if polyNormal is not None:
            self.polyNormal = polyNormal
        if vColor is not None:
            self.vColor = vColor
        if uv is not None:
            self.uv = vu

    def collisionFromLoops(mesh, IDTransl):
        """creates a poly list (triangle list) from a mesh"""
        polys = [None] * len(mesh.polygons) * 3
        for fi, f in enumerate(mesh.polygons):
            for i, lID in enumerate(f.loop_indices):
                loop = mesh.loops[lID]
                vIndex = IDTransl[loop.vertex_index]

                #creating a polyVert with only the poly index, since we only need that for collisions
                polys[fi + i] = PolyVert(vIndex)

        return polys

    def fromLoops(mesh, IDTransl, matDict):
        """Creates poly lists (triangle lists) from a mesh, requires material dictionary for translation"""
        print("not implemented yet, sorry")
        return collisionFromLoops(mesh, IDTransl)

    def distinct(polyList):
        """Takes a list of PolyVerts and returns a distinct list"""
        distinct = list()
        oIDtodID = [0] * len(polyList)

        for IDo, vo in enumerate(polyList):
            found = -1
            for IDd, vd in enumerate(distinct):
                if vo == vd:
                    found = IDd
                    break
            if found == -1:
                distinct.append(vo)
                oIDtodID[IDo] = len(distinct) - 1
            else:
                oIDtodID[IDo] = found

        return [distinct, oIDtodID]

    def toStrip(polyList):
        distPoly = PolyVert.distinct(polyList)
        stripIndices = Strippifier.strippify(distPoly[2]) #todo
        polyStrip = [None] * len(stripIndices)

        for i, index in enumerate(stripIndices):
            polyStrip[i] = distPoly[index]

        return polyStrip

    def write(fileW, meshName, materialID, polyList, baseOffset):
        """Writes a single mesh to the file
        
        returns a mesh set
        """
        # poly indices
        polyAddress = fileW.tell() + baseOffset
        for p in polyList:
            fileW.wUShort(p.polyIndex)
        fileW.align(4)

        # poly normal address
        polyNormalAddress = 0
        if hasattr(polyList[0], 'polyNormal'):
            polyNormalAddress = fileW.tell() + baseOffset
            for p in polyList:
                p.polyNormal.write(fileW)

        #vertex color
        vColorAddress = 0
        if hasattr(polyList[0], 'vColor'):
            vColorAddress = fileW.tell() + baseOffset
            for p in polyList:
                p.vColor.write(fileW)

        #uv map
        UVAddress = 0
        if hasattr(polyList[0], 'uv'):
            UVAddress = fileW.tell() + baseOffset
            for p in polyList:
                p.uv.write(fileW)

        return MeshSet(materialID, enums.PolyType.Strips, len(polyList), polyAddress, 0, polyNormalAddress, vColorAddress, UVAddress)

class MeshSet:
    """A single mesh set in the model"""

    materialID = 0
    polyType = enums.PolyType.Strips
    polyCount = 0
    polyAddress = 0
    polyAttribts = 0
    polyNormalAddress = 0
    vColorAddress = 0
    UVAddress = 0

    def __init__(self,
             materialID = 0,
             polytype = enums.PolyType.Strips,
             polyCount = 0,
             polyAddress = 0,
             polyAttribs = 0, # unused
             polyNormalAddress = 0, # not needed 99% of the time
             vColorAddress = 0,
             UVAddress = 0,
             ):
        self.materialID = materialID
        self.polytype = polytype
        self.polyCount = polyCount
        self.polyAddress = polyAddress
        self.polyAttribs = polyAttribs
        self.polyNormalAddress = polyNormalAddress
        self.vColorAddress = vColorAddress
        self.UVAddress = UVAddress

    def write(self, fileW):
        # combining material id and poly type into two bytes
        matPolytype = self.materialID & (~0xC000)
        matPolytype |= (self.polytype.value << 14)
        fileW.wUShort(self.matPolytype)
        fileW.wUShort(self.polyCount)

        fileW.wUInt(self.polyAddress)
        fileW.wUInt(self.polyAttribs)
        fileW.wUInt(self.polyNormalAddress)
        fileW.wUInt(self.vColorAddress)
        fileW.wUInt(self.UVAddress)
        fileW.wUInt(0) # gap

class BoundingBox:
    """Used to calculate the bounding sphere which the game uses"""

    x = 0
    xn = 0
    y = 0
    yn = 0
    z = 0
    zn = 0

    def __init__(self):
        self.x = 0
        self.xn = 0
        self.y = 0
        self.yn = 0
        self.z = 0
        self.zn = 0

    def checkUpdate(self, point):
        if self.x < point.x:
            self.x = point.x
        elif self.xn > point.x:
            self.xn = point.x

        if self.y < point.y:
            self.y = point.y
        elif self.yn > point.y:
            self.yn = point.y

        if self.z < point.z:
            self.z = point.z
        elif self.zn > point.z:
            self.zn = point.z

    def center(p1, p2):
        return (p1 + p2) / 2.0

    def getBoundingSphere(self):
        bs = [None] * 2
        bs[0] = Vector3( center(self.x,self.xn), center(self.y,self.yn), center(self.z,self.zn) )
        xd = abs(self.x - self.xn)
        yd = abs(self.y - self.yn)
        zd = abs(self.z - self.zn)
        bs[1] = max(xd, yd, zd) / 2.0
        return bs

    def write(self, fileW):
        bs = self.getBoundingSphere()
        bs[0].write(fileW)
        fileW.wFloat(bs[1])

def distinctVertNrm(vertices, exportMatrix):
    """returns a list of the vertex-normal-pairs without duplicates
    
    vertices: mesh vertices as input

    returns: 

    + distinct list of position and normal in pairs 
    
    + list to translate from original index to distinct index
    """
    entries = [None] * len(vertices)

    # putting them in pairs first, so that comparing is easier
    for i, v in enumerate(vertices):
        pos = exportMatrix @ v.co
        nrm = exportMatrix @ v.normal
        e = [Vector3(pos.x, pos.y, pos.z), Vector3(nrm.x, nrm.y, nrm.z)]
        entries[i] = e

    distinct = list()
    oIDtodID = [0] * len(vertices)

    for IDo, vo in enumerate(vertices):
        found = -1
        for IDd, vd in enumerate(distinct):
            if vo == vd:
                found = IDd
                break
        if found == -1:
            distinct.append(vo)
            oIDtodID[IDo] = len(distinct) - 1
        else:
            oIDtodID[IDo] = found

    return [distinct, oIDtodID]

def WriteCollision(mesh, exportMatrix, baseOffset, labels):
    """ Used for writing sa2 stage collision 
    
    mesh has to be triangulated
    """

    # creating temporary file to write to
    tFile = FileWriter() 

    # creating dummy material, just to be sure
    if 'b_col_material' in labels:
        materialaddress = labels['b_col_material']
    else:
        labels["b_col_material"] = baseOffset
        dummyMat = Material() 
        dummyMat.write(tFile)

    # the verts and normals in pairs and a list that translates between original id and distinct id
    distVertNrm = distinctVertNrm(mesh.vertices) 

    # creating the loops (as an index list)
    polys = PolyVert.collisionFromLoops(Mesh, distVertNrm[1])
    polys = PolyVert.toStrip(polys)

    # writing the Mesh data (polys)
    meshSet = PolyVert.write(tFile, mesh.name, 0, polys, baseOffset)    

    # writing the mesh properties (mesh set)
    meshSetAddress = tFile.tell() + baseOffset
    meshSet.write(tFile)

    #creating a bounding box and updating it while writing vertices
    bounds = BoundingBox()

    #writing vertices
    verticesAddress = tFile.tell() + baseOffset
    for v in distVertNrm[0]:
        v[0].write(tFile)
        bounds.checkUpdate(v[0])

    #writing normals
    normalsAddress = tFile.tell() + baseOffset
    for v in distVertNrm[0]:
        v[1].write(tFile)

    #adding mesh address to the labels
    labels[mesh.name] = tFile.tell() + baseOffset

    #writing addresses
    tFile.wUInt(verticesAddress)
    tFile.wUInt(normalsAddress)
    tFile.wUInt(len(distVertNrm[0]))
    tFile.wUInt(meshSetAddress)
    tFile.wUint(materialaddress)
    tFile.wUShort(1) # mesh count
    tFile.wUShort(1) # material count
    bounds.write(tFile)

    tFile.align(4)

    return tFile.close() # returns all data and closes file
