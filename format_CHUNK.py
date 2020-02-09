import bpy
import mathutils

import array
import copy
import math
from typing import List, Dict, Tuple
import collections

from . import enums, fileHelper, strippifier, common
from .common import Vector3, ColorARGB, UV, BoundingBox
from .__init__ import SAMaterialSettings

DO = False
writeSpecular = True

class Vertex:
    """A single vertex in the model, stored in vertex chunksd"""

    origIndex: int
    pos: Vector3
    nrm: Vector3
    col: ColorARGB
    ninjaFlags: int

    def __init__(self,
                 origIndex: int,
                 index: int,
                 pos: Vector3,
                 nrm: Vector3,
                 col: ColorARGB,
                 weight: float):
        self.ninjaFlags = 0
        self.origIndex = origIndex
        self.index = index
        self.pos = pos
        self.nrm = nrm
        self.col = col
        if weight > 0:
            self.weight = max(weight, 1 / 255.0)
        else:
            self.weight = 0

    @property
    def index(self) -> int:
        return self.ninjaFlags & 0xFFFF

    @index.setter
    def index(self, val: int):
        self.ninjaFlags &= ~0xFFFF
        self.ninjaFlags |= min(0xFFFF, val)

    @property
    def weight(self) -> float:
        return ((self.ninjaFlags >> 16) & 0xFF) / 255.0

    @weight.setter
    def weight(self, val: float):
        self.ninjaFlags &= ~0xFF0000
        cVal = max(0, min(0xFF,  round(255 * val)))
        self.ninjaFlags |= cVal << 16

    def writeVC(self, fileW: fileHelper.FileWriter):
        self.pos.write(fileW)
        self.col.writeARGB(fileW)

    def writeNRM(self, fileW: fileHelper.FileWriter):
        self.pos.write(fileW)
        self.nrm.write(fileW)

    def writeNRMW(self, fileW: fileHelper.FileWriter):
        self.pos.write(fileW)
        self.nrm.write(fileW)
        fileW.wUInt(self.ninjaFlags)

class VertexChunk:
    """One vertex data set"""

    chunkType: enums.ChunkType
    weightType: enums.WeightStatus
    weightContinue: bool
    indexBufferOffset: int
    vertices: List[Vertex]

    def __init__(self,
                 chunkType: enums.ChunkType,
                 weightType: enums.WeightStatus,
                 weightContinue: bool,
                 indexBufferOffset: int,
                 vertices: List[Vertex]):
        self.chunkType = chunkType
        self.weightType = weightType
        self.weightContinue = weightContinue
        self.indexBufferOffset = indexBufferOffset
        self.vertices = vertices

    def vertexSize(self) -> int:
        if self.chunkType == enums.ChunkType.Vertex_VertexDiffuse8:
            return 4
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormal:
            return 6
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags:
            return 7
        else:
            print("unsupported chunk format:", self.chunkType)
            return 0

    def write(self, fileW: fileHelper.FileWriter):
        fileW.wByte(self.chunkType.value)
        fileW.wByte(self.weightType.value)

        vertexSize = self.vertexSize()

        fileW.wUShort((vertexSize * len(self.vertices)) + 1)
        fileW.wUShort(self.indexBufferOffset)
        fileW.wUShort(len(self.vertices))

        if self.chunkType == enums.ChunkType.Vertex_VertexDiffuse8:
            for v in self.vertices:
                v.writeVC(fileW)
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormal:
            for v in self.vertices:
                v.writeNRM(fileW)
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags:
            for v in self.vertices:
                v.writeNRMW(fileW)

class PolyVert:
    """A single polygon corner of a mesh"""

    index: int
    uv: UV

    def __init__(self,
                 index: int,
                 uv: UV):
        self.index = index
        self.uv = uv

    def __eq__(self, other):
        return self.index == other.index and self.uv == other.uv

    def write(self, fileW):
        fileW.wUShort(self.index)

    def writeUV(self, fileW):
        fileW.wUShort(self.index)
        self.uv.write(fileW)

class PolyChunk:
    """Base polychunk"""

    chunkType: enums.ChunkType

    def __init__(self, chunkType: enums.ChunkType):
        self.chunkType = chunkType

    def write(self, fileW: fileHelper.FileWriter):
        fileW.wByte(self.chunkType.value)

class PolyChunk_Bit(PolyChunk):
    """Base class for one byte Poly chunks"""

    data: int

    def __init__(self, chunkType: enums.ChunkType):
        super(PolyChunk_Bit, self).__init__(chunkType)
        self.data = 0

    def write(self, fileW: fileHelper.FileWriter):
        super(PolyChunk_Bit, self).write(fileW)
        fileW.wByte(self.data)

class PolyChunk_BlendAlpha(PolyChunk_Bit):
    """Holds alpha instructions for the mesh"""

    def __init__(self, instr: enums.SA2AlphaInstructions):
        super(PolyChunk_BlendAlpha, self).__init__(enums.ChunkType.Bits_BlendAlpha)
        self.alphaInstruction = instr

    @property
    def alphaInstruction(self) -> enums.SA2AlphaInstructions:
        return enums.SA2AlphaInstructions(self.data)

    @alphaInstruction.setter
    def alphaInstruction(self, val: enums.SA2AlphaInstructions):
        self.data = val.value

class PolyChunk_MipmapDAdjust(PolyChunk_Bit):
    """Mipmap distance multiplicator"""

    def __init__(self, instr: enums.MipMapDistanceAdjust):
        super(PolyChunk_MipmapDAdjust, self).__init__(enums.ChunkType.Bits_MipmapDAdjust)
        self.value = instr

    @property
    def value(self) -> enums.MipMapDistanceAdjust:
        return enums.MipMapDistanceAdjust(self.data)

    @value.setter
    def value(self, val: enums.MipMapDistanceAdjust):
        self.data = val.value

class PolyChunk_SpecularExponent(PolyChunk_Bit):
    """Specular exponent of the mesh material (unused tho? eh, who cares)"""

    def __init__(self, exponent: float):
        super(PolyChunk_SpecularExponent, self).__init__(enums.ChunkType.Bits_SpecularExponent)
        self.exponent = exponent

    @property
    def exponent(self) -> float:
        return (self.data & 0x1F) / 16.0

    @exponent.setter
    def exponent(self, val: float):
        self.data &= ~0x1F
        self.data |= min(16, round(val * 16))

class PolyChunk_CachePolygonList(PolyChunk_Bit):

    def __init__(self, index: int):
        super(PolyChunk_CachePolygonList, self).__init__(enums.ChunkType.Bits_CachePolygonList)
        self.index = index

    @property
    def index(self) -> int:
        return self.data

    @index.setter
    def index(self, val: int):
        self.data = min(0xFF, val)

class PolyChunk_DrawpolygonList(PolyChunk_Bit):

    def __init__(self, index: int):
        super(PolyChunk_DrawpolygonList, self).__init__(enums.ChunkType.Bits_DrawPolygonList)
        self.index = index

    @property
    def index(self) -> int:
        return self.data

    @index.setter
    def index(self, val: int):
        self.data = min(0xFF, val)

