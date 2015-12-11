import config
import core
from common import SpriteMap
from core import GC, AssetManager, Graphics, Input, State
from entities import Player
from util import GUI

DECISION_STATE = 'decision'
GAME_OVER_STATE = 'game over'
MAIN_MENU_STATE = 'main menu' 
MESSAGE_STATE = 'message'
PAUSE_STATE = 'pause'
PLAY_STATE = 'play'
ROOM_TRANSITION_STATE = 'room transition state'
SHIP_STATE = 'ship'


def DEBUG_render_options(self):
    for i in xrange(len(self.options)):
        if i == self.current_selection:
            Graphics.set_color(0, 255, 0)
        else:
            Graphics.set_color(255, 255, 255)
        option = self.options[i]
        y = 8 * (i + 4)
        Graphics.draw_text(option, 12, y)


class AbsMenuState(State):

    def __init__(self, world, name):
        State.__init__(self, world, name)

        self.options = []
        self.current_selection = 0

    def select(self, option):
        return

    def update(self):
        if Input.pressed(config.KEY['UP']):
            self.current_selection -= 1
            if self.current_selection < 0:
                self.current_selection = len(self.options) - 1
        if Input.pressed(config.KEY['DOWN']):
            self.current_selection += 1
            if self.current_selection >= len(self.options):
                self.current_selection = 0
        if Input.pressed(config.KEY['SELECT']):
            self.select(self.options[self.current_selection])


class DecisionState(AbsMenuState):
    
    def __init__(self, world):
        AbsMenuState.__init__(self, world, DECISION_STATE)
        self.previous_state = None
        self.message = ''
        self.options = ['YES', 'NO']

    def enter(self, previous_state, *args):
        self.message = args[0]
        self.callback = args[1]
        self.previous_state = previous_state
        self.current_selection = 1

    def select(self, option):
        if Input.pressed(config.KEY['SELECT']):
            self.callback(option == 'YES')
            self.world.change_state(self.previous_state.name)

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text(self.message, 8, 8)

        DEBUG_render_options(self)


class GameOverState(State):
    
    def __init__(self, world):
        State.__init__(self, world, GAME_OVER_STATE)

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text('GAME OVER', 8, 8)

    def update(self):
        if Input.pressed('ANY'):
            self.world.change_state(MAIN_MENU_STATE)


class MainMenuState(AbsMenuState):
    
    def __init__(self, world):
        AbsMenuState.__init__(self, world, MAIN_MENU_STATE)
        self.options = ['NEW', 'CONTINUE', 'OPTIONS', 'EXIT']
        if GC.DEBUG:
            self.options.insert(0, 'DEBUG')

    def select(self, option):
        if option == 'NEW':
            self.world.new_game()
            self.world.change_state(PLAY_STATE)
        elif option == 'CONTINUE':
            try:
                self.world.load_game(config.SAVE_FILE)
            except IOError:
                print 'save file does not exist.'
            else:
                self.world.change_state(PLAY_STATE)
        elif option == 'DEBUG':
            self.world.start_debug()
        elif option == 'EXIT':
            GC.quit()

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text('OVER YONDER', 8, 8)

        DEBUG_render_options(self)


class MessageState(State):
    
    def __init__(self, world):
        State.__init__(self, world, MESSAGE_STATE)
        self.previous_state = None
        self.message = ''

        self.width = GC.view_size[0] - 64
        self.height = GC.view_size[1] - 64

    def enter(self, previous_state, *args):
        self.message = args[0]
        self.previous_state = previous_state

    def update(self):
        if Input.pressed('ANY'):
            self.world.change_state(self.previous_state.name)

    def render(self):
        self.previous_state.render()

        Graphics.set_color(0, 0, 0)
        Graphics.draw_rect(32, 32, self.width, self.height)
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text(self.message, 32, 32)

        # split words
        # check width of each word (use monospace font)
        # if width is greater than line width, new line
        

