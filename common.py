import bpy
import mathutils

import math
import copy
from typing import List

from . import fileWriter, enums

DO = False # Debug Out

def center(p1: float, p2:float) -> float:
    """Returns the mid point between two numbers"""
    return (p1 + p2) / 2.0

def hex4(number: int) -> str:
    return '{:08x}'.format(number)

def RadToBAMS(v: float) -> int:
    return round((math.degrees(v) / 360.0) * 0xFFFF)

def BAMSToRad(v: float) -> int:
    return v / (65536 / 360.0)

class ColorARGB:
    """4 Channel Color (ARGB)

    takes values from 0.0 - 1.0 as input and converts them to 0 - 255
    """

    a: int
    r: int
    g: int
    b: int

    def __init__(self, c = (1,1,1,1)):
        self.a = round(c[3] * 255)
        self.r = round(c[0] * 255)
        self.g = round(c[1] * 255)
        self.b = round(c[2] * 255)

    def writeRGBA(self, fileW):
        """writes data to file"""
        fileW.wByte(self.a)        
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)

    def writeARGB(self, fileW):
        """writes data to file"""
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)
        fileW.wByte(self.a)

    def __eq__(self, other):
        return self.a == other.a and self.r == other.r and self.g == other.g and self.b == other.b

    def __str__(self):
        return "(" + str(self.a) + ", " + str(self.r) + ", " + str(self.g) + ", " + str(self.b) + ")"

class UV:
    """A single texture coordinate

    Converts from 0.0 - 1.0 range to 0 - 255 range """

    x: int
    y: int

    def __init__(self, uv = (0.0, 0.0)):
        self.x = round(uv[0] * 256)
        self.y = round((1-uv[1]) * 256)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def write(self, fileW: fileWriter.FileWriter):
        """Writes data to file"""
        fileW.wShort(self.x)
        fileW.wShort(self.y)

class Vector3(mathutils.Vector):
    """Point in 3D Space"""

    def length(self):
        """returns length of the vector"""
        return (self.x**2 + self.y**2 + self.z**2)**(0.5)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wFloat(self.x)
        fileW.wFloat(self.y)
        fileW.wFloat(self.z)

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

class BAMSRotation(mathutils.Vector):
    """XYZ Rotation used for the adventure games"""

    def __init__(self, val):
        self.x = RadToBAMS(self.x)
        self.y = RadToBAMS(self.y)
        self.z = RadToBAMS(self.z)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wInt(round(self.x))
        fileW.wInt(round(self.y))
        fileW.wInt(round(self.z))

    def __str__(self):
        return "(" + '{:04x}'.format(round(self.x)) + ", " + '{:04x}'.format(round(self.y)) + ", " + '{:04x}'.format(round(self.z)) + ")"

class BoundingBox:
    """Used to calculate the bounding sphere which the game uses"""

    boundCenter: Vector3
    radius: float

    def __init__(self, vertices):
        """Creates a bounding sphere from a set of vertices"""

        if vertices == None:
            self.radius = 0
            self.boundCenter = Vector3((0,0,0))
            return

        x = 0
        xn = 0
        y = 0
        yn = 0
        z = 0
        zn = 0

        for v in vertices:
            if x < v.co.x:
                x = v.co.x
            elif xn > v.co.x:
                xn = v.co.x

            if y < v.co.y:
                y = v.co.y
            elif yn > v.co.y:
                yn = v.co.y

            if z < v.co.z:
                z = v.co.z
            elif zn > v.co.z:
                zn = v.co.z
        
        cx = center(x,xn)
        cy = center(y,yn)
        cz = center(z,zn)

        distance = 0
        for v in vertices:
            tDist = Vector3((cx - v.co.x,  cy - v.co.y, cz - v.co.z)).length()
            if tDist > distance:
                distance = tDist

        self.boundCenter = Vector3((cx, cy, cz))
        self.radius = distance
    
    def adjust(self, matrix: mathutils.Matrix):
        self.boundCenter = matrix @ self.boundCenter
        self.radius *= matrix.to_scale()[0]

    def write(self, fileW):
        self.boundCenter.write(fileW)
        fileW.wFloat(self.radius)