class PolyChunk_Texture(PolyChunk):
    """Texture info of the mesh"""

    texID: int
    flags: enums.TextureIDFlags
    anisotropy: bool
    filtering: enums.TextureFiltering

    def __init__(self,
                 texID: int,
                 flags: enums.TextureIDFlags,
                 anisotropy: bool,
                 filtering: enums.TextureFiltering):
        super(PolyChunk_Texture, self).__init__(enums.ChunkType.Tiny_TextureID)
        self.texID = texID
        self.flags = flags
        self.anisotropy = anisotropy
        self.filtering = filtering

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int):
        flags = enums.TextureIDFlags(fileR.rByte(address))
        header = fileR.rUShort(address + 1)
        texID = header & 0x1FFF
        aniso = (header & 0x2000) > 0
        filtering = enums.TextureFiltering( header >> 14 )
        return PolyChunk_Texture(texID, flags, aniso, filtering), address + 3

    def write(self, fileW: fileHelper.FileWriter):
        super(PolyChunk_Texture, self).write(fileW)
        fileW.wByte(self.flags.value)
        value = min(self.texID, 0x1FFF)
        if self.anisotropy:
            value |= 0x2000
        value |= (self.filtering.value << 14)
        fileW.wUShort(value)

class PolyChunk_Material(PolyChunk):
    """The material chunk with all 3 colors"""

    alphaInstruction: enums.SA2AlphaInstructions
    diffuse: ColorARGB
    ambient: ColorARGB
    specular: ColorARGB
    specularity: int

    def __init__(self,
                 alphaInstruction: enums.AlphaInstruction,
                 diffuse: ColorARGB,
                 ambient: ColorARGB,
                 specular: ColorARGB,
                 specularity: int):
        super(PolyChunk_Material, self).__init__(enums.ChunkType.Material_DiffuseAmbientSpecular if writeSpecular else enums.ChunkType.Material_DiffuseAmbient)
        self.alphaInstruction = alphaInstruction
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.specularity = specularity

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, chunkType: enums.ChunkType, address: int):

        alphaInstruction = enums.SA2AlphaInstructions(fileR.rByte(address))
        address += 3

        diffuse = ColorARGB()
        if chunkType.value & 0x1: # diffuse
            diffuse = ColorARGB.fromARGB(fileR.rUInt(address))
            address += 4

        ambient = ColorARGB()
        if chunkType.value & 0x2: # ambient
            ambient = ColorARGB.fromARGB(fileR.rUInt(address))
            address += 4

        specular = ColorARGB()
        specularity = 255
        if chunkType.value & 0x4: # specular
            specular = ColorARGB.fromARGB(fileR.rUInt(address))
            specularity = specular.a
            specular.a = 255
            address += 4

        return PolyChunk_Material(alphaInstruction, diffuse, ambient, specular, specularity), address

    def write(self, fileW: fileHelper.FileWriter):
        super(PolyChunk_Material, self).write(fileW)
        fileW.wByte(self.alphaInstruction.value)
        fileW.wUShort(6 if writeSpecular else 4) # size (amount of 2 byte sets)
        self.diffuse.writeARGB(fileW)
        self.ambient.writeARGB(fileW)
        if writeSpecular:
            self.specular.writeRGB(fileW)
            fileW.wByte(self.specularity)

class PolyChunk_Strip(PolyChunk):

    flags: enums.StripFlags
    readSize: int
    readUserFlags: int
    strips: List[List[PolyVert]] # list of strips
    reversedStrips: List[bool]

    def __init__(self,
                 hasUV: bool,
                 flags: enums.StripFlags,
                 strips: List[List[PolyVert]],
                 reversedStrips: List[bool] = None):
        if hasUV:
            super(PolyChunk_Strip, self).__init__(enums.ChunkType.Strip_StripUVN)
        else:
            super(PolyChunk_Strip, self).__init__(enums.ChunkType.Strip_Strip)
        self.flags = flags
        self.strips = strips
        if reversedStrips is None:
            self.reversedStrips = [False] * len(strips)
        else:
            self.reversedStrips = reversedStrips

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, chunkType: enums.ChunkType, address: int):

        flags = enums.StripFlags(fileR.rByte(address))
        address += 1
        size = fileR.rUShort(address)
        address += 2
        header = fileR.rUShort(address)
        stripCount = header & 0x3FFF
        userFlagCount = header >> 14
        #if userFlagCount > 0:
        #    print("  Userflag count:", userFlagCount)
        address += 2

        polyVerts = list()
        reversedStrips = list()

        c = chunkType.value
        hasUV = c == 65 or c == 66 or c == 68 or c == 69 or c == 71 or c == 72
        hasNRM = 1 if c >= 67 and c <= 69 else 0
        hasCOL = 1 if c >= 70 and c <= 72 else 0


        for i in range(stripCount):
            strip = list()
            pCount = fileR.rShort(address)
            reverse = pCount < 0

            if reverse:
                pCount = abs(pCount)

            address += 2
            for p in range(pCount):
                vIndex = fileR.rUShort(address)
                address += 2

                # check uv
                uv = UV()
                if hasUV:
                    u = fileR.rShort(address)
                    v = fileR.rShort(address + 2)
                    uv = UV()
                    uv.x = u
                    uv.y = v
                    address += 4

                # check normals
                address += 12 * hasNRM
                # check colors
                address += 4 * hasCOL

                address += userFlagCount * 2
                strip.append(PolyVert(vIndex, uv))

            #if len(strip) == 3:
            #    continue

            reversedStrips.append(reverse)
            polyVerts.append(strip)

        polyChunk = PolyChunk_Strip(hasUV, flags, polyVerts, reversedStrips)
        polyChunk.readSize = size
        polyChunk.readUserFlags = userFlagCount

        return polyChunk, address

    def getSize(self):
        size = 1
        stripSize = 3 if self.chunkType == enums.ChunkType.Strip_StripUVN else 1
        for s in self.strips:
            size += (len(s) * stripSize) + 1
        return size

    def write(self, fileW: fileHelper.FileWriter):
        super(PolyChunk_Strip, self).write(fileW)
        fileW.wByte(self.flags.value)
        fileW.wUShort(self.getSize())

        fileW.wUShort(min(0x3FFF, len(self.strips)))

        for s, rev in zip(self.strips, self.reversedStrips):
            size = min(0x7FFF, len(s)) * (-1 if rev else 1)
            fileW.wShort(size)
            if self.chunkType == enums.ChunkType.Strip_StripUVN:
                for p in s:
                    p.writeUV(fileW)
            else:
                for p in s:
                    p.write(fileW)


class Container(object):
    pass

