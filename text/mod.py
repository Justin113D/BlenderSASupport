import os
import io
import configparser

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