class ModelData:
    """A class that holds all necessary data to export an Object/COL"""

    name: str
    fmt: str

    origObject: bpy.types.Object # used for exporting the meshes in correct formats

    children: list
    child = None #: ModelData
    sibling = None #: ModelData
    parent = None #: ModelData
    hierarchyDepth: int

    position: Vector3
    rotation: BAMSRotation
    scale: Vector3
    bounds: BoundingBox

    saProps: dict

    unknown1: int # sa1 COL
    unknown2: int # both COL
    unknown3: int # both COL

    meshPtr: int# set after writing meshes
    objectPtr: int# set after writing model address

    def __init__(self, 
             bObject: bpy.types.Object,
             parent, #: ModelData,
             hierarchyDepth: int,
             name: str,
             global_matrix: mathutils.Matrix, 
             fmt: str = '',
             collision: bool = False, 
             visible: bool = False ):

        self.name = name
        self.hierarchyDepth = hierarchyDepth
        if bObject.type == 'MESH':
            self.fmt = fmt
            self.origObject = bObject

            self.bounds = BoundingBox(bObject.data.vertices)
            self.bounds.boundCenter = Vector3(global_matrix @ (self.bounds.boundCenter + bObject.location))
            self.bounds.radius *= global_matrix.to_scale()[0]

            self.saProps = bObject.saSettings.toDictionary()
            self.saProps["isCollision"] = collision
            self.saProps["isVisible"] = visible
        else:
            self.origObject = None
            self.bounds = BoundingBox(None)
            self.saProps = None

        self.children = list()
        self.parent = parent
        if parent is not None:
            self.parent.children.append(self)

        # settings space data
        obj_mat: mathutils.Matrix = global_matrix @ bObject.matrix_world
        rot: mathutils.Vector = bObject.matrix_world.to_euler('XZY')

        self.position = Vector3(obj_mat.to_translation())
        self.rotation = BAMSRotation( global_matrix @ mathutils.Vector((rot.x, rot.y, rot.z)) )
        self.scale = Vector3(obj_mat.to_scale())

        # settings the unknowns
        self.unknown1 = 0
        self.unknown2 = 0
        self.unknown3 = 0

    def updateMeshPointer(objList: list, labels: dict):
        """Updates the mesh pointer of a ModelData list utilizing the labels"""
        for o in objList:
            if o.origObject is not None:
                    o.meshPtr = labels[o.fmt + "_" + o.origObject.data.name]
            else:
                o.meshPtr = 0

    def getObjectFlags(self) -> enums.ObjectFlags:
        """Calculates the Objectflags"""
        from .enums import ObjectFlags
        flags = ObjectFlags.null
        flags |= ObjectFlags.NoAnimate # default
        flags |= ObjectFlags.NoMorph # default

        if self.position == Vector3((0,0,0)):
            flags |= ObjectFlags.NoPosition
        if self.rotation == BAMSRotation((0,0,0)):
            flags |= ObjectFlags.NoRotate
        if self.scale == Vector3((0,0,0)):
            flags |= ObjectFlags.NoScale
        if self.meshPtr == 0:
            flags |= ObjectFlags.NoDisplay
        if len(self.children) == 0:
            flags |= ObjectFlags.NoChildren

        return flags

    def getSA1SurfaceFlags(self) -> enums.SA1SurfaceFlags:
        """Calculates SA1 COL flags"""
        from .enums import SA1SurfaceFlags
        flags = SA1SurfaceFlags.null
        if self.saProps is None:
            return flags
        p = self.saProps

        if p["isCollision"]:
            if p["solid"]:
                flags |= SA1SurfaceFlags.Solid
            if p["water"]:
                flags |= SA1SurfaceFlags.Water
            if p["noFriction"]:
                flags |= SA1SurfaceFlags.NoFriction
            if p["noAcceleration"]:
                flags |= SA1SurfaceFlags.NoAcceleration
            if p["cannotLand"]:
                flags |= SA1SurfaceFlags.CannotLand
            if p["increasedAcceleration"]:
                flags |= SA1SurfaceFlags.IncreasedAcceleration
            if p["diggable"]:
                flags |= SA1SurfaceFlags.Diggable
            if p["unclimbable"]:
                flags |= SA1SurfaceFlags.Unclimbable
            if p["hurt"]:
                flags |= SA1SurfaceFlags.Hurt
        if p["isVisible"]:
            flags |= SA1SurfaceFlags.Visible
            if p["footprints"]:
                flags |= SA1SurfaceFlags.Footprints
        
        return flags

    def getSA2SurfaceFlags(self) -> enums.SA2SurfaceFlags:
        """Calculates SA1 COL flags"""
        from .enums import SA2SurfaceFlags
        flags = SA2SurfaceFlags.null
        if self.saProps is None:
            return flags
        p = self.saProps 

        if p["isCollision"]:
            if p["solid"]:
                flags |= SA2SurfaceFlags.Solid
            if p["water"]:
                flags |= SA2SurfaceFlags.Water
            if p["standOnSlope"]:
                flags |= SA2SurfaceFlags.StandOnSlope
            if p["diggable"]:
                flags |= SA2SurfaceFlags.Diggable
            if p["unclimbable"]:
                flags |= SA2SurfaceFlags.Unclimbable
            if p["hurt"]:
                flags |= SA2SurfaceFlags.Hurt
            if p["cannotLand"]:
                flags |= SA2SurfaceFlags.CannotLand
            if p["water2"]:
                flags |= SA2SurfaceFlags.Water2
            if p["unknown24"]:
                flags |= SA2SurfaceFlags.Unknown24
            if p["unknown29"]:
                flags |= SA2SurfaceFlags.Unknown29
            if p["unknown30"]:
                flags |= SA2SurfaceFlags.Unknown30  
        if p["isVisible"]:
            flags |= SA2SurfaceFlags.Visible
            if p["noShadows"]:
                flags |= SA2SurfaceFlags.NoShadows
            if p["noFog"]:
                flags |= SA2SurfaceFlags.noFog
        
        return flags

    def writeObjectList(objects: list, fileW: fileWriter.FileWriter, labels: dict, lvl: bool = False):
        for o in reversed(objects):
            o.writeObject(fileW, labels, lvl)
        return objects[0].objectPtr

    def writeObject(self, fileW: fileWriter.FileWriter, labels: dict, lvl: bool = False):
        """Writes object data"""
        labels["o_" + self.name] = fileW.tell()
        self.objectPtr = fileW.tell()

        fileW.wUInt(self.getObjectFlags().value)
        fileW.wUInt(self.meshPtr)
        self.position.write(fileW)
        self.rotation.write(fileW)
        self.scale.write(fileW)
        fileW.wUInt(0 if self.child is None or lvl else self.child.objectPtr)
        fileW.wUInt(0 if self.sibling is None or lvl else self.sibling.objectPtr)

    def writeCOL(self, fileW: fileWriter.FileWriter, labels: dict, SA2: bool):
        """writes COL data"""
        # a COL always needs a mesh
        if self.meshPtr == 0:
            return

        labels["col_" + self.name] = fileW.tell()

        if SA2:
            self.bounds.write(fileW)
            fileW.wUInt(self.objectPtr)
            fileW.wUInt(self.unknown2)
            fileW.wUInt(self.unknown3)
            fileW.wUInt(self.getSA2SurfaceFlags().value | int("0x" + self.saProps["userFlags"], 0))
        else:
            self.bounds.write(fileW)
            fileW.wUInt(self.unknown1)
            fileW.wUInt(self.unknown2)
            fileW.wUInt(self.objectPtr)
            fileW.wUInt(self.unknown3)
            fileW.wUInt(self.getSA1SurfaceFlags().value | int("0x" + self.saProps["userFlags"], 0))

