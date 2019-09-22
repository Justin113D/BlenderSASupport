import bpy
import math
import mathutils
from . import fileWriter, enums, strippifier

DO = False

def debug(*string):
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

    def write(self, fileW, noAlpha = False):
        """writes data to file"""
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)
        if not noAlpha:
            fileW.wByte(self.a)

class Vertex:

    origIndex = 0
    index = 0
    co = Vector3()
    nrm = Vector3()
    col = ColorARGB()
    ninjaFlags = 0

    def __init__(self, origIndex, index, pos, nrm, col = (1,1,1,1), ninjaFlags = 0):
        self.index = index
        self.origIndex = origIndex
        self.co = Vector3(pos)
        self.nrm = Vector3(nrm)
        if type(col) is ColorARGB:
            self.col = col
        else:
            self.col = ColorARGB(col)
        self.ninjaFlags = ninjaFlags

    def writeVC(self, fileW):
        self.co.write(fileW)
        self.col.write(fileW)
        
    def writeNRM(self, fileW):
        self.co.write(fileW)
        self.nrm.write(fileW)

    def writeNRMVC(self, fileW):
        self.co.write(fileW)
        self.nrm.write(fileW)
        self.col.write(fileW)

    def writeNRMW(self, fileW):
        print("nope")

class PolyVert:

    #vertexID = None
    # uv
    uv = (0.0, 0.0)

    def __init__(self, vertexID, uv = (0.0,0.0)):
        self.vertexID = vertexID
        self.uv = uv

    def __eq__(self, other):
        return self.vertexID == other.vertexID and self.uv == other.uv

    def updateUV(self, HD):
        if HD:
            self.uv = (round(self.uv[0] * 1023), round((1-self.uv[1]) * 1023))
        else:
            self.uv = (round(self.uv[0] * 255), round((1-self.uv[1]) * 255))

    def write(self, fileW):
        fileW.wUShort(self.vertexID)

    def writeUV(self, fileW):
        fileW.wUShort(self.vertexID)
        fileW.wShort(self.uv[0])
        fileW.wShort(self.uv[1])

class BoundingBox:
    """Used to calculate the bounding sphere which the game uses"""

    boundCenter = Vector3


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

