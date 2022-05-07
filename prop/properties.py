import bpy
import os
import shutil
from bpy_extras.io_utils import ExportHelper, ImportHelper
from typing import List, Dict, Union, Tuple
from bpy.props import (
	BoolProperty,
	FloatProperty,
	FloatVectorProperty,
	IntProperty,
	EnumProperty,
	StringProperty,
	CollectionProperty
	)
from ..parse.pxml import ProjectFile

from .. import common

class SASettings(bpy.types.PropertyGroup):				## Property Groups used across the Addon.
	"""Information global to the scene"""

	author: StringProperty(
		name="Author",
		description="The creator of this file",
		default="",
		)

	description: StringProperty(
		name="Description",
		description="A Description of the file contents",
		default="",
		)

	texFileName: StringProperty(
		name="Texture Filename",
		description="The name of the texture file specified in the landtable info (lvl format)",
		default=""
		)

	landtableName: StringProperty(
		name="Name",
		description="The label for the landtable in the file. If empty, the filename will be used",
		default=""
		)

	texListPointer: StringProperty(
		name="Texture List Pointer (hex)",
		description="Used for when replacing a stage and its textures",
		default="0"
		)

	drawDistance: FloatProperty(
		name="Draw Distance",
		description="How far the camera has to be away from an object to render (only sa2lvl)",
		default=3000
		)

	sceneIsLevel: BoolProperty(
		name="Enable Level Tools",
		description="Enables the LandTable/Level Tools for the scene.",
		default=False
		)

	doubleSidedCollision: BoolProperty(
		name="Double-Sided Collision",
		description="Enables double sided collision detection. This is supposed to be used as a failsafe for people unexperienced with how normals work",
		default=False
		)

	active_texture_index: IntProperty(
		name="Active texture index",
		description="Index of active item in texture list",
		default=-1
		)

	correct_Material_Textures: BoolProperty(
		name="Update Materials",
		description="If a texture is being moved, the material's texture id's will be adjusted so that every material keeps the same texture",
		default=True
		)

	LightDir: FloatVectorProperty(
		name="Light Direction",
		description="The direction of the emulated light (seen from the y+ axis)",
		subtype='DIRECTION',
		default=(0.0,0.0,1.0),
		min = 0,
		max = 1,
		size=3
		)

	LightColor: FloatVectorProperty(
		name="Light Color",
		description="The color of the emulated light",
		default=(1.0,1.0,1.0),
		subtype='COLOR_GAMMA',
		min = 0,
		max = 1,
		size=3
		)

	LightAmbientColor: FloatVectorProperty(
		name="Light Ambient Color",
		description="The ambient color of the emulated light",
		default=(0.3,0.3,0.3),
		subtype='COLOR_GAMMA',
		min = 0,
		max = 1,
		size=3
		)

	DisplaySpecular: BoolProperty(
		name="Viewport Specular",
		description="Display specular in the blender material view",
		default=True
		)

	viewportAlphaType: EnumProperty(
		name="Viewport Alpha Type",
		description="The Eevee alpha type to display transparent materials",
		items=(('BLEND', "Blend", "The default blending"),
			   ('HASHED', "Hashed", "Hashed transparency"),
			   ('CLIP', "Clip", "Sharp edges for certain thresholds")),
		default='BLEND'
		)

	viewportAlphaCutoff: FloatProperty(
		name="Viewport blend Cutoff",
		description="Cutoff value for the eevee alpha cutoff transparency",
		min = 0,
		max = 1,
		default=0.5
		)

	#panel stuff
	expandedLTPanel: BoolProperty( name="Landtable Info", default=False )
	expandedTexturePanel: BoolProperty( name="Texture List Info", default=False )
	expandedLightingPanel: BoolProperty( name="Lighting Data", default=False )

	expandedQEPanel: BoolProperty( name="Quick Edit", default=False )

	useMatEdit: BoolProperty(
		name ="Activate Quick Material Edit",
		description="When active, the Buttons will use and apply the material properties",
		default=False
		)
	expandedMatEdit: BoolProperty(
		name ="Material Quick Edit",
		description="A menu for quickly assigning material properties to mutliple objects",
		default=False
		)

	useLandEntryEdit: BoolProperty(
		name ="Activate Quick LandEntry Edit",
		description="When active, the Buttons will use and apply the ladntable properties",
		default=False
		)
	expandedLandEntryEdit: BoolProperty(
		name ="LandEntry Quick Edit",
		description="A menu for quickly assigning LandEntry properties to mutliple objects",
		default=False)

	useMeshEdit: BoolProperty(
		name ="Activate Quick Mesh Edit",
		description="When active, the Buttons will use and apply the mesh properties",
		default=False
		)
	expandedMeshEdit: BoolProperty(
		name ="Mesh Quick Edit",
		description="A menu for quickly assigning mesh properties to mutliple objects",
		default=False)

	useObjEdit: BoolProperty(
		name = "Activate Quick Object Edit",
		description="When ctive, the buttons will use and apply the object properties.",
		default=False
		)
	expandedObjEdit: BoolProperty(
		name = "Object Quick Edit",
		description="A menu for quickly assigning object flags to multiple objects.",
		default=False)

	# Quick material edit properties
	b_apply_diffuse: BoolProperty(
		name = "Apply diffuse",
		description="Sets the diffuse of all material when pressing 'Set'",
		default=False
		)

	b_apply_specular: BoolProperty(
		name = "Apply specular",
		description="Sets the specular of all material when pressing 'Set'",
		default=False
		)

	b_apply_Ambient: BoolProperty(
		name = "Apply ambient",
		description="Sets the ambient of all material when pressing 'Set'",
		default=False
		)

	b_apply_specularity: BoolProperty(
		name = "Apply specularity",
		description="Sets the specularity of all material when pressing 'Set'",
		default=False
		)

	b_apply_texID: BoolProperty(
		name = "Apply texture ID",
		description="Sets the texture ID of all selected materials when pressing 'Set'",
		default=False
		)

	b_apply_filter: BoolProperty(
		name = "Apply filter type",
		description="Sets the filter type of all selected materials when pressing 'Set'",
		default=False
		)

	gc_apply_shadowStencil: BoolProperty(
		name = "Apply shadow stencil",
		description="Sets the shadow stencil of all selected materials when pressing 'Set'",
		default=False
		)

	gc_apply_texID: BoolProperty(
		name = "Apply Texcoord ID",
		description="Sets the Texcoord ID of all selected materials when pressing 'Set'",
		default=False
		)

	gc_apply_typ: BoolProperty(
		name = "Apply Type",
		description="Sets the generation Type of all selected materials when pressing 'Set'",
		default=False
		)

	gc_apply_mtx: BoolProperty(
		name = "Apply Matrix",
		description="Sets the Matrix of all selected materials when pressing 'Set'",
		default=False
		)

	gc_apply_src: BoolProperty(
		name = "Apply Source",
		description="Sets the generation Source of all selected materials when pressing 'Set'",
		default=False
		)

	# quick object edit properties
	obj_apply_userFlags: BoolProperty(
		name = "Apply Custom Flags",
		description="Sets the userflags of all selected objects when pressing 'Set'",
		default=False
		)

	obj_apply_blockbit: BoolProperty(
		name = "Apply Blockbit",
		description="Sets the Blockbit of all selected objects when pressing 'Set'",
		default=False
		)

	me_apply_ExportType: BoolProperty(
		name = "Apply Export Type",
		description="Sets the export type of all selected objects when pressing 'Set'",
		default=False
		)

	me_apply_addVO: BoolProperty(
		name = "Apply Vertex Offset",
		description="Sets the additional vertex offset of all selected objects when pressing 'Set'",
		default=False
		)