class Attach:
    """Chunk mesh data"""

    name: str
    vertexChunks: List[VertexChunk]
    polyChunks: List[PolyChunk]
    bounds: BoundingBox

    def __init__(self,
                 name: str,
                 vertexChunks: List[VertexChunk],
                 polyChunks: List[PolyChunk],
                 bounds: BoundingBox):
        self.name = name
        self.polyChunks = polyChunks
        self.bounds = bounds

        self.vertexChunks = list()
        # getting the most out of the vertex chunks
        for v in vertexChunks:
            if v.vertexSize() * len(v.vertices) < 0xFFFF:
                self.vertexChunks.append(v)
            else:
                vertices = v.vertices
                offset = v.indexBufferOffset

                while len(vertices) > 0:
                    vCount = min(0xFFFF - offset, math.floor(min(len(vertices) * v.vertexSize(), 0xFFFF) / v.vertexSize()))

                    chunkV = vertices[:vCount]
                    vertices = vertices[vCount:]
                    print("set:", len(chunkV), len(vertices))

                    self.vertexChunks.append( VertexChunk(v.chunkType, v.weightType, v.weightContinue, offset, chunkV) )
                    offset += vCount

        # optimizing poly chunks (well, only the strips)
        self.polyChunks = list()
        for p in polyChunks:
            if not isinstance(p, PolyChunk_Strip):
                self.polyChunks.append(p)
            else:
                p: PolyChunk_Strip = p

                if p.getSize() > 0xFFFF or len(p.strips) > 0x3FFF:

                    polyCSize = 3 if p.chunkType == enums.ChunkType.Strip_StripUVN else 1

                    cSize = 1
                    strips = list()
                    revStrips = list()

                    for c in range(len(strips)):
                        strip =  p.strips[c]
                        stripSize = (len(strip) * polyCSize) + 1

                        if cSize + stripSize > 0xFFFF or len(strips) >= 0x3FFF:
                            self.polyChunks.append(PolyChunk_Strip(polyCSize == 3, p.flags, strips, revStrips))
                            strips = list()
                            revStrips = list()
                            cSize = 1

                        strips.append(strip)
                        revStrips.append(p.reversedStrips[c])

                        cSize += stripSize

                    if len(strips) > 0:
                        self.polyChunks.append(PolyChunk_Strip(polyCSize == 3, p.flags, strips, revStrips))

                else:
                    self.polyChunks.append(p)

    @classmethod
    def getPolygons(cls, mesh: bpy.types.Mesh,
                    writeUVs: bool,
                    polyVerts: List[PolyVert],
                    materials: Dict[str, bpy.types.Material]):

        # getting the distinct polygons
        distinctPolys = list()
        IDs = [0] * len(polyVerts)

        distinctPolys, IDs = common.getDistinctwID(polyVerts)

        polygons: List[List[PolyVert]] = [[] for m in range(len(mesh.materials))]
        if len(polygons) == 0:
            polygons.append(list())

        # assembling the polygons
        for p in mesh.polygons:
            for l in p.loop_indices:
                polygons[p.material_index].append(IDs[l])

        # converting triangle lists to strips
        strips: List[List[List[PolyVert]]] = list() # material specific -> strip -> polygon
        stripRev: List[List[bool]] = list()

        for l in polygons:
            if len(l) == 0:
                strips.append(None)
                stripRev.append(None)
                continue
            stripIndices = strippifier.Strippify(l, doSwaps=False, concat=False)

            polyStrips = [None] * len(stripIndices)
            polyStripsRev = [True] * len(stripIndices)

            for i, strip in enumerate(stripIndices):
                if strip[0] == strip[1]:
                    polyStripsRev[i] = False
                    strip = strip[1:]

                tStrip = [0] * len(strip)
                for j, index in enumerate(strip):
                    tStrip[j] = distinctPolys[index]
                polyStrips[i] = tStrip

            strips.append(polyStrips)
            stripRev.append(polyStripsRev)

        # generating polygon chunks
        polyChunks: List[PolyChunk] = list()

        for mID, strip in enumerate(zip(strips, stripRev)):
            l, lrev = strip
            if l is None:
                continue

            # getting material
            stripUVs = writeUVs
            material = None
            if len(mesh.materials) == 0:
                print(" Mesh has no materials")
            else:
                matName = mesh.materials[mID].name
                if matName in materials:
                    material = materials[matName]
                else:
                    print(" Material", matName, "not found")

            stripFlags = enums.StripFlags.null

            if material is None:
                polyChunks.append(PolyChunk_Material(enums.SA2AlphaInstructions.SA_SRC | enums.SA2AlphaInstructions.DA_INV_SRC, ColorARGB(), ColorARGB(), ColorARGB(), 255))
                polyChunks.append(PolyChunk_Texture(0, enums.TextureIDFlags.null, True, enums.TextureFiltering.Bilinear))
            else:
                matProps: SAMaterialSettings = material.saSettings

                # getting texture info
                textureFlags = enums.TextureIDFlags.null

                if matProps.b_d_025:
                    textureFlags |= enums.TextureIDFlags.D_025
                if matProps.b_d_050:
                    textureFlags |= enums.TextureIDFlags.D_050
                if matProps.b_d_100:
                    textureFlags |= enums.TextureIDFlags.D_100
                if matProps.b_d_200:
                    textureFlags |= enums.TextureIDFlags.D_200
                if matProps.b_clampV:
                    textureFlags |= enums.TextureIDFlags.CLAMP_V
                if matProps.b_clampU:
                    textureFlags |= enums.TextureIDFlags.CLAMP_U
                if matProps.b_mirrorV:
                    textureFlags |= enums.TextureIDFlags.FLIP_U
                if matProps.b_mirrorU:
                    textureFlags |= enums.TextureIDFlags.FLIP_V

                filtering = enums.TextureFiltering.Point

                if matProps.b_texFilter == 'BILINEAR':
                    filtering = enums.TextureFiltering.Bilinear
                elif matProps.b_texFilter == 'TRILINEAR':
                    filtering = enums.TextureFiltering.Trilinear
                elif matProps.b_texFilter == 'BLEND':
                    filtering = enums.TextureFiltering.Blend



                # getting alpha
                alphaflags = enums.SA2AlphaInstructions.null
                if matProps.b_useAlpha:
                    from .enums import SA2AlphaInstructions

                    src = matProps.b_srcAlpha
                    if src == 'ONE':
                        alphaflags |= SA2AlphaInstructions.SA_ONE
                    elif src == 'OTHER':
                        alphaflags |= SA2AlphaInstructions.SA_OTHER
                    elif src == 'INV_OTHER':
                        alphaflags |= SA2AlphaInstructions.SA_INV_OTHER
                    elif src == 'SRC':
                        alphaflags |= SA2AlphaInstructions.SA_SRC
                    elif src == 'INV_SRC':
                        alphaflags |= SA2AlphaInstructions.SA_INV_SRC
                    elif src == 'DST':
                        alphaflags |= SA2AlphaInstructions.SA_DST
                    elif src == 'INV_DST':
                        alphaflags |= SA2AlphaInstructions.SA_INV_DST

                    dst = matProps.b_destAlpha
                    if dst == 'ONE':
                        alphaflags |= SA2AlphaInstructions.DA_ONE
                    elif dst == 'OTHER':
                        alphaflags |= SA2AlphaInstructions.DA_OTHER
                    elif dst == 'INV_OTHER':
                        alphaflags |= SA2AlphaInstructions.DA_INV_OTHER
                    elif dst == 'SRC':
                        alphaflags |= SA2AlphaInstructions.DA_SRC
                    elif dst == 'INV_SRC':
                        alphaflags |= SA2AlphaInstructions.DA_INV_SRC
                    elif dst == 'DST':
                        alphaflags |= SA2AlphaInstructions.DA_DST
                    elif dst == 'INV_DST':
                        alphaflags |= SA2AlphaInstructions.DA_INV_DST
                else:
                    alphaflags = enums.SA2AlphaInstructions.SA_SRC | enums.SA2AlphaInstructions.DA_INV_SRC

                polyChunks.append(PolyChunk_Material(alphaflags, ColorARGB(matProps.b_Diffuse), ColorARGB(matProps.b_Ambient), ColorARGB(matProps.b_Specular), round(matProps.b_Exponent * 255)))
                polyChunks.append(PolyChunk_Texture(matProps.b_TextureID, textureFlags, matProps.b_use_Anisotropy, filtering))

                #getting strip flags
                if matProps.b_ignoreLighting:
                    stripFlags |= enums.StripFlags.IGNORE_LIGHT
                if matProps.b_ignoreSpecular:
                    stripFlags |= enums.StripFlags.INGORE_SPECULAR
                if matProps.b_ignoreAmbient:
                    stripFlags |= enums.StripFlags.IGNORE_AMBIENT
                if matProps.b_useAlpha:
                    stripFlags |= enums.StripFlags.USE_ALPHA
                if matProps.b_doubleSided:
                    stripFlags |= enums.StripFlags.DOUBLE_SIDE
                if matProps.b_flatShading:
                    stripFlags |= enums.StripFlags.FLAT_SHADING
                if matProps.b_useEnv:
                    stripFlags |= enums.StripFlags.ENV_MAPPING
                    stripUVs = False
                if matProps.b_unknown:
                    stripFlags |= enums.StripFlags.Unknown

            polyChunks.append(PolyChunk_Strip(stripUVs, stripFlags, l, lrev))

        return polyChunks

    @classmethod
    def fromMesh(cls, mesh: bpy.types.Mesh,
                 export_matrix: mathutils.Matrix,
                 materials: List[bpy.types.Material]):

        vertexType = mesh.saSettings.sa2ExportType
        if vertexType == 'VC' and len(mesh.vertex_colors) == 0:
            vertexType = 'NRM'
        extraOffset = mesh.saSettings.sa2IndexOffset


        writeUVs = len(mesh.uv_layers) > 0

        vertices: List[Vertex] = list()
        polyVerts: List[PolyVert] = list()

        # getting normals
        normals = common.getNormalData(mesh)

        if vertexType == 'VC':
            verts: List[List[Vertex]] = [[] for v in mesh.vertices]

            # generating the vertices with their colors
            for l in mesh.loops:
                vert = mesh.vertices[l.vertex_index]
                col = ColorARGB(mesh.vertex_colors[0].data[l.index].color)

                # only create the vertex if there isnt one with the same color already
                foundV: Vertex = None
                for v in verts[l.vertex_index]:
                    if v.col == col:
                        foundV = v
                        break

                if foundV is None:
                    foundV = Vertex(l.vertex_index, 0, Vector3(export_matrix @ vert.co), Vector3(), col, 0)
                    verts[l.vertex_index].append(foundV)

                uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
                polyVerts.append(PolyVert(foundV, uv))

            # correcting indices
            i = 0
            for v in verts:
                for vt in v:
                    vt.index = i
                    vertices.append(vt)
                    i += 1

            for p in polyVerts:
                p.index = p.index.index + extraOffset

        else: # normals are a lot simpler to generate (luckily)
            for v in mesh.vertices:
                vertices.append( Vertex(v.index, v.index, Vector3(export_matrix @ v.co), Vector3(export_matrix @ normals[v.index]), None, 0) )

            for l in mesh.loops:
                uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
                polyVert = PolyVert(l.vertex_index + extraOffset, uv)
                polyVerts.append(polyVert)

        # creating the vertex chunk
        chunkType = enums.ChunkType.Vertex_VertexDiffuse8 if vertexType == 'VC' else enums.ChunkType.Vertex_VertexNormal
        vertexChunks: List[VertexChunk] = [VertexChunk(chunkType, enums.WeightStatus.Start, False, extraOffset, vertices)]

        polyChunks = Attach.getPolygons(mesh, writeUVs, polyVerts, materials)

        bounds = BoundingBox(mesh.vertices)
        bounds.adjust(export_matrix)

        return Attach(mesh.name, vertexChunks, polyChunks, bounds)

    def write(self,
              fileW: fileHelper.FileWriter,
              labels: dict,
              meshDict: dict = None):
        global DO

        if self.name is None:
            self.name = "attach_" + common.hex4(fileW.tell())

        vertexChunkPtr = 0
        if len(self.vertexChunks) > 0:
            # writing vertex chunks
            vertexChunkPtr = fileW.tell()
            for v in self.vertexChunks:
                v.write(fileW)

            # writing vertex chunk terminator
            fileW.wULong(enums.ChunkType.End.value)
            labels[vertexChunkPtr] = "cnk_" + self.name + "_vtx"

        polyChunkPtr = 0
        if len(self.polyChunks) > 0:
            # writing polygon chunks
            polyChunkPtr = fileW.tell()
            for p in self.polyChunks:
                p.write(fileW)

            # writing poly chunk terminator
            fileW.wUShort(enums.ChunkType.End.value)
            labels[polyChunkPtr] = "cnk_" + self.name + "_poly"

        attachPtr = fileW.tell()
        if meshDict is not None:
            meshDict[self.name] = attachPtr
        labels[attachPtr] = "cnk_" + self.name

        fileW.wUInt(vertexChunkPtr)
        fileW.wUInt(polyChunkPtr)
        self.bounds.write(fileW)

        if DO:
            print("  Chunk mesh:", self.name)
            print("    Vertex chunks:", len(self.vertexChunks))
            for v in self.vertexChunks:
                print("     vertices:", len(v.vertices))
            print("    Vertex chunk ptr:", vertexChunkPtr)
            print("    Poly chunks:", len(self.polyChunks))
            print("    Poly chunk ptr:", polyChunkPtr, "\n")

        return attachPtr

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int, meshID: int, labels: dict):

        if address in labels:
            name: str = labels[address]
            if name.startswith("cnk_"):
                name = name[4:]
        else:
            name = "Attach_" + str(meshID)

        # reading vertex chunks
        vertexChunks: List[Vertex] = list()
        tmpAddr = fileR.rUInt(address)

        if tmpAddr > 0:
            chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
            while chunkType != enums.ChunkType.End:
                flags = fileR.rByte(tmpAddr + 1)
                weightStatus = enums.WeightStatus(flags & 0x3)
                otherFlags = flags & ~0x3
                size = fileR.rUShort(tmpAddr+2)
                indexBufferOffset = fileR.rUShort(tmpAddr + 4)
                vertexCount = fileR.rUShort(tmpAddr + 6)

                vertices = list()

                tmpAddr += 8

                for i in range(vertexCount):
                    # getting the position (part of every vertex)
                    posX = fileR.rFloat(tmpAddr)
                    posY = fileR.rFloat(tmpAddr + 4)
                    posZ = fileR.rFloat(tmpAddr + 8)
                    pos = Vector3((posX, -posZ, posY))
                    tmpAddr += 12

                    col = None

                    # getting color
                    if chunkType == enums.ChunkType.Vertex_VertexDiffuse8 or chunkType == enums.ChunkType.Vertex_VertexNormalDiffuse8:
                        col = ColorARGB.fromARGB(fileR.rUInt(tmpAddr))
                        tmpAddr += 4

                    weight = 0
                    index = i
                    nrm = None

                    if chunkType == enums.ChunkType.Vertex_VertexNormal or chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags or chunkType == enums.ChunkType.Vertex_VertexNormalDiffuse8:
                        nrmX = fileR.rFloat(tmpAddr)
                        nrmY = fileR.rFloat(tmpAddr + 4)
                        nrmZ = fileR.rFloat(tmpAddr + 8)
                        nrm = Vector3((nrmX, -nrmZ, nrmY))
                        tmpAddr += 12

                        if chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags:
                            ninjaFlags = fileR.rUInt(tmpAddr)
                            weight = ((ninjaFlags >> 16) & 0xFF) / 255.0
                            index = ninjaFlags & 0xFFFF
                            tmpAddr += 4

                    vertices.append(Vertex(index, index, pos, nrm, col, weight))

                vertexChunks.append( VertexChunk(chunkType, weightStatus, (otherFlags & 0x80) > 0, indexBufferOffset, vertices))

                chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
        # reading polygons chunks

        polygonChunks = list()
        tmpAddr = fileR.rUInt(address + 4)
        if tmpAddr > 0:
            chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
            while chunkType != enums.ChunkType.End:
                chunk = PolyChunk(chunkType)

                tmpAddr += 1
                if chunkType == enums.ChunkType.Bits_BlendAlpha:
                    chunk = PolyChunk_BlendAlpha(enums.SA2AlphaInstructions.null)
                elif chunkType == enums.ChunkType.Bits_CachePolygonList:
                    chunk = PolyChunk_CachePolygonList(0)
                elif chunkType == enums.ChunkType.Bits_DrawPolygonList:
                    chunk = PolyChunk_DrawpolygonList(0)
                elif chunkType == enums.ChunkType.Bits_MipmapDAdjust:
                    chunk = PolyChunk_MipmapDAdjust(enums.MipMapDistanceAdjust.null)
                elif chunkType == enums.ChunkType.Bits_SpecularExponent:
                    chunk = PolyChunk_SpecularExponent(0)
                elif chunkType == enums.ChunkType.Tiny_TextureID:
                    chunk, tmpAddr = PolyChunk_Texture.read(fileR, tmpAddr)
                elif chunkType.value > 15 and chunkType.value < 32: # material!
                    chunk, tmpAddr = PolyChunk_Material.read(fileR, chunkType, tmpAddr)
                elif chunkType.value > 63 and chunkType.value < 76: # strips
                    chunk, tmpAddr = PolyChunk_Strip.read(fileR, chunkType, tmpAddr)

                if isinstance(chunk, PolyChunk_Bit):
                    chunk.data = fileR.rByte(tmpAddr)
                    tmpAddr += 1

                    #if (chunkType == enums.ChunkType.Bits_CachePolygonList or chunkType == enums.ChunkType.Bits_DrawPolygonList) and DO:
                    #    print(chunk.data)

                if DO:
                    print(chunkType)

                polygonChunks.append(chunk)
                chunkType = enums.ChunkType(fileR.rByte(tmpAddr))

        return Attach(name, vertexChunks, polygonChunks, None)

    def debug(self):
        print("  Chunk mesh:", self.name)
        print("    Vertex chunks:", len(self.vertexChunks))
        print("    Poly chunks:", len(self.polyChunks))

