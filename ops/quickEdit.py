from doctest import BLANKLINE_MARKER
from multiprocessing.pool import MapResult
import bpy
import os
import shutil
from bpy.props import (
	BoolProperty,
	FloatProperty,
	FloatVectorProperty,
	IntProperty,
	EnumProperty,
	StringProperty,
	CollectionProperty
	)
from bpy_extras.io_utils import ExportHelper, ImportHelper
from typing import List, Dict, Union, Tuple

from .. import common
from ..prop.properties import(
	SASettings,
	SAEditPanelSettings,
	SALandEntrySettings,
	SAMaterialSettings,
	SAMeshSettings,
	SAObjectSettings,
	SATexture
)

def qeUpdate(context, qType, newValue = True):			## Quick Edit Menu Update Definition.
	'''Updates all selected objects with according properties'''

	qEditSettings = context.scene.saSettings
	objects = context.selected_objects

	# If the user specified to change materials...
	if context.scene.saSettings.useMatEdit:
		matQProps = context.scene.saSettings.matQProps

		mats = []
		for o in objects:
			if o.type == 'MESH':
				if (len(o.data.materials) == 0):
					newMat = bpy.data.materials.new('material_' + str(len(bpy.data.materials)-1))
					o.data.materials.append(newMat)
				for m in o.data.materials:
					if m not in mats:
						mats.append(m)

		for m in mats:
			matProps: SAMaterialSettings = m.saSettings

			if (qType == 1):
				for p in dir(matQProps):
					if not p.startswith("b_") and not p.startswith("gc_"):
						continue

					a = getattr(matQProps, p)
					if type(a) is bool:
						if a:
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
			else:
				matProps.b_Diffuse = matQProps.b_Diffuse
				matProps.b_Specular = matQProps.b_Specular
				matProps.b_Ambient = matQProps.b_Ambient
				matProps.b_Exponent = matQProps.b_Exponent
				matProps.b_TextureID = matQProps.b_TextureID
				matProps.b_d_025 = matQProps.b_d_025
				matProps.b_d_050 = matQProps.b_d_050
				matProps.b_d_100 = matQProps.b_d_100
				matProps.b_d_200 = matQProps.b_d_200
				matProps.b_use_Anisotropy = matQProps.b_use_Anisotropy
				matProps.b_texFilter = matQProps.b_texFilter
				matProps.b_clampU = matQProps.b_clampU
				matProps.b_clampV = matQProps.b_clampV
				matProps.b_mirrorU = matQProps.b_mirrorU
				matProps.b_mirrorV = matQProps.b_mirrorV
				matProps.b_useTexture = matQProps.b_useTexture
				matProps.b_useEnv = matQProps.b_useEnv
				matProps.b_useAlpha = matQProps.b_useAlpha
				matProps.b_srcAlpha = matQProps.b_srcAlpha
				matProps.b_destAlpha = matQProps.b_destAlpha
				matProps.b_doubleSided = matQProps.b_doubleSided
				matProps.b_ignoreSpecular = matQProps.ignoreSpecular
				matProps.b_ignoreLighting = matQProps.ignoreLighting
				matProps.b_ignoreSpecular = matQProps.ignoreSpecular
				matProps.b_flatShading = matQProps.b_flatShading
				matProps.b_unknown = matQProps.b_unknown
				matProps.gc_shadowStencil = matQProps.gc_shadowStencil
				matProps.gc_texCoordID = matQProps.texCoordID
				matProps.gc_texGenType = matQProps.gc_texGenType
				matProps.gc_texMatrixID = matQProps.gc_texMatrixID
				matProps.gc_texGenSourceBmp = matQProps.gc_texGenSourceBmp
				matProps.gc_texGenSourceMtx = matQProps.gc_texGenSourceMtx
				matProps.gc_texGenSourceSRTG = matQProps.gc_texGenSourceSRTG

	# If the user specified to change land entry flags...
	if context.scene.saSettings.useLandEntryEdit:
		for o in objects:
			objProps = o.saSettings

			if (qType == 1):
				for k, v in SALandEntrySettings.defaultDict().items():
					if isinstance(v, bool) and getattr(qEditSettings.landQProps, k):
						setattr(objProps, k, newValue)
				objProps.userFlags = qEditSettings.landQProps.userFlags
				objProps.blockbit = qEditSettings.landQProps.blockbit
			else:
				objProps.sfVisible = qEditSettings.landQProps.sfVisible
				objProps.sfSolid = qEditSettings.landQProps.sfSolid
				objProps.sfNoAccel = qEditSettings.landQProps.sfNoAccel
				objProps.sfLowAccel = qEditSettings.landQProps.sfLowAccel
				objProps.sfAccel = qEditSettings.landQProps.sfAccel
				objProps.sfIncAccel = qEditSettings.landQProps.sfIncAccel
				objProps.sfUnclimbable = qEditSettings.landQProps.sfUnclimbable
				objProps.sfDiggable = qEditSettings.landQProps.sfDiggable
				objProps.sfNoFriction = qEditSettings.landQProps.sfNoFriction
				objProps.sfStairs = qEditSettings.landQProps.sfStairs
				objProps.sfWater = qEditSettings.landQProps.sfWater
				objProps.sfCannotLand = qEditSettings.landQProps.sfCannotLand
				objProps.sfHurt = qEditSettings.landQProps.sfHurt
				objProps.sfFootprints = qEditSettings.landQProps.sfFootprints
				objProps.sfGravity = qEditSettings.landQProps.sfGravity
				objProps.sfUseRotation = qEditSettings.landQProps.sfUseRotation
				objProps.sfDynCollision = qEditSettings.landQProps.sfDynCollision
				objProps.sfWaterCollision = qEditSettings.landQProps.sfWaterCollision
				objProps.sfUseSkyDrawDistance = qEditSettings.landQProps.sfUseSkyDrawDistance
				objProps.sfNoZWrite = qEditSettings.landQProps.sfNoZWrite
				objProps.sfLowDepth = qEditSettings.landQProps.sfLowDepth
				objProps.sfDrawByMesh = qEditSettings.landQProps.sfDrawByMesh
				objProps.sfWaterfall = qEditSettings.landQProps.sfWaterfall
				objProps.sfChaos0Land = qEditSettings.landQProps.sfChaos0Land
				objProps.sfEnableManipulation = qEditSettings.landQProps.sfEnableManipulation
				objProps.sfSA1U_200 = qEditSettings.landQProps.sfSA1U_200
				objProps.sfSA1U_800 = qEditSettings.landQProps.sfSA1U_800
				objProps.sfSA1U_8000 = qEditSettings.landQProps.sfSA1U_8000
				objProps.sfSA1U_20000 = qEditSettings.landQProps.sfSA1U_20000
				objProps.sfSA1U_80000 = qEditSettings.landQProps.sfSA1U_80000
				objProps.sfSA1U_20000000 = qEditSettings.landQProps.sfSA1U_20000000
				objProps.sfSA1U_40000000 = qEditSettings.landQProps.sfSA1U_40000000
				objProps.sfWater2 = qEditSettings.landQProps.sfWater2
				objProps.sfNoShadows = qEditSettings.landQProps.sfNoShadows
				objProps.sfNoFog = qEditSettings.landQProps.sfNoFog
				objProps.sfSA2U_40 = qEditSettings.landQProps.sfSA2U_40
				objProps.sfSA2U_200 = qEditSettings.landQProps.sfSA2U_200
				objProps.sfSA2U_4000 = qEditSettings.landQProps.sfSA2U_4000
				objProps.sfSA2U_800000 = qEditSettings.landQProps.sfSA2U_800000
				objProps.sfSA2U_1000000 = qEditSettings.landQProps.sfSA2U_1000000
				objProps.sfSA2U_2000000 = qEditSettings.landQProps.sfSA2U_2000000
				objProps.sfSA2U_4000000 = qEditSettings.landQProps.sfSA2U_4000000
				objProps.sfSA2U_20000000 = qEditSettings.landQProps.sfSA2U_20000000
				objProps.sfSA2U_40000000 = qEditSettings.landQProps.sfSA2U_40000000

	# If the user specified to change meshes...
	if context.scene.saSettings.useMeshEdit:
		meshes = list()
		bones = list()
		if context.mode == 'POSE':
			bones = context.selected_pose_bones
		elif context.mode == 'EDIT_ARMATURE':
			bones = context.selected_bones

		for b in bones:
			objProps = b.bone.saObjflags

			if (qType == 1):
				for k, v in SAObjectSettings.defaultDict().items():
					if isinstance(v, bool) and getattr(qEditSettings.objQProps, k):
						setattr(objProps, k, newValue)
			else:
				objProps.ignorePosition = qEditSettings.objQProps.ignorePosition
				objProps.ignoreRotation = qEditSettings.objQProps.ignoreRotation
				objProps.ignoreScale = qEditSettings.objQProps.ignoreScale
				objProps.rotateZYX = qEditSettings.objQProps.rotateZYX
				objProps.skipDraw = qEditSettings.objQProps.skipDraw
				objProps.skipChildren = qEditSettings.objQProps.skipChildren
				objProps.flagAnimate = qEditSettings.objQProps.flagAnimate
				objProps.flagMorph = qEditSettings.objQProps.flagMorph

		for o in objects:
			objProps = o.saObjflags

			if (qType == 1):
				for k, v in SAObjectSettings.defaultDict().items():
					if isinstance(v, bool) and getattr(qEditSettings.objQProps, k):
						setattr(objProps, k, newValue)
			else:
				objProps.ignorePosition = qEditSettings.objQProps.ignorePosition
				objProps.ignoreRotation = qEditSettings.objQProps.ignoreRotation
				objProps.ignoreScale = qEditSettings.objQProps.ignoreScale
				objProps.rotateZYX = qEditSettings.objQProps.rotateZYX
				objProps.skipDraw = qEditSettings.objQProps.skipDraw
				objProps.skipChildren = qEditSettings.objQProps.skipChildren
				objProps.flagAnimate = qEditSettings.objQProps.flagAnimate
				objProps.flagMorph = qEditSettings.objQProps.flagMorph

			if o.type == 'MESH' and o.data not in meshes:
				meshes.append(o.data)

		for m in meshes:
			meshProps = m.saSettings

			if (qType == 1):
				if qEditSettings.me_apply_ExportType and newValue:
					meshProps.sa2ExportType = qEditSettings.meshQProps.sa2ExportType
				if qEditSettings.me_apply_addVO and newValue:
					meshProps.sa2IndexOffset = qEditSettings.meshQProps.sa2IndexOffset
			else:
				meshProps.sa2ExportType = qEditSettings.meshQProps.sa2ExportType
				meshProps.sa2IndexOffset = qEditSettings.meshQProps.sa2IndexOffset

