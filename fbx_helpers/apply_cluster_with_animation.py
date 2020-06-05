import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import xml.etree.ElementTree
import os

# conform to Left___ and Right___ naming
def mobu_convention(j):
    if j.name()[-2:-1] == "_":
        for old, new in [['l', 'Left'], ['r', 'Right']]:
            if j.name()[-1:].lower() == old:
                new_name = new + j.name()[:-2]
                pm.rename(j.name(), new_name)
                return
# delete the incoming node to translation and scale
def break_ts_anim(j):
    con = j.listConnections(connections = 1)
    for c in con:
        if c[1].type() in ['animCurveTL', 'animCurveTU']:
            pm.delete(c[1])
            #pm.setAttr(c[0], keyable = 0, cb = 1)

# export the deformer weights to the WORKING_DIR and 
# return a tuple of shape and associated xml file
def export_deformer_weights(geo, path):
    assert geo.type() == 'transform'
    shape = [sh for sh in pm.listRelatives(geo, s = 1) if sh.name() == geo + "Shape"][0]
    assert shape.type() == 'mesh'
    
    # due to our export it's only going to be 1 cluster anyway
    cl = shape.listConnections(t = 'skinCluster')[0]
    name = shape.name() + "_" + cl.name() + ".xml"
    try:
        file_name = pm.deformerWeights(name, deformer=cl, path=path, export = 1)
    except:
        print(shape.name() + " has no skinClusters to export.")

# freeze the rotations of joints, by disconnecting them first
def apply_joint_orientations(joints):
    
    for j in joints: # (angular ?)
        connections = j.listConnections(type='animCurveTA', connections = 1)
    
        # Freezing transforms doesn't work as expected, when
        # a parent is scaled.
        #pm.makeIdentity(j, apply=1, t=0, r=1, s=0, n=0, jo=0)
        
        #orient = pm.getAttr(ob + ".rotate")
        #j_orient = pm.getAttr(ob + ".jointOrient")
        start_values = pm.getAttr(j + ".rotate")
        
        for i, con in enumerate(connections):
            #pm.connectAttr(con[1] + ".output", con[0])
            crv = con[1]
            values = pm.keyframe(crv, q = 1, vc = 1)
            
            start_values[i] = values[0]
            pm.keyframe(crv, vc = -values[0], r = 1)
        
        pm.setAttr(j + ".rotate", pm.datatypes.Vector())
        pm.setAttr(j + ".jointOrient", start_values)


# "scale" a rig by scaling the translation values
def scale_joints(joints, scale_factor):
    for j in joints:
        v = j.getAttr("t")
        v = [scale_factor * x for x in v]
        j.setAttr("t", v)


# scale geometry and freeze everything
def scale_geo(geo, scale_factor):
    for g in geo:
        v = g.getAttr("s")
        v = [scale_factor * x for x in v]
        g.setAttr("s", v)
        pm.makeIdentity(g, apply=1, t=1, r=1, s=1, n=0, jo=0)


# remove bind poses 
def remove_bindPoses(joints):
    for j in joints:
        con = pm.listConnections(j, d = 1, type='dagPose')
        for c in con:
            try:
                pm.delete(c)
            except:
                # bind node already deleted
                pass

# shifts curves on the x axis an optionally removes doubles
def shift_curves(joints, START_FRAME = 1, REMOVE_DOUBLES = True):
    connections = []
    for j in joints:
        con = j.listConnections(type='animCurveTA', connections = 1)
        connections.extend(con)
    for con in connections:
        crv = con[1]
    
        keys = pm.keyframe(crv, q = 1, tc = 1)
    
        time_change = START_FRAME - keys[0]
        pm.keyframe(crv, tc = time_change, r = 1)
        
        keys = pm.keyframe(crv, q = 1, tc = 1)
        values = pm.keyframe(crv, q = 1, vc = 1)
        
        if REMOVE_DOUBLES:
            ranges = []
            last = values[0] + 1
            for i in range(len(keys)):
                if values[i] == last:
                    ranges.append(keys[i])
                last = values[i]
            for r in ranges:
                pm.cutKey(crv, time = (r, r))

