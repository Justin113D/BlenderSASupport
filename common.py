import bpy
import mathutils

import math
import copy
import queue
from typing import List, Dict


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
    return math.radians( v / (0xFFFF / 360.0))

def getDistinctwID(items: list):

    distinct = list()
    IDs = [0] * len(items)

    for i, o in enumerate(items):
        found = None
        for j, d in enumerate(distinct):
            if o == d:
                found = j
                break
        if found is None:
            distinct.append(o)
            IDs[i] = len(distinct) - 1
        else:
            IDs[i] = found

    return distinct, IDs


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

    def fromRGBA(value: int):
        col = ColorARGB()
        
        col.r = (value >> 24) & 0xFF
        col.g = (value >> 16) & 0xFF
        col.b = (value >> 8) & 0xFF
        col.a = value & 0xFF
        return col

    def writeRGBA(self, fileW):
        """writes data to file"""
        fileW.wByte(self.a)        
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)

    def fromARGB(value: int):
        col = ColorARGB()
        col.a = (value >> 24) & 0xFF
        col.r = (value >> 16) & 0xFF
        col.g = (value >> 8) & 0xFF
        col.b = value & 0xFF
        return col

    def writeARGB(self, fileW):
        """writes data to file"""
        fileW.wByte(self.b)
        fileW.wByte(self.g)
        fileW.wByte(self.r)
        fileW.wByte(self.a)

    def toBlenderTuple(self):
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a / 255.0)

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

    def getBlenderUV(self):
        return (self.x / 256.0, 1-(self.y / 256.0))

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
        return "(" + str(BAMSToRad(self.x)) + ", " + str(BAMSToRad(self.y)) + ", " + str(BAMSToRad(self.z)) + ")"
        #return "(" + '{:04x}'.format(round(self.x)) + ", " + '{:04x}'.format(round(self.y)) + ", " + '{:04x}'.format(round(self.z)) + ")"

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
    processedMesh: bpy.types.Mesh # the triangulated mesh

    children: list
    child = None #: ModelData
    sibling = None #: ModelData
    parent = None #: ModelData
    hierarchyDepth: int
    partOfArmature: bool

    worldMatrix: mathutils.Matrix
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
             visible: bool = False):

        self.name = name
        self.hierarchyDepth = hierarchyDepth
        if parent is not None:
            self.partOfArmature = isinstance(parent, Armature) or parent.partOfArmature
        else:
            self.partOfArmature = False
        if bObject is not None and bObject.type == 'MESH':
            self.fmt = fmt

            self.bounds = BoundingBox(bObject.data.vertices)
            self.bounds.boundCenter = Vector3(global_matrix @ (self.bounds.boundCenter + bObject.location))
            self.bounds.radius *= global_matrix.to_scale()[0]

            self.saProps = bObject.saSettings.toDictionary()
            self.saProps["isCollision"] = collision
            self.saProps["isVisible"] = visible
        else:
            self.bounds = BoundingBox(None)
            self.saProps = None

        self.origObject = bObject

        self.worldMatrix = bObject.matrix_world if bObject is not None else mathutils.Matrix.Identity(4)

        self.children = list()
        self.parent = parent
        if parent is not None:
            self.parent.children.append(self)
            matrix = parent.worldMatrix.inverted() @ self.worldMatrix
        else:
            matrix = self.worldMatrix

        # settings space data

        obj_mat: mathutils.Matrix = global_matrix @ matrix
        #print("xyz:", matrix.to_euler('XYZ'))
        
        rot: mathutils.Euler = matrix.to_euler('XZY')
        #print("xzy:", rot)

        rot = global_matrix @ mathutils.Vector((rot.x, rot.y, rot.z))
        #print("applied:", str(rot))

        self.position = Vector3(obj_mat.to_translation())
        self.rotation = BAMSRotation(rot)
        #print("reversed:", BAMSToRad(self.rotation.x), BAMSToRad(self.rotation.y), BAMSToRad(self.rotation.z))

        self.scale = Vector3(obj_mat.to_scale())

        # settings the unknowns
        self.unknown1 = 0
        self.unknown2 = 0
        self.unknown3 = 0

    def updateMeshes(objList: list, meshList: list):
        for o in objList:
            o.processedMesh = None
            if o.origObject is not None and o.origObject.type == 'MESH':
                for m in meshList:
                    if m.name == o.origObject.data.name:
                        o.processedMesh = m

    def updateMeshPointer(objList: list, meshDict: dict):
        """Updates the mesh pointer of a ModelData list utilizing a meshDict"""
        for o in objList:
            if o.processedMesh is not None:
                    o.meshPtr = meshDict[o.processedMesh.name]
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
        name = self.name
        numberCount = 0
        while name[numberCount].isdigit():
            numberCount += 1

        if name[numberCount + 1] == '_':
            name = name[numberCount + 1:]
        else:
            name = name[numberCount:]

        self.objectPtr = fileW.tell()
        labels[self.objectPtr] = name
        
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

        name = self.name
        
        numberCount = 0
        while name[numberCount].isdigit():
            numberCount += 1

        if name[numberCount + 1] == '_':
            name = name[numberCount + 1:]
        else:
            name = name[numberCount:]

        labels[fileW.tell()] = self.name

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


