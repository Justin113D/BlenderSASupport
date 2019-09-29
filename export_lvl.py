import bpy

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
     import os
     from . import fileWriter, enums, common, format_BASIC, format_GC, format_CHUNK
     
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
     if export_format == 'SA1LVL':
          fileW.wULong(enums.LVLFormatIndicator.SA1LVL.value | (fileVersion << 56))
          fmt = 'SA1'
          debug("Format: SA1LVL V", fileVersion)
     elif export_format == 'SA2LVL':
          fileW.wULong(enums.LVLFormatIndicator.SA2LVL.value | (fileVersion << 56))
          fmt = 'SA2'
          debug("Format: SA2LVL V", fileVersion)
     else: # SA2BLVL
          fileW.wULong(enums.LVLFormatIndicator.SA2BLVL.value | (fileVersion << 56))
          fmt = 'SA2B'
          debug("Format: SA2BLVL V", fileVersion)

     fileW.wUInt(0) # placeholder for the landtable address
     fileW.wUInt(0) # placeholder for the labels address
     
     labels = dict()

     # creating and getting variables to use in the export process
     if export_format == 'SA1LVL':
          #the sa1 format doesnt need to seperate between collision and visual meshes
          objects, noParents, meshes, materials = common.evaluateObjectsToWrite(use_selection, apply_modifs, context)

          common.writeBASICMaterialData(fileW, materials, labels)
          # then writing mesh data
          for m in meshes:
               format_BASIC.WriteMesh(fileW, m, global_matrix, materials, labels)

     else:
          #writing the collision material, just to be sure
          if context.scene.saSettings.doubleSidedCollision:
               colMat = format_BASIC.Material(materialFlags=enums.MaterialFlags.FLAG_DOUBLE_SIDE)
          else:
               colMat = format_BASIC.Material()
          labels["col_material"] = 0x00000010
          colMat.write(fileW)

          objects, noParents, cMeshes, vMeshes, materials, cObjects, vObjects, nObjects, temp = common.evaluateObjectsToWrite(use_selection, apply_modifs, context, True)
          if objects == {'FINISHED'}:
               return {'FINISHED'}

          #writing the collision meshes
          for m in cMeshes:
               format_BASIC.WriteMesh(fileW, m, global_matrix, [], labels, isCollision=True)

          #writing visual meshes
          if export_format == 'SA2LVL':
               for m in vMeshes:
                    format_CHUNK.write(fileW, m, global_matrix, materials, labels)
          else:
               for m in vMeshes:
                    format_GC.write(fileW, m, global_matrix, materials, labels)
     


     saObjects = common.getObjData(objects, noParents, global_matrix, labels, fmt, isLvl = True)
     common.saObject.writeObjList(fileW, saObjects, labels, True)

     #write COLs
     COLaddress = fileW.tell()

     if export_format == 'SA1LVL':
          for o in objects:
               labels["col_" + o.name] = fileW.tell()
               #labels[o.name] = fileW.tell()
               col = common.COL(o, global_matrix, labels, True)
               col.write(fileW, True)
     else:
          for o in vObjects:
               labels["col_" + o.name] = fileW.tell()
               #labels[o.name] = fileW.tell()
               col = common.COL(o, global_matrix, labels, False)
               col.write(fileW, False)
          for o in cObjects:
               labels["col_" + o.name] = fileW.tell()
               #labels[o.name] = fileW.tell()
               col = common.COL(o, global_matrix, labels, False)
               col.write(fileW, False)
          #nObjects dont receive a COL, since they are no level geometry, but they exist as an empty object

     texFileNameAddr = fileW.tell()
     #write texture filename
     if context.scene.saSettings.texFileName == "":
          texFileName =  os.path.splitext(os.path.basename(filepath))[0]
     else: 
          texFileName = context.scene.saSettings.texFileName
     
     texListPointer = int("0x" + context.scene.saSettings.texListPointer, 0)
     debug(" Texture file name:", texFileName)
     debug(" Tex list pointer:", '{:08X}'.format(texListPointer))
     fileW.wString(texFileName)

     fileW.align(4)

     landTableAddress = fileW.tell()
     labels[texFileName + "_Table"] = landTableAddress

     #landtable info
     fileW.wUShort(len(objects)) # COL count
     if export_format == 'SA1LVL':
          fileW.wUShort(0) # anim count (unused rn)
          fileW.wUInt(0x8) # landtable flags - 8 determines that PVM/GVM's should be used
          fileW.wFloat(context.scene.saSettings.drawDistance) # Draw Distance
          fileW.wUInt(COLaddress) # geometry address
          fileW.wUInt(0) # animation address (unused rn)
          fileW.wUInt(texFileNameAddr) # texture file name address
          fileW.wUInt(texListPointer) # texture list pointer (usually handled by mod)
          fileW.wFloat(0) # unknown2
          fileW.wFloat(0) # unknown3
     else:
          fileW.wUShort(len(vObjects)) # visual col count
          fileW.wULong(0) # gap
          fileW.wFloat(context.scene.saSettings.drawDistance) # Draw Distance
          fileW.wUInt(COLaddress) # geometry address
          fileW.wUInt(0) # animation address (unused rn)
          fileW.wUInt(texFileNameAddr) # (texFileNameAddr) texture file name address
          fileW.wUInt(texListPointer) # texture list pointer (usually handled by mod)

     labelsAddress = fileW.tell()
     fileW.seek(8, 0) # go to the location of the model properties addrees
     fileW.wUInt(landTableAddress) # and write the address
     fileW.wUInt(labelsAddress)
     fileW.seek(0,2) # then return back to the end

     common.writeMethaData(fileW, labels, context.scene)

     fileW.close()

     # remove the temporary objects
     if not export_format == 'SA1LVL':
          for o in temp:
               bpy.data.objects.remove(o)


     return {'FINISHED'}