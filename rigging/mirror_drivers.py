"""
Arun Leander, 2018
"""

import bpy

#con = bpy.context.object.pose.bones[3].constraints[0]

def mirror_drivers():
    pl = '.l'
    pr = '.r'
    
    rig = bpy.context.object
    if rig.type != 'ARMATURE':
        print('not armature')
        return
    
    if rig.animation_data == None:
        print('no drivers')
        return
    drivers = rig.animation_data.drivers
    
    for driver in drivers:
        dp = driver.data_path
        bone_name = dp[12:].split('"')[0]
        
        
        if dp.find(pl) and rig.pose.bones[bone_name].bone.select:
            driver_a = driver.driver
            dp_mirrored = dp.replace(pl, pr)
            driver_b = rig.driver_add(dp_mirrored).driver
            driver_b.type = driver_a.type
            
            for old_var in driver_a.variables:
                
                var = driver_b.variables.new()
                var.targets[0].id = rig
                
                var.name = old_var.name
                
                var.type = old_var.type
                var.targets[0].id_type = old_var.targets[0].id_type
                var.targets[0].id = old_var.targets[0].id
                var.targets[0].data_path = old_var.targets[0].data_path.replace(pl, pr)
            driver_b.expression = driver_a.expression
        else:
            print("assymetrical driver found:", driver.data_path)

        

mirror_drivers()