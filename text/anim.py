import json
from ..enums import InterpolationModeEnums
from typing import Dict, List

def NewJsonModel():
	mdl = dict()
	mdl["Position"] = dict()
	mdl["Rotation"] = dict()
	mdl["Scale"] = dict()
	mdl["Vector"] = dict()
	mdl["Vertex"] = dict()
	mdl["Normal"] = dict()
	mdl["Target"] = dict()
	mdl["Roll"] = dict()
	mdl["Angle"] = dict()
	mdl["Color"] = dict()
	mdl["Intensity"] = dict()
	mdl["Spot"] = dict()
	mdl["Point"] = dict()
	mdl["Quaternion"] = dict()
	mdl["PositionName"] = ""
	mdl["RotationName"] = ""
	mdl["ScaleName"] = ""
	mdl["VectorName"] = ""
	mdl["VertexName"] = ""
	mdl["VertexItemName"] = list()
	mdl["NormalItemName"] = list()
	mdl["NormalName"] = ""
	mdl["TargetName"] = ""
	mdl["RollName"] = ""
	mdl["AngleName"] = ""
	mdl["ColorName"] = ""
	mdl["IntensityName"] = ""
	mdl["SpotName"] = ""
	mdl["PointName"] = ""
	mdl["QuaternionName"] = ""
	mdl["NbKeyframes"] = 0
	return mdl

def NewJsonFile():
	file = dict()
	file["Models"] = dict()
	file["Frames"] = 0
	file["Name"] = ""
	file["Description"] = ""
	file["MdataName"] = ""
	file["ModelParts"] = 0
	file["InterpolationMode"] = InterpolationModeEnums.Linear
	file["ShortRot"] = False
	file["ActionName"] = ""
	file["ObjectName"] = ""
	return file

