import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import (
	BoolProperty,
	EnumProperty,
	StringProperty,
	CollectionProperty
	)
import os
from typing import List, Tuple
from .. import common, setReader
from .. import file_SAANIM
from ..text.saproject import ProjectFile
from ..text.mod import ModFile
from .object import	CreatePath
from ..text.satex import SATexFile
from ..text.paths import PathData

class ImportMDL(bpy.types.Operator, ImportHelper):			## Imports *MDL files made with the SA Tools.
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
		from .. import file_MDL

		path = os.path.dirname(self.filepath)
		for f in self.files:
			file_MDL.read(context, path + "\\" + f.name, self.noDoubleVerts, self.console_debug_output)

		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ImportLVL(bpy.types.Operator, ImportHelper):			## Imports *LVL files made with the SA Tools.
	"""Imports any sonic adventure lvl file"""
	bl_idname = "import_scene.lvl"
	bl_label = "Sonic Adv. level (.*lvl)"
	bl_options = {'PRESET', 'UNDO'}

	filter_glob: StringProperty(
		default="*.sa1lvl;*.sa2lvl;*.sa2blvl;",
		options={'HIDDEN'},
		)

	fixView: BoolProperty(
		name="Adjust Clip Distance",
		description="Adjusts viewport clipping values.",
		default=False
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
		from .. import file_LVL

		if self.fixView == True:
			context.space_data.clip_start = 1.0
			context.space_data.clip_end = 10000.0

		path = os.path.dirname(self.filepath)
		for f in self.files:
			file_LVL.read(context, path + "\\" + f.name, self.noDoubleVerts, self.console_debug_output)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ImportTexFile(bpy.types.Operator, ImportHelper):		## Imports texture archives. Only texture packs supported currently.
	"""Imports any sonic adventure texture file"""
	bl_idname = "import_texture.tex"
	bl_label = "Import SA tex file"

	filter_glob: StringProperty(
		default="*.pak;*.gvm;*.pvm;*.pvmx;*.txt;*.tls;*.satex",
		options={'HIDDEN'},
		)

	def stop(self):
		self.report({'WARNING'}, "File not a valid texture file!")
		return {'CANCELLED'}

	def execute(self, context):
		import os
		extension = os.path.splitext(self.filepath)[1]
		print(extension)
		folder = os.path.dirname(self.filepath)
		textures: List[Tuple[int, str]] = list()
		loaded = False
		satexf = SATexFile()
		if extension == '.txt' or extension == '.tls':
			content: List[str] = None
			with open(self.filepath) as f:
				content = f.readlines()
			loaded = True
		elif extension == '.satex':
			satexf.fromIni(self.filepath)
			loaded = True
		
		if loaded:
			if extension == '.txt':
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
			elif extension == '.tls':
				for c in content:
					c = c.strip().split('.')
					texturePath = folder + "\\" + c[0] + ".png"
					if not (os.path.isfile(texturePath)):
						return self.stop()
					textures.append((0, texturePath))
			elif extension == '.satex':
				for c in satexf.TextureNames:
					print(c)
					texturePath = folder + "\\" + c
					if not (os.path.isfile(texturePath)):
						return self.stop()
					textures.append((0, texturePath))

			self.LoadTextures(context, textures)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def LoadTextures(self, context, textures):
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

class LoadSetFile(bpy.types.Operator, ImportHelper):		## Imports a set file to empties with generic position, rotation, and scaling applie.
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
		default=False,
		)

	useIDFirst: BoolProperty(
		name="Use Item Index as Prefix",
		description="Uses the item's index in the set file as the prefix. Setting to false will set the index to be used as a suffix.",
		default=True,
	)

	def execute(self, context):
		setReader.ReadFile(self.filepath, context, self.bigEndian, self.useIDFirst)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadCamFile(bpy.types.Operator, ImportHelper):		## Imports a set file to empties with generic position, rotation, and scaling applie.
	"""Loads a Cam file and places Empties at the correct locations"""
	bl_idname = "object.load_cam"
	bl_label = "Load CAM file"

	filter_glob: StringProperty(
		default="*.bin",
		options={'HIDDEN'},
		)

	bigEndian: BoolProperty(
		name="Big Endian",
		description="Sets Big Endian for loading CAM files (DC Games/SADXPC Disable, GC Games/SA2BPC Enable)",
		default=False,
		)

	useIDFirst: BoolProperty(
		name="Use Camera Index as Prefix",
		description="Uses the camera's index in the cam file as the prefix. Setting to false will set the index to be used as a suffix.",
		default=True,
	)

	isSA2: BoolProperty(
		name="Is SA2 Cam",
		description="Toggle for SA2 cam files.",
		default=False
	)

	def execute(self, context):
		setReader.ReadCamFile(self.filepath, context, self.bigEndian, self.useIDFirst, self.isSA2)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadAnimFile(bpy.types.Operator, ImportHelper):		## Imports a SAANIM file made with the SA Tools.
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
		default='FILE'
		)

	@classmethod
	def poll(cls, context):
		active = context.active_object
		if active is None:
			return False
		return active.type == 'ARMATURE'

	def execute(self, context):
		from .. import file_SAANIM
		path = os.path.dirname(self.filepath)

		#if context.active_object.animation_data == None:
		#    context.active_object.animation_data_create()

		for f in self.files:
			try:
				file_SAANIM.readAnim(path + "\\" + f.name, self.naming, context.active_object)
			except file_SAANIM.ArmatureInvalidException as e:
				self.report({'WARNING'}, str(e))
				continue
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadShapeMotion(bpy.types.Operator, ImportHelper):		## Imports a SAANIM file made with the SA Tools.
	"""Loads Json formatted Shape Motions to selected objects"""
	bl_idname = "object.load_shapemotion"
	bl_label = "Import JSON Shape Motion"
	bl_description = "Loads a Json formatted Shape Motion"

	filter_glob: StringProperty(
		default="*.json",
		options={'HIDDEN'},
		)

	files: CollectionProperty(
		name='File paths',
		type=bpy.types.OperatorFileListElement
		)

	@classmethod
	def poll(cls, context):
		if (context.active_object != None):
			if (context.active_object.type == 'MESH'):
				return True
			else:
				return False
		else:
			return False


	def execute(self, context):
		from .. import file_SAANIM
		path = os.path.dirname(self.filepath)

		for f in self.files:
			try:
				file_SAANIM.readShape(path + "\\" + f.name, context.active_object)
			except file_SAANIM.ArmatureInvalidException as e:
				self.report({'WARNING'}, str(e))
				continue
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadCameraMotion(bpy.types.Operator, ImportHelper):		## Imports a SAANIM file made with the SA Tools.
	"""Loads Json formatted Camera Motions"""
	bl_idname = "object.load_cammotion"
	bl_label = "Import Camera Motion"
	bl_description = "Loads a Json formatted Camera Motion"

	filter_glob: StringProperty(
		default="*.json",
		options={'HIDDEN'},
		)

	files: CollectionProperty(
		name='File paths',
		type=bpy.types.OperatorFileListElement
		)

	def execute(self, context):
		path = os.path.dirname(self.filepath)

		for f in self.files:
			try:
				file_SAANIM.readAnim_Camera(path + "\\" + f.name)
			except file_SAANIM.ArmatureInvalidException as e:
				self.report({'WARNING'}, str(e))
				continue
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadPathFile(bpy.types.Operator, ImportHelper):
	bl_idname = "object.load_pathini"
	bl_label = "Import Path INI Files"
	bl_description = "Loads a Path from an ini file."

	filter_glob: StringProperty(
		default="*.ini",
		options={'HIDDEN'},
		)

	def execute(self, context):
		path = PathData()
		path.fromIni(self.filepath)
		newCol = bpy.data.collections.new('ImportPath_' + path.Name)
		bpy.context.scene.collection.children.link(newCol)
		CreatePath(path.Name, path.Entries, newCol)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class LoadProjectFile(bpy.types.Operator, ImportHelper):
	bl_idname = "object.load_project"
	bl_label = "Open SA Project File"
	bl_description = "Opens an SA Project (*.sap) file and loads some data into Blender."

	filter_glob: StringProperty(
		default="*.sap",
		options={'HIDDEN'}
	)

	def execute(self, context):
		ProjInfo = context.scene.saProjInfo
		ProjInfo.ProjectFilePath = self.filepath
		projFile = ProjectFile.ReadProjectFile(self.filepath)
		ProjInfo.ProjectFolder = ProjectFile.GetProjectFolder(projFile)
		modFilePath = ProjInfo.ProjectFolder + "mod.ini"
		if os.path.isfile(modFilePath):
			modFile = ModFile.ReadFile(modFilePath)
			ProjInfo.ModName = modFile.Name
			ProjInfo.ModAuthor = modFile.Author
			ProjInfo.ModDescription = modFile.Description
			ProjInfo.ModVersion = modFile.Description
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
