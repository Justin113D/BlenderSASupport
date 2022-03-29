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
from ..ops.materials import(
	UpdateMaterials
)

def propAdv(layout, label, prop1, prop1Name, prop2, prop2Name, autoScale = False, qe = False):		## Advanced Properties draw definition.
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

def drawMaterialPanel(layout, menuProps, matProps, qe = False):										## Draws the Material Properties Panel.

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

def drawLandEntryPanel(layout: bpy.types.UILayout, menuProps, objProps, qe = False):				## Draws the Land Entry Properties Panel.

	sProps = bpy.context.scene.saSettings

	# sa1 flags
	box = layout.box()
	box.prop(menuProps, "expandedSA1obj",
		icon="TRIA_DOWN" if menuProps.expandedSA1obj else "TRIA_RIGHT",
		emboss = False
		)

	if menuProps.expandedSA1obj:
		box.prop(objProps, "solid")
		box.prop(objProps, "sa1_water")
		box.prop(objProps, "sa1_noFriction")
		box.prop(objProps, "sa1_noAcceleration")
		box.prop(objProps, "sa1_lowAcceleration")
		box.prop(objProps, "sa1_useSkyDrawDistance")
		box.prop(objProps, "sa1_cannotLand")
		box.prop(objProps, "sa1_increasedAcceleration")
		box.prop(objProps, "sa1_diggable")
		box.prop(objProps, "sa1_waterfall")
		box.prop(objProps, "sa1_unclimbable")
		box.prop(objProps, "sa1_chaos0Land")
		box.prop(objProps, "sa1_stairs")
		box.prop(objProps, "sa1_hurt")
		box.prop(objProps, "sa1_lowDepth")
		box.prop(objProps, "sa1_footprints")
		box.prop(objProps, "sa1_accelerate")
		box.prop(objProps, "sa1_colWater")
		box.prop(objProps, "sa1_rotByGravity")
		box.prop(objProps, "sa1_noZWrite")
		box.prop(objProps, "sa1_drawByMesh")
		box.prop(objProps, "sa1_eneableManipulation")
		box.prop(objProps, "sa1_dynCollision")
		box.prop(objProps, "sa1_useRotation")
		box.prop(objProps, "isVisible")

	# sa2 flags
	box = layout.box()
	box.prop(menuProps, "expandedSA2obj",
		icon="TRIA_DOWN" if menuProps.expandedSA2obj else "TRIA_RIGHT",
		emboss = False
		)

	if menuProps.expandedSA2obj:
		box.prop(objProps, "solid")
		box.prop(objProps, "sa2_water")
		box.prop(objProps, "sa2_diggable")
		box.prop(objProps, "sa2_unclimbable")
		box.prop(objProps, "sa2_standOnSlope")
		box.prop(objProps, "sa2_hurt")
		box.prop(objProps, "sa2_footprints")
		box.prop(objProps, "sa2_cannotLand")
		box.prop(objProps, "sa2_water2")
		box.prop(objProps, "sa2_noShadows")
		box.prop(objProps, "sa2_noFog")
		box.prop(objProps, "sa2_unknown24")
		box.prop(objProps, "sa2_unknown29")
		box.prop(objProps, "sa2_unknown30")
		box.prop(objProps, "isVisible")

	propAdv(layout, "Custom (hex):  0x", objProps, "userFlags", sProps, "obj_apply_userFlags", qe = qe)

	propAdv(layout, "Blockbit (hex):  0x", objProps, "blockbit", sProps, "obj_apply_blockbit", qe = qe)

def drawMeshPanel(layout: bpy.types.UILayout, meshProps, qe = False):								## Draws the Mesh Properties Panel.
	sProps = bpy.context.scene.saSettings
	propAdv(layout, "Export Type (SA2)", meshProps, "sa2ExportType", sProps, "me_apply_ExportType", qe = qe)
	propAdv(layout, "+ Vertex Offset (SA2)", meshProps, "sa2IndexOffset", sProps, "me_apply_addVO", qe = qe)

def drawScenePanel(layout: bpy.types.UILayout, settings, qe = False):
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

class SCENE_UL_SATexList(bpy.types.UIList):															## UI List draw for Scene Texture List items.

	def draw_item(self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index, flt_flag):
		split = layout.split(factor=0.6)
		split.prop(item, "name", text="", emboss=False, icon_value=icon, icon= 'X' if item.image == None else 'CHECKMARK')
		split.prop(item, "globalID", text=str(index), emboss=False, icon_value=icon)

class SCENE_MT_Texture_Context_Menu(bpy.types.Menu):												## Scene Texture List Specials Menu.
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

class MATERIAL_UL_saMaterialSlots(bpy.types.UIList):												## UI List draw for Viewport Material List.
	# Draws a secondary Material Slots Viewer in the SA Materials Properties Panel
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
		ob = data
		slot = item
		mat = slot.material

		layout.prop(mat, "name", text="", emboss=False, icon_value=icon)