class qeApplyAll(bpy.types.Operator):
	"""Applies all properties to selected Quick Edit Options."""
	bl_idname = "object.qeall"
	bl_label = "Apply All"
	bl_description = "Applies properties to match those in the Quick Edit Menu Selection."

	def execute(self, context):
		qeUpdate(context, 0)
		return {'FINISHED'}

class qeAddProps(bpy.types.Operator):		## Sets the applied Quick Edit Menu selections.
	"""Quick Material Editor Updater for setting selected field to true"""
	bl_idname = "object.qeset"
	bl_label = "Add Props"
	bl_description = "Sets checked items in enabled Quick Edit Menu to True."

	def execute(self, context):
		qeUpdate(context, 1, True)
		return {'FINISHED'}

class qeRemoveProps(bpy.types.Operator):	## Removes the applied Quick Edit Menu selections.
	"""Quick Material Editor Updater for unsetting selected field to true"""
	bl_idname = "object.qeunset"
	bl_label = "Remove Props"
	bl_description = "Sets checked items in enabled Quick Edit Menu to False."

	def execute(self, context):
		qeUpdate(context, 1, False)
		return {'FINISHED'}

def qeSelection(context, bValue):
	menuProps: SASettings = context.scene.saSettings

	if menuProps.useMatEdit:
		matProps = context.scene.saSettings.matQProps
		for p in dir(matProps):
			if not p.startswith("b_") and not p.startswith("gc_"):
				continue

			a = getattr(matProps, p)
			if isinstance(a, bool):
				setattr(matProps, p, bValue)

		for p in dir(menuProps):
			if not p.startswith("b_") and not p.startswith("gc_"):
				continue

			a = getattr(menuProps, p)
			if type(a) is bool:
				setattr(menuProps, p, bValue)

	if menuProps.useLandEntryEdit:
		landProps = context.scene.saSettings.landQProps
		for k, v in landProps.toDictionary().items():
			landProps[k] = bValue

		menuProps.obj_apply_userFlags = bValue
		menuProps.obj_apply_blockBit = bValue

	if menuProps.useMeshEdit:
		menuProps.me_apply_addVO = bValue
		menuProps.me_apply_ExportType = bValue

		objProps = context.scene.saSettings.objQProps
		for k, v in objProps.toDictionary().items():
			objProps[k] = bValue

