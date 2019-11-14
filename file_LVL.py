import bpy
import os
import mathutils
from . import fileHelper, enums, common, format_BASIC, format_GC, format_CHUNK, __init__

DO = False # Debug out

def hex8(number : int):
    return '{:08x}'.format(number)

def hex16(number : int):
    return '{:016x}'.format(number)

def read(context: bpy.types.Context, filepath: str, console_debug_output: bool):

     global DO
     DO = console_debug_output
     common.DO = DO
     format_BASIC.DO = DO
     format_CHUNK.DO = DO
     format_GC.DO = DO
     if DO:
          os.system("cls")

     fileR = fileHelper.FileReader(filepath)

     if fileR.filepath is None:
          print("no valid filepath")
          return {'CANCELLED'}

     indicator = enums.LVLFormatIndicator( fileR.rULong(0) & ~0xFF00000000000000 )
     fileVersion = fileR.rByte(7)

     if indicator == enums.LVLFormatIndicator.SA1LVL:
          file_format = 'SA1'
     elif indicator == enums.LVLFormatIndicator.SA2LVL:
          file_format = 'SA2'
     elif indicator == enums.LVLFormatIndicator.SA2BLVL:
          file_format = 'SA2B'
     else:
          print("no Valid file")
          return {'CANCELLED'}

     if DO:
          print(" == Starting LVL file reading ==")
          print("  File:", filepath)
          print("  Format:", file_format, "version", fileVersion)
          print("  - - - - - -\n")

     labels: Dict[int, str] = dict()

     if fileVersion < 2:
          if fileVersion == 1:
               tmpAddr = fileR.rUInt(0xC)
               if tmpAddr != 0:
                    addr = fileR.rInt(tmpAddr)
                    while addr != -1:
                         labels[fileR.rUInt(tmpAddr)] = fileR.rString(tmpAddr + 4)
                         tmpAddr += 8
                         addr = fileR.rInt(tmpAddr)
     else:
          tmpAddr = fileR.rUInt(0xC)
          if tmpAddr != 0:
               finished = False
               while not finished:
                    cnkType = enums.Chunktypes(fileR.rUInt(tmpAddr))
                    cnkSize = fileR.rUInt(tmpAddr + 4)
                    cnkNext = tmpAddr + 8 + cnkSize

                    if fileVersion == 2:
                         cnkBase = 0
                    else:
                         cnkBase = tmpAddr + 8

                    tmpAddr += 8

                    if cnkType == enums.Chunktypes.Label: # labels
                         while fileR.rLong(tmpAddr) != -1:
                         labels[fileR.rUInt(tmpAddr)] = fileR.rString(cnkBase + fileR.rUInt(tmpAddr + 4))
                         tmpAddr += 8
                    elif cnkType == enums.Chunktypes.Author: # Author name
                         context.scene.saSettings.author = fileR.rString(tmpAddr)
                    elif cnkType == enums.Chunktypes.Description: # File description
                         context.scene.saSettings.description = fileR.rString(tmpAddr)
                    elif cnkType == enums.Chunktypes.Tool and DO: # Tool
                         print("Tool metadata found")
                    elif cnkType == enums.Chunktypes.Texture and DO: # texture
                         print("Texture metadata found")
                    elif cnkType == enums.Chunktypes.End: # end
                         finished = True
                    else: # everything else
                         if DO:
                         print("invalid Chunk type:", cnkType.value)

                    tmpAddr = cnkNext

     if DO:
          if len(labels) > 0:
               print("Labels:", len(labels))
               for l in labels.keys():
                    print(hex8(l), labels[l])
          if context.scene.saSettings.author != "":
               print("Author:", context.scene.saSettings.author)
          if context.scene.saSettings.description != "":
               print("Description:", context.scene.saSettings.description)
          print("\n")

          print(" == Reading Models ==")

     # get landtable data



def write(context,
         filepath, *,
         export_format,
         use_selection,
         apply_modifs,
         global_scale,
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
     fileW = fileHelper.FileWriter()#filepath=filepath)
     __init__.exportedFile = fileW

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
          print("  File:", filepath)
          print("  Format:", export_format, "version", fileVersion)
          print("  - - - - - -\n")

     # settings placeholders for the
     fileW.wUInt(0) # landtable address
     fileW.wUInt(0) # methadata address
     labels = dict() # for labels methadata
     meshDict = dict()

     from bpy_extras.io_utils import axis_conversion
     global_matrix = (mathutils.Matrix.Scale(global_scale, 4) @ axis_conversion(to_forward='-Z', to_up='Y',).to_4x4())

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
                    mesh.write(fileW, labels, meshDict)
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
                    mesh.write(fileW, labels, meshDict)

          #writing visual meshes
          if export_format == 'SA2':
               if DO:
                    print(" == Writing CHUNK attaches == \n")
               for m in vMeshes:
                    mesh = format_CHUNK.Attach.fromMesh(m, global_matrix, materials)
                    if mesh is not None:
                         mesh.write(fileW, labels, meshDict)
          else:
               if DO:
                    print(" == Writing GC attaches == \n")
               for m in vMeshes:
                    mesh = format_GC.Attach.fromMesh(m, global_matrix, materials)
                    if mesh is not None:
                         mesh.write(fileW, labels, meshDict)

     # writing model data
     ModelData.updateMeshPointer(objects, meshDict)
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
     if context.scene.saSettings.landtableName == "":
          labels[landTableAddress] = os.path.splitext(os.path.basename(filepath))[0]
     else:
          labels[landTableAddress] = context.scene.saSettings.landtableName

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
