import math
from typing import List
import configparser
import os
import io
import bpy
import mathutils
from .. import common

def GetCurveCodeAddress(type: str, addr: str):
	if (type == 'sa1_loop'):
		return ('4BB1F0')
	elif (type == 'sa2_rail'):
		return ('4980C0')
	elif (type == 'sa2_loop'):
		return ('497B50')
	elif (type == 'sa2_hand'):
		return ('498140')
	elif (type == 'none'):
		if addr != '':
			return (addr)
		else:
			return ('0')
	else:
		return ('0')

class PathEntry:
	XRotation: float
	ZRotation: float
	Distance: float
	px: float
	py: float
	pz: float

	def __init__(self):
		self.px = 0
		self.py = 0
		self.pz = 0
		self.Distance = 0
		self.XRotation = 0
		self.ZRotation = 0

	def setPoint(self,
				rotx: float,
				rotz: float,
				dist: float,
				pos: common.Vector3):
		self.px = pos[0]
		self.py = -pos[2]
		self.pz = pos[1]
		self.XRotation = rotx
		self.ZRotation = -rotz
		self.Distance = dist

	def fromIni(self, 
				coords: str,
				xrot: str,
				zrot: str,
				distance: float
				):
		sx = coords.split(', ')[0]
		sy = coords.split(', ')[1]
		sz = coords.split(', ')[2]
		self.px = float(sx)
		self.py = float(sy)
		self.pz = float(sz)

		if xrot != "":
			nxrot = int(xrot, 16)
			self.XRotation = common.BAMSToRad(nxrot)
		else:
			self.XRotation = 0

		if zrot != "":
			nzrot = int(zrot, 16)
			self.ZRotation = common.BAMSToRad(nzrot)
		else:
			self.ZRotation = 0

		if distance != "":
			self.Distance = float(distance)
		else:
			self.Distance = 0

	def fromMesh(self,
				vert: bpy.types.MeshVertex,
				dist: float):
		self.px = vert.co[0]
		self.py = vert.co[1]
		self.pz = vert.co[2]
		rotation = common.PGetAngleXZFromNormal(-vert.normal[0], vert.normal[2], -vert.normal[1])
		self.XRotation = math.radians(rotation[0])
		self.ZRotation = math.radians(-rotation[1])
		self.Distance = dist
		
class PathData:
	"""Ini Formatted Path Data from the Adventure Games."""

	Name: str
	TotalDistance: float
	Entries: List[PathEntry]

	def __init__(self):
		self.Name = ""
		self.TotalDistance = 0
		self.Entries = list()

	def fromIni(self, path):
		config = io.StringIO()
		filepath = os.path.abspath(path)
		print(filepath)

		if os.path.isfile(path):
			config.write('[Head]\n')
			config.write(open(filepath).read())
			config.seek(0, os.SEEK_SET)

			cp = configparser.ConfigParser()
			cp.read_file(config)
			entries = []
			self.Name = os.path.basename(filepath)
			for section in cp.sections():
				if section == "Head":
					self.TotalDistance = cp.getfloat(section, "TotalDistance")
				else:
					coords = ""
					if cp.has_option(section, "Position"):
						coords = cp.get(section, "Position")
					xrot = ""
					if cp.has_option(section, "XRotation"):
						xrot = cp.get(section, "XRotation")
					zrot = ""
					if cp.has_option(section, "ZRotation"):
						zrot = cp.get(section, "ZRotation")
					distance = 0
					if cp.has_option(section, "Distance"):
						distance = cp.getfloat(section, "Distance")

					entry = PathEntry()
					entry.fromIni(coords, xrot, zrot, distance)
					entries.append(entry)

			self.Entries = entries

	def toIni(path, curve: bpy.types.Spline, points: List[bpy.types.Object], pathtype: str, caddr: str):
		filepath = os.path.abspath(path) + '.ini'
		print(filepath)
		with open(filepath, 'w') as config:
			config.write('TotalDistance=' + ("%.6f" % curve.calc_length()) + '\n')
			config.write('Code=' + GetCurveCodeAddress(pathtype, caddr) + '\n\n')
			idx = 0
			for p in curve.points:
				s = str(idx)
				c = points[idx]
				config.write('[' + s + ']\n')
				print('Writing Point: ' + s)
				if (c.rotation_euler[0] != 0):
					rx = hex(common.RadToBAMS(c.rotation_euler[0]))[2:]
					config.write('XRotation=' + rx.upper() + '\n')
					print('X Rotation: ' + str(c.rotation_euler[0]) + ' -> ' + rx)
				if (c.rotation_euler[1] != 0):
					rz = hex(common.RadToBAMS(-c.rotation_euler[1]))[2:]
					config.write('ZRotation=' + rz.upper() + '\n')
					print('Z Rotation: ' + str(-c.rotation_euler[1]) + ' -> ' + rz)
				if (p != curve.points[-1]):
					dist = (mathutils.Vector((curve.points[idx+1].co - p.co)).length)
					config.write('Distance=' + ("%.6f" % dist) + '\n')
					print('Distance: ' + ("%.6f" % dist))
				sv = (("%.6f" % p.co[0]) + ', ' + ("%.6f" % p.co[2]) + ', ' + ("%.6f" % -p.co[1]))
				config.write('Position=' + sv + '\n\n')
				print('Position: ' + sv)
				idx += 1

			config.close()
		
	def toCode(path, curve: bpy.types.Spline, points: List[bpy.types.Object], pathtype: str, caddr: str, pathname: str):
		filepath = os.path.abspath(path) + '.c'
		pathname = pathname.split('.')[0]
		with open(filepath, 'w') as config:
			# Write Loop/Path Array
			config.write("Loop %s_Points[] = {\n" % (pathname))
			idx = 0
			for p in curve.points:
				c = points[idx]
				rx = hex(common.RadToBAMS(c.rotation_euler[0])).upper()
				rz = hex(common.RadToBAMS(-c.rotation_euler[1])).upper()
				if (p != curve.points[-1]):
					dist = (mathutils.Vector((curve.points[idx+1].co - p.co)).length)
					config.write("\t{ %s, %s, %.6f, { %.6f, %.6f, %.6f } },\n" % (rx, rz, dist, p.co[0], p.co[2], -p.co[1]))
				else:
					dist = 0.0
					config.write("\t{ %s, %s, %.6f, { %.6f, %.6f, %.6f } }\n" % (rx, rz, dist, p.co[0], p.co[2], -p.co[1]))	
				idx += 1
			config.write("};\n\n")

			# Write LoopHead/PathTag
			info = ("{ 0, LengthOfArray(%s_Points), %.6f, %s_Points, (ObjectFuncPtr)0x%s };" % (pathname, curve.calc_length(), pathname, GetCurveCodeAddress(pathtype, caddr)))
			config.write("LoopHead %s_Path = %s" % (pathname, info))

			config.close()