class SAEditPanelSettings(bpy.types.PropertyGroup):		## Property Group for managing expanded Material Properties menus.
	"""Menu settings for the material edit menus determining which menu should be visible"""

	expandedBMipMap: BoolProperty( name="Mipmap Distance Multiplicator", default=False )
	expandedBTexFilter: BoolProperty( name="Texture Filtering", default=False )
	expandedBUV: BoolProperty( name = "UV Properties", default=False )
	expandedBGeneral: BoolProperty( name = "General Properties", default=False )

	expandedGC: BoolProperty( name="SA2B specific", default=False )
	expandedGCTexGen: BoolProperty( name = "Generate texture coords", default=False )

	expandedSA1obj: BoolProperty( name ="SA1 Landtable Flags", default=False)
	expandedSA2obj: BoolProperty( name ="SA2 Landtable Flags", default=False)

	expandedObjFlags: BoolProperty( name ="Object Flags", default=False)

class SALandEntrySettings(bpy.types.PropertyGroup):		## Property Group for managing Land Entry surface flags.
	"""hosts all properties to edit the surface flags of a COL"""

	isSA1: BoolProperty(
		name="SA1 LandEntry Object",
		description="Enables SA1 LandEntry Flags.",
		default=False
		)

	isSA2: BoolProperty(
		name="SA2 LandEntry Object",
		description="Enables SA2 LandEntry Flags.",
		default=False
		)
	
	blockbit: StringProperty(
		name="Blockbit (hex)",
		description="BitFlags for LandEntry Objects",
		default="0"
		)

	userFlags: StringProperty(
		name="User flags",
		description="User determined flags (for experiments, otherwise usage is unadvised)",
		default="0"
		)

	solid: BoolProperty(
		name="Solid",
		description="Sets if the object has collision.",
		default=True
		)

	isVisible: BoolProperty(
		name="Visible",
		description="Sets visbility of the object.",
		default=False
		)

	# sa1 only
	sa1_water: BoolProperty(
		name="Water",
		description="Water collision with transparency sorting.",
		default=False
		)
		
	sa1_noFriction: BoolProperty(
		name="No Friction",
		description="Disable friction on object.",
		default=False
		)

	sa1_noAcceleration: BoolProperty(
		name="No Acceleration",
		description="Object will reset character acceleration on contact.",
		default=False
		)
		
	sa1_lowAcceleration: BoolProperty(
		name="Low Acceleration",
		description="Lower Acceleration for character.",
		default=False
		)
		
	sa1_useSkyDrawDistance: BoolProperty(
		name="Use Sky Draw Distance",
		description="Forces the object to use the Sky Draw Distance.",
		default=False
		)

	sa1_increasedAcceleration: BoolProperty(
		name="Increased acceleration",
		description="Increases acceleration of the character on interaction.",
		default=False
		)

	sa1_cannotLand: BoolProperty(
		name="Cannot Land",
		description="Disables the ability to stand on the object.",
		default=False
		)

	sa1_diggable: BoolProperty(
		name="Diggable",
		description="Allows Knuckles to dig on the object.",
		default=False
		)
		
	sa1_waterfall: BoolProperty(
		name="Waterfall",
		description="N/A",
		default=False
		)

	sa1_unclimbable: BoolProperty(
		name="Unclimbable",
		description="Disables Knuckles ability to climb on the object.",
		default=False
		)
		
	sa1_chaos0Land: BoolProperty(
		name="Chaos 0 Deload",
		description="Used to load/deload geometry based on if Chaos 0 is on a flagpole in his boss fight.",
		default=False
		)
	
	sa1_stairs: BoolProperty(
		name="Stairs",
		description="Treats a slope as a flat surface to walk up or down on.",
		default=False
		)
		
	sa1_hurt: BoolProperty(
		name="Hurt",
		description="Damages the player on contact.",
		default=False
		)
		
	sa1_lowDepth: BoolProperty(
		name="Low Depth",
		description="Places the model earlier in the draw queue for transparency sorting.",
		default=False
		)

	sa1_footprints: BoolProperty(
		name="Footprints",
		description="Player will leave footprints on the object.",
		default=False
		)

	sa1_accelerate: BoolProperty(
		name="Accelerate",
		description="N/A",
		default=False
		)
		
	sa1_colWater: BoolProperty(
		name="Water Collision",
		description="Water collision without transparency sorting.",
		default=False
		)
		
	sa1_rotByGravity: BoolProperty(
		name="Rotate By Gravity",
		description="N/A",
		default=False
		)

	sa1_noZWrite: BoolProperty(
		name="No Z Writing",
		description="Disables Z Writing for rendering the mesh in-game.",
		default=False
		)
		
	sa1_drawByMesh: BoolProperty(
		name="Draw By Mesh",
		description="N/A",
		default=False
		)
		
	sa1_enableManipulation: BoolProperty(
		name="Enable Manipulation",
		description="N/A",
		default=False
		)
		
	sa1_dynCollision: BoolProperty(
		name="Dynamic Collision",
		description="Sets Collision for moving objects.",
		default=False
		)

	sa1_useRotation: BoolProperty(
		name="Use Rotation",
		description="N/A",
		default=False
		)
		
	# sa2 only
	sa2_water: BoolProperty(
		name="Water",
		description="Water collision.",
		default=False
		)
		
	sa2_diggable: BoolProperty(
		name="Diggable",
		description="Allows Treasure Hunting characters to dig on the object.",
		default=False
		)
		
	sa2_unclimbable: BoolProperty(
		name="Unclimbable",
		description="Determines if Treasure Hunting characters can climb on the object.",
		default=False
		)
		
	sa2_stairs: BoolProperty(
		name="Stairs",
		description="Treats a slope as a flat surface to walk up or down on.",
		default=False
		)
		
	sa2_hurt: BoolProperty(
		name="Hurt",
		description="Damages the player on contact.",
		default=False
		)
		
	sa2_footprints: BoolProperty(
		name="Footprints",
		description="Player will leave footprints on the object.",
		default=False
		)

	sa2_cannotLand: BoolProperty(
		name="Cannot Land",
		description="Disables the ability to stand on the object.",
		default=False
		)
		
	sa2_water2: BoolProperty(
		name="Water 2",
		description="The same as water, but different!",
		default=False
		)

	sa2_noShadows: BoolProperty(
		name="No Shadows",
		description="Shadows will not render on the object.",
		default=False
		)

	sa2_noFog: BoolProperty(
		name="No Fog",
		description="Disables Fog on the object.",
		default=False
		)

	sa2_unknown24: BoolProperty(
		name="Unknown 24",
		description="N/A",
		default=False
		)

	sa2_unknown29: BoolProperty(
		name="Unknown 29",
		description="N/A",
		default=False
		)

	sa2_unknown30: BoolProperty(
		name="Unknown 30",
		description="N/A",
		default=False
		)

	@classmethod
	def defaultDict(cls) -> dict:
		d = dict()
		d["solid"]						= False
		d["isVisible"]					= False
		
		d["sa1_water"]					= False
		d["sa1_noFriction"]				= False
		d["sa1_noAcceleration"]			= False
		d["sa1_lowAcceleration"]		= False
		d["sa1_useSkyDrawDistance"]		= False
		d["sa1_increasedAcceleration"]	= False
		d["sa1_cannotLand"]				= False
		d["sa1_diggable"]				= False
		d["sa1_waterfall"]				= False
		d["sa1_unclimbable"]			= False
		d["sa1_chaos0Land"]				= False
		d["sa1_stairs"]					= False
		d["sa1_hurt"]					= False
		d["sa1_lowDepth"]				= False
		d["sa1_footprints"]				= False
		d["sa1_accelerate"]				= False
		d["sa1_colWater"]				= False
		d["sa1_rotByGravity"]			= False
		d["sa1_noZWrite"]				= False
		d["sa1_drawByMesh"]				= False
		d["sa1_enableManipulation"]		= False
		d["sa1_dynCollision"]			= False
		d["sa1_useRotation"]			= False

		d["sa2_water"]					= False
		d["sa2_diggable"]				= False
		d["sa2_unclimbable"]			= False
		d["sa2_stairs"]					= False
		d["sa2_hurt"]					= False
		d["sa2_footprints"]				= False
		d["sa2_cannotLand"]				= False
		d["sa2_water2"]					= False
		d["sa2_noShadows"]				= False
		d["sa2_noFog"]					= False
		d["sa2_unknown24"]				= False
		d["sa2_unknown29"]				= False
		d["sa2_unknown30"]				= False

		d["userFlags"]					= common.hex4(0)
		return d

	def toDictionary(self) -> dict:
		d = dict()
		d["solid"]						= self.solid
		d["isVisible"]					= self.isVisible
		
		d["sa1_water"]					= self.sa1_water
		d["sa1_noFriction"]				= self.sa1_noFriction
		d["sa1_noAcceleration"]			= self.sa1_noAcceleration
		d["sa1_lowAcceleration"]		= self.sa1_lowAcceleration
		d["sa1_useSkyDrawDistance"]		= self.sa1_useSkyDrawDistance
		d["sa1_increasedAcceleration"]	= self.sa1_increasedAcceleration
		d["sa1_cannotLand"]				= self.sa1_cannotLand
		d["sa1_diggable"]				= self.sa1_diggable
		d["sa1_waterfall"]				= self.sa1_waterfall
		d["sa1_unclimbable"]			= self.sa1_unclimbable
		d["sa1_chaos0Land"]				= self.sa1_chaos0Land
		d["sa1_stairs"]					= self.sa1_stairs
		d["sa1_hurt"]					= self.sa1_hurt
		d["sa1_lowDepth"]				= self.sa1_lowDepth
		d["sa1_footprints"]				= self.sa1_footprints
		d["sa1_accelerate"]				= self.sa1_accelerate
		d["sa1_colWater"]				= self.sa1_colWater
		d["sa1_rotByGravity"]			= self.sa1_rotByGravity
		d["sa1_noZWrite"]				= self.sa1_noZWrite
		d["sa1_drawByMesh"]				= self.sa1_drawByMesh
		d["sa1_enableManipulation"]		= self.sa1_enableManipulation
		d["sa1_dynCollision"]			= self.sa1_dynCollision
		d["sa1_useRotation"]			= self.sa1_useRotation

		d["sa2_water"]					= self.sa2_water
		d["sa2_diggable"]				= self.sa2_diggable
		d["sa2_unclimbable"]			= self.sa2_unclimbable
		d["sa2_stairs"]					= self.sa2_stairs
		d["sa2_hurt"]					= self.sa2_hurt
		d["sa2_footprints"]				= self.sa2_footprints
		d["sa2_cannotLand"]				= self.sa2_cannotLand
		d["sa2_water2"]					= self.sa2_water2
		d["sa2_noShadows"]				= self.sa2_noShadows
		d["sa2_noFog"]					= self.sa2_noFog
		d["sa2_unknown24"]				= self.sa2_unknown24
		d["sa2_unknown29"]				= self.sa2_unknown29
		d["sa2_unknown30"]				= self.sa2_unknown30

		d["userFlags"]					= self.userFlags
		d["blockbit"]					= self.blockbit

		return d

	def fromDictionary(self, d: dict):
		self.solid						= d["solid"]
		self.isVisible					= d["isVisible"]
		
		self.sa1_water					= d["sa1_water"]
		self.sa1_noFriction				= d["sa1_noFriction"] 
		self.sa1_noAcceleration			= d["sa1_noAcceleration"] 
		self.sa1_lowAcceleration		= d["sa1_lowAcceleration"] 
		self.sa1_useSkyDrawDistance		= d["sa1_useSkyDrawDistance"] 
		self.sa1_increasedAcceleration	= d["sa1_increasedAcceleration"] 
		self.sa1_cannotLand				= d["sa1_cannotLand"] 
		self.sa1_diggable				= d["sa1_diggable"] 
		self.sa1_waterfall				= d["sa1_waterfall"] 
		self.sa1_unclimbable			= d["sa1_unclimbable"] 
		self.sa1_chaos0Land				= d["sa1_chaos0Land"] 
		self.sa1_stairs					= d["sa1_stairs"] 
		self.sa1_hurt					= d["sa1_hurt"] 
		self.sa1_lowDepth				= d["sa1_lowDepth"] 
		self.sa1_footprints				= d["sa1_footprints"] 
		self.sa1_accelerate				= d["sa1_accelerate"] 
		self.sa1_colWater				= d["sa1_colWater"] 
		self.sa1_rotByGravity			= d["sa1_rotByGravity"] 
		self.sa1_noZWrite				= d["sa1_noZWrite"] 
		self.sa1_drawByMesh				= d["sa1_drawByMesh"] 
		self.sa1_enableManipulation		= d["sa1_enableManipulation"] 
		self.sa1_dynCollision			= d["sa1_dynCollision"] 
		self.sa1_useRotation			= d["sa1_useRotation"] 

		self.sa2_water					= d["sa2_water"] 
		self.sa2_diggable				= d["sa2_diggable"] 
		self.sa2_unclimbable			= d["sa2_unclimbable"] 
		self.sa2_stairs					= d["sa2_stairs"] 
		self.sa2_hurt					= d["sa2_hurt"] 
		self.sa2_footprints				= d["sa2_footprints"] 
		self.sa2_cannotLand				= d["sa2_cannotLand"] 
		self.sa2_water2					= d["sa2_water2"] 
		self.sa2_noShadows				= d["sa2_noShadows"] 
		self.sa2_noFog					= d["sa2_noFog"] 
		self.sa2_unknown24				= d["sa2_unknown24"] 
		self.sa2_unknown29				= d["sa2_unknown29"] 
		self.sa2_unknown30				= d["sa2_unknown30"] 

		self.userFlags					= d["userFlags"] 
		self.blockbit					= d["blockbit"]