class PauseState(State):

    def __init__(self, world):
        State.__init__(self, world, PAUSE_STATE)

    def render(self):
        core.ENTITY_ROOM.render()
        Graphics.translate(0, 0)
        Graphics.set_color(0, 0, 0)
        Graphics.draw_text('PAUSED', 8, 8)

    def enter(self, previous_state, *args):
        core.ENTITY_ROOM.pause()

    def exit(self, next_state, *args):
        core.ENTITY_ROOM.resume()

    def update(self):
        if Input.pressed(config.KEY['PAUSE']):
            self.world.change_state(PLAY_STATE)


class PlayState(State):

    def __init__(self, world):
        State.__init__(self, world, PLAY_STATE)

    def render(self):
        # Draw room
        core.ENTITY_ROOM.render()

        # Draw HUD
        Graphics.translate(0, 0)
        if GC.DEBUG:
            Graphics.set_color(255, 255, 255)
            Graphics.draw_text('HP: %d / %d' % 
                               (core.ENTITY_ROOM.player.health, core.ENTITY_ROOM.player.max_health), 
                                8, 8)
        else:
            GUI.draw_HUD()

    def update(self):
        core.ENTITY_ROOM.update()

        if core.ENTITY_ROOM.player.health <= 0:
            self.world.change_state(GAME_OVER_STATE)
        elif Input.pressed(config.KEY['PAUSE']):
            self.world.change_state(PAUSE_STATE)


class RoomTransitionState(State):

    def __init__(self, world):
        State.__init__(self, world, ROOM_TRANSITION_STATE)
        self.graphic = None
        self.new_stage = ''

        self.graphic = SpriteMap(AssetManager.get_image('VFX_TRANSITIONS'), 8, 8)
        self.graphic.add('ROOM_TRANSITION_START', [0, 1, 2, 3, 4, 5, 6], 3, False, self.process)
        self.graphic.add('ROOM_TRANSITION_END', [6, 5, 4, 3, 2, 1, 0], 3, False, self._exit)
    
    def enter(self, previous_state, new_stage):
        self.new_stage = new_stage
        self.graphic.play('ROOM_TRANSITION_START')

    def process(self):
        core.ENTITY_ROOM._load_stage(self.new_stage)
        self.graphic.play('ROOM_TRANSITION_END')

    def _exit(self):
        self.world.change_state(PLAY_STATE)

    def render(self):
        core.ENTITY_ROOM.render()

        frame = self.graphic.frames \
                [self.graphic.current_animation['frames'] \
                 [self.graphic.current_frame]]
        
        camera = core.ENTITY_ROOM.camera

        x = camera.x
        view_left = camera.x + GC.view_size[0]
        view_bottom = camera.y + GC.view_size[1]

        while x < view_left:
            y = camera.y
            while y < view_bottom:
                Graphics.draw_image(frame, x, y)
                y += self.graphic.frame_height
            x += self.graphic.frame_width
        self.graphic.step()


class ShipState(AbsMenuState):
    
    def __init__(self, world):
        AbsMenuState.__init__(self, world, SHIP_STATE)
        self.options = ['OBERON', 'CANCEL']
    
    def enter(self, previous_state, *args):
        player = core.ENTITY_ROOM.player
        self.options = []
        if Player.Item.ID_PLANET_OBERON in player.items:
            self.options.append('OBERON')
        if Player.Item.ID_PLANET_REPTILIA in player.items:
            self.options.append('REPTILIA')
        if Player.Item.ID_PLANET_TEKTONIA in player.items:
            self.options.append('TEKTONIA')
        self.options.append('CANCEL')

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text('WORLDS', 8, 16)

        DEBUG_render_options(self)
        
    def select(self, option):
        if option == 'CANCEL' or \
           option == core.ENTITY_ROOM.planet['name']:
            self.world.change_state(PLAY_STATE)
        elif option == 'OBERON':
            core.ENTITY_ROOM.change_stage('stage/oberon_landing_site.tmx')
        elif option == 'REPTILIA':
            core.ENTITY_ROOM.change_stage('stage/reptilia.tmx')

