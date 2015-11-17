import config
import core
from core import GC, Graphics, AssetManager
from worlds import GameRoom, GameWorld

def load_assets():
    AssetManager.assets_path = config.ASSET_PATH
    Graphics.font = AssetManager.load_font('MAIN', 'visitor1.ttf', 10)

    # TODO add to loading list file
    IMAGES = {
        'BREAKABLE_TILE': 'img/entity_breakable_tile.png',
        'DASHER': 'img/entity_dasher.png',
        'DOOR': 'img/entity_door.png',
        'HUD_HEALTH_FULL': 'img/hud_health_full.png',
        'HUD_HEALTH_EMPTY': 'img/hud_health_empty.png',
        'MOVING_PLATFORM': 'img/entity_moving_platform.png',
        'PLAYER': 'img/entity_player.png',
        'SAVE_STATION': 'img/entity_save_station.png',
        'SIGN_POST': 'img/entity_sign_post.png',
        'SKELETON': 'img/entity_skeleton.png',
        'SMALL_GOLEM': 'img/entity_golem.png',
        'SWITCH': 'img/entity_switch.png',
        'UPGRADES': 'img/item_upgrades.png',
        'WEIGHT': 'img/entity_weight.png',
        'BACKGROUND_OBERON_INNER': 'img/bg_oberon_inner.png',
        'BACKGROUND_OBERON_OUTER': 'img/bg_oberon_outer_TEMP.png',
        'BACKGROUND_REPTILIA_FAR': 'img/bg_reptilia_far.png',
        'BACKGROUND_REPTILIA_FARTHER': 'img/bg_reptilia_farther.png',
        'BACKGROUND_REPTILIA_FARTHEST': 'img/bg_reptilia_farthest.png'
    }

    for IMAGE_NAME, IMAGE_PATH in IMAGES.iteritems():
        image = AssetManager.load_image(IMAGE_NAME, IMAGE_PATH)

TITLE = 'OVER YONDER'
SCALE = 4 # TODO add to config.py
WINDOW_SIZE = (256, 160) # The same as GameRoom.VIEW_SIZE
DEBUG = True

if __name__ == "__main__":
    GC.init(WINDOW_SIZE, SCALE, TITLE, DEBUG)
    load_assets()

    core.ENTITY_ROOM = GameRoom()
    GC.world = GameWorld()

    GC.run()