class BoneMesh:

    model: ModelData
    weightIndex: int
    indexBufferOffset: int
    weightStatus: enums.WeightStatus

    # a weightindex of -1 indicates to write the entire mesh
    # and an index of -2 means to write only unweighted vertices

    def __init__(self,
                 model: ModelData,
                 weightIndex: int,
                 indexBufferOffset: int,
                 weightStatus: enums.WeightStatus):
        self.model = model
        self.weightIndex = weightIndex
        self.indexBufferOffset = indexBufferOffset
        self.weightStatus = weightStatus

class Bone:

    name: str
    hierarchyDepth: int

    matrix_world: mathutils.Matrix # in the world
    matrix_local: mathutils.Matrix # relative to parent bone

    weightedMeshes: List[BoneMesh]

    parentBone = None #:Bone
    children: list #: List[Bone]

    child = None
    sibling = None

    position: Vector3
    rotation: BAMSRotation
    scale: Vector3

    meshPtr: int# set after writing meshes
    objectPtr: int# set after writing model address

    def __init__(self,
                 name: str,
                 hierarchyDepth,
                 armatureMatrix: mathutils.Matrix,
                 localMatrix: mathutils.Matrix,
                 exportMatrix: mathutils.Matrix,
                 parentBone):
        self.name = name
        self.hierarchyDepth = hierarchyDepth

        self.matrix_world = armatureMatrix @ localMatrix
        if parentBone is not None:
            self.matrix_local = parentBone.matrix_world.inverted() @ self.matrix_world
            matrix = self.matrix_local
        else: # only the root can cause this
            self.matrix_local = self.matrix_world
            matrix = armatureMatrix

        posMatrix = exportMatrix @ matrix 
        self.position = Vector3(posMatrix.to_translation())
        self.scale = Vector3((1,1,1))

        rot: mathutils.Euler = matrix.to_euler('XZY')
        self.rotation = BAMSRotation( exportMatrix @ mathutils.Vector((rot.x, rot.y, rot.z)) )

        self.parentBone = parentBone
        self.weightedMeshes = list()
        self.children = list()

        if parentBone is not None:
            parentBone.children.append(self)

    def getBones(bBone: bpy.types.Bone,
                parent, #: Bone 
                hierarchyDepth: int,
                export_matrix: mathutils.Matrix,
                armatureMatrix: mathutils.Matrix,
                result: List[ModelData]):

        bone = Bone(bBone.name, hierarchyDepth, armatureMatrix, bBone.matrix_local, export_matrix, parent)
        result.append(bone)
        lastSibling = None

        for b in bBone.children:
            child = Bone.getBones(b, bone, hierarchyDepth + 1, export_matrix, armatureMatrix, result)
            if lastSibling is not None:
                lastSibling.sibling = child
            lastSibling = child

        # update sibling relationship
        if len(bone.children) > 0:
            bone.child = bone.children[0]
        
        return bone

    def writeMesh(self,
                  export_matrix: mathutils.Matrix,
                  materials: List[bpy.types.Material],
                  fileW: fileWriter.FileWriter,
                  labels: dict):
        self.meshPtr = 0  
        if len(self.weightedMeshes) > 0:
            if DO:
                print(self.name, ":")
                for m in self.weightedMeshes:
                    print("  -", m.model.processedMesh.name, m.weightIndex, m.indexBufferOffset, m.weightStatus)

            from . import format_CHUNK
            mesh = format_CHUNK.Attach.fromWeightData(self.name, self.weightedMeshes, self.matrix_world, export_matrix, materials)
            if mesh is not None:
                self.meshPtr = mesh.write(fileW, labels)
          
    def write(self, fileW: fileWriter.FileWriter, labels: dict):
        """Writes bone data in form of object data"""
        name = self.name
        numberCount = 0
        while name[numberCount].isdigit():
            numberCount += 1

        if name[numberCount] == '_':
            name = name[numberCount + 1:]
        else:
            name = name[numberCount:]

        
        self.objectPtr = fileW.tell()
        labels[self.objectPtr] = name

        objFlags = enums.ObjectFlags.NoMorph
        if self.meshPtr == 0:
            objFlags |= enums.ObjectFlags.NoDisplay
        if len(self.children) == 0:
            objFlags |= enums.ObjectFlags.NoChildren

        fileW.wUInt(objFlags.value)
        fileW.wUInt(self.meshPtr)
        self.position.write(fileW)
        self.rotation.write(fileW)
        self.scale.write(fileW)
        fileW.wUInt(0 if self.child is None else self.child.objectPtr)
        fileW.wUInt(0 if self.sibling is None else self.sibling.objectPtr)

