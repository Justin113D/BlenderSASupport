# meta info
bl_info = {
    "name": "SA2 Model Formats support",
    "author": "Justin113D",
    "version": (0,0,1),
    "blender": (2, 80, 0),
    "location": "File > Import/Export",
    "description": "Import/Exporter for the SA2 Models Formats. For any questions, contact me via Discord: Justin113D#1927",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "export_sa2mdl" in locals():
        importlib.reload(export_sa2mdl)
    if "export_sa2lvl" in locals():
        importlib.reload(export_sa2lvl)
    if "Strippifier" in locals():
        importlib.reload(Strippifier)
    #if "fileName" in locals():
    #    importlib.reload(fileName)

import bpy
from bpy.props import (
        StringProperty,
        EnumProperty,
        BoolProperty,
        FloatProperty,
        IntProperty,
        )
from bpy_extras.io_utils import (
        #ImportHelper,
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
        )

@orientation_helper(axis_forward='Z', axis_up='Y')    
class ExportSA2MDL(bpy.types.Operator, ExportHelper):
    """Export Objects into an SA2 model file"""
    bl_idname = "export_scene.sa2mdl"
    bl_label = "Export SA2MDL"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(
        default="*.sa2mdl; *.sa2bmdl;",
        options={'HIDDEN'},
        )

    export_format: EnumProperty(
        name="Format",
        description="The Format in which the models should be exported",
        items=( ('SA2BMDL', 'SA2BMDL', "The Gamecube SA2 Format (GC)"),
                ('SA2MDL', 'SA2MDL', "The Default SA2 Format (Chunk)"),
                ('SA1MDL', 'SA1MDL', "The SA1 Format (BASIC)"),
        ),
        default='SA2BMDL',        
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
        default = True,
        )
    
    def execute(self, context):
        from . import export_sa2mdl
        from mathutils import Matrix
        keywords = self.as_keywords(ignore=("global_scale",
                                    "check_existing",
                                    "filter_glob",
                                    ))
        
        global_matrix = (Matrix.Scale(self.global_scale, 4) @
                         axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())
        
        keywords["global_matrix"] = global_matrix
        return export_sa2mdl.load(context, **keywords)

@orientation_helper(axis_forward='Z', axis_up='Y')  
class ExportSA2LVL(bpy.types.Operator, ExportHelper):
    """Export scene into an SA2 level file"""
    bl_idname = "export_scene.sa2lvl"
    bl_label = "Export SA2MDL"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(
        default="*.sa2mdl; *.sa2bmdl;",
        options={'HIDDEN'},
        )

    export_format: EnumProperty(
        name="Format",
        description="The Format in which the models should be exported",
        items=( ('SA2BLVL', 'SA2BLVL', "The Gamecube SA2 Format (GC)"),
                ('SA2LVL', 'SA2LVL', "The Default SA2 Format (Chunk)"),
        ),
        default='SA2BLVL',        
    )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        )

    apply_modifs: BoolProperty(
        name="Apply Modifiers",
        description="Apply active viewport modifiers",
        default=True,
    )

    console_debug_output: BoolProperty(
        name = "Console Output",
        description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
        default = True,
        )
    
    def execute(self, context):
        from . import export_sa2lvl
        from mathutils import Matrix
        keywords = self.as_keywords(ignore=("global_scale",
                                    "check_existing",
                                    "filter_glob",
                                    "axis_forward",
                                    "axis_up",
                                    ))
        
        global_matrix = (Matrix.Scale(self.global_scale, 4) @
                         axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())
        
        keywords["global_matrix"] = global_matrix
        return export_sa2lvl.load(context, **keywords)

class StrippifyTest(bpy.types.Operator):
    bl_idname = "object.strippifytest"
    bl_label = "Strippify (testing)"
    bl_description = "Strippifies the active model object and puts each strip into a new object"

    def mesh_triangulate(self, me):
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED', ngon_method='FIXED')
        bm.to_mesh(me)
        bm.free()

    def execute(self, context):
        import os
        os.system("cls")
        obj = context.active_object
        if obj is None or not isinstance(obj.data, bpy.types.Mesh):
            print("active object not a mesh")
            return {'FINISHED'}

        ob_for_convert = obj.original
        me = ob_for_convert.to_mesh()
        self.mesh_triangulate(me)

        # creating the vertex list
        verts = []
        oIDtodID = [0] * len(me.vertices)
        
        for IDo, vo in enumerate(me.vertices):
            vert = [vo.co.x, vo.co.y, vo.co.z]
            found = -1
            for IDd, vd in enumerate(verts):
                if vert == vd:
                    found = IDd
                    break
            if found == -1:
                verts.append(vert)
                oIDtodID[IDo] = len(verts) - 1
            else:
                oIDtodID[IDo] = found

        # creating the index list
        indexList = [0] * len(me.polygons) * 3

        for i, p in enumerate(me.polygons):
            for j, li in enumerate(p.loop_indices):
                indexList[i * 3 + j] = oIDtodID[me.loops[li].vertex_index]

        doConcat = False

        # strippifying it
        from . import Strippifier
        stripf = Strippifier.Strippifier()
        indexStrips = stripf.seqStrippify(indexList, concat=doConcat)


        if not doConcat:
            empty = bpy.data.objects.new(obj.data.name + "_str", None)
            context.collection.objects.link(empty)           
            for i, s in enumerate(indexStrips):
                # making them lists so blender can use them
                indexList = list()
                for j in range(0, len(s)-2):
                    p = [s[j], s[j+1], s[j+2]]
                    indexList.append(p)

                mesh = bpy.data.meshes.new(name = obj.data.name + "_str_" + str(i))
                mesh.from_pydata(verts, [], indexList)
                meObj = bpy.data.objects.new(mesh.name, object_data = mesh)
                context.collection.objects.link(meObj)
                meObj.parent = empty
        else:
            indexList = list()
            for i in range(0, len(indexStrips) - 2):
                p = [indexStrips[i], indexStrips[i+1], indexStrips[i+2]]
                if len(set(p)) == 3:
                    indexList.append(p)

            mesh = bpy.data.meshes.new(name = obj.data.name + "_str")
            mesh.from_pydata(verts, [], indexList)
            meObj = bpy.data.objects.new(mesh.name, object_data = mesh)
            context.collection.objects.link(meObj)


        return {'FINISHED'}

def menu_func_exportmdl(self, context):
    self.layout.operator(ExportSA2MDL.bl_idname, text ="SA2 Model format (.sa2mdl/.sa2bmdl)")

def menu_func_exportlvl(self, context):
    self.layout.operator(ExportSA2LVL.bl_idname, text ="SA2 Level format (.sa2lvl/.sa2blvl)")
    
def menu_func_strippifyTest(self, context):
    self.layout.operator(StrippifyTest.bl_idname)

classes = (
    ExportSA2MDL,
    ExportSA2LVL,
    StrippifyTest
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportmdl)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportlvl)
    bpy.types.VIEW3D_MT_object.append(menu_func_strippifyTest)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportmdl)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportlvl)
    bpy.types.VIEW3D_MT_object.remove(menu_func_strippifyTest)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
   register()