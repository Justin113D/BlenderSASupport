import bpy

class SA_UI_Panel:				## Viewport UI Panel
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "SA Tools"

class SA_Scene_Panel:			## Scene Panel Info
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "scene"

class SA_Tool_Panel:			## Active Tool Panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_category = 'Tool'

class SA_Object_Panel:			## Object Panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "object"

class SA_Model_Panel:			## Mesh Panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"

class SA_Material_Panel:		## Material Panel
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "material"
