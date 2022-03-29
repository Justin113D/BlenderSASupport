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

from .. import common, strippifier

class StrippifyTest(bpy.types.Operator):
	'''An operator for test-strippifying a model'''
	bl_idname = "object.strippifytest"
	bl_label = "Strippify (testing)"
	bl_description = "Strippifies the active model object"

	doConcat: BoolProperty(
		name = "Concat",
		description="Combines all strips into one big strip",
		default=False
		)

	doSwaps: BoolProperty(
		name = "Utilize Swapping",
		description = "Utilizes swapping when creating strips, which can result in a smaller total strip count",
		default = False
		)

	raiseTopoError: BoolProperty(
		name = "Raise Topo Error",
		description = "Raise Topo Error if any occur",
		default = False
		)

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		import os
		os.system("cls")
		obj = context.active_object
		if obj is None or not isinstance(obj.data, bpy.types.Mesh):
			print("active object not a mesh")
			return {'FINISHED'}

		ob_for_convert = obj.original
		me = ob_for_convert.to_mesh(preserve_all_data_layers=True)
		common.trianglulateMesh(me)

		# creating the index list
		indexList = [0] * len(me.polygons) * 3

		for i, p in enumerate(me.polygons):
			for j, li in enumerate(p.loop_indices):
				indexList[i * 3 + j] = me.loops[li].vertex_index

		# strippifying it
		from . import strippifier
		try:
			indexStrips = strippifier.Strippify(indexList, doSwaps = self.doSwaps, concat = self.doConcat, raiseTopoError=self.raiseTopoError)
		except strippifier.TopologyError as e:
			self.report({'WARNING'}, "Topology error!\n" + str(e))
			return {'CANCELLED'}


		empty = bpy.data.objects.new(obj.data.name + "_str", None)
		context.collection.objects.link(empty)
		for i, s in enumerate(indexStrips):
			# making them lists so blender can use them

			verts = dict()
			for p in s:
				verts[p] = me.vertices[p].co

			indexList = list()
			firstTri = [s[i] for i in range(3)]

			rev = len(set(firstTri)) == 3
			for j in range(0 if rev else 1, len(s)-2):
				if rev:
					p = [s[j+1], s[j], s[j+2]]
				else:
					p = [s[j], s[j+1], s[j+2]]
				if len(set(p)) < 3:
					print("something wrong...")
				indexList.append(p)
				rev = not rev

			keys = list(verts.keys())
			indexList = [[keys.index(i) for i in l] for l in indexList]
			verts = list(verts.values())

			mesh = bpy.data.meshes.new(name = obj.data.name + "_str_" + str(i))
			mesh.from_pydata(verts, [], indexList)
			meObj = bpy.data.objects.new(mesh.name, object_data = mesh)
			context.collection.objects.link(meObj)
			meObj.parent = empty

		return {'FINISHED'}
