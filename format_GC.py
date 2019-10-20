import bpy
import math
import mathutils
from typing import List

from . import fileWriter, enums, strippifier, common
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

    def write(self, fileW: fileWriter.FileWriter):
        fileW.wUInt(self.pType.value)
        fileW.wUInt(self.data)

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
        g = (self.data >> 8) & 0xFF
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

        for p in params:
            if isinstance(p, IndexAttributes):
                self.indexAttributes = p.indexAttributes
            if isinstance(p, AlphaBlend):
                self.transparent = p.active

        if self.indexAttributes is None:
            print("Index attributes not found")

    def writeParams(self, fileW: fileWriter.FileWriter):
        """Writes the parameters of the geometry"""
        self.paramPtr = fileW.tell()
        for p in self.params:
            p.write(fileW)

    def writePolygons(self, fileW: fileWriter.FileWriter):
        """Writes the polygon data of the geometry"""
        self.polygonPtr = fileW.tell()
        fileW.setBigEndian(True)

        for l in self.polygons:
            if len(l) == 3:
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

    def writeGeom(self, fileW: fileWriter.FileWriter):
        """Writes geometry data (requires params and polygons to be written)"""
        fileW.wUInt(self.paramPtr)
        fileW.wUInt(len(self.params))
        fileW.wUInt(self.polygonPtr)
        fileW.wUInt(self.polygonSize)

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
        structSize = 1
        if self.compCount == enums.ComponentCount.Position_XYZ or self.compCount == enums.ComponentCount.Normal_XYZ:
            structSize = 3
        elif self.compCount == enums.ComponentCount.TexCoord_ST or self.compCount == enums.ComponentCount.Position_XY:
            structSize = 2

        if self.dataType == enums.DataType.Unsigned8 or self.dataType == enums.DataType.Signed8:
            structSize = structSize
        elif self.dataType == enums.DataType.Signed16 or self.dataType == enums.DataType.Unsigned16 or self.dataType == enums.DataType.RGB565 or self.dataType == enums.DataType.RGBA4 :
            structSize *= 2
        else:
            structSize *= 4

        return structSize
    
    def debug(self):
        print("  Attrib:", self.vType)
        print("   fracBitCount:", self.fracBitCount)
        print("   vCount:", len(self.data))
        print("   Component Count:", self.compCount)
        print("   Data Type:", self.dataType)
        print("   Data Pointer:", common.hex4(self.dataPtr))
        print("   Size:", len(self.data) * self.getCompSize())
        print(" - - - - \n")

    def writeData(self, fileW: fileWriter.FileWriter):
        """Writes the data and saves the pointer"""
        self.dataPtr = fileW.tell()

        if self.vType == enums.VertexAttribute.Color0 or self.vType == enums.VertexAttribute.Color1:
            for e in self.data:
                e.writeRGBA(fileW)
        else:
            for e in self.data:
                e.write(fileW)

    def writeAttrib(self, fileW: fileWriter.FileWriter):
        """Writes the attribute of the vertices (requires data to be written)"""
        fileW.wByte(self.vType.value)
        fileW.wByte(self.fracBitCount)
        fileW.wShort(len(self.data))
        
        datainfo = self.compCount.value | (self.dataType.value << 4)
        fileW.wUInt(datainfo)
        fileW.wUInt(self.dataPtr)
        fileW.wUInt(len(self.data) * self.getCompSize())

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

    def fromMesh(mesh: bpy.types.Mesh, 
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
            for i, v in enumerate(mesh.vertices):
                found = None
                nrm = Vector3(export_matrix @ v.normal)
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
        tris: List[List[PolyVert]] = [[] for n in mesh.materials]
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
            for m in materials:
                if m.name == mesh.materials[i].name:
                    mat = m

            # generating parameters
            parameters = list()
            # vtx attribute parameters come first
            parameters.append(VtxAttrFmt(enums.VertexAttribute.Position))
            if writeNRM:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Normal))
            if writeVC:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Color0))
            if writeUV:
                parameters.append(VtxAttrFmt(enums.VertexAttribute.Tex0))
            
            # ID attributes
            idAttribs = enums.IndexAttributeFlags.HasPosition
            if writeNRM:
                idAttribs |= enums.IndexAttributeFlags.HasNormal
            if writeVC:
                idAttribs |= enums.IndexAttributeFlags.HasColor
            if writeUV:
                idAttribs |= enums.IndexAttributeFlags.HasUV
            
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
              fileW: fileWriter.FileWriter, 
              labels: dict):
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

        labels["gc_" + self.name] = fileW.tell()
        fileW.wUInt(vertPtr)
        fileW.wUInt(0) # gap
        fileW.wUInt(opaquePtr)
        fileW.wUInt(transparentPtr)
        fileW.wUShort(len(self.opaqueGeom))
        fileW.wUShort(len(self.transparentGeom))
        self.bounds.write(fileW)


