import bpy
import mathutils

import math
from typing import List

from . import enums, fileWriter, strippifier, common
from .common import Vector3, ColorARGB, UV, BoundingBox

# note: In sa2's case, the BASIC model format is only used for collisions.

DO = False # debug out

class Material:
    """Material of a mesh"""

    name: str
    diffuse: ColorARGB
    specular: ColorARGB
    exponent: float
    textureID: int
    mFlags: enums.MaterialFlags

    def __init__(self,
                name: str = "default",
                diffuse = ColorARGB(), 
                specular = ColorARGB(),
                exponent = 11,
                textureID = 0,
                materialFlags = enums.MaterialFlags.null,
                ):
        self.name = name
        self.diffuse = diffuse
        self.specular = specular
        self.exponent = exponent
        self.textureID = textureID
        self.mFlags = materialFlags

    def fromBlenderMat(material: bpy.types.Material):
        
        matProps = material.saSettings
        diffuse = ColorARGB(c = matProps.b_Diffuse)
        specular = ColorARGB(c = matProps.b_Specular)
        exponent = matProps.b_Exponent * 11
        textureID = matProps.b_TextureID
        mFlags = enums.MaterialFlags.null

        #translating the properties to flags
        from .enums import MaterialFlags

        #mipmap distance multiplicator
        if matProps.b_d_025:
            mFlags |= MaterialFlags.D_025
        if matProps.b_d_050:
            mFlags |= MaterialFlags.D_050
        if matProps.b_d_100:
            mFlags |= MaterialFlags.D_100
        if matProps.b_d_200:
            mFlags |= MaterialFlags.D_200

        #texture filtering
        if matProps.b_use_Anisotropy:
            mFlags |= MaterialFlags.FLAG_USE_ANISOTROPIC
        if matProps.b_texFilter == 'BILINEAR':
            mFlags |= MaterialFlags.FILTER_BILINEAR
        elif matProps.b_texFilter == 'TRILINEAR':
            mFlags |= MaterialFlags.FILTER_TRILINEAR
        elif matProps.b_texFilter == 'BLEND':
            mFlags |= MaterialFlags.FILTER_BLEND
        
        # uv properties
        if matProps.b_clampV:
            mFlags |= MaterialFlags.FLAG_CLAMP_V
        if matProps.b_clampU:
            mFlags |= MaterialFlags.FLAG_CLAMP_U
        if matProps.b_mirrorV:
            mFlags |= MaterialFlags.FLAG_FLIP_U
        if matProps.b_mirrorU:
            mFlags |= MaterialFlags.FLAG_FLIP_V
        
        # general
        if matProps.b_ignoreSpecular:
            mFlags |= MaterialFlags.FLAG_IGNORE_SPECULAR
        if matProps.b_useAlpha:
            mFlags |= MaterialFlags.FLAG_USE_ALPHA
        if matProps.b_useTexture:
            mFlags |= MaterialFlags.FLAG_USE_TEXTURE
        if matProps.b_useEnv:
            mFlags |= MaterialFlags.FLAG_USE_ENV
        if matProps.b_doubleSided:
            mFlags |= MaterialFlags.FLAG_DOUBLE_SIDE
        if matProps.b_flatShading:
            mFlags |= MaterialFlags.FLAG_USE_FLAT
        if matProps.b_ignoreLighting:
            mFlags |= MaterialFlags.FLAG_IGNORE_LIGHT

        # alpha instructions
        src = matProps.b_srcAlpha
        if src == 'ONE':
            mFlags |= MaterialFlags.SA_ONE
        elif src == 'OTHER':
            mFlags |= MaterialFlags.SA_OTHER
        elif src == 'INV_OTHER':
            mFlags |= MaterialFlags.SA_INV_OTHER
        elif src == 'SRC':
            mFlags |= MaterialFlags.SA_SRC
        elif src == 'INV_SRC':
            mFlags |= MaterialFlags.SA_INV_SRC
        elif src == 'DST':
            mFlags |= MaterialFlags.SA_DST
        elif src == 'INV_DST':
            mFlags |= MaterialFlags.SA_INV_DST

        dst = matProps.b_destAlpha
        if dst == 'ONE':
            mFlags |= MaterialFlags.DA_ONE
        elif dst == 'OTHER':
            mFlags |= MaterialFlags.DA_OTHER
        elif dst == 'INV_OTHER':
            mFlags |= MaterialFlags.DA_INV_OTHER
        elif dst == 'SRC':
            mFlags |= MaterialFlags.DA_SRC
        elif dst == 'INV_SRC':
            mFlags |= MaterialFlags.DA_INV_SRC
        elif dst == 'DST':
            mFlags |= MaterialFlags.DA_DST
        elif dst == 'INV_DST':
            mFlags |= MaterialFlags.DA_INV_DST

        return Material(material.name, diffuse, specular, exponent, textureID, mFlags)

    def debug(self):
        """prints material info to the console"""
        print("  Material:", self.name)
        print("    Diffuse:", str(self.diffuse))
        print("    Specular:", str(self.specular))
        print("    Specularity:", self.exponent)
        print("    Texture ID:", self.textureID)
        print("    Flags:", self.mFlags, "\n")

    def writeMaterials(fileW: fileWriter.FileWriter, materials: List[bpy.types.Material], labels: dict):
        """writes materials as BASIC materal data"""
        mats = list()

        if len(materials) == 0:
            bMat = Material()
            bMat.write(fileW)
            mats.append(bMat)
        else:
            for m in materials:
                bMat = Material.fromBlenderMat(m)
                bMat.write(fileW, labels)
                mats.append(bMat)

        global DO
        if DO:
            print(" == BASIC Materials ==")
            for m in mats:
                m.debug()

        return mats

    def write(self, fileW, labels):
        labels[fileW.tell()] = "mat_" + self.name
        self.diffuse.writeRGBA(fileW)
        self.specular.writeRGBA(fileW)
        fileW.wFloat(self.exponent)
        fileW.wInt(self.textureID)
        fileW.wUInt(self.mFlags.value)

