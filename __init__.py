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
	ExportAnim
)
from .ops.imports import(
	ImportMDL,
	ImportLVL,
	ImportTexFile,
	LoadSetFile,
	LoadAnimFile
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
	ArmatureFromObjects
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
from .prop.properties import(
    SASettings,
    SAEditPanelSettings,
    SALandEntrySettings,
    SAMaterialSettings,
    SAMeshSettings,
    SATexture
)
from .ui.panel_draw import(
	propAdv,
	drawMaterialPanel,
	drawLandEntryPanel,
	drawMeshPanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots
)
from .ui.panel_viewport import(
	SA_SceneInfo_Panel,
	SA_LandEntryProperties_Panel,
	SA_ModelProps_Panel,
	SA_MaterialProps_Panel,
	SA_QuickEditMenu_Panel,
	SA_LevelInfo_Panel,
	SA_AdditionalOperators_Panel,
	SA_ProjectManagement_Panel,
	SA_AddonInfo_Panel
)

# meta info
bl_info = {
	"name": "SA Model Formats support",
	"author": "Justin113D",
	"version": (1, 6, 5),
	"blender": (2, 91, 0),
	"location": "File > Import/Export",
	"description": ("Import/Exporter for the SA Models Formats.\n"
					"Bugs should be reported to the github repository."),
	"warning": "",
	"wiki_url": "https://github.com/Justin113D/BlenderSASupport/wiki",
	"support": 'COMMUNITY',
	"category": "Import-Export"}

if locals().get('loaded'):
	loaded = False
	from importlib import reload
	from sys import modules

	modules[__name__] = reload(modules[__name__])
	for name, module in modules.items():
		if name.startswith(f"{__package__}."):
			globals()[name] = reload(module)
	del reload, modules

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

# menus
def menu_func_exportsa(self, context):
	self.layout.menu("TOPBAR_MT_SA_export")

def menu_func_importsa(self, context):
	self.layout.operator(ImportMDL.bl_idname)
	self.layout.operator(ImportLVL.bl_idname)

# registers
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

	ImportMDL,
	ImportLVL,
	ImportTexFile,
	LoadSetFile,
	LoadAnimFile,

	StrippifyTest,
	ArmatureFromObjects,
	AddTextureSlot,
	RemoveTextureSlot,
	MoveTextureSlot,
	ClearTextureList,
	AutoNameTextures,
	ToPrincipledBsdf,
	UpdateMaterials,
	AutoAssignTextures,
	MatToAssetLibrary,

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

	SA_SceneInfo_Panel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots,
	SA_MaterialProps_Panel,
	SA_ModelProps_Panel,
	SA_LandEntryProperties_Panel,
	SA_LevelInfo_Panel,
	SA_QuickEditMenu_Panel,
	SA_AdditionalOperators_Panel,
	#SA_AddonInfo_Panel,
	#SA_ProjectManagement_Panel,
	)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	SATexture.image = bpy.props.PointerProperty(type=bpy.types.Image)

	SASettings.editorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
	SASettings.qEditorSettings = bpy.props.PointerProperty(type=SAEditPanelSettings)
	SASettings.matQProps = bpy.props.PointerProperty(type=SAMaterialSettings)
	SASettings.objQProps = bpy.props.PointerProperty(type=SALandEntrySettings)
	SASettings.meshQProps = bpy.props.PointerProperty(type=SAMeshSettings)
	SASettings.textureList = bpy.props.CollectionProperty(
		type=SATexture,
		name="Texture list",
		description= "The textures used by sonic adventure"
		)

	bpy.types.Scene.saSettings = bpy.props.PointerProperty(type=SASettings)
	bpy.types.Object.saSettings = bpy.props.PointerProperty(type=SALandEntrySettings)
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

	bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportsa)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_importsa)

	for cls in classes:
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()

loaded = True