import bpy
import os

DO = False # Debug out

def debug(*string):
    global DO
    if DO:
        print(*string)

def write(context, 
         filepath, *, 
         export_format,
         use_selection,
         apply_modifs,
         global_matrix,
         console_debug_output
         ):
   from . import fileWriter, enums, common, format_BASIC, format_CHUNK, format_GC
   
   # clear console and enable debug outputs
   os.system("cls")
   global DO
   DO = console_debug_output
   common.DO = DO
   format_BASIC.DO = DO
   format_CHUNK.DO = DO
   format_GC.DO = DO

   # create the file
   fileW = fileWriter.FileWriter(filepath=filepath)
   debug("File:", fileW.filepath, "\n")

   # creating file and writing header   
   fileVersion = 3
   if export_format == 'SA1MDL':
      fileW.wULong(enums.MDLFormatIndicator.SA1MDL.value | (fileVersion << 56))
      fmt = 'SA1'
      debug("Format: SA1MDL V", fileVersion)
   elif export_format == 'SA2MDL':
      fileW.wULong(enums.MDLFormatIndicator.SA2MDL.value | (fileVersion << 56))
      fmt = 'SA2'
      debug("Format: SA2MDL V", fileVersion)
   else: # SA2BMDL
      fileW.wULong(enums.MDLFormatIndicator.SA2BMDL.value | (fileVersion << 56))
      fmt = 'SA2B'
      debug("Format: SA1BMDL V", fileVersion)

   # creating and getting variables to use in the export process
   objects, noParents, meshes, materials = common.evaluateObjectsToWrite(use_selection, apply_modifs, context)
   if objects == {'FINISHED'}:
      return {'FINISHED'}
   labels = dict()

   # Writing starts here

   fileW.wUInt(0) # placeholder for the model properties address
   fileW.wUInt(0) # placeholder for the labels address

   if export_format == 'SA1MDL':
      # writing material data first
      common.writeBASICMaterialData(fileW, materials, labels) 
      # then writing mesh data
      for m in meshes:
         format_BASIC.WriteMesh(fileW, m, global_matrix, materials, labels)

   elif export_format == 'SA2MDL':
      #writing mes data
      for m in meshes:
         format_CHUNK.write(fileW, m, global_matrix, materials, labels)

   else:
      #writing mes data
      for m in meshes:
         format_GC.write(fileW, m, global_matrix, materials, labels)


   saObjects = common.getObjData(objects, noParents, global_matrix, labels, fmt)
   mdlAddress = common.saObject.writeObjList(fileW, saObjects, labels, False)

   labelsAddress = fileW.tell()
   fileW.seek(8, 0) # go to the location of the model properties addrees
   fileW.wUInt(mdlAddress) # and write the address
   fileW.wUInt(labelsAddress)
   fileW.seek(0,2) # then return back to the end
   
   if DO:
      print(" model address: ", '{:08x}'.format(mdlAddress))
      print(" labels address:", '{:08x}'.format(labelsAddress), "\n") 

   # writing chunk data
   common.writeMethaData(fileW, labels, context.scene)

   fileW.close()
   return {'FINISHED'}