class SAMaterialSettings(bpy.types.PropertyGroup):		## Property Group for managing Material Properties.
	"""Hosts all of the material data necessary for exporting"""
	# sa1 properties

	b_Diffuse: FloatVectorProperty(
		name = "Diffuse Color",
		description="Color of the material",
		subtype='COLOR_GAMMA',
		size=4,
		min=0.0, max=1.0,
		default=(1.0, 1.0, 1.0, 1.0),
		)

	b_Specular: FloatVectorProperty(
		name = "Specular Color",
		description="Color of the Specular",
		subtype='COLOR_GAMMA',
		size=4,
		min=0.0, max=1.0,
		default=(1.0, 1.0, 1.0, 1.0),
		)

	b_Ambient : FloatVectorProperty(
		name = "Ambient Color",
		description="Ambient Color (SA2 only)",
		subtype='COLOR_GAMMA',
		size=4,
		min=0.0, max=1.0,
		default=(1.0, 1.0, 1.0, 1.0),
		)

	b_Exponent: FloatProperty(
		name = "Specularity",
		description= "Specular Precision on the material",
		default=1.0,
		min = 0, max = 1
		)

	b_TextureID: IntProperty(
		name = "Texture ID",
		description= "ID of the texture in the PVM/GVM to use",
		default=0,
		min = 0
		)

	# flags:
	# mipmap distance multiplier
	b_d_025: BoolProperty(
		name="+ 0.25",
		description="adds 0.25 to the mipmap distance multiplier",
		default=False
		)

	b_d_050: BoolProperty(
		name="+ 0.5",
		description="adds 0.5 to the mipmap distance multiplier",
		default=False
		)

	b_d_100: BoolProperty(
		name="+ 1",
		description="adds 1 to the mipmap distance multiplier",
		default=False
		)

	b_d_200: BoolProperty(
		name="+ 2",
		description="adds 2 to the mipmap distance multiplier",
		default=False
		)

	# texture filtering

	b_use_Anisotropy: BoolProperty(
		name="Anisotropy",
		description="Enable Anisotropy for the texture of the material",
		default=True
		)

	b_texFilter: EnumProperty(
		name="Filter Type",
		description="The texture filter",
		items=( ('POINT', 'Point', "no filtering"),
				('BILINEAR', 'Bilinear', "Bilinear Filtering"),
				('TRILINEAR', 'Trilinear', "Trilinear Filtering"),
				('BLEND', 'Blend', "Bi- and Trilinear Filtering blended together")
			),
		default='BILINEAR'
		)

	# uv properties

	b_clampV: BoolProperty(
		name="Clamp V",
		description="The V channel of the mesh UVs always stays between 0 and 1",
		default=False
		)

	b_clampU: BoolProperty(
		name="Clamp U",
		description="The U channel of the mesh UVs always stays between 0 and 1",
		default=False
		)

	b_mirrorV: BoolProperty(
		name="Mirror V",
		description="The V channel of the mesh UVs mirrors every time it reaches a multiple of 1",
		default=False
		)

	b_mirrorU: BoolProperty(
		name="Mirror U",
		description="The V channel of the mesh UVs mirrors every time it reaches a multiple of 1",
		default=False
		)

	# general material properties
	b_ignoreSpecular: BoolProperty(
		name="Ignore Specular",
		description="Removes the specularity from the material",
		default=False
		)

	b_useAlpha: BoolProperty(
		name="Use Alpha",
		description="Utilizes the alpha channel of the color and texture to render transparency",
		default=False
		)

	b_srcAlpha: EnumProperty(
		name = "Source Alpha",
		description="Destination Alpha",
		items=( ('ZERO', 'Zero', ""),
				('ONE', 'One', ""),
				('OTHER', 'Other', ""),
				('INV_OTHER', 'Inverted other', ""),
				('SRC', 'Source', ""),
				('INV_SRC', 'Inverted source', ""),
				('DST', 'Destination', ""),
				('INV_DST', 'Inverted destination', ""),
			  ),
		default='SRC'
		)

	b_destAlpha: EnumProperty(
		name = "Destination Alpha",
		description="Destination Alpha",
		items=( ('ZERO', 'Zero', ""),
				('ONE', 'One', ""),
				('OTHER', 'Other', ""),
				('INV_OTHER', 'Inverted other', ""),
				('SRC', 'Source', ""),
				('INV_SRC', 'Inverted source', ""),
				('DST', 'Destination', ""),
				('INV_DST', 'Inverted destination', ""),
			  ),
		default='INV_SRC'
		)

	b_useTexture: BoolProperty(
		name="Use Texture",
		description="Uses the texture references in the properties",
		default=True
		)

	b_useEnv: BoolProperty(
		name="Environment mapping",
		description="Uses normal mapping instead of the uv coordinates, to make the texture face the camera (equivalent to matcaps)",
		default=False
		)

	b_doubleSided: BoolProperty(
		name="Disable Backface culling",
		description="Renders both sides of the mesh",
		default=True
		)

	b_flatShading: BoolProperty(
		name="Flat Shading",
		description="Render without shading",
		default=False
		)

	b_ignoreLighting: BoolProperty(
		name="Ignore Lighting",
		description="Ignores lighting as a whole when rendering",
		default=False
		)

	b_ignoreAmbient: BoolProperty(
		name="Ignore Ambient",
		description="Ignores ambient as a whole when rendering (SA2 Only)",
		default=False
		)

	b_unknown: BoolProperty(
		name="unknown",
		description="to be figured out",
		default = False
		)

	# GC features (parameters)

	gc_shadowStencil: IntProperty(
		name="Shadow Stencil",
		description="shadow stencil",
		min=0, max=0xF,
		default=1
		)

	# texcoord gen

	gc_texMatrixID: EnumProperty(
		name = "Matrix ID",
		description="If gentype is matrix, then this property defines which user defined matrix to use",
		items=( ('MATRIX0', 'Matrix 0', ""),
				('MATRIX1', 'Matrix 1', ""),
				('MATRIX2', 'Matrix 2', ""),
				('MATRIX3', 'Matrix 3', ""),
				('MATRIX4', 'Matrix 4', ""),
				('MATRIX5', 'Matrix 5', ""),
				('MATRIX6', 'Matrix 6', ""),
				('MATRIX7', 'Matrix 7', ""),
				('MATRIX8', 'Matrix 8', ""),
				('MATRIX9', 'Matrix 9', ""),
				('IDENTITY', 'Identity', "")
			),
		default='IDENTITY'
		)

	gc_texGenSourceMtx: EnumProperty(
		name = "Generation Source - Matrix",
		description="Which data of the mesh to use when generating the uv coords (Matrix)",
		items=( ('POSITION', 'Position', ""),
				('NORMAL', 'Normal', ""),
				('BINORMAL', 'Binormal', ""),
				('TANGENT', 'Tangent', ""),
				('TEX0', 'Tex0', ""),
				('TEX1', 'Tex1', ""),
				('TEX2', 'Tex2', ""),
				('TEX3', 'Tex3', ""),
				('TEX4', 'Tex4', ""),
				('TEX5', 'Tex5', ""),
				('TEX6', 'Tex6', ""),
				('TEX7', 'Tex7', ""),
			),
		default='TEX0'
		)

	gc_texGenSourceBmp: EnumProperty(
		name = "Generation Source - Bump",
		description="Which uv map of the mesh to use when generating the uv coords (Bump)",
		items=( ('TEXCOORD0', 'TexCoord0', ""),
				('TEXCOORD1', 'TexCoord1', ""),
				('TEXCOORD2', 'TexCoord2', ""),
				('TEXCOORD3', 'TexCoord3', ""),
				('TEXCOORD4', 'TexCoord4', ""),
				('TEXCOORD5', 'TexCoord5', ""),
				('TEXCOORD6', 'TexCoord6', ""),
			),
		default='TEXCOORD0'
		)

	gc_texGenSourceSRTG: EnumProperty(
		name = "Generation Source - SRTG",
		description="Which color slot of the mesh to use when generating the uv coords (SRTG)",
		items=( ('COLOR0', 'Color0', ""),
				('COLOR1', 'Color1', ""),
			),
		default='COLOR0'
		)

	gc_texGenType: EnumProperty(
		name = "Generation Type",
		description="Which function to use when generating the coords",
		items=( ('MTX3X4', 'Matrix 3x4', ""),
				('MTX2X4', 'Matrix 2x4', ""),
				('BUMP0', 'Bump 0', ""),
				('BUMP1', 'Bump 1', ""),
				('BUMP2', 'Bump 2', ""),
				('BUMP3', 'Bump 3', ""),
				('BUMP4', 'Bump 4', ""),
				('BUMP5', 'Bump 5', ""),
				('BUMP6', 'Bump 6', ""),
				('BUMP7', 'Bump 7', ""),
				('SRTG', 'SRTG', ""),
			),
		default='MTX2X4'
		)

	gc_texCoordID: EnumProperty(
		name = "Texcoord ID (output slot)",
		description="Determines in which slot the generated coordinates should be saved, so that they can be used",
		items = ( ('TEXCOORD0', 'TexCoord0', ""),
				  ('TEXCOORD1', 'TexCoord1', ""),
				  ('TEXCOORD2', 'TexCoord2', ""),
				  ('TEXCOORD3', 'TexCoord3', ""),
				  ('TEXCOORD4', 'TexCoord4', ""),
				  ('TEXCOORD5', 'TexCoord5', ""),
				  ('TEXCOORD6', 'TexCoord6', ""),
				  ('TEXCOORD7', 'TexCoord7', ""),
				  ('TEXCOORDMAX', 'TexCoordMax', ""),
				  ('TEXCOORDNULL', 'TexCoordNull', ""),
			),
		default='TEXCOORD0'
		)

	def toDictionary(self) -> dict:
		d = dict()
		d["b_Diffuse"] = self.b_Diffuse
		d["b_Specular"] = self.b_Specular
		d["b_Ambient"] = self.b_Ambient
		d["b_Exponent"] = self.b_Exponent
		d["b_TextureID"] = self.b_TextureID
		d["b_d_025"] = self.b_d_025
		d["b_d_050"] = self.b_d_050
		d["b_d_100"] = self.b_d_100
		d["b_d_200"] = self.b_d_200
		d["b_use_Anisotropy"] = self.b_use_Anisotropy
		d["b_texFilter"] = self.b_texFilter
		d["b_clampV"] = self.b_clampV
		d["b_clampU"] = self.b_clampU
		d["b_mirrorV"] = self.b_mirrorV
		d["b_mirrorU"] = self.b_mirrorU
		d["b_ignoreSpecular"] = self.b_ignoreSpecular
		d["b_useAlpha"] = self.b_useAlpha
		d["b_srcAlpha"] = self.b_srcAlpha
		d["b_destAlpha"] = self.b_destAlpha
		d["b_useTexture"] = self.b_useTexture
		d["b_useEnv"] = self.b_useEnv
		d["b_doubleSided"] = self.b_doubleSided
		d["b_flatShading"] = self.b_flatShading
		d["b_ignoreLighting"] = self.b_ignoreLighting
		d["b_ignoreAmbient"] = self.b_ignoreAmbient
		d["b_unknown"] = self.b_unknown
		d["gc_shadowStencil"] = self.gc_shadowStencil
		d["gc_texMatrixID"] = self.gc_texMatrixID
		d["gc_texGenSourceMtx"] = self.gc_texGenSourceMtx
		d["gc_texGenSourceBmp"] = self.gc_texGenSourceBmp
		d["gc_texGenSourceSRTG"] = self.gc_texGenSourceSRTG
		d["gc_texGenType"] = self.gc_texGenType
		d["gc_texCoordID"] = self.gc_texCoordID
		return d

	def readMatDict(self, d):
		self.b_Diffuse = d["b_Diffuse"]
		self.b_Specular = d["b_Specular"]
		self.b_Ambient = d["b_Ambient"]
		self.b_Exponent = d["b_Exponent"]
		self.b_TextureID = d["b_TextureID"]
		self.b_d_025 = d["b_d_025"]
		self.b_d_050 = d["b_d_050"]
		self.b_d_100 = d["b_d_100"]
		self.b_d_200 = d["b_d_200"]
		self.b_use_Anisotropy = d["b_use_Anisotropy"]
		self.b_texFilter = d["b_texFilter"]
		self.b_clampV = d["b_clampV"]
		self.b_clampU = d["b_clampU"]
		self.b_mirrorV = d["b_mirrorV"]
		self.b_mirrorU = d["b_mirrorU"]
		self.b_ignoreSpecular = d["b_ignoreSpecular"]
		self.b_useAlpha = d["b_useAlpha"]
		self.b_srcAlpha = d["b_srcAlpha"]
		self.b_destAlpha = d["b_destAlpha"]
		self.b_useTexture = d["b_useTexture"]
		self.b_useEnv = d["b_useEnv"]
		self.b_doubleSided = d["b_doubleSided"]
		self.b_flatShading = d["b_flatShading"]
		self.b_ignoreLighting = d["b_ignoreLighting"]
		self.b_ignoreAmbient = d["b_ignoreAmbient"]
		self.b_unknown = d["b_unknown"]
		self.gc_shadowStencil = d["gc_shadowStencil"]
		self.gc_texMatrixID = d["gc_texMatrixID"]
		self.gc_texGenSourceMtx = d["gc_texGenSourceMtx"]
		self.gc_texGenSourceBmp = d["gc_texGenSourceBmp"]
		self.gc_texGenSourceSRTG = d["gc_texGenSourceSRTG"]
		self.gc_texGenType = d["gc_texGenType"]
		self.gc_texCoordID = d["gc_texCoordID"]

	@classmethod
	def getDefaultMatDict(cls) -> Dict[str, Union[str, bool, List[int]]]:
		d = dict()
		d["b_Diffuse"] = (1.0, 1.0, 1.0, 1.0)
		d["b_Specular"] = (1.0, 1.0, 1.0, 1.0)
		d["b_Ambient"] =(1.0, 1.0, 1.0, 1.0)
		d["b_Exponent"] = 1
		d["b_TextureID"] = 0
		d["b_d_025"] = False
		d["b_d_050"] = False
		d["b_d_100"] = False
		d["b_d_200"] = False
		d["b_use_Anisotropy"] = False
		d["b_texFilter"] = 'BILINEAR'
		d["b_clampV"] = False
		d["b_clampU"] = False
		d["b_mirrorV"] = False
		d["b_mirrorU"] = False
		d["b_ignoreSpecular"] = False
		d["b_useAlpha"] = False
		d["b_srcAlpha"] = 'SRC'
		d["b_destAlpha"] = 'INV_SRC'
		d["b_useTexture"] = True
		d["b_useEnv"] = False
		d["b_doubleSided"] = True
		d["b_flatShading"] = False
		d["b_ignoreLighting"] = False
		d["b_ignoreAmbient"] = False
		d["b_unknown"] = False
		d["gc_shadowStencil"] = 1
		d["gc_texMatrixID"] = 'IDENTITY'
		d["gc_texGenSourceMtx"] = 'TEX0'
		d["gc_texGenSourceBmp"] = 'TEXCOORD0'
		d["gc_texGenSourceSRTG"] = 'COLOR0'
		d["gc_texGenType"] = 'MTX2X4'
		d["gc_texCoordID"] = 'TEXCOORD0'
		return d

