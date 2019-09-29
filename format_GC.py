import bpy
import math
import mathutils
from . import fileWriter, enums, strippifier

DO = False

def debug(*string):
    global DO
    if DO:
        print(*string)

class Vector3(mathutils.Vector):

    def toMathutils(self):
        import mathutils
        return mathutils.Vector((self.x, self.y, self.z))

    def distanceFromCenter(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z)**(0.5)

    def write(self, fileW):
        fileW.wFloat(self.x)
        fileW.wFloat(self.y)
        fileW.wFloat(self.z)

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

    def __eq__(self, other):
        return self.a == other.a and self.r == other.r and self.g == other.g and self.b == other.b

    def __str__(self):
        return "(" + str(self.a) + ", " + str(self.r) + ", " + str(self.g) + ", " + str(self.b) + ")"

    def write(self, fileW):
        """writes data to file"""
      
        fileW.wByte(self.a)
        fileW.wByte(self.b)
        fileW.wByte(self.g)                
        fileW.wByte(self.r)


         


class UV:

    x = 0
    y = 0

    def __init__(self, uv):
        self.x = round(uv[0] * 256)
        self.y = round((1-uv[1]) * 256)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def write(self, fileW):
        fileW.wShort(self.x)
        fileW.wShort(self.y)

class PolyVert:

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

    def writeData(fileW, polyList, idFlags: enums.IndexAttributeFlags, material):
        
        # writing parameters
        paramAddress = fileW.tell()
        paramCount = 0

        # index attribute parameter
        fileW.wUInt(enums.ParameterType.IndexAttributeFlags.value)
        fileW.wUInt(idFlags.value)
        paramCount += 1

        # lighting parameters (we have no clue how those work atm, so we just write a default
        fileW.wUInt(enums.ParameterType.Lighting.value)
        fileW.wUInt(0x00010B11) # enables shadows and uses vertex colors, dont ask me why or how that works
        paramCount += 1

        # that unknown parameter
        fileW.wUInt(enums.ParameterType.Unknown_9.value)
        fileW.wUInt(0x04) # seems to be default
        paramCount += 1

        if material == None:
            # ambient color
            fileW.wUInt(enums.ParameterType.AmbientColor.value)
            color = ColorARGB([1,1,1,1])
            color.write(fileW)
            paramCount += 1

            #texture
            fileW.wUInt(enums.ParameterType.Texture.value)
            fileW.wUInt(0) # texture 0 with no tilemode
            paramCount += 1

            #texCoordGen
            fileW.wUInt(enums.ParameterType.TexCoordGen.value)

            mtx = enums.TexGenMtx.Identity # use default matrix
            src = enums.TexGenSrc.TexCoord0 # on uv set 0
            typ = enums.TexGenType.Matrix2x4 # with a 2x4 matrix (2d matrix)
            tID = enums.TexCoordID.TexCoord0 # and save that in uvslot 0

            value = mtx.value | (src.value << 4) | (typ.value << 12) | (tID.value << 16)
            fileW.wUInt(value)

            paramCount += 1

        else:
            matProps = material.saSettings

            # ambient color
            fileW.wUInt(enums.ParameterType.AmbientColor.value)
            color = ColorARGB(matProps.b_Ambient)
            color.write(fileW)
            paramCount += 1

            if matProps.b_useAlpha:
                fileW.wUInt(enums.ParameterType.BlendAlpha.value)

                srcInst = enums.AlphaInstruction.Zero

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

                dstInst = enums.AlphaInstruction.Zero
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
            
                value = (dstInst.value << 8) | (srcInst.value << 11)
                fileW.wUInt(value)

                paramCount += 1

            #texture
            fileW.wUInt(enums.ParameterType.Texture.value)
            fileW.wUShort(matProps.b_TextureID)
            
            tileMode = enums.TileMode.null

            if matProps.b_clampV:
                tileMode |= enums.TileMode.WrapV
            if matProps.b_clampU:
                tileMode |= enums.TileMode.WrapU
            if matProps.b_mirrorV:
                tileMode |= enums.TileMode.MirrorV
            if matProps.b_mirrorU:
                tileMode |= enums.TileMode.MirrorU
            
            fileW.wUShort(tileMode.value)

            paramCount += 1

            #texCoordGen
            fileW.wUInt(enums.ParameterType.TexCoordGen.value)

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

            value = mtx.value | (src.value << 4) | (typ.value << 12) | (tID.value << 16)
            fileW.wUInt(value)

            paramCount += 1
        
        #writing primitives

        indexAddress = fileW.tell()

        fileW.setBigEndian(bigEndian = True) # for some reason they are big endian

        for l in polyList:
            fileW.wByte(enums.PrimitiveType.TriangleStrip.value)
            fileW.wUShort(len(l))
            for p in l:
                if idFlags & enums.IndexAttributeFlags.Position16BitIndex:
                    fileW.wUShort(p.posID)
                else:
                    fileW.wByte(p.posID)

                if idFlags & enums.IndexAttributeFlags.HasNormal:
                    if idFlags & enums.IndexAttributeFlags.Normal16BitIndex:
                        fileW.wUShort(p.nrmID)
                    else:
                        fileW.wByte(p.nrmID)
                    
                if idFlags & enums.IndexAttributeFlags.HasColor:
                    if idFlags & enums.IndexAttributeFlags.Color16BitIndex:
                        fileW.wUShort(p.vcID)
                    else:
                        fileW.wByte(p.vcID)

                if idFlags & enums.IndexAttributeFlags.HasUV:
                    if idFlags & enums.IndexAttributeFlags.UV16BitIndex:
                        fileW.wUShort(p.uvID)
                    else:
                        fileW.wByte(p.uvID)

        fileW.setBigEndian(bigEndian = False)

        return meshProp(paramAddress, paramCount, indexAddress, fileW.tell() - indexAddress)