class Armature(ModelData):
    
    bones: List[Bone]

    def writeArmature(self,
                      fileW: fileWriter.FileWriter,
                      export_matrix: mathutils.Matrix,
                      materials: List[bpy.types.Material],
                      labels: dict
                    ):
        armature = self.origObject.data
        self.bones: List[Bone] = list()

        # first we need to evaluate all bone data (the fun part)
        # lets start with the root bone. thats basically representing the armature object
        root = Bone(self.name, 0, self.origObject.matrix_world, mathutils.Matrix.Identity(4), export_matrix, None)
        self.bones.append(root)

        # starting with the parentless bones
        lastSibling = None
        for b in armature.bones:
            if b.parent is None:
                bone = Bone.getBones(b, root, 1, export_matrix, self.origObject.matrix_world, self.bones)

                if lastSibling is not None:
                    lastSibling.sibling = bone
                lastSibling = bone

        if len(root.children) > 0:
            root.child = root.children[0]

        if DO:
            print(" == Bone Hierarchy == \n")
            for b in self.bones:
                marker = " "
                for r in range(b.hierarchyDepth):
                    marker += "- "
                if len(marker) > 1:
                    print(marker, b.name)
                else:
                    print("", b.name)
            print(" - - - -\n")

        # now, time to get the mesh data
        # first we need to get all objects that the armature modifies
        objects: List[ModelData] = list()
        objQueue = queue.Queue()

        for o in self.children:
            objQueue.put(o)

        while not objQueue.empty():
            o = objQueue.get()
            objects.append(o)
            for c in o.children:
                objQueue.put(c)
        
        # now we have all objects that get modified by the armature
        # lets get the meshes
        meshes = list()
        for o in objects:
            if o.processedMesh not in meshes:
                meshes.append(o.processedMesh)

        # giving each mesh an index buffer offset
        meshesWOffset = dict()
        currentOffset = 0
        for m in meshes:
            meshesWOffset[m] = currentOffset
            currentOffset += len(m.vertices)

        # ok lemme write some notes down:
        # there are 3 types of objects that the armature modifies:
        # 1. Objects with weights, which are parented to the armature
        # 2. Objects parented to bones (also no weights)        
        # 3. Objects without weights. may be parented to armature or object that is parented to armature


        # determining which meshes get written with weights at all
        weighted = list()
        weightStatus = dict()

        for o in objects:
            # check case 1
            if o.processedMesh is None:
                continue

            case1 = False
            for m in o.origObject.modifiers:
                if isinstance(m, bpy.types.ArmatureModifier):
                    if m.object is self.origObject:
                        # yeah then its case 1, otherwise no
                        case1 = True
                        break
                    
            if case1:
                weighted.append(o)
                weightStatus[o] = None
            elif len(o.origObject.parent_bone) > 0:
                for b in self.bones:
                    if b.name == o.origObject.parent_bone:
                        b.weightedMeshes.append(BoneMesh(o, -1, meshesWOffset[o.processedMesh], enums.WeightStatus.Start))
                        break
            else:
                root.weightedMeshes.append(BoneMesh(o, -1, meshesWOffset[o.processedMesh], enums.WeightStatus.Start))

        # assigning weighted meshes to bones

        for b in self.bones:
            if b is root:
                for w in weighted:
                    mesh = w.processedMesh
                    for v in mesh.vertices:
                        if len(v.groups) == 0:
                            root.weightedMeshes.append(BoneMesh(w, -2, meshesWOffset[mesh], enums.WeightStatus.Start))
                            weightStatus[w] = root
                            break
            else:
                for w in weighted:
                    obj = w.origObject
                    for g in obj.vertex_groups:
                        if g.name == b.name:
                            mesh = w.processedMesh

                            found = False
                            #checking if any vertex even holds a weight for the group
                            groupindex = g.index
                            for v in mesh.vertices:
                                try:
                                    weight = g.weight(v.index)
                                except RuntimeError:
                                    continue
                                found = True
                                break
                                
                            
                            # if the mesh has weights that can be written, then add it to the bone
                            if found:
                                if weightStatus[w] is None:
                                    ws = enums.WeightStatus.Start
                                else:
                                    ws = enums.WeightStatus.Middle
                                b.weightedMeshes.append(BoneMesh(w, groupindex, meshesWOffset[mesh], ws))
                                weightStatus[w] = b

        for o in weightStatus.keys():
            bone: Bone = weightStatus[o]

            for i, m in enumerate(bone.weightedMeshes):
                if m.model == o:
                    if m.weightStatus == enums.WeightStatus.Middle:
                        m.weightStatus = enums.WeightStatus.End

                    elif m.weightStatus == enums.WeightStatus.Start:
                        m.weightIndex = -1
        
        # writing mesh data
        for b in self.bones:
            b.writeMesh(export_matrix, materials, fileW, labels)

        if DO:
            print("\n - - - -")

        # writing object data
        for b in reversed(self.bones):
            b.write(fileW, labels)
        
        return self.bones[0].objectPtr         

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
    modelData: List[ModelData] = list()
    parent = None
    hierarchyDepth = 0
    if not lvl:
        if len(noParents) > 1:
            parent = ModelData(None, None, 0, "root", export_matrix, fmt, False, False)
            modelData.append(parent)
            hierarchyDepth = 1

    lastSibling = None
    for o in noParents:
        current = sortChildren(o, objects, parent, hierarchyDepth, export_matrix, fmt, lvl, modelData)
        if lastSibling is not None:
            lastSibling.sibling = current
        lastSibling = current

    if parent is not None:
        parent.child = parent.children[0]

    objects = modelData

    # get meshes
    depsgraph = context.evaluated_depsgraph_get()
    if not lvl or lvl and fmt == 'SA1':

        mObjects = list() # objects with a mesh
        for o in objects:
            if o.origObject is not None and o.origObject.type == 'MESH':
                mObjects.append(o)

        meshes, materials = getMeshesFromObjects(mObjects, depsgraph, apply_modifs)
        ModelData.updateMeshes(objects, meshes)

        if fmt == 'SA2': # since sa2 can have armatures, we need to handle things a little different...
            newObjects = list()
            newMeshes = list()
            for o in objects:
                if not o.partOfArmature:
                    newObjects.append(o)
                    if o.processedMesh is not None and o.processedMesh not in newMeshes:
                        newMeshes.append(o.processedMesh)
            if len(newObjects) == 1 and isinstance(newObjects[0], Armature):
                objects = newObjects
                meshes = list()

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
            if o.origObject.type == 'MESH':
                if o.saProps["isCollision"]:
                    cObjects.append(o)
                else:
                    vObjects.append(o)

        cMeshes, dontUse = getMeshesFromObjects(cObjects, depsgraph, apply_modifs)
        vMeshes, materials = getMeshesFromObjects(vObjects, depsgraph, apply_modifs)

        meshes = list()
        meshes.extend(cMeshes)
        meshes.extend(vMeshes)

        ModelData.updateMeshes(objects, meshes)
        
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
    elif fmt == 'SA2' and not lvl and cObject.type == 'ARMATURE':
        visible = True if not cObject.saSettings.isCollision else cObject.saSettings.isVisible
        model = Armature(cObject, parent, hierarchyDepth, cObject.name, export_matrix, "cnk", cObject.saSettings.isCollision, visible)
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
    toDisable = list()
    oldStates = list()
    for m in obj.modifiers:
        if isinstance(m, bpy.types.ArmatureModifier):
            toDisable.append(m)
    for m in toDisable:
        oldStates.append(m.show_viewport)
        m.show_viewport = False
        
    ob_for_convert = obj.evaluated_get(depsgraph) if apply_modifs else obj.original
    me = ob_for_convert.to_mesh()

    trianglulateMesh(me)

    for s, m in zip(oldStates, toDisable):
        m.show_viewport = s

    return me, obj.data.materials