class PolyVert:
    """Face loops of a mesh
    
    an array/list represents a single mesh
    """

    polyIndex: int
    polyNormal: Vector3
    color: ColorARGB
    uv: UV

    def __init__(self, 
                 polyIndex: int, 
                 polyNormal: Vector3, 
                 color: ColorARGB, 
                 uv: UV):
        self.polyIndex = polyIndex
        self.polyNormal = polyNormal
        self.color = color
        self.uv = uv

    def __eq__(self, other):
        eID = self.polyIndex == other.polyIndex
        ePNRM = self.polyNormal == other.polyNormal
        eVC = self.color == other.color
        eUV = self.uv == other.uv

        return eID and ePNRM and eVC and eUV

class MeshSet:
    """A single mesh set in the model"""

    mesh: bpy.types.Mesh
    materialID: int
    meshSetID: int
    polytype: enums.PolyType
    polycount: int

    # the polygon corners of the mesh
    # each list is a single poly
    polys: List[List[PolyVert]] 

    polyPtr: int
    polyAttribs: int
    polyNormalPtr: int
    ColorPtr: int 
    UVPtr: int

    def __init__(self,
                 mesh: bpy.types.Mesh,
                 materialID: int,
                 meshSetID: int,
                 polyType: enums.PolyType,
                 polys: List[List[PolyVert]],
                 polyAttribs: int = 0
                 ):
        self.mesh = mesh
        self.materialID = materialID
        self.meshSetID = meshSetID
        self.polytype = polyType
        self.polys = polys
        self.polyAttribs = polyAttribs
        self.polycount = len(polys) if polyType == enums.PolyType.Strips or polyType == enums.PolyType.NPoly else round(len(polys[0]) / 3)

    def writePolys(self, fileW: fileWriter.FileWriter, usePolyNormals: bool, useColor: bool, useUV: bool):

        #writing poly indices
        self.polyPtr = fileW.tell()

        for p in self.polys:
            if self.polytype == enums.PolyType.Strips or self.polytype == enums.PolyType.NPoly:
                fileW.wUShort(min(0x7FFF, len(p)))
            for l in p:
                fileW.wUShort(l.polyIndex)
        fileW.align(4)

        # writing poly normals (usually unused tho)
        self.polyNormalPtr = 0
        if usePolyNormals:
            self.polyNormalPtr = fileW.tell()
            for p in self.polys:
                for l in p:
                    l.polyNormal.write(fileW)
        
        # writing colors
        self.ColorPtr = 0
        if useColor:
            self.ColorPtr = fileW.tell()
            for p in self.polys:
                for l in p:
                    l.color.writeARGB(fileW)

        # writing uvs
        self.UVPtr = 0
        if useUV:
            self.UVPtr = fileW.tell()
            for p in self.polys:
                for l in p:
                    l.uv.write(fileW)

    def writeSet(self, fileW, labels):
        # combining material id and poly type into two bytes
        matPolytype = self.materialID & (~0xC000)
        matPolytype |= (self.polytype.value << 14)
        fileW.wUShort(matPolytype)
        fileW.wUShort(self.polycount)

        fileW.wUInt(self.polyPtr)
        fileW.wUInt(self.polyAttribs)
        fileW.wUInt(self.polyNormalPtr)
        fileW.wUInt(self.ColorPtr)
        fileW.wUInt(self.UVPtr)

        #setting the labels
        name = "bsc_" + self.mesh.name + "_"
        if self.polyPtr > 0:
            labels[self.polyPtr] = name + "p" + str(self.meshSetID)
        if self.polyNormalPtr > 0:
            labels[self.polyNormalPtr] = name + "nrm" + str(self.meshSetID)
        if self.ColorPtr > 0:
            labels[self.ColorPtr] = name + "vc" + str(self.meshSetID)
        if self.UVPtr > 0:
            labels[self.UVPtr] = name + "uv" + str(self.meshSetID)

