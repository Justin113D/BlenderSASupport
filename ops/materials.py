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

def autotexUpdate(context, newValue, DO):			## Definition for the auto-assign texture operator.
	# variables
	mats = []
	copyTex = []
	index = -1
	found = False

	# collections
	objects = context.visible_objects
	texList = context.scene.saSettings.textureList

	# place texList into array for ease of reference
	for t in texList:
		if DO:
			print("Process Texlist")
		if t.image is not None:
			copyTex.append(t.name)

	# loop through all objects
	for o in objects:
		#print("Checking Objects")
		if o.type == 'MESH':
			# if mesh type, check material slots
			for matslot in o.material_slots:
				if matslot.material:
					matProps : SAMaterialSettings = matslot.material.saSettings
					nodes = matslot.material.node_tree.nodes
					for n in nodes:
						# search valid materials for Texture Image input node
						if n.type == 'TEX_IMAGE':
							matname = os.path.splitext(str(n.image.name))[0]
							if matname in texList:
								if DO:
									print("Found, " + matname)
								index = copyTex.index(matname)
								if index > -1:
									# if updated index is > -1, update SA Material Texture ID
									matProps.b_TextureID = index
									if DO:
										print("Texture updated!")
									found = True
			
			# if Texture Image input cannot be found, check material name as backup.
			if found == False:
				for matslot in o.material_slots:
					if matslot.material:
						matname = matslot.material.name
						if matname in texList:
							if DO:
								print("Found, " + matname)
							index = copyTex.index(matname)
							if index > -1:
								# if updated index > -1, update SA Material Texture ID
								matProps.b_TextureID = index
								if DO:
									print("Texture updated!")
						else:
							print("Error! No matching texture for " + matname + "in object " + o.name)

class AutoAssignTextures(bpy.types.Operator):	## Auto-Assign texture IDs based on initial material's image name or material name.
	bl_idname = "scene.saautoassignmmd"
	bl_label = "Auto Assign Textures"
	bl_description = "Attempts to match texture or material names to an imported texlist. Only checks visible objects, may not work."

	def execute(self, context):
		DO = common.get_prefs().printDebug
		autotexUpdate(context, True, DO)
		return {'FINISHED'}

class ToPrincipledBsdf(bpy.types.Operator):		## Converts all materials in a scene to Principled BSDF for export.
	bl_idname = "scene.convmaterials"
	bl_label = "Convert to Principled BSDF"
	bl_description = "Converts materials to a Principled BSDF for exporting purposes."

	def execute(self, context):
		for m in bpy.data.materials:
			tree: bpy.types.NodeTree = m.node_tree
			nodes = tree.nodes
			out = nodes.get('Material Output')
			saShader = nodes.get('Group', None)
			texture = nodes.get('Image Texture', None)
			bsdf = nodes.new('ShaderNodeBsdfPrincipled')
			bsdf.inputs[5].default_value = 0

			if saShader is not None:
				nodes.remove(saShader)

			if texture is not None:
				tree.links.new(texture.outputs[0], bsdf.inputs[0]) # Assign texture
				tree.links.new(texture.outputs[1], bsdf.inputs[21]) # Assign alpha

			tree.links.new(bsdf.outputs[0], out.inputs[0])
			m.blend_method = 'CLIP'
		return {'FINISHED'}

