from typing import List, Dict, Tuple
import os
import io
import configparser

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

	def __init__(self, path):
		config = io.StringIO()
		filepath = os.path.abspath(path)
		print(filepath)
		if os.path.isfile(path):
			config.write('[mod]\n')
			config.write(open(filepath).read())
			config.seek(0, os.SEEK_SET)
			cp = configparser.ConfigParser()
			cp.read_file(config)
			if cp.has_option('mod', 'Name'):
				self.Name = cp.get('mod', 'Name')
			else:
				self.Name = ""
			if cp.has_option('mod', 'Description'):
				self.Description = cp.get('mod', 'Description')
			else:
				self.Description = ""
			if cp.has_option('mod', 'Author'):
				self.Author = cp.get('mod', 'Author')
			else:
				self.Author = ""
			if cp.has_option('mod', 'Version'):
				self.Version = cp.get('mod', 'Version')
			else:
				self.Version = ""