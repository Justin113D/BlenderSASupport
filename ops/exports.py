import bpy
import os
import shutil
from .. import common, setReader, strippifier
from bpy.props import (
	BoolProperty,
	FloatProperty,
	FloatVectorProperty,
	IntProperty,
	EnumProperty,
	StringProperty,
	CollectionProperty
	)
from ..parse import pini
from bpy_extras.io_utils import ExportHelper, ImportHelper
from typing import List, Dict, Union, Tuple

def removeFile() -> None:									## Removes the temporarily created export file.
	'''Removes the currently assigned temporary export file'''

	# get the export file (its set from outside this script,
	# so for some reason it only works with the __init__ in front of it)
	fileW = common.exportedFile
	# if the file is assigned, close and remove it
	if fileW is not None:
		fileW.close()
		os.remove(fileW.filepath)
		common.exportedFile = None

def exportFile(op, outType, context, **keywords):			## Main definition for exporting files.
	from .. import file_MDL, file_LVL
	common.exportedFile = None

	profile_output = keywords["profile_output"]
	del keywords["profile_output"]

	if profile_output:
		import cProfile
		import pstats
		pr = cProfile.Profile()
		pr.enable()

	try:
		if outType == 'MDL':
			out = file_MDL.write(context, **keywords)
		elif outType == 'LVL':
			out = file_LVL.write(context, **keywords)
		elif outType == 'ANIM':
			from .. import file_SAANIM
			out = file_SAANIM(keywords["filepath"], context.active_object)
	except (strippifier.TopologyError, common.ExportError) as e:
		op.report({'WARNING'}, "Export stopped!\n" + str(e))
		removeFile()
		if profile_output:
			pr.disable()
		return {'CANCELLED'}
	except Exception as e:
		removeFile()
		if profile_output:
			pqr.disable()
		raise e

	filepath = keywords["filepath"]

	if profile_output:
		pr.disable()
		prPath = filepath + ".profile"
		if(os.path.isfile(prPath)):
			os.remove(prPath)
		with open(prPath, 'w') as prStream:
			ps = pstats.Stats(pr, stream=prStream)
			ps.sort_stats("cumulative").print_stats()

	# moving and renaming the temporary file
	# Note: this is also removing the file that existed before
	fileW = common.exportedFile

	if(os.path.isfile(filepath)):
		os.remove(filepath)
	shutil.move(fileW.filepath, filepath)

	return {'FINISHED'}