class UpdateMaterials(bpy.types.Operator):		## Updates all materials in the scene to use the SA Shader.
	bl_idname = "scene.saupdatemats"
	bl_label="Update Materials"
	bl_description="Sets material nodetrees and variables of all selected objects to imitate how they would look in sadx/sa2"

	@classmethod
	def addSceneDrivers(cls):
		grp = bpy.data.node_groups["SAShader"]

		# Specular Toggle
		dr = grp.driver_add('nodes["DisplSpecular"].outputs[0].default_value')
		dr.driver.type = 'SCRIPTED'
		dr.driver.expression = 'var'
		var = dr.driver.variables.new()
		var.type = 'SINGLE_PROP'
		var.name = 'var'
		var.targets[0].id_type = 'SCENE'
		var.targets[0].id = bpy.context.scene
		var.targets[0].data_path = 'saSettings.DisplaySpecular'

		x = 0
		while x != 3:
			# Light Color
			dr = grp.driver_add('nodes["LightCol"].inputs[' + str(x) + '].default_value')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'SCENE'
			var.targets[0].id = bpy.context.scene
			var.targets[0].data_path = 'saSettings.LightColor[' + str(x) + ']'

			# Ambient Color
			dr = grp.driver_add('nodes["AmbientCol"].inputs[' + str(x) + '].default_value')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'SCENE'
			var.targets[0].id = bpy.context.scene
			var.targets[0].data_path = 'saSettings.LightAmbientColor[' + str(x) + ']'

			x += 1

		# Light Drivers
		light = 'nodes["LightDir"].inputs'
		# Light X
		dr = grp.driver_add(light + '[0].default_value')
		dr.driver.type = 'SCRIPTED'
		dr.driver.expression = 'var'
		var = dr.driver.variables.new()
		var.type = 'SINGLE_PROP'
		var.name = 'var'
		var.targets[0].id_type = 'SCENE'
		var.targets[0].id = bpy.context.scene
		var.targets[0].data_path = 'saSettings.LightDir[0]'

		# Light Y
		dr = grp.driver_add(light + '[1].default_value')
		dr.driver.type = 'SCRIPTED'
		dr.driver.expression = '-var'
		var = dr.driver.variables.new()
		var.type = 'SINGLE_PROP'
		var.name = 'var'
		var.targets[0].id_type = 'SCENE'
		var.targets[0].id = bpy.context.scene
		var.targets[0].data_path = 'saSettings.LightDir[2]'

		# Light Z
		dr = grp.driver_add(light + '[2].default_value')
		dr.driver.type = 'SCRIPTED'
		dr.driver.expression = 'var'
		var = dr.driver.variables.new()
		var.type = 'SINGLE_PROP'
		var.name = 'var'
		var.targets[0].id_type = 'SCENE'
		var.targets[0].id = bpy.context.scene
		var.targets[0].data_path = 'saSettings.LightDir[1]'

	@classmethod
	def addDriver(cls, material, path, dataPath, idx = -1, expression = 'var'):
		#mat = bpy.data.materials[material]
		dr = material.node_tree.driver_add(path, idx)
		dr.driver.type = 'SCRIPTED'
		dr.driver.expression = expression
		var = dr.driver.variables.new()
		var.type = 'SINGLE_PROP'
		var.name = 'var'
		var.targets[0].id_type = 'MATERIAL'
		var.targets[0].id = material
		var.targets[0].data_path = 'saSettings.' + dataPath

	def execute(self, context):
		# remove old trees

		ng = bpy.data.node_groups

		n = ng.find("UV Tiling")
		if n > -1:
			ng.remove(ng[n])

		n = ng.find("SAShader")
		if n > -1:
			ng.remove(ng[n])

		# now reload them them
		directory = os.path.dirname(os.path.realpath(__file__)) + "\\..\\Shaders.blend\\NodeTree\\"
		bpy.ops.wm.append(filename="UV Tiling", directory=directory)
		bpy.ops.wm.append(filename="SAShader", directory=directory)

		tilingGroup = ng[ng.find("UV Tiling")]
		saShaderGroup = ng[ng.find("SAShader")]
		envMapGroup = ng[ng.find("EnvMap")]

		#UpdateMaterials.addSceneDrivers()

		# The materials know whether the shader displays vertex colors based on the object color, its weird i know, but i didnt find any better way