def trianglulateMesh(mesh: bpy.types.Mesh) -> bpy.types.Mesh:
    """Transforms a mesh into a mesh only consisting of triangles, so that it can be stripped"""
    
    # if we use custom normals, we gotta correct them manually, since blenders triangulate is shit
    if mesh.use_auto_smooth:
        # calculate em, so that we can collect the correct normals
        mesh.calc_normals_split()
        
        # and now store them, together with the vertex indices, since those will be the only identical data after triangulating
        normalData = list()
        for p in mesh.polygons:
            indices = list()
            normals = list()

            for l in p.loop_indices:
                loop = mesh.loops[l]
                nrm = loop.normal
                normals.append((nrm.x, nrm.y, nrm.z))
                indices.append(loop.vertex_index)
                
            normalData.append((indices,normals))
                
        # free the split data
        #mesh.free_normals_split()
            
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(mesh)
    bm.free()

    if mesh.use_auto_smooth:
        polygons = list()
        for p in mesh.polygons:
            polygons.append(p)
        
        splitNormals = [None] * len(mesh.loops)

        for nd in normalData:
            foundTris = 0
            toFind = len(nd[0])-2
            
            out = False
            toRemove = list()
            
            for p in polygons:
                found = 0
                for l in p.loop_indices:
                    if mesh.loops[l].vertex_index in nd[0]:
                        found += 1
                        
                if found == 3:
                    foundTris += 1
                    
                    for l in p.loop_indices:
                        splitNormals[l] = nd[1][nd[0].index(mesh.loops[l].vertex_index)]
                        
                    toRemove.append(p)
                    if foundTris == toFind:
                        break
                    
            for p in toRemove:
                polygons.remove(p)
            
        if len(polygons) > 0:
            print("\ntriangulating went wrong?", len(polygons))
        else:
            mesh.normals_split_custom_set(splitNormals)

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
        for v,k in labels.items():
            print("  ", k + ":", hex4(v))
        print("")

    #placeholders
    for l in labels:
        fileW.wUInt(0)
        fileW.wUInt(0)

    fileW.wLong(-1)

    # writing the strings
    for val, key in labels.items():
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
  