class BoundingBox:
    """Used to calculate the bounding sphere which the game uses"""

    boundCenter = Vector3()

    def __init__(self, vertices):
        self.x = 0
        self.xn = 0
        self.y = 0
        self.yn = 0
        self.z = 0
        self.zn = 0

        for v in vertices:
            if self.x < v.co.x:
                self.x = v.co.x
            elif self.xn > v.co.x:
                self.xn = v.co.x

            if self.y < v.co.y:
                self.y = v.co.y
            elif self.yn > v.co.y:
                self.yn = v.co.y

            if self.z < v.co.z:
                self.z = v.co.z
            elif self.zn > v.co.z:
                self.zn = v.co.z
        cx = BoundingBox.center(self.x,self.xn)
        cy = BoundingBox.center(self.y,self.yn)
        cz = BoundingBox.center(self.z,self.zn)

        self.boundCenter = Vector3((cx,cy,cz))

        distance = 0
        for v in vertices:
            dif = Vector3( (self.boundCenter.x - v.co.x, 
                            self.boundCenter.y - v.co.y, 
                            self.boundCenter.z - v.co.z) )
            tDist = math.sqrt(pow(dif.x, 2) + pow(dif.y, 2) + pow(dif.z, 2))
            if tDist > distance:
                distance = tDist

        self.radius = distance
    
    def center(p1, p2):
        return (p1 + p2) / 2.0

    def write(self, fileW):
        self.boundCenter.write(fileW)
        fileW.wFloat(self.radius)

class vertexAttrib:

    vType = enums.VertexAttribute.Null
    fracBitCount = 12 #default
    unknown = 0
    compCount = enums.ComponentCount.Position_XYZ
    dataType = enums.DataType.Float32
    address = 0
    size = 0

    def __init__(self, vType, unknown, compCount, dataType, address, vCount):
        self.vType = vType
        if vType == enums.VertexAttribute.Null:
            self.fracBitCount = 0
        self.unknown = unknown
        self.compCount = compCount
        self.dataType = dataType
        self.address = address

        structSize = 1
        if compCount == enums.ComponentCount.Position_XYZ or compCount == enums.ComponentCount.Normal_XYZ:
            structSize = 3
        elif compCount == enums.ComponentCount.TexCoord_ST or compCount == enums.ComponentCount.Position_XY:
            structSize = 2

        if dataType == enums.DataType.Unsigned8 or dataType == enums.DataType.Signed8:
            structSize = structSize
        elif dataType == enums.DataType.Signed16 or dataType == enums.DataType.Unsigned16 or dataType == enums.DataType.RGB565 or dataType == enums.DataType.RGBA4 :
            structSize *= 2
        else:
            structSize *= 4

        self.size = vCount * structSize

    def debug(self):
        print(" Attrib:", self.vType)
        print("   fracBitCount:", self.fracBitCount)
        print("   unknown:", self.unknown)
        print("   Component Count:", self.compCount)
        print("   Data Type:", self.dataType)
        print("   Data Address:", self.address)
        print("   Size:", self.size)
        print(" ---- \n")

    def write(self, fileW):
        fileW.wByte(self.vType.value)
        fileW.wByte(self.fracBitCount)
        fileW.wShort(self.unknown)
        
        datainfo = self.compCount.value | (self.dataType.value << 4)
        fileW.wUInt(datainfo)
        fileW.wUInt(self.address)
        fileW.wUInt(self.size)

