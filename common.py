import bpy
from . import FileWriter, enums

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

    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = BAMSRotation.DegToBAMS(x)
        self.y = BAMSRotation.DegToBAMS(y)
        self.z = BAMSRotation.DegToBAMS(z)


    def DegToBAMS(v):
        return round(v * (65536 / 360.0))

    def BAMSToDeg(v):
        return v / (65536 / 360.0)

    def write(self, fileW):
        """Writes data to file"""
        fileW.wInt(self.x)
        fileW.wInt(self.y)
        fileW.wInt(self.z)

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

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
            self.meshAddress = labels["a_" + meshname]

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

        obj_mat = bObject.matrix_world @ global_matrix

        meshname = None
        if bObject.type == 'MESH':
            meshname = bObject.data.name

        obj = saObject(name=bObject.name,
                       meshname=meshname, 
                       # flags will be set later
                       pos= obj_mat.translation,
                       rot= obj_mat.to_euler(),
                       scale= obj_mat.to_scale(),
                       child= child,
                       sibling= sibling,
                       hlvl=hlvl,
                       labels=labels
                       )
        result.append(obj)
        return obj

    def write(self, fileW, labels):
        labels["o_" + self.name] = fileW.tell()
        self.address = fileW.tell()

        fileW.wUInt(self.flags.value)
        fileW.wUInt(self.meshAddress)
        self.position.write(fileW)
        self.rotation.write(fileW)
        self.scale.write(fileW)
        fileW.wUInt(0 if self.child is None else self.child.address)
        fileW.wUInt(0 if self.sibling is None else self.sibling.address)

    def writeObjList(fileW, objList, labels):
        for o in objList:
            o.write(fileW, labels)
        
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

def evaluateObjectsToWrite(use_selection: bool,
                           apply_modifs: bool,
                           context: bpy.types.Context
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

    # getting all meshdata first, so that it cna be checked which is used multiple times
    tMeshes = []
    for o in objects:
        if o.type == 'MESH' :
            tMeshes.append(o.data)

    # filtering the actual mesh data
    meshes = []
    for o in objects:
        if o.type == 'MESH' :
            if tMeshes.count(o.data) > 1 and meshes.count(o.data) == 0 :
                meshes.append(o.data)
            else:
                meshes.append(o)

    # convert them
    outMeshes = []
    materials = []
    depsgraph = context.evaluated_depsgraph_get()
    for m in meshes:
        newMesh = convertMesh(m, depsgraph, apply_modifs)
        outMeshes.append(newMesh)
        for m in newMesh.materials:
            if not (m in materials):
                materials.append(m)

    # getting the objects for starting
    noParents = list()

    for o in objects:
        if o.parent == None or not (o.parent in objects):
            noParents.append(o)

    global DO
    if DO:
        print(" Materials:", len(materials))
        print(" Meshes:", len(meshes))
        print(" Objects:", len(objects), "\n")

    return objects, noParents, outMeshes, materials

def trianglulateMesh(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()

def convertMesh(obj, depsgraph, apply_modifs):

    if isinstance(obj, bpy.types.Object):
        ob_for_convert = obj.evaluated_get(depsgraph) if apply_modifs else obj.original
        me = ob_for_convert.to_mesh()
        print(obj.data.name == me.name)
    else:
        me = obj

    trianglulateMesh(me)
    return me

def writeBASICMaterialData(fileW: FileWriter.FileWriter, materials, labels: dict):
    from . import BASIC

    mats = list()

    if len(materials) == 0:
        labels["mat_default"] = fileW.tell()
        bMat = BASIC.Material()
        bMat.write(fileW)
        mats.append(bMat)
    else:
        for m in materials:
            labels["mat_" + m.name] = fileW.tell()
            bMat = BASIC.Material(name=m.name, material=m)
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

def writeBASICMeshData( fileW: FileWriter.FileWriter,
                        meshes,
                        global_matrix,
                        materials,
                        labels: dict):
    from . import BASIC
    for m in meshes:
        BASIC.WriteMesh(fileW, m, global_matrix, materials, labels)

def getObjData(objects, noParents, global_matrix,  labels):
    saObjects = list()
    root = saObject.getObjList(noParents[0], objects, 0, global_matrix, noParents, saObjects, labels)

    #checking if the last object has siblings, if so add a root object
    if root.sibling is not None:
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

def writeMethaData(fileW: FileWriter.FileWriter,
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
    
