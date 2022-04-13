import bpy
import addon_utils
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

#region Addon Imports
from .. import common
from ..prop.properties import(
    SASettings,
    SAEditPanelSettings,
    SALandEntrySettings,
    SAMaterialSettings,
    SAMeshSettings,
    SATexture
)
from .panel_draw import(
	propAdv,
	drawMaterialPanel,
	drawLandEntryPanel,
	drawMeshPanel,
	drawScenePanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots
)
from .panel_spaces import(
    SA_UI_Panel
)
from ..ops.quickEdit import(
	qeUpdate,
	qeUpdateSet,
	qeUpdateUnset,
	qeReset,
	qeInvert
)
from ..ops.imports import(
	LoadSetFile,
	LoadAnimFile
)
from ..ops.exports import(
	ExportAnim
)
from ..ops.materials import(
	AutoAssignTextures,
	ToPrincipledBsdf,
	MatToAssetLibrary
)
from ..ops.object import(
	ArmatureFromObjects
)
from ..ops.projects import(
	openToolsHub,
	openSALVL,
	openSAMDL,
	openTexEdit,
	saveProjectPreferences
)
#endregion

version = [addon.bl_info.get('version') for addon in addon_utils.modules()
            if addon.bl_info['name'] == "Sonic Adventure Tools"][0]

class SA_SceneInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Scene Information Panel (Author, Texlist, etc)
	bl_idname = "SCENE_UI_saProperties"
	bl_label = "Scene Information"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		drawScenePanel(layout, settings)

class SA_LandEntryProperties_Viewport(SA_UI_Panel, bpy.types.Panel):	## NJS_OBJECT Information Panel
	bl_idname = "OBJECT_UI_saProperties"
	bl_label = "Landtable Entry Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		objProps = context.active_object.saSettings
		menuProps = context.scene.saSettings.editorSettings

		drawLandEntryPanel(layout, menuProps, objProps)

class SA_ModelProps_Viewport(SA_UI_Panel, bpy.types.Panel):				## NJS_MODEL Information Panel
	bl_idname = "MESH_UI_saProperties"
	bl_label = "Model Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		meshprops = context.active_object.data.saSettings

		drawMeshPanel(layout, meshprops)

class SA_MaterialProps_Viewport(SA_UI_Panel, bpy.types.Panel):			## NJS_MATERIAL Panel
	bl_idname = "MATERIAL_UI_saProperties"
	bl_label = "Material Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == 'MESH'

	def draw(self, context):
		layout = self.layout

		obj = context.object
		is_sortable = len(obj.material_slots) > 1

		box = layout.box()
		row = box.row()
		row.template_list("MATERIAL_UL_saMaterialSlots", "", obj, "material_slots", obj, "active_material_index")
		col = row.column()
		col.operator("object.material_slot_add", icon='ADD', text="")
		col.operator("object.material_slot_remove", icon='REMOVE', text="")
		col.separator()
		col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")
		if is_sortable:
			col.separator()
			col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
			col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
		
		row = box.row()
		if obj:
			row.template_ID(obj, "active_material", new="material.new")
			if obj.mode == 'EDIT':
				row = layout.row(align=True)
				row.operator("object.material_slot_assign", text="Assign")
				row.operator("object.material_slot_select", text="Select")
				row.operator("object.material_slot_deselect", text="Deselect")

		layout.separator()

		if context.active_object.active_material is not None:
			menuProps = context.scene.saSettings.editorSettings
			matProps = context.active_object.active_material.saSettings
			drawMaterialPanel(layout, menuProps, matProps)

class SA_QuickEditMenu_Viewport(SA_UI_Panel, bpy.types.Panel):			## Quick Edit Menu + Update Material Button, etc
	bl_idname = 'MESH_UI_satools'
	bl_label = 'Quick Edit Menu'
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.mode == 'OBJECT'

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout

		settings = context.scene.saSettings

		outerBox = layout.box()

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
		row.prop(settings, "useLandEntryEdit", text="")
		row.prop(settings, "expandedLandEntryEdit",
			icon="TRIA_DOWN" if settings.expandedLandEntryEdit else "TRIA_RIGHT",
			emboss = False
			)

		if settings.expandedLandEntryEdit:
			box.separator()
			drawLandEntryPanel(box, settings.qEditorSettings, settings.objQProps, qe=True)
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

class SA_LevelInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Level Information (landtable name, texlist pointer, texture name, etc)
	bl_idname = "UI_saLevelInfo"
	bl_label = "Level Properties"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		# Info Box
		box = layout.box()
		box.prop(settings, "landtableName")

		split = box.split(factor=0.5)
		split.label(text="Draw Distance:")
		split.prop(settings, "drawDistance", text="")

		row = box.row()
		row.alignment='LEFT'
		row.label(text="Texlist Pointer:  0x")
		row.alignment='EXPAND'
		row.prop(settings, "texListPointer", text="")
		layout.separator()
		split = box.split(factor=0.4)
		split.label(text="Texture Filename")
		split.prop(settings, "texFileName", text="")

		box.prop(settings, "doubleSidedCollision")

class SA_AdditionalOperators_Vieport(SA_UI_Panel, bpy.types.Panel):		## Additional Operators (Loading other files, extra functions, etc)
	bl_idname = "UI_saAddOperators"
	bl_label = "Additional Functions"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout

		layout.label(text="Import/Export")
		layout.operator(LoadSetFile.bl_idname)
		split = layout.split()
		split.operator(LoadAnimFile.bl_idname)
		split.operator(ExportAnim.bl_idname)

		layout.separator()
		layout.label(text="Material Helpers")
		layout.operator(AutoAssignTextures.bl_idname)
		layout.operator(ToPrincipledBsdf.bl_idname)
		layout.operator(MatToAssetLibrary.bl_idname)

		layout.separator()
		layout.label(text="Other Helpers")
		layout.operator(ArmatureFromObjects.bl_idname)
		layout.operator(StrippifyTest.bl_idname)

class SA_ProjectManagement_Viewport(SA_UI_Panel, bpy.types.Panel):		## Project Support Panel, currently unused.
	bl_idname = "UI_saProjectManagement"
	bl_label = "Project Management"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		# Need custom load def for filtering by type.
		layout.prop(settings, "ToolsPath")
		layout.prop(settings, "ProjectPath")
		layout.separator()
		layout.operator(openToolsHub.bl_idname)
		layout.operator(openSALVL.bl_idname)
		layout.operator(openSAMDL.bl_idname)
		layout.operator(openTexEdit.bl_idname)
		layout.separator()
		layout.operator(saveProjectPreferences.bl_idname, toolPath=settings.ToolsPath, projFile=settings.ProjectPath)
	
class SA_AddonInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Addon Information, currently unused.
	bl_idname = "UI_saAddonInfo"
	bl_label = "Addon Info"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout

		layout.label(text="Current Version: " + str(verison))
