# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2022 Steven Garcia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####

import bpy

from math import radians
from .format import JMAAsset
from mathutils import Matrix
from ..global_functions import mesh_processing, global_functions

def generate_jms_skeleton(JMS_A_nodes, JMS_A, JMS_B_nodes, JMS_B, JMA, armature, fix_rotations, game_version):
    created_bone_list = []
    file_version = JMA.version
    r_hand_idx = None
    is_fp_root_file_a = False
    file_type = "JMS"

    bpy.ops.object.mode_set(mode = 'EDIT')
    for idx, jma_node in enumerate(JMA.nodes):
        created_bone_list.append(jma_node.name)
        current_bone = armature.data.edit_bones.new(jma_node.name)
        if "r_hand" in jma_node.name.lower() or "r hand" in jma_node.name.lower():
            r_hand_idx = idx

        parent = None
        parent_name = None
        jms_node = None
        bone_distance = 5
        for a_idx, jms_a_node in enumerate(JMS_A_nodes):
            if jma_node.name.lower() in jms_a_node.lower():
                if JMA.nodes[0].name.lower() in JMS_A_nodes[0].lower():
                    is_fp_root_file_a = True

                file_version = JMS_A.version
                parent_idx = JMS_A.nodes[a_idx].parent
                parent_name = JMS_A.nodes[parent_idx].name
                rest_position = JMS_A.transforms[0]
                jms_node = rest_position[a_idx]
                bone_distance = mesh_processing.get_bone_distance(JMS_A, a_idx, "JMS")

        for b_idx, jms_b_node in enumerate(JMS_B_nodes):
            if jma_node.name.lower() in jms_b_node.lower():
                file_version = JMS_B.version
                parent_idx = JMS_B.nodes[b_idx].parent
                parent_name = JMS_B.nodes[parent_idx].name
                rest_position = JMS_B.transforms[0]
                jms_node = rest_position[b_idx]
                bone_distance = mesh_processing.get_bone_distance(JMS_B, b_idx, "JMS")

        if not jms_node:
            if is_fp_root_file_a:
                rest_position = JMS_A.transforms[0]

            else:
                rest_position = JMS_B.transforms[0]

            jms_node = rest_position[0]

        current_bone.tail[2] = bone_distance

        for bone_idx, bone in enumerate(created_bone_list):
            if not parent_name == None:
                if bone in parent_name:
                    parent = armature.data.edit_bones[bone_idx]

            else:
                parent = armature.data.edit_bones[0]

        matrix_translate = Matrix.Translation(jms_node.translation)
        matrix_rotation = jms_node.rotation.to_matrix().to_4x4()

        if not parent == None:
            current_bone.parent = parent

        elif "gun" in jma_node.name:
            current_bone.parent = armature.data.edit_bones[r_hand_idx]

        is_root = False
        if JMS_A:
            if jma_node.name.lower() in JMS_A.nodes[0].name.lower():
                is_root = True

        if JMS_B:
            if jma_node.name.lower() in JMS_B.nodes[0].name.lower():
                is_root = True

        transform_matrix = matrix_translate @ matrix_rotation
        if fix_rotations:
            if file_version < global_functions.get_version_matrix_check(file_type, game_version) and current_bone.parent and not is_root:
                transform_matrix = (current_bone.parent.matrix @ Matrix.Rotation(radians(90.0), 4, 'Z')) @ transform_matrix

            current_bone.matrix = transform_matrix @ Matrix.Rotation(radians(-90.0), 4, 'Z')

        else:
            if file_version < global_functions.get_version_matrix_check(file_type, game_version) and current_bone.parent and not is_root:
                transform_matrix = current_bone.parent.matrix @ transform_matrix

            current_bone.matrix = transform_matrix

