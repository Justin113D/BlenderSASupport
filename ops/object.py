import bpy
from bpy.props import (
	BoolProperty,
	EnumProperty
	)
from ..text.paths import PathEntry

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
		armatureObj.saObjflags.fromDictionary(active.saObjflags)
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
			bone.saObjflags.fromDictionary(b.saObjflags)
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

class ModifyBoneShape(bpy.types.Operator):
	bl_idname="object.modifyboneshape"
	bl_label="Bone Shapes to Empties"
	bl_description="Converts bone shapes to a selected empty type."

	emptySelection: EnumProperty(
		name="Empty Type",
		description="Empties for custom bone shapes.",
		items=( ('SPHERE', "Sphere", "Sphere Empty"),
				('CUBE', "Cube", "Cube Empty"),
				('PLAIN_AXIS', "Plain Axis", "Plain Axis Empty"),
				('ARROWS', "Arrows", "Arrows Empty") ),
		default='SPHERE'
	)

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	@classmethod
	def poll(cls, context):
		if (context.active_object != None) and (context.active_object.type == 'ARMATURE'):
			return True
		else:
			return False 

	def execute(self, context):
		shape = bpy.data.objects.new("boneShape", None)
		shape.empty_display_size = 0.25
		shape.empty_display_type = self.emptySelection
		
		armature = context.active_object
		bones = armature.pose.bones
		for b in bones:
			b.custom_shape = shape

		return {'FINISHED'}

def CreatePathPoints(name: str, points: list(), parent: bpy.types.Object, collection: bpy.types.Collection):
	idx = 0
	for p in points:
		objPoint = bpy.data.objects.new(name + '_point_' + ('{0:04}'.format(idx)), None)
		collection.objects.link(objPoint)
		objPoint.empty_display_type = 'SINGLE_ARROW'
		objPoint.empty_display_size = 5
		objPoint.parent = parent
		objPoint.parent_type = 'VERTEX'
		objPoint.rotation_mode='ZXY'
		objPoint.parent_vertices = (idx, idx, idx)
		objPoint.rotation_euler = [p.XRotation, -p.ZRotation, 0]
		idx += 1

def CreatePath(name: str, points: list(), collection: bpy.types.Collection, fromMesh=False):
	if points.count is not 0:
		crv = bpy.data.curves.new("curve_" + name, 'CURVE')
		curveObj = bpy.data.objects.new('path_' + name, crv)
		crv.dimensions = '3D'
		crv.twist_mode = 'Z_UP'
		spline = crv.splines.new(type='POLY')
		for po in points:
			if (fromMesh):
				spline.points[-1].co = [po.px, po.py, po.pz, 0.0]
			else:
				spline.points[-1].co = [po.px, -po.pz, po.py, 0.0]
			if po != points[-1]:
				spline.points.add(1)

		collection.objects.link(curveObj)
		CreatePathPoints(name, points, curveObj, collection)
	else:
		print("Points list was 0")

class GeneratePathFromMesh(bpy.types.Operator):
	bl_idname='object.pathfrommesh'
	bl_label='Generate Path'
	bl_description='Generates an Adventure games formatted path from a selected mesh.'

	revOrder: BoolProperty(
		name='Reverse Order',
		description='Reverses the order of the vertices for path generation.',
		default=False
	)

	delGeom: BoolProperty(
		name='Delete Geometry',
		description='Deletes original geometry the path was generated from.',
		default=False
	)

	cCollection: BoolProperty(
		name='Create Unique Collection',
		description='Creates a new collection based on the filename of the path. Setting this to False will default to a general paths collection.',
		default=True
	)

	@classmethod
	def poll(cls, context):
		if (context.active_object.type == 'MESH'):
			return True
		else:
			return False

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		obj = context.active_object
		bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
		pointList = list()
		if (len(obj.vertex_groups) == 0) or (len(obj.vertex_groups) > 1):
			print('Error, none/more than one vertex groups on object.')
		else:
			vertices = [v for v in obj.data.vertices if v.groups]
			if (self.revOrder):
				vertices.reverse()
			vidx = 0
			for v in vertices:
				dist = float(0)
				point = PathEntry()
				point.fromMesh(v, dist)
				pointList.append(point)
				vidx += 1
			if len(pointList) > 0:
				pthName = obj.name
				colName = 'ScenePaths'
				if (self.cCollection):
					colName = 'ScenePath_' + pthName
					newCol = bpy.data.collections.new(colName)
					bpy.context.scene.collection.children.link(newCol)
				else:
					cTest = bpy.data.collections.get(colName)
					if cTest is None:
						newCol = bpy.data.collections.new(colName)
						bpy.context.scene.collection.children.link(newCol)
				if (self.delGeom):
					bpy.data.objects.remove(obj)
				CreatePath(pthName, pointList, newCol, True)

		return {'FINISHED'}