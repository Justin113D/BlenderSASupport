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
	drawLandEntryPanel,
	drawMeshPanel,
	SCENE_UL_SATexList,
	SCENE_MT_Texture_Context_Menu,
	MATERIAL_UL_saMaterialSlots
)
from .panel_spaces import(
    SA_Material_Panel
)
from ..ops.quickEdit import(
	qeUpdate,
	qeUpdateSet,
	qeUpdateUnset,
	qeReset,
	qeInvert
)

class SA_MaterialProps_MaterialPanel(SA_Material_Panel, bpy.types.Panel):
    bl_idname = "MATERIAL_PT_saProperties"
    bl_label = "SA Material Properties"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        if context.active_object.active_material is not None:
            menuProps = context.scene.saSettings.editorSettings
            matProps = context.active_object.active_material.saSettings
            drawMaterialPanel(layout, menuProps, matProps)