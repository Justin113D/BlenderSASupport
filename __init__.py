# meta info
bl_info = {
    "name": "SA Model Formats support",
    "author": "Justin113D",
    "version": (0,8,9),
    "blender": (2, 80, 0),
    "location": "File > Import/Export",
    "description": "Import/Exporter for the SA Models Formats. For any questions, contact me via Discord: Justin113D#1927",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "file_MDL" in locals():
        importlib.reload(file_MDL)
    if "file_LVL" in locals():
        importlib.reload(file_LVL)
    if "format_BASIC" in locals():
        importlib.reload(format_BASIC)
    if "format_GC" in locals():
        importlib.reload(format_GC)
    if "format_CHUNK" in locals():
        importlib.reload(format_CHUNK)
    if "strippifier" in locals():
        importlib.reload(strippifier)
    if "fileHelper" in locals():
        importlib.reload(fileHelper)
    if "enums" in locals():
        importlib.reload(enums)
    if "common" in locals():
        importlib.reload(common)

import bpy
import os
from . import fileHelper, common
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    EnumProperty,
    StringProperty
    )
from bpy_extras.io_utils import ExportHelper, ImportHelper#, path_reference_mode
from typing import List, Dict, Union, Tuple

class TOPBAR_MT_SA_export(bpy.types.Menu):
    '''The export submenu in the export menu'''
    bl_label = "SA Formats"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Export as...")
        layout.operator("export_scene.sa1mdl")
        layout.operator("export_scene.sa2mdl")
        layout.operator("export_scene.sa2bmdl")
        layout.separator()
        layout.operator("export_scene.sa1lvl")
        layout.operator("export_scene.sa2lvl")
        layout.operator("export_scene.sa2blvl")

# export operators

def removeFile() -> None:
    '''Removes the currently assigned temporary export file'''

    # get the export file (its set from outside this script, so for some reason it only works with the __init__ in front of it)
    fileW = __init__.exportedFile
    # if the file is assigned, close and remove it
    if fileW is not None:
        fileW.close()
        os.remove(fileW.filepath)
        __init__.exportedFile = None

def exportFile(op, mdl: bool, context, **keywords):
    '''Exports the '''
    try:
        if mdl:
            out = file_MDL.write(context, **keywords)
        else:
            out = file_LVL.write(context, **keywords)
    except (strippifier.TopologyError, common.ExportError) as e:
        op.report({'WARNING'}, "Export stopped!\n" + str(e))
        removeFile()
        return {'CANCELLED'}
    except Exception as e:
        removeFile()
        raise e

    # moving and renaming the temporary file
    # Note: this is also removing the file that existed before
    fileW = __init__.exportedFile
    filepath = keywords["filepath"]
    if(os.path.isfile(filepath)):
        os.remove(filepath)
    os.rename(fileW.filepath, filepath)

    return {'FINISHED'}

