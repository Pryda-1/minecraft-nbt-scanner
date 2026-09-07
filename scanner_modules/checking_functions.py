# -*- coding: utf-8 -*-

"""

Functions: check_item, check_block_entity, check_entity.

  - check_item: flags an item or recursively searches it if it's a container.
    
  - check_block_entity: checks the block entity and potentially flags it, or
    searches its items if it's a container.
    
  - check_entity: checks the entity and potentially flags it, or searches its
    items if it's a container.

The constants and parameters used in the functions are also defined here.

"""


#### CONSTANTS & CONFIG ####

MINECRAFT_CONTAINER = "minecraft:container"
MINECRAFT_BUNDLE_CONTENTS = "minecraft:bundle_contents"

MIN_FLAG_ENCHANT = 50 # Items enchanted at or over this level may be flagged

# Components of items that can be obtained in creative mode or with commands
CREATIVE_ITEM_COMPONENTS = {
    "minecraft:unbreakable",
    "minecraft:max_stack_size"
}

# Item IDs of every spawn egg (I think)
MINECRAFT_SPAWN_EGGS = {
    "minecraft:allay_spawn_egg",
    "minecraft:armadillo_spawn_egg",
    "minecraft:axolotl_spawn_egg",
    "minecraft:bat_spawn_egg",
    "minecraft:bee_spawn_egg",
    "minecraft:blaze_spawn_egg",
    "minecraft:bogged_spawn_egg",
    "minecraft:breeze_spawn_egg",
    "minecraft:camel_spawn_egg",
    "minecraft:cat_spawn_egg",
    "minecraft:cave_spider_spawn_egg",
    "minecraft:chicken_spawn_egg",
    "minecraft:cod_spawn_egg",
    "minecraft:cow_spawn_egg",
    "minecraft:creeper_spawn_egg",
    "minecraft:dolphin_spawn_egg",
    "minecraft:donkey_spawn_egg",
    "minecraft:drowned_spawn_egg",
    "minecraft:elder_guardian_spawn_egg",
    "minecraft:ender_man_spawn_egg",
    "minecraft:endermite_spawn_egg",
    "minecraft:evoker_spawn_egg",
    "minecraft:fox_spawn_egg",
    "minecraft:frog_spawn_egg",
    "minecraft:ghast_spawn_egg",
    "minecraft:glow_squid_spawn_egg",
    "minecraft:goat_spawn_egg",
    "minecraft:guardian_spawn_egg",
    "minecraft:hoglin_spawn_egg",
    "minecraft:horse_spawn_egg",
    "minecraft:husk_spawn_egg",
    "minecraft:iron_golem_spawn_egg",
    "minecraft:llama_spawn_egg",
    "minecraft:magma_cube_spawn_egg",
    "minecraft:mooshroom_spawn_egg",
    "minecraft:mule_spawn_egg",
    "minecraft:ocelot_spawn_egg",
    "minecraft:panda_spawn_egg",
    "minecraft:parrot_spawn_egg",
    "minecraft:phantom_spawn_egg",
    "minecraft:pig_spawn_egg",
    "minecraft:piglin_brute_spawn_egg",
    "minecraft:piglin_spawn_egg",
    "minecraft:pillager_spawn_egg",
    "minecraft:polar_bear_spawn_egg",
    "minecraft:pufferfish_spawn_egg",
    "minecraft:rabbit_spawn_egg",
    "minecraft:ravager_spawn_egg",
    "minecraft:salmon_spawn_egg",
    "minecraft:sheep_spawn_egg",
    "minecraft:shulker_spawn_egg",
    "minecraft:silverfish_spawn_egg",
    "minecraft:skeleton_horse_spawn_egg",
    "minecraft:skeleton_spawn_egg",
    "minecraft:slime_spawn_egg",
    "minecraft:sniffer_spawn_egg",
    "minecraft:snow_golem_spawn_egg",
    "minecraft:spider_spawn_egg",
    "minecraft:squid_spawn_egg",
    "minecraft:stray_spawn_egg",
    "minecraft:strider_spawn_egg",
    "minecraft:tadpole_spawn_egg",
    "minecraft:trader_llama_spawn_egg",
    "minecraft:tropical_fish_spawn_egg",
    "minecraft:turtle_spawn_egg",
    "minecraft:vex_spawn_egg",
    "minecraft:villager_spawn_egg",
    "minecraft:vindicator_spawn_egg",
    "minecraft:wandering_trader_spawn_egg",
    "minecraft:warden_spawn_egg",
    "minecraft:witch_spawn_egg",
    "minecraft:wither_skeleton_spawn_egg",
    "minecraft:wolf_spawn_egg",
    "minecraft:zoglin_spawn_egg",
    "minecraft:zombie_horse_spawn_egg",
    "minecraft:zombie_spawn_egg",
    "minecraft:zombie_villager_spawn_egg",
    "minecraft:zombified_piglin_spawn_egg",
    "minecraft:enderman_spawn_egg",
    "minecraft:copper_golem_spawn_egg",
    "minecraft:nautilus_spawn_egg",
    "minecraft:creaking_spawn_egg",
    "minecraft:happy_ghast_spawn_egg",
    "minecraft:ender_dragon_spawn_egg",
    "minecraft:wither_spawn_egg"
}