class qeSelectAll(bpy.types.Operator):
	'''Quick Material Selection: Select All'''
	bl_idname = "object.qeselall"
	bl_label = "Select All"
	bl_description = "Selects all items and sets them to True in enabled Quick Edit Menu."

	def execute(self, context):
		qeSelection(context, True)
		return {'FINISHED'}

class qeReset(bpy.types.Operator):			## Resets the Quick Edit Menu to default selections.
	"""Quick Material Selection: Select None"""
	bl_idname = "object.qereset"
	bl_label = "Clear Selection"
	bl_description = "Resets all items to False in enabled Quick Edit Menu."

	def execute(self, context):
		qeSelection(context, False)
		return {'FINISHED'}

class qeInvert(bpy.types.Operator):			## Inverts current Quick Edit Menu selections.
	"""Quick Material Selection: Select Invert"""
	bl_idname = "object.qeinvert"
	bl_label = "Invert Selection"
	bl_description = "Inverts selected items in enabled Quick Edit Menu."

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

		if menuProps.useLandEntryEdit:
			landProps = context.scene.saSettings.landQProps
			for k, v in landProps.toDictionary().items():
				landProps[k] = not v

			menuProps.obj_apply_userFlags = not menuProps.obj_apply_userFlags
			menuProps.obj_apply_blockbit = not menuProps.obj_apply_blockbit

		if menuProps.useMeshEdit:
			menuProps.me_apply_addVO = not menuProps.me_apply_addVO
			menuProps.me_apply_ExportType = not menuProps.me_apply_ExportType

			objProps = context.scene.saSettings.objQProps
			for k, v in objProps.toDictionary().items():
				objProps[k] = not v


		return {'FINISHED'}
