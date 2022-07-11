import bpy
from typing import List, Dict, Tuple
import os
import io
import configparser
from .. import common
import math
import mathutils

class DLLMetaData:
	"""Metadata used in SAMDL."""

	Filename: str
	Name: str
	Texture: str

	def __init__(self,
				Filename: str,
				Name: str,
				Texture: str
				):
		self.Filename = Filename
		self.Name = Name
		self.Texture = Texture

class DataFile:
	"""Data File Class for *_data.ini project files."""

	Name: str
	Type: str
	Filename: str
	Texture: str

	def __init__(self,
				Name: str,
				Type: str,
				Filename: str,
				Texture: str
				):

		self.Name = Name
		self.Type = Type
		self.Filename = Filename
		self.Texture = Texture

class salvl_char:
	"""SALVL Character Sections"""

	Character: str
	Model: str
	Textures: str
	Height: float
	StartPos: str

class salvl_level:
	"""SALVL Level Sections"""

	LevelType: str
	LevelName: str
	LevelGeometry: str
	LevelID: str
	Textures: str
	ObjList: str
	ObjTexList: str
	DeathZones: str
	Effects: str
	ObjDefs: str

class ModFile:
	"""Partial Mod File class ported from SA Tools."""

	Name: str
	Description: str
	Author: str
	Version: str

	def __init__(self,
				name: str,
				desc: str,
				auth: str,
				vers: str):
		self.Name = name
		self.Description = desc
		self.Author = auth
		self.Version = vers


	def ReadFile(path):
		modFile = None
		config = io.StringIO()
		filepath = os.path.abspath(path)
		print(filepath)
		if os.path.isfile(path):
			config.write('[mod]\n')
			config.write(open(filepath).read())
			config.seek(0, os.SEEK_SET)
			cp = configparser.ConfigParser()
			cp.read_file(config)
			name = ""
			desc = ""
			auth = ""
			vers = ""
			if cp.has_option('mod', 'Name'):
				name = cp.get('mod', 'Name')
			if cp.has_option('mod', 'Description'):
				desc = cp.get('mod', 'Description')
			if cp.has_option('mod', 'Author'):
				auth = cp.get('mod', 'Author')
			if cp.has_option('mod', 'Version'):
				vers = cp.get('mod', 'Version')

			modFile = ModFile(name, desc, auth, vers)

		return modFile

def GetCurveCodeAddress(type: str):
	if (type == 'sa1_loop'):
		return ('4BB1F0')
	if (type == 'sa2_rail'):
		return ('4980C0')
	if (type == 'sa2_loop'):
		return ('497B50')
	if (type == 'sa2_hand'):
		return ('498140')
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

		if distance is not "":
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

	def toIni(path, curve: bpy.types.Spline, points: List[bpy.types.Object], pathtype: str):
		filepath = os.path.abspath(path)
		print(filepath)
		with open(filepath, 'w') as config:
			config.write('TotalDistance=' + ("%.6f" % curve.calc_length()) + '\n')
			config.write('Code=' + GetCurveCodeAddress(pathtype) + '\n\n')
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
		