class ExportSA1MDL(bpy.types.Operator, ExportHelper):
    """Export objects into an SA1 model file"""
    bl_idname = "export_scene.sa1mdl"
    bl_label = "SA1 model (.sa1mdl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa1mdl"

    filter_glob: StringProperty(
        default="*.sa1mdl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_MDL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
        keywords["export_format"] = 'SA1'
        return exportFile(self, True, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportSA2MDL(bpy.types.Operator, ExportHelper):
    """Export objects into an SA2 model file"""
    bl_idname = "export_scene.sa2mdl"
    bl_label = "SA2 model (.sa2mdl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa2mdl"

    filter_glob: StringProperty(
        default="*.sa2mdl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_MDL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
        keywords["export_format"] = 'SA2'
        return exportFile(self, True, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportSA2BMDL(bpy.types.Operator, ExportHelper):
    """Export objects into an SA2B model file"""
    bl_idname = "export_scene.sa2bmdl"
    bl_label = "SA2B model (.sa2bmdl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa2bmdl"

    filter_glob: StringProperty(
        default="*.sa2bmdl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_MDL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
        keywords["export_format"] = 'SA2B'
        return exportFile(self, True, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportSA1LVL(bpy.types.Operator, ExportHelper):
    """Export scene into an SA1 level file"""
    bl_idname = "export_scene.sa1lvl"
    bl_label = "SA1 level (.sa1lvl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa1lvl"

    filter_glob: StringProperty(
        default="*.sa1lvl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_LVL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
        keywords["export_format"] = 'SA1'
        return exportFile(self, False, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportSA2LVL(bpy.types.Operator, ExportHelper):
    """Export scene into an SA2 level file"""
    bl_idname = "export_scene.sa2lvl"
    bl_label = "SA2 level (.sa2lvl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa2lvl"

    filter_glob: StringProperty(
        default="*.sa2lvl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_LVL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
        keywords["export_format"] = 'SA2'
        return exportFile(self, False, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportSA2BLVL(bpy.types.Operator, ExportHelper):
    """Export scene into an SA2B level file"""
    bl_idname = "export_scene.sa2blvl"
    bl_label = "SA2B level (.sa2blvl)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".sa2blvl"

    filter_glob: StringProperty(
        default="*.sa2blvl;",
        options={'HIDDEN'},
        )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
        )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = False,
        )

    def execute(self, context):
        from . import file_LVL
        keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))

        keywords["export_format"] = 'SA2B'
        return exportFile(self, False, context, **keywords)

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        layout.alignment = 'RIGHT'

        layout.prop(self, "global_scale")
        layout.prop(self, "use_selection")
        layout.prop(self, "apply_modifs")
        layout.separator()
        layout.prop(self, "console_debug_output")

class ExportPAK(bpy.types.Operator, ExportHelper):
    """Imports any sonic adventure texture file"""
    bl_idname = "export_texture.pak"
    bl_label = "Export as PAK (SA2)"

    def execute(self, context):
        return {'FINISHED'}

class ExportPVMX(bpy.types.Operator, ExportHelper):
    """Imports any sonic adventure texture file"""
    bl_idname = "export_texture.pvmx"
    bl_label = "Export as PVMX (SADX)"

    def execute(self, context):
        return {'FINISHED'}

# import operators

class ImportMDL(bpy.types.Operator, ImportHelper):
    """Imports any sonic adventure mdl file"""
    bl_idname = "import_scene.mdl"
    bl_label = "Sonic Adv. model (.*mdl)"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(
        default="*.sa1mdl;*.sa2mdl;*.sa2bmdl;",
        options={'HIDDEN'},
        )

    console_debug_output: BoolProperty(
            name = "Console Output",
            description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
            default = False,
            )

    def execute(self, context):
        from . import file_MDL

        return file_MDL.read(context, self.filepath, self.console_debug_output)

class ImportLVL(bpy.types.Operator, ImportHelper):
    """Imports any sonic adventure lvl file"""
    bl_idname = "import_scene.lvl"
    bl_label = "Sonic Adv. level (.*lvl)"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(
        default="*.sa1lvl;*.sa2lvl;*.sa2blvl;",
        options={'HIDDEN'},
        )

    console_debug_output: BoolProperty(
            name = "Console Output",
            description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
            default = False,
            )

    def execute(self, context):
        from . import file_LVL

        return file_LVL.read(context, self.filepath, self.console_debug_output)

class ImportTexFile(bpy.types.Operator, ImportHelper):
    """Imports any sonic adventure texture file"""
    bl_idname = "import_texture.tex"
    bl_label = "Import SA tex file"

    filter_glob: StringProperty(
        default="*.pak;*.gvm;*.pvm;*.pvmx;*.txt",
        options={'HIDDEN'},
        )

    def stop(self):
        self.report({'WARNING'}, "File not a valid texture file!")
        return {'CANCELLED'}

    def execute(self, context):
        import os
        extension = os.path.splitext(self.filepath)[1]
        if extension == '.txt':
            #reading all lines from the index file
            content: List[str] = None
            with open(self.filepath) as f:
                content = f.readlines()
            folder = os.path.dirname(self.filepath)
            textures: List[Tuple[int, str]] = list()

            # validating index file
            for c in content:
                c = c.strip().split(',')
                if len(c) != 2:
                    return self.stop()
                try:
                    gIndex = int(c[0])
                except:
                    return self.stop()
                texturePath = folder + "\\" + c[1]
                if not os.path.isfile(texturePath):
                    return self.stop()
                textures.append((gIndex, texturePath))

            bpy.ops.scene.sacleartexturelist()
            texList = context.scene.saSettings.textureList
            for i, t in textures:
                img = None
                for image in bpy.data.images:
                    if image.filepath == t:
                        img = image
                        break
                if img is None:
                    img = bpy.data.images.load(t)
                img.use_fake_user = True
                tex = texList.add()
                tex.globalID = i
                tex.name = os.path.splitext(os.path.basename(t))[0]
                tex.image = img



        return {'FINISHED'}

# operators

class StrippifyTest(bpy.types.Operator):
    '''An operator for test-strippifying a model'''
    bl_idname = "object.strippifytest"
    bl_label = "Strippify (testing)"
    bl_description = "Strippifies the active model object"

    doConcat: BoolProperty(
        name = "Concat",
        description="Combines all strips into one big strip",
        default=False
        )

    doSwaps: BoolProperty(
        name = "Utilize Swapping",
        description = "Utilizes swapping when creating strips, which can result in a smaller total strip count",
        default = False
        )

    raiseTopoError: BoolProperty(
        name = "Raise Topo Error",
        description = "Raise Topo Error if any occur",
        default = False
        )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if obj is None or not isinstance(obj.data, bpy.types.Mesh):
            print("active object not a mesh")
            return {'FINISHED'}

        ob_for_convert = obj.original
        me = ob_for_convert.to_mesh(preserve_all_data_layers=True)
        common.trianglulateMesh(me)

        # creating the index list
        indexList = [0] * len(me.polygons) * 3

        for i, p in enumerate(me.polygons):
            for j, li in enumerate(p.loop_indices):
                indexList[i * 3 + j] = me.loops[li].vertex_index

        # strippifying it
        from . import strippifier
        stripf = strippifier.Strippifier()
        try:
            indexStrips = stripf.Strippify(indexList, doSwaps = self.doSwaps, concat = self.doConcat, raiseTopoError=self.raiseTopoError)
        except strippifier.TopologyError as e:
            self.report({'WARNING'}, "Topology error!\n" + str(e))
            return {'CANCELLED'}


        empty = bpy.data.objects.new(obj.data.name + "_str", None)
        context.collection.objects.link(empty)
        for i, s in enumerate(indexStrips):
            # making them lists so blender can use them

            verts = dict()
            for p in s:
                verts[p] = me.vertices[p].co

            indexList = list()
            rev = True
            for j in range(0, len(s)-2):
                if rev:
                    p = [s[j+1], s[j], s[j+2]]
                else:
                    p = [s[j], s[j+1], s[j+2]]
                indexList.append(p)
                rev = not rev

            keys = list(verts.keys())
            indexList = [[keys.index(i) for i in l] for l in indexList]
            verts = list(verts.values())

            mesh = bpy.data.meshes.new(name = obj.data.name + "_str_" + str(i))
            mesh.from_pydata(verts, [], indexList)
            meObj = bpy.data.objects.new(mesh.name, object_data = mesh)
            context.collection.objects.link(meObj)
            meObj.parent = empty

        return {'FINISHED'}

class ArmatureFromObjects(bpy.types.Operator):
    '''Generates an armature based on the selected node and its child hierarchy'''
    bl_idname = "object.armaturefromobjects"
    bl_label = "Armature from objects"
    bl_description = "Generate an armature from object. Select the parent of all objects, which will represent the root"

    @classmethod
    def addChildren(cls, parent, result, resultMeshes):
        if parent.type == 'MESH':
            resultMeshes.append(len(result))
        result.append(parent)

        for c in parent.children:
            ArmatureFromObjects.addChildren(c, result, resultMeshes)

    def execute(self, context):

        if len(context.selected_objects) == 0 or bpy.context.object.mode != 'OBJECT':
            return {'CANCELLED'}
        active = context.active_object

        objects = list()
        meshes = list()

        ArmatureFromObjects.addChildren(active, objects, meshes)

        zfillSize = max(2, len(str(len(meshes))))

        if len(objects) == 1:
            return {'CANCELLED'}

        armature = bpy.data.armatures.new("ARM_" + active.name)
        armatureObj = bpy.data.objects.new("ARM_" + active.name, armature)
        armatureObj.parent = active.parent
        armatureObj.matrix_local = active.matrix_local
        globalMatrix = active.matrix_world

        context.scene.collection.objects.link(armatureObj)

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = armatureObj
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        edit_bones = armatureObj.data.edit_bones
        boneMap = dict()
        bones = objects[1:]


        for b in bones:
            boneName = b.name
            bone = edit_bones.new(b.name)
            bone.layers[0] = True
            bone.head = (0,0,0)
            bone.tail = (1,0,0)
            bone.matrix = globalMatrix.inverted() @ b.matrix_world

            if b.parent in bones:
                bone.parent = boneMap[b.parent]
            boneMap[b] = bone

        bpy.ops.object.mode_set(mode='OBJECT')
        meshCount = 0

        for i in meshes:
            boneObject = objects[i]

            meshCopy = boneObject.data.copy()
            meshCopy.name = "Mesh_" + str(meshCount).zfill(zfillSize)
            meshObj = boneObject.copy()
            meshObj.name = meshCopy.name
            meshObj.data = meshCopy
            context.scene.collection.objects.link(meshObj)

            meshObj.parent = armatureObj
            meshObj.matrix_local = globalMatrix.inverted() @ boneObject.matrix_world

            bpy.ops.object.mode_set(mode='OBJECT')
            meshObj.select_set(True, view_layer=context.view_layer)
            bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)

            modif = meshObj.modifiers.new("deform", 'ARMATURE')
            modif.object = armatureObj

            group = meshObj.vertex_groups.new(name=boneObject.name)
            group.add([v.index for v in meshCopy.vertices], 1, 'ADD')

            meshCount += 1
            meshObj.select_set(False, view_layer=context.view_layer)





        return {'FINISHED'}

class AddTextureSlot(bpy.types.Operator):
    bl_idname = "scene.saaddtexturesslot"
    bl_label="Add texture"
    bl_description="Adds texture to the texture list"


    def execute(self, context):
        settings = context.scene.saSettings

        # getting next usable global id
        ids = list()
        for t in settings.textureList:
            ids.append(t.globalID)
        ids.sort(key=lambda x: x)
        globalID = -1
        for i, index in enumerate(ids):
            if i != index:
                globalID = i
                break
        if globalID == -1:
            globalID = len(settings.textureList)

        # creating texture
        tex = settings.textureList.add()
        #tex.image_user
        settings.active_texture_index = len(settings.textureList) -1

        tex.name = "Texture"
        tex.globalID = globalID

        return {'FINISHED'}

class RemoveTextureSlot(bpy.types.Operator):
    bl_idname = "scene.saremovetexturesslot"
    bl_label="Remove texture"
    bl_description="Removes the selected texture from the texture list"

    def execute(self, context):
        settings = context.scene.saSettings
        settings.textureList.remove(settings.active_texture_index)

        settings.active_texture_index -= 1
        if len(settings.textureList) == 0:
            settings.active_texture_index = -1
        elif settings.active_texture_index < 0:
            settings.active_texture_index = 0

        return {'FINISHED'}

class MoveTextureSlot(bpy.types.Operator):
    bl_idname = "scene.samovetexturesslot"
    bl_label="Move texture"
    bl_info="Moves texture slot in list"

    direction: EnumProperty(
        name="Direction",
        items=( ('UP',"up","up"),
                ('DOWN',"down","down"), )
        )

    def execute(self, context):
        settings = context.scene.saSettings
        newIndex = settings.active_texture_index + (-1 if self.direction == 'UP' else 1)
        if not (newIndex == -1 or newIndex >= len(settings.textureList)):
            if settings.correct_Material_Textures:
                for m in bpy.data.materials:
                    props: SAMaterialSettings = m.saSettings
                    if props.b_TextureID == newIndex:
                        props.b_TextureID = settings.active_texture_index
                    elif props.b_TextureID == settings.active_texture_index:
                        props.b_TextureID = newIndex

            settings.textureList.move(settings.active_texture_index, newIndex)

            settings.active_texture_index = newIndex
        return {'FINISHED'}

class ClearTextureList(bpy.types.Operator):
    bl_idname = "scene.sacleartexturelist"
    bl_label="Clear list"
    bl_info="Removes all entries from the list"

    def execute(self, context):
        settings = context.scene.saSettings
        settings.active_texture_index = -1

        for t in settings.textureList:
            if t.image is not None:
                t.image.use_fake_user = False


        settings.textureList.clear()
        return {'FINISHED'}

class AutoNameTextures(bpy.types.Operator):
    bl_idname = "scene.saautonametexlist"
    bl_label="Autoname entries"
    bl_info="Renames all entries to the assigned texture"

    def execute(self, context):
        texList = context.scene.saSettings.textureList

        for t in texList:
            if t.image is not None:
                t.name = os.path.splitext(t.image.name)[0]
            else:
                t.name = "Texture"
        return {'FINISHED'}

class UpdateMaterials(bpy.types.Operator):
    bl_idname = "scene.saupdatemats"
    bl_label="Update Materials"
    bl_info="Sets material nodetrees and variables of all selected objects to imitate how they would look in sadx/sa2"

    def addDriver(inputSocket, scene, path, entry = -1):
        #curve = inputSocket.driver_add("default_value")
        #driver = curve.driver
        #driver.type = 'AVERAGE'
        #variable = driver.variables.new()
        #variable.targets[0].id_type = 'SCENE'
        #variable.targets[0].id = scene
        #variable.targets[0].data_path = "saSettings." + path + ("" if entry == -1 else "[" + str(entry) + "]")
        #curve.update()
        inputSocket.default_value = getattr(scene.saSettings, path) if entry == -1 else getattr(scene.saSettings, path)[entry]

    def execute(self, context):
        # remove old trees

        ng = bpy.data.node_groups

        n = ng.find("UV Tiling")
        if n > -1:
            ng.remove(ng[n])

        n = ng.find("SAShader")
        if n > -1:
            ng.remove(ng[n])

        n = ng.find("EnvMap")
        if n > -1:
            ng.remove(ng[n])

        # now reload them them
        directory = os.path.dirname(os.path.realpath(__file__)) + "\\Shaders.blend\\NodeTree\\"
        bpy.ops.wm.append(filename="UV Tiling", directory=directory)
        bpy.ops.wm.append(filename="SAShader", directory=directory)
        bpy.ops.wm.append(filename="EnvMap", directory=directory)

        tilingGroup = ng[ng.find("UV Tiling")]
        saShaderGroup = ng[ng.find("SAShader")]
        envMapGroup = ng[ng.find("EnvMap")]

        # Drivers dont update automatically when set like this, and i cant find a way to update them through python, so we'll just set them temporarily
        nd = saShaderGroup.nodes
        lightDirNode: bpy.types.ShaderNodeCombineXYZ = nd[nd.find("LightDir")]
        lightColNode: bpy.types.ShaderNodeCombineRGB = nd[nd.find("LightCol")]
        ambientColNode: bpy.types.ShaderNodeCombineRGB = nd[nd.find("AmbientCol")]
        displSpecularNode: bpy.types.ShaderNodeValue = nd[nd.find("DisplSpecular")]

        UpdateMaterials.addDriver(lightDirNode.inputs[0], context.scene, "LightDir", 0)
        UpdateMaterials.addDriver(lightDirNode.inputs[1], context.scene, "LightDir", 1)
        UpdateMaterials.addDriver(lightDirNode.inputs[2], context.scene, "LightDir", 2)

        UpdateMaterials.addDriver(lightColNode.inputs[0], context.scene, "LightColor", 0)
        UpdateMaterials.addDriver(lightColNode.inputs[1], context.scene, "LightColor", 1)
        UpdateMaterials.addDriver(lightColNode.inputs[2], context.scene, "LightColor", 2)

        UpdateMaterials.addDriver(ambientColNode.inputs[0], context.scene, "LightAmbientColor", 0)
        UpdateMaterials.addDriver(ambientColNode.inputs[1], context.scene, "LightAmbientColor", 1)
        UpdateMaterials.addDriver(ambientColNode.inputs[2], context.scene, "LightAmbientColor", 2)

        UpdateMaterials.addDriver(displSpecularNode.outputs[0], context.scene, "DisplaySpecular")

        # The materials know whether the shader displays vertex colors based on the object color, its weird i know, but i didnt find any better way
        import math
        for o in context.scene.objects:
            if o.type == 'MESH':
                isNrm = o.data.saSettings.sa2ExportType == 'NRM'
                r = o.color[0]
                rc = bool(math.floor(r * 1000) % 2)

                if isNrm and rc:
                    r = (math.floor(r * 1000) + (1 if r < 1 else (-1))) / 1000.0
                elif not isNrm and not rc:
                    r = (math.floor(r * 1000) + ((-1) if r > 0 else 1)) / 1000.0
                o.color[0] = r

        # now its time to set all of the materials
        for m in bpy.data.materials:
            #creating an settings nodes
            mProps = m.saSettings
            m.use_nodes = True
            tree: bpy.types.NodeTree = m.node_tree
            nodes = tree.nodes
            nodes.clear()

            out = nodes.new("ShaderNodeOutputMaterial")
            saShader = nodes.new("ShaderNodeGroup")
            saShader.node_tree = saShaderGroup

            saShader.inputs[2].default_value = mProps.b_Diffuse
            saShader.inputs[3].default_value = mProps.b_Diffuse[3]
            saShader.inputs[4].default_value = mProps.b_ignoreLighting

            saShader.inputs[5].default_value = mProps.b_Specular
            saShader.inputs[6].default_value = mProps.b_Specular[3]
            saShader.inputs[7].default_value = mProps.b_Exponent
            saShader.inputs[8].default_value = mProps.b_ignoreSpecular

            saShader.inputs[9].default_value = mProps.b_Ambient
            saShader.inputs[10].default_value = mProps.b_Ambient[3]
            saShader.inputs[11].default_value = mProps.b_ignoreAmbient

            saShader.inputs[12].default_value = mProps.b_flatShading

            saShader.location = (-200, 0)

            tree.links.new(out.inputs[0], saShader.outputs[0])

            if mProps.b_useTexture:
                try:
                    img = context.scene.saSettings.textureList[mProps.b_TextureID]
                except IndexError:
                    img = None

                if img is not None:
                    tex = nodes.new("ShaderNodeTexImage")
                    tex.image = img.image
                    tex.interpolation = 'Closest' if mProps.b_texFilter == 'POINT' else 'Smart'
                    tex.location = (-500, 0)
                    tree.links.new(tex.outputs[0], saShader.inputs[0])
                    tree.links.new(tex.outputs[1], saShader.inputs[1])


                    uvNode = nodes.new("ShaderNodeGroup")
                    if mProps.b_useEnv:
                        uvNode.node_tree = envMapGroup
                    else:
                        uvNode.node_tree = tilingGroup

                        uvNode.inputs[1].default_value = mProps.b_mirrorV
                        uvNode.inputs[2].default_value = mProps.b_mirrorU
                        uvNode.inputs[3].default_value = mProps.b_clampV
                        uvNode.inputs[4].default_value = mProps.b_clampU

                        uvSrc = nodes.new("ShaderNodeUVMap")
                        uvSrc.location = (-900, 0)
                        tree.links.new(uvSrc.outputs[0], uvNode.inputs[0])
                    tree.links.new(uvNode.outputs[0], tex.inputs[0])
                    uvNode.location = (-700, 0)
                else:
                    saShader.inputs[0].default_value = (1,0,1,1)

            if mProps.b_useAlpha:
                m.blend_method = context.scene.saSettings.viewportAlphaType
                m.alpha_threshold = context.scene.saSettings.viewportAlphaCutoff
            else:
                m.blend_method = 'OPAQUE'
            m.shadow_method = 'NONE'
            m.use_backface_culling = not mProps.b_doubleSided

        # setting the color management
        context.scene.display_settings.display_device = 'sRGB'
        context.scene.view_settings.view_transform = 'Standard'
        context.scene.view_settings.look = 'None'
        context.scene.view_settings.exposure = 0
        context.scene.view_settings.gamma = 1
        context.scene.sequencer_colorspace_settings.name = 'sRGB'
        context.scene.view_settings.use_curve_mapping = False
        return {'FINISHED'}


#  quick edit

def qeUpdate(context, newValue):
    '''Updates all selected objects with according properties'''

    qEditSettings = context.scene.saSettings
    objects = context.selected_objects

    # If the user specified to change materials...
    if context.scene.saSettings.useMatEdit:
        matQProps = context.scene.saSettings.matQProps

        mats = []
        for o in objects:
            if o.type == 'MESH':
                for m in o.data.materials:
                    if m not in mats:
                        mats.append(m)

        for m in mats:
            matProps: SAMaterialSettings = m.saSettings

            for p in dir(matQProps):
                if not p.startswith("b_") and not p.startswith("gc_"):
                    continue

                a = getattr(matQProps, p)
                if type(a) is bool:
                    setattr(matProps, p, newValue)

            if qEditSettings.b_apply_diffuse and newValue:
                matProps.b_Diffuse = matQProps.b_Diffuse

            if qEditSettings.b_apply_specular and newValue:
                matProps.b_Specular = matQProps.b_Specular

            if qEditSettings.b_apply_Ambient and newValue:
                matProps.b_Ambient = matQProps.b_Ambient

            if qEditSettings.b_apply_specularity and newValue:
                matProps.b_Exponent = matQProps.b_Exponent

            if qEditSettings.b_apply_texID and newValue:
                matProps.b_TextureID = matQProps.b_TextureID

            if qEditSettings.b_apply_filter and newValue:
                matProps.b_texFilter = matQProps.b_texFilter

            if matQProps.b_useAlpha and newValue:
                matProps.b_destAlpha = matQProps.b_destAlpha
                matProps.b_srcAlpha = matQProps.b_srcAlpha

            if qEditSettings.gc_apply_shadowStencil and newValue:
                matProps.gc_shadowStencil = matQProps.gc_shadowStencil

            if qEditSettings.gc_apply_texID and newValue:
                matProps.gc_texCoordID = matQProps.gc_texCoordID

            if qEditSettings.gc_apply_typ and newValue:
                matProps.gc_texGenType = matQProps.gc_texGenType

            if matQProps.gc_texGenType[0] == 'M':
                if qEditSettings.gc_apply_mtx and newValue:
                    matProps.gc_texMatrixID = matQProps.gc_texMatrixID
                if qEditSettings.gc_apply_src and newValue:
                    matProps.gc_texGenSourceMtx = matQProps.gc_texGenSourceMtx

            elif matQProps.gc_texGenType[0] == 'B':
                if qEditSettings.gc_apply_src and newValue:
                    matProps.gc_texGenSourceBmp = matQProps.gc_texGenSourceBmp

            else: #srtg
                if qEditSettings.gc_apply_src and newValue:
                    matProps.gc_texGenSourceSRTG = matQProps.gc_texGenSourceSRTG

    # If the user specified to change objects...
    if context.scene.saSettings.useObjEdit:
        for o in objects:

            objProps = o.saSettings
            for k, v in SAObjectSettings.defaultDict().items():
                if isinstance(v, bool) and getattr(qEditSettings.objQProps, k):
                    setattr(objProps, k, newValue)

            if qEditSettings.obj_apply_userFlags and newValue:
                objProps.userFlags = qEditSettings.objQProps.userFlags

    # If the user specified to change meshes...
    if context.scene.saSettings.useMeshEdit:

        meshes = list()
        for o in objects:
            if o.type == 'MESH' and o.data not in meshes:
                meshes.append(o.data)

        for m in meshes:
            meshProps = m.saSettings

            if qEditSettings.me_apply_ExportType and newValue:
                meshProps.sa2ExportType = qEditSettings.meshQProps.sa2ExportType

            if qEditSettings.me_apply_addVO and newValue:
                meshProps.sa2IndexOffset = qEditSettings.meshQProps.sa2IndexOffset

class qeUpdateSet(bpy.types.Operator):
    """Quick Material Editor Updater for setting selected field to true"""
    bl_idname = "object.qeset"
    bl_label = "SET"
    bl_description = "Sets the selected QE properties in the materials of all selected objects to TRUE"

    def execute(self, context):
        qeUpdate(context, True)
        return {'FINISHED'}

class qeUpdateUnset(bpy.types.Operator):
    """Quick Material Editor Updater for unsetting selected field to true"""
    bl_idname = "object.qeunset"
    bl_label = "UNSET"
    bl_description = "Sets the selected QE properties in the materials of all selected objects to FALSE"

    def execute(self, context):
        qeUpdate(context, False)
        return {'FINISHED'}

class qeReset(bpy.types.Operator):
    """Quick Material Editor Resetter"""
    bl_idname = "object.qereset"
    bl_label = "Reset"
    bl_description = "Resets quick material editor properties"

    def execute(self, context):

        menuProps: SASettings = context.scene.saSettings

        if menuProps.useMatEdit:
            matProps = context.scene.saSettings.matQProps
            for p in dir(matProps):
                if not p.startswith("b_") and not p.startswith("gc_"):
                    continue

                a = getattr(matProps, p)
                if isinstance(a, bool):
                    setattr(matProps, p, False)

            for p in dir(menuProps):
                if not p.startswith("b_") and not p.startswith("gc_"):
                    continue

                a = getattr(menuProps, p)
                if type(a) is bool:
                    setattr(menuProps, p, False)

        if menuProps.useObjEdit:
            objProps = context.scene.saSettings.objQProps
            for k, v in SAObjectSettings.defaultDict().items():
                if isinstance(v, bool):
                    setattr(objProps, k, False)

            menuProps.obj_apply_userFlags = False

        if menuProps.useMeshEdit:
            menuProps.me_apply_addVO = False
            menuProps.me_apply_ExportType = False


        return {'FINISHED'}

class qeInvert(bpy.types.Operator):
    """Quick Material Editor Inverter"""
    bl_idname = "object.qeinvert"
    bl_label = "Invert"
    bl_description = "Inverts quick material editor properties"

    def execute(self, context):
        menuProps = context.scene.saSettings

        if menuProps.useMatEdit:
            matProps = context.scene.saSettings.matQProps
            for p in dir(matProps):
                if not p.startswith("b_") and not p.startswith("gc_"):
                    continue

                a = getattr(matProps, p)
                if type(a) is bool:
                    setattr(matProps, p, not a)

            for p in dir(menuProps):
                if not p.startswith("b_") and not p.startswith("gc_"):
                    continue

                a = getattr(menuProps, p)
                if type(a) is bool:
                    setattr(menuProps, p, not a)

        if menuProps.useObjEdit:
            objProps = context.scene.saSettings.objQProps
            for k, v in SAObjectSettings.defaultDict().items():
                if isinstance(v, bool):
                    setattr(objProps, k, not getattr(objProps, k))

            menuProps.obj_apply_userFlags = not menuProps.obj_apply_userFlags

        if menuProps.useMeshEdit:
            menuProps.me_apply_addVO = not menuProps.me_apply_addVO
            menuProps.me_apply_ExportType = not menuProps.me_apply_ExportType


        return {'FINISHED'}

# property groups

class SASettings(bpy.types.PropertyGroup):
    """Information global to the scene"""

    author: StringProperty(
        name="Author",
        description="The creator of this file",
        default="",
        )

    description: StringProperty(
        name="Description",
        description="A Description of the file contents",
        default="",
        )

    texFileName: StringProperty(
        name="Tex-File name",
        description="The name of the texture file specified in the landtable info (lvl format)",
        default=""
        )

    landtableName: StringProperty(
        name="Name",
        description="The label for the landtable in the file. If empty, the filename will be used",
        default=""
        )

    texListPointer: StringProperty(
        name="Texture List Pointer (hex)",
        description="Used for when replacing a stage and its textures",
        default="0"
        )

    drawDistance: FloatProperty(
        name="Draw Distance",
        description="How far the camera has to be away from an object to render (only sa2lvl)",
        default=3000
        )

    doubleSidedCollision: BoolProperty(
        name="Double sided collision",
        description="Enables double sided collision detection. This is supposed to be used as a failsafe for people unexperienced with how normals work",
        default=True
        )

    active_texture_index: IntProperty(
        name="Active texture index",
        description="Index of active item in texture list",
        default=-1
        )

    correct_Material_Textures: BoolProperty(
        name="Update Materials",
        description="If a texture is being moved, the material's texture id's will be adjusted so that every material keeps the same texture",
        default=True
        )

    LightDir: FloatVectorProperty(
        name="Light Direction",
        description="The direction of the emulated light (seen from the y+ axis)",
        subtype='DIRECTION',
        default=(0.0,0.0,1.0),
        min = 0,
        max = 1,
        size=3
        )

    LightColor: FloatVectorProperty(
        name="Light Color",
        description="The color of the emulated light",
        default=(1.0,1.0,1.0),
        subtype='COLOR_GAMMA',
        min = 0,
        max = 1,
        size=3
        )

    LightAmbientColor: FloatVectorProperty(
        name="Light Ambient Color",
        description="The ambient color of the emulated light",
        default=(0.3,0.3,0.3),
        subtype='COLOR_GAMMA',
        min = 0,
        max = 1,
        size=3
        )

    DisplaySpecular: BoolProperty(
        name="Viewport Specular",
        description="Display specular in the blender material view",
        default=True
        )

    viewportAlphaType: EnumProperty(
        name="Viewport Alpha Type",
        description="The Eevee alpha type to display transparent materials",
        items=(('BLEND', "Blend", "The default blending"),
               ('HASHED', "Hashed", "Hashed transparency"),
               ('CLIP', "Clip", "Sharp edges for certain thresholds")),
        default='BLEND'
        )

    viewportAlphaCutoff: FloatProperty(
        name="Viewport blend Cutoff",
        description="Cutoff value for the eevee alpha cutoff transparency",
        min = 0,
        max = 1,
        default=0.5
        )

    #panel stuff

    expandedLTPanel: BoolProperty( name="Landtable data", default=False )
    expandedTexturePanel: BoolProperty( name="Texture list", default=False )
    expandedLightingPanel: BoolProperty( name="Lighting data", default=False )

    expandedQEPanel: BoolProperty( name="Quick Edit", default=False )

    useMatEdit: BoolProperty(
        name ="Activate Quick Material Edit",
        description="When active, the Buttons will use and apply the material properties",
        default=False
        )
    expandedMatEdit: BoolProperty(
        name ="Material Quick Edit",
        description="A menu for quickly assigning material properties to mutliple objects",
        default=False
        )

    useObjEdit: BoolProperty(
        name ="Activate Quick Object Edit",
        description="When active, the Buttons will use and apply the object properties",
        default=False
        )
    expandedObjEdit: BoolProperty(
        name ="Object Quick Edit",
        description="A menu for quickly assigning object properties to mutliple objects",
        default=False)

    useMeshEdit: BoolProperty(
        name ="Activate Quick Object Edit",
        description="When active, the Buttons will use and apply the mesh properties",
        default=False
        )
    expandedMeshEdit: BoolProperty(
        name ="Mesh Quick Edit",
        description="A menu for quickly assigning mesh properties to mutliple objects",
        default=False)

    # Quick material edit properties

    b_apply_diffuse: BoolProperty(
        name = "Apply diffuse",
        description="Sets the diffuse of all material when pressing 'Set'",
        default=False
        )

    b_apply_specular: BoolProperty(
        name = "Apply specular",
        description="Sets the specular of all material when pressing 'Set'",
        default=False
        )

    b_apply_Ambient: BoolProperty(
        name = "Apply ambient",
        description="Sets the ambient of all material when pressing 'Set'",
        default=False
        )

    b_apply_specularity: BoolProperty(
        name = "Apply specularity",
        description="Sets the specularity of all material when pressing 'Set'",
        default=False
        )

    b_apply_texID: BoolProperty(
        name = "Apply texture ID",
        description="Sets the texture ID of all selected materials when pressing 'Set'",
        default=False
        )

    b_apply_filter: BoolProperty(
        name = "Apply filter type",
        description="Sets the filter type of all selected materials when pressing 'Set'",
        default=False
        )

    gc_apply_shadowStencil: BoolProperty(
        name = "Apply shadow stencil",
        description="Sets the shadow stencil of all selected materials when pressing 'Set'",
        default=False
        )

    gc_apply_texID: BoolProperty(
        name = "Apply Texcoord ID",
        description="Sets the Texcoord ID of all selected materials when pressing 'Set'",
        default=False
        )

    gc_apply_typ: BoolProperty(
        name = "Apply Type",
        description="Sets the generation Type of all selected materials when pressing 'Set'",
        default=False
        )

    gc_apply_mtx: BoolProperty(
        name = "Apply Matrix",
        description="Sets the Matrix of all selected materials when pressing 'Set'",
        default=False
        )

    gc_apply_src: BoolProperty(
        name = "Apply Source",
        description="Sets the generation Source of all selected materials when pressing 'Set'",
        default=False
        )

    # quick object edit properties

    obj_apply_userFlags: BoolProperty(
        name = "Apply Custom Flags",
        description="Sets the userflags of all selected objects when pressing 'Set'",
        default=False
        )

    me_apply_ExportType: BoolProperty(
        name = "Apply Export Type",
        description="Sets the export type of all selected objects when pressing 'Set'",
        default=False
        )

    me_apply_addVO: BoolProperty(
        name = "Apply Vertex Offset",
        description="Sets the additional vertex offset of all selected objects when pressing 'Set'",
        default=False
        )

class SAEditPanelSettings(bpy.types.PropertyGroup):
    """Menu settings for the material edit menus determining which menu should be visible"""

    expandedBMipMap: BoolProperty( name="Mipmap Distance Multiplicator", default=False )
    expandedBTexFilter: BoolProperty( name="Texture Filtering", default=False )
    expandedBUV: BoolProperty( name = "UV Properties", default=False )
    expandedBGeneral: BoolProperty( name = "General Properties", default=False )

    expandedGC: BoolProperty( name="SA2B specific", default=False )
    expandedGCTexGen: BoolProperty( name = "Generate texture coords", default=False )

    expandedSA1obj: BoolProperty( name ="Object SA1 Properties", default=False)
    expandedSA2obj: BoolProperty( name ="Object SA2 Properties", default=False)

class SAObjectSettings(bpy.types.PropertyGroup):
    """hosts all properties to edit the surface flags of a COL"""
    # used in both
    isCollision: BoolProperty(
        name="Is Collision",
        description="Whether the object can be collided with at all. \n Also determines whether the mesh is invisible in sa2",
        default=False
        )

    solid: BoolProperty(
        name="Solid",
        description="Whether the character can collide with the model",
        default=True
        )

    water: BoolProperty(
        name="Water",
        description="The model will act like water",
        default=False
        )

    cannotLand: BoolProperty(
        name="Cannot land",
        description="Whether you can stand on the model",
        default=False
        )

    diggable: BoolProperty(
        name="Diggable",
        description="Whether the treasure hunter characters can dig on the models surface",
        default=False
        )

    unclimbable: BoolProperty(
        name="Unclimbable",
        description="Whether the treasure hunter characters can climb on the models surface",
        default=False
        )

    footprints: BoolProperty(
        name="Footprints",
        description="The character will leave footprints behind when walking on this models surface",
        default=False
        )

    hurt: BoolProperty(
        name="Hurt",
        description="The character will take damage when coming in contact with this model",
        default=False
        )

    isVisible: BoolProperty(
        name="isVisible",
        description="Whether the model is Visible (only matters in sa1)",
        default=False
        )

    userFlags: StringProperty(
        name="User flags",
        description="User determined flags (for experiments, otherwise usage is unadvised)",
        default="0"
        )

    # sa2 only

    standOnSlope: BoolProperty(
        name="Stand on slope",
        description="Whether the character wont slide down when standing on stairs",
        default=False
        )

    water2: BoolProperty(
        name="Water 2",
        description="The same as water, but different!",
        default=False
        )

    noShadows: BoolProperty(
        name="No shadows",
        description="No shadows will be displayed on mesh",
        default=False
        )

    noFog: BoolProperty(
        name="No fog",
        description="Disables fog for this object",
        default=False
        )

    unknown24: BoolProperty(
        name="Unknown 24",
        description="No idea what this does",
        default=False
        )

    unknown29: BoolProperty(
        name="Unknown 29",
        description="No idea what this does",
        default=False
        )

    unknown30: BoolProperty(
        name="Unknown 30",
        description="No idea what this does",
        default=False
        )

    # sa1 only

    noFriction: BoolProperty(
        name="No friction",
        description="Whether the model has friction",
        default=False
        )

    noAcceleration: BoolProperty(
        name="no acceleration",
        description="If the acceleration of the character should stay when interacting with the model",
        default=False
        )

    increasedAcceleration: BoolProperty(
        name="Increased acceleration",
        description="Whether the acceleration of the character should be raised when interacting with the model",
        default=False
        )


    @classmethod
    def defaultDict(cls) -> dict:
        d = dict()
        d["isCollision"] = False
        d["solid"] = False
        d["water"] = False
        d["cannotLand"] = False
        d["diggable"] = False
        d["unclimbable"] = False
        d["hurt"] = False
        d["isVisible"] = False
        d["userFlags"] = common.hex4(0)

        d["standOnSlope"] = False
        d["water2"] = False
        d["noShadows"] = False
        d["noFog"] = False
        d["unknown24"] = False
        d["unknown29"] = False
        d["unknown30"] = False

        d["noFriction"] = False
        d["noAcceleration"] = False
        d["increasedAcceleration"] = False
        d["footprints"] = False
        return d

    def toDictionary(self) -> dict:
        d = dict()
        d["isCollision"] = self.isCollision
        d["solid"] = self.solid
        d["water"] = self.water
        d["cannotLand"] = self.cannotLand
        d["diggable"] = self.diggable
        d["unclimbable"] = self.unclimbable
        d["hurt"] = self.hurt
        d["isVisible"] = self.isVisible
        d["userFlags"] = self.userFlags

        d["standOnSlope"] = self.standOnSlope
        d["water2"] = self.water2
        d["noShadows"] = self.noShadows
        d["noFog"] = self.noFog
        d["unknown24"] = self.unknown24
        d["unknown29"] = self.unknown29
        d["unknown30"] = self.unknown30

        d["noFriction"] = self.noFriction
        d["noAcceleration"] = self.noAcceleration
        d["increasedAcceleration"] = self.increasedAcceleration
        d["footprints"] = self.footprints

        return d

    def fromDictionary(self, d: dict):
        self.isCollision = d["isCollision"]
        self.solid = d["solid"]
        self.water = d["water"]
        self.cannotLand = d["cannotLand"]
        self.diggable = d["diggable"]
        self.unclimbable = d["unclimbable"]
        self.hurt = d["hurt"]
        self.isVisible = d["isVisible"]
        self.userFlags = d["userFlags"]
        self.footprints = d["footprints"]

        self.standOnSlope = d["standOnSlope"]
        self.water2 = d["water2"]
        self.noShadows = d["noShadows"]
        self.noFog = d["noFog"]
        self.unknown24 = d["unknown24"]
        self.unknown29 = d["unknown29"]
        self.unknown30 = d["unknown30"]

        self.noFriction = d["noFriction"]
        self.noAcceleration = d["noAcceleration"]
        self.increasedAcceleration = d["increasedAcceleration"]

class SAMaterialSettings(bpy.types.PropertyGroup):
    """Hosts all of the material data necessary for exporting"""
    # sa1 properties

    b_Diffuse: FloatVectorProperty(
        name = "Diffuse Color",
        description="Color of the material",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        )

    b_Specular: FloatVectorProperty(
        name = "Specular Color",
        description="Color of the Specular",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        )

    b_Ambient : FloatVectorProperty(
        name = "Ambient Color",
        description="Ambient Color (SA2 only)",
        subtype='COLOR_GAMMA',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        )

    b_Exponent: FloatProperty(
        name = "Specularity",
        description= "Specular Precision on the material",
        default=1.0,
        min = 0, max = 1
        )

    b_TextureID: IntProperty(
        name = "Texture ID",
        description= "ID of the texture in the PVM/GVM to use",
        default=0,
        min = 0
        )

    # flags:
    # mipmap distance multiplier
    b_d_025: BoolProperty(
        name="+ 0.25",
        description="adds 0.25 to the mipmap distance multiplier",
        default=False
        )

    b_d_050: BoolProperty(
        name="+ 0.5",
        description="adds 0.5 to the mipmap distance multiplier",
        default=False
        )

    b_d_100: BoolProperty(
        name="+ 1",
        description="adds 1 to the mipmap distance multiplier",
        default=False
        )

    b_d_200: BoolProperty(
        name="+ 2",
        description="adds 2 to the mipmap distance multiplier",
        default=False
        )

    # texture filtering

    b_use_Anisotropy: BoolProperty(
        name="Anisotropy",
        description="Enable Anisotropy for the texture of the material",
        default=True
        )

    b_texFilter: EnumProperty(
        name="Filter Type",
        description="The texture filter",
        items=( ('POINT', 'Point', "no filtering"),
                ('BILINEAR', 'Bilinear', "Bilinear Filtering"),
                ('TRILINEAR', 'Trilinear', "Trilinear Filtering"),
                ('BLEND', 'Blend', "Bi- and Trilinear Filtering blended together")
            ),
        default='BILINEAR'
        )

    # uv properties

    b_clampV: BoolProperty(
        name="Clamp V",
        description="The V channel of the mesh UVs always stays between 0 and 1",
        default=False
        )

    b_clampU: BoolProperty(
        name="Clamp U",
        description="The U channel of the mesh UVs always stays between 0 and 1",
        default=False
        )

    b_mirrorV: BoolProperty(
        name="Mirror V",
        description="The V channel of the mesh UVs mirrors every time it reaches a multiple of 1",
        default=False
        )

    b_mirrorU: BoolProperty(
        name="Mirror U",
        description="The V channel of the mesh UVs mirrors every time it reaches a multiple of 1",
        default=False
        )

    # general material properties
    b_ignoreSpecular: BoolProperty(
        name="Ignore Specular",
        description="Removes the specularity from the material",
        default=False
        )

    b_useAlpha: BoolProperty(
        name="Use Alpha",
        description="Utilizes the alpha channel of the color and texture to render transparency",
        default=False
        )

    b_srcAlpha: EnumProperty(
        name = "Source Alpha",
        description="Destination Alpha",
        items=( ('ZERO', 'Zero', ""),
                ('ONE', 'One', ""),
                ('OTHER', 'Other', ""),
                ('INV_OTHER', 'Inverted other', ""),
                ('SRC', 'Source', ""),
                ('INV_SRC', 'Inverted source', ""),
                ('DST', 'Destination', ""),
                ('INV_DST', 'Inverted destination', ""),
              ),
        default='SRC'
        )

    b_destAlpha: EnumProperty(
        name = "Destination Alpha",
        description="Destination Alpha",
        items=( ('ZERO', 'Zero', ""),
                ('ONE', 'One', ""),
                ('OTHER', 'Other', ""),
                ('INV_OTHER', 'Inverted other', ""),
                ('SRC', 'Source', ""),
                ('INV_SRC', 'Inverted source', ""),
                ('DST', 'Destination', ""),
                ('INV_DST', 'Inverted destination', ""),
              ),
        default='INV_SRC'
        )

    b_useTexture: BoolProperty(
        name="Use Texture",
        description="Uses the texture references in the properties",
        default=True
        )

    b_useEnv: BoolProperty(
        name="Environment mapping",
        description="Uses normal mapping instead of the uv coordinates, to make the texture face the camera (equivalent to matcaps)",
        default=False
        )

    b_doubleSided: BoolProperty(
        name="Disable Backface culling",
        description="Renders both sides of the mesh",
        default=True
        )

    b_flatShading: BoolProperty(
        name="Flat Shading",
        description="Render without shading",
        default=False
        )

    b_ignoreLighting: BoolProperty(
        name="Ignore Lighting",
        description="Ignores lighting as a whole when rendering",
        default=False
        )

    b_ignoreAmbient: BoolProperty(
        name="Ignore Ambient",
        description="Ignores ambient as a whole when rendering (SA2 Only)",
        default=False
        )

    b_unknown: BoolProperty(
        name="unknown",
        description="to be figured out",
        default = False
        )

    # GC features (parameters)

    gc_shadowStencil: IntProperty(
        name="Shadow Stencil",
        description="shadow stencil",
        min=0, max=0xF,
        default=1
        )

    # texcoord gen

    gc_texMatrixID: EnumProperty(
        name = "Matrix ID",
        description="If gentype is matrix, then this property defines which user defined matrix to use",
        items=( ('MATRIX0', 'Matrix 0', ""),
                ('MATRIX1', 'Matrix 1', ""),
                ('MATRIX2', 'Matrix 2', ""),
                ('MATRIX3', 'Matrix 3', ""),
                ('MATRIX4', 'Matrix 4', ""),
                ('MATRIX5', 'Matrix 5', ""),
                ('MATRIX6', 'Matrix 6', ""),
                ('MATRIX7', 'Matrix 7', ""),
                ('MATRIX8', 'Matrix 8', ""),
                ('MATRIX9', 'Matrix 9', ""),
                ('IDENTITY', 'Identity', "")
            ),
        default='IDENTITY'
        )

    gc_texGenSourceMtx: EnumProperty(
        name = "Generation Source - Matrix",
        description="Which data of the mesh to use when generating the uv coords (Matrix)",
        items=( ('POSITION', 'Position', ""),
                ('NORMAL', 'Normal', ""),
                ('BINORMAL', 'Binormal', ""),
                ('TANGENT', 'Tangent', ""),
                ('TEX0', 'Tex0', ""),
                ('TEX1', 'Tex1', ""),
                ('TEX2', 'Tex2', ""),
                ('TEX3', 'Tex3', ""),
                ('TEX4', 'Tex4', ""),
                ('TEX5', 'Tex5', ""),
                ('TEX6', 'Tex6', ""),
                ('TEX7', 'Tex7', ""),
            ),
        default='TEX0'
        )

    gc_texGenSourceBmp: EnumProperty(
        name = "Generation Source - Bump",
        description="Which uv map of the mesh to use when generating the uv coords (Bump)",
        items=( ('TEXCOORD0', 'TexCoord0', ""),
                ('TEXCOORD1', 'TexCoord1', ""),
                ('TEXCOORD2', 'TexCoord2', ""),
                ('TEXCOORD3', 'TexCoord3', ""),
                ('TEXCOORD4', 'TexCoord4', ""),
                ('TEXCOORD5', 'TexCoord5', ""),
                ('TEXCOORD6', 'TexCoord6', ""),
            ),
        default='TEXCOORD0'
        )

    gc_texGenSourceSRTG: EnumProperty(
        name = "Generation Source - SRTG",
        description="Which color slot of the mesh to use when generating the uv coords (SRTG)",
        items=( ('COLOR0', 'Color0', ""),
                ('COLOR1', 'Color1', ""),
            ),
        default='COLOR0'
        )

    gc_texGenType: EnumProperty(
        name = "Generation Type",
        description="Which function to use when generating the coords",
        items=( ('MTX3X4', 'Matrix 3x4', ""),
                ('MTX2X4', 'Matrix 2x4', ""),
                ('BUMP0', 'Bump 0', ""),
                ('BUMP1', 'Bump 1', ""),
                ('BUMP2', 'Bump 2', ""),
                ('BUMP3', 'Bump 3', ""),
                ('BUMP4', 'Bump 4', ""),
                ('BUMP5', 'Bump 5', ""),
                ('BUMP6', 'Bump 6', ""),
                ('BUMP7', 'Bump 7', ""),
                ('SRTG', 'SRTG', ""),
            ),
        default='MTX2X4'
        )

    gc_texCoordID: EnumProperty(
        name = "Texcoord ID (output slot)",
        description="Determines in which slot the generated coordinates should be saved, so that they can be used",
        items = ( ('TEXCOORD0', 'TexCoord0', ""),
                  ('TEXCOORD1', 'TexCoord1', ""),
                  ('TEXCOORD2', 'TexCoord2', ""),
                  ('TEXCOORD3', 'TexCoord3', ""),
                  ('TEXCOORD4', 'TexCoord4', ""),
                  ('TEXCOORD5', 'TexCoord5', ""),
                  ('TEXCOORD6', 'TexCoord6', ""),
                  ('TEXCOORD7', 'TexCoord7', ""),
                  ('TEXCOORDMAX', 'TexCoordMax', ""),
                  ('TEXCOORDNULL', 'TexCoordNull', ""),
            ),
        default='TEXCOORD0'
        )

    def toDictionary(self) -> dict:
        d = dict()
        d["b_Diffuse"] = self.b_Diffuse
        d["b_Specular"] = self.b_Specular
        d["b_Ambient"] = self.b_Ambient
        d["b_Exponent"] = self.b_Exponent
        d["b_TextureID"] = self.b_TextureID
        d["b_d_025"] = self.b_d_025
        d["b_d_050"] = self.b_d_050
        d["b_d_100"] = self.b_d_100
        d["b_d_200"] = self.b_d_200
        d["b_use_Anisotropy"] = self.b_use_Anisotropy
        d["b_texFilter"] = self.b_texFilter
        d["b_clampV"] = self.b_clampV
        d["b_clampU"] = self.b_clampU
        d["b_mirrorV"] = self.b_mirrorV
        d["b_mirrorU"] = self.b_mirrorU
        d["b_ignoreSpecular"] = self.b_ignoreSpecular
        d["b_useAlpha"] = self.b_useAlpha
        d["b_srcAlpha"] = self.b_srcAlpha
        d["b_destAlpha"] = self.b_destAlpha
        d["b_useTexture"] = self.b_useTexture
        d["b_useEnv"] = self.b_useEnv
        d["b_doubleSided"] = self.b_doubleSided
        d["b_flatShading"] = self.b_flatShading
        d["b_ignoreLighting"] = self.b_ignoreLighting
        d["b_ignoreAmbient"] = self.b_ignoreAmbient
        d["b_unknown"] = self.b_unknown
        d["gc_shadowStencil"] = self.gc_shadowStencil
        d["gc_texMatrixID"] = self.gc_texMatrixID
        d["gc_texGenSourceMtx"] = self.gc_texGenSourceMtx
        d["gc_texGenSourceBmp"] = self.gc_texGenSourceBmp
        d["gc_texGenSourceSRTG"] = self.gc_texGenSourceSRTG
        d["gc_texGenType"] = self.gc_texGenType
        d["gc_texCoordID"] = self.gc_texCoordID
        return d

    def readMatDict(self, d):
        self.b_Diffused = d["b_Diffuse"]
        self.b_Specular = d["b_Specular"]
        self.b_Ambient = d["b_Ambient"]
        self.b_Exponent = d["b_Exponent"]
        self.b_TextureID = d["b_TextureID"]
        self.b_d_025 = d["b_d_025"]
        self.b_d_050 = d["b_d_050"]
        self.b_d_100 = d["b_d_100"]
        self.b_d_200 = d["b_d_200"]
        self.b_use_Anisotropy = d["b_use_Anisotropy"]
        self.b_texFilter = d["b_texFilter"]
        self.b_clampV = d["b_clampV"]
        self.b_clampU = d["b_clampU"]
        self.b_mirrorV = d["b_mirrorV"]
        self.b_mirrorU = d["b_mirrorU"]
        self.b_ignoreSpecular = d["b_ignoreSpecular"]
        self.b_useAlpha = d["b_useAlpha"]
        self.b_srcAlpha = d["b_srcAlpha"]
        self.b_destAlpha = d["b_destAlpha"]
        self.b_useTexture = d["b_useTexture"]
        self.b_useEnv = d["b_useEnv"]
        self.b_doubleSided = d["b_doubleSided"]
        self.b_flatShading = d["b_flatShading"]
        self.b_ignoreLighting = d["b_ignoreLighting"]
        self.b_ignoreAmbient = d["b_ignoreAmbient"]
        self.b_unknown = d["b_unknown"]
        self.gc_shadowStencil = d["gc_shadowStencil"]
        self.gc_texMatrixID = d["gc_texMatrixID"]
        self.gc_texGenSourceMtx = d["gc_texGenSourceMtx"]
        self.gc_texGenSourceBmp = d["gc_texGenSourceBmp"]
        self.gc_texGenSourceSRTG = d["gc_texGenSourceSRTG"]
        self.gc_texGenType = d["gc_texGenType"]
        self.gc_texCoordID = d["gc_texCoordID"]

    @classmethod
    def getDefaultMatDict(cls) -> Dict[str, Union[str, bool, List[int]]]:
        d = dict()
        d["b_Diffuse"] = (1.0, 1.0, 1.0, 1.0)
        d["b_Specular"] = (1.0, 1.0, 1.0, 1.0)
        d["b_Ambient"] =(1.0, 1.0, 1.0, 1.0)
        d["b_Exponent"] = 1
        d["b_TextureID"] = 0
        d["b_d_025"] = False
        d["b_d_050"] = False
        d["b_d_100"] = False
        d["b_d_200"] = False
        d["b_use_Anisotropy"] = False
        d["b_texFilter"] = 'BILINEAR'
        d["b_clampV"] = False
        d["b_clampU"] = False
        d["b_mirrorV"] = False
        d["b_mirrorU"] = False
        d["b_ignoreSpecular"] = False
        d["b_useAlpha"] = False
        d["b_srcAlpha"] = 'SRC'
        d["b_destAlpha"] = 'INV_SRC'
        d["b_useTexture"] = True
        d["b_useEnv"] = False
        d["b_doubleSided"] = True
        d["b_flatShading"] = False
        d["b_ignoreLighting"] = False
        d["b_ignoreAmbient"] = False
        d["b_unknown"] = False
        d["gc_shadowStencil"] = 1
        d["gc_texMatrixID"] = 'IDENTITY'
        d["gc_texGenSourceMtx"] = 'TEX0'
        d["gc_texGenSourceBmp"] = 'TEXCOORD0'
        d["gc_texGenSourceSRTG"] = 'COLOR0'
        d["gc_texGenType"] = 'MTX2X4'
        d["gc_texCoordID"] = 'TEXCOORD0'
        return d

class SAMeshSettings(bpy.types.PropertyGroup):
    '''Settings used by the exporters for specific meshes'''

    sa2ExportType: EnumProperty(
        name = "SA2 Export Type",
        description = "Determines which vertex data should be written for sa2",
        items = ( ('VC', "Colors", "Only vertex colors are gonna be written"),
                  ('NRM', "Normals", "Only normals are gonna be written"),
                ),
        default = 'NRM'
        )

    sa2IndexOffset: IntProperty(
        name = "(SA2) Additional Vertex Offset",
        description = "Additional vertex offset for specific model mods",
        min=0, max = 32767,
        default = 0
    )

def texUpdate(self, context):
    settings = context.scene.saSettings

    # checking if texture object is in list
    index = -1
    tList = settings.textureList
    for i, t in enumerate(tList):
        if t == self:
            index = i
            break

    if index == -1:
        print("Texture slot not found in list")
        return

    if self.name != self.prevName:
        if self.name.isspace() or self.name == "":
            self.name = self.prevName
            return

        names = list()
        for t in tList:
            if t == self:
                continue
            names.append(t.name)

        if self.name not in names:
            self.prevName = self.name
            return

        # check if the texture has a number tag
        splits = self.name.split(".")
        isNumberTag = len(splits) > 1 and splits[-1].isdecimal()

        if isNumberTag:
            name = self.name[:len(self.name) - 1 - len(splits[-1])]
            number = int(splits[-1])
        else:
            name = self.name
            number = 0

        numbers = list()

        for t in context.scene.saSettings.textureList:
            if t == self:
                continue
            splits = t.name.split(".")
            if len(splits) > 1 and splits[-1].isdecimal():
                tname = t.name[:len(t.name) - 1 - len(splits[-1])]
                if tname == name:
                    numbers.append(int(splits[-1]))
            elif t.name == name:
                numbers.append(0)


        numbers.sort(key=lambda x: x)
        found = False
        for i, n in enumerate(numbers):
            if i != n:
                found = True
                break
        if not found:
            i += 1
        self.name = name + "." + str(i).zfill(3)

    if self.globalID != self.prevGlobalID:
        ids = list()
        for t in settings.textureList:
            if t == self:
                continue
            ids.append(t.globalID)

        if self.globalID not in ids:
            self.prevGlobalID = self.globalID
            return

        ids.sort(key=lambda x: x)
        current = 0
        if self.globalID == self.prevGlobalID - 1: # if value was just reduced by one
            found = -1
            for index in ids:
                if current < index:
                    current = index
                    t = index - 1
                    if t < self.prevGlobalID:
                        found = t
                    else:
                        break

                current += 1

            if found == -1:
                self.globalID = self.prevGlobalID
            else:
                self.globalID = found
        elif self.globalID == self.prevGlobalID + 1: # if value was just raise by one
            found = -1
            oldIndex = ids[0]
            for index in ids:
                if current < index:
                    current = index
                    t = oldIndex + 1
                    if t > self.prevGlobalID:
                        found = t
                        break
                oldIndex = index
                current += 1

            if found == -1:
                self.globalID = ids[-1] + 1
            else:
                self.globalID = found
        else:  # everything else
            closestFree = -1
            oldindex = ids[0]
            for index in ids:
                if current < index:
                    current = index
                    if index < self.globalID:
                        t = index - 1
                    else:
                        t = oldindex + 1

                    if abs(t - self.globalID) < abs(closestFree - self.globalID) or closestFree == -1:
                        closestFree = t
                    elif abs(t - self.globalID) > abs(closestFree - self.globalID):
                        break
                    elif self.globalID < self.prevGlobalID:
                        closestFree = t
                        break

                oldindex = index
                current += 1

            if closestFree == -1:
                closestFree = self.prevGlobalID

            self.globalID = closestFree

class SATexture(bpy.types.PropertyGroup):

    name: StringProperty(
        name = "Slot name",
        description="The name of the slot",
        maxlen=0x20,
        default="",
        update=texUpdate
        )

    prevName: StringProperty(
        name="Previous name",
        maxlen=0x20,
        default=""
        )

    globalID: IntProperty(
        name="Global ID",
        description="The global texture id in the texture file",
        default=0,
        min = 0,
        update=texUpdate
        )

    prevGlobalID: IntProperty(
        name="Previous Global ID",
        min = 0,
        default=0,
        )

# panels

def propAdv(layout, label, prop1, prop1Name, prop2, prop2Name, autoScale = False, qe = False):
    '''For quick edit properties, to put simply'''

    if not autoScale:
        split = layout.split(factor=0.5)
        row = split.row()
        row.alignment='LEFT'
        if qe:
            row.prop(prop2, prop2Name, text="")
        row.label(text=label)
        split.prop(prop1, prop1Name, text="")

    else:
        row = layout.row()
        row.alignment='LEFT'
        if qe:
            row.prop(prop2, prop2Name, text="")
        row.label(text=label)
        row.alignment='EXPAND'
        row.prop(prop1, prop1Name, text="")

def drawMaterialPanel(layout, menuProps, matProps, qe = False):

    sProps = bpy.context.scene.saSettings

    menu = layout
    menu.alignment = 'RIGHT'

    propAdv(menu, "Diffuse Color:", matProps, "b_Diffuse", sProps, "b_apply_diffuse", qe = qe)
    propAdv(menu, "Specular Color:", matProps, "b_Specular", sProps, "b_apply_specular", qe = qe)
    propAdv(menu, "Ambient Color:", matProps, "b_Ambient", sProps, "b_apply_Ambient", qe = qe)
    propAdv(menu, "Specular Strength:", matProps, "b_Exponent", sProps, "b_apply_specularity", qe = qe)
    propAdv(menu, "Texture ID:", matProps, "b_TextureID", sProps, "b_apply_texID", qe = qe)

    #mipmap menu
    box = menu.box()
    box.prop(menuProps, "expandedBMipMap",
        icon="TRIA_DOWN" if menuProps.expandedBMipMap else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedBMipMap:
        box.prop(matProps, "b_d_025")
        box.prop(matProps, "b_d_050")
        box.prop(matProps, "b_d_100")
        box.prop(matProps, "b_d_200")
        mmdm = 0.25 if matProps.b_d_025 else 0
        mmdm += 0.5 if matProps.b_d_050 else 0
        mmdm += 1 if matProps.b_d_100 else 0
        mmdm += 2 if matProps.b_d_200 else 0
        box.label(text = "Total multiplicator: " + str(mmdm))

    #texture filtering menu
    box = menu.box()
    box.prop(menuProps, "expandedBTexFilter",
        icon="TRIA_DOWN" if menuProps.expandedBTexFilter else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedBTexFilter:
        box.prop(matProps, "b_use_Anisotropy")
        propAdv(box, "Filter Type:", matProps, "b_texFilter", sProps, "b_apply_filter", qe = qe)

    # uv properties
    box = menu.box()
    box.prop(menuProps, "expandedBUV",
        icon="TRIA_DOWN" if menuProps.expandedBUV else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedBUV:
        box.prop(matProps, "b_clampU")
        box.prop(matProps, "b_clampV")
        box.prop(matProps, "b_mirrorV")
        box.prop(matProps, "b_mirrorU")

    box = menu.box()
    box.prop(menuProps, "expandedBGeneral",
        icon="TRIA_DOWN" if menuProps.expandedBGeneral else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedBGeneral:
        box.prop(matProps, "b_useTexture")
        box.prop(matProps, "b_useEnv")
        box.prop(matProps, "b_useAlpha")
        if matProps.b_useAlpha:
            split = box.split(factor= 0.5)
            split.label(text ="Source Alpha:")
            split.prop(matProps, "b_srcAlpha", text = "")

            split = box.split(factor= 0.5)
            split.label(text ="Destination Alpha:")
            split.prop(matProps, "b_destAlpha", text = "")
        box.prop(matProps, "b_doubleSided")
        box.prop(matProps, "b_ignoreSpecular")
        box.prop(matProps, "b_ignoreLighting")
        box.prop(matProps, "b_ignoreAmbient")
        box.prop(matProps, "b_flatShading")
        box.prop(matProps, "b_unknown")

    box = menu.box()
    box.prop(menuProps, "expandedGC",
        icon="TRIA_DOWN" if menuProps.expandedGC else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedGC:

        propAdv(box, "Shadow Stencil:", matProps, "gc_shadowStencil", sProps, "gc_apply_shadowStencil", qe = qe)

        box.prop(menuProps, "expandedGCTexGen",
            icon="TRIA_DOWN" if menuProps.expandedGCTexGen else "TRIA_RIGHT",
            emboss = False
            )
        if menuProps.expandedGCTexGen:
            propAdv(box, "Output slot:", matProps, "gc_texCoordID", sProps, "gc_apply_texID", qe = qe)
            propAdv(box, "Generation Type:", matProps, "gc_texGenType", sProps, "gc_apply_typ", qe = qe)

            if matProps.gc_texGenType[0] == 'M': #matrix
                propAdv(box, "Matrix ID:", matProps, "gc_texMatrixID", sProps, "gc_apply_mtx", qe = qe)
                propAdv(box, "Source:", matProps, "gc_texGenSourceMtx", sProps, "gc_apply_src", qe = qe)

            elif matProps.gc_texGenType[0] == 'B': # Bump
                propAdv(box, "Source:", matProps, "gc_texGenSourceBmp", sProps, "gc_apply_src", qe = qe)

            else: #SRTG
                propAdv(box, "Source:", matProps, "gc_texGenSourceSRTG", sProps, "gc_apply_src", qe = qe)

def drawObjectPanel(layout: bpy.types.UILayout, menuProps, objProps, qe = False):

    sProps = bpy.context.scene.saSettings

    layout.prop(objProps, "isCollision")
    if objProps.isCollision:
        layout.prop(objProps, "isVisible")

    # sa1 flags
    box = layout.box()
    box.prop(menuProps, "expandedSA1obj",
        icon="TRIA_DOWN" if menuProps.expandedSA1obj else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedSA1obj and (objProps.isCollision or qe):
        box.prop(objProps, "solid")
        box.prop(objProps, "water")
        box.prop(objProps, "noFriction")
        box.prop(objProps, "noAcceleration")
        box.prop(objProps, "cannotLand")
        box.prop(objProps, "increasedAcceleration")
        box.prop(objProps, "diggable")
        box.prop(objProps, "unclimbable")
        box.prop(objProps, "hurt")

    if menuProps.expandedSA1obj and ((not objProps.isCollision or objProps.isCollision and objProps.isVisible) or qe):
        box.prop(objProps, "footprints")

    # sa2 flags

    box = layout.box()
    box.prop(menuProps, "expandedSA2obj",
        icon="TRIA_DOWN" if menuProps.expandedSA2obj else "TRIA_RIGHT",
        emboss = False
        )

    if menuProps.expandedSA2obj and (objProps.isCollision or qe):
        box.prop(objProps, "solid")
        box.prop(objProps, "water")
        box.prop(objProps, "standOnSlope")
        box.prop(objProps, "diggable")
        box.prop(objProps, "unclimbable")
        box.prop(objProps, "footprints")
        box.prop(objProps, "hurt")
        box.prop(objProps, "cannotLand")
        box.prop(objProps, "water2")

    if menuProps.expandedSA2obj and ((not objProps.isCollision or objProps.isCollision and objProps.isVisible) or qe):
        box.prop(objProps, "noShadows")
        box.prop(objProps, "noFog")

    if menuProps.expandedSA2obj and (objProps.isCollision or qe):
        box.separator()
        box.label(text="Experimental")
        box.prop(objProps, "unknown24")
        box.prop(objProps, "unknown29")
        box.prop(objProps, "unknown30")

    propAdv(layout, "Custom (hex):  0x", objProps, "userFlags", sProps, "obj_apply_userFlags", qe = qe)

def drawMeshPanel(layout: bpy.types.UILayout, meshProps, qe = False):

    sProps = bpy.context.scene.saSettings
    propAdv(layout, "Export Type (SA2)", meshProps, "sa2ExportType", sProps, "me_apply_ExportType", qe = qe)
    propAdv(layout, "+ Vertex Offset (SA2)", meshProps, "sa2IndexOffset", sProps, "me_apply_addVO", qe = qe)

class SCENE_UL_SATexList(bpy.types.UIList):

    def draw_item(self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index, flt_flag):
        split = layout.split(factor=0.6)
        split.prop(item, "name", text="", emboss=False, icon_value=icon, icon= 'X' if item.image == None else 'CHECKMARK')
        split.prop(item, "globalID", text=str(index), emboss=False, icon_value=icon)

class SAObjectPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_saProperties"
    bl_label = "SA Object Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        objProps = context.active_object.saSettings
        menuProps = context.scene.saSettings.editorSettings

        drawObjectPanel(layout, menuProps, objProps)

class SAMeshPanel(bpy.types.Panel):
    bl_idname = "MESH_PT_saProperties"
    bl_label = "SA Mesh Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        meshprops = context.active_object.data.saSettings

        drawMeshPanel(layout, meshprops)

class SAMaterialPanel(bpy.types.Panel):
    bl_idname = "MATERIAL_PT_saProperties"
    bl_label = "SA Material Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"


    @classmethod
    def poll(cls, context):
        return (context.active_object.active_material is not None)

    def draw(self, context):
        layout = self.layout
        menuProps = context.scene.saSettings.editorSettings
        matProps = context.active_object.active_material.saSettings

        drawMaterialPanel(layout, menuProps, matProps)

class SCENE_MT_Texture_Context_Menu(bpy.types.Menu):
    bl_label = "Texture list specials"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.saSettings

        layout.prop(settings, "correct_Material_Textures")
        layout.operator(AutoNameTextures.bl_idname)
        layout.operator(ClearTextureList.bl_idname)
        layout.separator()
        layout.operator(ImportTexFile.bl_idname)
        layout.separator()
        layout.operator(ExportPVMX.bl_idname)
        layout.operator(ExportPAK.bl_idname)

class SAScenePanel(bpy.types.Panel):
    bl_idname = "SCENE_PT_saProperties"
    bl_label = "SA file info"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.saSettings

        layout.prop(settings, "author")
        layout.prop(settings, "description")

        layout.separator(factor=2)

        box = layout.box()
        box.prop(settings, "expandedLTPanel",
            icon="TRIA_DOWN" if settings.expandedLTPanel else "TRIA_RIGHT",
            emboss = False
            )
        if settings.expandedLTPanel:
            box.prop(settings, "landtableName")

            split = box.split(factor=0.5)
            split.label(text="Draw Distance:")
            split.prop(settings, "drawDistance", text="")

            row = box.row()
            row.alignment='LEFT'
            row.label(text="TexListPtr:  0x")
            row.alignment='EXPAND'
            row.prop(settings, "texListPointer", text="")

            box.prop(settings, "doubleSidedCollision")

        box = layout.box()
        box.prop(settings, "expandedTexturePanel",
            icon="TRIA_DOWN" if settings.expandedTexturePanel else "TRIA_RIGHT",
            emboss = False
            )

        if settings.expandedTexturePanel:
            split = box.split(factor=0.4)
            split.label(text="Tex-file name")
            split.prop(settings, "texFileName", text="")
            row = box.row()
            row.template_list("SCENE_UL_SATexList", "", settings, "textureList", settings, "active_texture_index")

            col = row.column()
            col.operator(AddTextureSlot.bl_idname, icon='ADD', text="")
            col.operator(RemoveTextureSlot.bl_idname, icon='REMOVE', text="")

            col.separator()
            col.operator(MoveTextureSlot.bl_idname, icon='TRIA_UP', text="").direction = 'UP'
            col.operator(MoveTextureSlot.bl_idname, icon='TRIA_DOWN', text="").direction = 'DOWN'
            col.menu("SCENE_MT_Texture_Context_Menu", icon='DOWNARROW_HLT', text="")

            if settings.active_texture_index >= 0:
                tex = settings.textureList[settings.active_texture_index]
                box.prop_search(tex, "image", bpy.data, "images")

        box = layout.box()
        box.prop(settings, "expandedLightingPanel",
            icon="TRIA_DOWN" if settings.expandedLightingPanel else "TRIA_RIGHT",
            emboss = False
            )

        if settings.expandedLightingPanel:
            split = box.split(factor=0.5)
            split.label(text="Light Direction")
            split.prop(settings, "LightDir", text="")

            split = box.split(factor=0.5)
            split.label(text="Light Color")
            split.prop(settings, "LightColor", text="")

            split = box.split(factor=0.5)
            split.label(text="Ambient Light")
            split.prop(settings, "LightAmbientColor", text="")

            box.separator(factor=0.5)
            box.prop(settings, "DisplaySpecular")
            split = box.split(factor=0.5)
            split.label(text="Viewport blend mode")
            split.prop(settings, "viewportAlphaType", text="")
            if settings.viewportAlphaType == 'CUT':
                box.prop(settings, "viewportAlphaCutoff")


class SA3DPanel(bpy.types.Panel):
    bl_idname = 'MESH_PT_satools'
    bl_label = 'SA Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout

        settings = context.scene.saSettings

        outerBox = layout.box()

        outerBox.prop(settings, "expandedQEPanel",
            icon="TRIA_DOWN" if settings.expandedQEPanel else "TRIA_RIGHT",
            emboss = False
            )

        if settings.expandedQEPanel:
            split = outerBox.split(factor=0.5)
            split.operator(qeUpdateSet.bl_idname)
            split.operator(qeUpdateUnset.bl_idname)
            outerBox.separator(factor=0.1)
            split = outerBox.split(factor=0.5)
            split.operator(qeReset.bl_idname)
            split.operator(qeInvert.bl_idname)

            box = outerBox.box()

            row = box.row()
            row.prop(settings, "useMatEdit", text="")
            row.prop(settings, "expandedMatEdit",
                icon="TRIA_DOWN" if settings.expandedMatEdit else "TRIA_RIGHT",
                emboss = False
                )

            if settings.expandedMatEdit:
                box.separator()
                drawMaterialPanel(box, settings.qEditorSettings, settings.matQProps, qe=True)
                box.separator()

            box = outerBox.box()

            row = box.row()
            row.prop(settings, "useObjEdit", text="")
            row.prop(settings, "expandedObjEdit",
                icon="TRIA_DOWN" if settings.expandedObjEdit else "TRIA_RIGHT",
                emboss = False
                )

            if settings.expandedObjEdit:
                box.separator()
                drawObjectPanel(box, settings.qEditorSettings, settings.objQProps, qe=True)
                box.separator()

            box = outerBox.box()

            row = box.row()
            row.prop(settings, "useMeshEdit", text="")
            row.prop(settings, "expandedMeshEdit",
                icon="TRIA_DOWN" if settings.expandedMeshEdit else "TRIA_RIGHT",
                emboss = False
                )

            if settings.expandedMeshEdit:
                box.separator()
                drawMeshPanel(box, settings.meshQProps, qe=True)
                box.separator()

        layout.operator(UpdateMaterials.bl_idname)
        layout.separator()
        layout.operator(ArmatureFromObjects.bl_idname)
        layout.operator(StrippifyTest.bl_idname)

def menu_func_exportsa(self, context):
    self.layout.menu("TOPBAR_MT_SA_export")

def menu_func_importsa(self, context):
    self.layout.operator(ImportMDL.bl_idname)
    self.layout.operator(ImportLVL.bl_idname)

classes = (
    TOPBAR_MT_SA_export,
    ExportSA1MDL,
    ExportSA2MDL,
    ExportSA2BMDL,
    ExportSA1LVL,
    ExportSA2LVL,
    ExportSA2BLVL,
    ExportPAK,
    ExportPVMX,
    ImportMDL,
    ImportLVL,
    ImportTexFile,

    StrippifyTest,
    ArmatureFromObjects,
    AddTextureSlot,
    RemoveTextureSlot,
    MoveTextureSlot,
    ClearTextureList,
    AutoNameTextures,
    UpdateMaterials,

    qeReset,
    qeInvert,
    qeUpdateSet,
    qeUpdateUnset,

    SAObjectSettings,
    SASettings,
    SAMaterialSettings,
    SAEditPanelSettings,
    SAMeshSettings,
    SATexture,

    SCENE_UL_SATexList,
    SAObjectPanel,
    SAMaterialPanel,
    SCENE_MT_Texture_Context_Menu,
    SAScenePanel,
    SA3DPanel,
    SAMeshPanel,
    )

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    SATexture.image = bpy.props.PointerProperty(type=bpy.types.Image)

    SASettings.editorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
    SASettings.qEditorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
    SASettings.matQProps = bpy.props.PointerProperty(type=SAMaterialSettings)
    SASettings.objQProps = bpy.props.PointerProperty(type=SAObjectSettings)
    SASettings.meshQProps = bpy.props.PointerProperty(type=SAMeshSettings)
    SASettings.textureList = bpy.props.CollectionProperty(
        type=SATexture,
        name="Texture list",
        description= "The textures used by sonic adventure"
        )

    bpy.types.Scene.saSettings = bpy.props.PointerProperty(type=SASettings)
    bpy.types.Object.saSettings = bpy.props.PointerProperty(type=SAObjectSettings)
    bpy.types.Material.saSettings = bpy.props.PointerProperty(type=SAMaterialSettings)
    bpy.types.Mesh.saSettings = bpy.props.PointerProperty(type=SAMeshSettings)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportsa)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_importsa)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportsa)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_importsa)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()