def generate_jma_skeleton(JMS_A_nodes, JMS_A, JMS_A_invalid, JMS_B_nodes, JMS_B, JMS_B_invalid, JMA, armature, parent_id_class, fix_rotations, game_version):
    file_version = JMA.version
    first_frame = JMA.transforms[0]

    file_type = "JMA"
    if JMS_A and not JMS_A_invalid:
        file_type = "JMS"

    bpy.ops.object.mode_set(mode = 'EDIT')
    for idx, jma_node in enumerate(JMA.nodes):
        current_bone = armature.data.edit_bones.new(jma_node.name)
        parent_idx = jma_node.parent

        if not parent_idx == -1 and not parent_idx == None:
            if 'thigh' in jma_node.name and not parent_id_class.pelvis == None and not parent_id_class.thigh0 == None and not parent_id_class.thigh1 == None:
                parent_idx = parent_id_class.pelvis

            elif 'clavicle' in jma_node.name and not parent_id_class.spine1 == None and not parent_id_class.clavicle0 == None and not parent_id_class.clavicle1 == None:
                parent_idx = parent_id_class.spine1

            parent = JMA.nodes[parent_idx].name
            current_bone.parent = armature.data.edit_bones[parent]

        bone_distance = mesh_processing.get_bone_distance(JMA, idx, "JMA")

        matrix_translate = Matrix.Translation(first_frame[idx].translation)
        matrix_rotation = first_frame[idx].rotation.to_matrix().to_4x4()
        if JMS_A and not JMS_A_invalid and not JMS_B_invalid:
            for a_idx, jms_a_node in enumerate(JMS_A_nodes):
                if jma_node.name.lower() in jms_a_node.lower():
                    file_version = JMS_A.version
                    rest_position = JMS_A.transforms[0]
                    jms_node = rest_position[a_idx]
                    bone_distance = mesh_processing.get_bone_distance(JMS_A, a_idx, "JMS")

            for b_idx, jms_b_node in enumerate(JMS_B_nodes):
                if jma_node.name.lower() in jms_b_node.lower():
                    file_version = JMS_B.version
                    rest_position = JMS_B.transforms[0]
                    jms_node = rest_position[b_idx]
                    bone_distance = mesh_processing.get_bone_distance(JMS_B, b_idx, "JMS")

            matrix_translate = Matrix.Translation(jms_node.translation)
            matrix_rotation = jms_node.rotation.to_matrix().to_4x4()

        current_bone.tail[2] = bone_distance

        is_root = False
        if JMS_A and not JMS_A_invalid:
            if jma_node.name.lower() in JMS_A.nodes[0].name.lower():
                is_root = True

        if JMS_B and not JMS_B_invalid:
            if jma_node.name.lower() in JMS_B.nodes[0].name.lower():
                is_root = True

        transform_matrix = matrix_translate @ matrix_rotation
        if fix_rotations:
            if file_version < global_functions.get_version_matrix_check(file_type) and current_bone.parent and not is_root:
                transform_matrix = (current_bone.parent.matrix @ Matrix.Rotation(radians(90.0), 4, 'Z')) @ transform_matrix

            current_bone.matrix = transform_matrix @ Matrix.Rotation(radians(-90.0), 4, 'Z')

        else:
            if file_version < global_functions.get_version_matrix_check(file_type) and current_bone.parent and not is_root:
                transform_matrix = current_bone.parent.matrix @ transform_matrix

            current_bone.matrix = transform_matrix

    bpy.ops.object.mode_set(mode = 'OBJECT')

def set_parent_id_class(JMA, parent_id_class):
    for idx, jma_node in enumerate(JMA.nodes):
        if 'pelvis' in jma_node.name:
            parent_id_class.pelvis = idx

        if 'thigh' in jma_node.name:
            if parent_id_class.thigh0 == None:
                parent_id_class.thigh0 = idx

            else:
                parent_id_class.thigh1 = idx

        elif 'spine1' in jma_node.name:
            parent_id_class.spine1 = idx

        elif 'clavicle' in jma_node.name:
            if parent_id_class.clavicle0 == None:
                parent_id_class.clavicle0 = idx

            else:
                parent_id_class.clavicle1 = idx