# Items that can be obtained in creative mode or with commands
CREATIVE_ITEMS = {
    "minecraft:bedrock",
    "minecraft:end_portal_frame",
    "minecraft:reinforced_deepslate",
    "minecraft:barrier",
    "minecraft:structure_void",
    "minecraft:light",
    "minecraft:command_block",
    "minecraft:chain_command_block",
    "minecraft:repeating_command_block",
    "minecraft:command_block_minecart",
    "minecraft:vault",
    "minecraft:spawner",
    "minecraft:mob_spawner",
    "minecraft:trial_spawner",
    "minecraft:jigsaw",
    "minecraft:structure_block",
    "minecraft:test_instance_block",
    "minecraft:test_block",
    "minecraft:debug_stick",
    "minecraft:knowledge_book",
}

# Don't ever flag items with these item IDs
ITEM_IDS_TO_SKIP = {
    "minecraft:enchanted_golden_apple", # (Example placeholder)
    "minecraft:experience_bottle", # (Example placeholder)
    "minecraft:end_crystal", # (Example placeholder)
}

# Mobs that appear in mob spawners naturally
NATURAL_SPAWNER_MOBS = {
    "minecraft:skeleton",
    "minecraft:zombie",
    "minecraft:spider",
    "minecraft:cave_spider",
    "minecraft:silverfish",
    "minecraft:blaze",
    "minecraft:magma_cube",
}

# Flag trial spawners that spawn these mobs
TRIAL_SPAWNER_FLAG_MOBS = {
    'minecraft:ender_dragon', # (Example placeholder)
    'minecraft:wither', # (Example placeholder)
    'minecraft:warden', # (Example placeholder)
}

# Block entities that can be obtained in creative mode or with commands
CREATIVE_BLOCK_ENTITIES = {
    "minecraft:command_block",
    "minecraft:chain_command_block",
    "minecraft:repeating_command_block",
    "minecraft:jigsaw",
    "minecraft:structure_block",
    "minecraft:test_instance_block",
    "minecraft:test_block",
}

# Entities that can be obtained in creative mode or with commands
CREATIVE_ENTITIES = {
    "minecraft:command_block_minecart",
    "minecraft:spawner_minecart"
}


#### HELPER FUNCTIONS ####

def enchant_level(level):
    """
    If level has the "value" attribute, return level.value. Otherwise,
    return level. This is due to the differences in how the .mca and .dat
    files are loaded.
    """
    return getattr(level, "value", level)


#### CHECKING FUNCTIONS ####


def check_item(item):
    """
    Flags an item if meeting certain conditions. If the item is a container,
    the function recursively searches its contents (via DFS), stopping only
    if an item is flagged or all items within the container are checked.
    
    Used for both the player data (.dat) files and the region (.mca) files for
    the chunk data (block entities and entities).
    
    Returns
    -------
    Tuple: (flag, flagged_item_id)
      flag: True if item is flagged; False otherwise.
      flagged_item_id: the ID of the flagged item. None if not flagged.
    """

    #### Get item ID & components ####

    item_id = str(item["id"])
    components = item.get("components", {})


    #### SKIPPING: cases when to definitely not flag ####

    ## Skip if item ID is in ITEM_IDS_TO_SKIP ##
    
    if item_id in ITEM_IDS_TO_SKIP:
        
        return False, None
    
    ## (Example) Skip a regeneration 5 potion ##
    
    if (
            item_id == "minecraft:potion" and
            'minecraft:potion_contents' in components and
            'custom_effects' in components['minecraft:potion_contents'] and
            len(components['minecraft:potion_contents']
                ['custom_effects']) == 1 and
            str(components['minecraft:potion_contents']['custom_effects'][0]
            ["id"]) == "minecraft:regeneration" and
            int(components['minecraft:potion_contents']['custom_effects'][0]
            ["amplifier"]) == 4
        ):
        
        return False, None
    
    ## (Example) Skip custom food items ##
    
    if (
            "minecraft:food" in components or
            "minecraft:consumable" in components
        ):
        
        return False, None
    
    
    #### BASE CASE: item flagging ####
    
    ## Flag item if it is a spawn egg ##
    
    if item_id in MINECRAFT_SPAWN_EGGS:
        
        return True, item_id
    
    ## Flag item if it is one of CREATIVE_ITEMS ##
    
    if item_id in CREATIVE_ITEMS:
        
        return True, item_id
    
    ## (Example) Flag if potion or tipped arrow with custom effects ##
    
    if (
            (item_id == "minecraft:tipped_arrow" or
             item_id == "minecraft:potion") and
            "minecraft:potion_contents" in components and
            ("custom_color" in components['minecraft:potion_contents'] or
             "custom_effects" in components['minecraft:potion_contents'])
        ):
        
        return True, item_id
    
    ## (Example) Flag items with enchantments at or past MIN_FLAG_ENCHANT ##
    
    if (
            "minecraft:enchantments" in components and
            any(
                enchant_level(level) >= MIN_FLAG_ENCHANT for level in
                components["minecraft:enchantments"].values()
            )
        ):
        
        return True, item_id
    
    
    #### RECURSION: check items in a container ####

    ## Non-bundle container ##
    
    if MINECRAFT_CONTAINER in components:
        
        for nested_entry in components[MINECRAFT_CONTAINER]:
            nested_item = nested_entry["item"]

            flag, flagged_item_id = check_item(nested_item)
            
            if flag:
                return True, flagged_item_id

    ## Bundle ##
    
    if MINECRAFT_BUNDLE_CONTENTS in components:

        for nested_item in components[MINECRAFT_BUNDLE_CONTENTS]:

            flag, flagged_item_id = check_item(nested_item)
            
            if flag:
                return True, flagged_item_id
    
    
    #### Non-container item not flagged or no flagged item found ####
    
    return False, None