def convertObjectData(context: bpy.types.Context,
                      use_selection: bool,
                      apply_modifs: bool,
                      export_matrix: mathutils.Matrix,
                      fmt: str,
                      lvl: bool):
    
    global DO

    # gettings the objects to export
    if use_selection:
        objects = context.selected_objects
    else:
        objects = context.scene.objects.values()

    if len(objects) == 0:
        print("No objects found")
        if fmt == 'SA1' or not lvl:
            return None, None, None, None
        else:
            return None, None, None, None, None, None

    # getting the objects without parents
    noParents = list()
    for o in objects:
        if o.parent == None or not (o.parent in objects):
            noParents.append(o)
    
    # correct object order
    # sort top level objects first
    noParents.sort(key=lambda x: x.name)

    # sort children recursively and convert them to ModelData objects
    modelData = list()
    lastSibling = None
    for o in noParents:
        current = sortChildren(o, objects, None, 0, export_matrix, fmt, lvl, modelData)
        if lastSibling is not None:
            lastSibling.sibling = current
        lastSibling = current

    objects = modelData

    # get meshes
    depsgraph = context.evaluated_depsgraph_get()
    if not lvl or lvl and fmt == 'SA1':

        mObjects = list() # objects with a mesh
        for o in objects:
            if o.origObject is not None:
                mObjects.append(o)

        meshes, materials = getMeshesFromObjects(mObjects, depsgraph, apply_modifs)

        if DO:
            print(" == Exporting ==")
            print("  Materials:", len(materials))
            print("  Meshes:", len(meshes))
            print("  Objects:", len(objects))
            print("  - - - - - -\n")
        
        return objects, meshes, materials, mObjects

    else: # only occurs when format is sa2lvl or sa2blvl
        cObjects = list() # collision objects
        vObjects = list() # visual objects

        for o in objects:
            if o.origObject is not None:
                if o.saProps["isCollision"]:
                    cObjects.append(o)
                else:
                    vObjects.append(o)

        cMeshes, dontUse = getMeshesFromObjects(cObjects, depsgraph, apply_modifs)
        vMeshes, materials = getMeshesFromObjects(vObjects, depsgraph, apply_modifs)
    
        if DO:
            print(" == Exporting ==")
            print("  Materials:", len(materials))
            print("  Visual Meshes:", len(vMeshes))
            print("  Collision Meshes:", len(cMeshes))
            print("  Objects:", len(objects))
            print("  - - - - - -\n")

        return objects, cMeshes, vMeshes, materials, cObjects, vObjects

