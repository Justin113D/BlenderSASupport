import bpy
import os
import shutil
from .. import common, setReader
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

class ImportMDL(bpy.types.Operator, ImportHelper):
	"""Imports any sonic adventure mdl file"""
	bl_idname = "import_scene.mdl"
	bl_label = "Sonic Adv. model (.*mdl)"
	bl_options = {'PRESET', 'UNDO'}

	filter_glob: StringProperty(
		default="*.sa1mdl;*.sa2mdl;*.sa2bmdl;",
		options={'HIDDEN'},
		)

	noDoubleVerts: BoolProperty(
		name = "Merge double vertices",
		description = "Merge the doubled vertices after importing",
		default = True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	files: CollectionProperty(
		name='File paths',
		type=bpy.types.OperatorFileListElement
		)

	def execute(self, context):
		from . import file_MDL

		path = os.path.dirname(self.filepath)
		for f in self.files:
			file_MDL.read(context, path + "\\" + f.name, self.noDoubleVerts, self.console_debug_output)

		return {'FINISHED'}

class ImportLVL(bpy.types.Operator, ImportHelper):
	"""Imports any sonic adventure lvl file"""
	bl_idname = "import_scene.lvl"
	bl_label = "Sonic Adv. level (.*lvl)"
	bl_options = {'PRESET', 'UNDO'}

	filter_glob: StringProperty(
		default="*.sa1lvl;*.sa2lvl;*.sa2blvl;",
		options={'HIDDEN'},
		)

	noDoubleVerts: BoolProperty(
		name = "Merge double vertices",
		description = "Merge the doubled vertices after importing",
		default = True,
		)

	files: CollectionProperty(
		name='File paths',
		type=bpy.types.OperatorFileListElement
		)

	console_debug_output: BoolProperty(
			name = "Console Output",
			description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
			default = False,
			)

	def execute(self, context):
		from . import file_LVL

		path = os.path.dirname(self.filepath)
		for f in self.files:
			file_LVL.read(context, path + "\\" + f.name, self.noDoubleVerts, self.console_debug_output)
		return {'FINISHED'}

class ImportTexFile(bpy.types.Operator, ImportHelper):
	"""Imports any sonic adventure texture file"""
	bl_idname = "import_texture.tex"
	bl_label = "Import SA tex file"

	filter_glob: StringProperty(
		default="*.pak;*.gvm;*.pvm;*.pvmx;*.txt;*.tls",
		options={'HIDDEN'},
		)

	def stop(self):
		self.report({'WARNING'}, "File not a valid texture file!")
		return {'CANCELLED'}

	def execute(self, context):
		import os
		extension = os.path.splitext(self.filepath)[1]
		if extension == '.txt':
			#reading all lines from the index file
			content: List[str] = None
			with open(self.filepath) as f:
				content = f.readlines()
			folder = os.path.dirname(self.filepath)
			textures: List[Tuple[int, str]] = list()

			# validating index file
			for c in content:
				c = c.strip().split(',')
				if len(c) < 2:
					return self.stop()
				try:
					gIndex = int(c[0])
				except:
					return self.stop()
				texturePath = folder + "\\" + c[1]
				if not os.path.isfile(texturePath):
					return self.stop()
				textures.append((gIndex, texturePath))

			bpy.ops.scene.sacleartexturelist()
			texList = context.scene.saSettings.textureList
			for i, t in textures:
				img = None
				for image in bpy.data.images:
					if image.filepath == t:
						img = image
						break
				if img is None:
					img = bpy.data.images.load(t)
				img.use_fake_user = True
				tex = texList.add()
				tex.globalID = i
				tex.name = os.path.splitext(os.path.basename(t))[0]
				tex.image = img
		elif extension == '.tls':
			content: List[str] = None
			with open(self.filepath) as f:
				content = f.readlines()
			folder = os.path.dirname(self.filepath)
			textures: List[Tuple[int, str]] = list()

			for c in content:
				c = c.strip().split('.')
				texturePath = folder + "\\" + c[0] + ".png"
				if not (os.path.isfile(texturePath)):
					return self.stop()
				textures.append((0, texturePath))

			bpy.ops.scene.sacleartexturelist()
			texList = context.scene.saSettings.textureList
			for i, t in textures:
				img = None 
				for image in bpy.data.images:
					if image.filepath == t:
						img = image
						break
				if img is None:
					img = bpy.data.images.load(t)
				img.use_fake_user = True
				tex = texList.add()
				tex.globalID = i
				tex.name = os.path.splitext(os.path.basename(t))[0]
				tex.image = img
		return {'FINISHED'}

class LoadSetFile(bpy.types.Operator, ImportHelper):
	"""Loads a Set file and places objects at the correct locations"""
	bl_idname = "object.load_set"
	bl_label = "Load SET file"

	filter_glob: StringProperty(
		default="*.bin",
		options={'HIDDEN'},
		)

	bigEndian: BoolProperty(
		name="Big Endian",
		description="Sets Big Endian for loading Set files (DC Games/SADXPC Disable, GC Games/SA2BPC Enable)",
		default=True,
		)

	def execute(self, context):
		setReader.ReadFile(self.filepath, context, self.bigEndian)
		return {'FINISHED'}

class LoadAnimFile(bpy.types.Operator, ImportHelper):
	"""Loads animations from saanim files to a selected armature"""
	bl_idname = "object.load_saanim"
	bl_label = "Import JSON Animation"
	bl_description = "Loads JSON animation files to a selected armature"

	filter_glob: StringProperty(
		default="*.json",
		options={'HIDDEN'},
		)

	files: CollectionProperty(
		name='File paths',
		type=bpy.types.OperatorFileListElement
		)

	naming: EnumProperty(
		name="Animation naming",
		description="The way in which the animations should be named",
		items=(('FILE', "File", "Names the animation after the file"),
			   ('CONTENT', "Content", "Names the animation after the contents name"),
			   ('COMB', "File_Content", "Combines both names types to name the animation")),
		default='CONTENT'
		)

	@classmethod
	def poll(cls, context):
		active = context.active_object
		if active is None:
			return False
		return active.type == 'ARMATURE'

	def execute(self, context):
		from . import file_SAANIM
		path = os.path.dirname(self.filepath)

		#if context.active_object.animation_data == None:
		#    context.active_object.animation_data_create()

		for f in self.files:
			try:
				file_SAANIM.read(path + "\\" + f.name, self.naming, context.active_object)
			except file_SAANIM.ArmatureInvalidException as e:
				self.report({'WARNING'}, str(e))
				continue
		return {'FINISHED'}
