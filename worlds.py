from core import GC, EntityRoom, Graphics, Input, World
from util import Camera, ParallaxBackground, Stage
from entities import *
from states import *


class GameWorld(World):

    def __init__(self):
        World.__init__(self)

        self.states = {
            GAME_OVER_STATE: GameOverState(self),
            MAIN_MENU_STATE: MainMenuState(self),
            MESSAGE_STATE: MessageState(self),
            PAUSE_STATE: PauseState(self),
            PLAY_STATE: PlayState(self)
        }

        self.current_state = self.states[PLAY_STATE]

        self.setup()

    def setup(self, save_file=-1):
        # save_file < 0 == NEW GAME

        core.ENTITY_ROOM.player.health = Player.MAX_HEALTH

        if GC.DEBUG:
            # core.ENTITY_ROOM.change_stage("stage/oberon_landing_site.tmx")
            # core.ENTITY_ROOM.change_stage("stage/oberon_split.tmx")
            # core.ENTITY_ROOM.change_stage("stage/reptilia_long_bridge.tmx")
            # core.ENTITY_ROOM.change_stage("stage/test/oberon_tile_test.tmx")
            core.ENTITY_ROOM.change_stage("stage/test/test_room.tmx")
            # core.ENTITY_ROOM.change_stage("stage/test/background_test.tmx")

            core.ENTITY_ROOM.player.x = 20
            # core.ENTITY_ROOM.player.y = 48
            core.ENTITY_ROOM.player.weapon.available = [
                Player.Weapon.ID_NONE, 
                Player.Weapon.ID_PISTOL,
                Player.Weapon.ID_MISSILE
            ]
            core.ENTITY_ROOM.player.items = [
                Player.Item.ID_DASH_BOOTS,
                Player.Item.ID_DOUBLE_JUMP
            ]

            # core.ENTITY_ROOM.add(Bat(200, 100))
        else:
            core.ENTITY_ROOM.change_stage("stage/oberon_landing_site.tmx")
            core.ENTITY_ROOM.player.x = 944
            core.ENTITY_ROOM.player.y = 112

    def change_state(self, state_name, message=''):
        if state_name == self.current_state.name:
            return

        previous_state = self.current_state

        self.current_state.exit()
        self.current_state = self.states[state_name]
        
        if state_name in self.states:
            if state_name == MESSAGE_STATE:
                self.current_state.enter(message, previous_state)
            else:
                self.current_state.enter()
        elif GC.DEBUG:
            print '*ERROR* state does not exist: ' + state_name

    def render(self):
        self.current_state.render()
        if GC.DEBUG and Input.down('g'):
            off_x = 0 - core.ENTITY_ROOM.camera.x % 16
            off_y = 0 - core.ENTITY_ROOM.camera.y % 16
            Graphics.set_color(50, 50, 50)
            Graphics.debug_draw_grid(16, 16, off_x, off_y)

    def update(self):
        if Input.pressed('escape'):
            GC.quit()
        else:
            self.current_state.update()