# stuff for weighted exporting and importing

def fromWeightData(boneMap: Dict[str, mathutils.Matrix], # [BoneName] = boneMatrix
                    meshData: List[common.ArmatureMesh],
                    export_matrix: mathutils.Matrix,
                    materials: List[bpy.types.Material]) -> Dict[str, Attach]:

    # these will carry the chunks for the attaches
    boneVertChunks: Dict[str, List[VertexChunk]] = dict()
    bonePolyChunks: Dict[str, List[PolyChunk]] = dict()

    for b in boneMap.keys():
        boneVertChunks[b] = list()
        bonePolyChunks[b] = list()

    for m in meshData:
        # data for every bone that has weights in this mesh
        boneData: Dict[int, Tuple[enums.WeightStatus, mathutils.Matrix, List[Vertex], enums.ChunkType]] = dict()

        for b in m.weightMap.keys():
            index, status = m.weightMap[b]
            boneData[index] = (status, export_matrix @ (boneMap[b].inverted() @ m.model.origObject.matrix_world), list(), enums.ChunkType.Vertex_VertexNormalNinjaFlags)

        mesh = m.model.processedMesh
        normals = common.getNormalData(mesh)

        # if the only bone is index -1, then just write the entire mesh to the bone
        if list(boneData.keys())[0] == -1:
            status, matrix, vList, _ = boneData[-1]
            for v in mesh.vertices:
                vList.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), None, 1) )
            boneData[-1] = (status, matrix, vList, enums.ChunkType.Vertex_VertexNormal)

        else:
            for v in mesh.vertices:
                # get all used weights and the average weight, for proper normalizing
                cWeight: Dict[int, float] = dict()
                weightsAdded = 0
                for g in v.groups:
                    if g.group in boneData:
                        weightsAdded += g.weight
                        cWeight[g.group] =  g.weight

                # if there are no used weights, then attach it to index -2
                if len(cWeight) == 0:
                    status, matrix, vList, _ = boneData[-2]
                    vList.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), None, 1) )
                else:
                    for b in boneData.keys():
                        if b not in cWeight:
                            cWeight[b] = 0
                    for k, weight in cWeight.items():
                        if weightsAdded > 0:
                            weight = weight / weightsAdded
                        status, matrix, vList, _ = boneData[k]

                        if status == enums.WeightStatus.Start or weight > 0:
                            vList.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), None, weight) )


        # getting polygon data

        writeUVs = len(mesh.uv_layers) > 0
        polyVerts: List[PolyVert] = list()
        for l in mesh.loops:
            uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
            polyVert = PolyVert(l.vertex_index + m.indexBufferOffset, uv)
            polyVerts.append(polyVert)

        polyChunks = Attach.getPolygons(mesh, writeUVs, polyVerts, materials)

        assignedPolys = False
        for b, t in m.weightMap.items():
            index, status = t
            _, matrix, vList, chunkType = boneData[index]
            vChunk = VertexChunk(chunkType, status, False, m.indexBufferOffset, vList)
            boneVertChunks[b].append(vChunk)

            if len(m.weightMap) == 1 or status == enums.WeightStatus.End:
                bonePolyChunks[b].extend(polyChunks)
                assignedPolys = True

    boneAttaches: Dict[str, Attach] = dict()

    for b in list(boneMap.keys()):
        vChunks = boneVertChunks[b]
        pChunks = bonePolyChunks[b]

        if len(vChunks) > 0:

            bounds = BoundingBox(None)
            #if len(pChunks) > 0:
            vertices = list()
            for vc in vChunks:
                for v in vc.vertices:
                    vert = Container()
                    vert.co = v.pos
                    vertices.append(vert)
            bounds = BoundingBox(vertices)

            boneAttaches[b] = Attach("atc_" + b, vChunks, pChunks, bounds)

    return boneAttaches


