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
    SATexture
)

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

	# If the user specified to change objects...
	if context.scene.saSettings.useObjEdit:
		for o in objects:

			objProps = o.saSettings
			for k, v in SALandEntrySettings.defaultDict().items():
				if isinstance(v, bool) and getattr(qEditSettings.objQProps, k):
					setattr(objProps, k, newValue)

			if qEditSettings.obj_apply_userFlags and newValue:
				objProps.userFlags = qEditSettings.objQProps.userFlags

			if qEditSettings.obj_apply_blockbit and newValue:
				objProps.blockbit = qEditSettings.objQProps.blockbit

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
			for k, v in SALandEntrySettings.defaultDict().items():
				if isinstance(v, bool):
					setattr(objProps, k, False)

			menuProps.obj_apply_userFlags = False
			menuProps.obj_apply_blockBit = False

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
			for k, v in SALandEntrySettings.defaultDict().items():
				if isinstance(v, bool):
					setattr(objProps, k, not getattr(objProps, k))

			menuProps.obj_apply_userFlags = not menuProps.obj_apply_userFlags
			menuProps.obj_apply_blockbit = not menuProps.obj_apply_blockbit

		if menuProps.useMeshEdit:
			menuProps.me_apply_addVO = not menuProps.me_apply_addVO
			menuProps.me_apply_ExportType = not menuProps.me_apply_ExportType


		return {'FINISHED'}
