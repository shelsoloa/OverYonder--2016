import sys

import peachy
from game import config
from game.worlds import MainMenuWorld, GameWorld


class OverYonderEngine(peachy.Engine):
    def __init__(self, debug):
        super().__init__((config.WINDOW_HEIGHT, config.WINDOW_WIDTH),
                         'Over Yonder', debug=debug, scale=4)

    def preload(self):
        peachy.fs.load_font('MAIN', 'assets/visitor1.ttf', 10)
        peachy.graphics.set_font(peachy.fs.get_font('MAIN'))

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
            'BACKGROUND_REPTILIA_FARTHEST': 'img/bg_reptilia_farthest.png',
            'VFX_TRANSITIONS': 'img/vfx_overlays.png'
        }

        SOUNDS = {
            'FOOTSTEP': 'snd/sfx_step.wav'
        }

        for IMAGE_NAME, IMAGE_PATH in IMAGES.items():
            peachy.fs.load_image(IMAGE_NAME, 'assets/' + IMAGE_PATH)

        for SOUND_NAME, SOUND_PATH in SOUNDS.items():
            peachy.fs.load_sound(SOUND_NAME, 'assets/' + SOUND_PATH)

        # GUI.init()
        self.add_world(MainMenuWorld())
        self.add_world(GameWorld())

        try:
            override_stage = sys.argv[1]
            self.world.stage._load_stage(override_stage)
        except IndexError:
            pass
