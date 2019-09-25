import os
import bpy
import mathutils
import struct
import bpy_extras.io_utils
import math

from . import enums, fileWriter, strippifier

# note: In sa2's case, the BASIC model format is only used for collisions.

DO = False # debug out

class ColorARGB:
    """4 Channel Color

    takes values from 0.0 - 1.0 as input and converts them to 0 - 255
    """

    a = 0
    r = 0
    g = 0
    b = 0

    def __init__(self, c = [0,0,0,0]):
        self.a = round(c[3] * 255)
        self.r = round(c[0] * 255)
        self.g = round(c[1] * 255)
        self.b = round(c[2] * 255)

    def isIdentical(self, other):
        return self.a == other.a and self.r == other.r and self.g == other.g and self.b == other.b

    def __str__(self):
        return "(" + str(self.a) + ", " + str(self.r) + ", " + str(self.g) + ", " + str(self.b) + ")"

    def write(self, fileW):
        """writes data to file"""
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)
        fileW.wByte(self.a)

class Vector3:
    """Point in 3D Space"""

    x = 0
    y = 0
    z = 0

    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def isIdentical(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

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

    def __init__(self, uv = [0.0,0.0]):
        self.x = round(uv[0] * 256)
        self.y = round((1-uv[1]) * 256)

    def isIdentical(self, other):
        return self.x == other.x and self.y == other.y

    def write(self, fileW):
        """Writes data to file"""
        fileW.wShort(self.x)
        fileW.wShort(self.y)

class Material:
    """Material of a mesh"""

    name = ""
    diffuse = ColorARGB()
    specular = ColorARGB()
    exponent = 0
    textureID = 0
    mFlags = enums.MaterialFlags.null

    def __init__(self,
             name: str = "",
             diffuse = ColorARGB(), 
             specular = ColorARGB(),
             exponent = 1,
             textureID = 0,
             materialFlags = enums.MaterialFlags.null,
             material: bpy.types.Material = None
             ):
        self.name = name
        if material is None:
            self.diffuse = diffuse
            self.specular = specular
            self.exponent = exponent
            self.textureID = textureID
            self.mFlags = materialFlags
        else:
            matProps = material.saSettings
            self.diffuse = ColorARGB(c = matProps.b_Diffuse)
            self.specular = ColorARGB(c = matProps.b_Specular)
            self.exponent = matProps.b_Exponent * 11
            self.textureID = matProps.b_TextureID
            self.mFlags = enums.MaterialFlags.null

            #translating the properties to flags
            from .enums import MaterialFlags

            #mipmap distance multiplicator
            if matProps.b_d_025:
                self.mFlags |= MaterialFlags.D_025
            if matProps.b_d_050:
                self.mFlags |= MaterialFlags.D_050
            if matProps.b_d_100:
                self.mFlags |= MaterialFlags.D_100
            if matProps.b_d_200:
                self.mFlags |= MaterialFlags.D_200

            #texture filtering
            if matProps.b_use_Anisotropy:
                self.mFlags |= MaterialFlags.FLAG_USE_ANISOTROPIC
            if matProps.b_texFilter == 'BILINEAR':
                self.mFlags |= MaterialFlags.FILTER_BILINEAR
            elif matProps.b_texFilter == 'TRILINEAR':
                self.mFlags |= MaterialFlags.FILTER_TRILINEAR
            elif matProps.b_texFilter == 'BLEND':
                self.mFlags |= MaterialFlags.FILTER_BLEND
            
            # uv properties
            if matProps.b_clampV:
                self.mFlags |= MaterialFlags.FLAG_CLAMP_V
            if matProps.b_clampU:
                self.mFlags |= MaterialFlags.FLAG_CLAMP_U
            if matProps.b_mirrorV:
                self.mFlags |= MaterialFlags.FLAG_FLIP_U
            if matProps.b_mirrorU:
                self.mFlags |= MaterialFlags.FLAG_FLIP_V
            
            # general
            if matProps.b_ignoreSpecular:
                self.mFlags |= MaterialFlags.FLAG_IGNORE_SPECULAR
            if matProps.b_useAlpha:
                self.mFlags |= MaterialFlags.FLAG_USE_ALPHA
            if matProps.b_useTexture:
                self.mFlags |= MaterialFlags.FLAG_USE_TEXTURE
            if matProps.b_useEnv:
                self.mFlags |= MaterialFlags.FLAG_USE_ENV
            if matProps.b_doubleSided:
                self.mFlags |= MaterialFlags.FLAG_DOUBLE_SIDE
            if matProps.b_flatShading:
                self.mFlags |= MaterialFlags.FLAG_USE_FLAT
            if matProps.b_ignoreLighting:
                self.mFlags |= MaterialFlags.FLAG_IGNORE_LIGHT

            # alpha instructions
            src = matProps.b_srcAlpha
            if src == 'ONE':
                self.mFlags |= MaterialFlags.SA_ONE
            elif src == 'OTHER':
                self.mFlags |= MaterialFlags.SA_OTHER
            elif src == 'INV_OTHER':
                self.mFlags |= MaterialFlags.SA_INV_OTHER
            elif src == 'SRC':
                self.mFlags |= MaterialFlags.SA_SRC
            elif src == 'INV_SRC':
                self.mFlags |= MaterialFlags.SA_INV_SRC
            elif src == 'DST':
                self.mFlags |= MaterialFlags.SA_DST
            elif src == 'INV_DST':
                self.mFlags |= MaterialFlags.SA_INV_DST

            dst = matProps.b_destAlpha
            if dst == 'ONE':
                self.mFlags |= MaterialFlags.DA_ONE
            elif dst == 'OTHER':
                self.mFlags |= MaterialFlags.DA_OTHER
            elif dst == 'INV_OTHER':
                self.mFlags |= MaterialFlags.DA_INV_OTHER
            elif dst == 'SRC':
                self.mFlags |= MaterialFlags.DA_SRC
            elif dst == 'INV_SRC':
                self.mFlags |= MaterialFlags.DA_INV_SRC
            elif dst == 'DST':
                self.mFlags |= MaterialFlags.DA_DST
            elif dst == 'INV_DST':
                self.mFlags |= MaterialFlags.DA_INV_DST

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
        self.polyNormal = polyNormal
        self.vColor = vColor
        self.uv = uv

    def collisionFromLoops(mesh):
        """creates a poly list (triangle list) from a mesh"""
        polys = list()
        for f in mesh.polygons:
            for lID in f.loop_indices:
                loop = mesh.loops[lID]
                #vIndex = IDTransl[loop.vertex_index]

                #creating a polyVert with only the poly index, since we only need that for collisions
                polys.append(PolyVert(loop.vertex_index))
                
        return [ polys ]

    def fromLoops(mesh: bpy.types.Mesh):
        matCount = len(mesh.materials)
        if matCount == 0:
            matCount = 1
        meshes = list()
        for m in range(0, matCount):
            meshes.append(list())

        hasColors = len(mesh.vertex_colors) > 0
        hasUV = len(mesh.uv_layers) > 0

        for f in mesh.polygons:
            for lID in f.loop_indices:

                loop = mesh.loops[lID]
                vc = ColorARGB(mesh.vertex_colors[0].data[lID].color) if hasColors else None
                uv = UV(mesh.uv_layers[0].data[lID].uv) if hasUV else None

                poly = PolyVert(loop.vertex_index, vColor=vc, uv=uv)
                meshes[f.material_index].append(poly)

        return meshes

    def isIdentical(self, checkPNRM, checkVC, checkUV, other):
        sameIndexID = self.polyIndex == other.polyIndex
        samePolyNRM = self.polyNormal.isIdentical(other.polyNormal) if checkPNRM else True
        sameVC = self.vColor.isIdentical(other.vColor) if checkVC else True
        sameUV = self.uv.isIdentical(other.uv) if checkUV else True

        return sameIndexID and samePolyNRM and sameVC and sameUV

    def distinct(polyList):
        """Takes a list of PolyVerts and returns a distinct list"""
        distinct = list()
        oIDtodID = [0] * len(polyList)
        
        checkPNRM = polyList[0].polyNormal is not None
        checkVC = polyList[0].vColor is not None
        checkUV = polyList[0].uv is not None

        for IDo, vo in enumerate(polyList):
            found = -1
            for IDd, vd in enumerate(distinct):
                if vo.isIdentical(checkPNRM, checkVC, checkUV, vd):
                    found = IDd
                    break
            if found == -1:
                distinct.append(vo)
                oIDtodID[IDo] = len(distinct) - 1
            else:
                oIDtodID[IDo] = found

        return [distinct, oIDtodID]

    def toStrips(polyList):

        Stripf = strippifier.Strippifier()
        result = list()

        for l in polyList:
            if len(l) == 0:
                result.append(None)
                continue

            distPoly = PolyVert.distinct(l)
            stripIndices = Stripf.Strippify(distPoly[1], doSwaps=False, concat=False)

            polyStrips = [None] * len(stripIndices)

            for i, strip in enumerate(stripIndices):
                tStrip = [0] * len(strip)
                for j, index in enumerate(strip):
                    tStrip[j] = distPoly[0][index]
                polyStrips[i] = tStrip

            result.append(polyStrips)
                

        return result

    def write(fileW, mesh, materialID, meshSetID, polyList, isCollision = False):
        """Writes a single mesh to the file
        
        returns a mesh set
        """
        polyAddress = fileW.tell()     
        # poly indices               
        for s in polyList:
            #the length of the strip
            length = len(s) & 0x7FFF # the last bit determines whether its reversed, which isnt really necessary
            fileW.wUShort(length)
            for p in s:
                fileW.wUShort(p.polyIndex)
        fileW.align(4)

        # poly normal address
        polyNormalAddress = 0
        if polyList[0][0].polyNormal is not None and not isCollision:
            polyNormalAddress = fileW.tell()
            for s in polyList:
                for p in s:
                    p.polyNormal.write(fileW)

        #vertex color
        vColorAddress = 0
        if polyList[0][0].vColor is not None and not isCollision:      
            vColorAddress = fileW.tell()              
            for s in polyList:
                for p in s:
                    p.vColor.write(fileW)

        #uv map
        UVAddress = 0
        if polyList[0][0].uv is not None and not isCollision:
            UVAddress = fileW.tell()            
            for s in polyList:
                for p in s:
                    p.uv.write(fileW)

        return MeshSet(mesh, meshSetID, materialID, enums.PolyType.Strips, len(polyList), polyAddress, 0, polyNormalAddress, vColorAddress, UVAddress)

class MeshSet:
    """A single mesh set in the model"""

    materialID = 0
    name = ""
    meshSetID = 0
    polytype = enums.PolyType.Strips
    polyCount = 0
    polyAddress = 0
    polyAttribts = 0
    polyNormalAddress = 0
    vColorAddress = 0
    UVAddress = 0

    def __init__(self,
                 mesh = None,
                 meshSetID = 0,
                 materialID = 0,
                 polytype = enums.PolyType.Strips,
                 polyCount = 0,
                 polyAddress = 0,
                 polyAttribs = 0, # unused
                 polyNormalAddress = 0, # not needed 99% of the time
                 vColorAddress = 0,
                 UVAddress = 0,
                 ):
        self.mesh = mesh
        self.meshSetID = meshSetID
        self.materialID = materialID
        self.polytype = polytype
        self.polyCount = polyCount
        self.polyAddress = polyAddress
        self.polyAttribs = polyAttribs
        self.polyNormalAddress = polyNormalAddress
        self.vColorAddress = vColorAddress
        self.UVAddress = UVAddress

    def write(self, fileW, labels):
        # combining material id and poly type into two bytes
        matPolytype = self.materialID & (~0xC000)
        matPolytype |= (self.polytype.value << 14)
        fileW.wUShort(matPolytype)
        fileW.wUShort(self.polyCount)

        fileW.wUInt(self.polyAddress)
        fileW.wUInt(self.polyAttribs)
        fileW.wUInt(self.polyNormalAddress)
        fileW.wUInt(self.vColorAddress)
        fileW.wUInt(self.UVAddress)

        #setting the labels
        name = self.mesh.name
        if self.polyAddress > 0:
            labels["b_" + name + "_p" + str(self.meshSetID)] = self.polyAddress
            #labels["p" + str(self.meshSetID)] = self.polyAddress
        if self.polyNormalAddress > 0:
            labels["b_" + name + "_nrm" + str(self.meshSetID)] = self.polyNormalAddress
            #labels["nrm" + str(self.meshSetID)] = self.polyNormalAddress
        if self.vColorAddress > 0:
            labels["b_" + name + "_vc" + str(self.meshSetID) + "_" + self.mesh.vertex_colors[0].name] = self.vColorAddress
            #labels[self.mesh.vertex_colors[0].name] = self.vColorAddress
        if self.UVAddress > 0:
            labels["b_" + name + "_uv" + str(self.meshSetID) + "_" + self.mesh.uv_layers[0].name] = self.UVAddress
            #labels[self.mesh.uv_layers[0].name] = self.UVAddress

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

    def calcCenter(self):
        self.boundCenter = Vector3( BoundingBox.center(self.x,self.xn), 
                                    BoundingBox.center(self.y,self.yn), 
                                    BoundingBox.center(self.z,self.zn) )

    def calcRadius(self, vs):
        distance = 0
        for v in vs:
            dif = Vector3(  self.boundCenter.x - v.co.x, 
                            self.boundCenter.y - v.co.y, 
                            self.boundCenter.z - v.co.z)
            tDist = math.sqrt(pow(dif.x, 2) + pow(dif.y, 2) + pow(dif.z, 2))
            if tDist > distance:
                distance = tDist

        self.radius = distance

    def write(self, fileW):
        self.boundCenter.write(fileW)
        fileW.wFloat(self.radius)

def VertNrmPairs(vertices, exportMatrix):
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
        e = (Vector3(pos.x, pos.y, pos.z), Vector3(nrm.x, nrm.y, nrm.z))
        entries[i] = e

    return entries

def WriteMesh(fileW, mesh, exportMatrix, materials, labels, isCollision = False):
    """Writes a basic mesh into a temporary file and returns the result """
    from . import fileWriter, enums
    global DO

    debug(" Writing BASIC:", mesh.name)
    start = fileW.tell()

    # the verts and normals in pairs and a list that translates between original id and distinct id
    distVertNrm = VertNrmPairs(mesh.vertices, exportMatrix) 

    #creating a bounding box and updating it while writing vertices
    bounds = BoundingBox()

    #writing vertices
    verticesAddress = fileW.tell()
    for v in distVertNrm:
        v[0].write(fileW)
        bounds.checkUpdate(v[0])

    bounds.calcCenter()
    bounds.calcRadius(mesh.vertices)

    #writing normals
    normalsAddress = fileW.tell()
    for v in distVertNrm:
        v[1].write(fileW)

    # creating the loops (as an index list)

    if isCollision:
        polyVs = PolyVert.collisionFromLoops(mesh)
    else:
        polyVs = PolyVert.fromLoops(mesh)

    # making them strips, each set is for one mesh set
    materialLength = len(materials)
    if materialLength < 2:
        polyT = list()
        for p in polyVs:
            polyT.extend(p)
        polyVs = [polyT]


    polyStrips = PolyVert.toStrips(polyVs)

    if DO:
        for i,s in enumerate(polyStrips):
            if s is not None:
                print(" strip", i, ":", len(s))

    #writing the mesh data and getting the mesh sets
    meshSets = list() #[None] * len(polyStrips)

    if materialLength == 0 or isCollision:
        for i, p in enumerate(polyStrips):
            if p == None:
                continue
            meshSets.append(PolyVert.write(fileW, mesh, 0, i, p, isCollision))
    else:
        for i, p in enumerate(polyStrips):
            if p == None:
                continue
            matID = 0
            try:
                for mid, m in enumerate(materials):
                    if m.name == mesh.materials[i].name:
                        matID = mid
                        break
            except ValueError:
                debug(" material", mesh.materials[i].name, "not found")
            meshSets.append(PolyVert.write(fileW, mesh, matID, i, p))

    # writing the mesh sets
    meshSetAddress = fileW.tell()

    for m in meshSets:
        m.write(fileW, labels)

    #adding mesh address to the labels
    labels["a_" + mesh.name] = fileW.tell()
    #labels[mesh.name] = fileW.tell()

    #writing addresses

    labels["b_" + mesh.name + "_v"] = verticesAddress
    fileW.wUInt(verticesAddress)
    labels["b_" + mesh.name + "_nrm"] = normalsAddress
    fileW.wUInt(normalsAddress)
    fileW.wUInt(len(distVertNrm))
    labels["b_" + mesh.name + "_ml"] = meshSetAddress # ml = "mesh list"
    fileW.wUInt(meshSetAddress)
    fileW.wUInt(0x00000010) # material address is always the same (at least the way this addon exports the format)
    fileW.wUShort(len(meshSets))
    fileW.wUShort(materialLength) # material count
    bounds.write(fileW)
    fileW.wUInt(0) #sa1 gap

    if DO:
        print("  vert addr:", '{:08x}'.format(verticesAddress))
        print("  nrm addr:", '{:08x}'.format(normalsAddress))
        print("  vertices:", len(distVertNrm))
        print("  set addr:", '{:08x}'.format(meshSetAddress))
        print("  sets:", len(meshSets))
        print("  mats:", materialLength)
        print(" BASIC length:", (fileW.tell() - start))
        print("----- \n")

    fileW.align(4)

def debug(*string):
    global DO
    if DO:
        print(*string)