class meshProp:

    parameterAddress = 0
    parameterCount = 0
    indexDataAddress = 0
    indexDataSize = 0

    def __init__(self, parameterAddress, parameterCount, indexDataAddress, indexDataSize):
        self.parameterAddress = parameterAddress
        self.parameterCount = parameterCount
        self.indexDataAddress = indexDataAddress
        self.indexDataSize = indexDataSize

    def debug(self):
        print(" MeshProp:")
        print("  Param Address:", self.parameterAddress)
        print("  Param Count:", self.parameterCount)
        print("  Index Address:", self.indexDataAddress)
        print("  Index Size:", self.indexDataSize)

    def write(self, fileW):
        fileW.wUInt(self.parameterAddress)
        fileW.wUInt(self.parameterCount)
        fileW.wUInt(self.indexDataAddress)
        fileW.wUInt(self.indexDataSize)

def distinctPolys(polys):
    """Takes a list of PolyVerts and returns a distinct list"""
    distinct = list()
    oIDtodID = [0] * len(polys)
    
    for IDo, vo in enumerate(polys):
        found = None
        for IDd, vd in enumerate(distinct):
            if vo == vd:
                found = IDd
                break
        if found is None:
            distinct.append(vo)
            oIDtodID[IDo] = len(distinct) - 1
        else:
            oIDtodID[IDo] = found

    return distinct, oIDtodID

