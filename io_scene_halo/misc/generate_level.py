# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2023 Steven Garcia
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

import os
import bpy
import json
import random

from math import radians, degrees
from mathutils import Matrix, Vector, Euler
from ..global_ui.maze_ui import CharacterFlags
from ..misc.maze_gen.solve_maze import solve_maze
from ..global_functions.tag_format import TagAsset
from ..misc.maze_gen.generate_maze import generate_maze
from ..global_functions.mesh_processing import deselect_objects, select_object
from ..file_tag.h1.file_scenario.build_asset import build_asset as build_h1_scenario
from ..file_tag.h1.file_scenario.format import ScenarioAsset, EncounterFlags, GroupFlags, TeamEnum, ObjectFlags

DEBUG = False
ADDON_DIRECTORY = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def create_object(collection, parent, file_path):
    block = None
    attachment_points = []
    with bpy.data.libraries.load(file_path) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        if obj.name.startswith("attach"):
            attachment_points.append(obj)
        else:
            if not obj.name.startswith("render"):
                block = obj
                obj.parent = parent

        collection.objects.link(obj)

    attachment_points.sort(key=lambda x: x.name)
    return block, attachment_points

def attach_object(block, attachment_points, end_point, transform_matrix, scale_matrix):
    block_matrix = block.matrix_world
    local_matrix =  (attachment_points[0].matrix_world @ transform_matrix).inverted() @ block_matrix
    block.matrix_world = end_point.matrix_world @ local_matrix
    block.scale[1] = scale_matrix

