import peachy
from peachy import PC
from peachy.utils import Key

from game import config, rooms
from game.entities import Player
from game.utility import save, load

DECISION_STATE = 'decision'
GAME_OVER_STATE = 'game over'
MESSAGE_STATE = 'message'
PAUSE_STATE = 'pause'
PLAY_STATE = 'play'
ROOM_TRANSITION_STATE = 'room transition state'
SHIP_STATE = 'ship'


def DEBUG_render_options(self):
    for i in range(len(self.options)):
        if i == self.current_selection:
            peachy.graphics.set_color(0, 255, 0)
        else:
            peachy.graphics.set_color(255, 255, 255)
        option = self.options[i]
        y = 8 * (i + 4)
        peachy.graphics.draw_text(option, 12, y)


class GameWorld(peachy.World):

    def __init__(self):
        super().__init__('GAME')

        self.states = {
            DECISION_STATE: DecisionState(self),
            GAME_OVER_STATE: GameOverState(self),
            MESSAGE_STATE: MessageState(self),
            PAUSE_STATE: PauseState(self),
            PLAY_STATE: PlayState(self),
            ROOM_TRANSITION_STATE: RoomTransitionState(self),
            SHIP_STATE: ShipState(self)
        }

        self.state = self.states[PLAY_STATE]
        self.stage = rooms.OverYonderRoom()

        self.subcontext = peachy.graphics.Surface((config.WINDOW_HEIGHT,
                                                   config.WINDOW_WIDTH))
        self.subcontext_rect = self.subcontext.get_rect()

    def start_debug(self):
        self.state = self.states[PLAY_STATE]

        self.stage.player = Player(0, 0)

        # self.stage._load_stage('stage/oberon_landing_site.tmx')
        self.stage._load_stage('stage/reptilia.tmx')
        # self.stage._load_stage('stage/test/test_room.tmx')

        # Add debug entities here so they are rendered below the player
        # self.stage.add(AbsClimbable(200, 40, 100))
        # self.stage.add(ArrowTrap(200, 100, 'LEFT'))
        # self.stage.add(BreakableReinforcedTile(200, 100, 100, 100))
        # self.stage.add(GoblinSwordsman(200, 10))
        # self.stage.add(Boulder(100, 50, 'LEFT'))
        # BOULDER_SPAWNER

        # self.stage.player.x = 20
        # self.stage.player.y = 0
        self.stage.player.items = [
            Player.Item.ID_FIST,
            Player.Item.ID_PISTOL,
            Player.Item.ID_MISSILE,
            # Player.Item.ID_DASH_BOOTS,
            # Player.Item.ID_DOUBLE_JUMP,
            Player.Item.ID_PLANET_OBERON,
            Player.Item.ID_PLANET_REPTILIA
        ]

    def new_game(self):
        self.stage._load_stage("stage/oberon_landing_site.tmx")
        player = self.stage.player
        player.x = 944
        player.y = 116
        self.stage.camera.snap(player.x, player.y, True)

        self.options = ['NEW', 'CONTINUE', 'OPTIONS', 'EXIT']
        if PC.debug:
            self.options.insert(0, 'DEBUG')
        self.current_selection = 0

    def save_game(self, file_name):
        data = []

        data.append(self.stage.stage.path)
        data.append(self.stage.player.ammo)
        data.append(self.stage.player.items)
        data.append(self.stage.event_flags)

        save(data, file_name)

    def load_game(self, file_name):
        try:
            save_data = load(file_name)
        except IOError:
            raise

        stage = save_data[0]
        ammo = save_data[1]
        items = save_data[2]
        flags = save_data[3]

        player = Player(0, 0)
        player.max_health = Player.BASE_HEALTH
        for item_id in items:
            if item_id[:2] == 'HP':
                player.max_health += 3
        player.health = player.max_health
        player.items = items
        player.ammo = ammo

        self.stage.flags = flags
        self.stage.player = player
        self.stage._load_stage(stage)

    def render(self):
        # Draw stage
        self.state.render()

    def update(self):
        if PC.debug:
            if peachy.utils.Key.pressed('q'):
                print(self.stage.player.items)

        # Update entities
        if peachy.utils.Key.pressed('escape'):
            PC.quit()
        elif PC.debug and peachy.utils.Key.pressed('F1'):
            self.load_game('debug.sav')
            print('Game Loaded')
        elif PC.debug and peachy.utils.Key.pressed('1'):
            self.save_game('debug.sav')
            print('Game Saved')
        else:
            self.state.update()


class AbsMenuState(peachy.State):

    def __init__(self, name, world):
        super().__init__(name, world)

        self.options = []
        self.current_selection = 0

    def select(self, option):
        return

    def update(self):
        if Key.pressed(config.KEY['UP']):
            self.current_selection -= 1
            if self.current_selection < 0:
                self.current_selection = len(self.options) - 1
        if Key.pressed(config.KEY['DOWN']):
            self.current_selection += 1
            if self.current_selection >= len(self.options):
                self.current_selection = 0
        if Key.pressed(config.KEY['SELECT']):
            self.select(self.options[self.current_selection])


