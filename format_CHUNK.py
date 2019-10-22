import bpy
import mathutils

import array
import copy
import math
from typing import List, Dict

from . import enums, fileWriter, strippifier, common
from .common import Vector3, ColorARGB, UV, BoundingBox, BoneMesh
from .__init__ import SAMaterialSettings

DO = False

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

    def writeVC(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
        self.col.writeARGB(fileW)
        
    def writeNRM(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
        self.nrm.write(fileW)

    def writeNRMW(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
        self.nrm.write(fileW)
        fileW.wUInt(self.ninjaFlags)

class VertexChunk:
    """One vertex data set"""

    chunkType: enums.ChunkType
    weightType: enums.WeightStatus
    indexBufferOffset: int
    vertices: List[Vertex]

    def __init__(self,
                 chunkType: enums.ChunkType,
                 weightType: enums.WeightStatus,
                 indexBufferOffset: int,
                 vertices: List[Vertex]):
        self.chunkType = chunkType
        self.weightType = weightType
        self.indexBufferOffset = indexBufferOffset
        self.vertices = vertices

    def write(self, fileW: fileWriter.FileWriter):
        fileW.wByte(self.chunkType.value)
        fileW.wByte(self.weightType.value)
        
        if self.chunkType == enums.ChunkType.Vertex_VertexDiffuse8:
            vertexSize = 4
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormal:
            vertexSize = 6
        elif self.chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags:
            vertexSize = 7
        else:
            print("unsupported chunk format:", self.chunkType)

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

    vertex: Vertex
    uv: UV

    def __init__(self, 
                 vertex: Vertex, 
                 uv: UV):
        self.vertex = vertex
        self.uv = uv

    def __eq__(self, other):
        return self.vertex == other.vertex and self.uv == other.uv

    def vIndex(self):
        if isinstance(self.vertex, Vertex):
            return self.vertex.index
        else:
            return self.vertex

    def write(self, fileW):
        if isinstance(self.vertex, Vertex):
            fileW.wUShort(self.vertex.index)
        else:
            fileW.wUShort(self.vertex)

    def writeUV(self, fileW):
        if isinstance(self.vertex, Vertex):
            fileW.wUShort(self.vertex.index)
        else:
            fileW.wUShort(self.vertex)
        self.uv.write(fileW)

class PolyChunk:
    """Base polychunk"""

    chunkType: enums.ChunkType

    def __init__(self, chunkType: enums.ChunkType):
        self.chunkType = chunkType

    def write(self, fileW: fileWriter.FileWriter):
        fileW.wByte(self.chunkType.value)

class PolyChunk_Bit(PolyChunk):
    """Base class for one byte Poly chunks"""

    data: int

    def __init__(self, chunkType: enums.ChunkType):
        super(PolyChunk_Bit, self).__init__(chunkType)
        self.data = 0

    def write(self, fileW: fileWriter.FileWriter):
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
        self.data |= 0x10
        self.exponent = exponent

    @property
    def exponent(self) -> float:
        return (self.data & 0xF) / 15.0

    @exponent.setter
    def exponent(self, val: float):
        self.data &= ~0xF
        self.data |= min(0xF, round(val * 15))

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

    def read(fileR: fileWriter.FileReader, address: int):
        flags = enums.TextureIDFlags(fileR.rByte(address))
        header = fileR.rUShort(address + 1)
        texID = header & 0x1FFF
        aniso = (header & 0x2000) > 0
        filtering = enums.TextureFiltering( header >> 14 )
        return PolyChunk_Texture(texID, flags, aniso, filtering), address + 3
     
    def write(self, fileW: fileWriter.FileWriter):
        super(PolyChunk_Texture, self).write(fileW)
        fileW.wByte(self.flags.value)
        value = min(self.texID, 0x1FFF)
        if self.anisotropy:
            value |= 0x2000
        value |= (self.filtering.value << 14)
        fileW.wUShort(value)

class PolyChunk_Material(PolyChunk):
    """The material chunk with all 3 colors"""

    diffuse: ColorARGB
    ambient: ColorARGB
    specular: ColorARGB
    
    def __init__(self,
                 diffuse: ColorARGB,
                 ambient: ColorARGB,
                 specular: ColorARGB):
        super(PolyChunk_Material, self).__init__(enums.ChunkType.Material_DiffuseAmbientSpecular)
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular

    def read(fileR: fileWriter.FileReader, chunkType: enums.ChunkType, address: int):
        address += 3 # skipping gap and size

        diffuse = ColorARGB()
        if chunkType.value & 0x1: # diffuse
            diffuse = ColorARGB.fromARGB(fileR.rUInt(address))
            address += 4
            
        ambient = ColorARGB()
        if chunkType.value & 0x2: # ambient
            ambient = ColorARGB.fromARGB(fileR.rUInt(address))
            address += 4

        specular = ColorARGB()
        if chunkType.value & 0x4: # specular
            specular = ColorARGB.fromARGB(fileR.rUInt(address))
            address += 4
        
        return PolyChunk_Material(diffuse, ambient, specular), address


    def write(self, fileW: fileWriter.FileWriter):
        super(PolyChunk_Material, self).write(fileW)
        fileW.wByte(0) # gap, usually flags, but those are unused in sa2
        fileW.wUShort(6) # size (amount of 2 byte sets)
        self.diffuse.writeARGB(fileW)
        self.ambient.writeARGB(fileW)
        self.specular.writeARGB(fileW)
    
class PolyChunk_Strip(PolyChunk):

    flags: enums.StripFlags
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
    
    def read(fileR: fileWriter.FileReader, chunkType: enums.ChunkType, address: int):
        
        flags = enums.StripFlags(fileR.rByte(address))
        address += 1
        size = fileR.rUShort(address)
        address += 2
        header = fileR.rUShort(address)
        stripCount = header & 0x3FFF
        userFlagCount = header >> 14 
        if userFlagCount > 0:
            print("  Userflag count:", userFlagCount)
        address += 2

        polyVerts = list()
        reversedStrips = list()

        c = chunkType.value 
        hasUV = c == 65 or c == 66 or c == 68 or c == 69 or c == 71 or c == 72
        hasNRM = 1 if c >= 67 and c <= 69 else 0
        hasCOL = 1 if c >= 70 and c <= 72 else 0

        if DO:
            print("  UV:", hasUV, ", NRM:", hasNRM, " COL:", hasCOL)
            print("  flags:", flags)
            print("  size:", size)
            print("  stripCount:", stripCount)
            print("  userflags:", userFlagCount)

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
            
            reversedStrips.append(reverse)
            polyVerts.append(strip)


        return PolyChunk_Strip(hasUV, flags, polyVerts, reversedStrips), address

    def write(self, fileW: fileWriter.FileWriter):
        super(PolyChunk_Strip, self).write(fileW)
        fileW.wByte(self.flags.value)
        size = 1
        stripSize = 3 if self.chunkType == enums.ChunkType.Strip_StripUVN else 1
        for s in self.strips:
            size += (len(s) * stripSize) + 1
        fileW.wUShort(size)

        fileW.wUShort(min(0x3FFF, len(self.strips)))

        for s in self.strips:
            fileW.wUShort(min(0x7FFF, len(s)))
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
        self.vertexChunks = vertexChunks
        self.polyChunks = polyChunks
        self.bounds = bounds

    def getPolygons(mesh: bpy.types.Mesh,
                    writeUVs: bool,
                    polyVerts: List[PolyVert],
                    materials: List[bpy.types.Material]):

        # getting the distinct polygons
        distinctPolys = list()
        IDs = [0] * len(polyVerts)

        distinctPolys, IDs = common.getDistinctwID(polyVerts)
        
        polygons: List[List[PolyVert]] = [[] for m in mesh.materials]
        if len(polygons) == 0:
            polygons.append(list())

        # assembling the polygons
        for p in mesh.polygons:
            for l in p.loop_indices:
                polygons[p.material_index].append(IDs[l])

        # converting triangle lists to strips
        strips: List[List[PolyVert]] = list() # material specific -> strip -> polygon
        Stripf = strippifier.Strippifier()

        for l in polygons:
            if len(l) == 0:
                strips.append(None)
                continue
            stripIndices = Stripf.Strippify(l, doSwaps=False, concat=False)

            polyStrips = [None] * len(stripIndices)

            for i, strip in enumerate(stripIndices):
                tStrip = [0] * len(strip)
                for j, index in enumerate(strip):
                    tStrip[j] = distinctPolys[index]
                polyStrips[i] = tStrip
            
            strips.append(polyStrips)

        # generating polygon chunks
        polyChunks: List[PolyChunk] = list()

        for mID, l in enumerate(strips):
            if l is None:
                continue
            
            # getting material
            material = None
            if len(mesh.materials) > 0:
                for m in materials:
                    if m.name == mesh.materials[mID].name:
                        material = m
                        break
            else:
                print(" mesh contains no material")

            stripFlags = enums.StripFlags.null

            if material is None:
                polyChunks.append(PolyChunk_Texture(0, enums.TextureIDFlags.null, True, enums.TextureFiltering.Bilinear))
                polyChunks.append(PolyChunk_Material(ColorARGB(), ColorARGB(), ColorARGB()))
                polyChunks.append(PolyChunk_SpecularExponent(1))
                polyChunks.append(PolyChunk_BlendAlpha(enums.SA2AlphaInstructions.SA_SRC | enums.SA2AlphaInstructions.DA_INV_SRC))
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

                polyChunks.append(PolyChunk_Texture(matProps.b_TextureID, textureFlags, matProps.b_use_Anisotropy, filtering))
                polyChunks.append(PolyChunk_Material(ColorARGB(matProps.b_Diffuse), ColorARGB(matProps.b_Ambient), ColorARGB(matProps.b_Specular)))
                polyChunks.append(PolyChunk_SpecularExponent(matProps.b_Exponent))

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
                
                polyChunks.append(PolyChunk_BlendAlpha(alphaflags))

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
            
            polyChunks.append(PolyChunk_Strip(writeUVs, stripFlags, l))

        return polyChunks

    def fromMesh(mesh: bpy.types.Mesh, 
                 export_matrix: mathutils.Matrix, 
                 materials: List[bpy.types.Material]):
        
        vertexType = mesh.saSettings.sa2ExportType
        if vertexType == 'VC' and len(mesh.vertex_colors) == 0:
            vertexType = 'NRM'

        writeUVs = len(mesh.uv_layers) > 0
        
        vertices: List[Vertex] = list()
        polyVerts: List[PolyVert] = list()

        # getting normals
        normals = list()
        if mesh.use_auto_smooth:
            mesh.calc_normals_split()
            for v in mesh.vertices:
                normal = mathutils.Vector((0,0,0))
                normalCount = 0
                for l in mesh.loops:
                    if l.vertex_index == v.index:
                        normal += l.normal
                        normalCount += 1
                if normalCount == 0:
                    normals.append(v.normal)
                else:
                    normals.append(normal / normalCount)

            mesh.free_normals_split()
        else:
            for v in mesh.vertices:
                normals.append(v.normal)

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

        else: # normals are a lot simpler to generate (luckily)
            for v in mesh.vertices:
                vertices.append( Vertex(v.index, v.index, Vector3(export_matrix @ v.co), Vector3(export_matrix @ normals[v.index]), ColorARGB(), 0) )

            for l in mesh.loops:
                uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
                polyVert = PolyVert(vertices[l.vertex_index], uv)
                polyVerts.append(polyVert)

        # creating the vertex chunk
        chunkType = enums.ChunkType.Vertex_VertexDiffuse8 if vertexType == 'VC' else enums.ChunkType.Vertex_VertexNormal
        vertexChunks: List[VertexChunk] = [VertexChunk(chunkType, enums.WeightStatus.Start, 0, vertices)]

        polyChunks = Attach.getPolygons(mesh, writeUVs, polyVerts, materials)
                
        bounds = BoundingBox(mesh.vertices)
        bounds.adjust(export_matrix)

        return Attach(mesh.name, vertexChunks, polyChunks, bounds)

    def fromWeightData(boneName: str,
                       meshData: List[BoneMesh],
                       boneMatrix_world: mathutils.Matrix, 
                       export_matrix: mathutils.Matrix, 
                       materials: List[bpy.types.Material]):

        vertexChunks: List[VertexChunk] = list()
        polyChunks: List[PolyChunk] = list()

        allVertices = list()

        for m in meshData:
            matrix = export_matrix @ (boneMatrix_world.inverted() @ m.model.origObject.matrix_world)

            mesh = m.model.processedMesh
            
            # getting normals
            normals = list()
            if mesh.use_auto_smooth:
                mesh.calc_normals_split()
                for v in mesh.vertices:
                    normal = mathutils.Vector((0,0,0))
                    normalCount = 0
                    for l in mesh.loops:
                        if l.vertex_index == v.index:
                            normal += l.normal
                            normalCount += 1
                    if normalCount == 0:
                        normals.append(v.normal)
                    else:
                        normals.append(normal / normalCount)

                mesh.free_normals_split()
            else:
                for v in mesh.vertices:
                    normals.append(v.normal)

            vertices: List[Vertex] = list()
            vChunkType = enums.ChunkType.Vertex_VertexNormalNinjaFlags
            if m.weightIndex >= 0: # do weights
                if m.weightStatus == enums.WeightStatus.Start:
                    for v in mesh.vertices:
                        # normalizing weight at the same time
                        weightsAdded = 0
                        weight = 0
                        for g in v.groups:
                            weightsAdded += g.weight
                            if g.group == m.weightIndex:
                                weight = g.weight
                        if weightsAdded > 0:
                                weight = weight / weightsAdded
                        vertices.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), ColorARGB(), weight) )

                        vert = Container()
                        vert.co = Vector3(matrix @ v.co)
                        allVertices.append(vert)
                else:
                    for v in mesh.vertices:
                        weightsAdded = 0
                        weight = None
                        for g in v.groups:
                            weightsAdded += g.weight
                            if g.group == m.weightIndex:
                                weight = g.weight
                        if weight is not None:
                            if weightsAdded > 0:
                                weight = weight / weightsAdded
                            vertices.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), ColorARGB(), weight) )

                            vert = Container()
                            vert.co = Vector3(matrix @ v.co)
                            allVertices.append(vert)
            elif m.weightIndex == -1: # do all
                for v in mesh.vertices:
                    vertices.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), ColorARGB(), 0) )

                    vert = Container()
                    vert.co = Vector3(matrix @ v.co)
                    allVertices.append(vert)
                vChunkType = enums.ChunkType.Vertex_VertexNormal
            elif m.weightIndex == -2: # do those with no weights
                for v in mesh.vertices:
                    if len(v.groups) == 0:
                        vertices.append( Vertex(v.index, v.index, Vector3(matrix @ v.co), Vector3((matrix.to_3x3() @ normals[v.index]).normalized()), ColorARGB(), 1) )

                        vert = Container()
                        vert.co = Vector3(matrix @ v.co)
                        allVertices.append(vert)
            
            vertexChunks.append(VertexChunk(vChunkType, m.weightStatus, m.indexBufferOffset, vertices))

            if m.weightIndex == -1 or m.weightStatus == enums.WeightStatus.End: # write polygons
                writeUVs = len(mesh.uv_layers) > 0
                polyVerts: List[PolyVert] = list()
                for l in mesh.loops:
                    uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
                    polyVert = PolyVert(l.vertex_index + m.indexBufferOffset, uv)
                    polyVerts.append(polyVert)
                
                polyChunks.extend(Attach.getPolygons(mesh, writeUVs, polyVerts, materials))

        bounds = BoundingBox(allVertices)
                
        return Attach(boneName, vertexChunks, polyChunks, bounds)

    def write(self, 
              fileW: fileWriter.FileWriter,
              labels: dict,
              meshDict: dict = None):
        global DO
        
        # writing vertex chunks
        vertexChunkPtr = fileW.tell()
        for v in self.vertexChunks:
            v.write(fileW)
        # writing vertex chunk terminator
        fileW.wULong(enums.ChunkType.End.value)

        # writing polygon chunks
        polyChunkPtr = fileW.tell()
        for p in self.polyChunks:
            p.write(fileW)
                
        # writing poly chunk terminator
        fileW.wUShort(enums.ChunkType.End.value)

        attachPtr = fileW.tell()
        if meshDict is not None:
            meshDict[self.name] = attachPtr
        labels[attachPtr] = "cnk_" + self.name
        labels[vertexChunkPtr] = "cnk_" + self.name + "_vtx"
        labels[polyChunkPtr] = "cnk_" + self.name + "_poly"

        fileW.wUInt(vertexChunkPtr)
        fileW.wUInt(polyChunkPtr)
        self.bounds.write(fileW)

        if DO:
            print("  Chunk mesh:", self.name)
            print("    Vertex chunks:", len(self.vertexChunks))
            print("    Vertex chunk ptr:", vertexChunkPtr)
            print("    Poly chunks:", len(self.polyChunks))
            print("    Poly chunk ptr:", polyChunkPtr, "\n")

        return attachPtr

    def read(fileR: fileWriter.FileReader, address: int, meshID: int, labels: dict):

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
                if DO:
                    print("ChunkType:", chunkType)
                    print("  weightstatus:", weightStatus)
                    print("  otherFlags:", '{:02x}'.format(otherFlags))
                    print("  size:", size)
                    print("  index buffer offset:", indexBufferOffset)
                    print("  vCount:", vertexCount)

                    
                tmpAddr += 8

                for i in range(vertexCount):
                    # getting the position (part of every vertex)
                    posX = fileR.rFloat(tmpAddr)
                    posY = fileR.rFloat(tmpAddr + 4)
                    posZ = fileR.rFloat(tmpAddr + 8)
                    pos = Vector3((posX, -posZ, posY))
                    tmpAddr += 12

                    col = ColorARGB()

                    # getting color
                    if chunkType == enums.ChunkType.Vertex_VertexDiffuse8:
                        col = ColorARGB.fromARGB(fileR.rUInt(tmpAddr))
                        tmpAddr += 4
                        
                    weight = 0
                    index = i
                    nrm = None

                    if chunkType == enums.ChunkType.Vertex_VertexNormal or chunkType == enums.ChunkType.Vertex_VertexNormalNinjaFlags:
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

                vertexChunks.append( VertexChunk(chunkType, weightStatus, indexBufferOffset, vertices))

                chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
        else:
            if DO:
                print("Attach has no Vertex chunk")
        # reading polygons chunks

        polygonChunks = list()
        tmpAddr = fileR.rUInt(address + 4)
        if tmpAddr > 0: 
            chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
            while chunkType != enums.ChunkType.End:
                chunk = PolyChunk(chunkType)
                if DO:
                    print("Chunktype:", chunkType)

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

                    if (chunkType == enums.ChunkType.Bits_CachePolygonList or chunkType == enums.ChunkType.Bits_DrawPolygonList) and DO:
                        print(chunk.data)

                
                polygonChunks.append(chunk)
                chunkType = enums.ChunkType(fileR.rByte(tmpAddr))
        else:
            if DO:
                print("Attach has no poly chunk")

        return Attach(name, vertexChunks, polygonChunks, None)

    def debug(self):
        print("  Chunk mesh:", self.name)
        print("    Vertex chunks:", len(self.vertexChunks))
        print("    Poly chunks:", len(self.polyChunks))


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

    def __init__(self):
        self.vertices = list()

    def reset(self, newVert: ProcessedVert):
        self.vertices = [newVert]
    
    def add(self, vert: ProcessedVert):
        self.vertices.append(vert)

    def getWorldPos(self):
        pos = Vector3((0,0,0))
        for v in self.vertices:
            pos += v.model.matrix_world @ v.position
        pos = pos / len(self.vertices)
        return (pos.x, pos.y, pos.z)

    def getWorldNormals(self):
        nrm = Vector3((0,0,0))
        nrmCount = 0
        for v in self.vertices:
            if v.normal is not None:
                nrm += v.model.matrix_world.to_3x3() @ v.normal
                nrmCount += 1
        
        if nrmCount == 0:
            return (0,0,0)
        else:
            nrm /= nrmCount
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