class ProcessedVert:

    model: common.Model
    position: Vector3
    normal: Vector3
    color: ColorARGB
    weight: float

    def __init__(self,
                 model: common.Model,
                 vert: Vertex):
        self.model = model
        self.position = vert.pos
        self.normal = vert.nrm
        self.color = vert.col
        self.weight = vert.weight

class BufferedVertex:

    vertices: List[ProcessedVert]

    def __init__(self, vertices = list()):
        self.vertices = vertices

    def reset(self, newVert: ProcessedVert):
        self.vertices = [newVert]

    def add(self, vert: ProcessedVert):
        self.vertices.append(vert)

    def getWorldPos(self, armatureMatrix):
        pos = Vector3((0,0,0))
        if armatureMatrix is None:
            for v in self.vertices:
                pos += (v.model.matrix_world @ v.position) * v.weight
        else:
            for v in self.vertices:
                pos += ((armatureMatrix.inverted() @ v.model.matrix_world) @ v.position) * v.weight
        return (pos.x, pos.y, pos.z)

    def getWorldNrm(self, armatureMatrix):
        nrm = Vector3((0,0,0))
        if armatureMatrix is None:
            for v in self.vertices:
                if v.normal is not None:
                    nrm += (v.model.matrix_world.to_3x3() @ v.normal) * v.weight
        else:
            for v in self.vertices:
                if v.normal is not None:
                    nrm += ((armatureMatrix.inverted() @ v.model.matrix_world).to_3x3() @ v.normal) * v.weight
        nrm.normalize()

        return (nrm.x, nrm.y, nrm.z)

    def getLocalPos(self):
        """only use if only one item in self.vertices"""
        pos = self.vertices[0].position
        return (pos.x, pos.y, pos.z)

    def getLocalNrm(self):
        """only use if only one item in self.vertices"""
        nrm = self.vertices[0].normal
        if nrm is None:
            return (0,0,0)
        else:
            return (nrm.x, nrm.y, nrm.z)

    def hasColor(self):
        for v in self.vertices:
            if v.color is not None:
                return True
        return False

    def getColor(self):
        if len(self.vertices) == 0:
            print("No vertices to fetch color from")
            return mathutils.Vector(ColorARGB().toBlenderTuple())

        return mathutils.Vector(self.vertices[-1].color.toBlenderTuple())

