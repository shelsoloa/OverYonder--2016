MAP
  > PLANET -> The name of the planet

LAYERS
    FOREGROUND
      * Tiles drawn after entities
    BACKGROUND
      * Tiles drawn before entities
    OBJECTS
      * All game objects are put on this layer (excluding solids)
          BAT
          BREAKABLE (Breakable Wall)
          DEBUG_SPAWN
          DASHER
            > DIRECTION -> The initial direction of the dasher
          DOOR
            > LINK -> The name of the map that this door will take the player too
          ITEM
            > GLOBAL_ID -> Used to tell whether or not this item has been obtained
            > TYPE -> The type of item (HEALTH_UPGRAGE, WEAPON_CASE)
            > VALUE -> Additional value variable (HEALTH_UPGRADE_VALUE, WEAPON_NAME)
          MOVING_PLATFORM
            * Made using polyline tool
            > DIRECTION -> The initial direction of the moving platform
          PRESSURE_PLATE
            > ON_ACTIVATE -> Script to be ran upon activation
            > ON_DEACTIVATE -> Script to be ran upon deactivation
          SKELETON
          SMALL_GOLEM
          SPIKES
          WEIGHT
    SOLID
      * All static solid objects