class SAMeshSettings(bpy.types.PropertyGroup):			## Property Group for managing Mesh Properties.
	'''Settings used by the exporters for specific meshes'''

	sa2ExportType: EnumProperty(
		name = "SA2 Export Type",
		description = "Determines which vertex data should be written for sa2",
		items = ( ('VC', "Colors", "Only vertex colors are gonna be written"),
				  ('NRM', "Normals", "Only normals are gonna be written"),
				),
		default = 'NRM'
		)

	sa2IndexOffset: IntProperty(
		name = "(SA2) Additional Vertex Offset",
		description = "Additional vertex offset for specific model mods",
		min=0, max = 32767,
		default = 0
	)

class SAObjectSettings(bpy.types.PropertyGroup):
	"""NJS_OBJECT Flag Settings"""

	ignorePosition: BoolProperty(
		name="Ignore Position",
		description="Ignores object position.",
		default=False
		)

	ignoreRotation: BoolProperty(
		name="Ignore Rotation",
		description="Ignores object rotation.",
		default=False
		)

	ignoreScale: BoolProperty(
		name="Ignore Scale",
		description="Ignores object scale.",
		default=False
		)

	rotateZYX: BoolProperty(
		name="Rotate ZYX",
		description="Sets rotation mode to ZYX order.",
		default=False
		)

	skipDraw: BoolProperty(
		name="Skip Draw",
		description="Skips drawing the model.",
		default=False
		)

	skipChildren: BoolProperty(
		name="Skip Children",
		description="Skips any child nodes of the current node.",
		default=False
		)

	flagAnimate: BoolProperty(
		name="Not Animated",
		description="Sets if the node is counted in the hierarchy for animations.",
		default=False
		)

	flagMorph: BoolProperty(
		name="No Morph",
		description="Sets if the node can have morph effect applied.",
		default=False
		)

	@classmethod
	def defaultDict(cls) -> dict:
		d = dict()

		d["ignorePosition"] = False
		d["ignoreRotation"] = False
		d["ignoreScale"] 	= False
		d["rotateZYX"] 		= False
		d["skipDraw"] 		= False
		d["skipChildren"] 	= False
		d["flagAnimate"] 	= False
		d["flagMorph"] 		= False

		return d

	def toDictionary(self) -> dict:
		d = dict()

		d["ignorePosition"] = self.ignorePosition
		d["ignoreRotation"] = self.ignoreRotation
		d["ignoreScale"] 	= self.ignoreScale
		d["rotateZYX"] 		= self.rotateZYX
		d["skipDraw"] 		= self.skipDraw
		d["skipChildren"] 	= self.skipChildren
		d["flagAnimate"] 	= self.flagAnimate
		d["flagMorph"] 		= self.flagMorph

		return d

	def fromDictionary(self, d: dict):
		self.ignorePosition = d["ignorePosition"]
		self.ignoreRotation = d["ignoreRotation"]
		self.ignoreScale 	= d["ignoreScale"]
		self.rotateZYX 		= d["rotateZYX"]
		self.skipDraw 		= d["skipDraw"]
		self.skipChildren 	= d["skipChildren"]
		self.flagAnimate 	= d["flagAnimate"]
		self.flagMorph 		= d["flagMorph"]

