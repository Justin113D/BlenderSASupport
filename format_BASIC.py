import bpy
import mathutils

import math
from typing import List, Dict

from . import enums, fileHelper, strippifier, common
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

    def writeMaterials(fileW: fileHelper.FileWriter, materials: List[bpy.types.Material], labels: dict):
        """writes materials as BASIC materal data"""
        mats = list()

        if len(materials) == 0:
            bMat = Material()
            bMat.write(fileW)
            mats.append(bMat)
        else:
            for m in materials.values():
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

    def read(fileR: fileHelper.FileReader, address: int, index: int):
        diffuse = ColorARGB.fromARGB(fileR.rUInt(address))
        specular = ColorARGB.fromARGB(fileR.rUInt(address + 4))
        specularExponent = fileR.rFloat(address + 8)
        textureID = fileR.rUInt(address + 12)
        flags = enums.MaterialFlags(fileR.rUInt(address + 16))
        return Material("Material_" + str(index), diffuse, specular, specularExponent, textureID, flags)

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

    name: str
    materialID: int
    meshSetID: int
    polytype: enums.PolyType
    polycount: int

    # the polygon corners of the mesh
    # each list is a single poly
    polys: List[List[PolyVert]]
    reverse: List[bool]

    polyPtr: int
    polyAttribs: int
    polyNormalPtr: int
    ColorPtr: int
    UVPtr: int

    def __init__(self,
                 name: str,
                 materialID: int,
                 meshSetID: int,
                 polyType: enums.PolyType,
                 polys: List[List[PolyVert]],
                 usePolyNormals: bool,
                 useColor: bool,
                 useUV: bool,
                 polyAttribs: int = 0,
                 reverse: List[bool] = None
                 ):
        self.name = name
        self.materialID = materialID
        self.meshSetID = meshSetID
        self.polytype = polyType
        self.polys = polys
        self.polyAttribs = polyAttribs
        self.polycount = len(polys) if polyType == enums.PolyType.Strips or polyType == enums.PolyType.NPoly else round(len(polys[0]) / 3)
        self.reverse = reverse

        self.polyNormalPtr = -1 if usePolyNormals else 0
        self.ColorPtr = -1 if useColor else 0
        self.UVPtr = -1 if useUV else 0

    def writePolys(self, fileW: fileHelper.FileWriter):

        #writing poly indices
        self.polyPtr = fileW.tell()

        for p in self.polys:
            if self.polytype == enums.PolyType.Strips or self.polytype == enums.PolyType.NPoly:
                fileW.wUShort(min(0x7FFF, len(p)))
            for l in p:
                fileW.wUShort(l.polyIndex)
        fileW.align(4)

        # writing poly normals (usually unused tho)
        if self.polyNormalPtr == -1:
            self.polyNormalPtr = fileW.tell()
            for p in self.polys:
                for l in p:
                    l.polyNormal.write(fileW)

        # writing colors
        if self.ColorPtr == -1:
            self.ColorPtr = fileW.tell()
            for p in self.polys:
                for l in p:
                    l.color.writeARGB(fileW)

        # writing uvs
        if self.UVPtr == -1:
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
        name = "bsc_" + self.name + "_"
        if self.polyPtr > 0:
            labels[self.polyPtr] = name + "p" + str(self.meshSetID)
        if self.polyNormalPtr > 0:
            labels[self.polyNormalPtr] = name + "nrm" + str(self.meshSetID)
        if self.ColorPtr > 0:
            labels[self.ColorPtr] = name + "vc" + str(self.meshSetID)
        if self.UVPtr > 0:
            labels[self.UVPtr] = name + "uv" + str(self.meshSetID)

    def read(fileR: fileHelper.FileReader, address: int, meshName: str, setID: int):


        header = fileR.rUShort(address)
        materialID = header & 0x3FFF
        polyType = enums.PolyType((header & 0xC000) >> 14)

        polyCount = fileR.rUShort(address + 2)
        polyAttribs = fileR.rUInt(address + 8)

        polyPtr = fileR.rUInt(address + 4)
        polyNrmPtr = fileR.rUInt(address + 12)
        colPtr = fileR.rUInt(address + 16)
        uvPtr = fileR.rUInt(address + 20)

        polys = list()
        reverse = list() if polyType == enums.PolyType.Strips else None
        for p in range(polyCount):
            vCount = 3
            if polyType == enums.PolyType.Strips:
                stripSize = fileR.rShort(polyPtr)
                reverse.append(stripSize < 0)
                vCount = abs(stripSize)
                polyPtr += 2
            elif polyType == enums.PolyType.NPoly:
                vCount = fileR.rUShort(polyPtr)
                polyPtr += 2
            elif polyType == enums.PolyType.Quads:
                vCount = 4

            polyVerts = list()
            for v in range(vCount):

                vIndex = fileR.rUShort(polyPtr)
                polyPtr += 2

                polyNormal = Vector3()
                if polyNrmPtr:
                    polyNormal = Vector3((fileR.rFloat(polyNrmPtr), fileR.rFloat(polyNrmPtr + 4), fileR.rFloat(polyNrmPtr + 8)))
                    polyNrmPtr += 12

                color = ColorARGB()
                if colPtr:
                    color = ColorARGB.fromARGB(fileR.rUInt(colPtr))
                    colPtr += 4

                uv = UV()
                if uvPtr:
                    uv.x = fileR.rShort(uvPtr)
                    uv.y = fileR.rShort(uvPtr + 2)
                    uvPtr += 4

                polyVerts.append(PolyVert(vIndex, polyNormal, color, uv))

            polys.append(polyVerts)

        return MeshSet(meshName, materialID, setID, polyType, polys, polyNrmPtr > 0, colPtr > 0, uvPtr > 0, polyAttribs, reverse)

