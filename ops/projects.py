#region Standard Imports
import bpy
import subprocess
from .. import common
#endregion

tools = [
	"\\SAToolsHub.exe",
	"\\tools\\SALVL.exe",
	"\\tools\\SAMDL.exe",
	"\\tools\\TextureEditor.exe"
]

def openTool(idx, useArgs: bool):
	settings = bpy.context.scene.saProjInfo
	
	path = common.get_prefs().toolspath
	toolpath = path + tools[idx]

	if useArgs:
		if (settings.ProjectFilePath != "") and (idx != 3):
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

def GetDataFiles(file, context):
	dataFiles = []
	
	return dataFiles

def GetMdlFiles(file, context):
	mdlFiles = []

	return mdlFiles