# for reading only
class Model:
    
    name: str
    objFlags: enums.ObjectFlags
    meshPtr: int

    matrix_world: mathutils.Matrix
    matrix_local: mathutils.Matrix

    child = None
    sibling = None

    parent = None
    children = list()
    meshes = list()

    def __init__(self,
                 name: str,
                 objFlags: enums.ObjectFlags,
                 meshPtr: int,
                 matrix_world: mathutils.Matrix,
                 matrix_local: mathutils.Matrix,
                 parent):
        self.name = name
        self.objFlags = objFlags
        self.meshPtr = meshPtr
        self.matrix_world = matrix_world
        self.matrix_local = matrix_local
        self.parent = parent
        if parent is not None:
            parent.children.append(self)
        self.children = list()
        self.meshes = list()

    def debug(self):
        print("  Model:", self.name)
        print("    objectFlags:", self.objFlags)
        print("    meshPtr:", hex4(self.meshPtr))
        print("    position:", str(Vector3(self.matrix_local.to_translation())))
        rot = self.matrix_local.to_euler()
        print("    rotation:", "(", str(rot.x) + ",", str(rot.y) + ",", str(rot.z), ")")
        print("    scale:", str(Vector3(self.matrix_local.to_scale())))

def readObjects(fileR: fileWriter.FileReader, address: int, hierarchyDepth: int, parent, labels: dict, result: list, tempOBJ: bpy.types.Object) -> int:

    if address in labels:
        label: str = labels[address]

        name = label
    else:
        name = "node_" + hex4(address)

    objFlags = enums.ObjectFlags(fileR.rUInt(address))
    meshPtr = fileR.rUInt(address + 4)

    position = Vector3((fileR.rFloat(address + 8), -fileR.rFloat(address + 16), fileR.rFloat(address + 12)))
    scale = Vector3((fileR.rFloat(address + 32), fileR.rFloat(address + 40), fileR.rFloat(address + 36)))

    # getting the rotation is a bit more difficult
    xRot = BAMSToRad(fileR.rInt(address + 20))
    yRot = BAMSToRad(fileR.rInt(address + 24))
    zRot = BAMSToRad(fileR.rInt(address + 28))

    rotation = mathutils.Euler((xRot, -zRot, yRot), 'XZY')
    rotation = rotation.to_matrix().to_euler('XYZ')

    tempOBJ.location = position
    tempOBJ.rotation_euler = rotation
    tempOBJ.scale = scale
    matrix_local =  tempOBJ.matrix_basis.copy()


    if parent is not None:
        matrix_world = parent.matrix_world @ matrix_local
    else:
        matrix_world = tempOBJ.matrix_basis.copy()

    model = Model(name, objFlags, meshPtr, matrix_world, matrix_local, parent)
    result.append(model)

    childPtr = fileR.rUInt(address + 44)
    if childPtr > 0:
        child = readObjects(fileR, childPtr, hierarchyDepth + 1, model, labels, result, tempOBJ)
        model.child = child
    
    siblingPtr = fileR.rUInt(address + 48)
    if siblingPtr > 0:
        sibling = readObjects(fileR, siblingPtr, hierarchyDepth, parent, labels, result, tempOBJ)
        model.sibling = sibling

    return model