def sortChildren(cObject: bpy.types.Object, 
                objects: List[bpy.types.Object],
                parent: ModelData, 
                hierarchyDepth: int,
                export_matrix: mathutils.Matrix,
                fmt: str,
                lvl: bool,
                result: List[ModelData]) -> ModelData:
    """Converts objects to ModelData and writes them in the correct order into the result list"""

    lastSibling = None
    if cObject.type == 'MESH':
        if lvl and fmt != 'SA1' and cObject.saSettings.isCollision and cObject.saSettings.isVisible:
            model = ModelData(cObject, parent, hierarchyDepth, "vsl_" + cObject.name, export_matrix, 'cnk' if fmt == "SA2" else 'gc', False, True)
            # collision
            lastSibling = ModelData(cObject, model, hierarchyDepth, "cls_" + cObject.name, export_matrix, 'bsc', True, False)
        else:
            if fmt == 'SA1' or cObject.saSettings.isCollision and lvl:
                meshTag = 'bsc' # BASIC is used by all sa1 models and sa2 collisions
            elif fmt == 'SA2':
                meshTag = 'cnk' # sa2 format is CHUNK
            else: # SA2B
                meshTag = 'gc' # sa2b format is GC

            visible = True if not cObject.saSettings.isCollision else cObject.saSettings.isVisible
                
            model = ModelData(cObject, parent, hierarchyDepth, cObject.name, export_matrix, meshTag, cObject.saSettings.isCollision, visible)
    else:
        # everything that is not a mesh should be written as an empty
        model = ModelData(cObject, parent, hierarchyDepth, cObject.name, export_matrix, fmt, False, False)
    
    result.append(model)

    for c in cObject.children:
        if c in objects:
            child = sortChildren(c, objects, model, hierarchyDepth + 1, export_matrix, fmt, lvl, result)
            if lastSibling is not None:
                lastSibling.sibling = child
            lastSibling = child

    # update sibling relationship
    if len(model.children) > 0:
        model.child = model.children[0]
    
    return model

