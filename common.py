import bpy
from . import fileWriter, enums
import math
import mathutils

DO = False # Debug Out

class Vector3:
    """Point in 3D Space"""

    x = 0
    y = 0
    z = 0

    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

    def toMathutils(self):
        import mathutils
        return mathutils.Vector((self.x, self.y, self.z))

    def distanceFromCenter(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z)**(0.5)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wFloat(self.x)
        fileW.wFloat(self.y)
        fileW.wFloat(self.z)

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

class BAMSRotation:

    x = 0
    y = 0
    z = 0

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = BAMSRotation.RadToBAMS(x)
        self.y = BAMSRotation.RadToBAMS(y)
        self.z = BAMSRotation.RadToBAMS(z)


    def RadToBAMS(v):
        return round((math.degrees(v) / 360.0) * 0xFFFF)

    def BAMSToRad(v):
        return v / (65536 / 360.0)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wInt(self.x)
        fileW.wInt(self.y)
        fileW.wInt(self.z)

    def __str__(self):
        return "(" + '{:04x}'.format(self.x) + ", " + '{:04x}'.format(self.y) + ", " + '{:04x}'.format(self.z) + ")"

class saObject:

    name = ""
    hierarchyLvl = 0
    address = 0
    flags = enums.ObjectFlags.NoAnimate | enums.ObjectFlags.NoMorph
    meshAddress = 0
    position = Vector3()
    rotation = BAMSRotation()
    scale = Vector3(1,1,1)
    child = None
    sibling = None

    def __init__(self,
                 name: str = "",
                 meshname: str = None,
                 flags = enums.ObjectFlags.NoAnimate | enums.ObjectFlags.NoMorph,
                 pos = [0,0,0],
                 rot = [0,0,0],
                 scale = [0,0,0],
                 child = None,
                 sibling = None,
                 hlvl = 0,
                 labels = None):
    
        self.name = name
        self.flags = flags
        if meshname is None:
            self.meshAddress = 0
            self.flags |= enums.ObjectFlags.NoDisplay
        else:
            meshKey = "a_" + meshname
            if meshKey in labels.keys():
                self.meshAddress = labels["a_" + meshname]
            else:
                self.meshAddress = 0
                self.flags |= enums.ObjectFlags.NoDisplay
            #self.meshAddress = labels[meshname]

        self.position = Vector3(pos[0], pos[1], pos[2])
        self.rotation = BAMSRotation(rot[0], rot[1], rot[2])
        self.scale = Vector3(scale[0], scale[1], scale[2])
        self.child = child
        if child is None:
            self.flags |= enums.ObjectFlags.NoChildren
        self.sibling = sibling
        self.address = 0 # set when writing
        self.hierarchyLvl = hlvl

    def getObjList(bObject: bpy.types.Object, objects, hlvl, global_matrix, siblings, result, labels):

        sibling = None
        if len(siblings) > 1:
            
            siblIndex = siblings.index(bObject) + 1
            if siblIndex < len(siblings):
                sibling = siblings[siblIndex]
                while not (sibling in objects):
                    siblIndex += 1
                    if siblIndex < len(siblings):
                        sibling = siblings[siblIndex]
                    else:
                        sibling = None
                        break
                    
                if sibling is not None:
                    saObject.getObjList(sibling, objects, hlvl, global_matrix, siblings, result, labels)
                    sibling = result[-1]

        if len(bObject.children) > 0 and bObject.children[0] in objects:
            saObject.getObjList(bObject.children[0], objects, hlvl + 1, global_matrix, bObject.children, result, labels)
            child = result[-1]
        else:
            child = None

        obj_mat = global_matrix @ bObject.matrix_world

        rot = bObject.matrix_world.to_euler('XZY')
        rot = global_matrix @ mathutils.Vector((rot.x, rot.y, rot.z))

        meshname = None
        if bObject.type == 'MESH':
            meshname = bObject.data.name

        obj = saObject(name=bObject.name,
                       meshname=meshname, 
                       # flags will be set later
                       pos= obj_mat.translation,
                       rot= rot,
                       scale= obj_mat.to_scale(),
                       child= child,
                       sibling= sibling,
                       hlvl=hlvl,
                       labels=labels
                       )
        result.append(obj)
        return obj

    def write(self, fileW, labels, lvl):
        labels["o_" + self.name] = fileW.tell()
        #labels[self.name] = fileW.tell()
        self.address = fileW.tell()

        fileW.wUInt(self.flags.value)
        fileW.wUInt(self.meshAddress)
        self.position.write(fileW)
        self.rotation.write(fileW)
        self.scale.write(fileW)
        fileW.wUInt(0 if self.child is None or lvl else self.child.address)
        fileW.wUInt(0 if self.sibling is None or lvl else self.sibling.address)

    def writeObjList(fileW, objList, labels, lvl):
        for o in objList:
            o.write(fileW, labels, lvl)
        
        return objList[-1].address # last object address

    def debugOut(self):
        print(" Object:", self.name)
        print("   address:", '{:08x}'.format(self.address))
        print("   mesh addr:", '{:08x}'.format(self.meshAddress))
        print("   flags:", self.flags)
        print("   position:", str(self.position))
        print("   rotation:", str(self.rotation))
        print("   scale:", str(self.scale))
        print("   child:", "None" if self.child is None else self.child.name)
        print("   sibling:", "None" if self.sibling is None else self.sibling.name)
        print("---- \n")

    def debugHierarchy(objList):
        print("object hierarchy:")
        for o in reversed(objList):
            print(" --" * o.hierarchyLvl, o.name)
        print("\n---- \n")

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
        
        self.boundCenter = Vector3( BoundingBox.center(self.x,self.xn), 
                            BoundingBox.center(self.y,self.yn), 
                            BoundingBox.center(self.z,self.zn) )

        distance = 0
        for v in vertices:
            dif = Vector3(  self.boundCenter.x - v.co.x, 
                            self.boundCenter.y - v.co.y, 
                            self.boundCenter.z - v.co.z)
            tDist = math.sqrt(pow(dif.x, 2) + pow(dif.y, 2) + pow(dif.z, 2))
            if tDist > distance:
                distance = tDist

        self.radius = distance
    
    def center(p1, p2):
        return (p1 + p2) / 2.0

    def write(self, fileW):
        self.boundCenter.write(fileW)
        fileW.wFloat(self.radius)