class GameRoom(EntityRoom):

    ACTIVE_ZONE_SIZE = (320, 200)  # GC.view_size * 1.25
    
    # If player moves at 2.5/s then they will pass the active zone in 25 cycles. Therefore
    # the active zone must be updated every 24 cycles to prevent the player from interracting
    # with an inactive entity.
    ACTIVITY_UPDATE_WAIT_TIME = 24
    
    def __init__(self):
        EntityRoom.__init__(self)

        self.refresh_activity_timer = GameRoom.ACTIVITY_UPDATE_WAIT_TIME

        self.camera = Camera(*GC.view_size)
        self.background = ParallaxBackground(*GC.view_size)
        self.stage = Stage()
        self.player = Player(0, 0)

        self.planet = {
            'name': '',
            'outside': False
        }

        # Used only for rendering. Alterations to stage layers should be
        # processed by self.stage.layers
        self._BACKGROUND_LAYERS = []
        self._FOREGROUND_LAYERS = []

    def change_stage(self, path):
        if GC.DEBUG:
            print 'PATH: ' + path

        # Load map
        prev_stage = self.stage
        new_stage = Stage()
        new_stage.load_tiled(path)

        if 'PLANET' in new_stage.properties:
            self.planet['name'] = new_stage.properties['PLANET']
        else:
            self.planet['name'] = ''
            if GC.DEBUG:
                print '*WARNING* Planet not specified'
        if 'OUTSIDE' in new_stage.properties:
            self.planet['outside'] = bool(new_stage.properties['OUTSIDE'])
        else:
            self.planet['outside'] = False

        # Reset
        self.clear()
        self._BACKGROUND_LAYERS = []
        self._FOREGROUND_LAYERS = []

        # Parse layers
        for layer in new_stage.layers:
            name = layer.name[:10]
            if name == 'BACKGROUND':
                self._BACKGROUND_LAYERS.append(layer)
            if name == 'FOREGROUND':
                self._FOREGROUND_LAYERS.append(layer)

        # Parse objects
        player_spawn_x = None
        player_spawn_y = None

        for OBJ in new_stage.objects:

            if OBJ.group == 'SOLIDS':

                flip_x = False
                flip_y = False
                solid_obj = None

                if OBJ.is_polygon:
                    x = OBJ.x
                    y = OBJ.y
                    w = 0
                    h = 0
                    flip_x = True

                    for point in OBJ.polygon_points:
                        if point[0] != 0:
                            if w != 0:
                                flip_x = False
                            w = abs(point[0])
                        if point[1] != 0:
                            h = abs(point[1])
                            if point[1] < 0:
                                y -= h

                    self.add(Solid(x, y, w, h, True, flip_x, flip_y))
                else:
                    self.add(Solid(OBJ.x, OBJ.y, OBJ.w, OBJ.h))

            elif OBJ.group == 'OBJECTS':

                obj = None

                if OBJ.name == 'BAT':
                    obj = Bat(OBJ.x, OBJ.y)

                elif OBJ.name == 'BREAKABLE':
                    obj = BreakableTile(OBJ.x, OBJ.y)

                elif OBJ.name == 'DASHER':
                    initial_direction = OBJ.properties['DIRECTION']
                    obj = Dasher(OBJ.x, OBJ.y, initial_direction)

                elif OBJ.name == 'DOOR':
                    link = OBJ.properties['LINK']

                    obj = Door(OBJ.x, OBJ.y, link)

                    if link == prev_stage.path:
                        player_spawn_x = OBJ.x + 3
                        player_spawn_y = OBJ.y + 4

                elif OBJ.name == 'ITEM':
                    global_id = OBJ.properties['GLOBAL_ID']
                    item_type = OBJ.properties['ITEM_TYPE']
                    value = OBJ.properties['VALUE']

                    obj = Item(OBJ.x, OBJ.y, global_id, item_type, value)

                elif OBJ.name == 'MOVING_PLATFORM':
                    start_x = OBJ.x
                    start_y = OBJ.y
                    end_x = OBJ.x + OBJ.polygon_points[1][0]
                    end_y = OBJ.y + OBJ.polygon_points[1][1]

                    obj = MovingPlatform(start_x, start_y, end_x, end_y)

                elif OBJ.name == 'PLATFORM':
                    obj = Platform(OBJ.x, OBJ.y, OBJ.w)
                
                elif OBJ.name == 'PRESSURE_PLATE':
                    on_activate = OBJ.properties['ON_ACTIVATE']
                    on_deactive = OBJ.properties['ON_DEACTIVATE']
                    obj = PressurePlate(OBJ.x, OBJ.y+12, on_activate, on_deactive)

                elif OBJ.name == 'RETRACTABLE_DOOR':
                    obj = RetractableDoor(OBJ.x, OBJ.y, OBJ.h)

                elif OBJ.name == 'SAVE_POINT':
                    obj = SaveStation(OBJ.x, OBJ.y)

                    if not (player_spawn_x or player_spawn_y):
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                elif OBJ.name == 'SIGN':
                    message = OBJ.properties['MESSAGE']
                    obj = SignPost(OBJ.x, OBJ.y, message)
                
                elif OBJ.name == 'SPIKES':
                    obj = Spikes(OBJ.x, OBJ.y, OBJ.w)

                elif OBJ.name == 'SMALL_GOLEM':
                    obj = SmallGolem(OBJ.x, OBJ.y)

                elif OBJ.name == 'SKELETON':
                    obj = Skeleton(OBJ.x, OBJ.y)

                elif OBJ.name == 'SWITCH':
                    on_activate = OBJ.properties['ON_ACTIVATE']
                    obj = Switch(OBJ.x, OBJ.y, on_activate)

                elif OBJ.name == 'WEIGHT':
                    obj = Weight(OBJ.x, OBJ.y)

                elif OBJ.name == 'DEBUG_SPAWN':
                    if GC.DEBUG:
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                if obj is not None:
                    if 'NAME' in OBJ.properties:
                        obj.name = OBJ.properties['NAME']
                    if 'ACTIVE' in OBJ.properties:
                        obj.active = bool(OBJ.properties['ACTIVE'])
                    self.add(obj)
        
        # TODO load player like regular entity
        if self.player is None: 
            self.player = Player(0, 0)
        if player_spawn_x is not None and player_spawn_y is not None:
            self.player.x = player_spawn_x
            self.player.y = player_spawn_y
        self.add(self.player)

        if self.stage is not None:
            self.stage.clear()

        self.stage = new_stage

        self.camera.max_width = self.stage.width
        self.camera.max_height = self.stage.height

        self.change_background()

    def clear(self):
        EntityRoom.clear(self)
        self._BACKGROUND_LAYERS = []
        self._BACKGROUND_LAYERS = []

    def close(self):
        self.clear()
        self.stage.clear()

    def render(self):
        # Update camera
        pcx = self.player.x + Player.WIDTH / 2
        pcy = self.player.y + Player.HEIGHT / 2

        self.camera.center_on(pcx, pcy)
        self.camera.update()
        self.camera.translate()

        # Draw stage & entities
        self.background.render(self.camera.x, self.camera.y)

        for layer in self._BACKGROUND_LAYERS:
            self.stage.render_layer(layer)
        for entity in self.entities:
            if entity.visible:
                entity.render()
        for layer in self._FOREGROUND_LAYERS:
            self.stage.render_layer(layer)

    def update(self):
        # Update activity zone
        self.refresh_activity_timer -= 1
        if self.refresh_activity_timer <= 0:
            self.refresh_activity_timer = GameRoom.ACTIVITY_UPDATE_WAIT_TIME
            self.update_active_zone()
        
        # Update entities
        if Input.pressed('up'):
            door = self.player.collides_group('door')
            if door:
                core.ENTITY_ROOM.change_stage(door[0].link)

        for entity in self.entities:
            # TODO add END_UPDATE event
            if entity.active:
                entity.update()

    def update_active_zone(self):
        arw, arh = GameRoom.ACTIVE_ZONE_SIZE
        arx = (self.player.x + Player.WIDTH / 2) - arw / 2
        ary = (self.player.y + Player.HEIGHT / 2) - arh / 2

        if arx < 0:
            arx = 0
        elif arx > self.stage.width - arw:
            arx = self.stage.width - arw
        if ary < 0:
            ary = 0
        elif ary > self.stage.height - arh:
            ary = self.stage.height - arh

        active_zone = (arx, ary, arw, arh)

        for entity in self.entities:
            if entity.group == 'solid' or entity.collides_rect(active_zone):
                entity.active = True
            elif entity.group == 'projectile':
                entity.destroy()
            else:
                entity.active = False

    def change_background(self):
        self.background.clear()
        get_image = AssetManager.get_image

        if self.planet['name'] == 'oberon':
            if self.planet['outside']:
                self.background.add_layer(get_image('BACKGROUND_OBERON_OUTER'), 0.5, 0.5, True, True)
            else:
                self.background.add_layer(get_image('BACKGROUND_OBERON_INNER'), 0, 0, True, True)
        elif self.planet['name'] == 'reptilia':
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHEST'), 0.25, 0, True, independent=True)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHER'), 0, 0)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FAR'), 0.25, 0, True)