class ExportSA1MDL(bpy.types.Operator, ExportHelper):		## Exports an SA1MDL file.
	"""Export objects into an SA1 model file"""
	bl_idname = "export_scene.sa1mdl"
	bl_label = "SA1 model (.sa1mdl)"
	bl_description = "Exports scene or selected items to an sa1mdl file."
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa1mdl"

	filter_glob: StringProperty(
		default="*.sa1mdl;",
		options={'HIDDEN'},
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_MDL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
		keywords["write_Specular"] = True
		keywords["export_format"] = 'SA1'
		return exportFile(self, 'MDL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportSA2MDL(bpy.types.Operator, ExportHelper):		## Exports an SA2MDL file.
	"""Export objects into an SA2 model file"""
	bl_idname = "export_scene.sa2mdl"
	bl_description = "Exports scene or selected items to an sa2mdl file."
	bl_label = "SA2 model (.sa2mdl)"
	
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa2mdl"

	filter_glob: StringProperty(
		default="*.sa2mdl;",
		options={'HIDDEN'},
		)

	write_Specular: BoolProperty(
		name = "Write Specular",
		description = "Write specular info to materials",
		default = False
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_MDL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
		keywords["export_format"] = 'SA2'
		return exportFile(self, 'MDL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "write_Specular")
		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportSA2BMDL(bpy.types.Operator, ExportHelper):		## Exports an SA2BMDL file.
	"""Export objects into an SA2B model file"""
	bl_idname = "export_scene.sa2bmdl"
	bl_label = "SA2B model (.sa2bmdl)"
	bl_description = "Exports scene or selected items to an sa2bmdl file."
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa2bmdl"

	filter_glob: StringProperty(
		default="*.sa2bmdl;",
		options={'HIDDEN'},
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_MDL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
		keywords["write_Specular"] = False
		keywords["export_format"] = 'SA2B'
		return exportFile(self, 'MDL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportSA1LVL(bpy.types.Operator, ExportHelper):		## Exports an SA1LVL file.
	"""Export scene into an SA1 level file"""
	bl_idname = "export_scene.sa1lvl"
	bl_label = "SA1 level (.sa1lvl)"
	bl_description = "Exports scene or selected items to an sa1lvl file."
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa1lvl"

	filter_glob: StringProperty(
		default="*.sa1lvl;",
		options={'HIDDEN'},
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_LVL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
		keywords["write_Specular"] = True
		keywords["export_format"] = 'SA1'
		return exportFile(self, 'LVL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportSA2LVL(bpy.types.Operator, ExportHelper):		## Exports an SA2LVL file.
	"""Export scene into an SA2 level file"""
	bl_idname = "export_scene.sa2lvl"
	bl_label = "SA2 level (.sa2lvl)"
	bl_description = "Exports scene or selected items to an sa2lvl file."
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa2lvl"

	filter_glob: StringProperty(
		default="*.sa2lvl;",
		options={'HIDDEN'},
		)

	write_Specular: BoolProperty(
		name = "Write Specular",
		description = "Write specular info to materials",
		default = False
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_LVL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))
		keywords["export_format"] = 'SA2'
		return exportFile(self, 'LVL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "write_Specular")
		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportSA2BLVL(bpy.types.Operator, ExportHelper):		## Exports an SA2BLVL file.
	"""Export scene into an SA2B level file"""
	bl_idname = "export_scene.sa2blvl"
	bl_label = "SA2B level (.sa2blvl)"
	bl_description = "Exports scene or selected items to an sa2blvl file."
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ".sa2blvl"

	filter_glob: StringProperty(
		default="*.sa2blvl;",
		options={'HIDDEN'},
		)

	use_selection: BoolProperty(
		name="Selection Only",
		description="Export selected objects only",
		default=False,
		)

	apply_modifs: BoolProperty(
		name="Apply Modifiers",
		description="Apply active viewport modifiers",
		default=True,
		)

	console_debug_output: BoolProperty(
		name = "Console Output",
		description = "Shows exporting progress in Console (Slows down Exporting Immensely)",
		default = False,
		)

	profile_output: BoolProperty(
		name = "Profiling output",
		description = "Records where the addon spends most of its time and writes it to a file next to the actual output file",
		default = False
		)

	def execute(self, context):
		from .. import file_LVL
		keywords = self.as_keywords(ignore=( "check_existing", "filter_glob"))

		keywords["write_Specular"] = False
		keywords["export_format"] = 'SA2B'
		return exportFile(self, 'LVL', context, **keywords)

	def draw(self, context):
		layout: bpy.types.UILayout = self.layout
		layout.alignment = 'RIGHT'

		layout.prop(self, "use_selection")
		layout.prop(self, "apply_modifs")
		layout.separator()
		layout.prop(self, "console_debug_output")
		layout.prop(self, "profile_output")

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportPAK(bpy.types.Operator, ExportHelper):			## Non-functional. Planned to export PAK texture archives.
	bl_idname = "export_texture.pak"
	bl_label = "Export as PAK (SA2)"

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportPVMX(bpy.types.Operator, ExportHelper):			## Non-functional. Planned to export PVMX texture archives.
	bl_idname = "export_texture.pvmx"
	bl_label = "Export as PVMX (SADX)"

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportAnim(bpy.types.Operator, ExportHelper):			## Exports an SAANIM file.
	bl_idname = "object.export_anim"
	bl_label = "Export JSON Animation"
	bl_description = "Exports animation data to a valid json file."

	filename_ext = ".json"

	filter_glob: StringProperty(
		default="*.json;",
		options={'HIDDEN'},
		)

	bakeAll: BoolProperty(
		name = "Bake all keyframes",
		description="Bakes all keyframes of the exported curves, instead of calculating only the necessary ones",
		default=False
		)

	shortRot: BoolProperty(
		name = "Short Rotation",
		description="Save rotation values in a short, not an int. Required for chao anmimations",
		default = False
		)

	bezierInterpolation: BoolProperty(
		name = "Bezier Interpolation",
		description = "Set keyframe interoplation mode to bezier",
		default = False
		)

	currentTransforms: BoolProperty(
		name = "Current Transforms",
		description="If e.g. one of the 3 positional channels are not set in the animation, then use the current corresponding channel of the bone for that channel instead of a default value (always 0, except W in quaternions and scales which is 1)",
		default=False
		)

	@classmethod
	def poll(cls, context):
		active = context.active_object
		if active is None:
			return False
		if active.type != 'ARMATURE':
			return False
		if active.animation_data is None:
			return False
		return active.animation_data.action != None

	def execute(self, context):
		#return exportFile(self, 'ANIM', context, self.as_keywords())
		from .. import file_SAANIM
		file_SAANIM.write(self.filepath, self.bakeAll, self.shortRot, self.bezierInterpolation, self.currentTransforms, context.active_object)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportCurve(bpy.types.Operator, ExportHelper):
	bl_idname = "object.export_curve"
	bl_label = "Export Path Data"
	bl_description = "Currently non-functional."

	filename_ext = ".ini"

	filter_glob: StringProperty(
		default="*.ini;",
		options={'HIDDEN'},
		)

	curveTypes: EnumProperty(
		name='Curve Code',
		description='Set Code address for Path to use in-game.',
		items = (
			('none', 'No Code', 'Code Address is 0'),
			('sa1_loop', 'SA1 Loops', 'Used on most paths where the player is moved, ie Loops.'),
			('sa2_loop', 'SA2 Loops', 'Used on most paths where the player is moved, ie Loops.'),
			('sa2_rail', 'SA2 Grind Rails', 'Used for most grind rails.'),
			('sa2_hand', 'SA2 Hand Rails', 'Used for the hand/gravity rails used in Crazy Gadget.')
		),
		default='none'
	)

	@classmethod
	def poll(cls, context):
		active = context.active_object
		if active is None:
			return False
		elif active.type != 'CURVE':
			return False
		else:
			return True

	def execute(self, context):
		obj = context.active_object
		curve = obj.data.splines[0]
		points = obj.children
		pini.PathData.toIni(self.filepath, curve, points, self.curveTypes)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportShapeMotion(bpy.types.Operator, ExportHelper):			## Exports an SAANIM file.
	'''Export Shape Motions'''
	bl_idname = "object.export_shape"
	bl_label = "Export Shape Animation"
	bl_description = "Exports Shape Keys to a valid json file."

	filename_ext = ".json"

	filter_glob: StringProperty(
		default="*.json;",
		options={'HIDDEN'},
		)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		if (obj != None) and (obj.type == 'MESH'):
			if ((obj.data.shape_keys != None) and (len(obj.data.shape_keys.key_blocks) > 1)):
				return True
			else:
				return False
		else:
			return False

	def execute(self, context):
		from .. import file_SAANIM
		file_SAANIM.writeShape(self.filepath, context.active_object)
		return {'FINISHED'}

	def invoke(self, context, event):
		self.filepath = common.getDefaultPath()
		wm = context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}