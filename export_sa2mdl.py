import bpy
import os

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
   from . import FileWriter, enums, common
   
   os.system("cls")

   filepath = filepath.split('.')[0]

   fileVersion = 3
   #creating file and writing header
   if export_format == 'SA1MDL':
      fileW = FileWriter.FileWriter(filepath= filepath + ".sa1mdl")
      fileW.wULong(enums.MDLFormatIndicator.SA1MDL.value | (fileVersion << 56))
   elif export_format == 'SA2MDL':
      fileW = FileWriter.FileWriter(filepath= filepath + ".sa2mdl")
      fileW.wULong(enums.MDLFormatIndicator.SA2MDL.value | (fileVersion << 56))
   else: # SA2BMDL
      fileW = FileWriter.FileWriter(filepath= filepath + ".sa2bmdl")
      fileW.wULong(enums.MDLFormatIndicator.SA2BMDL.value | (fileVersion << 56))

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
   materials = []
   for o in objects:
      if o.type == 'MESH' :
         tMeshes.append(o.data)
         for m in o.data.materials:
            if not m in materials:
               materials.append(m)

   # filtering the actual mesh data
   meshes = []
   for o in objects:
      if o.type == 'MESH' :
         if tMeshes.count(o.data) > 1 and meshes.count(o.data) == 0 :
               meshes.append(o.data)
         else:
               meshes.append(o)

   # Writing starts here

   fileW.wUInt(0) # placeholder for the model properties address
   fileW.wUInt(0) # placeholder for the labels address

   if export_format == 'SA1MDL':
      materialAddress = fileW.tell()
      common.writeBASICMaterialData(fileW, materials, labels) # writing material data first
      common.writeBASICMeshData( fileW,
                                 meshes,
                                 apply_modifs,
                                 global_matrix,
                                 materialAddress,
                                 materials,
                                 labels )

   # getting the objects for starting
   noParents = list()
   for o in objects:
      if o.parent == None:
         noParents.append(o)

   saObjects = list()
   common.saObject.getObjList(noParents[0], global_matrix, noParents, saObjects, labels)
   mdlAddress = common.saObject.writeObjList(fileW, saObjects, labels)
   print(mdlAddress)

   labelsAddress = fileW.tell()
   fileW.seek(8, 0) # go to the location of the model properties addrees
   fileW.wUInt(mdlAddress) # and write the address
   fileW.wUInt(labelsAddress)
   fileW.seek(0,2) # then return back to the end

   # === CHUNK DATA ===

   #writing the labels
   
   fileW.wUInt(enums.Chunktypes.Label.value)
   newLabels = dict()
   sizeLoc = fileW.tell()
   fileW.wUInt(0)

   #placeholders
   for k in labels:
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


   # author
   if not (author == ""):
      fileW.wUInt(enums.Chunktypes.Author.value)
      sizeLoc = fileW.tell()
      fileW.wUInt(0)
      fileW.wString(author)
      fileW.align(4)
      size = fileW.tell() - sizeLoc - 4
      fileW.seek(sizeLoc, 0)
      fileW.wUInt(size)
      fileW.seek(0, 2)

   # description
   if not (description == ""):
      fileW.wUInt(enums.Chunktypes.Description.value)
      sizeLoc = fileW.tell()
      fileW.wUInt(0)
      fileW.wString(description)
      fileW.align(4)
      size = fileW.tell() - sizeLoc - 4
      fileW.seek(sizeLoc, 0)
      fileW.wUInt(size)
      fileW.seek(0, 2)

   fileW.wUInt(enums.Chunktypes.End.value)
   fileW.wUInt(0)

   fileW.close()
   return {'FINISHED'}