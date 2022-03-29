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

class SA_SceneInfo_Panel(SA_UI_Panel, bpy.types.Panel):				## Scene Information Panel (Author, Texlist, etc)
	bl_idname = "SCENE_PT_saProperties"
	bl_label = "Scene Information"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		layout.prop(settings, "author")
		layout.prop(settings, "description")
		layout.separator()
		layout.alignment = 'CENTER'
		layout.label(text="Scene Update Functions")
		layout.alignment = 'EXPAND'
		layout.operator(UpdateMaterials.bl_idname)
		layout.separator(factor=2)

		# Scene Texlist
		box = layout.box()
		box.prop(settings, "expandedTexturePanel",
			icon="TRIA_DOWN" if settings.expandedTexturePanel else "TRIA_RIGHT",
			emboss = False
			)

		if settings.expandedTexturePanel:
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

		
		# Scene Lighting
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

class SA_LandEntryProperties_Panel(SA_UI_Panel, bpy.types.Panel):	## NJS_OBJECT Information Panel
	bl_idname = "OBJECT_PT_saProperties"
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

class SA_ModelProps_Panel(SA_UI_Panel, bpy.types.Panel):			## NJS_MODEL Information Panel
	bl_idname = "MESH_PT_saProperties"
	bl_label = "Model Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.active_object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		meshprops = context.active_object.data.saSettings

		drawMeshPanel(layout, meshprops)

class SA_MaterialProps_Panel(SA_UI_Panel, bpy.types.Panel):			## NJS_MATERIAL Panel
	bl_idname = "MATERIAL_PT_saProperties"
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

class SA_QuickEditMenu_Panel(SA_UI_Panel, bpy.types.Panel):			## Quick Edit Menu + Update Material Button, etc
	bl_idname = 'MESH_PT_satools'
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

class SA_LevelInfo_Panel(SA_UI_Panel, bpy.types.Panel):				## Level Information (landtable name, texlist pointer, texture name, etc)
	bl_idname = "UI_saLevelInfo"
	bl_label = "Level Properies"
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

class SA_AdditionalOperators_Panel(SA_UI_Panel, bpy.types.Panel):	## Additional Operators (Loading other files, extra functions, etc)
	bl_idname = "UI_PT_saAddOperators"
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

class SA_ProjectManagement_Panel(SA_UI_Panel, bpy.types.Panel):		## Project Support Panel, currently unused.
	bl_idname = "UI_PT_saProjectManagement"
	bl_label = "Project Management"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		# Need custom load def for filtering by type.
		layout.prop(settings, "ToolsPath")
		layout.prop(settings, "ProjectPath")
		
class SA_AddonInfo_Panel(SA_UI_Panel, bpy.types.Panel):				## Addon Information, currently unused.
	bl_idname = "UI_PT_saProperties"
	bl_label = "Addon Info"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout

		layout.label(text="Current Ver: ")
