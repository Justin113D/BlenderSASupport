import bpy
from . import FileWriter, enums

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

class BAMSRotation:

    x = 0
    y = 0
    z = 0

    def __init__(self, x: float, y: float, z: float):
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

class saObject:

    def __init__(self,
                 name: str = "",
                 meshname: str = "",
                 flags = enums.ObjectFlags.NoAnimate | enums.ObjectFlags.NoMorph,
                 pos = [0,0,0],
                 rot = [0,0,0],
                 scale = [0,0,0],
                 child = None,
                 sibling = None,
                 labels = None):
    
        self.name = name
        self.flags = flags
        self.meshAddress = labels["a_" + meshname]
        self.position = Vector3(pos[0], pos[1], pos[2])
        self.rotation = BAMSRotation(rot[0], rot[1], rot[2])
        self.scale = Vector3(scale[0], scale[1], scale[2])
        self.child = child
        if child is None:
            self.flags |= enums.ObjectFlags.NoChildren
        self.sibling = sibling
        self.address = 0 # set when writing

    def getObjList(bObject: bpy.types.Object, global_matrix, siblings, result, labels):
        
        if len(bObject.children) > 0:
            saObject.getObjList(bObject.children[0], global_matrix, siblings, result, labels)
            child = result[-1]
        else:
            child = None

        if len(siblings) > 1:
            siblIndex = siblings.index(bObject)
            if siblIndex == len(siblings) - 1:
                sibling = None
            else:
                saObject.getObjList(siblings[siblIndex+1], global_matrix, siblings, result, labels)
                sibling = result[-1]
        else:
            sibling = None

        obj_mat = bObject.matrix_world @ global_matrix
        obj = saObject(name=bObject.name,
                       meshname=bObject.data.name, 
                       # flags will be set later
                       pos= obj_mat.translation,
                       rot= obj_mat.to_euler(),
                       scale= obj_mat.to_scale(),
                       child= child,
                       sibling= sibling,
                       labels=labels
                       )
        result.append(obj)

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


def trianglulateMesh(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()

def convertMesh(obj, apply_modifs):

   if isinstance(obj, bpy.types.Object):
      ob_for_convert = obj.evaluated_get(depsgraph) if apply_modifs else obj.original
      me = ob_for_convert.to_mesh()
      name = obj.data.name
   else:
      me = obj
      name = me.name

   trianglulateMesh(me)
   return [me, name]

def writeBASICMaterialData(fileW: FileWriter.FileWriter, materials, labels: dict):
    from . import BASIC

    if len(materials) == 0:
        labels["mat_default"] = fileW.tell()
        bMat = BASIC.Material()
        bMat.write(fileW)
    else:
        for m in materials:
            labels["mat_" + m.name] = fileW.tell()
            bMat = BASIC.Material(material=m)
            bMat.write(fileW)

def writeBASICMeshData( fileW: FileWriter.FileWriter,
                        meshes,
                        apply_modifs,
                        global_matrix,
                        materialAddress,
                        materials,
                        labels: dict):
    from . import BASIC
    for m in meshes:
        me = convertMesh(m, apply_modifs)
        basicMesh = BASIC.WriteMesh(me[0], me[1], global_matrix, fileW.tell(), materialAddress, materials, labels)
        fileW.w(basicMesh)