class COL:
    unknown1 = 0
    mdlAddress = 0
    unknown2 = 0
    unknown3 = 0
    flags = enums.SA1SurfaceFlags.null

    def __init__(self, bObject, global_matrix, labels, sa1):
        self.name = bObject.name
        # placeholders to test
        self.bounds = None
        self.unknown1 = 0
        self.unknown2 = 0
        self.unknown3 = 0

        if bObject.type == 'MESH':
            self.mdlAddress = labels["o_" + bObject.name]
            #self.mdlAddress = labels[bObject.name]
            self.bounds = BoundingBox(bObject.data.vertices)

            bc = self.bounds.boundCenter.toMathutils()
            bc += bObject.location
            bc = global_matrix @ bc

            self.bounds.boundCenter = Vector3(bc.x, bc.y, bc.z)
        else:
            self.mdlAddress = 0


        if bObject.type == 'MESH':
            props = bObject.saSettings
            if sa1:
                self.flags = enums.SA1SurfaceFlags.null
                if props.isCollision:
                    if props.solid:
                        self.flags |= enums.SA1SurfaceFlags.Solid
                    if props.water:
                        self.flags |= enums.SA1SurfaceFlags.Water
                    if props.noFriction:
                        self.flags |= enums.SA1SurfaceFlags.NoFriction
                    if props.noAcceleration:
                        self.flags |= enums.SA1SurfaceFlags.NoAcceleration
                    if props.cannotLand:
                        self.flags |= enums.SA1SurfaceFlags.CannotLand
                    if props.increasedAcceleration:
                        self.flags |= enums.SA1SurfaceFlags.IncreasedAcceleration
                    if props.diggable:
                        self.flags |= enums.SA1SurfaceFlags.Diggable
                    if props.unclimbable:
                        self.flags |= enums.SA1SurfaceFlags.Unclimbable
                    if props.hurt:
                        self.flags |= enums.SA1SurfaceFlags.Hurt
                    if props.footprints:
                        self.flags |= enums.SA1SurfaceFlags.Footprints
                    if props.isVisible:
                        self.flags |= enums.SA1SurfaceFlags.Visible
                else:
                    self.flags |= enums.SA1SurfaceFlags.Visible
            else: #sa2
                self.flags = enums.SA2SurfaceFlags.null
                if props.isCollision:
                    if props.solid:
                        self.flags |= enums.SA2SurfaceFlags.Solid
                    if props.water:
                        self.flags |= enums.SA2SurfaceFlags.Water
                else:
                    self.flags = enums.SA2SurfaceFlags.Visible

    def write(self, fileW, sa1):
        if self.mdlAddress == 0:
            fileW.wFloat(0)
            fileW.wFloat(0)
            fileW.wFloat(0)
            fileW.wFloat(0)
        else:
            self.bounds.write(fileW)
        if sa1:
            fileW.wUInt(self.unknown1)
            fileW.wUInt(self.unknown2)
            fileW.wUInt(self.mdlAddress)
        else:
            fileW.wUInt(self.mdlAddress)            
            fileW.wUInt(self.unknown2)
        fileW.wUInt(self.unknown3)
        fileW.wUInt(self.flags.value)

        if DO:
            print(" COL:", self.name)
            print("   mdl address:", '{:08x}'.format(self.mdlAddress))
            print("   surface flags:", self.flags)
            print("   Bounds:", str(self.bounds.boundCenter), ", ", self.bounds.radius)
            print("---- \n")


