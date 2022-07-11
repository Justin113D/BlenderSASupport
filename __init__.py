#region Standard Imports
import bpy
import os
import shutil
from bpy_extras.io_utils import ExportHelper, ImportHelper
from typing import List, Dict, Union, Tuple
from bpy.props import (
	BoolProperty,
	FloatProperty,
	FloatVectorProperty,
	IntProperty,
	EnumProperty,
	StringProperty,
	CollectionProperty
	)
#endregion

#region Modules
from . import addon_updater_ops
#endregion

#region Addon Imports
from . import common, setReader
from .ops.exports import (
	ExportSA1MDL,
	ExportSA2MDL,
	ExportSA2BMDL,
	ExportSA1LVL,
	ExportSA2LVL,
	ExportSA2BLVL,
	ExportPAK,
	ExportPVMX,
	ExportAnim,
	ExportCurve,
	ExportShapeMotion
)
from .ops.imports import(
	ImportMDL,
	ImportLVL,
	ImportTexFile,
	LoadSetFile,
	LoadCamFile,
	LoadAnimFile,
	LoadShapeMotion,
	LoadCameraMotion,
	LoadPathFile,
	LoadProjectFile
)
from .ops.materials import(
	AutoAssignTextures,
	ToPrincipledBsdf,
	UpdateMaterials,
	MatToAssetLibrary
)
from .ops.mesh import(
	StrippifyTest
)
from .ops.object import(
	ArmatureFromObjects,
	ModifyBoneShape,
	GeneratePathFromMesh
)
from .ops.textures import(
	AddTextureSlot,
	RemoveTextureSlot,
	MoveTextureSlot,
	ClearTextureList,
	AutoNameTextures
)
from .ops.quickEdit import(
	qeUpdateSet,
	qeUpdateUnset,
	qeReset,
	qeInvert
)
from .ops.projects import(
	openToolsHub,
	openSALVL,
	openSAMDL,
	openTexEdit
)
from .prop.properties import(
    SASettings,
    SAEditPanelSettings,
    SALandEntrySettings,
    SAMaterialSettings,
    SAMeshSettings,
    SATexture,
	SAObjectSettings,
	SAProjectSettings
)
from .ui.panel_draw import(
	propAdv,
	drawMaterialPanel,
	drawLandEntryPanel,
	drawMeshPanel,
	drawScenePanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots,
	LoadDataFiles
)
from .ui.panel_viewport import(
	SA_ImportExport_Viewport,
	SA_SceneInfo_Viewport,
	SA_LandProperties_Viewport,
	SA_ModelProps_Viewport,
	SA_MaterialProps_Viewport,
	SA_QuickEditMenu_Viewport,
	SA_LevelInfo_Viewport,
	SA_ProjectManagement_Viewport,
	SA_CurveInfo_Viewport,
	SA_AddonInfo_Viewport
)
from .ui.panel_material import(
	SA_MaterialProps_MaterialPanel 
)
from .ui.panel_scene import(
	SA_SceneInfo_ScenePanel
)
#endregion

## Start Addon Initialization

# Addon Meta Information
bl_info = {
	"name": "Sonic Adventure Tools",
	"author": "Justin113D",
	"description": "Import/Exporter for the SA Models Formats.",
	"version": (1, 7, 0),
	"blender": (2, 91, 0),
	"location": "File > Import/Export",
	"warning": "",
	"doc_url": "https://github.com/Justin113D/BlenderSASupport/wiki",
	"tracker_url": "https://github.com/Justin113D/BlenderSASupport/issues/new",
	"category": "Import-Export"
}

if locals().get('loaded'):
	loaded = False
	from importlib import reload
	from sys import modules

	modules[__name__] = reload(modules[__name__])
	for name, module in modules.items():
		if name.startswith(f"{__package__}."):
			globals()[name] = reload(module)
	del reload, modules

@addon_updater_ops.make_annotations
class AddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __package__

	auto_check_update = BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

	updater_interval_months = IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

	updater_interval_days = IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

	updater_interval_hours = IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

	updater_interval_minutes = IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

	printDebug: BoolProperty(
		name="Print Debug",
		description="Prints debug info to output window, will slow down exports.",
		default=False,
	)

	useProjectPath: BoolProperty(
		name="Use Project Folder",
		description="Overrides the set Default Path if a Project File has been loaded.",
		default=True
	)

	defaultPath: StringProperty(
		name="Default Path",
		description="Sets the default path used when importing/exporting files. Defaults to user's documents folder if not set.",
		default="",
		subtype='FILE_PATH'
	)

	toolspath: StringProperty(
        name="SA Tools Path",
		description="Path to your SA Tools install.",
		default="",
        subtype='FILE_PATH'
    )

	def draw(self, context):
		layout = self.layout
		split = layout.split()
		split.prop(self, "printDebug")
		split.prop(self, "useProjectPath")
		split = layout.split()
		split.prop(self, "toolspath")
		split.prop(self, "defaultPath")
		mainrow = layout.row()
		col = mainrow.column()
		addon_updater_ops.update_settings_ui(self, context)

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

