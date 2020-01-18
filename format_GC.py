import bpy
import math
import mathutils
from typing import List, Dict, Tuple
import copy

from . import fileHelper, enums, strippifier, common
from .common import Vector3, ColorARGB, UV, BoundingBox
from .__init__ import SAMaterialSettings

DO = False

def debug(*string):
    global DO
    if DO:
        print(*string)

# == Geometry parameters ==

class Parameter:

    pType: enums.ParameterType
    data: int

    def __init__(self, pType: enums.ParameterType):
        self.pType = pType
        self.data = 0

    def write(self, fileW: fileHelper.FileWriter):
        fileW.wUInt(self.pType.value)
        fileW.wUInt(self.data)

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int):
        pType = enums.ParameterType(fileR.rUInt(address))
        data = fileR.rUInt(address+4)

        if pType == enums.ParameterType.VtxAttrFmt:
            param = VtxAttrFmt(enums.VertexAttribute.Null)
        elif pType == enums.ParameterType.IndexAttributeFlags:
            param = IndexAttributes(enums.IndexAttributeFlags.HasPosition)
        elif pType == enums.ParameterType.Lighting:
            param = Lighting(1)
        elif pType == enums.ParameterType.BlendAlpha:
            param = AlphaBlend(enums.AlphaInstruction.SrcAlpha, enums.AlphaInstruction.InverseSrcAlpha, False)
        elif pType == enums.ParameterType.AmbientColor:
            param = AmbientColor(ColorARGB())
        elif pType == enums.ParameterType.Texture:
            param = Texture(0, enums.TileMode.null)
        elif pType == enums.ParameterType.Unknown_9:
            param = unknown_9()
        elif pType == enums.ParameterType.TexCoordGen:
            param = TexCoordGen(enums.TexGenMtx.Identity, enums.TexGenSrc.TexCoord0, enums.TexGenType.Matrix2x4, enums.TexCoordID.TexCoord0)
        else:
            print("type not found?")

        param.data = data

        return param

class VtxAttrFmt(Parameter):
    """We dont know what this does but we know that we
    need one for each vertex data set"""

    def __init__(self,
                 vtxType: enums.VertexAttribute):
        super(VtxAttrFmt, self).__init__(enums.ParameterType.VtxAttrFmt)
        self.vtxType = vtxType
        if vtxType == enums.VertexAttribute.Position:
            self.unknown = 5120
        elif vtxType == enums.VertexAttribute.Normal:
            self.unknown = 9216
        elif vtxType == enums.VertexAttribute.Color0:
            self.unknown = 27136
        elif vtxType == enums.VertexAttribute.Tex0:
            self.unknown = 33544


    @property
    def unknown(self) -> int:
        return self.data & 0xFFFF

    @unknown.setter
    def unknown(self, val: int):
        self.data &= ~0xFFFF
        self.data |= min(0xFFFF, val)

    @property
    def vtxType(self) -> enums.VertexAttribute:
        return enums.VertexAttribute((self.data >> 16) & 0xFFFF)

    @vtxType.setter
    def vtxType(self, val: enums.VertexAttribute):
        self.data &= ~0xFFFF0000
        self.data |= val.value << 16

class IndexAttributes(Parameter):
    """Which data the polygon corners hold"""

    def __init__(self,
                 idAttr: enums.IndexAttributeFlags):
        super(IndexAttributes, self).__init__(enums.ParameterType.IndexAttributeFlags)
        self.indexAttributes = idAttr

    @property
    def indexAttributes(self) -> enums.IndexAttributeFlags:
        return enums.IndexAttributeFlags(self.data)

    @indexAttributes.setter
    def indexAttributes(self, val: enums.IndexAttributeFlags):
        self.data = val.value

class Lighting(Parameter):
    """Holds lighting data for the mesh"""

    def __init__(self,
                 shadowStencil: int):
        super(Lighting, self).__init__(enums.ParameterType.Lighting)
        # everything except shadow stencil are default values
        self.lightingFlags = 0x0B11
        self.shadowStencil = shadowStencil
        self.unknown1 = 0
        self.unknown2 = 0

    @property
    def lightingFlags(self) -> int:
        return self.data & 0xFFFF

    @lightingFlags.setter
    def lightingFlags(self, val: int):
        self.data &= (~0xFFFF)
        self.data |= min(0xFFFF, val)

    @property
    def shadowStencil(self) -> int:
        return (self.data >> 16) & 0xF

    @shadowStencil.setter
    def shadowStencil(self, val: int):
        self.data &= (~0xF0000)
        self.data |= min(0xF, val) << 16

    @property
    def unknown1(self) -> int:
        return (self.data >> 20) & 0xF

    @unknown1.setter
    def unknown1(self, val: int):
        self.data &= (~0xF00000)
        self.data |= min(0xF, val) << 20

    @property
    def unknown2(self) -> int:
        return (self.data >> 24) & 0xFF

    @unknown2.setter
    def unknown2(self, val: int):
        self.data &= (~0xFF000000)
        self.data |= min(0xFF, val) << 24

class AlphaBlend(Parameter):
    """How the alpha is rendered on top of the opaque geometry"""

    def __init__(self,
                 src: enums.AlphaInstruction,
                 dst: enums.AlphaInstruction,
                 active: bool):
        super(AlphaBlend, self).__init__(enums.ParameterType.BlendAlpha)
        self.src = src
        self.dst = dst
        self.active = active

    @property
    def dst(self) -> enums.AlphaInstruction:
        return enums.AlphaInstruction((self.data >> 8) & 0x7)

    @dst.setter
    def dst(self, val: enums.AlphaInstruction):
        self.data &= ~0x700
        self.data |= val.value << 8

    @property
    def src(self) -> enums.AlphaInstruction:
        return enums.AlphaInstruction((self.data >> 11) & 0x7)

    @src.setter
    def src(self, val: enums.AlphaInstruction):
        self.data &= ~0x3800
        self.data |= val.value << 11

    @property
    def active(self) -> bool:
        return (self.data & 0x4000) > 1

    @active.setter
    def active(self, val: bool):
        if val:
            self.data |= 0x4000
        else:
            self.data &= ~0x4000

class AmbientColor(Parameter):
    """Ambient color of the mesh"""

    def __init__(self, color: ColorARGB):
        super(AmbientColor, self).__init__(enums.ParameterType.AmbientColor)
        self.color = color

    @property
    def color(self) -> ColorARGB:
        a = self.data & 0xFF
        r = (self.data >> 8) & 0xFF
        g = (self.data >> 16) & 0xFF
        b = (self.data >> 24) & 0xFF
        return ColorARGB((a,r,g,b))

    @color.setter
    def color(self, val: ColorARGB):
        self.data = min(val.a, 0xFF) | min(val.b, 0xFF) << 8 | min(val.g, 0xFF) << 16 | min(val.r, 0xFF) << 24