def getMeshesFromObjects(objects: List[ModelData], depsgraph: bpy.types.Depsgraph, apply_modifs: bool):
    """checking which meshes are in the objects at all"""
    tMeshes = list()
    for o in objects:
        tMeshes.append(o.origObject.data)

    #checking whether there are any objects that share a mesh
    collectedMOMeshes = list()
    mObjects = list()
    meshesToConvert = list()
    for o in objects:
        if tMeshes.count(o.origObject.data) > 1:
            if collectedMOMeshes.count(o.origObject.data) == 0:
                mObjects.append(o)
                meshesToConvert.append(o)
                collectedMOMeshes.append(o.origObject.data)
        else:
            meshesToConvert.append(o)

    outMeshes = list()
    materials = list()
    for o in meshesToConvert:
        if len(o.origObject.data.vertices) == 0:
            continue

        newMesh, mats = convertMesh(o.origObject, depsgraph, False if o in mObjects else apply_modifs)
        outMeshes.append(newMesh)
        if not (o.saProps["isCollision"] and not o.saProps["isVisible"]):
            for m in mats:
                if m not in materials:
                    materials.append(m)

    return outMeshes, materials

def convertMesh(obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph, apply_modifs: bool):
    """Applies modifiers (or not), triangulates the mesh and returns materials"""
    ob_for_convert = obj.evaluated_get(depsgraph) if apply_modifs else obj.original
    me = ob_for_convert.to_mesh()

    trianglulateMesh(me)
    return me, obj.data.materials

def trianglulateMesh(me: bpy.types.Mesh) -> bpy.types.Mesh:
    """Transforms a mesh into a mesh only consisting of triangles, so that it can be stripped"""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()

def writeMethaData(fileW: fileWriter.FileWriter,
                   labels: dict,
                   scene: bpy.types.Scene,
                   ):
    """Writes the meta data of the file"""

    # === LABELS ===
    fileW.wUInt(enums.Chunktypes.Label.value)
    newLabels = dict()
    sizeLoc = fileW.tell()
    fileW.wUInt(0)

    global DO
    if DO:
        print(" == Labels ==")
        for k,v in labels.items():
            print("  ", k + ":", '{:08x}'.format(v))
        print("")

    #placeholders
    for l in labels:
        fileW.wUInt(0)
        fileW.wUInt(0)

    fileW.wLong(-1)

    # writing the strings
    for key, val in labels.items():
        newLabels[val] = fileW.tell() - sizeLoc - 4
        strKey = str(key)
        strKey = strKey.replace('.', '_')
        strKey = strKey.replace(' ', '_')
        fileW.wString(strKey)
        fileW.align(4)

    # returning to the dictionary start
    size = fileW.tell() - sizeLoc - 4
    fileW.seek(sizeLoc, 0)
    fileW.wUInt(size)

    # writing the dictionary
    for key, val in newLabels.items():
        fileW.wUInt(key)
        fileW.wUInt(val)

    #back to the end
    fileW.seek(0,2)

    #getting the file info
    settings = scene.saSettings

    # === AUTHOR ===
    if not (settings.author == ""):
        fileW.wUInt(enums.Chunktypes.Author.value)
        sizeLoc = fileW.tell()
        fileW.wUInt(0)
        fileW.wString(settings.author)
        fileW.align(4)
        size = fileW.tell() - sizeLoc - 4
        fileW.seek(sizeLoc, 0)
        fileW.wUInt(size)
        fileW.seek(0, 2)

        if DO:
            print(" Author:", settings.author)

    # === DESCRIPTION ===
    if not (settings.description == ""):
        fileW.wUInt(enums.Chunktypes.Description.value)
        sizeLoc = fileW.tell()
        fileW.wUInt(0)
        fileW.wString(settings.description)
        fileW.align(4)
        size = fileW.tell() - sizeLoc - 4
        fileW.seek(sizeLoc, 0)
        fileW.wUInt(size)
        fileW.seek(0, 2)

        if DO:
            print(" Description:", settings.description)

    fileW.wUInt(enums.Chunktypes.End.value)
    fileW.wUInt(0)
    