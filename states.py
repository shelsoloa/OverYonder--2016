import core
from core import GC, AssetManager, Graphics, Input, State
from entities import Player

MAIN_MENU_STATE = 'main menu' 
MESSAGE_STATE = 'message'
GAME_OVER_STATE = 'game over'
PAUSE_STATE = 'pause'
PLAY_STATE = 'play'


class AbsMenuState(State):

    def __init__(self, world, name):
        State.__init__(self, world, name)

        self.options = []
        self.current_selection = 0

    def update(self):
        if Input.pressed('up'):
            self.current_selection -= 1
            if self.current_selection < 0:
                self.current_selection = len(self.options)
        if Input.pressed('down'):
            self.current_selection += 1
            if self.current_selection > len(self.options):
                self.current_selection = 0


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
        self.options = ['NEW', 'CONTINUE', 'EXIT']

    def update(self):
        if Input.pressed('ANY'):
            self.world.setup()
            self.world.change_state(PLAY_STATE)

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_text('PRESS ANY KEY', 8, 8)


class MessageState(State):
    
    def __init__(self, world):
        State.__init__(self, world, MESSAGE_STATE)
        self.previous_state = None
        self.message = ''

        self.width = GC.view_size[0] - 64
        self.height = GC.view_size[1] - 64

    def enter(self, message, previous_state):
        self.message = message
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

    def update(self):
        if Input.pressed('p'):
            self.world.change_state(PLAY_STATE)


class PlayState(State):

    IMG_HEALTH_FULL = None
    IMG_HEALTH_EMPTY = None

    def __init__(self, world):
        State.__init__(self, world, PLAY_STATE)
        PlayState.IMG_HEALTH_FULL = AssetManager.get_image('HUD_HEALTH_FULL')
        PlayState.IMG_HEALTH_EMPTY = AssetManager.get_image('HUD_HEALTH_EMPTY')

    def render(self):
        # Draw room
        core.ENTITY_ROOM.render()

        # Draw HUD
        Graphics.translate(0, 0)
        if GC.DEBUG:# and Input.down('g'):
            Graphics.set_color(255, 255, 255)
            Graphics.draw_text('HP: %d / %d' % (core.ENTITY_ROOM.player.health, Player.MAX_HEALTH), 9, 8)
        else:
            self.draw_HUD()

    def draw_HUD(self):
        for i in range(Player.MAX_HEALTH):
            if i >= core.ENTITY_ROOM.player.health:
                Graphics.draw_image(PlayState.IMG_HEALTH_EMPTY, 8 + 4*i, 12)
            else:
                Graphics.draw_image(PlayState.IMG_HEALTH_FULL, 8 + 4*i, 12)

    def update(self):
        core.ENTITY_ROOM.update()

        if core.ENTITY_ROOM.player.health <= 0:
            self.world.change_state(GAME_OVER_STATE)
        elif Input.pressed('p'):
            self.world.change_state(PAUSE_STATE)