def write(fileW,
          mesh,
          exportMatrix,
          materials,
          labels: dict):

    debug(" Writing GC:", mesh.name, "\n")

    # determining which data should be written
    vertexType = mesh.saSettings.sa2ExportType
    if vertexType == 'NRMW':
        vertexType = 'NRMVC'

    writeNRM = vertexType == 'NRMVC' or vertexType == 'NRM'
    writeVC = (vertexType == 'NRMVC' or vertexType == 'VC') and len(mesh.vertex_colors) > 0
    writeUV = len(mesh.uv_layers) > 0

    posData = list()
    nrmData = list()
    vcData = list()
    uvData = list()

    # gettings all of the data to be written
    # getting position data
    posIDs = [0] * len(mesh.vertices)
    for i, v in enumerate(mesh.vertices):
        found = None
        pos = Vector3(exportMatrix @ v.co)
        for j, p in enumerate(posData):
            if p == pos:
                found = j
                break
        if found is None:
            posData.append(pos)
            posIDs[i] = len(posData) - 1
        else:
            posIDs[i] = found

    # getting normal data
    if writeNRM:
        nrmIDs = [0] * len(mesh.vertices)
        for i, v in enumerate(mesh.vertices):
            found = None
            nrm = Vector3(exportMatrix @ v.normal)
            for j, n in enumerate(nrmData):
                if n == nrm:
                    found = j
                    break
            if found is None:
                nrmData.append(nrm)
                nrmIDs[i] = len(nrmData) - 1
            else:
                nrmIDs[i] = found

    # getting vertex color data
    if writeVC:
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

    # getting uv data
    if writeUV:
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


    # assembling poly data
    tris = list()
    for m in mesh.materials:
        tris.append([])
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
    
    strips = list() # material specific -> strip -> polygon
    Stripf = strippifier.Strippifier()

    for l in tris:
        if len(l) == 0:
            strips.append(None)
            continue
        distinct, indices = distinctPolys(l)

        stripIndices = Stripf.Strippify(indices, doSwaps=False, concat=False)

        polyStrips = [None] * len(stripIndices)

        for i, strip in enumerate(stripIndices):
            tStrip = [None] * len(strip)
            for j, index in enumerate(strip):
                tStrip[j] = distinct[index]
            polyStrips[i] = tStrip
        
        strips.append(polyStrips)

    # data ready to write!

    # === WRITING TO THE FILE === #

    # writing vertex data

    vAttribs = list()

    # position data
    vAttribs.append( vertexAttrib(enums.VertexAttribute.Position, 0, enums.ComponentCount.Position_XYZ, enums.DataType.Float32, fileW.tell(), len(posData) ) )
    for pos in posData:
        pos.write(fileW)
    
    # normal data
    if writeNRM:
        vAttribs.append( vertexAttrib(enums.VertexAttribute.Normal, 0, enums.ComponentCount.Normal_XYZ, enums.DataType.Float32, fileW.tell(), len(nrmData) ) )
        for nrm in nrmData:
            nrm.write(fileW)   
    
    # color data
    if writeVC:
        vAttribs.append( vertexAttrib(enums.VertexAttribute.Color0, 0, enums.ComponentCount.Color_RGBA, enums.DataType.RGBA8, fileW.tell(), len(vcData) ) )
        for vc in vcData:
            vc.write(fileW)

    # uv data
    if writeUV:
        vAttribs.append( vertexAttrib(enums.VertexAttribute.Tex0, 0, enums.ComponentCount.TexCoord_ST, enums.DataType.Signed16, fileW.tell(), len(uvData) ) )
        for uv in uvData:
            uv.write(fileW)

    # attrib end marker
    vAttribs.append( vertexAttrib(enums.VertexAttribute.Null, 0, enums.ComponentCount.Position_XY, enums.DataType.Unsigned8, 0, 0) )

    # writing vertex properties
    vAttribAddress = fileW.tell()
    for v in vAttribs:
        v.write(fileW)
    
    if DO:
        for v in vAttribs:
            v.debug()
    
    # writing geometry

    indexAttributes = enums.IndexAttributeFlags.HasPosition
    if len(posData) > 255:
        indexAttributes |= enums.IndexAttributeFlags.Position16BitIndex
    if writeNRM:
        indexAttributes |= enums.IndexAttributeFlags.HasNormal
        if len(nrmData) > 255:
            indexAttributes |= enums.IndexAttributeFlags.Normal16BitIndex
    if writeVC:
        indexAttributes |= enums.IndexAttributeFlags.HasColor
        if len(vcData) > 255:
            indexAttributes |= enums.IndexAttributeFlags.Color16BitIndex
    if writeUV:
        indexAttributes |= enums.IndexAttributeFlags.HasUV
        if len(uvData) > 255:
            indexAttributes |= enums.IndexAttributeFlags.UV16BitIndex

    # writing opaque geometry first
    opaqueProps = list()
    transparentProps = list()
    for i, s in enumerate(strips):
        if s is None:
            continue
        mat = None
        for m in materials:
            if m.name == mesh.materials[i].name:
                mat = m
        if mat is None:
            debug("  no material found")

        mp = PolyVert.writeData(fileW, s, indexAttributes, mat)

        if mat is not None and mat.saSettings.b_useAlpha:
            transparentProps.append(mp)
        else:
            opaqueProps.append(mp)

    opaqueAddress = fileW.tell()

    for m in opaqueProps:
        m.write(fileW)
        if DO:
            m.debug()
    
    transparentAddress = fileW.tell()

    for m in transparentProps:
        m.write(fileW)
        if DO:
            m.debug()

    # gc info
    labels["gc_" + mesh.name] = fileW.tell()

    fileW.wUInt(vAttribAddress) # vertex address
    fileW.wUInt(0) # gap
    fileW.wUInt(opaqueAddress)
    fileW.wUInt(transparentAddress)
    fileW.wUShort(len(opaqueProps))
    fileW.wUShort(len(transparentProps))

    bounds = BoundingBox(mesh.vertices)
    bounds.boundCenter = exportMatrix @ bounds.boundCenter

    bounds.write(fileW)