class Attach:
    """Attach for the BASIC format"""

    name: str
    positions: List[Vector3]
    normals: List[Vector3]
    meshSets: List[MeshSet]

    materials: List[Material]
    bounds: BoundingBox

    def __init__(self,
                 name: str,
                 positions: List[Vector3],
                 normals: List[Vector3],
                 meshSets: List[MeshSet],
                 materials: List[Material],
                 bounds: BoundingBox):

        self.name = name
        self.positions = positions
        self.normals = normals
        self.meshSets = meshSets
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
                meshsets.append(MeshSet(mesh.name, 0, 0, stripPolys[0][0], stripPolys[0][1], usePolyNormals, useColor, useUV))
        else:
            for i, p in enumerate(stripPolys):
                if p is None or len(p) == 0:
                    continue
                matID = 0
                if len(mesh.materials) > 0:
                    try:
                        for mid, m in enumerate(materials.values()):
                            if m.name == mesh.materials[i].name:
                                matID = mid
                                break
                    except ValueError:
                        print(" material", mesh.materials[i].name, "not found")

                meshsets.append(MeshSet(mesh.name, matID, i, p[0], p[1], usePolyNormals, useColor, useUV))

        if len(meshsets) == 0:
            print(" Mesh not valid (?); no meshsets could be created")
            return None
        return Attach(mesh.name, positions, normals, meshsets, materials, bounds)

    def write(self, fileW: fileHelper.FileWriter, labels: dict, meshDict: dict = None):
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
            m.writePolys(fileW)

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
        fileW.wUShort(max(1, len(self.materials)))
        self.bounds.write(fileW)

        if DO:
            print("  BASIC:", self.name)
            print("    Position Ptr:", common.hex4(posPtr))
            print("    Normal Ptr:", common.hex4(nrmPtr))
            print("    Vertices:", len(self.positions))
            print("    Mesh set Ptr:", common.hex4(setPtr))
            print("    Mesh sets:", len(self.meshSets), "\n")

    def read(fileR: fileHelper.FileReader, address: int, meshID: int, labels: dict):

        if address in labels:
            name: str = labels[address]
            if name.startswith("bsc_"):
                name = name[4:]
        else:
            name = "Attach_" + str(meshID)

        pos = fileR.rUInt(address)
        nrm = fileR.rUInt(address + 4)
        vCount = fileR.rUInt(address + 8)

        positions: List[Vector3] = list()
        normals: List[Vector3] = list()

        for v in range(vCount):
            positions.append(Vector3((fileR.rFloat(pos), fileR.rFloat(pos + 4), fileR.rFloat(pos + 8))))
            normals.append(Vector3((fileR.rFloat(nrm), fileR.rFloat(nrm + 4), fileR.rFloat(nrm + 8))))
            pos += 12
            nrm += 12

        tempAddr = fileR.rUInt(address + 12)
        meshSetCount = fileR.rUShort(address + 20)
        meshSets = list()

        for m in range(meshSetCount):
            meshSets.append(MeshSet.read(fileR, tempAddr, name, m))
            tempAddr += 24

        tempAddr = fileR.rUInt(address + 16)
        materialCount = fileR.rUShort(address + 22)
        materials: List[Material] = list()

        for m in range(materialCount):
            materials.append(Material.read(fileR, tempAddr, m))
            tempAddr += 20

        return Attach(name, positions, normals, meshSets, materials, None)

