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
from configparser import ConfigParser
#endregion

tools = [
	"\\SAToolsHub.exe",
	"\\tools\\SALVL.exe",
	"\\tools\\SAMDL.exe",
	"\\tools\\TextureEditor.exe"
]

path = "D:\Modding\Sonic Adventure\SA Tools"

def openTool(idx):
	toolpath = path + tools[idx]
	print(toolpath)
	subprocess.Popen(toolpath)

def saveConfig(addonPath, toolDir, projFile):
	config = ConfigParser()
	cfgfile = open(addonPath + "\\config.ini", 'w')
	config.add_section('Settings')
	config.set('Settings', 'Tools', toolDir)
	config.set('Settings', 'Project', projFile)
	config.write(cfgfile)
	cfgfile.close()

def readConfig(addonPath):
	config = ConfigParser()
	cfgfile = open(addonPath + "\\config.ini")
	config.read(cfgfile)
	toolPath = config.get('Settings', 'Tools')
	sapPath = config.get('Settings', 'Project')

class openToolsHub(bpy.types.Operator):
	bl_idname = "sap.opentoolshub"
	bl_label = "Open SA Tools Hub"
	bl_description = "Opens the SA Tools Hub program."

	toolPath: StringProperty(default='')

	@classmethod
	def poll(self, context):
		if self.toolPath is "" or os.path.exist(self.toolPath + tools[1]) is False:
			return False
		else:
			return True

	def execute(self, context):
		openTool(0)
		return {'FINISHED'}

class openSALVL(bpy.types.Operator):
	bl_idname = "sap.opensalvl"
	bl_label = "Open SALVL"
	bl_description = "Opens the SALVL program."

	toolPath: StringProperty(default='')

	@classmethod
	def poll(self, context):
		if self.toolPath is "" or os.path.exist(self.toolPath + tools[1]) is False:
			return False
		else:
			return True

	def execute(self, context):
		openTool(1)
		return {'FINISHED'}

class openSAMDL(bpy.types.Operator):
	bl_idname = "sap.opensamdl"
	bl_label = "Open SAMDL"
	bl_description = "Opens the SAMDL program."

	toolPath: StringProperty(default='')

	@classmethod
	def poll(self, context):
		if self.toolPath is "" or os.path.exist(self.toolPath + tools[1]) is False:
			return False
		else:
			return True

	def execute(self, context):
		openTool(2)
		return {'FINISHED'}

class openTexEdit(bpy.types.Operator):
	bl_idname = "sap.opentexedit"
	bl_label = "Open Texture Editor"
	bl_description = "Opens the Texture Editor program."

	toolPath: StringProperty(default='')

	@classmethod
	def poll(self, context):
		if self.toolPath is "" or os.path.exist(self.toolPath + tools[1]) is False:
			return False
		else:
			return True

	def execute(self, context):
		openTool(3)
		return {'FINISHED'}

class saveProjectPreferences(bpy.types.Operator):
	bl_idname = "sap.saveconfig"
	bl_label = "Save Project Configuration"
	bl_description = "Saves the current Project Configuration."

	toolPath: StringProperty(default='')

	@classmethod
	def poll(self, context):
		if self.toolPath is "" or os.path.exist(self.toolPath + tools[1]) is False:
			return False
		else:
			return True

	def execute(self, context):
		return { 'FINISHED' }