class DecisionState(AbsMenuState):

    def __init__(self, world):
        super().__init__(DECISION_STATE, world)
        self.previous_state = None
        self.message = ''
        self.options = ['YES', 'NO']

    def enter(self, previous_state, *args):
        self.message = args[0]
        self.callback = args[1]
        self.previous_state = previous_state
        self.current_selection = 1

    def select(self, option):
        if Key.pressed(config.KEY['SELECT']):
            self.callback(option == 'YES')
            self.world.change_state(self.previous_state.name)

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_text(self.message, 8, 8)

        DEBUG_render_options(self)


class GameOverState(peachy.State):

    def __init__(self, world):
        super().__init__(GAME_OVER_STATE, world)

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_text('GAME OVER', 8, 8)

    def update(self):
        if Key.pressed('ANY'):
            PC.engine.change_world('MAIN')


class MessageState(peachy.State):

    def __init__(self, world):
        super().__init__(MESSAGE_STATE, world)
        self.previous_state = None
        self.message = ''

        self.width = PC.width - 64
        self.height = PC.height - 64

    def enter(self, previous_state, *args):
        self.message = args[0]
        self.previous_state = previous_state

    def update(self):
        if Key.pressed('ANY'):
            self.world.change_state(self.previous_state.name)

    def render(self):
        self.previous_state.render()

        peachy.graphics.set_color(0, 0, 0)
        peachy.graphics.draw_rect(32, 32, self.width, self.height)
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_text(self.message, 32, 32)

        # split words
        # check width of each word (use monospace font)
        # if width is greater than line width, new line


class PauseState(peachy.State):

    def __init__(self, world):
        super().__init__(PAUSE_STATE, world)

    def render(self):
        self.world.stage.render()
        peachy.graphics.translate(0, 0)
        peachy.graphics.set_color(0, 0, 0)
        peachy.graphics.draw_text('PAUSED', 8, 8)

    def enter(self, previous_state, *args):
        self.world.stage.pause()

    def exit(self, next_state, *args):
        self.world.stage.resume()

    def update(self):
        if Key.pressed(config.KEY['PAUSE']):
            self.world.change_state(PLAY_STATE)


class PlayState(peachy.State):

    def __init__(self, world):
        super().__init__(PLAY_STATE, world)

    def render(self):
        # Draw room
        self.world.stage.render()

        # Draw HUD
        peachy.graphics.translate(0, 0)
        if PC.debug:
            peachy.graphics.set_color(255, 255, 255)
            peachy.graphics.draw_text(
                'HP: %d / %d' %
                (self.world.stage.player.health,
                 self.world.stage.player.max_health), 8, 8)
        # else:
        #     GUI.draw_HUD()

    def update(self):
        self.world.stage.update()

        if self.world.stage.player.health <= 0:
            self.world.change_state(GAME_OVER_STATE)
        elif Key.pressed(config.KEY['PAUSE']):
            self.world.change_state(PAUSE_STATE)


class RoomTransitionState(peachy.State):

    def __init__(self, world):
        super().__init__(ROOM_TRANSITION_STATE, world)
        self.graphic = None
        self.new_stage = ''

        self.graphic = peachy.graphics.SpriteMap(peachy.fs.get_image('VFX_TRANSITIONS'), 8, 8)
        self.graphic.add('ROOM_TRANSITION_START', [0, 1, 2, 3, 4, 5, 6], 3, False, self.process)
        self.graphic.add('ROOM_TRANSITION_END', [6, 5, 4, 3, 2, 1, 0], 3, False, self._exit)

    def enter(self, previous_state, new_stage):
        self.new_stage = new_stage
        self.graphic.play('ROOM_TRANSITION_START')

    def process(self):
        self.world.stage._load_stage(self.new_stage)
        self.graphic.play('ROOM_TRANSITION_END')

    def _exit(self):
        self.world.change_state(PLAY_STATE)

    def render(self):
        self.world.stage.render()

        frame = self.graphic.frames[self.graphic.current_animation['frames']
            [self.graphic.current_frame]]

        camera = self.world.stage.camera

        x = camera.x
        view_left = camera.x + PC.width
        view_bottom = camera.y + PC.height

        while x < view_left:
            y = camera.y
            while y < view_bottom:
                peachy.graphics.draw(frame, x, y)
                y += self.graphic.frame_height
            x += self.graphic.frame_width
        self.graphic.step()


class ShipState(AbsMenuState):

    def __init__(self, world):
        super().__init__(SHIP_STATE, world)
        self.options = ['OBERON', 'CANCEL']

    def enter(self, previous_state, *args):
        player = self.world.stage.player
        self.options = []
        if Player.Item.ID_PLANET_OBERON in player.items:
            self.options.append('OBERON')
        if Player.Item.ID_PLANET_REPTILIA in player.items:
            self.options.append('REPTILIA')
        if Player.Item.ID_PLANET_TEKTONIA in player.items:
            self.options.append('TEKTONIA')
        self.options.append('CANCEL')

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_text('WORLDS', 8, 16)

        DEBUG_render_options(self)

    def select(self, option):
        if option == 'CANCEL' or \
           option == self.world.stage.planet['name']:
            self.world.change_state(PLAY_STATE)
        elif option == 'OBERON':
            self.world.stage.change_stage('stage/oberon_landing_site.tmx')
        elif option == 'REPTILIA':
            self.world.stage.change_stage('stage/reptilia.tmx')
