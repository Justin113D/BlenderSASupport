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

from .. import common
from ..prop.properties import(
    SASettings,
    SAEditPanelSettings,
    SALandEntrySettings,
    SAMaterialSettings,
    SAMeshSettings,
    SATexture
)
from .panel_draw import(
	propAdv,
	drawMaterialPanel,
	drawObjPanel,
	drawMeshPanel,
	drawScenePanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots
)
from .panel_spaces import(
    SA_Scene_Panel
)
from ..ops.quickEdit import(
	qeUpdate,
	qeUpdateSet,
	qeUpdateUnset,
	qeReset,
	qeInvert
)

class SA_SceneInfo_ScenePanel(SA_Scene_Panel, bpy.types.Panel):				## Scene Information Panel (Author, Texlist, etc)
	bl_idname = "WORLD_PT_saProperties"
	bl_label = "SA Scene Information"

	def draw(self, context):
		layout = self.layout
		settings = context.scene.saSettings

		drawScenePanel(layout, settings)