def jms_file_check(JMS_A, JMS_B, JMA_nodes, report):
    JMS_A_nodes = []
    JMS_A_invalid = False
    JMS_B_nodes = []
    JMS_B_invalid = False
    if JMS_A and not JMS_B:
        for jms_node in JMS_A.nodes:
            JMS_A_nodes.append(jms_node.name)

        for jms_node_name in JMS_A_nodes:
            if not jms_node_name in JMA_nodes:
                JMS_A_invalid = True
                report({'WARNING'}, "Node '%s' from JMS skeleton not found in JMA skeleton." % jms_node_name)

        report({'WARNING'}, "No valid armature detected. Attempting to created one and the referenced JMS will be used for the rest position")

    elif JMS_A and JMS_B:
        for jms_node in JMS_A.nodes:
            JMS_A_nodes.append(jms_node.name)

        for jms_node in JMS_B.nodes:
            JMS_B_nodes.append(jms_node.name)

        jms_nodes = JMS_A_nodes + JMS_B_nodes

        for jms_node_name in jms_nodes:
            if not jms_node_name in JMA_nodes:
                JMS_B_invalid = True
                report({'WARNING'}, "Node '%s' from JMS skeleton not found in JMA skeleton." % jms_node_name)

        report({'WARNING'}, "No valid armature detected. Attempting to created one and the referenced JMS files will be used for the rest position")

    return JMS_A_nodes, JMS_B_nodes, JMS_A_invalid, JMS_B_invalid

