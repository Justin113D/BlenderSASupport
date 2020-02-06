import bpy
import mathutils
import os
import math

from typing import Dict, List, Tuple

# Big thanks to @SageOfMirrors, without whom this would have taken at least 10 times longer to make!

class ArmatureInvalidException(Exception):
    def __init__(self, message):
        super().__init__(message)

def read(filepath: str, nameConv, obj):
    from .common import BAMSToRad

    print("importing", filepath)
    if filepath.endswith(".json"):
        import json
        f = open(filepath)
        anim = json.load(f)
        f.close()

        os.path.basename(filepath)

        name = ""
        if nameConv != "CONTENT":
            name = os.path.basename(filepath)[:len(name) - 5]
            try:
                name = int(name)
                name = str(name).zfill(3)
            except:
                pass
        if nameConv != "FILE":
            if len(name) > 0:
                name += "_"
            name += anim["Name"]

        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        frame_count = anim["Frames"]

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
                    mtx = obj.matrix_local.inverted() @ bone.matrix_local
                else:
                    mtx = (obj.matrix_local.inverted() @ bone.parent.matrix_local).inverted() @ bone.matrix_local

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

                if posCurves is not None and frameStr in mdl["Position"]:
                    posVec = mdl["Position"][frameStr]
                    posVec = posVec.split(", ")
                    posVec = mathutils.Vector((float(posVec[0]), -float(posVec[2]), float(posVec[1])))
                    posVec = posVec - mtx.to_translation()

                    for i, k in enumerate(posCurves):
                        keyframe = k.keyframe_points[posFrameID]
                        keyframe.interpolation = "LINEAR"
                        keyframe.co = frame, posVec[i]

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
                        keyframe.co = frame, rotVec[i]

                    rotFrameID += 1

                if posCurves is not None and frameStr in mdl["Scale"]:
                    scaleVec = mdl["Scale"][frameStr]
                    scaleVec = scaleVec.split(", ")
                    scaleVec = (float(scaleVec[0]), float(scaleVec[2]), float(scaleVec[1]))

                    for i, k in enumerate(scaleCurves):
                        keyframe = k.keyframe_points[scaleFrameID]
                        keyframe.interpolation = "LINEAR"
                        keyframe.co = frame, scaleVec[i]

                    scaleFrameID += 1

def jsonEmptyModel():
    model = dict()
    model["Position"] = dict()
    model["Rotation"] = dict()
    model["Scale"] = dict()
    model["Vector"] = dict()
    model["Vertex"] = dict()
    model["Normal"] = dict()
    model["Target"] = dict()
    model["Roll"] = dict()
    model["Angle"] = dict()
    model["Color"] = dict()
    model["Intensity"] = dict()
    model["Spot"] = dict()
    model["Point"] = dict()
    return model

