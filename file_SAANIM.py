import bpy
import mathutils

# Big thanks to @SageOfMirrors, without whom this would have taken at least 10 times longer to make!

class ArmatureInvalidException(Exception):
    def __init__(self, message):
        super().__init__(message)

def read(filepath: str, obj):
    from .common import BAMSToRad

    print("importing", filepath)
    if filepath.endswith(".json"):
        import json
        f = open(filepath)
        anim = json.load(f)
        f.close()

        action = bpy.data.actions.new(anim["Name"])
        action.use_fake_user = True
        frame_count = anim["Frames"]
        rate = 2 # get this from the ini!

        armature = obj.data

        # creating the fcurves for later usage
        for m in anim["Models"]:
            if int(m) == 0:
                basePath = ""
                mtx = obj.matrix_local
                group = action.groups.new("Root")
            else:
                bone = armature.bones[int(m) - 1] # the root is a bone too, but doesnt count as one
                basePath = "pose.bones[\"{}\"].".format(bone.name)

                if bone.parent is None:
                    mtx = bone.matrix_local
                else:
                    mtx = (bone.parent.matrix_local.inverted() @ bone.matrix_local)

                group = action.groups.new(bone.name)

            mdl = anim["Models"][m]

            posCurves: list = None
            rotCurves: list = None
            scaleCurves: list = None

            if len(mdl["Position"]) > 0:
                posCurves = list()
                for pos in range(3):
                    pos_comp = action.fcurves.new(data_path=basePath + "location", index = pos)
                    pos_comp.keyframe_points.add(len(mdl["Position"]))
                    pos_comp.auto_smoothing = "NONE"
                    pos_comp.group = group
                    posCurves.append(pos_comp)

            if len(mdl["Rotation"]) > 0:
                rotCurves = list()
                for rot in range(4):
                    quat_comp = action.fcurves.new(data_path=basePath + "rotation_quaternion", index = rot)
                    quat_comp.keyframe_points.add(len(mdl["Rotation"]))
                    quat_comp.auto_smoothing = "NONE"
                    quat_comp.group = group
                    rotCurves.append(quat_comp)

            if len(mdl["Scale"]) > 0:
                scaleCurves = list()
                for scale in range(3):
                    scale_comp = action.fcurves.new(data_path=basePath + "scale", index = scale)
                    scale_comp.keyframe_points.add(len(mdl["Scale"]))
                    scale_comp.group = group
                    scaleCurves.append(scale_comp)

            posFrameID = 0
            rotFrameID = 0
            scaleFrameID = 0



            for frame in range(frame_count):
                frameStr = str(frame)
                frameLoc = frame * rate

                if posCurves is not None and frameStr in mdl["Position"]:
                    posVec = mdl["Position"][frameStr]
                    posVec = posVec.split(", ")
                    posVec = mathutils.Vector((float(posVec[0]), -float(posVec[2]), float(posVec[1])))
                    posVec = posVec - mtx.to_translation()

                    for i, k in enumerate(posCurves):
                        keyframe = k.keyframe_points[posFrameID]
                        keyframe.interpolation = "LINEAR"
                        keyframe.co = frameLoc, posVec[i]

                    posFrameID += 1

                if rotCurves is not None and frameStr in mdl["Rotation"]:
                    rotVec = mdl["Rotation"][frameStr]
                    rotVec = rotVec.split(", ")
                    rotVec = (  BAMSToRad(int(rotVec[0], 16)),
                                -BAMSToRad(int(rotVec[2], 16)),
                                BAMSToRad(int(rotVec[1], 16)) )
                    rotMtx = mathutils.Euler(rotVec, 'XZY').to_matrix().to_4x4() #.to_quaternion()

                    rotVec = (mtx.inverted() @ rotMtx).to_quaternion()

                    for i, k in enumerate(rotCurves):
                        keyframe = k.keyframe_points[rotFrameID]
                        keyframe.interpolation = "LINEAR"
                        keyframe.co = frameLoc, rotVec[i]

                    rotFrameID += 1

                if posCurves is not None and frameStr in mdl["Scale"]:
                    scaleVec = mdl["Scale"][frameStr]
                    scaleVec = scaleVec.split(", ")
                    scaleVec = (float(scaleVec[0]), float(scaleVec[2]), float(scaleVec[1]))

                    for i, k in enumerate(scaleCurves):
                        keyframe = k.keyframe_points[scaleFrameID]
                        keyframe.interpolation = "LINEAR"
                        keyframe.co = frameLoc, scaleVec[i]

                    scaleFrameID += 1