class processedAttach:
    attachID: int
    attachName: str
    vertices: Dict[int, BufferedVertex]
    polyChunks: List[PolyChunk]
    affectedBy: List[common.Model]

    hasColor: bool

    def __init__(self,
                 attachID: int,
                 attachName: str,
                 vertices: Dict[int, BufferedVertex],
                 polyChunks: List[PolyChunk],
                 hasColor: bool):
        self.attachID = attachID
        self.attachName = attachName
        self.vertices = vertices
        self.polyChunks = polyChunks
        self.hasColor = hasColor

        self.affectedBy = list()

        for bv in vertices.values():
            for v in bv.vertices:
                if v.model not in self.affectedBy:
                    self.affectedBy.append(v.model)

    def name(self, isArmature: bool) -> str:
        if isArmature:
            return "Mesh_" + str(self.attachID).zfill(2)
        else:
            return self.attachName

def OrderChunks(models: List[common.Model], attaches: Dict[int, Attach]) -> Dict[int, processedAttach]:

    vertexBuffer: List[BufferedVertex] = [None] * 0x7FFF # [BufferedVertex() for v in range(0x7FFF)]
    polyCaches: List[List[PolyChunk]] = [[] for i in range(16)] # lets hope nothing uses 17 caches

    pAttaches: Dict[int, processedAttach] = dict()

    # we are iterating through the models, and not the attaches, as the attach order needs to be kept
    for o in models:
        if o.meshPtr == 0 or o.meshPtr not in attaches or o.meshPtr in pAttaches:
            continue
        attach = attaches[o.meshPtr]
        if DO:
            print("  Object:", o.name)
            print("  Attach:", attach.name, "\n")
            print("  Vertex Chunks:\n")
            for v in attach.vertexChunks:
                print("     Type:", v.chunkType)
                print("     WeightType:", v.weightType)
                print("     WeightContinue:", v.weightContinue)
                print("     Index Offset:", v.indexBufferOffset)
                print("     VertexCount:", len(v.vertices), "\n")

        # setting vertex buffers
        for vtxCnk in attach.vertexChunks:

            typ = vtxCnk.weightType == enums.WeightStatus.Start

            # setting them accordingly to the model type
            for v in vtxCnk.vertices:
                # getting the verbex buffer
                vbID = vtxCnk.indexBufferOffset + v.index
                # create one if they dont exist yet
                if vertexBuffer[vbID] == None:
                    vertexBuffer[vbID] = BufferedVertex()
                vb = vertexBuffer[vbID]

                # setting the vertex buffer
                if typ:
                    vb.reset(ProcessedVert(o, v))
                else:
                    vb.add(ProcessedVert(o, v))

        polyChunks = list() # the chunks that we are about to process

        # defaulting the cache index to -1, which means that no cache is being used
        cacheIndex = -1

        # iterating through the polygon chunks
        for polyCnk in attach.polyChunks:
            # if the cache id is set, then place the chunk inside the cache
            if cacheIndex > -1:
                polyCaches[cacheIndex].append(polyCnk)
            else:
                # if the chunk is a CachePolygonList, then the future polygon chunks should be stored in a cache
                if polyCnk.chunkType == enums.ChunkType.Bits_CachePolygonList:
                    cacheIndex = polyCnk.data
                    polyCaches[cacheIndex] = list()
                elif polyCnk.chunkType == enums.ChunkType.Bits_DrawPolygonList: # if its a DrawPolygonList, then the chunks stored in the cache should be added to the current list
                    polyChunks.extend(polyCaches[polyCnk.data])
                else: # otherwise, just add it to the regular list
                    polyChunks.append(polyCnk)

        # only if there are polychunks available should we generate a processed attach.
        if len(polyChunks) > 0:
            if DO:
                print(" Active Poly Chunks: ", len(polyChunks) ,"\n")
                for p in polyChunks:
                    print("    Chunktype:", p.chunkType)
                    c = p.chunkType.value
                    if c > 63 and c < 76:
                        hasUV = c == 65 or c == 66 or c == 68 or c == 69 or c == 71 or c == 72
                        hasNRM = c >= 67 and c <= 69
                        hasCOL = c >= 70 and c <= 72
                        print("     UV:", hasUV, ", NRM:", hasNRM, ", COL:", hasCOL)
                        print("     flags:", p.flags)
                        print("     size:", p.readSize)
                        print("     stripCount:", len(p.strips))
                        print("     userflags:", p.readUserFlags, "\n")
                        # getting the vertice that the polygons require

            vertices: Dict[int, BufferedVertex] = dict()

            hasColor = False

            # here we are getting the vertices which are being used
            for c in polyChunks:
                if c.chunkType.value > 63 and c.chunkType.value < 76: # its a strip
                    for s in c.strips: # for every strip...
                        for p in s: # for every polygon corner in the strip...
                            if p.index not in vertices:
                                vert = vertexBuffer[p.index]
                                # if it was written only once, then the onjly vertex as a whole has the weight 1
                                if len(vert.vertices) == 1:
                                    vert.vertices[0].weight = 1

                                vertices[p.index] = BufferedVertex(vert.vertices.copy())

                                # checking if the vertex has colors
                                if not hasColor and vert.hasColor():
                                    hasColor = True

            vertices = collections.OrderedDict(sorted(vertices.items()))

            pAttaches[o.meshPtr] = processedAttach(len(pAttaches), attach.name, vertices, polyChunks, hasColor)

    return pAttaches

