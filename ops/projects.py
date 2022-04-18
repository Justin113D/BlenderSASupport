#region Standard Imports
import bpy
import addon_utils
import os, os.path
import shutil
import subprocess
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

from ..prop.properties import (
	SAEditPanelSettings
)
#endregion

tools = [
	"\\SAToolsHub.exe",
	"\\tools\\SALVL.exe",
	"\\tools\\SAMDL.exe",
	"\\tools\\TextureEditor.exe"
]

def openTool(idx, useArgs: bool):
	settings = bpy.context.scene.saSettings
	
	path = common.get_prefs().toolspath
	toolpath = path + tools[idx]

	if useArgs:
		if settings.ProjectFilePath is not None:
			args = "\"" + settings.ProjectFilePath + "\""
			executePath = toolpath + " " + args
			subprocess.Popen(executePath)
		else:
			subprocess.Popen(toolpath)
	else:
		subprocess.Popen(toolpath)

class openToolsHub(bpy.types.Operator):
	bl_idname = "sap.opentoolshub"
	bl_label = "Open SA Tools Hub"
	bl_description = "Opens the SA Tools Hub program."

	def execute(self, context):

		openTool(0, True)
		return {'FINISHED'}

class openSALVL(bpy.types.Operator):
	bl_idname = "sap.opensalvl"
	bl_label = "Open SALVL"
	bl_description = "Opens the SALVL program."

	def execute(self, context):
		openTool(1, True)
		return {'FINISHED'}

class openSAMDL(bpy.types.Operator):
	bl_idname = "sap.opensamdl"
	bl_label = "Open SAMDL"
	bl_description = "Opens the SAMDL program."

	def execute(self, context):
		openTool(2, True)
		return {'FINISHED'}

class openTexEdit(bpy.types.Operator):
	bl_idname = "sap.opentexedit"
	bl_label = "Open Texture Editor"
	bl_description = "Opens the Texture Editor program."

	def execute(self, context):
		openTool(3, False)
		return {'FINISHED'}