import bpy
import os
from . import fileWriter, enums, common, format_BASIC, format_GC, format_CHUNK

DO = False # Debug out

def hex8(number : int):
    return '{:08x}'.format(number)

def hex16(number : int):
    return '{:016x}'.format(number)

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

     # write the file header
     fileVersion = 3
     
     if export_format == 'SA1':
          indicator = enums.LVLFormatIndicator.SA1LVL
     elif export_format == 'SA2':
          indicator = enums.LVLFormatIndicator.SA2LVL
     else: # SA2BLVL
          indicator = enums.LVLFormatIndicator.SA2BLVL

     fileW.wULong(indicator.value | (fileVersion << 56))          

     if DO:
          print(" == Starting LVL file exporting ==")
          print("  File:", fileW.filepath)
          print("  Format:", export_format, "version", fileVersion)
          print("  - - - - - -\n")

     # settings placeholders for the
     fileW.wUInt(0) # landtable address
     fileW.wUInt(0) # methadata address
     labels = dict() # for labels methadata

     # creating and getting variables to use in the export process
     if export_format == 'SA1':
          #the sa1 format doesnt need to seperate between collision and visual meshes
          objects, meshes, materials, mObjects = common.convertObjectData(context, use_selection, apply_modifs, global_matrix, export_format, True)
          if objects == {'FINISHED'}:
               file.close()
               return {'FINISHED'}

          bscMaterials = format_BASIC.Material.writeMaterials(fileW, materials, labels)

          # then writing mesh data
          if DO:
               print(" == Writing BASIC attaches == \n")
          for m in meshes:
               mesh = format_BASIC.Attach.fromMesh(m, global_matrix, bscMaterials)
               if mesh is not None:
                    mesh.write(fileW, labels)
          if DO:
               print(" - - - - \n")
     else:
          #writing the collision material, just to be sure
          if context.scene.saSettings.doubleSidedCollision:
               colMat = format_BASIC.Material(materialFlags=enums.MaterialFlags.FLAG_DOUBLE_SIDE)
          else:
               colMat = format_BASIC.Material()
          colMat.write(fileW, labels)

          objects, cMeshes, vMeshes, materials, cObjects, vObjects = common.convertObjectData(context, use_selection, apply_modifs, global_matrix, export_format, True)
          if objects == {'FINISHED'}:
               file.close()
               return {'FINISHED'}

          #writing the collision meshes
          if DO:
               print(" == Writing BASIC attaches == \n")          
          for m in cMeshes:
               mesh = format_BASIC.Attach.fromMesh(m, global_matrix, [], isCollision=True)
               if mesh is not None:
                    mesh.write(fileW, labels)

          #writing visual meshes
          if export_format == 'SA2':
               if DO:
                    print(" == Writing CHUNK attaches == \n")  
               for m in vMeshes:
                    mesh = format_CHUNK.Attach.fromMesh(m, global_matrix, materials)
                    if mesh is not None:
                         mesh.write(fileW, labels)
          else:
               if DO:
                    print(" == Writing GC attaches == \n")
               for m in vMeshes:
                    mesh = format_GC.Attach.fromMesh(m, global_matrix, materials)
                    if mesh is not None:
                         mesh.write(fileW, labels)
     
     # writing model data
     ModelData.updateMeshPointer(objects, labels)
     ModelData.writeObjectList(objects, fileW, labels, True)

     #write COLs
     COLPtr = fileW.tell()

     if export_format == 'SA1':
          COLcount = len(mObjects)
          for o in mObjects:
               o.writeCOL(fileW, labels, False)
     else:
          COLcount = len(vObjects) + len(cObjects) 
          for o in vObjects:
               o.writeCOL(fileW, labels, True)
          for o in cObjects:
               o.writeCOL(fileW, labels, True)

     #write texture filename
     texFileNameAddr = fileW.tell()
     if context.scene.saSettings.texFileName == "":
          texFileName =  os.path.splitext(os.path.basename(filepath))[0]
     else: 
          texFileName = context.scene.saSettings.texFileName
     
     texListPointer = int("0x" + context.scene.saSettings.texListPointer, 0)
     fileW.wString(texFileName)

     fileW.align(4)

     landTableAddress = fileW.tell()
     labels[texFileName + "_Table"] = landTableAddress

     #landtable info
     fileW.wUShort(COLcount) # COL count
     drawDist = context.scene.saSettings.drawDistance
     animPtr = 0
     
     if export_format == 'SA1':
          animCount = 0
          fileW.wUShort(animCount) # (unused rn)
          ltFlags = 8
          fileW.wUInt(ltFlags) # landtable flags - 8 determines that PVM/GVM's should be used
          fileW.wFloat(drawDist) # Draw Distance
          fileW.wUInt(COLPtr) # geometry address
          fileW.wUInt(animPtr) # animation address (unused rn)
          fileW.wUInt(texFileNameAddr) # texture file name address
          fileW.wUInt(texListPointer) # texture list pointer (usually handled by mod)

          unknown2 = 0
          fileW.wFloat(unknown2)
          unknown3 = 0
          fileW.wFloat(unknown3)
     else:
          fileW.wUShort(len(vObjects)) # visual col count
          ltFlags = 0
          fileW.wULong(ltFlags)
          fileW.wFloat(drawDist) # Draw Distance
          fileW.wUInt(COLPtr) # geometry address
          fileW.wUInt(animPtr) # animation address (unused rn)
          fileW.wUInt(texFileNameAddr) # (texFileNameAddr) texture file name address
          fileW.wUInt(texListPointer) # texture list pointer (usually handled by mod)

     labelsAddress = fileW.tell()

     # writing the 
     fileW.seek(8, 0) # go to the location of the model properties addrees
     fileW.wUInt(landTableAddress) # and write the address
     fileW.wUInt(labelsAddress) # labels address
     fileW.seek(0,2) # then return back to the end

     if DO:
          print(" == Landtable info ==")
          if export_format == 'SA1':
               print("  COL count:        ",  len(objects))
               print("  Animation count:  ",  animCount)
               print("  Landtable Flags:  ",  hex8(ltFlags))
               print("  Draw distance:    ",  drawDist)
               print("  COL address:      ",  hex8(COLPtr))
               print("  Animation address:",  hex8(animPtr))
               print("  Texture file name:",  texFileName)
               print("  Tex list pointer: ",  hex8(texListPointer))
          else:
               print("  COL count:        ",  len(objects))
               print("  Visual COL count: ",  len(vObjects))
               print("  Unknown:          ",  hex16(ltFlags))
               print("  Draw distance:    ",  drawDist)
               print("  COL address:      ",  hex8(COLPtr))
               print("  Anim address:     ",  hex8(animPtr))
               print("  Texture file name:",  texFileName)
               print("  Tex list pointer: ",  hex8(texListPointer))
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

     common.writeMethaData(fileW, labels, context.scene)

     fileW.close()
     return {'FINISHED'}