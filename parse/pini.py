import bpy
from typing import List, Dict, Tuple
import os
import io
import configparser
from .. import common
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

class PathEntry:
	XRotation: float
	YRotation: float
	ZRotation: float
	Distance: float
	px: float
	py: float
	pz: float

	def __init__(self, 
				coords: str,
				xrot: str,
				yrot: str,
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

		if yrot != "":
			nyrot = int(yrot, 16)
			self.YRotation = common.BAMSToRad(nyrot)
		else:
			self.YRotation = 0

		if zrot != "":
			nzrot = int(zrot, 16)
			self.ZRotation = common.BAMSToRad(nzrot)
		else:
			self.ZRotation = 0

		if distance is not "":
			self.Distance = float(distance)
		else:
			self.Distance = 0

class PathData:
	"""Ini Formatted Path Data from the Adventure Games."""

	Name: str
	TotalDistance: float
	Entries: List[PathEntry]

	def __init__(self, path):
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
					yrot = ""
					if cp.has_option(section, "YRotation"):
						yrot = cp.get(section, "YRotation")
					zrot = ""
					if cp.has_option(section, "ZRotation"):
						zrot = cp.get(section, "ZRotation")
					distance = 0
					if cp.has_option(section, "Distance"):
						distance = cp.getfloat(section, "Distance")

					entry = PathEntry(coords, xrot, yrot, zrot, distance)
					entries.append(entry)

			self.Entries = entries