class AnimJsonModel:
	Position: dict()
	Rotation: dict()
	Scale: dict()
	Vector: dict()
	Vertex: dict()
	Normal: dict()
	Target: dict()
	Roll: dict()
	Angle: dict()
	Color: dict()
	Intensity: dict()
	Spot: dict()
	Point: dict()
	Quaternion: dict()
	PositionName: str
	RotationName: str
	ScaleName: str
	VectorName: str
	VertexName: str
	VertexItemName: List[str]
	NormalItemName: List[str]
	NormalName: str
	TargetName: str
	RollName: str
	AngleName: str
	ColorName: str
	IntensityName: str
	SpotName: str
	PointName: str
	QuaternionName: str
	NbKeyframes: int

	def __init__(self):
		self.Position = dict()
		self.Rotation = dict()
		self.Scale = dict()
		self.Vector = dict()
		self.Vertex = dict()
		self.Normal = dict()
		self.Target = dict()
		self.Roll = dict()
		self.Angle = dict()
		self.Color = dict()
		self.Intensity = dict()
		self.Spot = dict()
		self.Point = dict()
		self.Quaternion = dict()
		self.PositionName = ""
		self.RotationName = ""
		self.ScaleName = ""
		self.VectorName = ""
		self.VertexName = ""
		self.VertexItemName = list()
		self.NormalItemName = list()
		self.NormalName = ""
		self.TargetName = ""
		self.RollName = ""
		self.AngleName = ""
		self.ColorName = ""
		self.IntensityName = ""
		self.SpotName = ""
		self.PointName = ""
		self.QuaternionName = ""
		self.NbKeyframes = 0

	def ReadModelEntry(self, jsonF):
		if (jsonF.get('Position') != None):
			if (jsonF["Position"] != None):
				if (len(jsonF["Position"]) > 0):
					for k, v in jsonF["Position"].items():
						self.Position[k] = v
		if (jsonF.get('Rotation') != None):
			if (jsonF["Rotation"] != None):
				if (len(jsonF["Rotation"]) > 0):
					for k, v in jsonF["Rotation"].items():
						self.Rotation[k] = v
		if (jsonF.get('Scale') != None):
			if (jsonF["Scale"] != None):
				if (len(jsonF["Scale"]) > 0):
					for k, v in jsonF["Scale"].items():
						self.Scale[k] = v
		if (jsonF.get('Vector') != None):
			if (jsonF["Vector"] != None):
				if (len(jsonF["Vector"]) > 0):
					for k, v in jsonF["Vector"].items():
						self.Vector[k] = v
		if (jsonF.get('Vertex') != None):
			if (jsonF["Vertex"] != None):
				if (len(jsonF["Vertex"]) > 0):
					for k, v in jsonF["Vertex"].items():
						self.Vertex[k] = v
		if (jsonF.get('Normal') != None):
			if (jsonF["Normal"] != None):
				if (len(jsonF["Normal"]) > 0):
					for k, v in jsonF["Normal"].items():
						self.Normal[k] = v
		if (jsonF.get('Target') != None):
			if (jsonF["Target"] != None):
				if (len(jsonF["Target"]) > 0):
					for k, v in jsonF["Target"].items():
						self.Target[k] = v
		if (jsonF.get('Roll') != None):
			if (jsonF["Roll"] != None):
				if (len(jsonF["Roll"]) > 0):
					for k, v in jsonF["Roll"].items():
						self.Roll[k] = v
		if (jsonF.get('Angle') != None):
			if (jsonF["Angle"] != None):
				if (len(jsonF["Angle"]) > 0):
					for k, v in jsonF["Angle"].items():
						self.Angle[k] = v
		if (jsonF.get('Color') != None):
			if (jsonF["Color"] != None):
				if (len(jsonF["Color"]) > 0):
					for k, v in jsonF["Color"].items():
						self.Color[k] = v
		if (jsonF.get('Intensity') != None):
			if (jsonF["Intensity"] != None):
				if (len(jsonF["Intensity"]) > 0):
					for k, v in jsonF["Intensity"].items():
						self.Intensity[k] = v
		if (jsonF.get('Spot') != None):
			if (jsonF["Spot"] != None):
				if (len(jsonF["Spot"]) > 0):
					for k, v in jsonF["Spot"].items():
						self.Spot[k] = v
		if (jsonF.get('Point') != None):
			if (jsonF["Point"] != None):
				if (len(jsonF["Point"]) > 0):
					for k, v in jsonF["Point"].items():
						self.Point[k] = v
		if (jsonF.get('Quaternion') != None):
			if (jsonF["Quaternion"] != None):
				if (len(jsonF["Quaternion"]) > 0):
					for k, v in jsonF["Quaternion"].items():
						self.Quaternion[k] = v
		if (jsonF.get('PositionName') != None):
			if (jsonF["PositionName"] != None):
				self.PositionName = jsonF["PositionName"]
		if (jsonF.get('RotationName') != None):
			if (jsonF["RotationName"] != None):
				self.RotationName = jsonF["RotationName"]
		if (jsonF.get('ScaleName') != None):
			if (jsonF["ScaleName"] != None):
				self.ScaleName = jsonF["ScaleName"]
		if (jsonF.get('VectorName') != None):
			if (jsonF["VectorName"] != None):
				self.VectorName = jsonF["VectorName"]
		if (jsonF.get('VertexName') != None):
			if (jsonF["VertexName"] != None):
				self.VertexName = jsonF["VertexName"]
		if (jsonF.get('VertexItemName') != None):
			if (jsonF["VertexItemName"] != None):
				if (len(jsonF["VertexItemName"]) > 0):
					for i in jsonF["VertexItemName"]:
						self.VertexItemName.append(i)
		if (jsonF.get('NormalItemName') != None):
			if (jsonF["NormalItemName"] != None):
				if (len(jsonF["NormalItemName"]) > 0):
					for i in jsonF["NormalItemName"]:
						self.NormalItemName.append(i)
		if (jsonF.get('NormalName') != None):
			if (jsonF["NormalName"] != None):
				self.NormalName = jsonF["NormalName"]
		if (jsonF.get('TargetName') != None):
			if (jsonF["TargetName"] != None):
				self.TargetName = jsonF["TargetName"]
		if (jsonF.get('RollName') != None):
			if (jsonF["RollName"] != None):
				self.RollName = jsonF["RollName"]
		if (jsonF.get('AngleName') != None):
			if (jsonF["AngleName"] != None):
				self.AngleName = jsonF["AngleName"]
		if (jsonF.get('ColorName') != None):
			if (jsonF["ColorName"] != None):
				self.ColorName = jsonF["ColorName"]
		if (jsonF.get('IntensityName') != None):
			if (jsonF["IntensityName"] != None):
				self.IntensityName = jsonF["IntensityName"]
		if (jsonF.get('SpotName') != None):
			if (jsonF["SpotName"] != None):
				self.SpotName = jsonF["SpotName"]
		if (jsonF.get('PointName') != None):
			if (jsonF["PointName"] != None):
				self.PointName = jsonF["PointName"]
		if (jsonF.get('QuaternionName') != None):
			if (jsonF["QuaternionName"] != None):
				self.QuaternionName = jsonF["QuaternionName"]
		if (jsonF.get('NbKeyframes') != None):
			if (jsonF["NbKeyframes"] != None):
				self.NbKeyframes = jsonF["NbKeyframes"]

	def toJson(self):
		outMdl = NewJsonModel()

		outMdl["NbKeyframes"] = self.NbKeyframes
		outMdl["VertexItemName"] = self.VertexItemName
		outMdl["NormalItemName"] = self.NormalItemName

		if (len(self.Position) > 0):
			for k, v in self.Position.items():
				outMdl["Position"][k] = v
		if (len(self.Rotation) > 0):
			for k, v in self.Rotation.items():
				outMdl["Rotation"][k] = v
		if (len(self.Scale) > 0):
			for k, v in self.Scale.items():
				outMdl["Scale"][k] = v
		if (len(self.Vector) > 0):
			for k, v in self.Vector.items():
				outMdl["Vector"][k] = v
		if (len(self.Vertex) > 0):
			for k, v in self.Vertex.items():
				outMdl["Vertex"][k] = v
		else:
			outMdl["Vertex"] = dict()
		if (len(self.Normal) > 0):
			for k, v in self.Normal.items():
				outMdl["Normal"][k] = v
		else:
			outMdl["Normal"] = dict()
		if (len(self.Target) > 0):
			for k, v in self.Target.items():
				outMdl["Target"][k] = v
		if (len(self.Roll) > 0):
			for k, v in self.Roll.items():
				outMdl["Roll"][k] = v
		if (len(self.Angle) > 0):
			for k, v in self.Angle.items():
				outMdl["Angle"][k] = v
		if (len(self.Color) > 0):
			for k, v in self.Color.items():
				outMdl["Color"][k] = v
		if (len(self.Intensity) > 0):
			for k, v in self.Intensity.items():
				outMdl["Intensity"][k] = v
		if (len(self.Spot) > 0):
			for k, v in self.Spot.items():
				outMdl["Spot"][k] = v
		if (len(self.Point) > 0):
			for k, v in self.Point.items():
				outMdl["Point"][k] = v
		if (len(self.Quaternion) > 0):
			for k, v in self.Quaternion.items():
				outMdl["Quaternion"][k] = v

		if (self.PositionName != ""):
			outMdl["PositionName"] = self.PositionName
		else:
			outMdl["PositionName"] = None
		if (self.RotationName != ""):
			outMdl["RotationName"] = self.RotationName
		else:
			outMdl["RotationName"] = None
		if (self.ScaleName != ""):
			outMdl["ScaleName"] = self.ScaleName
		else:
			outMdl["ScaleName"] = None
		if (self.VectorName != ""):
			outMdl["VectorName"] = self.VectorName
		else:
			outMdl["VectorName"] = None
		if (self.VertexName != ""):
			outMdl["VertexName"] = self.VertexName
		else:
			outMdl["VertexName"] = None
		if (self.NormalName != ""):
			outMdl["NormalName"] = self.NormalName
		else:
			outMdl["NormalName"] = None
		if (self.TargetName != ""):
			outMdl["TargetName"] = self.TargetName
		else:
			outMdl["TargetName"] = None
		if (self.RollName != ""):
			outMdl["RollName"] = self.RollName
		else:
			outMdl["RollName"] = None
		if (self.AngleName != ""):
			outMdl["AngleName"] = self.AngleName
		else:
			outMdl["AngleName"] = None
		if (self.ColorName != ""):
			outMdl["ColorName"] = self.ColorName
		else:
			outMdl["ColorName"] = None
		if (self.IntensityName != ""):
			outMdl["IntensityName"] = self.IntensityName
		else:
			outMdl["IntensityName"] = None
		if (self.SpotName != ""):
			outMdl["SpotName"] = self.SpotName
		else:
			outMdl["SpotName"] = None
		if (self.PointName != ""):
			outMdl["PointName"] = self.PointName
		else:
			outMdl["PointName"] = None
		if (self.QuaternionName != ""):
			outMdl["QuaternionName"] = self.QuaternionName
		else:
			outMdl["QuaternionName"] = None

		return outMdl

