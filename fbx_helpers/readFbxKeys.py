"""
Arun Leander, 2020

Requires FBX API

"""

import FbxCommon
import sys

def GetHierarchy(pScene, parent = None):
    nodes = []
    if parent == None:
        parent = pScene.GetRootNode()
    else:
        nodes.append(parent)
    
    for i in range(parent.GetChildCount()):
        nodes.extend(GetHierarchy(pScene, parent.GetChild(i)))
    return nodes


def GetTakes(pScene):
    return [pScene.GetSrcObject(FbxCommon.FbxCriteria.ObjectType(FbxCommon.FbxAnimStack.ClassId), i)
            for i in range(pScene.GetSrcObjectCount(FbxCommon.FbxCriteria.ObjectType(FbxCommon.FbxAnimStack.ClassId)))]

def GetAnimLayer(pAnimStack, pNode):
    numberOfAnimLayers = pAnimStack.GetSrcObjectCount(FbxCommon.FbxCriteria.ObjectType(FbxCommon.FbxAnimLayer.ClassId))
    lAnimLayer = pAnimStack.GetSrcObject(FbxCommon.FbxCriteria.ObjectType(FbxCommon.FbxAnimLayer.ClassId),
                                        0)

    return {
        'tx': GetCrvKeys(pNode.LclTranslation.GetCurve(lAnimLayer, "X")),
        'ty': GetCrvKeys(pNode.LclTranslation.GetCurve(lAnimLayer, "Y")),
        'tz': GetCrvKeys(pNode.LclTranslation.GetCurve(lAnimLayer, "Z")),
        'rx': GetCrvKeys(pNode.LclRotation.GetCurve(lAnimLayer, "X")),
        'ry': GetCrvKeys(pNode.LclRotation.GetCurve(lAnimLayer, "Y")),
        'rz': GetCrvKeys(pNode.LclRotation.GetCurve(lAnimLayer, "Z"))
    }

def GetCrvKeys(pCurve):
    if pCurve == None:
        return []

    lKeyCount = pCurve.KeyGetCount()
    return {pCurve.KeyGetTime(i).GetFrameCountPrecise(): pCurve.KeyGetValue(i) for i in range(lKeyCount)}

def GetFbxData(fileName, namespace):
    lSdkManager, lScene = FbxCommon.InitializeSdkObjects()

    lResult = FbxCommon.LoadScene(lSdkManager, lScene, fileName)

    nodes = [n for n in GetHierarchy(lScene) if n.GetTypeName() == "LimbNode" and namespace in n.GetName()]

    takes = {}
    for take in GetTakes(lScene):
        skeleton = {}
        for node in nodes:
            name = node.GetName()[len(namespace):]
            skeleton[name] = GetAnimLayer(take, node)

        takes[take.GetName()] = skeleton
    return takes

# testing
#PrintFbxData("transfer.fbx", "dude:")
#exit()


takeName = sys.argv[1]
namespace = sys.argv[2]
takes = GetFbxData(takeName, namespace)

import json
sys.stdout.write(json.dumps(takes))