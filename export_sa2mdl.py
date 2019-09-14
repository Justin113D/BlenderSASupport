import bpy
import os

def mesh_triangulate(me):
   import bmesh
   bm = bmesh.new()
   bm.from_mesh(me)
   bmesh.ops.triangulate(bm, faces=bm.faces)
   bm.to_mesh(me)
   bm.free()

def writeMeshData(meshes
                  export_format,
                  apply_modifs,
                  global_matrix,
                  labels):
   
   


   return [meshData, meshPropertiesAddress]


def write(context, 
         filepath, *, 
         export_format,
         use_selection,
         apply_modifs,
         author,
         description,
         global_matrix,
         console_debug_output
         ):
   from . import FileWriter, enums
   
   os.system("cls")

   filepath = filepath.split('.')[0]
   print(filepath)

   #creating file and writing header
   if export_format == 'SA1MDL':
      fileW = FileWriter.FileWriter(filepath + ".sa1mdl")
      fileW.wULong(enums.MDLFormatIndicator.SA1MDL.value)
   elif export_format == 'SA2MDL':
      fileW = FileWriter.FileWriter(filepath + ".sa2mdl")
      fileW.wULong(enums.MDLFormatIndicator.SA2MDL.value)
   else: # SA2BMDL
      fileW = FileWriter.FileWriter(filepath + ".sa2bmdl")
      fileW.wULong(enums.MDLFormatIndicator.SA2BMDL.value)

   labels = dict()

   scene = context.scene

   # getting the objects to export
   if use_selection:
      if len(context.selected_objects) == 0:
         print("No objects selected")
         return {'CANCELLED'}
      objects = context.selected_objects
   else:
      if len(context.scene.objects) == 0:
         print("No objects found")
         return {'CANCELLED'}
      objects = context.scene.objects

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

   meshData = writeMeshData(meshes,
                            export_format,
                            apply_modifs,
                            global_matrix,
                            labels )

   fileW.close()
   return {'FINISHED'}