def process_BASIC(models: List[common.Model], attaches: Dict[int, Attach]):

    import bmesh
    meshes: Dict[int, bpy.types.Mesh] = dict()

    materials: List[bpy.types.Material] = list()
    matDicts: List[dict] = list()

    for o in models:
        if o.meshPtr == 0:
            continue
        elif o.meshPtr in meshes:
            o.meshes.append(meshes[o.meshPtr])
            continue

        attach = attaches[o.meshPtr]

        # creating materials
        meshMaterials = list()
        matIDs = list()

        from .enums import MaterialFlags
        for m in attach.materials:
            d = common.getDefaultMatDict()

            d["b_Diffuse"] = m.diffuse.toBlenderTuple()
            d["b_Specular"] = m.specular.toBlenderTuple()
            d["b_Exponent"] = m.exponent / 11
            d["b_TextureID"] = m.textureID
            f = m.mFlags
            d["b_d_025"] = bool(f & MaterialFlags.D_025)
            d["b_d_050"] = bool(f & MaterialFlags.D_050)
            d["b_d_100"] = bool(f & MaterialFlags.D_100)
            d["b_d_200"] = bool(f & MaterialFlags.D_200)
            d["b_use_Anisotropy"] = bool(f & MaterialFlags.FLAG_USE_ANISOTROPIC)
            d["b_clampV"] = bool(f & MaterialFlags.FLAG_CLAMP_V)
            d["b_clampU"] = bool(f & MaterialFlags.FLAG_CLAMP_U)
            d["b_mirrorV"] = bool(f & MaterialFlags.FLAG_FLIP_V)
            d["b_mirrorU"] = bool(f & MaterialFlags.FLAG_FLIP_U)
            d["b_ignoreSpecular"] = bool(f & MaterialFlags.FLAG_IGNORE_SPECULAR)
            d["b_useAlpha"] = bool(f & MaterialFlags.FLAG_USE_ALPHA)
            d["b_useTexture"] = bool(f & MaterialFlags.FLAG_USE_TEXTURE)
            d["b_useEnv"] = bool(f & MaterialFlags.FLAG_USE_ENV)
            d["b_doubleSided"] = bool(f & MaterialFlags.FLAG_DOUBLE_SIDE)
            d["b_flatShading"] = bool(f & MaterialFlags.FLAG_USE_FLAT)
            d["b_ignoreLighting"] = bool(f & MaterialFlags.FLAG_IGNORE_LIGHT)
            d["b_ignoreAmbient"] = False

            if f & MaterialFlags.FILTER_BLEND == MaterialFlags.FILTER_BLEND:
                d["b_texFilter"] = 'BLEND'
            elif f & MaterialFlags.FILTER_TRILINEAR:
                d["b_texFilter"] = 'TRILINEAR'
            elif f & MaterialFlags.FILTER_BILINEAR:
                d["b_texFilter"] = 'BILINEAR'
            else:
                 d["b_texFilter"] = 'POINT'

            if f & MaterialFlags.SA_INV_DST == MaterialFlags.SA_INV_DST:
                d["b_srcAlpha"] = 'INV_DST'
            elif f & MaterialFlags.SA_DST == MaterialFlags.SA_DST:
                d["b_srcAlpha"] = 'DST'
            elif f & MaterialFlags.SA_INV_SRC == MaterialFlags.SA_INV_SRC:
                d["b_srcAlpha"] = 'INV_SRC'
            elif f & MaterialFlags.SA_INV_OTHER == MaterialFlags.SA_INV_OTHER:
                d["b_srcAlpha"] = 'INV_OTHER'
            elif f & MaterialFlags.SA_SRC:
                d["b_srcAlpha"] = 'SRC'
            elif f & MaterialFlags.SA_OTHER:
                d["b_srcAlpha"] = 'OTHER'
            elif f & MaterialFlags.SA_ONE:
                d["b_srcAlpha"] = 'ONE'
            else:
                d["b_srcAlpha"] = 'ZERO'

            if f & MaterialFlags.DA_INV_DST == MaterialFlags.DA_INV_DST:
                d["b_destAlpha"] = 'INV_DST'
            elif f & MaterialFlags.DA_DST == MaterialFlags.DA_DST:
                d["b_destAlpha"] = 'DST'
            elif f & MaterialFlags.DA_INV_SRC == MaterialFlags.DA_INV_SRC:
                d["b_destAlpha"] = 'INV_SRC'
            elif f & MaterialFlags.DA_INV_OTHER == MaterialFlags.DA_INV_OTHER:
                d["b_destAlpha"] = 'INV_OTHER'
            elif f & MaterialFlags.DA_SRC:
                d["b_destAlpha"] = 'SRC'
            elif f & MaterialFlags.DA_OTHER:
                d["b_destAlpha"] = 'OTHER'
            elif f & MaterialFlags.DA_ONE:
                d["b_destAlpha"] = 'ONE'
            else:
                d["b_destAlpha"] = 'ZERO'

            material = None

            for md, mt in zip(matDicts, materials):
                if md == d:
                    material = mt
                    break

            if material is None:
                material = bpy.data.materials.new(name="material_" + str(len(materials)))
                material.saSettings.readMatDict(d)

                materials.append(material)
                matDicts.append(d)

            if material not in meshMaterials:
                meshMaterials.append(material)

            matIDs.append(meshMaterials.index(material))

        polySets: List[List[List[PolyVert]]] = [[] for m in meshMaterials]

        hasColor = False
        hasUV = False

        for m in attach.meshSets:
            if m.ColorPtr == -1:
                hasColor = True
            if m.UVPtr == -1:
                hasUV = True

            polySet: List[List[PolyVert]] = list()

            if m.polytype == enums.PolyType.Strips:
                for s, r in zip(m.polys, m.reverse):
                    if r:
                        for p in range(len(s) - 2):
                            polySet.append((s[p+1], s[p], s[p+2]))
                    else:
                        for p in range(len(s) - 2):
                            polySet.append((s[p], s[p+1], s[p+2]))
            else:
                polySet = m.polys

            polySets[matIDs[m.materialID]].extend(polySet)

        # creating mesh
        mesh = bpy.data.meshes.new(attach.name)
        matIDs = dict()

        for i, s in enumerate(polySets):
            if len(s) > 0:
                matIDs[i] = len(mesh.materials)
                mesh.materials.append(meshMaterials[i])


        bm = bmesh.new()
        bm.from_mesh(mesh)

        for v in attach.positions:
            bm.verts.new((v.x, -v.z, v.y))
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        if hasUV:
            uvLayer = bm.loops.layers.uv.new("UV0")
        if hasColor:
            colorLayer = bm.loops.layers.color.new("COL0")

        doubleFaces = 0

        for i, polySet in enumerate(polySets):
            if len(polySet) == 0:
                continue
            matID = matIDs[i]
            for p in polySet:
                if i == 1:
                    print("doin")
                verts = []
                for l in p:
                    verts.append(bm.verts[l.polyIndex])
                try:
                    face = bm.faces.new(verts)
                except Exception as e:
                    if not str(e).endswith("exists"):
                        print("Invalid triangle:", str(e))
                    else:
                        doubleFaces += 1
                    continue

                for l, pc in zip(face.loops, p):
                    if hasUV:
                        l[uvLayer].uv = pc.uv.getBlenderUV()
                    if hasColor:
                        l[colorLayer] = pc.color.toBlenderTuple()

                face.smooth = True
                face.material_index = matID


        if doubleFaces > 0 and DO:
            print("Double faces:", doubleFaces)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        bm.to_mesh(mesh)
        bm.clear()

        normals = [mathutils.Vector((n.x, -n.z, n.y)).normalized() for n in attach.normals]

        for p in mesh.polygons:
            normal = mathutils.Vector((0,0,0))
            for v in p.vertices:
                normal += normals[v]
            if normal != mathutils.Vector((0,0,0)):
                normal /= len(p.vertices)
                if normal.dot(p.normal) < 0:
                    p.flip()

        mesh.create_normals_split()
        split_normal = [normals[l.vertex_index] for l in mesh.loops]
        mesh.normals_split_custom_set(split_normal)
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 180

        o.meshes.append(mesh)
        meshes[o.meshPtr] = mesh
