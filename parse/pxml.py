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
		if info.get('canBuild') == "true":
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
		if root.get('BigEndian') == "true":
			self.BigEndian = True
		else:
			self.BigEndian = False
		self.ModelFile = root.get('ModelFile')
		for mot in root.findall('MotionFile'):
			self.MotionFiles.append(mot.text)

class ProjectFile:
	"""Sonic Adventure Project File Class.
	Ported from the SA Tools C# code."""

	Filepath: str
	GameInfo: ProjectInfo
	SplitEntries: List[SplitEntry]
	SplitMDLEntries: List[SplitEntryMdl]

	def __init__(self, 
				filepath: str,
				gameInfo: ProjectInfo,
				splitEntries: list(),
				splitMdlEntries: list()):
		self.Filepath = filepath
		self.GameInfo = gameInfo
		self.SplitEntries = splitEntries
		self.SplitMDLEntries = splitMdlEntries

	def ReadProjectFile(path):
		if os.path.isfile(path):
			file = ET.parse(path)
			root = file.getroot()

			t_splitEntries = []
			t_splitMDLEntries = []
			t_info = ProjectInfo(root)
			#for entry in root.findall('SplitEntry'):
			#	t_splitEntries.append(SplitEntry(entry))
			#for mdl in root.findall('SplitEntryMDL'):
			#	t_splitMDLEntries.append(SplitEntryMdl(mdl))

			projFile = ProjectFile(path, t_info, t_splitEntries, t_splitMDLEntries)

			return projFile

	def GetProjectFolder(file):
		projPath = ""
		if file.GameInfo:
			projPath = file.GameInfo.ProjectFolder
			print(projPath)
			if projPath.__contains__("\"") is False:
				path = file.Filepath.split(".")
				projPath = path[0] + "\\"
				print(projPath)

		return projPath