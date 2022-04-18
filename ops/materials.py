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

def autotexUpdate(context, newValue):			## Definition for the auto-assign texture operator.
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
		#print("Process Texlist")
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
								#print("Found, " + matname)
								index = copyTex.index(matname)
								if index > -1:
									# if updated index is > -1, update SA Material Texture ID
									matProps.b_TextureID = index
									#print("Texture updated!")
									found = True
			
			# if Texture Image input cannot be found, check material name as backup.
			if found == False:
				for matslot in o.material_slots:
					if matslot.material:
						matname = matslot.material.name
						if matname in texList:
							#print("Found, " + matname)
							index = copyTex.index(matname)
							if index > -1:
								# if updated index > -1, update SA Material Texture ID
								matProps.b_TextureID = index
								#print("Texture updated!")
						else:
							print("Error! No matching texture for " + matname + "in object " + o.name)

class AutoAssignTextures(bpy.types.Operator):	## Auto-Assign texture IDs based on initial material's image name or material name.
	bl_idname = "scene.saautoassignmmd"
	bl_label = "Auto Assign Textures"
	bl_description = "Attempts to match texture or material names to an imported texlist. Only checks visible objects, may not work."

	def execute(self, context):
		autotexUpdate(context, True)
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
		return {'FINISHED'}

