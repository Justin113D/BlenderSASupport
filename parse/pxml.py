from typing import List, Dict, Tuple
import os
import xml.etree.ElementTree as ET

class ProjectInfo:
	"""Project Info storage used in a Project File."""

	GameName: str
	CheckFile: str
	GameDataFolder: str
	ProjectFolder: str
	CanBuild: bool

	def __init__(self, root: ET.Element):
		info = root.find('GameInfo')
		self.GameName = info.get('gameName')
		self.CheckFile = info.get('checkFile')
		self.GameDataFolder = info.get('gameDataFolder')
		self.ProjectFolder = info.get('projectFolder')
		if info.get('canBuild') is "true":
			self.CanBuild = True
		else:
			self.CanBuild = False

class SplitEntry:
	"""Split Entry Information"""

	SourceFile: str
	IniFile: str
	CmnName: str

	def __init__(self, root: ET.Element):
		self.SourceFile = root.get('SourceFile')
		self.IniFile = root.get('IniFile')
		self.CmnName = root.get('CmnName')

class SplitEntryMdl:
	"""Split Entry Information for SA2 MDL Files."""

	BigEndian: bool
	ModelFile: str
	MotionFiles: List[str]

	def __init__(self, root: ET.Element):
		if root.get('BigEndian') is "true":
			self.BigEndian = True
		else:
			self.BigEndian = False
		self.ModelFile = root.get('ModelFile')
		for mot in root.findall('MotionFile'):
			self.MotionFiles.append(mot.text)

class ProjectFile:
	"""Sonic Adventure Project File Class.
	Ported from the SA Tools C# code."""

	GameInfo: ProjectInfo
	SplitEntries: List[SplitEntry]
	SplitMDLEntries: List[SplitEntryMdl]

	def __init__(self, path):
		print(path)
		if os.path.isfile(path):
			file = ET.parse(path)
			root = file.getroot()

			t_splitEntries = []
			t_splitMDLEntries = []
			t_info = ProjectInfo(root)
			for entry in root.findall('SplitEntry'):
				t_splitEntries.append(SplitEntry(entry))
			for mdl in root.findall('SplitEntryMDL'):
				t_splitMDLEntries.append(SplitEntryMDL(mdl))

			self.GameInfo = t_info
			self.SplitEntries = t_splitEntries
			self.SplitMDLEntries = t_splitMDLEntries
