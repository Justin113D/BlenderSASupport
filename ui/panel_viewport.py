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
	drawObjPanel,
	drawScenePanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots,
	drawProjectData
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
from ..ops.exports import (
	ExportCurve,
	ExportSA1MDL,
	ExportSA2MDL,
	ExportSA2BMDL,
	ExportSA1LVL,
	ExportSA2LVL,
	ExportSA2BLVL,
	ExportPAK,
	ExportPVMX,
	ExportAnim,
	ExportShapeMotion
)
from ..ops.imports import(
	ImportMDL,
	ImportLVL,
	ImportTexFile,
	LoadProjectFile,
	LoadSetFile,
	LoadCamFile,
	LoadAnimFile,
	LoadShapeMotion,
	LoadCameraMotion,
	LoadPathFile,
	LoadProjectFile
)
from ..ops.materials import(
	AutoAssignTextures,
	ToPrincipledBsdf,
	MatToAssetLibrary,
	UpdateMaterials
)
from ..ops.object import(
	ArmatureFromObjects,
	ModifyBoneShape,
	GeneratePathFromMesh
)
from ..ops.projects import(
	openToolsHub,
	openSALVL,
	openSAMDL,
	openTexEdit
)
from ..ops.mesh import(
	StrippifyTest
)
from ..parse.pxml import(
	ProjectFile
)
from .. import addon_updater_ops
#endregion

addonVersion = [addon.bl_info.get('version') for addon in addon_utils.modules()
            if addon.bl_info['name'] == "Sonic Adventure Tools"][0]

verNum = str(addonVersion).split('(')[1].split(')')[0].replace(',', '.').replace(' ', '')

class SA_ImportExport_Viewport(SA_UI_Panel, bpy.types.Panel):			## Import/Export: MDL and LVL Import/Export, Animation Import/Export and Tools, 
	bl_idname = "SCENE_PT_saImportExport"
	bl_label = "Tools"

	def draw(self, context):
		layout = self.layout

		# Model Tools
		row = layout.row()
		row.alignment = 'CENTER'
		row.label(text="Model Tools")
		row.scale_x = 1.0
		split = layout.split()
		split.operator(ImportMDL.bl_idname, text="Import *MDL")
		split.operator(ImportLVL.bl_idname, text="Import *LVL")
		layout.separator()
		split = layout.split()
		split.operator(ExportSA1MDL.bl_idname, text="Export SA1MDL")
		split.operator(ExportSA1LVL.bl_idname, text="Export SA1LVL")
		split = layout.split()
		split.operator(ExportSA2MDL.bl_idname, text="Export SA2MDL")
		split.operator(ExportSA2LVL.bl_idname, text="Export SA2LVL")
		split = layout.split()
		split.operator(ExportSA2BMDL.bl_idname, text="Export SA2BMDL")
		split.operator(ExportSA2BLVL.bl_idname, text="Export SA2BLVL")
		layout.separator()

		# Animation Tools
		row = layout.row()
		row.alignment = 'CENTER'
		row.label(text="Animation Tools")
		row.scale_x = 1.0
		layout.operator(ArmatureFromObjects.bl_idname)
		split = layout.split()
		split.operator(LoadAnimFile.bl_idname, text="Import Anim")
		split.operator(ExportAnim.bl_idname, text="Export Anim")
		split = layout.split()
		split.operator(LoadShapeMotion.bl_idname, text="Import Shape Motion")
		split.operator(ExportShapeMotion.bl_idname, text="Export Shape Motion")
		layout.operator(ModifyBoneShape.bl_idname)
		layout.operator(LoadCameraMotion.bl_idname)
		layout.separator()

		# Extra Tools
		row = layout.row()
		row.alignment = 'CENTER'
		row.label(text="Extra Tools")
		row.scale_x = 1.0
		layout.operator(LoadSetFile.bl_idname)
		layout.operator(LoadCamFile.bl_idname)
		layout.operator(LoadPathFile.bl_idname)
		layout.operator(StrippifyTest.bl_idname)

class SA_SceneInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Scene Info: Author, Description, Texlist, Scene Lighting, Material Operators
	bl_idname = "SCENE_PT_infoPanel"
	bl_label = "Scene Information"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		drawScenePanel(layout, settings)

class SA_LandProperties_Viewport(SA_UI_Panel, bpy.types.Panel):			## LandEntry Info: Landtable Flags
	bl_idname = "SCENE_PT_lvlProperties"
	bl_label = "Surface Flags"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		if context.scene.saSettings.sceneIsLevel:
			if context.active_object.type == 'MESH':	# Mesh Nodes/Empty Nodes
				return True
			else:
				return False
		else:
			return False

	def draw(self, context):
		layout = self.layout

		lvlProps = context.active_object.saSettings
		menuProps = context.scene.saSettings.editorSettings

		drawLandEntryPanel(layout, menuProps, lvlProps)

