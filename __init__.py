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


def menu_func_exportmdl(self, context):
    self.layout.operator(ExportSA2MDL.bl_idname, text ="SA2 Model format (.sa2mdl/.sa2bmdl)")

def menu_func_exportlvl(self, context):
    self.layout.operator(ExportSA2LVL.bl_idname, text ="SA2 Level format (.sa2lvl/.sa2blvl)")
    
classes = (
    ExportSA2MDL,
    ExportSA2LVL,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportmdl)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportlvl)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportmdl)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportlvl)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
   register()