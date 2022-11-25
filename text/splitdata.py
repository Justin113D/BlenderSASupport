from typing import List
import configparser
import os
import io

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