def getDefaultMatDict() -> dict:
    d = dict()
    d["b_Diffuse"] = (1.0, 1.0, 1.0, 1.0)
    d["b_Specular"] = (1.0, 1.0, 1.0, 1.0)
    d["b_Ambient"] =(1.0, 1.0, 1.0, 1.0)
    d["b_Exponent"] = 1
    d["b_TextureID"] = 0
    d["b_d_025"] = False
    d["b_d_050"] = False
    d["b_d_100"] = False
    d["b_d_200"] = False
    d["b_use_Anisotropy"] = False
    d["b_texFilter"] = 'BILINEAR'
    d["b_clampV"] = False
    d["b_clampU"] = False
    d["b_mirrorV"] = False
    d["b_mirrorU"] = False
    d["b_ignoreSpecular"] = False
    d["b_useAlpha"] = False
    d["b_srcAlpha"] = 'SRC'
    d["b_destAlpha"] = 'INV_SRC'
    d["b_useTexture"] = True
    d["b_useEnv"] = False
    d["b_doubleSided"] = True
    d["b_flatShading"] = False
    d["b_ignoreLighting"] = False
    d["b_ignoreAmbient"] = False
    d["gc_shadowStencil"] = 1
    d["gc_texMatrixID"] = 'IDENTITY'
    d["gc_texGenSourceMtx"] = 'TEX0'
    d["gc_texGenSourceBmp"] = 'TEXCOORD0'
    d["gc_texGenSourceSRTG"] = 'COLOR0'
    d["gc_texGenType"] = 'MTX2X4'
    d["gc_texCoordID"] = 'TEXCOORD0'
    return d
