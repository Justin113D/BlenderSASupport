import bpy
import mathutils

import math
from typing import List

from . import enums, fileWriter, strippifier, common
from .common import Vector3, ColorARGB, UV, BoundingBox
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
        self.weight = weight
        
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
        self.ninjaFlags |= min(1, max(0, round(255 * val))) << 16

    def writeVC(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
        self.col.writeARGB(fileW)
        
    def writeNRM(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
        self.nrm.write(fileW)

    def writeNRMW(self, fileW: fileWriter.FileWriter):
        self.pos.write(fileW)
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

    def write(self, fileW):
        fileW.wUShort(self.vertex.index)

    def writeUV(self, fileW):
        fileW.wUShort(self.vertex.index)
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

    def __init__(self,
                 hasUV: bool,
                 flags: enums.StripFlags,
                 strips: List[List[PolyVert]]):
        if hasUV:
            super(PolyChunk_Strip, self).__init__(enums.ChunkType.Strip_StripUVN)
        else:
            super(PolyChunk_Strip, self).__init__(enums.ChunkType.Strip_Strip)
        self.flags = flags
        self.strips = strips
    
    def write(self, fileW: fileWriter.FileWriter):
        super(PolyChunk_Strip, self).write(fileW)
        fileW.wByte(self.flags.value)
        size = 1
        for s in self.strips:
            size += len(s) * (3 if self.chunkType == enums.ChunkType.Strip_StripUVN else 1) + 1
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

    def fromMesh(mesh: bpy.types.Mesh, 
                 export_matrix: mathutils.Matrix, 
                 materials: List[bpy.types.Material]):
        
        vertexType = mesh.saSettings.sa2ExportType
        if vertexType == 'VC' and len(mesh.vertex_colors) == 0:
            vertexType = 'NRM'

        writeUVs = len(mesh.uv_layers) > 0
        
        vertices: List[Vertex] = list()
        polyVerts: List[PolyVert] = list()

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
                vertices.append( Vertex(v.index, v.index, Vector3(export_matrix @ v.co), Vector3(export_matrix @ v.normal), ColorARGB(), 0) )

            for l in mesh.loops:
                uv = UV(mesh.uv_layers[0].data[l.index].uv) if writeUVs else UV()
                polyVert = PolyVert(vertices[l.vertex_index], uv)
                polyVerts.append(polyVert)

        # creating the vertex chunk
        chunkType = enums.ChunkType.Vertex_VertexDiffuse8 if vertexType == 'VC' else enums.ChunkType.Vertex_VertexNormal
        vertexChunks: List[VertexChunk] = [VertexChunk(chunkType, enums.WeightStatus.Start, 0, vertices)]

        # getting the distinct polygons
        distinctPolys = list()
        IDs = [0] * len(polyVerts)
        
        for i, o in enumerate(polyVerts):
            found = None
            for j, d in enumerate(distinctPolys):
                if o == d:
                    found = j
                    break
            if found is None:
                distinctPolys.append(o)
                IDs[i] = len(distinctPolys) - 1
            else:
                IDs[i] = found
        
        
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
                
        bounds = BoundingBox(mesh.vertices)
        bounds.adjust(export_matrix)

        return Attach(mesh.name, vertexChunks, polyChunks, bounds)

    def write(self, 
              fileW: fileWriter.FileWriter,
              labels: dict):
        
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

        labels["cnk_" + self.name] = fileW.tell()
        labels["cnk_" + self.name + "_vtx"] = vertexChunkPtr
        labels["cnk_" + self.name + "_poly"] = polyChunkPtr

        fileW.wUInt(vertexChunkPtr)
        fileW.wUInt(polyChunkPtr)
        self.bounds.write(fileW)