def evaluateObjectsToWrite(use_selection: bool,
                           apply_modifs: bool,
                           context: bpy.types.Context,
                           lvlFmt = False # only used for sa2 levels
                           ):
    # getting the objects to export
    if use_selection:
        if len(context.selected_objects) == 0:
            print("No objects selected")
            return {'FINISHED'}, None, None, None
        objects = context.selected_objects
    else:
        if len(context.scene.objects) == 0:
            print("No objects found")
            return {'FINISHED'}, None, None, None
        objects = context.scene.objects.values()

    depsgraph = context.evaluated_depsgraph_get()
    if not lvlFmt:
        meshes, materials = getMeshesFromObjects(objects, depsgraph, apply_modifs)
    else:
        cObjects = [] # collision objects
        vObjects = [] # visual objects

        for o in objects:
            if o.type == 'MESH' and o.saSettings.isCollision:
                cObjects.append(o)
            else:
                vObjects.append(o)

        cMeshes, dontUse = getMeshesFromObjects(cObjects, depsgraph, apply_modifs)
        vMeshes, materials = getMeshesFromObjects(vObjects, depsgraph, apply_modifs)
    
    # getting the objects for starting
    noParents = list()
    for o in objects:
        if o.parent == None or not (o.parent in objects):
            noParents.append(o)

    global DO
    if DO:
        print(" Materials:", len(materials))
        if lvlFmt:
            print(" Visual Meshes:", len(vMeshes))
            print(" Collision Meshes:", len(cMeshes))
        else:
            print(" Meshes:", len(meshes))
        print(" Objects:", len(objects), "\n")

    if not lvlFmt:
        return objects, noParents, meshes, materials
    else:        
        return objects, noParents, cMeshes, vMeshes, materials, cObjects, vObjects

def getMeshesFromObjects(objects, depsgraph, apply_modifs):
    #checking which meshes are in the objects at all
    tMeshes = []
    for o in objects:
        if o.type == 'MESH':
            tMeshes.append(o.data)

    #checking whether there are any objects that share a mesh
    collectedMOMeshes = []
    mObjects = []
    meshesToConvert = []
    for o in objects:
        if o.type == 'MESH':
            if tMeshes.count(o.data) > 1:
                if collectedMOMeshes.count(o.data) == 0:
                    mObjects.append(o)
                    meshesToConvert.append(o)
                    collectedMOMeshes.append(o.data)
            else:
                meshesToConvert.append(o)

    outMeshes = []
    materials = []
    for o in meshesToConvert:
        if len(o.data.vertices) == 0:
            continue

        newMesh, mats = convertMesh(o, depsgraph, False if o in mObjects else apply_modifs)
        outMeshes.append(newMesh)
        if not o.saSettings.isCollision:
            for m in mats:
                if m not in materials:
                    materials.append(m)

    return outMeshes, materials

def convertMesh(obj, depsgraph, apply_modifs):

    ob_for_convert = obj.evaluated_get(depsgraph) if apply_modifs else obj.original
    me = ob_for_convert.to_mesh()

    trianglulateMesh(me)
    return me, obj.data.materials

def trianglulateMesh(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()

def writeBASICMaterialData(fileW: fileWriter.FileWriter, materials, labels: dict):
    from . import format_BASIC

    mats = list()

    if len(materials) == 0:
        labels["mat_default"] = fileW.tell()
        bMat = format_BASIC.Material()
        bMat.write(fileW)
        mats.append(bMat)
    else:
        for m in materials:
            labels["mat_" + m.name] = fileW.tell()
            #labels[m.name] = fileW.tell()
            bMat = format_BASIC.Material(name=m.name, material=m)
            bMat.write(fileW)
            mats.append(bMat)

    global DO
    if DO:
        for m in mats:
            print(" Material:", m.name)
            print("   diffuse color:", str(m.diffuse))
            print("   specular color:", str(m.specular))
            print("   specular strength:", m.exponent)
            print("   texture ID:", m.textureID)
            print("   flags:", m.mFlags, "\n---- \n")

def writeGCMeshData(fileW: fileWriter.FileWriter,
                    meshes,
                    global_matrix, 
                    labels: dict):
    from . import format_GC
    for m in meshes:
        print("to be done")

def getObjData(objects, noParents, global_matrix,  labels, isLvl = False):
    saObjects = list()
    root = saObject.getObjList(noParents[0], objects, 0, global_matrix, noParents, saObjects, labels)

    #checking if the last object has siblings, if so add a root object
    if root.sibling is not None and not isLvl:
        root = saObject("root", None, child = saObjects[-1])

        global DO
        if DO:
            for o in saObjects:
                o.hierarchyLvl += 1

        saObjects.append(root)

    if DO:
        for o in saObjects:
            o.debugOut()

        saObject.debugHierarchy(saObjects)

    return saObjects

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
        print(" Labels:")
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
        fileW.wString(key)
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
    
