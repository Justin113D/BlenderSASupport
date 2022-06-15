import bpy

from . import fileHelper, common, os
import mathutils

class ObjEntry:

	index: int
	clippingLvl: int

	worldMtx: mathutils.Matrix
	var: common.Vector3

	def __init__(self,
				 index: int,
				 clippingLvl: int,
				 xRot: int,
				 yRot: int,
				 zRot: int,
				 posx: float,
				 posy: float,
				 posz: float,
				 var1: float,
				 var2: float,
				 var3: float):
		self.index = index
		self.clippingLvl = clippingLvl
		self.var = common.Vector3((var1, var2, var3))

		xRot = common.BAMSToRad(xRot)
		yRot = common.BAMSToRad(yRot)
		zRot = common.BAMSToRad(zRot)

		posMtx = mathutils.Matrix.Translation((posx, -posz, posy))
		rotMtx = mathutils.Euler((xRot, -zRot, yRot), 'XZY').to_matrix().to_4x4()
		scale = 1
		scaleMtx = common.matrixFromScale((scale,scale,scale))

		self.worldMtx = posMtx @ rotMtx @ scaleMtx

def ReadFile(path: str, context, bigEndian: bool, useEntryNum: bool):
	fileR = fileHelper.FileReader(path)
	fileR.setBigEndian(bigEndian)

	objCount = fileR.rUInt(0)
	print("objects:", objCount)

	objs = list()

	for i in range(objCount):
		tmpAddr = 0x20 + (i * 0x20)
		header = fileR.rUShort(tmpAddr)
		objs.append(ObjEntry(
			header & 0x0FFF,
			(header & 0xF000) >> 0xC,
			fileR.rShort(tmpAddr + 0x02),
			fileR.rShort(tmpAddr + 0x04),
			fileR.rShort(tmpAddr + 0x06),
			fileR.rFloat(tmpAddr + 0x08),
			fileR.rFloat(tmpAddr + 0x0C),
			fileR.rFloat(tmpAddr + 0x10),
			fileR.rFloat(tmpAddr + 0x14),
			fileR.rFloat(tmpAddr + 0x18),
			fileR.rFloat(tmpAddr + 0x1C) ))

	cName = os.path.splitext(os.path.basename(path))[0]
	col = bpy.data.collections.new("SET_" + cName)
	context.scene.collection.children.link(col)

	for i, o in enumerate(objs):
		#print(str(o))
		if (useEntryNum):
			name = str(i) + "_SetItem_" + str(o.index)
		else:
			name = "SetItem_" + str(o.index)
		obj = bpy.data.objects.new(name, None)
		obj.matrix_world = o.worldMtx

		col.objects.link(obj)

class sa1CamEntry:
	camType: int
	camPriority: int
	camAdjType: int
	camColType: int
	camRotationX: int
	camRotationY: int
	camPositionX: float
	camPositionY: float
	camPositionZ: float
	camScaleX: float
	camScaleY: float
	camScaleZ: float
	camAngleX: int
	camAngleY: int
	camPointAx: float
	camPointAy: float
	camPointAz: float
	camPointBx: float
	camPointBy: float
	camPointBz: float
	camVariable: float

	camMtx: mathutils.Matrix
	camPointAMtx: mathutils.Matrix
	camPointBMtx: mathutils.Matrix

	def __init__(self,
				camType: int,
				camPriority: int,
				camAdjType: int,
				camColType: int,
				camRotationX: int,
				camRotationY: int,
				camPositionX: float,
				camPositionY: float,
				camPositionZ: float,
				camScaleX: float,
				camScaleY: float,
				camScaleZ: float,
				camAngleX: int,
				camAngleY: int,
				camPointAx: float,
				camPointAy: float,
				camPointAz: float,
				camPointBx: float,
				camPointBy: float,
				camPointBz: float,
				camVariable: float):

		self.camType = camType
		self.camPriority = camPriority
		self.camAdjType = camAdjType
		self.camColType = camColType

		xRot = common.BAMSToRad(camRotationX)
		yRot = common.BAMSToRad(camRotationY)

		posMtx = mathutils.Matrix.Translation((camPositionX, -camPositionZ, camPositionY))
		rotMtx = mathutils.Euler((xRot, 0, yRot), 'XZY').to_matrix().to_4x4()
		scaleMtx = common.matrixFromScale((1, 1, 1))

		camPointRotMtx = mathutils.Euler((0, 0, 0), 'XZY').to_matrix().to_4x4()
		camPointA_posMtx = mathutils.Matrix.Translation((camPointAx, -camPointAz, camPointAy))
		camPointB_posMtx = mathutils.Matrix.Translation((camPointBx, -camPointBz, camPointBy))

		self.camMtx = posMtx @ rotMtx @ scaleMtx
		self.camPointAMtx = camPointA_posMtx @ camPointRotMtx @ scaleMtx
		self.camPointBMtx = camPointB_posMtx @ camPointRotMtx @ scaleMtx

def ReadCamFile(path: str, context, bigEndian: bool, useEntryNum: bool, isSA2: bool):
	fileR = fileHelper.FileReader(path)
	fileR.setBigEndian(bigEndian)

	camCount = fileR.rUInt(0)
	print("Cameras: ", camCount)

	camList = list()

	if (isSA2):
		print("SA2 Camera Import not Implemented")
	else:
		for i in range(camCount):
			tmpAddr = 0x40 + (i * 0x40)
			camList.append(sa1CamEntry(
				fileR.rSByte(tmpAddr),
				fileR.rSByte(tmpAddr + 0x01),
				fileR.rSByte(tmpAddr + 0x02),
				fileR.rSByte(tmpAddr + 0x03),
				fileR.rUShort(tmpAddr + 0x04),
				fileR.rUShort(tmpAddr + 0x06),
				fileR.rFloat(tmpAddr + 0x08),
				fileR.rFloat(tmpAddr + 0x0C),
				fileR.rFloat(tmpAddr + 0x10),
				fileR.rFloat(tmpAddr + 0x14),
				fileR.rFloat(tmpAddr + 0x18),
				fileR.rFloat(tmpAddr + 0x1C),
				fileR.rUShort(tmpAddr + 0x20),
				fileR.rUShort(tmpAddr + 0x22),
				fileR.rFloat(tmpAddr + 0x24),
				fileR.rFloat(tmpAddr + 0x28),
				fileR.rFloat(tmpAddr + 0x2C),
				fileR.rFloat(tmpAddr + 0x30),
				fileR.rFloat(tmpAddr + 0x34),
				fileR.rFloat(tmpAddr + 0x38),
				fileR.rFloat(tmpAddr + 0x3C)
			))

		cName = os.path.splitext(os.path.basename(path))[0]
		col = bpy.data.collections.new("CamFile_" + cName)
		context.scene.collection.children.link(col)

		for i, o in enumerate(camList):
			#print(str(o))
			if (useEntryNum):
				name = str(i) + "_Cam_" + str(o.camType)
			else:
				name = "Cam_" + str(o.camType) + "_" + str(i)
			cam = bpy.data.objects.new(name, None)
			camA = bpy.data.objects.new(name + "_A", None)
			camA.parent = cam
			camB = bpy.data.objects.new(name + "_B", None)
			camB.parent = cam
			cam.matrix_world = o.camMtx
			camA.matrix_world = o.camPointAMtx
			camB.matrix_world = o.camPointBMtx

			cam.empty_display_type = 'CUBE'
			camA.empty_display_type = 'SPHERE'
			camB.empty_display_type = 'SPHERE'
			
			col.objects.link(camA)
			col.objects.link(camB)
			col.objects.link(cam)