def menu_func_exportsa(self, context):
	self.layout.menu("TOPBAR_MT_SA_export")

def menu_func_importsa(self, context):
	self.layout.operator(ImportMDL.bl_idname)
	self.layout.operator(ImportLVL.bl_idname)

# Register/Unregister for Addon
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
	ExportAnim,
	ExportCurve,
	ExportShapeMotion,

	ImportMDL,
	ImportLVL,
	ImportTexFile,
	LoadSetFile,
	LoadCamFile,
	LoadAnimFile,
	LoadShapeMotion,
	LoadCameraMotion,
	LoadPathFile,
	LoadProjectFile,

	StrippifyTest,
	ArmatureFromObjects,
	ModifyBoneShape,
	GeneratePathFromMesh,
	AddTextureSlot,
	RemoveTextureSlot,
	MoveTextureSlot,
	ClearTextureList,
	AutoNameTextures,
	ToPrincipledBsdf,
	UpdateMaterials,
	AutoAssignTextures,
	MatToAssetLibrary,
	openToolsHub,
	openSALVL,
	openSAMDL,
	openTexEdit,

	qeReset,
	qeInvert,
	qeUpdateSet,
	qeUpdateUnset,

	SALandEntrySettings,
	SASettings,
	SAMaterialSettings,
	SAEditPanelSettings,
	SAMeshSettings,
	SATexture,
	SAObjectSettings,
	SAProjectSettings,

	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots,
	#LoadDataFiles,
	SA_ImportExport_Viewport,
	SA_SceneInfo_Viewport,
	SA_MaterialProps_Viewport,
	SA_ModelProps_Viewport,
	SA_LandProperties_Viewport,
	SA_LevelInfo_Viewport,
	SA_CurveInfo_Viewport,
	SA_QuickEditMenu_Viewport,
	SA_ProjectManagement_Viewport,
	SA_AddonInfo_Viewport,

	SA_SceneInfo_ScenePanel,
	SA_MaterialProps_MaterialPanel,
	AddonPreferences,
)

def register():
	# Updater Registration
	addon_updater_ops.register(bl_info)
	for cls in classes:
		bpy.utils.register_class(cls)
	
	SATexture.image = bpy.props.PointerProperty(type=bpy.types.Image)

	SASettings.editorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
	SASettings.qEditorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
	SASettings.matQProps = bpy.props.PointerProperty(type=SAMaterialSettings)
	SASettings.landQProps = bpy.props.PointerProperty(type=SALandEntrySettings)
	SASettings.objQProps = bpy.props.PointerProperty(type=SAObjectSettings)
	SASettings.meshQProps = bpy.props.PointerProperty(type=SAMeshSettings)
	SASettings.textureList = bpy.props.CollectionProperty(
		type=SATexture,
		name="Texture list",
		description= "The textures used by sonic adventure"
		)

	bpy.types.Scene.saSettings = bpy.props.PointerProperty(type=SASettings)
	bpy.types.Scene.saProjInfo = bpy.props.PointerProperty(type=SAProjectSettings)
	bpy.types.Object.saSettings = bpy.props.PointerProperty(type=SALandEntrySettings)
	bpy.types.Object.saObjflags = bpy.props.PointerProperty(type=SAObjectSettings)
	bpy.types.Bone.saObjflags = bpy.props.PointerProperty(type=SAObjectSettings)
	bpy.types.EditBone.saObjflags = bpy.props.PointerProperty(type=SAObjectSettings)
	bpy.types.Armature.saObjflags = bpy.props.PointerProperty(type=SAObjectSettings)
	bpy.types.Material.saSettings = bpy.props.PointerProperty(type=SAMaterialSettings)
	bpy.types.Mesh.saSettings = bpy.props.PointerProperty(type=SAMeshSettings)

	bpy.types.TOPBAR_MT_file_export.append(menu_func_exportsa)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_importsa)

	import pathlib
	path = str(pathlib.Path(__file__).parent.absolute()) + "\\IOSA2.dll"

	import ctypes
	common.DLL = ctypes.cdll.LoadLibrary(path)

def unregister():
	del common.DLL
	addon_updater_ops.unregister()
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportsa)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_importsa)

	for cls in classes:
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()

loaded = True