class SAProjectSettings(bpy.types.PropertyGroup):
	"""Stores info related to SA Project Files"""

	ProjectFilePath: StringProperty(
		name="SA Project File: ",
		default=""
	)

	ProjectFolder: StringProperty(
		name="SA Project Folder",
		default=""
	)

	ModName: StringProperty(
		name="Mod name",
		default=""
	)

	ModAuthor: StringProperty(
		name="Mod Author",
		default=""
	)

	ModDescription: StringProperty(
		name="Mod Description",
		default=""
	)

	ModVersion: StringProperty(
		name="Mod Version",
		default=""
	)

def texUpdate(self, context):							## Definitions for handling texture updates.
	settings = context.scene.saSettings

	# checking if texture object is in list
	index = -1
	tList = settings.textureList
	for i, t in enumerate(tList):
		if t == self:
			index = i
			break

	if index == -1:
		print("Texture slot not found in list")
		return

	if self.name != self.prevName:
		if self.name.isspace() or self.name == "":
			self.name = self.prevName
			return

		names = list()
		for t in tList:
			if t == self:
				continue
			names.append(t.name)

		if self.name not in names:
			self.prevName = self.name
			return

		# check if the texture has a number tag
		splits = self.name.split(".")
		isNumberTag = len(splits) > 1 and splits[-1].isdecimal()

		if isNumberTag:
			name = self.name[:len(self.name) - 1 - len(splits[-1])]
			number = int(splits[-1])
		else:
			name = self.name
			number = 0

		numbers = list()

		for t in context.scene.saSettings.textureList:
			if t == self:
				continue
			splits = t.name.split(".")
			if len(splits) > 1 and splits[-1].isdecimal():
				tname = t.name[:len(t.name) - 1 - len(splits[-1])]
				if tname == name:
					numbers.append(int(splits[-1]))
			elif t.name == name:
				numbers.append(0)


		numbers.sort(key=lambda x: x)
		found = False
		for i, n in enumerate(numbers):
			if i != n:
				found = True
				break
		if not found:
			i += 1
		self.name = name + "." + str(i).zfill(3)

	if self.globalID != self.prevGlobalID:
		ids = list()
		for t in settings.textureList:
			if t == self:
				continue
			ids.append(t.globalID)

		if self.globalID not in ids:
			self.prevGlobalID = self.globalID
			return

		ids.sort(key=lambda x: x)
		current = 0
		if self.globalID == self.prevGlobalID - 1: # if value was just reduced by one
			found = -1
			for index in ids:
				if current < index:
					current = index
					t = index - 1
					if t < self.prevGlobalID:
						found = t
					else:
						break

				current += 1

			if found == -1:
				self.globalID = self.prevGlobalID
			else:
				self.globalID = found
		elif self.globalID == self.prevGlobalID + 1: # if value was just raise by one
			found = -1
			oldIndex = ids[0]
			for index in ids:
				if current < index:
					current = index
					t = oldIndex + 1
					if t > self.prevGlobalID:
						found = t
						break
				oldIndex = index
				current += 1

			if found == -1:
				self.globalID = ids[-1] + 1
			else:
				self.globalID = found
		else:  # everything else
			closestFree = -1
			oldindex = ids[0]
			for index in ids:
				if current < index:
					current = index
					if index < self.globalID:
						t = index - 1
					else:
						t = oldindex + 1

					if abs(t - self.globalID) < abs(closestFree - self.globalID) or closestFree == -1:
						closestFree = t
					elif abs(t - self.globalID) > abs(closestFree - self.globalID):
						break
					elif self.globalID < self.prevGlobalID:
						closestFree = t
						break

				oldindex = index
				current += 1

			if closestFree == -1:
				closestFree = self.prevGlobalID

			self.globalID = closestFree

class SATexture(bpy.types.PropertyGroup):				## Property Group for storing Texture List information.

	name: StringProperty(
		name = "Slot name",
		description="The name of the slot",
		maxlen=0x20,
		default="",
		update=texUpdate
		)

	prevName: StringProperty(
		name="Previous name",
		maxlen=0x20,
		default=""
		)

	globalID: IntProperty(
		name="Global ID",
		description="The global texture id in the texture file",
		default=0,
		min = 0,
		update=texUpdate
		)

	prevGlobalID: IntProperty(
		name="Previous Global ID",
		min = 0,
		default=0,
		)