def ProcessChunkData(models: List[common.Model], attaches: Dict[int, processedAttach], noDoubleVerts: bool, armatureRoot: common.Model):

    import bmesh
    from .__init__ import SAMaterialSettings

    tmpMat = SAMaterialSettings.getDefaultMatDict()

    # the converted meshes
    meshes: Dict[int, bpy.types.Mesh] = dict()

    # you cant hash a dictionary in a dictionary, so i make a "virtual" dictionary
    materials: List[bpy.types.Material] = list()
    matDicts: List[dict] = list()

    isArmature = armatureRoot != None
    armatureMatrix = armatureRoot.matrix_world if isArmature else None

    for o in models:
        if o.meshPtr == 0 or o.meshPtr not in attaches:
            continue
        if o.meshPtr in meshes:
            o.meshes.append(meshes[o.meshPtr])
            continue

        a = attaches[o.meshPtr]
        # calculating vertices
        normals = list()
        vIDs = dict()
        vDistinct = list()
        if isArmature:
            # removing double vertices kinda causes trouble...
            for i, e in enumerate(a.vertices.items()):
                nrm = e[1].getWorldNrm(armatureMatrix)
                normals.append(nrm)
                vDistinct.append((e[1].getWorldPos(armatureMatrix), nrm))
                vIDs[e[0]] = i
        else:

            if noDoubleVerts:
                vertexSets = list()
                for v in a.vertices.values():
                    vertexSets.append((v.getLocalPos(), v.getLocalNrm()))
                vDistinct, t = common.getDistinctwID(vertexSets)

                normals = [d[1] for d in vDistinct]

                for i, k in enumerate(a.vertices.keys()):
                    vIDs[k] = t[i]
            else:
                for i, e in enumerate(a.vertices.items()):
                    nrm = e[1].getLocalNrm()
                    normals.append(nrm)
                    vDistinct.append((e[1].getLocalPos(), nrm))
                    vIDs[e[0]] = i



        # getting the polygons
        polygons: List[List[PolyVert]] = list()
        matMarkers = dict()
        meshMaterials = list()
        filteredPolys = 0
        from .enums import StripFlags
        for c in a.polyChunks:
            if c.chunkType.value > 63 and c.chunkType.value < 76: # if its a strip chunk

                f = c.flags
                tmpMat["b_ignoreLighting"] = bool(f & StripFlags.IGNORE_LIGHT)
                tmpMat["b_ignoreSpecular"] = bool(f & StripFlags.INGORE_SPECULAR)
                tmpMat["b_ignoreAmbient"] = bool(f & StripFlags.IGNORE_AMBIENT)
                tmpMat["b_useAlpha"] = bool(f & StripFlags.USE_ALPHA)
                tmpMat["b_doubleSided"] = bool(f & StripFlags.DOUBLE_SIDE)
                tmpMat["b_flatShading"] = bool(f & StripFlags.FLAT_SHADING)
                tmpMat["b_useEnv"] = bool(f & StripFlags.ENV_MAPPING)
                tmpMat["b_unknown"] = bool(f & StripFlags.Unknown)

                material = None

                for i, key in enumerate(matDicts):
                    if key == tmpMat:
                        material = materials[i]
                        break

                if material is None:
                    material = bpy.data.materials.new(name="material_" + str(len(materials)))
                    material.saSettings.readMatDict(tmpMat)

                    materials.append(material)
                    matDicts.append(copy.deepcopy(tmpMat))


                if material not in meshMaterials:
                    meshMaterials.append(material)

                matIndex = meshMaterials.index(material)

                if len(matMarkers) == 0 or matMarkers[lastAdded] != matIndex:
                    lastAdded = len(polygons)
                    matMarkers[lastAdded] = matIndex


                for si, s in enumerate(c.strips):
                    rev = c.reversedStrips[si]
                    for p in range(len(s) - 2):
                        if rev:
                            p = (s[p+1], s[p], s[p+2])
                        else:
                            p = (s[p], s[p+1], s[p+2])
                        rev = not rev
                        if p[0] == p[1] or p[1] == p[2] or p[2] == p[0]:
                            filteredPolys += 1
                            continue
                        polygons.append(p)

            # if material or blendalpha
            elif (c.chunkType.value > 15 and c.chunkType.value < 32) or c.chunkType == enums.ChunkType.Bits_BlendAlpha:
                instr = c.alphaInstruction
                from .enums import SA2AlphaInstructions

                if instr & SA2AlphaInstructions.SA_INV_DST == SA2AlphaInstructions.SA_INV_DST:
                    tmpMat["b_srcAlpha"] = 'INV_DST'
                elif instr & SA2AlphaInstructions.SA_DST == SA2AlphaInstructions.SA_DST:
                    tmpMat["b_srcAlpha"] = 'DST'
                elif instr & SA2AlphaInstructions.SA_INV_SRC == SA2AlphaInstructions.SA_INV_SRC:
                    tmpMat["b_srcAlpha"] = 'INV_SRC'
                elif instr & SA2AlphaInstructions.SA_INV_OTHER == SA2AlphaInstructions.SA_INV_OTHER:
                    tmpMat["b_srcAlpha"] = 'INV_OTHER'
                elif instr & SA2AlphaInstructions.SA_SRC:
                    tmpMat["b_srcAlpha"] = 'SRC'
                elif instr & SA2AlphaInstructions.SA_OTHER:
                    tmpMat["b_srcAlpha"] = 'OTHER'
                elif instr & SA2AlphaInstructions.SA_ONE:
                    tmpMat["b_srcAlpha"] = 'ONE'
                else:
                    tmpMat["b_srcAlpha"] = 'ZERO'

                if instr & SA2AlphaInstructions.DA_INV_DST == SA2AlphaInstructions.DA_INV_DST:
                    tmpMat["b_destAlpha"] = 'INV_DST'
                elif instr & SA2AlphaInstructions.DA_DST == SA2AlphaInstructions.DA_DST:
                    tmpMat["b_destAlpha"] = 'DST'
                elif instr & SA2AlphaInstructions.DA_INV_SRC == SA2AlphaInstructions.DA_INV_SRC:
                    tmpMat["b_destAlpha"] = 'INV_SRC'
                elif instr & SA2AlphaInstructions.DA_INV_OTHER == SA2AlphaInstructions.DA_INV_OTHER:
                    tmpMat["b_destAlpha"] = 'INV_OTHER'
                elif instr & SA2AlphaInstructions.DA_SRC:
                    tmpMat["b_destAlpha"] = 'SRC'
                elif instr & SA2AlphaInstructions.DA_OTHER:
                    tmpMat["b_destAlpha"] = 'OTHER'
                elif instr & SA2AlphaInstructions.DA_ONE:
                    tmpMat["b_destAlpha"] = 'ONE'
                else:
                    tmpMat["b_destAlpha"] = 'ZERO'

                if c.chunkType.value > 15 and c.chunkType.value < 32:
                    tmpMat["b_Diffuse"] = c.diffuse.toBlenderTuple()
                    tmpMat["b_Ambient"] = c.ambient.toBlenderTuple()
                    tmpMat["b_Specular"] = c.specular.toBlenderTuple()
                    tmpMat["b_Exponent"] = c.specularity / 255.0
            elif c.chunkType == enums.ChunkType.Tiny_TextureID:
                tmpMat["b_TextureID"] = c.texID
                tmpMat["b_use_Anisotropy"] = c.anisotropy

                if c.filtering == enums.TextureFiltering.Point:
                    tmpMat["b_texFilter"] = 'POINT'
                elif c.filtering == enums.TextureFiltering.Bilinear:
                    tmpMat["b_texFilter"] = 'BILINEAR'
                elif c.filtering == enums.TextureFiltering.Trilinear:
                    tmpMat["b_texFilter"] = 'TRILINEAR'
                elif c.filtering == enums.TextureFiltering.Blend:
                    tmpMat["b_texFilter"] = 'BLEND'

                tmpMat["b_d_025"] = (c.flags & enums.TextureIDFlags.D_025).value > 0
                tmpMat["b_d_050"] = (c.flags & enums.TextureIDFlags.D_050).value > 0
                tmpMat["b_d_100"] = (c.flags & enums.TextureIDFlags.D_100).value > 0
                tmpMat["b_d_200"] = (c.flags & enums.TextureIDFlags.D_200).value > 0
                tmpMat["b_clampU"] = (c.flags & enums.TextureIDFlags.CLAMP_U).value > 0
                tmpMat["b_clampV"] = (c.flags & enums.TextureIDFlags.CLAMP_V).value > 0
                tmpMat["b_mirrorU"] = (c.flags & enums.TextureIDFlags.FLIP_U).value > 0
                tmpMat["b_mirrorV"] = (c.flags & enums.TextureIDFlags.FLIP_V).value > 0
            elif c.chunkType == enums.ChunkType.Bits_SpecularExponent:
                tmpMat["b_Exponent"] = c.exponent
            elif c.chunkType == enums.ChunkType.Bits_MipmapDAdjust:
                tmpMat["b_d_025"] = (c.value & enums.MipMapDistanceAdjust.D_025).value > 0
                tmpMat["b_d_050"] = (c.value & enums.MipMapDistanceAdjust.D_050).value > 0
                tmpMat["b_d_100"] = (c.value & enums.MipMapDistanceAdjust.D_100).value > 0
                tmpMat["b_d_200"] = (c.value & enums.MipMapDistanceAdjust.D_200).value > 0

        # creating the mesh
        mesh = bpy.data.meshes.new(a.name(isArmature))

        # adding the materials
        for m in meshMaterials:
            mesh.materials.append(m)

        if not a.hasColor:
            mesh.saSettings.sa2ExportType = 'NRM'
        else:
            mesh.saSettings.sa2ExportType = 'VC'

        bm = bmesh.new()
        bm.from_mesh(mesh)

        # adding the vertices
        for v in vDistinct:
            bm.verts.new(v[0])

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # adding the polygons
        uvLayer = bm.loops.layers.uv.new("UV0")
        if a.hasColor:
            colorLayer = bm.loops.layers.color.new("COL0")

        # creating the polygons
        split_normals = list()
        doubleFaces = 0
        matIndex = 0
        for i, p in enumerate(polygons):
            verts = []
            for c in p:
                verts.append(bm.verts[vIDs[c.index]])
            try:
                face = bm.faces.new(verts)
            except Exception as e:
                doubleFaces += 1
                continue

            for li, c in enumerate(p):
                split_normals.append(normals[vIDs[c.index]])
                face.loops[li][uvLayer].uv = c.uv.getBlenderUV()
                if a.hasColor:
                    face.loops[li][colorLayer] = a.vertices[c.index].getColor()

            if i in matMarkers:
                matIndex = matMarkers[i]
            face.smooth = True
            face.material_index = matIndex

        bm.to_mesh(mesh)
        bm.clear()

        # setting normals
        mesh.create_normals_split()
        mesh.normals_split_custom_set(split_normals)
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 180

        if isArmature:
            meshOBJ = bpy.data.objects.new(mesh.name, mesh)

            #adding weights
            weightGroups: Dict[common.Model, bpy.types.VertexGroup] = dict()

            a.affectedBy.sort(key=lambda x: x.name)
            for o in a.affectedBy:
                weightGroups[o] = meshOBJ.vertex_groups.new(name=o.name)

            for i, v in enumerate(a.vertices.values()):
                for ov in v.vertices:
                    weightGroups[ov.model].add([mesh.vertices[i].index], ov.weight, 'REPLACE')

            armatureRoot.meshes.append(meshOBJ)
        else:
            o.meshes.append(mesh)
            meshes[o.meshPtr] = mesh