# assign the color of an object to the incandescence field
def lambert_to_flat(ob):
    shapes = ob.listRelatives(c=1, s=1)
    for s in shapes:
        connections = s.listConnections(type="shadingEngine")
        connections = list(set(connections))
        for shadingEng in connections:
            print("se", shadingEng)
            lamberts = shadingEng.listConnections(type="lambert")
            for l in lamberts:
                print("la", l)
                col = l.getAttr('color')
                l.setAttr('ambientColor', (0, 0, 0))
                if col != (0.0, 0.0, 0.0):
                    l.setAttr('incandescence', col)
                    l.setAttr('color', (0, 0, 0))
                
# import all xml files as deformer weights and apply them to the skincluster
def import_deformer_weights(WORKING_DIR):
    files = [x for x in os.listdir(WORKING_DIR) if x[-4:] == '.xml']
    
    for f in files:
        file_path = os.path.join(WORKING_DIR, f)
        deformer_xml = xml.etree.ElementTree.parse(file_path)
        
        # only made for one skincluster per mesh
        geo = None
        joints = []
        for atype in deformer_xml.findall('shape'):
            geo = pm.ls(atype.get('name'))[0]
        for atype in deformer_xml.findall('weights'):
            joints.append(atype.get('source'))
        print(str(geo) + " > "  + str(joints))
        
        # create the skincluster and apply it to the geo
        # note: geo is shape-node
        skin_cluster = pm.skinCluster(joints, geo, toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=0, inf=1)
        # already connected? then assign manually
        #skin_cluster = pm.ls("skinCluster1")[0]
        print(skin_cluster)
        
        pm.deformerWeights(f, deformer=skin_cluster, path=WORKING_DIR, im = 1)
        pm.select(geo)
        mel.eval("skinPercent -normalize true " + skin_cluster)
        #return shape, name
        #cmds.select(cmds.skinCluster('skinCluster2', q=True, inf=True))


WORKING_DIR = "D:/weights/"
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

START_FRAME = 1
GLOBAL_SCALE = 1

geo = [g for g in pm.ls(an=1, ap=1,et='transform') if pm.listRelatives(g, s = 1)[0].type() == 'mesh']
joints = pm.ls(an=1, ap=1, et='joint')

# do we need to conform functions to always take lists of joints
# or do the looping outside of the function and only pass single joints
if True:
    for j in joints:
        break_ts_anim(j)
        if not len(j.listRelatives(p=True)):
            pm.setAttr(j + '.tx', 0)
            pm.setAttr(j + '.ty', 0)
            pm.setAttr(j + '.tz', 0)
        pm.setAttr(j + ".radius", 0.5)

# export weights
if True:
    for g in geo:
        export_deformer_weights(g, WORKING_DIR)
        
        # don't use single shader, use incandescence option
        
        #shader = [x for x in pm.ls(type="shadingEngine") if x.name() == 'initialShadingGroup'][0]
        #pm.sets(shader, forceElement=g)
        
        #lambert_to_flat(g)
        
        # remove skinCluster
        pm.delete(g, ch = 1)

if True:
    shift_curves(joints, START_FRAME)
    pm.setCurrentTime(START_FRAME)
    apply_joint_orientations(joints)

# scale geometry and joints, freeze scale on geometry, use the translation method for joints
if True:
    scale_factor = GLOBAL_SCALE
    scale_joints(joints, scale_factor)
    scale_geo(geo, scale_factor)

# delete the construction history and import the exported weights
if True:
    pm.refresh()
    for g in geo:
        pm.delete(g, ch = 1)
    import_deformer_weights(WORKING_DIR)
    pm.refresh()

# key all translate vale at the start frame
if True:
    for j in joints:
        if not len(j.listRelatives(p=True)):
            pm.setKeyframe(j, at='translate', time=[START_FRAME], v=0)
        else:
            pm.setKeyframe(j, at='translate', time=[START_FRAME])



if True:
    for j in joints:
        mobu_convention(j)

if True:
    for files in os.listdir(WORKING_DIR):
        os.remove(os.path.join(WORKING_DIR, files))
    import shutil
    shutil.rmtree(WORKING_DIR)
