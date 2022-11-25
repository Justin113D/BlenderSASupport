from typing import List
import configparser
import os
import io

class SATexFile:
	'''SA Tex File (.satex) Class Handler'''

	Name: str
	TexnameArrayName: str
	Num: int
	TextureNames: List[str]

	def __init__(self):
		self.Name = ""
		self.TexnameArrayName = ""
		self.Num = 0
		self.TextureNames = list()

	def fromIni(self, path):
		'''Loads .satex data into Blender.'''
		config = io.StringIO()
		filepath = os.path.abspath(path)
		print(filepath)

		if os.path.isfile(path):
			config.write('[Head]\n')
			config.write(open(filepath).read())
			config.seek(0, os.SEEK_SET)

			cp = configparser.ConfigParser()
			cp.read_file(config)
			s = "Head"
			self.Name = cp.get(s, "Name")
			self.TexnameArrayName = cp.get(s, "TexnameArrayName")
			self.Num = cp.getint(s, "NumTextures")
			for i in range(self.Num):
				name = cp.get(s, "TextureNames[" + str(i) + "]") + ".png"
				print(name)
				self.TextureNames.append(name)