def write(fileW: fileWriter.FileWriter,
          mesh: bpy.types.Mesh,
          exportMatrix,
          materials,
          labels: dict
          ):

    debug("Writing CHUNK mesh:", mesh.name) 

    #getting vertex data

    # weights arent supported rn
    vertexType = mesh.saSettings.sa2ExportType
    if vertexType == 'NRMW':
        vertexType = 'NRMVC'
        debug("Weights not supported as of now")

    # if type includes colors, but the mesh doesnt contain any colors, write normals only
    if (vertexType == 'NRMVC' or vertexType == 'VC') and len(mesh.vertex_colors) == 0:
        debug("Mesh doesnt contain any colors, writing normals only...")
        vertexType = 'NRM'

    writeUVs = len(mesh.uv_layers) > 0
    HDUV = True

    # creating 2d vertex array
    vertices = list()
    for v in mesh.vertices:
        vertices.append(list())

    polyVerts = list()

    # getting the vertices
    if vertexType == 'NRMVC' or vertexType == 'VC':
        # creating a vertex for each loop color
        for l in mesh.loops:
            vert = mesh.vertices[l.vertex_index]
            col = ColorARGB(mesh.vertex_colors[0].data[l.index].color)

            # only create the vertex if there isnt one with the same color already
            exists = False
            foundV = None
            for v in vertices[l.vertex_index]:
                if v.col == col:
                    exists = True
                    foundV = v
                    break

            if not exists:
                pos = exportMatrix @ vert.co
                nrm = exportMatrix @ vert.normal
                foundV = Vertex(l.vertex_index, 0, pos, nrm, col)
                vertices[l.vertex_index].append(foundV)

            if writeUVs:
                uv = mesh.uv_layers[0].data[l.index].uv
                polyVert = PolyVert(foundV, uv)
                if abs(uv[0]) > 32 or abs(uv[1]) > 32:
                    HDUV = False

            else:
                polyVert = PolyVert(foundV)

            polyVerts.append(polyVert)

        # correcting indices
        i = 0
        for v in vertices:
            for vt in v:
                vt.index = i
                i += 1

        # now that the vertices have their index, we can exchange the vertex in the polyverts with the vertex' index
        if writeUVs:
            for p in polyVerts:
                p.vertexID = p.vertexID.index
                # update the uvs too
                p.updateUV(HDUV)
        else:
            for p in polyVerts:
                p.vertexID = p.vertexID.index
    else:
        for i, v in enumerate(mesh.vertices):
            pos = exportMatrix @ v.co
            nrm = exportMatrix @ v.normal
            vertices[i] = [Vertex(i, i, pos, nrm)]
        for l in mesh.loops:
            if writeUVs:
                uv = mesh.uv_layers[0].data[l.index].uv
                polyVert = PolyVert(l.vertex_index, uv)
                if abs(uv[0]) > 32 or abs(uv[1]) > 32:
                    HDUV = False
            else:
                polyVert = PolyVert(l.vertex_index)

            polyVerts.append(polyVert)

        # updating the uv's
        if writeUVs:
            for p in polyVerts:
                p.updateUV(HDUV)

    # getting the distinct polygons
    distinctPolys = list()
    oIDtodID = [0] * len(polyVerts)
    
    for IDo, vo in enumerate(polyVerts):
        found = -1
        for IDd, vd in enumerate(distinctPolys):
            if vo == vd:
                found = IDd
                break
        if found == -1:
            distinctPolys.append(vo)
            oIDtodID[IDo] = len(distinctPolys) - 1
        else:
            oIDtodID[IDo] = found
    
    #setting up the triangle lists
    tris = list()
    for m in mesh.materials:
        tris.append(list())

    for p in mesh.polygons:
        for l in p.loop_indices:
            tris[p.material_index].append(oIDtodID[l])

    strips = list() # material specific -> strip -> polygon

    Stripf = strippifier.Strippifier()

    for l in tris:
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

    # now everything is ready to be written

    # === WRITING TO THE FILE === #

    # writing the vertex chunks:
    if vertexType == 'VC':
        vertexType = enums.ChunkType.Vertex_VertexDiffuse8
        vertexSize = 4
    elif vertexType == 'NRM':
        vertexType = enums.ChunkType.Vertex_VertexNormal
        vertexSize = 6
    elif vertexType == 'NRMVC':
        vertexType = enums.ChunkType.Vertex_VertexNormalDiffuse8
        vertexSize = 7
    else: # 'NRMW'
        vertexType = enums.ChunkType.Vertex_VertexNormalNinjaFlags
        vertexSize = 7

    chunkFlags = enums.WeightStatus.Start # this is generally todo
    vertexAddress = fileW.tell()
    vertexCount = vertices[-1][-1].index + 1
    size = (vertexSize * vertexCount) + 1
    indexOffset = 0

    # first header
    fileW.wByte(vertexType.value) # chunktype
    fileW.wByte(chunkFlags.value) # flags
    fileW.wUShort(size) # amount of 4-byte sets after the first header
    # second header
    fileW.wUShort(indexOffset) # index offset. doesnt matter for non weighted models
    fileW.wUShort(vertexCount) # vertex count

    if DO:
        print(" Vertices:")
        print("   Chunktype:", vertexType)
        print("   Flags:", chunkFlags)
        print("   Size:", size)
        print("   Index Offset:", indexOffset)
        print("   Vertex Count:", vertexCount)

    #writing the vertices
    if vertexType == enums.ChunkType.Vertex_VertexDiffuse8:
        for v in vertices:
            for vt in v:
                vt.writeVC(fileW)
    elif vertexType == enums.ChunkType.Vertex_VertexNormal:
        for v in vertices:
            for vt in v:
                vt.writeNRM(fileW)
    elif vertexType == enums.ChunkType.Vertex_VertexNormalDiffuse8:
        for v in vertices:
            for vt in v:
                vt.writeNRMVC(fileW)
    else: # 'NRMW'
        for v in vertices:
            for vt in v:
                vt.writeNRMW(fileW)
    #marking the end of the vertex chunks
    fileW.wULong(enums.ChunkType.End.value)

    polyAddress = fileW.tell()

    #Writing the poly chunks
    from .enums import ChunkType
    for mID, ms in enumerate(strips):
        if ms is None:
            continue
        #writing material chunks
        material = None
        try:
            for m in materials:
                if m.name == mesh.materials[mID].name:
                    material = m
                    break
        except ValueError:
            debug(" material", mesh.materials[i].name, "not found")

        stripFlags = enums.StripFlags.null

        if material is not None:
            matProps = material.saSettings

            #writing the colors
            fileW.wByte(ChunkType.Material_DiffuseAmbientSpecular.value)
            fileW.wByte(0) # empty flags
            fileW.wUShort(6) # size
            ColorARGB(matProps.b_Diffuse).write(fileW) # diffuse color
            ColorARGB(matProps.b_Ambient).write(fileW) # ambient color
            ColorARGB(matProps.b_Specular).write(fileW, noAlpha=True) # specular color
            fileW.wByte(round(matProps.b_Exponent * 255)) # specularity

            # collecting texture info
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

            texParams = min( matProps.b_TextureID, 0x1FFF)

            if matProps.b_use_Anisotropy:
                texParams |= 0x2000

            filtering = enums.TextureFiltering.Point

            if matProps.b_texFilter == 'BILINEAR':
                filtering = enums.TextureFiltering.Bilinear
            elif matProps.b_texFilter == 'TRILINEAR':
                filtering = enums.TextureFiltering.Trilinear
            elif matProps.b_texFilter == 'BLEND':
                filtering = enums.TextureFiltering.Blend

            filtering = filtering.value << 14
            texParams |= filtering
            
            # writing texture info
            fileW.wByte(ChunkType.Tiny_TextureID.value)
            fileW.wByte(textureFlags.value)
            fileW.wUShort(texParams)
              
            # writing alpha
            fileW.wByte(ChunkType.Bits_BlendAlpha.value)
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
            fileW.wByte(alphaflags.value)

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

        else:
            debug("error occured! no material found!")

        # writing strips
        if writeUVs:
            if HDUV:
                stripType = ChunkType.Strip_StripUVH
            else:
                stripType = ChunkType.Strip_StripUVN
        else:
            stripType = ChunkType.Strip_Strip

        size = 1
        for s in ms:
            size += len(s) * (3 if writeUVs else 1) + 1

        stripCount = min(len(ms), 0x3FFF)

        fileW.wByte(stripType.value)
        fileW.wByte(stripFlags.value)
        fileW.wUShort(size)
        fileW.wUShort(stripCount)

        if DO:
            print(" Strip", mID, "data:")
            print("   type:", stripType)
            print("   flags:", stripFlags)
            print("   size:", size)
            print("   stripCount:", stripCount)
            
        #writing the polygons
        for i, s in enumerate(ms):
            fileW.wShort(min(len(s), 0x7FFF)) # strip length
            #debug("   strip", i, "length:", len(s))
            if writeUVs:
                for p in s:
                    p.writeUV(fileW)
            else:
                for p in s:
                    p.write(fileW)

    fileW.wUShort(enums.ChunkType.End.value)

    labels["a_" + mesh.name] = fileW.tell()
    fileW.wUInt(vertexAddress)
    fileW.wUInt(polyAddress)
    
    bounds = BoundingBox(mesh.vertices)
    bounds.boundCenter = exportMatrix @ bounds.boundCenter
    bounds.write(fileW)

    debug(" ---- \n")