class SA_ModelProps_Viewport(SA_UI_Panel, bpy.types.Panel):				## Object/Model Info: Object Flags, Mesh Types
	bl_idname = "SCENE_PT_mdlProperties"
	bl_label = "Object & Mesh Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		if (context.active_object != None):
			if (context.active_object.type == 'MESH') or (context.active_object.type == 'EMPTY') or (context.active_object.type == 'ARMATURE'):	# Mesh Nodes/Empty Nodes
				return True
			elif (context.mode == 'POSE') or (context.mode == 'EDIT_ARMATURE'):	# Bones
				return True
			else:
				return False
		else:
			return False

	def draw(self, context):
		layout = self.layout
		menuProps = context.scene.saSettings.editorSettings
		meshprops = None
		if context.active_object.type == 'MESH':
			meshprops = context.active_object.data.saSettings
		
		if context.mode == 'POSE':
			objProps = context.active_object.data.bones.active.saObjflags
		elif context.mode == 'EDIT_ARMATURE':
			objProps = context.active_object.data.edit_bones.active.saObjflags
		else:	
			objProps = context.active_object.saObjflags

		if meshprops is not None:
			drawMeshPanel(layout, meshprops)

		drawObjPanel(layout, menuProps, objProps)

class SA_MaterialProps_Viewport(SA_UI_Panel, bpy.types.Panel):			## Material: Materials on object, SA Material Properties
	bl_idname = "SCENE_PT_matProperties"
	bl_label = "Material Properties"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		if (context.active_object != None):
			return context.active_object.type == 'MESH'
		else:
			return False

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

class SA_QuickEditMenu_Viewport(SA_UI_Panel, bpy.types.Panel):			## Quick Edit: All Quick Edit Items
	bl_idname = 'SCENE_PT_satools'
	bl_label = 'Quick Edit Menu'
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		if (context.active_object != None):
			if (context.active_object.type == 'MESH') or (context.active_object.type == 'EMPTY') or (context.active_object.type == 'ARMATURE'):	# Mesh Nodes/Empty Nodes
				return True
			elif (context.mode == 'POSE') or (context.mode == 'EDIT_ARMATURE'):	# Bones
				return True
			else:
				return False
		else:
			return False

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
		row.prop(settings, "useMeshEdit", text="")
		row.prop(settings, "expandedMeshEdit",
			icon="TRIA_DOWN" if settings.expandedMeshEdit else "TRIA_RIGHT",
			emboss = False
			)

		if settings.expandedMeshEdit:
			box.separator()
			if (context.mode == 'OBJECT'): 
				drawMeshPanel(box, settings.meshQProps, qe=True)
			drawObjPanel(box, settings.qEditorSettings, settings.objQProps, qe=True)
			box.separator()

		if settings.sceneIsLevel:
			box = outerBox.box()

			row = box.row()
			row.prop(settings, "useLandEntryEdit", text="")
			row.prop(settings, "expandedLandEntryEdit",
				icon="TRIA_DOWN" if settings.expandedLandEntryEdit else "TRIA_RIGHT",
				emboss = False
				)

			if settings.expandedLandEntryEdit:
				box.separator()
				drawLandEntryPanel(box, settings.qEditorSettings, settings.landQProps, qe=True)
				box.separator()

class SA_LevelInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Level Information (landtable name, texlist pointer, texture name, etc)
	bl_idname = "SCENE_PT_saLevelInfo"
	bl_label = "Level Info"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		return context.scene.saSettings.sceneIsLevel

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

class SA_CurveInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Curve Info: Currently Inoperable
	bl_idname = "SCENE_PT_CurveInfo"
	bl_label = "Curve Info"
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context):
		if context.scene.saSettings.sceneIsLevel:
			return True
		else:
			return False

	def draw(self, context):
		layout = self.layout
		layout.operator(GeneratePathFromMesh.bl_idname)
		layout.separator()
		layout.operator(ExportCurve.bl_idname)
		layout.separator()
		if (context.active_object.type == 'CURVE'):
			spline = context.active_object.data.splines[0]
			spLength = spline.calc_length()
			layout.label(text='Path Point Count: ' + str(len(spline.points)))
			layout.label(text='Path Length: ' + str(spLength))
		else:
			layout.label(text='No Spline Selected')
		
class SA_ProjectManagement_Viewport(SA_UI_Panel, bpy.types.Panel):		## Project Info: Project 
	bl_idname = "SCENE_PT_saProjectManagement"
	bl_label = "Project Management"
	bl_options = {"DEFAULT_CLOSED"}

	@classmethod
	def poll(cls, context):
		if common.get_prefs().toolspath != "":
			return True

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saProjInfo

		layout.operator(openToolsHub.bl_idname)
		layout.operator(openSALVL.bl_idname)
		layout.operator(openSAMDL.bl_idname)
		layout.operator(openTexEdit.bl_idname)
		layout.separator()
		layout.operator(LoadProjectFile.bl_idname)

		if settings.ProjectFilePath != "":
			projFile = ProjectFile.ReadProjectFile(settings.ProjectFilePath)
			drawProjectData(layout, projFile, settings)
	
class SA_AddonInfo_Viewport(SA_UI_Panel, bpy.types.Panel):				## Addon Information
	bl_idname = "SCENE_PT_saAddonInfo"
	bl_label = "Addon Info"
	bl_options = {"DEFAULT_CLOSED"}

	def draw(self, context):
		layout = self.layout
		layout.label(text="Current Version: " + str(verNum))

		addon_updater_ops.update_notice_box_ui()