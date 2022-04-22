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

class ArmatureFromObjects(bpy.types.Operator):		## Creates an armature for models that do not use armatures.
	'''Generates an armature based on the selected node and its child hierarchy'''
	bl_idname = "object.armaturefromobjects"
	bl_label = "Armature from objects"
	bl_description = "Generate an armature from object. Select the parent of all objects, which will represent the root"

	rotMode: EnumProperty(
		name="Rotation Mode",
		description="The rotation mode of each bone in the generated armature",
		items=( ('QUATERNION', "Quaternion (WXYZ)", "No Gimbal Lock."),
				('XYZ', "XYZ Euler", "XYZ Rotation Order - prone to Gimbal Lock (default)."),
				('XZY', "XZY Euler", "XZY Rotation Order - prone to Gimbal Lock."),
				('YXZ', "YXZ Euler", "YXZ Rotation Order - prone to Gimbal Lock."),
				('YZX', "YZX Euler", "YZX Rotation Order - prone to Gimbal Lock."),
				('ZXY', "ZXY Euler", "ZXY Rotation Order - prone to Gimbal Lock."),
				('ZYX', "ZYX Euler", "ZYX Rotation Order - prone to Gimbal Lock.") ),
		default='QUATERNION'
		)

	mergeModel: BoolProperty(
		name="Merge Meshes",
		description="Generates a single mesh object instead of keeping the single objects",
		default=False
		)

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	@classmethod
	def poll(cls, context):
		return len(context.selected_objects) > 0

	@classmethod
	def addChildren(cls, parent, result, resultMeshes):
		if parent.type == 'MESH':
			resultMeshes.append(len(result))
		result.append(parent)

		for c in parent.children:
			ArmatureFromObjects.addChildren(c, result, resultMeshes)

	def execute(self, context):
		import mathutils

		if len(context.selected_objects) == 0 or bpy.context.object.mode != 'OBJECT':
			return {'CANCELLED'}
		active = context.active_object

		objects = list()
		meshes = list()

		ArmatureFromObjects.addChildren(active, objects, meshes)

		zfillSize = max(2, len(str(len(meshes))))

		if len(objects) == 1:
			return {'CANCELLED'}

		armature = bpy.data.armatures.new("ARM_" + active.name)
		armatureObj = bpy.data.objects.new("ARM_" + active.name, armature)
		armatureObj.parent = active.parent
		armatureObj.matrix_local = active.matrix_local
		globalMatrix = active.matrix_world

		context.scene.collection.objects.link(armatureObj)

		bpy.ops.object.select_all(action='DESELECT')
		context.view_layer.objects.active = armatureObj
		bpy.ops.object.mode_set(mode='EDIT', toggle=False)

		edit_bones = armatureObj.data.edit_bones
		boneMap = dict()
		bones = objects[1:]

		scales = dict()

		for b in bones:
			boneName = b.name
			bone = edit_bones.new(b.name)
			bone.layers[0] = True
			bone.head = (0,0,0)
			bone.tail = (1,0,0)

			pos, rot, _ = b.matrix_world.decompose()

			matrix = mathutils.Matrix.Translation(pos) @ rot.to_matrix().to_4x4()

			bone.matrix = globalMatrix.inverted() @ matrix

			if b.parent in bones:
				bone.parent = boneMap[b.parent]
			boneMap[b] = bone

			_, _, poseScale = b.matrix_local.decompose()
			if poseScale.x != 1 or poseScale.y != 1 or poseScale.z != 1:
				scales[boneName] = poseScale

		bpy.ops.object.mode_set(mode='OBJECT')
		meshCount = 0

		print("making meshes")

		bpy.ops.object.select_all(action='DESELECT')

		meshOBJs = list()

		for i in meshes:
			boneObject = objects[i]

			meshCopy = boneObject.data.copy()
			meshCopy.name = "Mesh_" + str(meshCount).zfill(zfillSize)
			meshObj = boneObject.copy()
			meshObj.name = meshCopy.name
			meshObj.data = meshCopy
			context.scene.collection.objects.link(meshObj)

			meshObj.parent = armatureObj
			meshObj.matrix_local = globalMatrix.inverted() @ boneObject.matrix_world

			bpy.ops.object.mode_set(mode='OBJECT')
			meshObj.select_set(True, view_layer=context.view_layer)
			meshObj.scale = (1,1,1)
			bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)

			modif = meshObj.modifiers.new("deform", 'ARMATURE')
			modif.object = armatureObj

			group = meshObj.vertex_groups.new(name=boneObject.name)
			group.add([v.index for v in meshCopy.vertices], 1, 'ADD')

			meshCount += 1
			meshObj.select_set(False, view_layer=context.view_layer)

			meshOBJs.append(meshObj)

		if self.mergeModel:
			for o in meshOBJs:
				o.select_set(True)
			context.view_layer.objects.active = meshOBJs[0]
			bpy.ops.object.join()

		bpy.ops.object.select_all(action='DESELECT')

		print("made meshes")

		armatureObj.rotation_mode = self.rotMode
		for b in armatureObj.pose.bones:
			b.rotation_mode = self.rotMode
			if b.name in scales:
				b.scale = scales[b.name]


		return {'FINISHED'}

def CreatePath(name: str, points: list()):
	if points.count is not 0:
		crv = bpy.data.curves.new("curve" + name, 'CURVE')
		crv.dimensions = '3D'
		spline = crv.splines.new(type='POLY')
		for po in points:
			spline.points[-1].co = [po.px, po.pz*-1, po.py, 1]
			spline.points[-1].tilt = po.ZRotation
			if po != points[-1]:
				spline.points.add(1)

		obj = bpy.data.objects.new(name, crv)
		bpy.context.scene.collection.objects.link(obj)
	else:
		print("Points list was 0")