# this method is generally usable for every addon btw :3
# It's always nice to only export the necessary frames :P
def getFramesToCalc(curves: List[bpy.types.FCurve], end) -> List[int]:
    # notes:
    # 1. Every curve/model needs a keyframe for start and end
    # 2. if a curve is not starting/ending at the first/last frame,
    # then the frames between the first frame and start of the curve/last frame and end of the curve can be left out.
    # Everything inside the curve range should be baked
    # 3. except if:
    # - the curve is in repeat mode, then the entire animation should be baked
    # - the last read keyframe was set to linear

    frameLists: List[int] = list()
    for c in curves:
        ip = c.keyframe_points[0].interpolation

        frames: Dict[int, str] = dict()
        floatingFrames: Dict[int, List[Tuple[int, str]]] = dict() # e.g. 0 = nodes between 0 and 1

        # getting the basic keyframes first
        for i in c.keyframe_points:
            if i.co.x.is_integer():
                frames[int(i.co.x)] = i.interpolation
            else:
                base = math.floor(i.co.x)
                if base not in floatingFrames:
                    floatingFrames[base] = list()

                floatingFrames[base].append((i.co.x, i.interpolation))

        for k, v in floatingFrames.items():
            if k not in frames:
                frames[k] = 'LINEAR' # we can just put linear, since the next frame is definitely set

            if k + 1 not in frames:
                if len(v) == 1:
                    frames[k + 1] = v[0][1]
                else:
                    v = sorted(v, key=lambda x: x[0])
                    frames[k + 1] = v[-1][1]

        # now lets get the ones between frames that we specifically need to calculate (stuff that isnt linear)
        frameList: List[int] = list()
        keys = sorted(frames.keys())
        lastKey = len(keys) - 1

        for i, f in enumerate(keys):
            frameList.append(f)
            if i < lastKey:
                ip = frames[f]
                nextFrame = keys[i + 1]
                if ip == 'CONSTANT':
                    if c.evaluate(f) != c.evaluate(nextFrame):
                        frameList.append(nextFrame - 1)
                elif ip != 'LINEAR':
                    frameList.extend(range(f + 1, nextFrame)) # add all frames in between

        frameLists.append(frameList)

    # and lastly, join those frame lists

    output: List[int] = [0, int(end)]
    for f in frameLists:
        output.extend(f)

    return sorted(set(output))

def setFrameValues(curve: bpy.data.curves, default: int, channel: int, outList: Dict[int, mathutils.Vector]):
    if curve is None:
        for v in outList.values():
            v[channel] = default
    else:
        for k, v in outList.items():
            v[channel] = curve.evaluate(k)