def ProcessChunkData(models: List[common.Model], attaches: Dict[int, Attach], isArmature: bool):
    
    vertexBuffer: List[BufferedVertex] = [BufferedVertex() for v in range(0x7FFF)]
    polyCaches: List[List[PolyChunk]] = [[] for i in range(16)] # lets hope nothing uses 17 caches
    import bmesh

    tmpMat = common.getDefaultMatDict()

    materials: List[bpy.types.Material] = list()
    matDicts: List[dict] = list()


    for o in models:
        if o.meshPtr == 0:
            continue
        attach = attaches[o.meshPtr]

        for vtxCnk in attach.vertexChunks:
            if vtxCnk.weightType == enums.WeightStatus.Start:
                for v in vtxCnk.vertices:
                    vertexBuffer[vtxCnk.indexBufferOffset + v.index].reset(ProcessedVert(o, v))
            else:
                for v in vtxCnk.vertices:
                    vertexBuffer[vtxCnk.indexBufferOffset + v.index].add(ProcessedVert(o, v))

        polyChunks = list() # the chunks that we are about to process

        cacheIndex = -1
        for polyCnk in attach.polyChunks:
            if cacheIndex > -1:
                polyCaches[cacheIndex].append(polyCnk)
            else:
                if polyCnk.chunkType == enums.ChunkType.Bits_CachePolygonList:
                    cacheIndex = polyCnk.data
                    polyCaches[cacheIndex] = list()
                elif polyCnk.chunkType == enums.ChunkType.Bits_DrawPolygonList:
                    polyChunks.extend(polyCaches[polyCnk.data])
                else:
                    polyChunks.append(polyCnk)
            
        if len(polyChunks) > 0:
            # getting the vertice that the polygons require
            vertices: List[BufferedVertex] = list()
            vertexIndices = [0] * 0x7FFF

            for c in polyChunks:
                if c.chunkType.value > 63 and c.chunkType.value < 76: # its a strip
                    for s in c.strips:
                        for p in s:
                            vert = vertexBuffer[p.vIndex()]
                            if vert not in vertices:
                                vertices.append(vert)
                                vertexIndices[p.vIndex()] = len(vertices) - 1

            affectedBy: List[model] = list()

            for v in vertices:
                if len(v.vertices) == 1:
                    v.vertices[0].weight = 1
                for vtx in v.vertices:
                    if vtx.model not in affectedBy:
                        affectedBy.append(vtx.model)

            #weighted = len(affectedBy) > 1
            
            # getting distinct vertices, so that we can weld them and prevent doubles
            vertexSets = list()
            if isArmature:
                for v in vertices:
                    vertexSets.append((v.getWorldPos(), v.getWorldNormals()))
            else:
                for v in vertices:
                    vertexSets.append((v.getLocalPos(), v.getLocalNrm()))

            # getting the distinct positions and adding them to the py data:

            vDistinct, vIDs = common.getDistinctwID(vertexSets)

            for i in range(len(vertexIndices)):
                vertexIndices[i] = vIDs[vertexIndices[i]]

            # getting the polygon data

            polygons: List[List[PolyVert]] = list()
            matMarkers = dict()
            meshMaterials = list()
            for c in polyChunks:
                if c.chunkType.value > 63 and c.chunkType.value < 76: # its a strip
                    tmpMat["b_ignoreLighting"] = (c.flags & enums.StripFlags.IGNORE_LIGHT).value > 0
                    tmpMat["b_ignoreSpecular"] = (c.flags & enums.StripFlags.INGORE_SPECULAR).value > 0
                    tmpMat["b_ignoreAmbient"] = (c.flags & enums.StripFlags.IGNORE_AMBIENT).value > 0
                    tmpMat["b_useAlpha"] = (c.flags & enums.StripFlags.USE_ALPHA).value > 0
                    tmpMat["b_doubleSided"] = (c.flags & enums.StripFlags.DOUBLE_SIDE).value > 0
                    tmpMat["b_flatShading"] = (c.flags & enums.StripFlags.FLAT_SHADING).value > 0
                    tmpMat["b_useEnv"] = (c.flags & enums.StripFlags.ENV_MAPPING).value > 0

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
                    matMarkers[len(polygons)] = matIndex

                    for si, s in enumerate(c.strips):
                        rev = c.reversedStrips[si]
                        if rev:
                            for p in range(len(s) - 2):
                                polygons.append((s[p+1], s[p], s[p+2]))
                        else:
                            for p in range(len(s) - 2):
                                polygons.append((s[p], s[p+1], s[p+2])) 

                    
                elif c.chunkType == enums.ChunkType.Material_DiffuseAmbientSpecular:
                    tmpMat["b_Diffuse"] = c.diffuse.toBlenderTuple()
                    tmpMat["b_Ambient"] = c.ambient.toBlenderTuple()
                    tmpMat["b_Specular"] = c.specular.toBlenderTuple()
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
                elif c.chunkType == enums.ChunkType.Bits_BlendAlpha:
                    instr = c.alphaInstruction
                    from .enums import SA2AlphaInstructions
                    
                    if instr & SA2AlphaInstructions.SA_ONE:
                        tmpMat["b_srcAlpha"] = 'ONE'
                    elif instr & SA2AlphaInstructions.SA_OTHER:
                        tmpMat["b_srcAlpha"] = 'OTHER'
                    elif instr & SA2AlphaInstructions.SA_INV_OTHER:
                        tmpMat["b_srcAlpha"] = 'INV_OTHER'
                    elif instr & SA2AlphaInstructions.SA_SRC:
                        tmpMat["b_srcAlpha"] = 'SRC'
                    elif instr & SA2AlphaInstructions.SA_INV_SRC:
                        tmpMat["b_srcAlpha"] = 'INV_SRC'
                    elif instr & SA2AlphaInstructions.SA_DST:
                        tmpMat["b_srcAlpha"] = 'DST'
                    elif instr & SA2AlphaInstructions.SA_INV_DST:
                        tmpMat["b_srcAlpha"] = 'INV_DST'
                    else:
                        tmpMat["b_srcAlpha"] = 'ZERO'

                    if instr & SA2AlphaInstructions.DA_ONE:
                        tmpMat["b_destAlpha"] = 'ONE'
                    elif instr & SA2AlphaInstructions.DA_OTHER:
                        tmpMat["b_destAlpha"] = 'OTHER'
                    elif instr & SA2AlphaInstructions.DA_INV_OTHER:
                        tmpMat["b_destAlpha"] = 'INV_OTHER'
                    elif instr & SA2AlphaInstructions.DA_SRC:
                        tmpMat["b_destAlpha"] = 'SRC'
                    elif instr & SA2AlphaInstructions.DA_INV_SRC:
                        tmpMat["b_destAlpha"] = 'INV_SRC'
                    elif instr & SA2AlphaInstructions.DA_DST:
                        tmpMat["b_destAlpha"] = 'DST'
                    elif instr & SA2AlphaInstructions.DA_INV_DST:
                        tmpMat["b_destAlpha"] = 'INV_DST'
                    else:
                        tmpMat["b_destAlpha"] = 'ZERO'

                            
            # creating the mesh

            mesh = bpy.data.meshes.new(attach.name)
            for m in meshMaterials:
                mesh.materials.append(m)

            bm = bmesh.new()
            bm.from_mesh(mesh)

            for v in vDistinct:
                vert = bm.verts.new(v[0])
            bm.verts.ensure_lookup_table()
            bm.verts.index_update()

            matIndex = 0
            uvLayer = bm.loops.layers.uv.new("UV0")
            for i, p in enumerate(polygons):
                verts = []
                indices = []
                for l in p:
                    vID = vertexIndices[ l.vIndex() ]
                    verts.append(bm.verts[vID])
                    indices.append(vID)
                try:
                    face = bm.faces.new(verts)
                except ValueError as err:
                    if DO:
                        print("concat?", indices)
                    continue

                for l, pc in zip(face.loops, p):
                    l[uvLayer].uv = pc.uv.getBlenderUV()

                if i in matMarkers:
                    matIndex = matMarkers[i]
                face.smooth = True
                face.material_index = matIndex

            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            bm.to_mesh(mesh)
            bm.free()

            mesh.create_normals_split()
            
            mesh.validate(clean_customdata=False)  # *Very* important to not remove lnors here!
            mesh.update()

            split_normal = [vDistinct[l.vertex_index][1] for l in mesh.loops]
            mesh.normals_split_custom_set(split_normal)
            mesh.use_auto_smooth = True

            # dont ask me why, but blender likes to add sharp edges- we dont need those at all in this case
            for e in mesh.edges:
                e.use_edge_sharp = False

            if isArmature:
                meshOBJ = bpy.data.objects.new(mesh.name, mesh)

                #adding weights
                weightGroups: Dict[common.Model, bpy.types.VertexGroup] = dict()
                for o in affectedBy:
                    weightGroups[o] = meshOBJ.vertex_groups.new(name=o.name)

                for v, bV in zip(vertices, mesh.vertices):
                    for ov in v.vertices:
                        weightGroups[ov.model].add([bV.index], ov.weight, 'REPLACE') 

                models[0].meshes.append(meshOBJ)
            else:
                o.meshes.append(mesh)