class AnimJsonFile:
	Frames: int
	Name: str
	Description: str
	MdataName: str
	ModelParts: int
	InterpolationMode: InterpolationModeEnums
	ShortRot: bool
	ActionName: str
	ObjectName: str
	Models: Dict[int, AnimJsonModel]

	def __init__(self):
		self.Frames = 0
		self.Name = ""
		self.Description = ""
		self.MdataName = ""
		self.ModelParts = 0
		self.InterpolationMode = InterpolationModeEnums.Linear
		self.ShortRot = False
		self.ActionName = ""
		self.ObjectName = ""
		self.Models = dict()

	def ReadJsonFile(self, file: str):
		print("Opening: " + file)
		f = open(file)
		jsonF = json.load(f)
		f.close()

		if (jsonF.get('Models') != None):
			if (jsonF["Models"] != None):
				if (len(jsonF["Models"]) > 0):
					for k, v in jsonF["Models"].items():
						animModel = AnimJsonModel()
						animModel.ReadModelEntry(v)
						self.Models[k] = animModel
		if (jsonF.get('Frames') != None):
			if (jsonF["Frames"] != None):
				self.Frames = jsonF["Frames"]
		if (jsonF.get('Name') != None):
			if (jsonF["Name"] != None):
				self.Name = jsonF["Name"]
		if (jsonF.get('Description') != None):
			if (jsonF["Description"] != None):
				self.Description = jsonF["Description"]
		if (jsonF.get('MdataName') != None):
			if (jsonF["MdataName"] != None):
				self.MdataName = jsonF["MdataName"]
		if (jsonF.get('ModelParts') != None):
			if (jsonF["ModelParts"] != None):
				self.ModelParts = jsonF["ModelParts"]
		if (jsonF.get('InterpolationMode') != None):
			if (jsonF["InterpolationMode"] != None):
				self.InterpolationMode = InterpolationModeEnums(jsonF["InterpolationMode"])
		if (jsonF.get('ShortRot') != None):
			if (jsonF["ShortRot"] != None):
				self.ShortRot = jsonF["ShortRot"]
		if (jsonF.get('ActionName') != None):
			if (jsonF["ActionName"] != None):
				self.ActionName = jsonF["ActionName"]
		if (jsonF.get('ObjectName') != None):
			if (jsonF["ObjectName"] != None):
				self.ObjectName = jsonF["ObjectName"]

	def toJson(self, file: str):
		jsonF = NewJsonFile()

		for k, v in self.Models.items():
			mdlF = v.toJson()
			jsonMdl = mdlF
			jsonF["Models"][k] = jsonMdl

		jsonF["Frames"] = self.Frames
		jsonF["ShortRot"] = self.ShortRot
		jsonF["InterpolationMode"] = int(self.InterpolationMode.value)
		jsonF["ModelParts"] = self.ModelParts

		if (self.Name != ""):
			jsonF["Name"] = self.Name
		else:
			jsonF["Name"] = None

		if (self.MdataName != ""):
			jsonF["MdataName"] = self.MdataName
		else:
			jsonF["MdataName"] = None
		
		if (self.ActionName != ""):	
			jsonF["ActionName"] = self.ActionName
		else:
			jsonF["ActionName"] = None
		
		if (self.ObjectName != ""):
			jsonF["ObjectName"] = self.ObjectName
		else:
			jsonF["ObjectName"] = None

		
		with open(file, 'w') as outfile:
			json.dump(jsonF, outfile, indent=2)
			print(file + " saved successfully!")