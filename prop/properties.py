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
from ..ops import projects
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
	
	me_apply_objflags: BoolProperty(
		name = "Apply Object Flags",
		description="Sets object flags for all selected objects when pressing 'Set'",
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

	expandedSA1obj: BoolProperty( name ="SA1 Surface Flags", default=False)
	expandedSA2obj: BoolProperty( name ="SA2 Surface Flags", default=False)

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

	# Surface Flags
	sfVisible: BoolProperty(
		name="Visible",
		description="Object will be visible in the level.",
		default=False
	)

	sfSolid: BoolProperty(
		name="Solid",
		description="Enables collision on object.",
		default=False
	)

	sfNoAccel: BoolProperty(
		name="No Acceleration",
		description="Multiplies acceleration by 0.25.",
		default=False
	)

	sfLowAccel: BoolProperty(
		name="Low Acceleration",
		description="Multiplies acceleration by 0.50.",
		default=False
	)

	sfAccel: BoolProperty(
		name="Normal Acceleration",
		description="Multiplies acceleration by 1.00.",
		default=False
	)

	sfIncAccel: BoolProperty(
		name="Increased Acceleration",
		description="Multiplies acceleration by 1.50.",
		default=False
	)

	sfUnclimbable: BoolProperty(
		name="Unclimbable",
		description="Makes surface unclimbable.",
		default=False
	)

	sfDiggable: BoolProperty(
		name="Diggable",
		description="Makes surface diggable.",
		default=False
	)

	sfNoFriction: BoolProperty(
		name="No Friction",
		description="Makes surface slippery.",
		default=False
	)

	sfStairs: BoolProperty(
		name="Stairs",
		description="Makes surfaces act like stairs.",
		default=False
	)

	sfWater: BoolProperty(
		name="Water",
		description="Sets surface to a water region.",
		default=False
	)

	sfCannotLand: BoolProperty(
		name="Cannot Land",
		description="Unable to land on surface.",
		default=False
	)

	sfHurt: BoolProperty(
		name="Hurt",
		description="Damages the player.",
		default=False
	)

	sfFootprints: BoolProperty(
		name="Footprints",
		description="Surface will display footprints if players walks on it.",
		default=False
	)

	sfGravity: BoolProperty(
		name="Modified Gravity",
		description="Changes the gravity for the player.",
		default=False
	)

	sfUseRotation: BoolProperty(
		name="Enables Rotation",
		description="Allows rotation (Used for moving objects).",
		default=False
	)

	sfDynCollision: BoolProperty(
		name="Dynamic Collision",
		description="Uses Dynamic Collision buffer (Used for objects).",
		default=False
	)

	# Start SA1 Land Flags
	sfWaterCollision: BoolProperty(
		name="Alternate Water",
		description="Different water flag for SA1.",
		default=False
	)

	sfUseSkyDrawDistance: BoolProperty(
		name="Use Sky Draw Distance",
		description="Object will use the Skybox Draw Distance rather than the Landtable's Draw Distance (SA1 Only)",
		default=False
	)

	sfNoZWrite: BoolProperty(
		name="No Z-Buffer Writing",
		description="Object doesn't write to the Z-Buffer (SA1 Only)",
		default=False
	)

	sfLowDepth: BoolProperty(
		name="Low Render Depth",
		description="Lowers render depth for object (SA1 Only).",
		default=False
	)

	sfDrawByMesh: BoolProperty(
		name="Draw By Mesh",
		description="Draws the model by each mesh for transparency sorting reasons (SA1 Only)",
		default=False
	)

	sfWaterfall: BoolProperty(
		name="Waterfall",
		description="Object will function like a waterfall (SA1 Only)",
		default=False
	)

	sfChaos0Land: BoolProperty(
		name="Chaos 0 Land Flag",
		description="Used for Chaos 0 Boss Fight. ",
		default=False
	)

	sfEnableManipulation: BoolProperty(
		name="Enable Model Modifications",
		description="Allows the model to be modified via code.",
		default=False
	)

	sfSA1U_200: BoolProperty(
		name="Unknown Flag 1",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_800: BoolProperty(
		name="Unknown Flag 2",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_8000: BoolProperty(
		name="Unknown Flag 3",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_20000: BoolProperty(
		name="Unknown Flag 4",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_80000: BoolProperty(
		name="Unknown Flag 5",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_20000000: BoolProperty(
		name="Unknown Flag 6",
		description="Unknown SA1 Flag",
		default=False
	)

	sfSA1U_40000000: BoolProperty(
		name="Unknown Flag 7",
		description="Unknown SA1 Flag",
		default=False
	)

	# Start SA2 Land Flags
	sfWater2: BoolProperty(
		name="Alternate Water",
		description="Alternative Water in SA2.",
		default=False
	)

	sfNoShadows: BoolProperty(
		name="Disable Shadows on Surface",
		description="Shadows will not render on the surface.",
		default=False
	)

	sfNoFog: BoolProperty(
		name="Disable Fog on Surface",
		description="Fog will not affect the surface.",
		default=False
	)

	sfSA2U_40: BoolProperty(
		name="Unknown Flag 1",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_200: BoolProperty(
		name="Unknown Flag 2",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_4000: BoolProperty(
		name="Unknown Flag 3",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_10000: BoolProperty(
		name="Unknown Flag 4",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_20000: BoolProperty(
		name="Unknown Flag 5",
		description="Unknown SA2 Flag",
		default=False
	)
	
	sfSA2U_40000: BoolProperty(
		name="Unknown Flag 6",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_800000: BoolProperty(
		name="Unknown Flag 7",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_1000000: BoolProperty(
		name="Unknown Flag 8",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_2000000: BoolProperty(
		name="Unknown Flag 9",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_4000000: BoolProperty(
		name="Unknown Flag 10",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_20000000: BoolProperty(
		name="Unknown Flag 11",
		description="Unknown SA2 Flag",
		default=False
	)

	sfSA2U_40000000: BoolProperty(
		name="Unknown Flag 12",
		description="Unknown SA2 Flag",
		default=False
	)

	@classmethod
	def defaultDict(cls) -> dict:
		d = dict()

		d['sfVisible']			= False
		d['sfSolid']			= False
		d['sfNoAccel']			= False
		d['sfLowAccel']			= False
		d['sfAccel']			= False
		d['sfIncAccel']			= False
		d['sfUnclimbable']		= False
		d['sfDiggable']			= False
		d['sfNoFriction']		= False
		d['sfStairs']			= False
		d['sfWater']			= False
		d['sfCannotLand']		= False
		d['sfHurt']				= False
		d['sfFootprints']		= False
		d['sfGravity']			= False
		d['sfUseRotation']		= False
		d['sfDynCollision']		= False


		# SA1
		d['sfWaterCollision']		= False
		d['sfUseSkyDrawDistance']	= False
		d['sfNoZWrite']				= False
		d['sfLowDepth']				= False
		d['sfDrawByMesh']			= False
		d['sfWaterfall']			= False
		d['sfChaos0Land']			= False
		d['sfEnableManipulation']	= False
		d['sfSA1U_200']				= False
		d['sfSA1U_800']				= False
		d['sfSA1U_8000']			= False
		d['sfSA1U_20000']			= False
		d['sfSA1U_80000']			= False
		d['sfSA1U_20000000']		= False
		d['sfSA1U_40000000']		= False


		# SA2
		d['sfWater2']			= False
		d['sfNoShadows']		= False
		d['sfNoFog']			= False
		d['sfSA2U_40']			= False
		d['sfSA2U_200']			= False
		d['sfSA2U_4000']		= False
		d['sfSA2U_10000']		= False
		d['sfSA2U_20000']		= False
		d['sfSA2U_40000']		= False
		d['sfSA2U_800000']		= False
		d['sfSA2U_1000000']		= False
		d['sfSA2U_2000000']		= False
		d['sfSA2U_4000000']		= False
		d['sfSA2U_20000000']	= False
		d['sfSA2U_40000000']	= False

		d["userFlags"]					= common.hex4(0)
		return d

	def toDictionary(self) -> dict:
		d = dict()

		d['sfVisible']			= self.sfVisible
		d['sfSolid']			= self.sfSolid
		d['sfNoAccel']			= self.sfNoAccel
		d['sfLowAccel']			= self.sfLowAccel
		d['sfAccel']			= self.sfAccel
		d['sfIncAccel']			= self.sfIncAccel
		d['sfUnclimbable']		= self.sfUnclimbable
		d['sfDiggable']			= self.sfDiggable
		d['sfNoFriction']		= self.sfNoFriction
		d['sfStairs']			= self.sfStairs
		d['sfWater']			= self.sfWater
		d['sfCannotLand']		= self.sfCannotLand
		d['sfHurt']				= self.sfHurt
		d['sfFootprints']		= self.sfFootprints
		d['sfGravity']			= self.sfGravity
		d['sfUseRotation']		= self.sfUseRotation
		d['sfDynCollision']		= self.sfDynCollision


		# SA1
		d['sfWaterCollision']		= self.sfWaterCollision
		d['sfUseSkyDrawDistance']	= self.sfUseSkyDrawDistance
		d['sfNoZWrite']				= self.sfNoZWrite
		d['sfLowDepth']				= self.sfLowDepth
		d['sfDrawByMesh']			= self.sfDrawByMesh
		d['sfWaterfall']			= self.sfWaterfall
		d['sfChaos0Land']			= self.sfChaos0Land
		d['sfEnableManipulation']	= self.sfEnableManipulation
		d['sfSA1U_200']				= self.sfSA1U_200
		d['sfSA1U_800']				= self.sfSA1U_800
		d['sfSA1U_8000']			= self.sfSA1U_8000
		d['sfSA1U_20000']			= self.sfSA1U_20000
		d['sfSA1U_80000']			= self.sfSA1U_80000
		d['sfSA1U_20000000']		= self.sfSA1U_20000000
		d['sfSA1U_40000000']		= self.sfSA1U_40000000


		# SA2
		d['sfWater2']			= self.sfWater2
		d['sfNoShadows']		= self.sfNoShadows
		d['sfNoFog']			= self.sfNoFog
		d['sfSA2U_40']			= self.sfSA2U_40
		d['sfSA2U_200']			= self.sfSA2U_200
		d['sfSA2U_4000']		= self.sfSA2U_4000
		d['sfSA2U_10000']		= self.sfSA2U_10000
		d['sfSA2U_20000']		= self.sfSA2U_20000
		d['sfSA2U_40000']		= self.sfSA2U_40000
		d['sfSA2U_800000']		= self.sfSA2U_800000
		d['sfSA2U_1000000']		= self.sfSA2U_1000000
		d['sfSA2U_2000000']		= self.sfSA2U_2000000
		d['sfSA2U_4000000']		= self.sfSA2U_4000000
		d['sfSA2U_20000000']	= self.sfSA2U_20000000
		d['sfSA2U_40000000']	= self.sfSA2U_40000000

		d["userFlags"]			= self.userFlags
		d["blockbit"]			= self.blockbit

		return d

	def fromDictionary(self, d: dict):
		self.sfVisible		= d['sfVisible']
		self.sfSolid		= d['sfSolid']
		self.sfNoAccel		= d['sfNoAccel']
		self.sfLowAccel		= d['sfLowAccel']
		self.sfAccel		= d['sfAccel']
		self.sfIncAccel		= d['sfIncAccel']
		self.sfUnclimbable	= d['sfUnclimbable']
		self.sfDiggable		= d['sfDiggable']
		self.sfNoFriction	= d['sfNoFriction']
		self.sfStairs		= d['sfStairs']
		self.sfWater		= d['sfWater']
		self.sfCannotLand	= d['sfCannotLand']
		self.sfHurt			= d['sfHurt']
		self.sfFootprints	= d['sfFootprints']
		self.sfGravity		= d['sfGravity']
		self.sfUseRotation	= d['sfUseRotation']
		self.sfDynCollision	= d['sfDynCollision']


		# SA1
		self.sfWaterCollision		= d['sfWaterCollision']	
		self.sfUseSkyDrawDistance	= d['sfUseSkyDrawDistance']
		self.sfNoZWrite				= d['sfNoZWrite']
		self.sfLowDepth				= d['sfLowDepth']
		self.sfDrawByMesh			= d['sfDrawByMesh']
		self.sfWaterfall			= d['sfWaterfall']
		self.sfChaos0Land			= d['sfChaos0Land']
		self.sfEnableManipulation	= d['sfEnableManipulation']
		self.sfSA1U_200				= d['sfSA1U_200']
		self.sfSA1U_800				= d['sfSA1U_800']
		self.sfSA1U_8000			= d['sfSA1U_8000']
		self.sfSA1U_20000			= d['sfSA1U_20000']
		self.sfSA1U_80000			= d['sfSA1U_80000']
		self.sfSA1U_20000000		= d['sfSA1U_20000000']
		self.sfSA1U_40000000		= d['sfSA1U_40000000']


		# SA2
		self.sfWater2			= d['sfWater2']
		self.sfNoShadows		= d['sfNoShadows']
		self.sfNoFog			= d['sfNoFog']
		self.sfSA2U_40			= d['sfSA2U_40']
		self.sfSA2U_200			= d['sfSA2U_200']
		self.sfSA2U_4000		= d['sfSA2U_4000']
		self.sfSA2U_10000		= d['sfSA2U_10000']
		self.sfSA2U_20000		= d['sfSA2U_20000']
		self.sfSA2U_40000		= d['sfSA2U_40000']
		self.sfSA2U_800000		= d['sfSA2U_800000']
		self.sfSA2U_1000000		= d['sfSA2U_1000000']
		self.sfSA2U_2000000		= d['sfSA2U_2000000']
		self.sfSA2U_4000000		= d['sfSA2U_4000000']
		self.sfSA2U_20000000	= d['sfSA2U_20000000']
		self.sfSA2U_40000000	= d['sfSA2U_40000000']

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

	DataFiles: EnumProperty(
		name="Data Files",
		items=()
	)

	MdlFiles: EnumProperty(
		name="Mdl Files",
		items=()
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