# cT = Use the current pose transform as default value for nonexistent channels
def write(filepath: str, bakeAll: bool, shortRot: bool, bezierInterpolation: bool, cT: bool, obj):
    from .common import RadToBAMS
    action: bpy.types.Action = obj.animation_data.action
    armature = obj.data

    from bpy_extras.io_utils import axis_conversion
    global_matrix = axis_conversion(to_forward='-Z', to_up='Y',).to_4x4()

    # mapping the curves to the bones
    curveMap: Dict[str, List[bpy.types.FCurve]] = dict()
    frame_End = 0
    for c in action.fcurves:
        c: bpy.types.FCurve = c
        name = c.data_path

        if name.startswith("pose.bones[\""):
            end = name.find("\"]")
            name = name[12:end]

            if name not in curveMap:
                curveMap[name] = list()

            curveMap[name].append(c)
        elif name.count('.') == 0: # the root

            if None not in curveMap:
                curveMap[None] = list()

            curveMap[None].append(c)
        else:
            continue

        # getting the end of the curve
        end = c.keyframe_points[-1].co.x
        if end > frame_End:
            frame_End = end

    models = dict()
    allFrames = range(0, int(frame_End + 1))

    for k, v in curveMap.items():
        if k != None:
            bone = None

            for b in obj.pose.bones:
                if b.name == k:
                    bone = b
                    break

            if bone == None:
                print("Couldnt find bone in armature!")
                continue

            index = armature.bones.find(bone.bone.name) + 1

            endKey = k + "\"]."

            if bone.parent is None:
                mtx = bone.bone.matrix_local
            else:
                mtx = bone.bone.parent.matrix_local.inverted() @ bone.bone.matrix_local

            rotType = bone.rotation_mode

            defaultPos, defaultRot, defaultScale = bone.matrix_basis.decompose()

            if rotType != 'QUATERNION':
                defaultRot = bone.matrix_basis.to_euler(rotType)

        else:
            endKey = ""
            mtx = obj.matrix_local
            rotType = obj.rotation_mode
            index = 0
            defaultPos, defaultRot, defaultScale = mtx.decompose()

            if rotType != 'QUATERNION':
                defaultRot = mtx.to_euler(rotType)

        posCurves = list()
        rotCurves = list()
        scaleCurves = list()

        for c in v:
            name = c.data_path
            if name.endswith(endKey + "location"):
                posCurves.append(c)
            elif rotType == 'QUATERNION' and name.endswith(endKey + "rotation_quaternion") or rotType != 'QUATERNION' and name.endswith(endKey + "rotation_euler"):
                rotCurves.append(c)
            elif name.endswith(endKey + "scale"):
                scaleCurves.append(c)

        model = jsonEmptyModel()

        # doing positions first
        if len(posCurves) > 0:

            # determining which frames to write first
            frames = allFrames if bakeAll else getFramesToCalc(posCurves, frame_End)
            positions: Dict[int, mathutils.Vector] = {f: mathutils.Vector() for f in frames}

            curves = [None] * 3

            for c in posCurves:
                curves[c.array_index] = c

            if cT:
                for c in curves:
                    setFrameValues(c, defaultPos[c.array_index], c.array_index, positions)
            else:
                for c in curves:
                    setFrameValues(c, 0, c.array_index, positions)

            jsonPos = model["Position"]
            for k, v in positions.items():
                pos = global_matrix @ (mtx @ v)
                jsonPos[str(k)] = "{0}, {1}, {2}".format(round(pos.x, 6), round(pos.y, 6), round(pos.z, 6))

        # next the rotations
        if len(rotCurves) > 0:

            frames = allFrames if bakeAll else getFramesToCalc(rotCurves, frame_End)
            if rotType == 'QUATERNION':
                rotations: Dict[int, mathutils.Vector] = {f: mathutils.Quaternion() for f in frames}
                curves = [None] * 4
                identityRot = (0,0,0,1)
            else:
                rotations: Dict[int, mathutils.Vector] = {f: mathutils.Euler() for f in frames}
                curves = [None] * 3
                identityRot = (0,0,0)

            for c in rotCurves:
                curves[c.array_index] = c

            if cT:
                for c in curves:
                    setFrameValues(c, defaultRot[c.array_index], c.array_index, rotations)
            else:
                for c in curves:
                    setFrameValues(c, identityRot[c.array_index], c.array_index, rotations)

            jsonRot = model["Rotation"]
            for k, v in rotations.items():
                # please dont kill me mathematicians owo'
                matrix = v.to_matrix().to_4x4()
                rot = matrix.to_euler('XZY')
                rot = global_matrix @ mathutils.Vector((rot.x, rot.y, rot.z))

                x = hex(RadToBAMS(rot.x, not shortRot))[2:]
                y = hex(RadToBAMS(rot.y, not shortRot))[2:]
                z = hex(RadToBAMS(rot.z, not shortRot))[2:]

                jsonRot[str(k)] = "{0}, {1}, {2}".format(x,y,z)

        # and lastly the scale curves
        if len(scaleCurves) > 0:

            frames = allFrames if bakeAll else getFramesToCalc(scaleCurves, frame_End)
            scales: Dict[int, mathutils.Vector] = {f: mathutils.Vector() for f in frames}

            curves = [None] * 3

            for c in scaleCurves:
                curves[c.array_index] = c

            if cT:
                for c in curves:
                    setFrameValues(c, defaultScale[c.array_index], c.array_index, scales)
            else:
                for c in curves:
                    setFrameValues(c, 1, c.array_index, scales)

            jsonScale = model["Scale"]
            for k, v in scales.items():
                # scaling doesnt need to get affected by any matrix, as it isnt part of the bones edit matrix
                jsonScale[str(k)] = "{0}, {1}, {2}".format(round(v.x, 6), round(v.z, 6), round(v.y, 6))


        models[str(index)] = model

    # setting up the json file

    jsonF = dict()
    jsonF["Models"] = models
    jsonF["Frames"] = int(frame_End) + 1
    jsonF["Name"] = action.name
    jsonF["ModelParts"] = len(armature.bones) + 1
    jsonF["InteroplationMode"] = 1 if bezierInterpolation else 0
    jsonF["ShortRot"] = shortRot

    import json
    with open(filepath, 'w') as outfile:
        json.dump(jsonF, outfile, indent=2)

    return {'FINISHED'}