def get_cell_settings(cells, cell_idx):
    rotation = 0.0
    scale = 1
    flip = False
    is_hallway = False

    previous_cell = cells[cell_idx - 1]
    current_cell = cells[cell_idx]
    next_cell = cells[cell_idx + 1]

    if previous_cell[0] == current_cell[0] and next_cell[0] == current_cell[0] or previous_cell[1] == current_cell[1] and next_cell[1] == current_cell[1]:
        is_hallway = True
        rotation = 0.0
        if previous_cell[0] == current_cell[0] and previous_cell[1] < current_cell[1]:
            flip = True
            scale = 1
            rotation = -90.0

        if previous_cell[0] == current_cell[0] and previous_cell[1] > current_cell[1]:
            flip = True
            scale = 1
            rotation = 90.0

    else:
        if previous_cell[0] < current_cell[0] and previous_cell[1] == current_cell[1] and next_cell[0] == current_cell[0] and next_cell[1] > current_cell[1]:
            # 1 0 1
            # 1 0 0
            # 1 1 1
            if DEBUG:
                print("A Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = 0.0
            scale = 1
            flip = True

        elif previous_cell[0] == current_cell[0] and previous_cell[1] > current_cell[1] and next_cell[0] > current_cell[0] and next_cell[1] == current_cell[1]:
            # 1 1 1
            # 1 0 0
            # 1 0 1
            if DEBUG:
                print("B Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = 90.0
            scale = 1
            flip = True

        elif previous_cell[0] > current_cell[0] and previous_cell[1] == current_cell[1] and next_cell[0] == current_cell[0] and next_cell[1] < current_cell[1]:
            # 1 1 1
            # 0 0 1
            # 1 0 1
            if DEBUG:
                print("C Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = 180.0
            scale = 1
            flip = True

        elif previous_cell[0] == current_cell[0] and previous_cell[1] < current_cell[1] and next_cell[0] < current_cell[0] and next_cell[1] == current_cell[1]:
            # 1 0 1
            # 0 0 1
            # 1 1 1
            if DEBUG:
                print("D Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = 270.0
            scale = 1
            flip = True

        elif previous_cell[0] < current_cell[0] and previous_cell[1] == current_cell[1] and next_cell[0] == current_cell[0] and next_cell[1] < current_cell[1]:
            # 1 0 1
            # 0 0 1
            # 1 1 1
            if DEBUG:
                print("E Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = 0.0
            scale = -1
            flip = True

        elif previous_cell[0] == current_cell[0] and previous_cell[1] < current_cell[1] and next_cell[0] > current_cell[0] and next_cell[1] == current_cell[1]:
            # 1 1 1
            # 0 0 1
            # 1 0 1
            if DEBUG:
                print("F Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = -90
            scale = -1


        elif previous_cell[0] > current_cell[0] and previous_cell[1] == current_cell[1] and next_cell[0] == current_cell[0] and next_cell[1] > current_cell[1]:
            # 1 1 1
            # 1 0 0
            # 1 0 1
            if DEBUG:
                print("H Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = -180
            scale = -1

        elif previous_cell[0] == current_cell[0] and previous_cell[1] > current_cell[1] and next_cell[0] < current_cell[0] and next_cell[1] == current_cell[1]:
            # 1 0 1
            # 1 0 0
            # 1 1 1
            if DEBUG:
                print("I Junction")
                print(previous_cell)
                print(current_cell)
                print(next_cell)

            rotation = -270
            scale = -1

        else:
            print("Failed to find a proper shape")
            if DEBUG:
                print(previous_cell)
                print(current_cell)
                print(next_cell)

    return rotation, scale, flip, is_hallway

def apply_transform(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')

def flip_normals(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')

def generate_player_starting_locations(SCENARIO, player_count, block, attachment_points, valid_polygons):
    is_valid = False
    if not len(valid_polygons) == 0:
        is_valid = True

    for player_idx in range(player_count):
        if is_valid:
            player_position = block.matrix_world @ random.choice(valid_polygons).center

        else:
            player_position = block.matrix_world @ Vector()

        attachment_position = attachment_points[-1].matrix_world.to_translation()
        vector_a = Vector((player_position[0], player_position[1]))
        vector = Vector((-1, 0))

        facing_angle = 0.0
        if not vector_a[0] == 0 and not vector_a[1] == 0:
            facing_angle = vector_a.angle_signed(vector)

        player_starting_location = SCENARIO.PlayerStartingLocation()
        player_starting_location.position = player_position / 100
        player_starting_location.facing = facing_angle
        player_starting_location.team_index = 0
        player_starting_location.bsp_index = 0
        player_starting_location.type_0 = 0
        player_starting_location.type_1 = 0
        player_starting_location.type_2 = 0
        player_starting_location.type_3 = 0

        SCENARIO.player_starting_locations.append(player_starting_location)

def generate_player_profiles(TAG, SCENARIO, mission_key, weapons_dic):
    mission_globals = mission_key["globals"]
    mission_scripts = mission_key["scripts"]

    for player_idx, player_starting_location in enumerate(SCENARIO.player_starting_locations):
        player_starting_profile = SCENARIO.PlayerStartingProfile()

        player_starting_profile.name = "player%s_starting_profile" % player_idx
        player_starting_profile.starting_health_damage = 1
        player_starting_profile.starting_shield_damage = 1

        primary_tag_group = "weap"
        primary_tag_path = ""
        player_starting_profile.primary_weapon_tag_ref = TAG.TagRef(primary_tag_group, primary_tag_path, len(primary_tag_path), upgrade_patches=TAG.upgrade_patches)

        player_starting_profile.primary_rounds_loaded = 0
        player_starting_profile.primary_rounds_total = 0

        secondary_tag_group = "weap"
        secondary_tag_path = ""
        player_starting_profile.secondary_weapon_tag_ref = TAG.TagRef(secondary_tag_group, secondary_tag_path, len(secondary_tag_path), upgrade_patches=TAG.upgrade_patches)

        player_starting_profile.secondary_rounds_loaded = 0
        player_starting_profile.secondary_rounds_total = 0
        player_starting_profile.starting_fragmentation_grenades_count = 0
        player_starting_profile.starting_plasma_grenade_count = 0
        player_starting_profile.starting_custom_2_grenade_count = 0
        player_starting_profile.starting_custom_3_grenade_count = 0

    loadout_count = 24
    loadout_id_key = mission_globals["loadout_id"] = {}
    loadout_id_key["type"] = "short"
    loadout_id_key["value"] = "0"

    loadout_key = mission_scripts["(get_loadout (unit player))"] = {}

    loadout_key["type"] = "static"
    loadout_key["object"] = "void"
    loadout_body = loadout_key["body"] = ["(set loadout_id (random_range 0 %s))" % (loadout_count - 1)]

    cond_list = []
    for loadout_idx in range(loadout_count):
        primary = random.choice(weapons_dic["weapons"])
        secondary = random.choice(weapons_dic["weapons"])
        while primary["name"] == secondary["name"]:
            secondary = random.choice(weapons_dic["weapons"])

        player_starting_profile = SCENARIO.PlayerStartingProfile()

        player_starting_profile.name = "loadout_%s" % loadout_idx
        player_starting_profile.starting_health_damage = 0
        player_starting_profile.starting_shield_damage = 0

        primary_tag_group = "weap"
        primary_tag_path = primary["path"]
        player_starting_profile.primary_weapon_tag_ref = TAG.TagRef(primary_tag_group, primary_tag_path, len(primary_tag_path), upgrade_patches=TAG.upgrade_patches)

        player_starting_profile.primary_rounds_loaded = primary["rounds_loaded"]
        player_starting_profile.primary_rounds_total = primary["rounds_total"]

        secondary_tag_group = "weap"
        secondary_tag_path = secondary["path"]
        player_starting_profile.secondary_weapon_tag_ref = TAG.TagRef(secondary_tag_group, secondary_tag_path, len(secondary_tag_path), upgrade_patches=TAG.upgrade_patches)

        player_starting_profile.secondary_rounds_loaded = secondary["rounds_loaded"]
        player_starting_profile.secondary_rounds_total = secondary["rounds_total"]
        player_starting_profile.starting_fragmentation_grenades_count = 2
        player_starting_profile.starting_plasma_grenade_count = 0
        player_starting_profile.starting_custom_2_grenade_count = 0
        player_starting_profile.starting_custom_3_grenade_count = 0

        SCENARIO.player_starting_profiles.append(player_starting_profile)
        cond_list.append("((= loadout_id %s)(player_add_equipment player loadout_%s 0))" % (loadout_idx, loadout_idx))

    loadout_body.append(cond_list)

def find_center(block):
    local_bbox_center = 0.125 * sum((Vector(b) for b in block.bound_box), Vector())
    global_bbox_center = block.matrix_world @ local_bbox_center

    return global_bbox_center

def generate_trigger_volume(SCENARIO, trigger_name, block):
    trigger_volume = SCENARIO.TriggerVolume()
    trigger_volume.name = trigger_name
    trigger_volume.forward = Vector((1.0, 0.0, 0.0))
    trigger_volume.up = Vector((0.0, 0.0, 1.0))
    trigger_volume.position = (find_center(block) - (block.dimensions / 2)) / 100
    trigger_volume.extents = block.dimensions / 100

    SCENARIO.trigger_volumes.append(trigger_volume)

def generate_actor_palette(TAG, SCENARIO, actor_path):
    actor = TAG.TagRef("actv", actor_path, len(actor_path), upgrade_patches=TAG.upgrade_patches)

    SCENARIO.actor_palette.append(actor)

def unduplicate_name(material_name):
    undupped_name = material_name
    if "." in material_name:
        split_mat_name = material_name.rsplit(".", 1)
        if len(split_mat_name[1]) >= 3 and split_mat_name[1].isnumeric():
            undupped_name = split_mat_name[0]

    return undupped_name

def generate_encounters(TAG, SCENARIO, block, attachment_points, mission_body, valid_polygons, characters_dic, active_teams):
    ai_count = 3

    if len(valid_polygons) > 0:
        for team in active_teams:
            team_id = TeamEnum[team]
            actor_dic = characters_dic[team]

            encounter = SCENARIO.Encounter()

            encounter_name = "encounter_%s_%s" % (block.name, team_id.name)
            mission_body.append("(ai_place %s)" % encounter_name)

            encounter_flags = EncounterFlags.not_intially_created.value
            if team_id == TeamEnum.sentinel:
                encounter_flags += EncounterFlags._3d_firing_positions.value

            encounter.name = encounter_name
            encounter.flags = encounter_flags
            encounter.team_index = team_id.value
            encounter.search_behavior = 0
            encounter.manual_bsp_index = 0
            encounter.respawn_delay = (0.0, 0.0)
            encounter.squads = []
            encounter.platoons = []
            encounter.firing_positions = []
            encounter.player_starting_locations = []
            for squad_idx in range(1):
                squad = SCENARIO.Squad()

                squad.name = "squad_%s" % squad_idx
                squad.actor_type = -1
                squad.platoon = -1
                squad.initial_state = 0
                squad.return_state = 0
                squad.flags = 0
                squad.unique_leader_type = 0
                squad.maneuver_to_squad = -1
                squad.squad_delay_time = 0
                squad.attacking = GroupFlags.a.value
                squad.attacking_search = GroupFlags.a.value
                squad.attacking_guard = GroupFlags.a.value
                squad.defending = 0
                squad.defending_search = 0
                squad.defending_guard = 0
                squad.pursuing = 0
                squad.normal_diff_count = ai_count
                squad.insane_diff_count = ai_count
                squad.major_upgrade = 0
                squad.respawn_min_actors = 0
                squad.respawn_max_actors = 0
                squad.respawn_total = 0
                squad.respawn_delay = (0.0, 0.0)
                squad.move_positions = []
                squad.starting_locations = []
                for location_idx in range(ai_count):
                    starting_location = SCENARIO.StartingLocation()

                    valid_actors = []
                    polygon_count = len(valid_polygons)
                    counter = 0
                    while len(valid_actors) == 0 and counter < polygon_count:
                        selected_polygon = random.choice(valid_polygons)
                        poly_index = selected_polygon.index
                        character_value = block.data.attributes["Halo Valid Characters"].data[poly_index].value

                        character_flags = CharacterFlags(character_value)

                        for actor in actor_dic:
                            actor_flag = CharacterFlags[actor["name"]]
                            if actor_flag in character_flags:
                                valid_actors.append(actor)

                        counter += 1

                    random_actor = random.choice(valid_actors)
                    random_variant = random.choice(random_actor["variants"])

                    position = block.matrix_world @ selected_polygon.center

                    actor_index = -1
                    for actor_idx, actor in enumerate(SCENARIO.actor_palette):
                        if random_variant == actor.name:
                            actor_index = actor_idx
                            break

                    if actor_index == -1:
                        generate_actor_palette(TAG, SCENARIO, random_variant)
                        actor_index = len(SCENARIO.actor_palette) - 1

                    if team_id == TeamEnum.sentinel:
                        position += Vector((random_actor["position_additive"][0], random_actor["position_additive"][1], random_actor["position_additive"][2]))

                    starting_location.position = position / 100
                    starting_location.facing = 0.0
                    starting_location.sequence_id = 0
                    starting_location.flags = 0
                    starting_location.return_state = 0
                    starting_location.initial_state = 0
                    starting_location.actor_type = actor_index
                    starting_location.command_list = -1

                    squad.starting_locations.append(starting_location)

                squad.move_positions_tag_block = TAG.TagBlock()
                squad.starting_locations_tag_block = TAG.TagBlock(len(squad.starting_locations))

                encounter.squads.append(squad)

            for squad_idx in range(64):
                firing_position = SCENARIO.FiringPosition()

                selected_polygon = random.choice(valid_polygons)
                poly_index = selected_polygon.index
                position = block.matrix_world @ selected_polygon.center

                if team_id == TeamEnum.sentinel:
                    ray_direction = Vector((0, 0, 1))
                    ray_origin =  selected_polygon.center + Vector((0.0, 0.0, 0.1))
                    success, location, normal, poly_index = block.ray_cast(ray_origin, ray_direction)

                    ceiling_height = (location - ray_origin).length

                    height_additive = random.uniform(0, ceiling_height)
                    if height_additive > (ceiling_height - 5):
                        height_additive = height_additive - 5

                    position = position + Vector((0.0, 0.0, height_additive))

                firing_position.position = position / 100
                firing_position.group_index = 0

                encounter.firing_positions.append(firing_position)

            encounter.squads_tag_block = TAG.TagBlock(len(encounter.squads))
            encounter.platoons_tag_block = TAG.TagBlock()
            encounter.firing_positions_tag_block = TAG.TagBlock(len(encounter.firing_positions))
            encounter.player_starting_locations_tag_block = TAG.TagBlock()

            SCENARIO.encounters.append(encounter)

def process_dic_element(script_function, script_name):
    dic_string = ""
    if script_function["type"] == "static":
        dic_string += "(script %s %s %s\r\n" % (script_function["type"], script_function["object"], script_name)
    else:
        dic_string += "(script %s %s\r\n" % (script_function["type"], script_name)

    for body_element in script_function["body"]:
        if type(body_element) == list:
            dic_string += "\t(cond\r\n"
            for condition in body_element:
                dic_string += "\t\t%s\r\n" % condition
            dic_string += "\t)\r\n"
        else:
            dic_string += "\t%s\r\n" % body_element

    dic_string += ")\r\n\r\n"

    return dic_string

def generate_string_from_dic(script):
    dic_string = ""
    script_globals = script["globals"]
    for global_name in script_globals:
        script_global = script_globals[global_name]
        dic_string += "(global %s %s %s)\r\n" % (script_global["type"], global_name, script_global["value"])

    dic_string += "\r\n"

    script_functions = script["scripts"]
    for script_name in script_functions:
        if script_functions[script_name]["type"] == "dormant":
            dic_string += process_dic_element(script_functions[script_name], script_name)

    for script_name in script_functions:
        if not script_functions[script_name]["type"] == "startup" and not script_functions[script_name]["type"] == "dormant":
            dic_string += process_dic_element(script_functions[script_name], script_name)

    for script_name in script_functions:
        if script_functions[script_name]["type"] == "startup":
            dic_string += process_dic_element(script_functions[script_name], script_name)

    return dic_string

def generate_source_files(TAG, SCENARIO, output_path, script_dic):
    hek_root, local_path = output_path.split("\\tags\\")
    data_directory = os.path.join(hek_root, "data")
    script_directory = os.path.join(data_directory, local_path, "scripts")
    if not os.path.exists(script_directory):
        os.makedirs(script_directory)

    for script_name in script_dic:
        ascii_text = generate_string_from_dic(script_dic[script_name])
        if script_name == "global_scripts":
            with open(os.path.join(data_directory, "global_scripts.hsc"), 'wb') as f:
                f.write(ascii_text.encode('ascii'))
        else:
            with open(os.path.join(script_directory, "%s.hsc" % script_name), 'wb') as f:
                f.write(ascii_text.encode('ascii'))

        source_file = SCENARIO.SourceFile()
        source_file.name = script_name
        source_file.source = ascii_text
        source_file.source_tag_data = TAG.RawData(len(source_file.source) + 1)

        SCENARIO.source_files.append(source_file)

def generate_structure_bsps(TAG, SCENARIO):
    sbsp_tag_group = "sbsp"
    sbsp_tag_path = r"levels\test\maze_gen\maze_gen"

    structure_bsp = TAG.TagRef(sbsp_tag_group, sbsp_tag_path, len(sbsp_tag_path), upgrade_patches=TAG.upgrade_patches)

    SCENARIO.structure_bsps.append(structure_bsp)

def initialize_scenario():
    TAG = TagAsset()
    SCENARIO = ScenarioAsset()
    TAG.is_legacy = False

    SCENARIO.header = TAG.Header()
    SCENARIO.header.unk1 = 0
    SCENARIO.header.flags = 0
    SCENARIO.header.type = 0
    SCENARIO.header.name = ""
    SCENARIO.header.tag_group = "scnr"
    SCENARIO.header.checksum = -1
    SCENARIO.header.data_offset = 64
    SCENARIO.header.data_length = 0
    SCENARIO.header.unk2 = 0
    SCENARIO.header.version = 2
    SCENARIO.header.destination = 0
    SCENARIO.header.plugin_handle = -1
    SCENARIO.header.engine_tag = "blam"

    SCENARIO.dont_use_tag_ref = TAG.TagRef()
    SCENARIO.wont_use_tag_ref = TAG.TagRef()
    SCENARIO.cant_use_tag_ref = TAG.TagRef()
    SCENARIO.skies_tag_block = TAG.TagBlock()
    SCENARIO.child_scenarios_tag_block = TAG.TagBlock()
    SCENARIO.predicted_resources_tag_block = TAG.TagBlock()
    SCENARIO.functions_tag_block = TAG.TagBlock()
    SCENARIO.editor_scenario_data = TAG.RawData()
    SCENARIO.comments_tag_block = TAG.TagBlock()
    SCENARIO.scavenger_hunt_objects_tag_block = TAG.TagBlock()
    SCENARIO.object_names_tag_block = TAG.TagBlock()
    SCENARIO.scenery_tag_block = TAG.TagBlock()
    SCENARIO.scenery_palette_tag_block = TAG.TagBlock()
    SCENARIO.bipeds_tag_block = TAG.TagBlock()
    SCENARIO.biped_palette_tag_block = TAG.TagBlock()
    SCENARIO.vehicles_tag_block = TAG.TagBlock()
    SCENARIO.vehicle_palette_tag_block = TAG.TagBlock()
    SCENARIO.equipment_tag_block = TAG.TagBlock()
    SCENARIO.equipment_palette_tag_block = TAG.TagBlock()
    SCENARIO.weapons_tag_block = TAG.TagBlock()
    SCENARIO.weapon_palette_tag_block = TAG.TagBlock()
    SCENARIO.device_groups_tag_block = TAG.TagBlock()
    SCENARIO.machines_tag_block = TAG.TagBlock()
    SCENARIO.machine_palette_tag_block = TAG.TagBlock()
    SCENARIO.controls_tag_block = TAG.TagBlock()
    SCENARIO.control_palette_tag_block = TAG.TagBlock()
    SCENARIO.light_fixtures_tag_block = TAG.TagBlock()
    SCENARIO.light_fixtures_palette_tag_block = TAG.TagBlock()
    SCENARIO.sound_scenery_tag_block = TAG.TagBlock()
    SCENARIO.sound_scenery_palette_tag_block = TAG.TagBlock()
    SCENARIO.player_starting_profile_tag_block = TAG.TagBlock()
    SCENARIO.player_starting_locations_tag_block = TAG.TagBlock()
    SCENARIO.trigger_volumes_tag_block = TAG.TagBlock()
    SCENARIO.recorded_animations_tag_block = TAG.TagBlock()
    SCENARIO.netgame_flags_tag_block = TAG.TagBlock()
    SCENARIO.netgame_equipment_tag_block = TAG.TagBlock()
    SCENARIO.starting_equipment_tag_block = TAG.TagBlock()
    SCENARIO.bsp_switch_trigger_volumes_tag_block = TAG.TagBlock()
    SCENARIO.decals_tag_block = TAG.TagBlock()
    SCENARIO.decal_palette_tag_block = TAG.TagBlock()
    SCENARIO.detail_object_collection_palette_tag_block = TAG.TagBlock()
    SCENARIO.actor_palette_tag_block = TAG.TagBlock()
    SCENARIO.encounters_tag_block = TAG.TagBlock()
    SCENARIO.command_lists_tag_block = TAG.TagBlock()
    SCENARIO.ai_animation_references_tag_block = TAG.TagBlock()
    SCENARIO.ai_script_references_tag_block = TAG.TagBlock()
    SCENARIO.ai_recording_references_tag_block = TAG.TagBlock()
    SCENARIO.ai_conversations_tag_block = TAG.TagBlock()
    SCENARIO.script_syntax_data_tag_data = TAG.RawData()
    SCENARIO.script_string_data_tag_data = TAG.RawData()
    SCENARIO.scripts_tag_block = TAG.TagBlock()
    SCENARIO.globals_tag_block = TAG.TagBlock()
    SCENARIO.references_tag_block = TAG.TagBlock()
    SCENARIO.source_files_tag_block = TAG.TagBlock()
    SCENARIO.cutscene_flags_tag_block = TAG.TagBlock()
    SCENARIO.cutscene_camera_points_tag_block = TAG.TagBlock()
    SCENARIO.cutscene_titles_tag_block = TAG.TagBlock()
    SCENARIO.custom_object_names_tag_ref = TAG.TagRef()
    SCENARIO.chapter_title_text_tag_ref = TAG.TagRef()
    SCENARIO.hud_messages_tag_ref = TAG.TagRef()
    SCENARIO.structure_bsps_tag_block = TAG.TagBlock()

    SCENARIO.skies = []
    SCENARIO.child_scenarios = []
    SCENARIO.predicted_resources = []
    SCENARIO.functions = []
    SCENARIO.editor_scenario_data = bytes()
    SCENARIO.comments = []
    SCENARIO.scavenger_hunt_objects = []
    SCENARIO.object_names = []
    SCENARIO.scenery = []
    SCENARIO.scenery_palette = []
    SCENARIO.bipeds = []
    SCENARIO.biped_palette = []
    SCENARIO.vehicles = []
    SCENARIO.vehicle_palette = []
    SCENARIO.equipment = []
    SCENARIO.equipment_palette = []
    SCENARIO.weapons = []
    SCENARIO.weapon_palette = []
    SCENARIO.device_groups = []
    SCENARIO.device_machines = []
    SCENARIO.device_machine_palette = []
    SCENARIO.device_controls = []
    SCENARIO.device_control_palette = []
    SCENARIO.device_light_fixtures = []
    SCENARIO.device_light_fixtures_palette = []
    SCENARIO.sound_scenery = []
    SCENARIO.sound_scenery_palette = []
    SCENARIO.player_starting_profiles = []
    SCENARIO.player_starting_locations = []
    SCENARIO.trigger_volumes = []
    SCENARIO.recorded_animations = []
    SCENARIO.netgame_flags = []
    SCENARIO.netgame_equipment = []
    SCENARIO.starting_equipment = []
    SCENARIO.bsp_switch_trigger_volumes = []
    SCENARIO.decals = []
    SCENARIO.decal_palette = []
    SCENARIO.detail_object_collection_palette  = []
    SCENARIO.actor_palette = []
    SCENARIO.encounters = []
    SCENARIO.command_lists = []
    SCENARIO.ai_animation_references = []
    SCENARIO.ai_script_references = []
    SCENARIO.ai_recording_references = []
    SCENARIO.ai_conversations = []
    SCENARIO.script_syntax_data = bytes()
    SCENARIO.script_string_data = bytes()
    SCENARIO.scripts = []
    SCENARIO.script_globals = []
    SCENARIO.references = []
    SCENARIO.source_files = []
    SCENARIO.cutscene_flags = []
    SCENARIO.cutscene_camera_points = []
    SCENARIO.cutscene_titles = []
    SCENARIO.structure_bsps = []

    return TAG, SCENARIO

def create_level_root(collection, context):
    level_mesh = bpy.data.meshes.new("frame_root")
    level_root = bpy.data.objects.new("frame_root", level_mesh)
    collection.objects.link(level_root)
    level_root.select_set(True)
    context.view_layer.objects.active = level_root
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.object.mode_set(mode='OBJECT')
    level_root.select_set(False)
    context.view_layer.objects.active = None

    return level_root

def initialize_tag_blocks(TAG, SCENARIO):
    SCENARIO.dont_use_tag_ref = TAG.TagRef("sbsp")
    SCENARIO.wont_use_tag_ref = TAG.TagRef("sbsp")
    SCENARIO.cant_use_tag_ref = TAG.TagRef("sky ")
    SCENARIO.skies_tag_block = TAG.TagBlock(len(SCENARIO.skies))
    SCENARIO.scenario_type = 0
    SCENARIO.scenario_flags = 0
    SCENARIO.child_scenarios_tag_block = TAG.TagBlock(len(SCENARIO.child_scenarios))
    SCENARIO.local_north = 0.0
    SCENARIO.predicted_resources_tag_block = TAG.TagBlock(len(SCENARIO.predicted_resources))
    SCENARIO.functions_tag_block = TAG.TagBlock(len(SCENARIO.functions))
    SCENARIO.editor_scenario_data = TAG.RawData()
    SCENARIO.comments_tag_block = TAG.TagBlock(len(SCENARIO.comments))
    SCENARIO.scavenger_hunt_objects_tag_block = TAG.TagBlock(len(SCENARIO.scavenger_hunt_objects))
    SCENARIO.object_names_tag_block = TAG.TagBlock(len(SCENARIO.object_names))
    SCENARIO.scenery_tag_block = TAG.TagBlock(len(SCENARIO.scenery))
    SCENARIO.scenery_palette_tag_block = TAG.TagBlock(len(SCENARIO.scenery_palette))
    SCENARIO.bipeds_tag_block = TAG.TagBlock(len(SCENARIO.bipeds))
    SCENARIO.biped_palette_tag_block = TAG.TagBlock(len(SCENARIO.biped_palette))
    SCENARIO.vehicles_tag_block = TAG.TagBlock(len(SCENARIO.vehicles))
    SCENARIO.vehicle_palette_tag_block = TAG.TagBlock(len(SCENARIO.vehicle_palette))
    SCENARIO.equipment_tag_block = TAG.TagBlock(len(SCENARIO.equipment))
    SCENARIO.equipment_palette_tag_block = TAG.TagBlock(len(SCENARIO.equipment_palette))
    SCENARIO.weapons_tag_block = TAG.TagBlock(len(SCENARIO.weapons))
    SCENARIO.weapon_palette_tag_block = TAG.TagBlock(len(SCENARIO.weapon_palette))
    SCENARIO.device_groups_tag_block = TAG.TagBlock(len(SCENARIO.device_groups))
    SCENARIO.machines_tag_block = TAG.TagBlock(len(SCENARIO.device_machines))
    SCENARIO.machine_palette_tag_block = TAG.TagBlock(len(SCENARIO.device_machine_palette))
    SCENARIO.controls_tag_block = TAG.TagBlock(len(SCENARIO.device_controls))
    SCENARIO.control_palette_tag_block = TAG.TagBlock(len(SCENARIO.device_control_palette))
    SCENARIO.light_fixtures_tag_block = TAG.TagBlock(len(SCENARIO.device_light_fixtures))
    SCENARIO.light_fixtures_palette_tag_block = TAG.TagBlock(len(SCENARIO.device_light_fixtures_palette))
    SCENARIO.sound_scenery_tag_block = TAG.TagBlock(len(SCENARIO.sound_scenery))
    SCENARIO.sound_scenery_palette_tag_block = TAG.TagBlock(len(SCENARIO.sound_scenery_palette))
    SCENARIO.player_starting_profile_tag_block = TAG.TagBlock(len(SCENARIO.player_starting_profiles))
    SCENARIO.player_starting_locations_tag_block = TAG.TagBlock(len(SCENARIO.player_starting_locations))
    SCENARIO.trigger_volumes_tag_block = TAG.TagBlock(len(SCENARIO.trigger_volumes))
    SCENARIO.recorded_animations_tag_block = TAG.TagBlock(len(SCENARIO.recorded_animations))
    SCENARIO.netgame_flags_tag_block = TAG.TagBlock(len(SCENARIO.netgame_flags))
    SCENARIO.netgame_equipment_tag_block = TAG.TagBlock(len(SCENARIO.netgame_equipment))
    SCENARIO.starting_equipment_tag_block = TAG.TagBlock(len(SCENARIO.starting_equipment))
    SCENARIO.bsp_switch_trigger_volumes_tag_block = TAG.TagBlock(len(SCENARIO.bsp_switch_trigger_volumes))
    SCENARIO.decals_tag_block = TAG.TagBlock(len(SCENARIO.decals))
    SCENARIO.decal_palette_tag_block = TAG.TagBlock(len(SCENARIO.decal_palette))
    SCENARIO.detail_object_collection_palette_tag_block = TAG.TagBlock(len(SCENARIO.detail_object_collection_palette))
    SCENARIO.actor_palette_tag_block = TAG.TagBlock(len(SCENARIO.actor_palette))
    SCENARIO.encounters_tag_block = TAG.TagBlock(len(SCENARIO.encounters))
    SCENARIO.command_lists_tag_block = TAG.TagBlock(len(SCENARIO.command_lists))
    SCENARIO.ai_animation_references_tag_block = TAG.TagBlock(len(SCENARIO.ai_animation_references))
    SCENARIO.ai_script_references_tag_block = TAG.TagBlock(len(SCENARIO.ai_script_references))
    SCENARIO.ai_recording_references_tag_block = TAG.TagBlock(len(SCENARIO.ai_recording_references))
    SCENARIO.ai_conversations_tag_block = TAG.TagBlock(len(SCENARIO.ai_conversations))
    SCENARIO.script_syntax_data_tag_data = TAG.RawData()
    SCENARIO.script_string_data_tag_data = TAG.RawData()
    SCENARIO.scripts_tag_block = TAG.TagBlock(len(SCENARIO.scripts))
    SCENARIO.globals_tag_block = TAG.TagBlock(len(SCENARIO.globals))
    SCENARIO.references_tag_block = TAG.TagBlock(len(SCENARIO.references))
    SCENARIO.source_files_tag_block = TAG.TagBlock(len(SCENARIO.source_files))
    SCENARIO.cutscene_flags_tag_block = TAG.TagBlock(len(SCENARIO.cutscene_flags))
    SCENARIO.cutscene_camera_points_tag_block = TAG.TagBlock(len(SCENARIO.cutscene_camera_points))
    SCENARIO.cutscene_titles_tag_block = TAG.TagBlock(len(SCENARIO.cutscene_titles))
    SCENARIO.custom_object_names_tag_ref = TAG.TagRef("ustr")
    SCENARIO.chapter_title_text_tag_ref = TAG.TagRef("ustr")
    SCENARIO.hud_messages_tag_ref = TAG.TagRef("hmt ")
    SCENARIO.structure_bsps_tag_block = TAG.TagBlock(len(SCENARIO.structure_bsps))

def grab_block(blocks_dic, game_title, level_theme, block_type):
    block_name = random.choice(blocks_dic[level_theme][block_type])["name"]
    absolute_path = os.path.join(ADDON_DIRECTORY, "misc\\maze_gen\\level_assets\\%s\\blocks\\%s\\%s.blend" % (game_title, level_theme, block_name))

    return absolute_path

def append_keys(main_dic, json_path):
    item_stream = open(json_path, "r")
    item_dic = json.load(item_stream)

    for item_key in item_dic:
        target_key = main_dic.get(item_key)
        donor_key = item_dic.get(item_key)
        if type(donor_key) is dict:
            sub_dic_key = main_dic[item_key] = {}
            for sub_key in donor_key:
                target_key = sub_dic_key[sub_key] = []
                for key in donor_key[sub_key]:
                    target_key.append(key)

        else:
            if target_key is None:
                target_key = main_dic[item_key] = []

            for key in item_dic[item_key]:
                target_key.append(key)

def generate_camera_armature(context):
    armdata = bpy.data.armatures.new('Armature')
    armature = bpy.data.objects.new('Armature', armdata)
    context.collection.objects.link(armature)

    select_object(context, armature)

    bpy.ops.object.mode_set(mode = 'EDIT')
    current_bone = armature.data.edit_bones.new("frame_root")
    current_bone.tail[2] = 10
    current_bone.matrix = Matrix.Identity(4)

    bpy.ops.object.mode_set(mode = 'POSE')
    armature.pose.bones[0].rotation_mode = 'XYZ'

    bpy.ops.object.mode_set(mode = 'OBJECT')

    return armature

def generate_camera_zoom(context, armature, shot_start, shot_end, distance, zoom_in, SCENARIO):
    shot_timing = (shot_start, shot_start + (shot_end - 1))
    bpy.ops.object.mode_set(mode = 'POSE')
    pose_bone = armature.pose.bones["frame_root"]

    p_loc = SCENARIO.player_starting_locations[0].position
    facing_z = SCENARIO.player_starting_locations[0].facing
    player_matrix = Matrix.Translation(p_loc * 100)
    p_radius = 30
    p_height = 55
    for keyframe_idx, frame_idx in enumerate(shot_timing):
        if zoom_in:
            if keyframe_idx == 0:
                cam_pos = p_radius + distance
            else:
                cam_pos = p_radius
        else:
            if not keyframe_idx == 0:
                cam_pos = p_radius + distance
            else:
                cam_pos = p_radius

        local_pos = Vector((cam_pos, 0, p_height))
        facing_direction = Euler((0.0, 0.0, facing_z), 'XYZ')
        local_pos.rotate(facing_direction)

        transform_matrix = player_matrix @ (Matrix.Translation(local_pos) @ Matrix.Rotation(facing_z, 4, 'Z'))
        loc, rot, sca = transform_matrix.decompose()

        rot_mat = rot.to_matrix() @ Euler((0.0, 0.0, radians(180.0))).to_matrix()
        transform_matrix = Matrix.LocRotScale(loc, rot_mat, sca)

        context.scene.frame_set(frame_idx)
        pose_bone.matrix = transform_matrix
        context.view_layer.update()
        pose_bone.keyframe_insert(data_path='location', group=pose_bone.name)
        pose_bone.keyframe_insert(data_path='rotation_euler', group=pose_bone.name)

    bpy.ops.object.mode_set(mode = 'OBJECT')
    context.scene.frame_set(context.scene.frame_current + 1)

def generate_camera_arc(context, armature, shot_start, shot_end, interpolation, angle, SCENARIO):
    interpolation += 1
    bpy.ops.object.mode_set(mode = 'POSE')
    pose_bone = armature.pose.bones["frame_root"]

    p_loc = SCENARIO.player_starting_locations[0].position
    facing_z = degrees(SCENARIO.player_starting_locations[0].facing)
    player_matrix = Matrix.Translation(p_loc * 100)

    shot_timings = [round(shot_end + x * (1 - shot_end) / (interpolation - 1)) for x in range(interpolation)]
    shot_timings.reverse()

    for shot_idx, frame_idx in enumerate(shot_timings):
        local_pos = Vector((80, 0, 55))

        facing_direction = Euler((0.0, 0.0, radians(facing_z + (shot_idx * angle))), 'XYZ')
        local_pos.rotate(facing_direction)

        transform_matrix = player_matrix @ Matrix.Translation(local_pos)

        context.scene.frame_set(shot_start + (frame_idx - 1))
        pose_bone.location = transform_matrix.to_translation()
        rad_rot = radians(angle)
        if shot_idx == 0:
            rad_rot = 0

        pose_bone.rotation_euler[2] += rad_rot
        context.view_layer.update()
        pose_bone.keyframe_insert(data_path='location', group=pose_bone.name)
        pose_bone.keyframe_insert(data_path='rotation_euler', group=pose_bone.name)

    bpy.ops.object.mode_set(mode = 'OBJECT')
    context.scene.frame_set(context.scene.frame_current + 1)

def generate_intro_cutscene(context, SCENARIO, TAG):
    tag_path = r"cinematics\effects\teleportation\teleportation"
    machine = TAG.TagRef("mach", tag_path, len(tag_path), upgrade_patches=TAG.upgrade_patches)

    SCENARIO.device_machine_palette.append(machine)

    for player_idx, player_starting_location in enumerate(SCENARIO.player_starting_locations):
        object_name = SCENARIO.ObjectName()

        object_name.name = "tele_%s" % player_idx
        object_name.object_type = -1
        object_name.placement_index = -1

        SCENARIO.object_names.append(object_name)

        device_machine = SCENARIO.DeviceMachine()
        device_machine.type_index = 0
        device_machine.name_index = player_idx
        device_machine.placement_flags = 0
        device_machine.desired_permutation = 0
        device_machine.position = player_starting_location.position
        device_machine.rotation = Euler()
        device_machine.appearance_player_index = 0
        device_machine.power_group_index = -1
        device_machine.position_group_index = -1
        device_machine.flags_0 = 0
        device_machine.flags_1 = 0

        SCENARIO.device_machines.append(device_machine)

    deselect_objects(context)
    context.scene.frame_start = 1
    context.scene.frame_set(1)

    armature = generate_camera_armature(context)

    bpy.ops.object.mode_set(mode = 'POSE')
    pose_bone = armature.pose.bones["frame_root"]

    p_loc = SCENARIO.player_starting_locations[0].position
    facing_z = degrees(SCENARIO.player_starting_locations[0].facing)
    player_matrix = Matrix.Translation(p_loc * 100)

    local_pos = Vector((80, 0, 55))

    facing_direction = Euler((0.0, 0.0, radians(facing_z)), 'XYZ')
    local_pos.rotate(facing_direction)

    transform_matrix = player_matrix @ Matrix.Translation(local_pos)

    pose_bone.matrix = transform_matrix
    pose_bone.rotation_euler[2] = radians(180 + facing_z)
    context.view_layer.update()

    #generate_camera_zoom(context, armature, context.scene.frame_current, 150, 50, False, SCENARIO)
    generate_camera_arc(context, armature, context.scene.frame_current, 100, 24, 15, SCENARIO)
    generate_camera_arc(context, armature, context.scene.frame_current, 100, 24, -15, SCENARIO)
    #generate_camera_zoom(context, armature, context.scene.frame_current, 150, 50, True, SCENARIO)
    frames = []
    action = armature.animation_data.action
    for fcu in action.fcurves:
        for keyframe in fcu.keyframe_points:
            frames.append(keyframe.co[0])

    context.scene.frame_end = int(max(frames))

def generate_global_scripts(script_dic, player_count):
    gs_key = script_dic["global_scripts"] = {}
    gs_globals = gs_key["globals"] = {}
    gs_scripts = gs_key["scripts"] = {}

    global_dialog_on_key = gs_globals["global_dialog_on"] = {}
    global_dialog_on_key["type"] = "boolean"
    global_dialog_on_key["value"] = "false"

    global_dialog_on_key = gs_globals["global_music_on"] = {}
    global_dialog_on_key["type"] = "boolean"
    global_dialog_on_key["value"] = "false"

    global_dialog_on_key = gs_globals["global_delay_music"] = {}
    global_dialog_on_key["type"] = "long"
    global_dialog_on_key["value"] = "(* 30 300)"

    global_dialog_on_key = gs_globals["global_delay_music_alt"] = {}
    global_dialog_on_key["type"] = "long"
    global_dialog_on_key["value"] = "(* 30 300)"

    for player_idx in range(player_count):
        player_key = gs_scripts["player%s" % player_idx] = {}

        player_key["type"] = "static"
        player_key["object"] = "unit"
        player_key["body"] = ["(unit (list_get (players) %s))" % player_idx]

    player_count_key = gs_scripts["player_count"] = {}

    player_count_key["type"] = "static"
    player_count_key["object"] = "short"
    player_count_key["body"] = ["(list_count (players))"]

    css_key = gs_scripts["cinematic_skip_start"] = {}

    css_key["type"] = "static"
    css_key["object"] = "boolean"
    css_key["body"] = ["(cinematic_skip_start_internal)",
                       "(game_save_totally_unsafe)",
                       "(sleep_until (not (game_saving)) 1)",
                       "(not (game_reverted))"
                       ]

    css2_key = gs_scripts["cinematic_skip_stop"] = {}

    css2_key["type"] = "static"
    css2_key["object"] = "void"
    css2_key["body"] = ["(cinematic_skip_stop_internal)"
                       ]

    sds_key = gs_scripts["script_dialog_start"] = {}

    sds_key["type"] = "static"
    sds_key["object"] = "void"
    sds_key["body"] = ["(sleep_until (not global_dialog_on))",
                       "(set global_dialog_on true)",
                       "(ai_dialogue_triggers off)"
                       ]

    sds2_key = gs_scripts["script_dialog_stop"] = {}

    sds2_key["type"] = "static"
    sds2_key["object"] = "void"
    sds2_key["body"] = ["(ai_dialogue_triggers on)",
                        "(sleep 30)",
                        "(set global_dialog_on false)"
                        ]

    pei_key = gs_scripts["player_effect_impact"] = {}

    pei_key["type"] = "static"
    pei_key["object"] = "void"
    pei_key["body"] = ["(player_effect_set_max_translation .05 .05 .075)",
                       "(player_effect_set_max_rotation 0 0 0)",
                       "(player_effect_set_max_vibrate .4 1)",
                       "(player_effect_start (real_random_range .7 .9) .1)"
                       ]

    pee_key = gs_scripts["player_effect_explosion"] = {}

    pee_key["type"] = "static"
    pee_key["object"] = "void"
    pee_key["body"] = ["(player_effect_set_max_translation .01 .01 .025)",
                       "(player_effect_set_max_rotation .5 .5 1)",
                       "(player_effect_set_max_vibrate .5 .4)",
                       "(player_effect_start (real_random_range .7 .9) .1)"
                       ]

    per_key = gs_scripts["player_effect_rumble"] = {}

    per_key["type"] = "static"
    per_key["object"] = "void"
    per_key["body"] = ["(player_effect_set_max_translation .01 0 .02)",
                       "(player_effect_set_max_rotation .1 .1 .2)",
                       "(player_effect_set_max_vibrate .5 .3)",
                       "(player_effect_start (real_random_range .7 .9) .5)"
                       ]

    pev_key = gs_scripts["player_effect_vibration"] = {}

    pev_key["type"] = "static"
    pev_key["object"] = "void"
    pev_key["body"] = ["(player_effect_set_max_translation .0075 .0075 .0125)",
                       "(player_effect_set_max_rotation .01 .01 .05)",
                       "(player_effect_set_max_vibrate .2 .5)",
                       "(player_effect_start (real_random_range .7 .9) 1)"
                       ]

def generate_level(context, game_title, level_seed, level_theme, level_damage, level_goal, player_biped, level_conflict, mutator_random_weapons, mutator_extended_family, maze_height, maze_width, output_directory, report):
    player_count = 2

    if not level_seed == 0:
        random.seed(level_seed)

    blocks_dic = {}
    weapons_dic = {}
    characters_dic = {}
    music_dic = {}

    block_configs = []
    character_configs = []
    weapon_configs = []
    music_configs = []
    for path, subdirs, files in os.walk(os.path.join(ADDON_DIRECTORY, r"misc\maze_gen\level_assets")):
        for name in files:
            if "blocks" in name.lower():
                block_configs.append(os.path.join(path, name))

            elif "characters" in name.lower():
                character_configs.append(os.path.join(path, name))

            elif "music" in name.lower():
                music_configs.append(os.path.join(path, name))

            elif "weapons" in name.lower():
                weapon_configs.append(os.path.join(path, name))

    for block_config in block_configs:
        append_keys(blocks_dic, block_config)

    for character_config in character_configs:
        append_keys(characters_dic, character_config)

    for music_config in music_configs:
        append_keys(music_dic, music_config)

    for weapon_config in weapon_configs:
        append_keys(weapons_dic, weapon_config)

    maze, start, end = generate_maze(maze_height, maze_width)
    maze_solution = solve_maze(maze, start, end)

    scene = context.scene
    collection = context.collection

    TAG, SCENARIO = initialize_scenario()

    script_dic = {}
    generate_global_scripts(script_dic, player_count)
    mission_key = script_dic["mission"] = {}
    mission_globals = mission_key["globals"] = {}
    mission_scripts = mission_key["scripts"] = {}
    mission_main_key = mission_scripts["main"] = {}

    mission_main_key["type"] = "startup"
    mission_main_body = mission_main_key["body"] = []

    level_root = create_level_root(collection, context)

    end_point = None
    cell_count = len(maze_solution)
    bpy.ops.object.select_all(action='DESELECT')
    valid_teams = []
    for faction_key in characters_dic:
        if not faction_key == "human":
            valid_teams.append(faction_key)

    active_teams = []
    selected_team = random.choice(valid_teams)
    active_teams.append(selected_team)
    valid_teams.remove(selected_team)

    mission_main_body.append("(player_intro)")

    for cell_idx, cell in enumerate(maze_solution):
        if not len(valid_teams) == 0:
            roll_100 = random.randint(1, 100)
            if roll_100 > 90:
                selected_team = random.choice(valid_teams)
                active_teams.append(selected_team)
                valid_teams.remove(selected_team)

        if cell_idx == 0:
            # Create starting point
            block, attachment_points = create_object(collection, level_root, grab_block(blocks_dic, game_title, level_theme, "start_blocks"))

            block.name = str(cell_idx)

            valid_polygons = []
            hvs_attribute = block.data.attributes.get("Halo Valid Surface")
            if not hvs_attribute == None:
                for surface_idx, surface in enumerate(hvs_attribute.data):
                    if surface.value:
                        valid_polygons.append(block.data.polygons[surface_idx])

            player_intro_key = mission_scripts["player_intro"] = {}

            player_intro_key["type"] = "static"
            player_intro_key["object"] = "void"
            player_intro_body = player_intro_key["body"] = ["(fade_out 0 0 0 0)",]

            for player_idx in range(player_count):
                player_intro_body.append("(object_set_scale (list_get (players) %s) .1 0)" % player_idx)

            player_intro_body.append("(sleep 10)")
            player_intro_body.append("(fade_in 0 0 0 10)")
            player_intro_body.append('(sound_looping_start "%s" NONE 1.0)' % random.choice(music_dic["music"]))
            player_intro_body.append("(camera_control 1)")
            player_intro_body.append('(camera_set_animation "levels\\test\\maze_gen\\cinematics\\cinematics" "intro")')
            for player_idx in range(player_count):
                player_intro_body.append(['((> (list_count (players)) %s)(device_set_position "tele_%s" 1))' % (player_idx, player_idx)])

            for player_idx in range(player_count):
                player_intro_body.append("(object_set_scale (list_get (players) %s) 1 30)" % player_idx)

            for player_idx in range(player_count):
                player_intro_body.append("(get_loadout (player%s))" % player_idx)

            player_intro_body.append("(sleep (camera_time))")
            player_intro_body.append("(camera_control 0)")

            generate_player_starting_locations(SCENARIO, player_count, block, attachment_points, valid_polygons)

            generate_trigger_volume(SCENARIO, "starting_trigger", block)

            generate_intro_cutscene(context, SCENARIO, TAG)

            generate_player_profiles(TAG, SCENARIO, mission_key, weapons_dic)

            end_point = attachment_points[-1]

        elif cell_idx == cell_count-1:
            # Create end point
            block, attachment_points = create_object(collection, level_root, grab_block(blocks_dic, game_title, level_theme, "start_blocks"))
            block.name = str(cell_idx)
            attach_matrix = Matrix.Rotation(radians(180.0), 4, 'Z')
            scale_value = 1
            attach_object(block, attachment_points, end_point, attach_matrix, scale_value)
            apply_transform(block)
            for point in attachment_points:
                apply_transform(point)

            generate_trigger_volume(SCENARIO, "ending_trigger", block)

            end_key = mission_scripts["end"] = {}

            end_key["type"] = "dormant"
            end_key["body"] = ['(sleep_until (volume_test_objects ending_trigger (players)) 1)',
                                '(player_enable_input FALSE)',
                                '(player_camera_control FALSE)',
                                '(fade_out 1 1 1 100)',
                                '(sleep 100)',
                                '(game_won)'
                                ]

            mission_main_body.append('(wake end)')

            end_point = attachment_points[-1]

        else:
            rotation, scale, flip, is_hallway = get_cell_settings(maze_solution, cell_idx)
            if is_hallway:
                # Create hallway
                block, attachment_points = create_object(collection, level_root, grab_block(blocks_dic, game_title, level_theme, "hallway_blocks"))
                block.name = str(cell_idx)

                attach_matrix = Matrix.Rotation(radians(rotation), 4, 'Z')
                attach_object(block, attachment_points, end_point, attach_matrix, scale)
                apply_transform(block)
                for point in attachment_points:
                    apply_transform(point)

                if scale == -1:
                    flip_normals(block)

                valid_polygons = []
                hvs_attribute = block.data.attributes.get("Halo Valid Surface")
                if not hvs_attribute == None:
                    for surface_idx, surface in enumerate(hvs_attribute.data):
                        if surface.value:
                            valid_polygons.append(block.data.polygons[surface_idx])

                generate_trigger_volume(SCENARIO, "cell_%s_trigger" % cell_idx, block)

                generate_encounters(TAG, SCENARIO, block, attachment_points, mission_main_body, valid_polygons, characters_dic, active_teams)

                end_point = attachment_points[-1]

            else:
                # Create L junction
                block, attachment_points = create_object(collection, level_root, grab_block(blocks_dic, game_title, level_theme, "elbow_blocks"))
                block.name = str(cell_idx)

                attach_matrix = Matrix.Rotation(radians(rotation), 4, 'Z')
                attach_object(block, attachment_points, end_point, attach_matrix, scale)
                apply_transform(block)
                for point in attachment_points:
                    apply_transform(point)

                if scale == -1:
                    flip_normals(block)

                generate_trigger_volume(SCENARIO, "cell_%s_trigger" % cell_idx, block)

                end_point = attachment_points[-1]

        for slot in block.material_slots:
            if slot.material is not None:
                material_name = slot.material.name
                if "." in slot.material.name:
                    split_mat_name = material_name.rsplit(".", 1)
                    if len(split_mat_name[1]) >= 3 and split_mat_name[1].isnumeric():
                        material = bpy.data.materials.get(split_mat_name[0])
                        slot.material = material

    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    generate_source_files(TAG, SCENARIO, output_directory, script_dic)

    generate_structure_bsps(TAG, SCENARIO)

    initialize_tag_blocks(TAG, SCENARIO)

    if not os.path.exists(os.path.dirname(output_directory)):
        os.makedirs(os.path.dirname(output_directory))

    output_file = os.path.join(output_directory, "maze_gen.scenario")
    output_stream = open(output_file, 'wb')
    build_h1_scenario(output_stream, SCENARIO, report)
    output_stream.close()

    return {'FINISHED'}
