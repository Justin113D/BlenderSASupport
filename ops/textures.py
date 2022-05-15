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

class AddTextureSlot(bpy.types.Operator):		## Adds a texture slot to the Scene Texture List.
	bl_idname = "scene.saaddtexturesslot"
	bl_label="Add texture"
	bl_description="Adds texture to the texture list"


	def execute(self, context):
		settings = context.scene.saSettings

		# getting next usable global id
		ids = list()
		for t in settings.textureList:
			ids.append(t.globalID)
		ids.sort(key=lambda x: x)
		globalID = -1
		for i, index in enumerate(ids):
			if i != index:
				globalID = i
				break
		if globalID == -1:
			globalID = len(settings.textureList)

		# creating texture
		tex = settings.textureList.add()
		#tex.image_user
		settings.active_texture_index = len(settings.textureList) -1

		tex.name = "Texture"
		tex.globalID = globalID

		return {'FINISHED'}

class RemoveTextureSlot(bpy.types.Operator):	## Removes the selected texture slot from the Scene Texture List.
	bl_idname = "scene.saremovetexturesslot"
	bl_label="Remove texture"
	bl_description="Removes the selected texture from the texture list"

	def execute(self, context):
		settings = context.scene.saSettings
		settings.textureList.remove(settings.active_texture_index)

		settings.active_texture_index -= 1
		if len(settings.textureList) == 0:
			settings.active_texture_index = -1
		elif settings.active_texture_index < 0:
			settings.active_texture_index = 0

		return {'FINISHED'}

class MoveTextureSlot(bpy.types.Operator):		## Moves the selected texture slot in the Scene Texture List.
	bl_idname = "scene.samovetexturesslot"
	bl_label="Move texture"
	bl_description="Moves texture slot in list"

	direction: EnumProperty(
		name="Direction",
		items=( ('UP',"up","up"),
				('DOWN',"down","down"), )
		)

	def execute(self, context):
		settings = context.scene.saSettings
		newIndex = settings.active_texture_index + (-1 if self.direction == 'UP' else 1)
		if not (newIndex == -1 or newIndex >= len(settings.textureList)):
			if settings.correct_Material_Textures:
				for m in bpy.data.materials:
					props: SAMaterialSettings = m.saSettings
					if props.b_TextureID == newIndex:
						props.b_TextureID = settings.active_texture_index
					elif props.b_TextureID == settings.active_texture_index:
						props.b_TextureID = newIndex

			settings.textureList.move(settings.active_texture_index, newIndex)

			settings.active_texture_index = newIndex
		return {'FINISHED'}

class ClearTextureList(bpy.types.Operator):		## Clears all entries from the Scene Texture List.
	bl_idname = "scene.sacleartexturelist"
	bl_label="Clear list"
	bl_description="Removes all entries from the list"

	def execute(self, context):
		settings = context.scene.saSettings
		settings.active_texture_index = -1

		for t in settings.textureList:
			if t.image is not None:
				t.image.use_fake_user = False


		settings.textureList.clear()
		return {'FINISHED'}

class AutoNameTextures(bpy.types.Operator):		## Autonames Scene Texture List entries based on their assigned image names.
	bl_idname = "scene.saautonametexlist"
	bl_label="Autoname entries"
	bl_description="Renames all entries to the assigned texture"

	def execute(self, context):
		texList = context.scene.saSettings.textureList

		for t in texList:
			if t.image is not None:
				t.name = os.path.splitext(t.image.name)[0]
			else:
				t.name = "Texture"
		return {'FINISHED'}