class Attach:
    """Attach for the BASIC format"""

    name: str
    positions: List[Vector3]
    normals: List[Vector3]
    meshSets: List[MeshSet]

    usePolyNormals: bool
    useColor: bool
    useUV: bool

    materials: List[Material]
    bounds: BoundingBox

    def __init__(self,
                 name: str,
                 positions: List[Vector3],
                 normals: List[Vector3],
                 meshSets: List[MeshSet],
                 usePolyNormals: bool,
                 useColor: bool,
                 useUV: bool,
                 materials: List[Material],
                 bounds: BoundingBox):

        self.name = name
        self.positions = positions
        self.normals = normals
        self.meshSets = meshSets
        self.usePolyNormals = usePolyNormals
        self.useColor = useColor
        self.useUV = useUV
        self.materials = materials
        self.bounds = bounds

    def fromMesh(mesh: bpy.types.Mesh, 
                 export_matrix: mathutils.Matrix, 
                 materials: List[Material], 
                 isCollision: bool = False):
        """Creates a BASIC mesh from a Blender mesh"""
        global DO

        # gettings the positions and normals
        positions = [None] * len(mesh.vertices)
        normals = common.getNormalData(mesh)

        for i, v in enumerate(mesh.vertices):
            positions[i] = Vector3(export_matrix @ v.co)
            normals[i] = Vector3(export_matrix @ normals[i])

        # calculating bounds
        bounds = BoundingBox(mesh.vertices)
        bounds.adjust(export_matrix)

        # determining which data the polys require
        usePolyNormals = False # basically unused for our purposes
        useColor = len(mesh.vertex_colors) > 0 and not isCollision
        useUV = len(mesh.uv_layers) > 0 and not isCollision

        # we take minimum number between the mesh materials and global materials first, just to be sure.
        # then we make it a minimum of 1 (so that there is at least one poly list)
        # if we are writing collisions, then it can directly just be 1 array
        polyLists = 1 if isCollision else max(1, min(len(mesh.materials), len(materials))) 
        polyListMin = polyLists - 1
        polys: List[list[PolyVert]] = [[] for i in range(polyLists)] # one poly list for each material

        for f in mesh.polygons:
            for lID in f.loop_indices:

                loop = mesh.loops[lID]
                vc = ColorARGB(mesh.vertex_colors[0].data[lID].color) if useColor else None
                uv = UV(mesh.uv_layers[0].data[lID].uv) if useUV else None

                poly = PolyVert(loop.vertex_index, None, vc, uv)
                polys[min(f.material_index, polyListMin)].append(poly) 
                # we take the minimum number, this way if we use collisions, 
                # it will always place them in list no. 0
        

        # strippifying
        stripf = strippifier.Strippifier()
        stripPolys = list()

        for l in polys:
            # if there are no polys in the poly list, then we ignore it
            if len(l) == 0:
                stripPolys.append(None) # so that the material order is still correct
                continue
            
            # getting distinct polys first
            distinct = list()
            IDs = [0] * len(l)

            distinct, IDs = common.getDistinctwID(l)

            stripIndices = stripf.Strippify(IDs, doSwaps=False, concat=False)

            # if the strips are longer than a
            stripLength = 0
            for s in stripIndices:
                stripLength += len(s) + 1 # +1 for the strip length in the poly data later on

            if stripLength > len(l):
                stripPolys.append((enums.PolyType.Triangles, [l]))
            else:
                polyStrips = [None] * len(stripIndices)

                for i, strip in enumerate(stripIndices):
                    tStrip = [None] * len(strip)
                    for j, index in enumerate(strip):
                        tStrip[j] = distinct[index]
                    polyStrips[i] = tStrip
                
                stripPolys.append((enums.PolyType.Strips, polyStrips))

        # creating the meshsets
        meshsets: List[meshsets] = list()
        

        if isCollision or len(materials) == 0:
            if stripPolys[0] is not None:
                meshsets.append(MeshSet(mesh, 0, 0, stripPolys[0][0], stripPolys[0][1]))
        else:
            for i, p in enumerate(stripPolys):
                if p == None:
                    continue
                matID = 0
                if len(mesh.materials) > 0:
                    try:
                        for mid, m in enumerate(materials):
                            if m.name == mesh.materials[i].name:
                                matID = mid
                                break
                    except ValueError:
                        print(" material", mesh.materials[i].name, "not found")

                meshsets.append(MeshSet(mesh, matID, i, p[0], p[1]))

        if len(meshsets) == 0:
            print(" Mesh not valid (?); no meshsets could be created")
            return None
        return Attach(mesh.name, positions, normals, meshsets, usePolyNormals, useColor, useUV, materials, bounds)
    
    def write(self, fileW: fileWriter.FileWriter, labels: dict, meshDict: dict = None):
        global DO

        posPtr = fileW.tell()
        labels[posPtr] = "bsc_" + self.name + "_pos"
        for p in self.positions:
            p.write(fileW)
        
        nrmPtr = fileW.tell()
        labels[nrmPtr] = "bsc_" + self.name + "_nrm"
        for n in self.normals:
            n.write(fileW)

        for m in self.meshSets:
            m.writePolys(fileW, self.usePolyNormals, self.useColor, self.useUV)

        setPtr = fileW.tell()
        labels[setPtr] = "bsc_" + self.name + "_set"
        for m in self.meshSets:
            m.writeSet(fileW, labels)

        # writing attach info
        attachPtr = fileW.tell()
        labels[attachPtr] = "bsc_" + self.name
        if meshDict is not None:
            meshDict[self.name] = attachPtr
        fileW.wUInt(posPtr)
        fileW.wUInt(nrmPtr)
        fileW.wUInt(len(self.positions))
        fileW.wUInt(setPtr)
        fileW.wUInt(0x10) # material list is always at 0x00000010 in my exporter
        fileW.wUShort(len(self.meshSets))
        fileW.wUShort(min(1, len(self.materials)))
        self.bounds.write(fileW)

        if DO:
            print("  BASIC:", self.name)
            print("    Position Ptr:", common.hex4(posPtr))
            print("    Normal Ptr:", common.hex4(nrmPtr))
            print("    Vertices:", len(self.positions))
            print("    Mesh set Ptr:", common.hex4(setPtr))
            print("    Mesh sets:", len(self.meshSets), "\n")