class Texture(Parameter):
    """Holds texture info"""

    def __init__(self, texID: int, tilemode: enums.TileMode):
        super(Texture, self).__init__(enums.ParameterType.Texture)
        self.texID = texID
        self.tilemode = tilemode

    @property
    def texID(self) -> int:
        return self.data & 0xFFFF

    @texID.setter
    def texID(self, val: int):
        self.data &= ~0xFFFF
        self.data |= min(0xFFFF, val)

    @property
    def tilemode(self) -> enums.TileMode:
        return enums.TileMode((self.data >> 16) & 0xFFFF)

    @tilemode.setter
    def tilemode(self, val: enums.TileMode):
        self.data &= ~0xFFFF0000
        self.data |= val.value << 16

class unknown_9(Parameter):
    """We have absolutely no clue what this is for, but we need it"""

    def __init__(self):
        super(unknown_9, self).__init__(enums.ParameterType.Unknown_9)
        self.unknown1 = 4
        self.unknown2 = 0

    @property
    def unknown1(self) -> int:
        return self.data & 0xFFFF

    @unknown1.setter
    def unknown1(self, val: int):
        self.data &= ~0xFFFF
        self.data |= min(0xFFFF, val)

    @property
    def unknown2(self) -> int:
        return (self.data >> 16) & 0xFFFF

    @unknown2.setter
    def unknown2(self, val: int):
        self.data &= ~0xFFFF0000
        self.data |= min(0xFFFF, val) << 16

class TexCoordGen(Parameter):
    """Determines how the uv data should be used"""

    def __init__(self,
                 mtx: enums.TexGenMtx,
                 src: enums.TexGenSrc,
                 typ: enums.TexGenType,
                 texID: enums.TexCoordID):
        super(TexCoordGen, self).__init__(enums.ParameterType.TexCoordGen)
        self.mtx = mtx
        self.src = src
        self.typ = typ
        self.texID = texID

    @property
    def mtx(self) -> enums.TexGenMtx:
        return enums.TexGenMtx(self.data & 0xF)

    @mtx.setter
    def mtx(self, val: enums.TexGenMtx):
        self.data &= ~0xF
        self.data |= val.value

    @property
    def src(self) -> enums.TexGenSrc:
        return enums.TexGenSrc((self.data >> 4) & 0xFF)

    @src.setter
    def src(self, val: enums.TexGenSrc):
        self.data &= ~0xFF0
        self.data |= val.value << 4

    @property
    def typ(self) -> enums.TexGenType:
        return enums.TexGenType((self.data >> 12) & 0xF)

    @typ.setter
    def typ(self, val: enums.TexGenType):
        self.data &= ~0xF000
        self.data |= val.value << 12

    @property
    def texID(self) -> enums.TexCoordID:
        return enums.TexCoordID((self.data >> 16) & 0xFF)

    @texID.setter
    def texID(self, val: enums.TexCoordID):
        self.data &= ~0xFF0000
        self.data |= val.value << 16


class PolyVert:
    """Indices of a single polygon corner"""

    posID = 0
    nrmID = 0
    vcID = 0
    uvID = 0

    def __init__(self, posID, nrmID, vcID, uvID):
        self.posID = posID
        self.nrmID = nrmID
        self.vcID = vcID
        self.uvID = uvID

    def __eq__(self, other):
        return self.posID == other.posID and self.nrmID == other.nrmID and self.vcID == other.vcID and self.uvID == other.uvID

    def __str__(self):
        return "(" + str(self.posID).zfill(3) + ", " + str(self.nrmID).zfill(3) + ", " + str(self.vcID).zfill(3) + ", " + str(self.uvID).zfill(3) + ")"

class Geometry:
    """Holds a single polygon data set"""

    params: List[Parameter]
    paramPtr: int
    polygons: List[List[PolyVert]] # each list in the list is a polygon. lists with 3 items are triangles, more items and its a strip
    polygonPtr: int
    polygonSize: int
    indexAttributes: enums.IndexAttributeFlags
    transparent: bool

    def __init__(self,
                 params: List[Parameter],
                 polygons: List[List[PolyVert]]):
        self.params = params
        self.polygons = polygons

        self.indexAttributes = None
        self.transparent = False
        for p in params:
            if isinstance(p, IndexAttributes):
                self.indexAttributes = p.indexAttributes
            if isinstance(p, AlphaBlend):
                self.transparent = p.active

        if self.indexAttributes is None:
            print("Index attributes not found")

    def writeParams(self, fileW: fileHelper.FileWriter):
        """Writes the parameters of the geometry"""
        self.paramPtr = fileW.tell()
        for p in self.params:
            p.write(fileW)

    def writePolygons(self, fileW: fileHelper.FileWriter):
        """Writes the polygon data of the geometry"""
        self.polygonPtr = fileW.tell()
        fileW.setBigEndian(True)

        toWrite = list()
        triangleList = list()

        for l in self.polygons:
            if len(l) == 3:
                triangleList.extend(l)
            else:
                toWrite.append(l)

        if len(triangleList) > 0:
            toWrite.append(triangleList)

        for l in toWrite:
            if l is triangleList:
                fileW.wByte(enums.PrimitiveType.Triangles.value)
            else:
                fileW.wByte(enums.PrimitiveType.TriangleStrip.value)
            fileW.wUShort(len(l))

            for p in l:
                if self.indexAttributes & enums.IndexAttributeFlags.Position16BitIndex:
                    fileW.wUShort(p.posID)
                else:
                    fileW.wByte(p.posID)

                if self.indexAttributes & enums.IndexAttributeFlags.HasNormal:
                    if self.indexAttributes & enums.IndexAttributeFlags.Normal16BitIndex:
                        fileW.wUShort(p.nrmID)
                    else:
                        fileW.wByte(p.nrmID)

                if self.indexAttributes & enums.IndexAttributeFlags.HasColor:
                    if self.indexAttributes & enums.IndexAttributeFlags.Color16BitIndex:
                        fileW.wUShort(p.vcID)
                    else:
                        fileW.wByte(p.vcID)

                if self.indexAttributes & enums.IndexAttributeFlags.HasUV:
                    if self.indexAttributes & enums.IndexAttributeFlags.UV16BitIndex:
                        fileW.wUShort(p.uvID)
                    else:
                        fileW.wByte(p.uvID)

        fileW.setBigEndian(False)

        self.polygonSize = fileW.tell() - self.polygonPtr

    def writeGeom(self, fileW: fileHelper.FileWriter):
        """Writes geometry data (requires params and polygons to be written)"""
        fileW.wUInt(self.paramPtr)
        fileW.wUInt(len(self.params))
        fileW.wUInt(self.polygonPtr)
        fileW.wUInt(self.polygonSize)

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int, paramDict: dict):

        paramPtr = fileR.rUInt(address)
        paramCount = fileR.rUInt(address + 4)
        polyPtr = fileR.rUInt(address + 8)
        polySize = fileR.rUInt(address + 12)

        if DO:
            print("   Param Count:", paramCount)
            print("   Poly Size:", polySize, "\n")

        for i in range(paramCount):
            param = Parameter.read(fileR, paramPtr)
            if param.pType == enums.ParameterType.VtxAttrFmt:
                paramDict[param.vtxType] = param
            else:
                paramDict[param.pType] = param
            paramPtr += 8

        idAttr = enums.IndexAttributeFlags.null

        params = list()

        for p in paramDict.values():
            params.append(copy.deepcopy(p))

        if enums.ParameterType.IndexAttributeFlags in paramDict:
            idAttr = paramDict[enums.ParameterType.IndexAttributeFlags].indexAttributes
        else:
            print("no index attributes found")

        #reading polygons
        tmpAddr = polyPtr
        polygons: List[List[PolyVert]] = list()
        fileR.setBigEndian(True)
        while tmpAddr - polyPtr < polySize:
            polyType = fileR.rByte(tmpAddr)
            tmpAddr += 1
            if polyType == 0:
                break
            polyType = enums.PrimitiveType(polyType)
            vCount = fileR.rUShort(tmpAddr)
            tmpAddr += 2
            polys = list()
            if vCount == 0:
                break
            for i in range(vCount):
                if idAttr & enums.IndexAttributeFlags.Position16BitIndex:
                    pos = fileR.rUShort(tmpAddr)
                    tmpAddr += 2
                else:
                    pos = fileR.rByte(tmpAddr)
                    tmpAddr += 1

                nrm = 0
                if idAttr & enums.IndexAttributeFlags.HasNormal:
                    if idAttr & enums.IndexAttributeFlags.Normal16BitIndex:
                        nrm = fileR.rUShort(tmpAddr)
                        tmpAddr += 2
                    else:
                        nrm = fileR.rByte(tmpAddr)
                        tmpAddr += 1

                col = 0
                if idAttr & enums.IndexAttributeFlags.HasColor:
                    if idAttr & enums.IndexAttributeFlags.Color16BitIndex:
                        col = fileR.rUShort(tmpAddr)
                        tmpAddr += 2
                    else:
                        col = fileR.rByte(tmpAddr)
                        tmpAddr += 1

                uv = 0
                if idAttr & enums.IndexAttributeFlags.HasUV:
                    if idAttr & enums.IndexAttributeFlags.UV16BitIndex:
                        uv = fileR.rUShort(tmpAddr)
                        tmpAddr += 2
                    else:
                        uv = fileR.rByte(tmpAddr)
                        tmpAddr += 1

                polys.append(PolyVert(pos, nrm, col, uv))

            if polyType == enums.PrimitiveType.Triangles and vCount > 3:
                triCount = math.floor(vCount/3)
                for i in range(triCount):
                    polygons.append([polys[i*3], polys[i*3 +1], polys[i*3 +2]])
            else:
                polygons.append(polys)
        fileR.setBigEndian(False)

        return Geometry(params, polygons)