#		import math
#		for o in context.scene.objects:
#			if o.type == 'MESH':
#				isNrm = o.data.saSettings.sa2ExportType == 'NRM'
#				r = o.color[0]
#				rc = bool(math.floor(r * 1000) % 2)
#
#				if isNrm and rc:
#					r = (math.floor(r * 1000) + (1 if r < 1 else (-1))) / 1000.0
#				elif not isNrm and not rc:
#					r = (math.floor(r * 1000) + ((-1) if r > 0 else 1)) / 1000.0
#				o.color[0] = r

		# Update all Materials within the Scene.
		for m in bpy.data.materials:
			#creating an settings nodes
			mProps = m.saSettings
			m.use_nodes = True
			m.show_transparent_back = False
			tree: bpy.types.NodeTree = m.node_tree
			nodes = tree.nodes
			nodes.clear()

			out = nodes.new("ShaderNodeOutputMaterial")
			saShader = nodes.new("ShaderNodeGroup")
			saShader.node_tree = saShaderGroup
			saShader.location = (-200, 0)
			tree.links.new(out.inputs[0], saShader.outputs[0])
			tex = nodes.new("ShaderNodeTexImage")
			tex.location = (-500, 0)
			tree.links.new(tex.outputs[0], saShader.inputs[0])
			tree.links.new(tex.outputs[1], saShader.inputs[1])
			uvNode = nodes.new("ShaderNodeGroup")
			uvNode.node_tree = tilingGroup
			uvSrc = nodes.new("ShaderNodeUVMap")
			uvSrc.location = (-900, 0)
			tree.links.new(uvSrc.outputs[0], uvNode.inputs[0])
			tree.links.new(uvNode.outputs[0], tex.inputs[0])
			uvNode.location = (-700, 0)

			# Setup imported data that's not driver managed.
			saShader.inputs[2].default_value[0] = mProps.b_Diffuse[0]
			saShader.inputs[2].default_value[1] = mProps.b_Diffuse[1]
			saShader.inputs[2].default_value[2] = mProps.b_Diffuse[2]
			saShader.inputs[2].default_value[3] = mProps.b_Diffuse[3]
			saShader.inputs[6].default_value[0] = mProps.b_Specular[0]
			saShader.inputs[6].default_value[1] = mProps.b_Specular[1]
			saShader.inputs[6].default_value[2] = mProps.b_Specular[2]
			saShader.inputs[6].default_value[3] = mProps.b_Specular[3]
			saShader.inputs[8].default_value = mProps.b_Exponent
			saShader.inputs[10].default_value[0] = mProps.b_Ambient[0]
			saShader.inputs[10].default_value[1] = mProps.b_Ambient[1]
			saShader.inputs[10].default_value[2] = mProps.b_Ambient[2]
			saShader.inputs[10].default_value[3] = mProps.b_Ambient[3]
			saShader.inputs[13].default_value = mProps.b_flatShading
			if mProps.b_useTexture:
				try:
					img = context.scene.saSettings.textureList[mProps.b_TextureID]
				except IndexError:
					img = None

				if img is not None:
					tex.image = img.image
					tex.interpolation = 'Closest' if mProps.b_texFilter == 'POINT' else 'Smart'

			# Driver Management
			# SAShader Lighting/Alpha Drivers
			UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[3].default_value', 'b_useAlpha')
			UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[5].default_value', 'b_ignoreLighting')
			UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[9].default_value', 'b_ignoreSpecular')
			UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[12].default_value', 'b_ignoreAmbient')
			#UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[13].default_value', 'b_flatShading')
			UpdateMaterials.addDriver(m, 'nodes["Group"].inputs[14].default_value', 'b_useTexture')

			# SAShader UV Drivers
			UpdateMaterials.addDriver(m, 'nodes["Group.001"].inputs[1].default_value', 'b_mirrorU')
			UpdateMaterials.addDriver(m, 'nodes["Group.001"].inputs[2].default_value', 'b_mirrorV')
			UpdateMaterials.addDriver(m, 'nodes["Group.001"].inputs[3].default_value', 'b_clampV')
			UpdateMaterials.addDriver(m, 'nodes["Group.001"].inputs[4].default_value', 'b_clampU')
			UpdateMaterials.addDriver(m, 'nodes["Group.001"].inputs[5].default_value', 'b_useEnv')

			# SA Shader Material Drivers
			# Diffuse Alpha (Texture Alpha) Driver
			dr = m.node_tree.driver_add('nodes["Group"].inputs[4].default_value')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'MATERIAL'
			var.targets[0].id = m
			var.targets[0].data_path = 'node_tree.nodes["Group"].inputs[2].default_value[3]'
			# Specular Alpha Driver
			dr = m.node_tree.driver_add('nodes["Group"].inputs[7].default_value')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'MATERIAL'
			var.targets[0].id = m
			var.targets[0].data_path = 'node_tree.nodes["Group"].inputs[6].default_value[3]'
			# Ambient Alpha Driver
			dr = m.node_tree.driver_add('nodes["Group"].inputs[11].default_value')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'MATERIAL'
			var.targets[0].id = m
			var.targets[0].data_path = 'node_tree.nodes["Group"].inputs[10].default_value[3]'
			# Material Settings
			dr = m.driver_add('use_backface_culling')
			dr.driver.type = 'SCRIPTED'
			dr.driver.expression = 'var'
			var = dr.driver.variables.new()
			var.type = 'SINGLE_PROP'
			var.name = 'var'
			var.targets[0].id_type = 'MATERIAL'
			var.targets[0].id = m
			var.targets[0].data_path = 'saSettings.b_doubleSided'

			# General Material Proper Management
			if mProps.b_useAlpha:
				m.blend_method = context.scene.saSettings.viewportAlphaType
				m.alpha_threshold = context.scene.saSettings.viewportAlphaCutoff
			else:
				m.blend_method = 'OPAQUE'
			#m.shadow_method = 'NONE'
			m.preview_render_type = 'FLAT'

		# setting the color management
		context.scene.display_settings.display_device = 'sRGB'
		context.scene.view_settings.view_transform = 'Standard'
		context.scene.view_settings.look = 'None'
		context.scene.view_settings.exposure = 0
		context.scene.view_settings.gamma = 1
		context.scene.sequencer_colorspace_settings.name = 'sRGB'
		context.scene.view_settings.use_curve_mapping = False
		return {'FINISHED'}

