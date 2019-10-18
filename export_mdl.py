import bpy
import os
from . import fileWriter, enums, common, format_BASIC, format_CHUNK, format_GC
from .common import ModelData

DO = False # Debug out

def hex8(number : int):
    return '{:08x}'.format(number)

def write(context, 
         filepath, *, 
         export_format,
         use_selection,
         apply_modifs,
         global_matrix,
         console_debug_output
         ):

   from .common import ModelData

   global DO
   DO = console_debug_output
   common.DO = DO
   format_BASIC.DO = DO
   format_CHUNK.DO = DO
   format_GC.DO = DO

   if DO:
         # clear console and enable debug outputs
         os.system("cls")


   # create the file
   fileW = fileWriter.FileWriter(filepath=filepath)

   # write the header
   fileVersion = 3

   if export_format == 'SA1':
      indicator = enums.MDLFormatIndicator.SA1MDL
   elif export_format == 'SA2':
      indicator = enums.MDLFormatIndicator.SA2MDL
   else: # SA2BLVL
      indicator = enums.MDLFormatIndicator.SA2BMDL
      
   fileW.wULong(indicator.value | (fileVersion << 56))

   if DO:
      print(" == Starting MDL file exporting ==")
      print("  File:", fileW.filepath)
      print("  Format:", export_format, "version", fileVersion)
      print("  - - - - - -\n")

   fileW.wUInt(0) # placeholder for the model properties address
   fileW.wUInt(0) # placeholder for the labels address     
   labels = dict() # for labels methadata

   # creating and getting variables to use in the export process
   objects, meshes, materials, mObjects = common.convertObjectData(context, use_selection, apply_modifs, global_matrix, export_format, False)
   if objects is None:
      fileW.close()
      return {'CANCELLED'}

   if export_format == 'SA1':
      # writing material data first
      bscMaterials = format_BASIC.Material.writeMaterials(fileW, materials, labels)
      # then writing mesh data
      for m in meshes:
         mesh = format_BASIC.Attach.fromMesh(m, global_matrix, bscMaterials)
         if mesh is not None:
               mesh.write(fileW, labels)

   elif export_format == 'SA2':
      if not (len(objects) == 1 and isinstance(objects[0], common.Armature)):
         for m in meshes:
            mesh = format_CHUNK.Attach.fromMesh(m, global_matrix, materials)
            if mesh is not None:
               mesh.write(fileW, labels)

   else:
      for m in meshes:
          mesh = format_GC.Attach.fromMesh(m, global_matrix, materials)
          if mesh is not None:
              mesh.write(fileW, labels)

   # writing model data
   if export_format == 'SA2' and len(objects) == 1 and isinstance(objects[0], common.Armature):
      modelPtr = objects[0].writeArmature(fileW, global_matrix, materials, labels)
   else:
      ModelData.updateMeshPointer(objects, labels)
      modelPtr = ModelData.writeObjectList(objects, fileW, labels)

   labelsAddress = fileW.tell()
   fileW.seek(8, 0) # go to the location of the model properties addrees
   fileW.wUInt(modelPtr) # and write the address
   fileW.wUInt(labelsAddress)
   fileW.seek(0,2) # then return back to the end
   
   if DO:
      print(" == Model file info ==")
      print("  model pointer: ", hex8(modelPtr))
      print("  labels pointer:", hex8(labelsAddress))
      print(" - - - -\n")
      print(" == Model hierarchy == \n")
      for o in objects:
         marker = " "
         for r in range(o.hierarchyDepth):
            marker += "--"
         if len(marker) > 1:
            print(marker, o.name)
         else:
            print("", o.name)
      print(" - - - -\n")
      

   # writing chunk data
   common.writeMethaData(fileW, labels, context.scene)

   fileW.close()
   return {'FINISHED'}