class Vertices:
    """One vertex data array"""

    vType: enums.VertexAttribute
    fracBitCount: int
    compCount: enums.ComponentCount
    dataType: enums.DataType
    dataPtr: int
    data: list

    def __init__(self,
                 vType: enums.VertexAttribute,
                 fracBitCount: int,
                 compCount: enums.ComponentCount,
                 dataType: enums.DataType,
                 data: list):
        self.vType = vType
        self.fracBitCount = fracBitCount
        self.compCount = compCount
        self.dataType = dataType
        self.data = data

    def getCompSize(self) -> int:
        """Calculates the size of a single element in bytes"""
        return self.compCount.length * self.dataType.length

    def debug(self):
        print("  Attrib:", self.vType)
        print("   fracBitCount:", self.fracBitCount)
        print("   vCount:", len(self.data))
        print("   Component Count:", self.compCount)
        print("   Data Type:", self.dataType)
        print("   Data Pointer:", common.hex4(self.dataPtr))
        print("   Size:", len(self.data) * self.getCompSize())
        print(" - - - - \n")

    def writeData(self, fileW: fileHelper.FileWriter):
        """Writes the data and saves the pointer"""
        self.dataPtr = fileW.tell()

        if self.vType == enums.VertexAttribute.Color0 or self.vType == enums.VertexAttribute.Color1:
            for e in self.data:
                e.writeRGBA(fileW)
        else:
            for e in self.data:
                e.write(fileW)

    def writeAttrib(self, fileW: fileHelper.FileWriter):
        """Writes the attribute of the vertices (requires data to be written)"""
        fileW.wByte(self.vType.value)
        fileW.wByte(self.fracBitCount)
        fileW.wShort(len(self.data))

        datainfo = self.compCount.value | (self.dataType.value << 4)
        fileW.wUInt(datainfo)
        fileW.wUInt(self.dataPtr)
        fileW.wUInt(len(self.data) * self.getCompSize())

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int):

        vType = enums.VertexAttribute(fileR.rByte(address))
        fracBitCount = enums.VertexAttribute(fileR.rByte(address + 1))
        vCount = fileR.rUShort(address +2)

        dataComp = fileR.rByte(address+4)
        compCount = enums.ComponentCount(dataComp & 0xF)
        dataType = enums.DataType(dataComp >> 4)

        dataPtr = fileR.rUInt(address + 8)
        dataSize = fileR.rUInt(address + 12)

        data = list()
        vProps = Vertices(vType, fracBitCount, compCount, dataType, data)
        compSize = vProps.getCompSize()

        for i in range(vCount):
            values = []

            for c in range(compCount.length):
                t = 0
                if dataType == enums.DataType.Signed8:
                    t = fileR.rSByte(dataPtr)
                elif dataType == enums.DataType.Unsigned8:
                    t = fileR.rByte(dataPtr)
                elif dataType == enums.DataType.Signed16:
                    t = fileR.rShort(dataPtr)
                elif dataType == enums.DataType.Unsigned16:
                    t = fileR.rUShort(dataPtr)
                elif dataType == enums.DataType.Float32:
                    t = fileR.rFloat(dataPtr)
                elif dataType == enums.DataType.RGB565:
                    t = fileR.rUShort(dataPtr)
                elif dataType == enums.DataType.RGBA4:
                    t = fileR.rUShort(dataPtr)
                    t = ((t & 0xF) * 2) | ((((t & 0xF0) >> 4) * 2) << 8) | ((((t & 0xF00) >> 8) * 2) << 16) | ((((t & 0xF000) >> 12) * 2) << 24)
                    t = common.ColorARGB.fromRGBA(t)
                elif dataType == enums.DataType.RGBA6:
                    t = fileR.rUInt(dataPtr)
                    t = round((t & 0x3F) * 1.5) | (round(((t & 0xFc0) >> 6) * 1.5) << 8) | (round(((t & 0x3F000) >> 12) * 1.5) << 16) | (round(((t & 0xFC0000) >> 18) * 1.5) << 24)
                    t = common.ColorARGB.fromRGBA(t)
                elif dataType == enums.DataType.RGBX8 or dataType == enums.DataType.RGB8:
                    t = fileR.rUInt(dataPtr) | 0xFF000000
                    t = common.ColorARGB.fromRGBA(t)
                elif dataType == enums.DataType.RGBA8:
                    t = fileR.rUInt(dataPtr)
                    t = common.ColorARGB.fromRGBA(t)

                values.append(t)
                dataPtr += dataType.length

            if compCount == enums.ComponentCount.TexCoord_S or compCount == enums.ComponentCount.TexCoord_ST:
                t = UV()
                t.x = values[0]
                if len(values) == 2:
                    t.y = values[1]

            elif compCount == enums.ComponentCount.Position_XY or compCount == enums.ComponentCount.Position_XYZ or compCount == enums.ComponentCount.Normal_XYZ:
                if len(values) == 2:
                    values.append(0)
                t = Vector3(values)

            data.append(t)

        return Vertices(vType, fracBitCount, compCount, dataType, data)