def build_scene(context, JMA, JMS_A, JMS_B, filepath, game_version, fix_parents, fix_rotations, report):
    collection = context.collection
    scene = context.scene
    view_layer = context.view_layer
    armature = None
    object_list = list(scene.objects)

    collections = []
    layer_collections = list(context.view_layer.layer_collection.children)

    while len(layer_collections) > 0:
        collection_batch = layer_collections
        layer_collections = []
        for collection in collection_batch:
            collections.append(collection)
            for collection_child in collection.children:
                layer_collections.append(collection_child)

    scene_nodes = []
    jma_nodes = []
    for obj in object_list:
        if armature is None:
            if obj.type == 'ARMATURE' and mesh_processing.set_ignore(collections, obj) == False:
                is_armature_good = False
                if JMA.version == 16390:
                    if len(obj.data.bones) == JMA.node_count:
                        is_armature_good = True

                else:
                    exist_count = 0
                    armature_bone_list = list(obj.data.bones)
                    for node in armature_bone_list:
                        for jma_node in JMA.nodes:
                            if node.name == jma_node.name:
                                scene_nodes.append(node.name)
                                exist_count += 1

                    if exist_count == len(JMA.nodes):
                        is_armature_good = True

                if is_armature_good:
                    armature = obj
                    mesh_processing.select_object(context, armature)

    for jma_node in JMA.nodes:
        jma_nodes.append(jma_node.name)

    if len(scene_nodes) > 0:
        for jma_node in jma_nodes:
            if not jma_node in scene_nodes:
                report({'WARNING'}, "Node '%s' not found in an existing armature" % jma_node)

    if armature == None:
        parent_id_class = global_functions.ParentIDFix()
        JMS_A_nodes, JMS_B_nodes, JMS_A_invalid, JMS_B_invalid = jms_file_check(JMS_A, JMS_B, jma_nodes, report)
        if not JMA.broken_skeleton and JMA.version >= 16392:
            if JMA.version >= 16392:
                armdata = bpy.data.armatures.new('Armature')
                armature = bpy.data.objects.new('Armature', armdata)
                collection.objects.link(armature)
                mesh_processing.select_object(context, armature)
                if fix_parents:
                    if game_version == 'halo2' or game_version == 'halo3':
                        set_parent_id_class(JMA, parent_id_class)

                generate_jma_skeleton(JMS_A_nodes, JMS_A, JMS_A_invalid, JMS_B_nodes, JMS_B, JMS_B_invalid, JMA, armature, parent_id_class, fix_rotations, game_version)

            else:
                report({'ERROR'}, "No valid armature detected and not enough information to build valid skeleton due to version. Import will now be aborted")

                return {'CANCELLED'}

        else:
            if JMS_A:
                armdata = bpy.data.armatures.new('Armature')
                armature = bpy.data.objects.new('Armature', armdata)
                collection.objects.link(armature)
                mesh_processing.select_object(context, armature)

                generate_jms_skeleton(JMS_A_nodes, JMS_A, JMS_B_nodes, JMS_B, JMA, armature, fix_rotations, game_version)

            else:
                report({'ERROR'}, "No valid armature detected and animation graph is invalid. Import will now be aborted")

                return {'CANCELLED'}

    scene.frame_end = JMA.frame_count
    scene.render.fps = JMA.frame_rate

    animation_filename = bpy.path.basename(filepath).rsplit('.', 1)[0]
    action = bpy.data.actions.get(animation_filename)
    if action is None:
        action = bpy.data.actions.new(name=animation_filename)

    armature.animation_data_create()
    armature.animation_data.action = action

    bpy.ops.object.mode_set(mode = 'POSE')

    nodes = JMA.nodes
    if JMA.version == 16390:
        nodes = global_functions.sort_by_layer(list(armature.data.bones), armature)[0]

    for frame_idx, frame in enumerate(JMA.transforms):
        scene.frame_set(frame_idx + 1)

        if JMA.biped_controller_frame_type != JMAAsset.BipedControllerFrameType.DISABLE:
            controller_transform = JMA.biped_controller_transforms[frame_idx]

            if JMA.biped_controller_frame_type & JMAAsset.BipedControllerFrameType.DX:
                armature.location.x = controller_transform.translation[0]

            if JMA.biped_controller_frame_type & JMAAsset.BipedControllerFrameType.DY:
                armature.location.y = controller_transform.translation[1]

            if JMA.biped_controller_frame_type & JMAAsset.BipedControllerFrameType.DZ:
                armature.location.z = controller_transform.translation[2]

            if JMA.biped_controller_frame_type & JMAAsset.BipedControllerFrameType.DYAW:
                armature.rotation_euler.z = controller_transform.rotation.to_euler().z

            view_layer.update()
            armature.keyframe_insert('location')
            armature.keyframe_insert('rotation_euler')

        for idx, node in enumerate(nodes):
            pose_bone = armature.pose.bones[node.name]

            matrix_scale = Matrix.Scale(frame[idx].scale, 4, (1, 1, 1))
            matrix_rotation = frame[idx].rotation.to_matrix().to_4x4()
            transform_matrix = Matrix.Translation(frame[idx].translation) @ matrix_rotation @ matrix_scale

            if fix_rotations:
                if (JMA.version > 16390 or JMA.version < 16394) and pose_bone.parent:
                    transform_matrix = (pose_bone.parent.matrix @ Matrix.Rotation(radians(90.0), 4, 'Z')) @ transform_matrix

                rotated_matrix = transform_matrix @ Matrix.Rotation(radians(-90.0), 4, 'Z')
                pose_bone.matrix = rotated_matrix
                pose_bone.rotation_euler = rotated_matrix.to_euler()

            else:
                if JMA.version < 16394 and pose_bone.parent:
                    transform_matrix = pose_bone.parent.matrix @ transform_matrix

                pose_bone.matrix = transform_matrix
                pose_bone.rotation_euler = transform_matrix.to_euler()

            view_layer.update()

            pose_bone.keyframe_insert('location')
            pose_bone.keyframe_insert('rotation_euler')
            pose_bone.keyframe_insert('rotation_quaternion')
            pose_bone.keyframe_insert('scale')

    scene.frame_set(1)
    bpy.ops.object.mode_set(mode = 'OBJECT')

    report({'INFO'}, "Import completed successfully")

    return {'FINISHED'}
