from typing import List
import configparser
import os
import io

class CharacterInfo:
	"""SALVL Character Sections"""

	Character: str
	Model: str
	Textures: str
	Height: float
	StartPos: str

	def __init__(self,
			chr: str,
			mdl: str,
			tex: str,
			hgt: float,
			sPos: str):
		self.Character = chr
		self.Model = mdl
		self.Textures = tex
		self.Height = hgt
		self.StartPos = sPos

class LevelInfo:
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

	def __init__(self,
			type: str,
			name: str,
			geo: str,
			id: str,
			tex: str,
			objList: str,
			objTList: str,
			dZones: str,
			effect: str,
			objDefs: str):
		self.LevelType = type
		self.LevelName = name
		self.LevelGeometry = geo
		self.LevelID = id
		self.Textures = tex
		self.ObjList = objList
		self.ObjTexList = objTList
		self.DeathZones = dZones
		self.Effects = effect
		self.ObjDefs = objDefs