class Attach:
    """Gamecube format attach"""

    name: str
    vertices: List[Vertices]
    opaqueGeom: List[Geometry]
    transparentGeom: List[Geometry]
    bounds: BoundingBox

    def __init__(self,
                 name: str,
                 vertices: List[Vertices],
                 opaqueGeom: List[Geometry],
                 transparentGeom: List[Geometry],
                 bounds: BoundingBox):
        self.name = name
        self.vertices = vertices
        self.opaqueGeom = opaqueGeom
        self.transparentGeom = transparentGeom
        self.bounds = bounds

    @classmethod
    def fromMesh(cls, mesh: bpy.types.Mesh,
                 export_matrix: mathutils.Matrix,
                 materials: List[bpy.types.Material]):

        # determining which data should be written
        vertexType = mesh.saSettings.sa2ExportType

        # the model has to either contain normals or vertex colors. it wont work with both or none of each
        writeNRM = vertexType == 'NRM' or vertexType == 'NRMW' or (vertexType == 'VC' and len(mesh.vertex_colors) == 0)
        writeVC = not writeNRM #vertexType == 'VC' and len(mesh.vertex_colors) > 0
        writeUV = len(mesh.uv_layers) > 0

        # aquiring the vertex data
        vertices: List[Vertices] = list()

        # position data is always required
        posData = list()
        posIDs = [0] * len(mesh.vertices)
        for i, v in enumerate(mesh.vertices):
            found = None
            pos = Vector3(export_matrix @ v.co)
            for j, p in enumerate(posData):
                if p == pos:
                    found = j
                    break
            if found is None:
                posData.append(pos)
                posIDs[i] = len(posData) - 1
            else:
                posIDs[i] = found
        vertices.append( Vertices(enums.VertexAttribute.Position, 12, enums.ComponentCount.Position_XYZ, enums.DataType.Float32, posData))

        # getting normal data
        if writeNRM:
            nrmData = list()
            nrmIDs = [0] * len(mesh.vertices)
            normals = common.getNormalData(mesh)
            for i, v in enumerate(mesh.vertices):
                found = None
                nrm = Vector3(export_matrix @ normals[i])
                for j, n in enumerate(nrmData):
                    if n == nrm:
                        found = j
                        break
                if found is None:
                    nrmData.append(nrm)
                    nrmIDs[i] = len(nrmData) - 1
                else:
                    nrmIDs[i] = found
            vertices.append( Vertices(enums.VertexAttribute.Normal, 12, enums.ComponentCount.Normal_XYZ, enums.DataType.Float32, nrmData))

        # getting vertex color data
        if writeVC:
            vcData = list()
            vcIDs = [0] * len(mesh.vertex_colors[0].data)
            for i, vc in enumerate(mesh.vertex_colors[0].data):
                found = None
                col = ColorARGB(vc.color)
                for j, c in enumerate(vcData):
                    if col == c:
                        found = j
                        break
                if found is None:
                    vcData.append(col)
                    vcIDs[i] = len(vcData) - 1
                else:
                    vcIDs[i] = found
            vertices.append( Vertices(enums.VertexAttribute.Color0, 4, enums.ComponentCount.Color_RGBA, enums.DataType.RGBA8, vcData))

        # getting uv data
        if writeUV:
            uvData = list()
            uvIDs = [0] * len(mesh.uv_layers[0].data)
            for i, uv in enumerate(mesh.uv_layers[0].data):
                    found = None
                    newUV = UV(uv.uv)
                    for j, uvD in enumerate(uvData):
                        if newUV == uvD:
                            found = j
                            break
                    if found is None:
                        uvData.append(newUV)
                        uvIDs[i] = len(uvData) - 1
                    else:
                        uvIDs[i] = found
            vertices.append( Vertices(enums.VertexAttribute.Tex0, 4, enums.ComponentCount.TexCoord_ST, enums.DataType.Signed16, uvData))

        # assembling polygons

        # preparing polygon lists
        tris: List[List[PolyVert]] = [[] for n in range(len(mesh.materials))]
        if len(tris) == 0:
            tris.append([])

        for p in mesh.polygons:
            for l in p.loop_indices:
                loop = mesh.loops[l]

                posID = posIDs[loop.vertex_index]
                nrmID = None
                vcID = None
                uvID = None

                if writeNRM:
                    nrmID = nrmIDs[loop.vertex_index]
                if writeVC:
                    vcID = vcIDs[l]
                if writeUV:
                    uvID = uvIDs[l]

                tris[p.material_index].append( PolyVert(posID, nrmID, vcID, uvID) )

        #strippifying the poly data

        strips: List[List[List[PolyVert]]] = list() # material specific -> strip -> polygon
        Stripf = strippifier.Strippifier()

        for l in tris:
            if len(l) == 0:
                strips.append(None)
                continue

            distinct = list()
            IDs = [0] * len(l)

            distinct, IDs = common.getDistinctwID(l)

            stripIndices = Stripf.Strippify(IDs, doSwaps=False, concat=False)

            polyStrips = [None] * len(stripIndices)

            for i, strip in enumerate(stripIndices):
                tStrip = [None] * len(strip)
                for j, index in enumerate(strip):
                    tStrip[j] = distinct[index]
                polyStrips[i] = tStrip

            strips.append(polyStrips)

        # generating geometry from the polygon strips
        opaqueGeom = list()
        transparentGeom = list()

        for i, s in enumerate(strips):
            if s is None:
                continue
            mat = None
            matName = mesh.materials[i].name
            if matName in materials:
                mat = materials[matName]
            else:
                print(" Material", matName, "not found")

            # generating parameters
            parameters = list()
            # vtx attribute parameters come first
            parameters.append(VtxAttrFmt(enums.VertexAttribute.Position))
            idAttribs = enums.IndexAttributeFlags.HasPosition
            if writeNRM:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Normal))
                idAttribs |= enums.IndexAttributeFlags.HasNormal
            if writeVC:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Color0))
                idAttribs |= enums.IndexAttributeFlags.HasColor
            if writeUV:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Tex0))
                idAttribs |= enums.IndexAttributeFlags.HasUV

            # ID attributes
            for l in s:
                for p in l:
                    if p.posID > 0xFF:
                        idAttribs |= enums.IndexAttributeFlags.Position16BitIndex
                    if writeNRM and p.nrmID > 0xFF:
                        idAttribs |= enums.IndexAttributeFlags.Normal16BitIndex
                    if writeVC and p.vcID > 0xFF:
                        idAttribs |= enums.IndexAttributeFlags.Color16BitIndex
                    if writeUV and p.uvID > 0xFF:
                        idAttribs |= enums.IndexAttributeFlags.UV16BitIndex

            parameters.append(IndexAttributes(idAttribs))

            # material dependend things
            if mat is None:
                parameters.append(Lighting(1))
                parameters.append(AlphaBlend(enums.AlphaInstruction.SrcAlpha, enums.AlphaInstruction.InverseSrcAlpha, False))
                parameters.append(AmbientColor(ColorARGB((1,1,1,1))))
                parameters.append(Texture(0, enums.TileMode.WrapU | enums.TileMode.WrapV))
                parameters.append(unknown_9())
                parameters.append(TexCoordGen(enums.TexGenMtx.Identity, enums.TexGenSrc.TexCoord0, enums.TexGenType.Matrix2x4, enums.TexCoordID.TexCoord0))
            else:
                matProps: SAMaterialSettings = mat.saSettings
                parameters.append(Lighting(matProps.gc_shadowStencil))

                srcInst = enums.AlphaInstruction.SrcAlpha
                dstInst = enums.AlphaInstruction.InverseSrcAlpha
                if matProps.b_useAlpha:
                    src = matProps.b_srcAlpha
                    if src == 'ONE':
                        srcInst = enums.AlphaInstruction.One
                    elif src == 'OTHER':
                        srcInst = enums.AlphaInstruction.SrcColor
                    elif src == 'INV_OTHER':
                        srcInst = enums.AlphaInstruction.InverseSrcColor
                    elif src == 'SRC':
                        srcInst = enums.AlphaInstruction.SrcAlpha
                    elif src == 'INV_SRC':
                        srcInst = enums.AlphaInstruction.InverseSrcAlpha
                    elif src == 'DST':
                        srcInst = enums.AlphaInstruction.DstAlpha
                    elif src == 'INV_DST':
                        srcInst = enums.AlphaInstruction.InverseDstAlpha
                    else:
                        srcInst = enums.AlphaInstruction.Zero

                    dst = matProps.b_destAlpha
                    if dst == 'ONE':
                        dstInst = enums.AlphaInstruction.One
                    elif dst == 'OTHER':
                        dstInst = enums.AlphaInstruction.SrcColor
                    elif dst == 'INV_OTHER':
                        dstInst = enums.AlphaInstruction.InverseSrcColor
                    elif dst == 'SRC':
                        dstInst = enums.AlphaInstruction.SrcAlpha
                    elif dst == 'INV_SRC':
                        dstInst = enums.AlphaInstruction.InverseSrcAlpha
                    elif dst == 'DST':
                        dstInst = enums.AlphaInstruction.DstAlpha
                    elif dst == 'INV_DST':
                        dstInst = enums.AlphaInstruction.InverseDstAlpha
                    else:
                        dstInst = enums.AlphaInstruction.Zero

                parameters.append(AlphaBlend(srcInst, dstInst, matProps.b_useAlpha))
                parameters.append(AmbientColor(ColorARGB(matProps.b_Ambient)))

                tileMode = enums.TileMode.null

                if not matProps.b_clampV:
                    tileMode |= enums.TileMode.WrapV
                if not matProps.b_clampU:
                    tileMode |= enums.TileMode.WrapU
                if matProps.b_mirrorV:
                    tileMode |= enums.TileMode.MirrorV
                if matProps.b_mirrorU:
                    tileMode |= enums.TileMode.MirrorU

                parameters.append(Texture(matProps.b_TextureID, tileMode))
                parameters.append(unknown_9())

                #texMatrixID
                if matProps.gc_texMatrixID == 'MATRIX0':
                    mtx = enums.TexGenMtx.Matrix0
                elif matProps.gc_texMatrixID == 'MATRIX1':
                    mtx = enums.TexGenMtx.Matrix1
                elif matProps.gc_texMatrixID == 'MATRIX2':
                    mtx = enums.TexGenMtx.Matrix2
                elif matProps.gc_texMatrixID == 'MATRIX3':
                    mtx = enums.TexGenMtx.Matrix3
                elif matProps.gc_texMatrixID == 'MATRIX4':
                    mtx = enums.TexGenMtx.Matrix4
                elif matProps.gc_texMatrixID == 'MATRIX5':
                    mtx = enums.TexGenMtx.Matrix5
                elif matProps.gc_texMatrixID == 'MATRIX6':
                    mtx = enums.TexGenMtx.Matrix6
                elif matProps.gc_texMatrixID == 'MATRIX7':
                    mtx = enums.TexGenMtx.Matrix7
                elif matProps.gc_texMatrixID == 'MATRIX8':
                    mtx = enums.TexGenMtx.Matrix8
                elif matProps.gc_texMatrixID == 'MATRIX9':
                    mtx = enums.TexGenMtx.Matrix9
                elif matProps.gc_texMatrixID == 'IDENTITY':
                    mtx = enums.TexGenMtx.Identity

                #texGenSrc
                if matProps.gc_texGenType[0] == 'M': #Matrix
                    if matProps.gc_texGenSourceMtx == 'POSITION':
                        src = enums.TexGenSrc.Position
                    elif matProps.gc_texGenSourceMtx == 'NORMAL':
                        src = enums.TexGenSrc.Normal
                    elif matProps.gc_texGenSourceMtx == 'BINORMAL':
                        src = enums.TexGenSrc.Binormal
                    elif matProps.gc_texGenSourceMtx == 'TANGENT':
                        src = enums.TexGenSrc.Tangent
                    elif matProps.gc_texGenSourceMtx == 'TEX0':
                        src = enums.TexGenSrc.Tex0
                    elif matProps.gc_texGenSourceMtx == 'TEX1':
                        src = enums.TexGenSrc.Tex1
                    elif matProps.gc_texGenSourceMtx == 'TEX2':
                        src = enums.TexGenSrc.Tex2
                    elif matProps.gc_texGenSourceMtx == 'TEX3':
                        src = enums.TexGenSrc.Tex3
                    elif matProps.gc_texGenSourceMtx == 'TEX4':
                        src = enums.TexGenSrc.Tex4
                    elif matProps.gc_texGenSourceMtx == 'TEX5':
                        src = enums.TexGenSrc.Tex5
                    elif matProps.gc_texGenSourceMtx == 'TEX6':
                        src = enums.TexGenSrc.Tex6
                    elif matProps.gc_texGenSourceMtx == 'TEX7':
                        src = enums.TexGenSrc.Tex7
                elif matProps.gc_texGenType[0] == 'B': #Bump
                    if matProps.gc_texGenSourceBmp == 'TEXCOORD0':
                        src = enums.TexGenSrc.TexCoord0
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD1':
                        src = enums.TexGenSrc.TexCoord1
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD2':
                        src = enums.TexGenSrc.TexCoord2
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD3':
                        src = enums.TexGenSrc.TexCoord3
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD4':
                        src = enums.TexGenSrc.TexCoord4
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD5':
                        src = enums.TexGenSrc.TexCoord5
                    elif matProps.gc_texGenSourceBmp == 'TEXCOORD6':
                        src = enums.TexGenSrc.TexCoord6
                else: #SRTG
                    if matProps.gc_texGenSourceSRTG == 'COLOR0':
                        src = enums.TexGenSrc.Color0
                    elif matProps.gc_texGenSourceSRTG == 'COLOR1':
                        src = enums.TexGenSrc.Color1

                #texGenType
                if matProps.gc_texGenType == 'MTX3X4':
                    typ = enums.TexGenType.Matrix3x4
                elif matProps.gc_texGenType == 'MTX2X4':
                    typ = enums.TexGenType.Matrix2x4
                elif matProps.gc_texGenType == 'BUMP0':
                    typ = enums.TexGenType.Bump0
                elif matProps.gc_texGenType == 'BUMP1':
                    typ = enums.TexGenType.Bump1
                elif matProps.gc_texGenType == 'BUMP2':
                    typ = enums.TexGenType.Bump2
                elif matProps.gc_texGenType == 'BUMP3':
                    typ = enums.TexGenType.Bump3
                elif matProps.gc_texGenType == 'BUMP4':
                    typ = enums.TexGenType.Bump4
                elif matProps.gc_texGenType == 'BUMP5':
                    typ = enums.TexGenType.Bump5
                elif matProps.gc_texGenType == 'BUMP6':
                    typ = enums.TexGenType.Bump6
                elif matProps.gc_texGenType == 'BUMP7':
                    typ = enums.TexGenType.Bump7
                elif matProps.gc_texGenType == 'SRTG':
                    typ = enums.TexGenType.SRTG

                #texCoordID
                if matProps.gc_texCoordID == 'TEXCOORD0':
                    tID = enums.TexCoordID.TexCoord0
                elif matProps.gc_texCoordID == 'TEXCOORD1':
                    tID = enums.TexCoordID.TexCoord1
                elif matProps.gc_texCoordID == 'TEXCOORD2':
                    tID = enums.TexCoordID.TexCoord2
                elif matProps.gc_texCoordID == 'TEXCOORD3':
                    tID = enums.TexCoordID.TexCoord3
                elif matProps.gc_texCoordID == 'TEXCOORD4':
                    tID = enums.TexCoordID.TexCoord4
                elif matProps.gc_texCoordID == 'TEXCOORD5':
                    tID = enums.TexCoordID.TexCoord5
                elif matProps.gc_texCoordID == 'TEXCOORD6':
                    tID = enums.TexCoordID.TexCoord6
                elif matProps.gc_texCoordID == 'TEXCOORD7':
                    tID = enums.TexCoordID.TexCoord7
                elif matProps.gc_texCoordID == 'TEXCOORD8':
                    tID = enums.TexCoordID.TexCoord8
                elif matProps.gc_texCoordID == 'TEXCOORD9':
                    tID = enums.TexCoordID.TexCoord9
                elif matProps.gc_texCoordID == 'TEXCOORDMAX':
                    tID = enums.TexCoordID.TexCoordMax
                elif matProps.gc_texCoordID == 'TEXCOORDNULL':
                    tID = enums.TexCoordID.TexCoordNull

                parameters.append(TexCoordGen(mtx, src, typ, tID))

            geom = Geometry(parameters, s)
            if mat is not None and mat.saSettings.b_useAlpha:
                transparentGeom.append(geom)
            else:
                opaqueGeom.append(geom)

        # calculating the bounds
        bounds = BoundingBox(mesh.vertices)
        bounds.adjust(export_matrix)

        return Attach(mesh.name, vertices, opaqueGeom, transparentGeom, bounds)

    def write(self,
              fileW: fileHelper.FileWriter,
              labels: dict,
              meshDict: dict = None):
        # writing vertex data first
        for l in self.vertices:
            l.writeData(fileW)

        # writing the vertex properties
        vertPtr = fileW.tell()

        for l in self.vertices:
            l.writeAttrib(fileW)

        fileW.wULong(0xFF) # an empty vertex attrib (terminator)

        # next we write geometry data
        # opaque data comes first
        for g in self.opaqueGeom:
            g.writeParams(fileW)
            g.writePolygons(fileW)

        opaquePtr = fileW.tell()
        for g in self.opaqueGeom:
            g.writeGeom(fileW)

        # then the transparent data
        for g in self.transparentGeom:
            g.writeParams(fileW)
            g.writePolygons(fileW)

        transparentPtr = fileW.tell()
        for g in self.transparentGeom:
            g.writeGeom(fileW)

        # writing attach info

        attachPtr = fileW.tell()
        labels[attachPtr] = "gc_" + self.name
        if meshDict is not None:
            meshDict[self.name] = attachPtr
        fileW.wUInt(vertPtr)
        fileW.wUInt(0) # gap
        fileW.wUInt(opaquePtr)
        fileW.wUInt(transparentPtr)
        fileW.wUShort(len(self.opaqueGeom))
        fileW.wUShort(len(self.transparentGeom))
        self.bounds.write(fileW)

    @classmethod
    def read(cls, fileR: fileHelper.FileReader, address: int, meshID: int, labels: dict):

        if address in labels:
            name: str = labels[address]
            if name.startswith("gc_"):
                name = name[3:]
        else:
            name = "Attach_" + str(meshID)

        if DO:
            print("\n === reading gc:", name, "===")

        # reading vertex attributes
        vertPtr = fileR.rUInt(address)

        vertices = list()
        attrType = enums.VertexAttribute(fileR.rByte(vertPtr))
        while attrType != enums.VertexAttribute.Null:
            vertices.append(Vertices.read(fileR, vertPtr))
            vertPtr += 16
            attrType = enums.VertexAttribute(fileR.rByte(vertPtr))

        oMeshCount = fileR.rUShort(address + 16)
        tMeshCount = fileR.rUShort(address + 18)

        opaqueGeom = list()
        transparentGeom = list()

        tmpAddr = fileR.rUInt(address + 8)

        # the geometries in a mesh can reuse parameters, so we gotta store them
        params = dict()

        for o in range(oMeshCount):
            if DO:
                print(" -- Geometry", o, "--")
            opaqueGeom.append(Geometry.read(fileR, tmpAddr, params))
            tmpAddr += 16

        tmpAddr = fileR.rUInt(address + 12)
        for t in range(tMeshCount):
            transparentGeom.append(Geometry.read(fileR, tmpAddr, params))
            tmpAddr += 16


        return Attach(name, vertices, opaqueGeom, transparentGeom, None)

