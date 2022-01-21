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
		scale = 1 + var1
		scaleMtx = common.matrixFromScale((scale,scale,scale))

		self.worldMtx = posMtx @ rotMtx @ scaleMtx

	#def __str__(self):
	#    return str(self.index) + " : " + str(self.clippingLvl) + ", " + str(self.rotation) + ", " + str(self.pos) + ", " + str(self.var) + ";"


def ReadFile(path: str, context, bigEndian: bool):
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

		obj = bpy.data.objects.new("SET_" + str(o.index) + "_" + str(i), None)
		obj.matrix_world = o.worldMtx

		col.objects.link(obj)