class UpdateMaterials(bpy.types.Operator):		## Updates all materials in the scene to use the SA Shader.
	bl_idname = "scene.saupdatemats"
	bl_label="Update Materials"
	bl_description="Sets material nodetrees and variables of all selected objects to imitate how they would look in sadx/sa2"

	@classmethod
	def addDriver(cls, inputSocket, scene, path, entry = -1):
		#curve = inputSocket.driver_add("default_value")
		#driver = curve.driver
		#driver.type = 'AVERAGE'
		#variable = driver.variables.new()
		#variable.targets[0].id_type = 'SCENE'
		#variable.targets[0].id = scene
		#variable.targets[0].data_path = "saSettings." + path + ("" if entry == -1 else "[" + str(entry) + "]")
		#curve.update()
		inputSocket.default_value = getattr(scene.saSettings, path) if entry == -1 else getattr(scene.saSettings, path)[entry]

	def execute(self, context):
		# remove old trees

		ng = bpy.data.node_groups

		n = ng.find("UV Tiling")
		if n > -1:
			ng.remove(ng[n])

		n = ng.find("SAShader")
		if n > -1:
			ng.remove(ng[n])

		n = ng.find("EnvMap")
		if n > -1:
			ng.remove(ng[n])

		# now reload them them
		directory = os.path.dirname(os.path.realpath(__file__)) + "\\..\\Shaders.blend\\NodeTree\\"
		bpy.ops.wm.append(filename="UV Tiling", directory=directory)
		bpy.ops.wm.append(filename="SAShader", directory=directory)
		bpy.ops.wm.append(filename="EnvMap", directory=directory)

		tilingGroup = ng[ng.find("UV Tiling")]
		saShaderGroup = ng[ng.find("SAShader")]
		envMapGroup = ng[ng.find("EnvMap")]

		# Drivers dont update automatically when set like this, and i cant find a way to update them through python, so we'll just set them temporarily
		nd = saShaderGroup.nodes
		lightDirNode: bpy.types.ShaderNodeCombineXYZ = nd[nd.find("LightDir")]
		lightColNode: bpy.types.ShaderNodeCombineRGB = nd[nd.find("LightCol")]
		ambientColNode: bpy.types.ShaderNodeCombineRGB = nd[nd.find("AmbientCol")]
		displSpecularNode: bpy.types.ShaderNodeValue = nd[nd.find("DisplSpecular")]

		UpdateMaterials.addDriver(lightDirNode.inputs[0], context.scene, "LightDir", 0)
		UpdateMaterials.addDriver(lightDirNode.inputs[1], context.scene, "LightDir", 1)
		UpdateMaterials.addDriver(lightDirNode.inputs[2], context.scene, "LightDir", 2)

		UpdateMaterials.addDriver(lightColNode.inputs[0], context.scene, "LightColor", 0)
		UpdateMaterials.addDriver(lightColNode.inputs[1], context.scene, "LightColor", 1)
		UpdateMaterials.addDriver(lightColNode.inputs[2], context.scene, "LightColor", 2)

		UpdateMaterials.addDriver(ambientColNode.inputs[0], context.scene, "LightAmbientColor", 0)
		UpdateMaterials.addDriver(ambientColNode.inputs[1], context.scene, "LightAmbientColor", 1)
		UpdateMaterials.addDriver(ambientColNode.inputs[2], context.scene, "LightAmbientColor", 2)

		UpdateMaterials.addDriver(displSpecularNode.outputs[0], context.scene, "DisplaySpecular")

		# The materials know whether the shader displays vertex colors based on the object color, its weird i know, but i didnt find any better way
		import math
		for o in context.scene.objects:
			if o.type == 'MESH':
				isNrm = o.data.saSettings.sa2ExportType == 'NRM'
				r = o.color[0]
				rc = bool(math.floor(r * 1000) % 2)

				if isNrm and rc:
					r = (math.floor(r * 1000) + (1 if r < 1 else (-1))) / 1000.0
				elif not isNrm and not rc:
					r = (math.floor(r * 1000) + ((-1) if r > 0 else 1)) / 1000.0
				o.color[0] = r

		# now its time to set all of the materials
		for m in bpy.data.materials:
			#creating an settings nodes
			mProps = m.saSettings
			m.use_nodes = True
			tree: bpy.types.NodeTree = m.node_tree
			nodes = tree.nodes
			nodes.clear()

			out = nodes.new("ShaderNodeOutputMaterial")
			saShader = nodes.new("ShaderNodeGroup")
			saShader.node_tree = saShaderGroup

			saShader.inputs[2].default_value = mProps.b_Diffuse
			saShader.inputs[3].default_value = mProps.b_Diffuse[3]
			saShader.inputs[4].default_value = mProps.b_ignoreLighting

			saShader.inputs[5].default_value = mProps.b_Specular
			saShader.inputs[6].default_value = mProps.b_Specular[3]
			saShader.inputs[7].default_value = mProps.b_Exponent
			saShader.inputs[8].default_value = mProps.b_ignoreSpecular

			saShader.inputs[9].default_value = mProps.b_Ambient
			saShader.inputs[10].default_value = mProps.b_Ambient[3]
			saShader.inputs[11].default_value = mProps.b_ignoreAmbient

			saShader.inputs[12].default_value = mProps.b_flatShading

			saShader.location = (-200, 0)

			tree.links.new(out.inputs[0], saShader.outputs[0])

			if mProps.b_useTexture:
				try:
					img = context.scene.saSettings.textureList[mProps.b_TextureID]
				except IndexError:
					img = None

				if img is not None:
					tex = nodes.new("ShaderNodeTexImage")
					tex.image = img.image
					tex.interpolation = 'Closest' if mProps.b_texFilter == 'POINT' else 'Smart'
					tex.location = (-500, 0)
					tree.links.new(tex.outputs[0], saShader.inputs[0])
					tree.links.new(tex.outputs[1], saShader.inputs[1])


					uvNode = nodes.new("ShaderNodeGroup")
					if mProps.b_useEnv:
						uvNode.node_tree = envMapGroup
					else:
						uvNode.node_tree = tilingGroup

						uvNode.inputs[1].default_value = mProps.b_mirrorV
						uvNode.inputs[2].default_value = mProps.b_mirrorU
						uvNode.inputs[3].default_value = mProps.b_clampV
						uvNode.inputs[4].default_value = mProps.b_clampU

						uvSrc = nodes.new("ShaderNodeUVMap")
						uvSrc.location = (-900, 0)
						tree.links.new(uvSrc.outputs[0], uvNode.inputs[0])
					tree.links.new(uvNode.outputs[0], tex.inputs[0])
					uvNode.location = (-700, 0)
				else:
					saShader.inputs[0].default_value = (1,0,1,1)

			if mProps.b_useAlpha:
				m.blend_method = context.scene.saSettings.viewportAlphaType
				m.alpha_threshold = context.scene.saSettings.viewportAlphaCutoff
			else:
				m.blend_method = 'OPAQUE'
			m.shadow_method = 'NONE'
			m.use_backface_culling = not mProps.b_doubleSided

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

	# uncomment print commands in case of debugging.
	def execute(self, context):
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
				#print("Material Name Not Found, Creating new material.")
				mat = bpy.data.materials.new(name=matname)
			else:
				#print("Material Name Found, Updating exisitng material.")
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