def process_GC(models: List[common.Model], attaches: Dict[int, Attach]):

    import bmesh
    meshes: Dict[int, bpy.types.Mesh] = dict()

    materials: List[bpy.types.Material] = list()
    matDicts: List[dict] = list()

    for o in models:
        if o.meshPtr == 0 or o.meshPtr not in attaches:
            continue
        elif o.meshPtr in meshes:
            o.meshes.append(meshes[o.meshPtr])
            continue

        attach = attaches[o.meshPtr]

        pos: List[Vector3] = None
        nrm: List[Vector3] = None
        col: List[ColorARGB] = None
        uv: List[UV] = None

        for v in attach.vertices:
            if v.vType == enums.VertexAttribute.Position:
                pos = v.data
            elif v.vType == enums.VertexAttribute.Normal:
                nrm = v.data
            elif v.vType == enums.VertexAttribute.Color0:
                col = v.data
            elif v.vType == enums.VertexAttribute.Tex0:
                uv = v.data

        vertPairs: Dict[Tuple[int, int], bmesh.types.BMVert] = dict()

        # going through the polygons and creating the vertpairs
        geom: List[Geometry] = list()
        geom.extend(attach.opaqueGeom)
        geom.extend(attach.transparentGeom)

        for g in geom:
            for p in g.polygons:
                for pv in p:
                    pair = (pv.posID, pv.nrmID)
                    if pair not in vertPairs.keys():
                        vertPairs[pair] = None

        # creating the materials

        meshMaterials = list()
        geomMaterials = list()
        from .__init__ import SAMaterialSettings

        for g in geom:
            tmpMat = SAMaterialSettings.getDefaultMatDict()

            for p in g.params:
                if p.pType == enums.ParameterType.AmbientColor:
                    tmpMat["b_Ambient"] = p.color.toBlenderTuple()
                elif p.pType == enums.ParameterType.BlendAlpha:
                    if p.dst == enums.AlphaInstruction.Zero:
                        tmpMat["b_destAlpha"] = 'ZERO'
                    elif p.dst == enums.AlphaInstruction.One:
                        tmpMat["b_destAlpha"] = 'ONE'
                    elif p.dst == enums.AlphaInstruction.SrcColor:
                        tmpMat["b_destAlpha"] = 'OTHER'
                    elif p.dst == enums.AlphaInstruction.InverseSrcColor:
                        tmpMat["b_destAlpha"] = 'INV_OTHER'
                    elif p.dst == enums.AlphaInstruction.SrcAlpha:
                        tmpMat["b_destAlpha"] = 'SRC'
                    elif p.dst == enums.AlphaInstruction.InverseSrcAlpha:
                        tmpMat["b_destAlpha"] = 'INV_SRC'
                    elif p.dst == enums.AlphaInstruction.DstAlpha:
                        tmpMat["b_destAlpha"] = 'DST'
                    elif p.dst == enums.AlphaInstruction.InverseDstAlpha:
                        tmpMat["b_destAlpha"] = 'INV_DST'

                    if p.src == enums.AlphaInstruction.Zero:
                        tmpMat["b_srcAlpha"] = 'ZERO'
                    elif p.src == enums.AlphaInstruction.One:
                        tmpMat["b_srcAlpha"] = 'ONE'
                    elif p.src == enums.AlphaInstruction.SrcColor:
                        tmpMat["b_srcAlpha"] = 'OTHER'
                    elif p.src == enums.AlphaInstruction.InverseSrcColor:
                        tmpMat["b_srcAlpha"] = 'INV_OTHER'
                    elif p.src == enums.AlphaInstruction.SrcAlpha:
                        tmpMat["b_srcAlpha"] = 'SRC'
                    elif p.src == enums.AlphaInstruction.InverseSrcAlpha:
                        tmpMat["b_srcAlpha"] = 'INV_SRC'
                    elif p.src == enums.AlphaInstruction.DstAlpha:
                        tmpMat["b_srcAlpha"] = 'DST'
                    elif p.src == enums.AlphaInstruction.InverseDstAlpha:
                        tmpMat["b_srcAlpha"] = 'INV_DST'

                    tmpMat["b_useAlpha"] = p.active
                elif p.pType == enums.ParameterType.TexCoordGen:

                    #texMatrixID
                    if p.mtx == enums.TexGenMtx.Matrix0:
                        tmpMat["gc_texMatrixID"] = 'MATRIX0'
                    elif p.mtx == enums.TexGenMtx.Matrix1:
                        tmpMat["gc_texMatrixID"] = 'MATRIX1'
                    elif p.mtx == enums.TexGenMtx.Matrix2:
                        tmpMat["gc_texMatrixID"] = 'MATRIX2'
                    elif p.mtx == enums.TexGenMtx.Matrix3:
                        tmpMat["gc_texMatrixID"] = 'MATRIX4'
                    elif p.mtx == enums.TexGenMtx.Matrix5:
                        tmpMat["gc_texMatrixID"] = 'MATRIX6'
                    elif p.mtx == enums.TexGenMtx.Matrix7:
                        tmpMat["gc_texMatrixID"] = 'MATRIX7'
                    elif p.mtx == enums.TexGenMtx.Matrix8:
                        tmpMat["gc_texMatrixID"] = 'MATRIX9'
                    elif p.mtx == enums.TexGenMtx.Matrix9:
                        tmpMat["gc_texMatrixID"] = 'MATRIX9'
                    elif p.mtx == enums.TexGenMtx.Identity:
                        tmpMat["gc_texMatrixID"] = 'IDENTITY'

                    #texGenType
                    if p.typ == enums.TexGenType.Matrix3x4:
                        tmpMat["gc_texGenType"] = 'MTX3X4'
                    elif p.typ == enums.TexGenType.Matrix2x4:
                        tmpMat["gc_texGenType"] = 'MTX2X4'
                    elif p.typ == enums.TexGenType.Bump0:
                        tmpMat["gc_texGenType"] = 'BUMP0'
                    elif p.typ == enums.TexGenType.Bump1:
                        tmpMat["gc_texGenType"] = 'BUMP1'
                    elif p.typ == enums.TexGenType.Bump2:
                        tmpMat["gc_texGenType"] = 'BUMP2'
                    elif p.typ == enums.TexGenType.Bump3:
                        tmpMat["gc_texGenType"] = 'BUMP3'
                    elif p.typ == enums.TexGenType.Bump4:
                        tmpMat["gc_texGenType"] = 'BUMP4'
                    elif p.typ == enums.TexGenType.Bump5:
                        tmpMat["gc_texGenType"] = 'BUMP5'
                    elif p.typ == enums.TexGenType.Bump6:
                        tmpMat["gc_texGenType"] = 'BUMP6'
                    elif p.typ == enums.TexGenType.Bump7:
                        tmpMat["gc_texGenType"] = 'BUMP7'
                    elif p.typ == enums.TexGenType.SRTG:
                        tmpMat["gc_texGenType"] = 'SRTG'


                    #texGenSrc
                    if tmpMat["gc_texGenType"][0] == 'M': #Matrix
                        if p.src == enums.TexGenSrc.Position:
                            tmpMat["gc_texGenSourceMtx"] = 'POSITION'
                        elif p.src == enums.TexGenSrc.Normal:
                            tmpMat["gc_texGenSourceMtx"] = 'NORMAL'
                        elif p.src == enums.TexGenSrc.Binormal:
                            tmpMat["gc_texGenSourceMtx"] = 'BINORMAL'
                        elif p.src == enums.TexGenSrc.Tangent:
                            tmpMat["gc_texGenSourceMtx"] = 'TANGENT'
                        elif p.src == enums.TexGenSrc.Tex0:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX0'
                        elif p.src == enums.TexGenSrc.Tex1:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX1'
                        elif p.src == enums.TexGenSrc.Tex2:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX2'
                        elif p.src == enums.TexGenSrc.Tex3:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX3'
                        elif p.src == enums.TexGenSrc.Tex4:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX4'
                        elif p.src == enums.TexGenSrc.Tex5:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX5'
                        elif p.src == enums.TexGenSrc.Tex6:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX6'
                        elif p.src == enums.TexGenSrc.Tex7:
                            tmpMat["gc_texGenSourceMtx"] = 'TEX7'
                        else:
                            print("Not valid mtx + src combination:", p.typ, p.src)
                    elif tmpMat["gc_texGenType"][0] == 'B': #Bump
                        if p.src == enums.TexGenSrc.TexCoord0:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD0'
                        elif p.src == enums.TexGenSrc.TexCoord1:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD1'
                        elif p.src == enums.TexGenSrc.TexCoord2:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD2'
                        elif p.src == enums.TexGenSrc.TexCoord3:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD3'
                        elif p.src == enums.TexGenSrc.TexCoord4:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD4'
                        elif p.src == enums.TexGenSrc.TexCoord5:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD5'
                        elif p.src == enums.TexGenSrc.TexCoord6:
                            tmpMat["gc_texGenSourceBmp"] = 'TEXCOORD6'
                        else:
                            print("Not valid mtx + src combination:", p.typ, p.src)
                    else: #SRTG
                        if p.src == enums.TexGenSrc.Color0:
                            tmpMat["gc_texGenSourceSRTG"] = 'COLOR0'
                        elif p.src == enums.TexGenSrc.Color0:
                            tmpMat["gc_texGenSourceSRTG"] = 'COLOR1'
                        else:
                            print("Not valid mtx + src combination:", p.typ, p.src)

                    #texCoordID
                    if p.texID == enums.TexCoordID.TexCoord0:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD0'
                    elif p.texID == enums.TexCoordID.TexCoord1:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD1'
                    elif p.texID == enums.TexCoordID.TexCoord2:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD2'
                    elif p.texID == enums.TexCoordID.TexCoord3:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD3'
                    elif p.texID == enums.TexCoordID.TexCoord4:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD4'
                    elif p.texID == enums.TexCoordID.TexCoord5:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD5'
                    elif p.texID == enums.TexCoordID.TexCoord6:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD6'
                    elif p.texID == enums.TexCoordID.TexCoord7:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD7'
                    elif p.texID == enums.TexCoordID.TexCoord8:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD8'
                    elif p.texID == enums.TexCoordID.TexCoord9:
                        tmpMat["gc_texCoordID"] = 'TEXCOORD9'
                    elif p.texID == enums.TexCoordID.TexCoordMax:
                        tmpMat["gc_texCoordID"] = 'TEXCOORDMAX'
                    elif p.texID == enums.TexCoordID.TexCoordNull:
                        tmpMat["gc_texCoordID"] = 'TEXCOORDNULL'
                elif p.pType == enums.ParameterType.Texture:
                    tmpMat["b_TextureID"] = p.texID
                    tmpMat["b_clampU"] = not bool(p.tilemode & enums.TileMode.WrapU)
                    tmpMat["b_clampV"] = not bool(p.tilemode & enums.TileMode.WrapV)
                    tmpMat["b_mirrorU"] = bool(p.tilemode & enums.TileMode.MirrorU)
                    tmpMat["b_mirrorV"] = bool(p.tilemode & enums.TileMode.MirrorV)

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

            geomMaterials.append(meshMaterials.index(material))

        # creating the mesh

        mesh = bpy.data.meshes.new(attach.name)
        for m in meshMaterials:
            mesh.materials.append(m)

        bm = bmesh.new()
        bm.from_mesh(mesh)

        normals = list()

        for vn in vertPairs:
            v = pos[vn[0]]
            v = bm.verts.new((v.x, -v.z, v.y))
            vertPairs[vn] = v
            if nrm is not None:
                normals.append(nrm[vn[1]])

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        doubleFaces = 0

        if uv is not None:
            uvLayer = bm.loops.layers.uv.new("UV0")
        if col is not None:
            colorLayer = bm.loops.layers.color.new("COL0")

        for matIndex, g in enumerate(geom):
            for p in g.polygons:
                rev = True
                for i in range(len(p) - 2):

                    polyVerts: List[PolyVert] = list()
                    verts = list()
                    for pv in range(3):
                        pVert = p[i + pv]
                        pVert.uvID
                        polyVerts.append(pVert)
                        verts.append(vertPairs[(pVert.posID, pVert.nrmID)])
                    if rev:
                        verts = [verts[1], verts[0], verts[2]]
                        polyVerts = [polyVerts[1], polyVerts[0], polyVerts[2]]
                    rev = not rev
                    if len(set(verts)) < 3:
                        continue

                    try:
                        face = bm.faces.new(verts)
                    except Exception as e:
                        if not str(e).endswith("exists"):
                            print("Invalid triangle:", str(e))
                        else:
                            doubleFaces += 1
                        continue

                    for l, pc in zip(face.loops, polyVerts):
                        if uv is not None:
                            l[uvLayer].uv = uv[pc.uvID].getBlenderUV()
                        if col is not None:
                            l[colorLayer] = col[pc.vcID].toBlenderTuple()

                    face.smooth = True
                    face.material_index = geomMaterials[matIndex]

        bm.to_mesh(mesh)
        bm.clear()

        if nrm is not None:
            normals = [mathutils.Vector((n.x, -n.z, n.y)).normalized() for n in normals]

            mesh.create_normals_split()
            split_normal = [normals[l.vertex_index] for l in mesh.loops]
            mesh.normals_split_custom_set(split_normal)

        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = 180

        # dont ask me why, but blender likes to add sharp edges- we dont need those at all in this case
        for e in mesh.edges:
            e.use_edge_sharp = False

        mesh.saSettings.sa2ExportType = 'VC' if col is not None else 'NRM'

        o.meshes.append(mesh)
        meshes[o.meshPtr] = mesh