def check_block_entity(be):
    """
    Flags a block entity if meeting certain conditions.
    
    Returns
    -------
    Tuple: (flag, be_id, flagged_item_id)
      flag: True if the block entity is flagged; False otherwise.
      entity_id: the ID of the flagged block entity.
      flagged_item_id: the ID of the flagged item. None if not applicable or
          no flagged item found.
    """
    
    be_id = str(be['id'])
    
    
    #### (Example) Flag if creative block entity ####
    
    if be_id in CREATIVE_BLOCK_ENTITIES:
        
        return True, be_id, None
    
    
    #### If block is a container, check its items ####
    
    ## A containter that can store multiple items ##
    
    if "Items" in be:

        for item in be["Items"]:

            flag, flagged_item_id = check_item(item)
            
            if flag:
                return True, be_id, flagged_item_id

    ## A containter that stores just one item, e.g. a decorated pot ##
    
    elif "item" in be:

        flag, flagged_item_id = check_item(be["item"])
        
        if flag:
            return True, be_id, flagged_item_id
    
    
    #### MOB SPAWNER ####
    
    ## (Example) Flag if mob spawner has a non-natural mob ##
    
    if (
            be_id == "minecraft:mob_spawner" and
            "SpawnData" in be and "entity" in be["SpawnData"] and
            "id" in be["SpawnData"]["entity"] and
            str(be["SpawnData"]["entity"]["id"]) not in NATURAL_SPAWNER_MOBS
        ):
        
        return True, be_id, None
    
    
    #### TRIAL SPAWNER ####
    
    ## (Example) Flag if trial spawner spawns mob in TRIAL_SPAWNER_FLAG_MOBS ##
    
    if (be_id == "minecraft:trial_spawner" and
        "spawn_data" in be and "entity" in be["spawn_data"] and
        "id" in be["spawn_data"]["entity"] and
        str(be["spawn_data"]["entity"]["id"]) in TRIAL_SPAWNER_FLAG_MOBS):
        
        return True, be_id, None
    
    
    #### Nothing flagged ####
    
    return False, be_id, None


def check_entity(entity):
    """
    Flags an entity if meeting certain conditions.
    
    Returns
    -------
    Tuple: (flag, entity_id, flagged_item_id)
      flag: True if the entity is flagged; False otherwise.
      entity_id: the ID of the entity that is flagged.
      flagged_item_id: the ID of the flagged item. None if not applicable or
          no flagged item found.
    """
    
    entity_id = str(entity['id'])
    
    
    #### Flag if creative entity ####
    
    if entity_id in CREATIVE_ENTITIES:
        
        return True, entity_id, None
    
    
    #### (Example) flag if invulnerable zombie ####
    
    if (
            entity_id == "minecraft:zombie" and
            "Invulnerable" in entity and
            entity["Invulnerable"].value == 1
        ):
        
        return True, entity_id, None
    
    
    #### Check item dropped on ground or in item frame ####
    
    if "Item" in entity:
        
        flag, flagged_item_id = check_item(entity["Item"])
        
        if flag:
            return True, entity_id, flagged_item_id
    
    
    #### If stores items, check them ####
    
    if "Items" in entity:
        
        for item in entity["Items"]:

            flag, flagged_item_id = check_item(item)
            
            if flag:
                return True, entity_id, flagged_item_id
    
    
    #### Check equipment (zombie, armour stand, etc) ####
    
    if "equipment" in entity:
        
        for eq_key in entity['equipment'].keys():
            
            flag, flagged_item_id = check_item(entity['equipment'][eq_key])
            
            if flag:
                return True, entity_id, flagged_item_id
    
    
    #### If entity has passengers, recursively check them ####
    
    if "Passengers" in entity:
        
        for pas in entity["Passengers"]:
            
            flag, pas_entity_id, flagged_item_id = check_entity(pas)
            
            if flag:
                return True, pas_entity_id, flagged_item_id
    
    
    ### Nothing flagged ###
    
    return False, entity_id, None