class MatToAssetLibrary(bpy.types.Operator):	## Creates Asset Library Material entries based on an imported Texlist.
	bl_idname = "scene.samatslib"
	bl_label="Materials to Asset Library"
	bl_description="Generates new materials from an imported texlist and automatically marks them for the Asset Library."

	def execute(self, context):
		DO = common.get_prefs().printDebug
		texList = context.scene.saSettings.textureList
		arr_tls = []
		genmats = []

		# no apparent method for retrieving the index of a bpy_collection, so we use an array
		for t in texList:
			arr_tls.append(t.name)

		for tex in texList:
			idx = 0
			texname = tex.name
			
			if tex.image is not None:
				matname = texname
			else:
				matname = "material_" + str(arr_tls.index(texname))

			if matname not in bpy.data.materials:
				if DO: 
					print("Material Name Not Found, Creating new material.")
				mat = bpy.data.materials.new(name=matname)
			else:
				if DO:
					print("Material Name Found, Updating exisitng material.")
				mat = bpy.data.materials[matname]

			matProps : SAMaterialSettings = mat.saSettings

			# set bpy.data.materials specifics here
			mat.preview_render_type = 'FLAT'	## sets preview image to flat preview, better for viewing textures

			# set saMaterialSettings specifics here
			matProps.b_TextureID = arr_tls.index(texname)	## updates saSettings Texture ID for material

			genmats.append(mat)

		
		UpdateMaterials.execute(self, context)

		for m in genmats:
			# add to asset library after updating material
			m.asset_mark()					## marks as asset for asset library
			m.asset_generate_preview()		## generates preview image in the asset library

		return {'FINISHED'}