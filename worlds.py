from core import GC, EntityRoom, Graphics, Input, World
from common import save, load, Stage
from util import Camera, ParallaxBackground
from entities import *
from states import *


class GameWorld(World):

    def __init__(self):
        World.__init__(self)

        self.states = {
            DECISION_STATE: DecisionState(self),
            GAME_OVER_STATE: GameOverState(self),
            MAIN_MENU_STATE: MainMenuState(self),
            MESSAGE_STATE: MessageState(self),
            PAUSE_STATE: PauseState(self),
            PLAY_STATE: PlayState(self),
            ROOM_TRANSITION_STATE: RoomTransitionState(self),
            SHIP_STATE: ShipState(self)
        }

        self.current_state = self.states[MAIN_MENU_STATE]


    def start_debug(self):
        self.current_state = self.states[PLAY_STATE]
        
        core.ENTITY_ROOM.player = Player(0, 0)

        # core.ENTITY_ROOM._load_stage('stage/oberon_landing_site.tmx')
        core.ENTITY_ROOM._load_stage('stage/reptilia_underpass.tmx')
        # core.ENTITY_ROOM._load_stage('stage/test/test_room.tmx')

        # Add debug entities here so they are rendered below the player
        # core.ENTITY_ROOM.add(AbsClimbable(200, 40, 100))
        # core.ENTITY_ROOM.add(ArrowTrap(200, 100, 'LEFT'))
        # core.ENTITY_ROOM.add(BreakableReinforcedTile(200, 100, 100, 100))
        # core.ENTITY_ROOM.add(GoblinSwordsman(200, 10))
        # core.ENTITY_ROOM.add(Boulder(100, 50, 'LEFT'))
        # BOULDER_SPAWNER 

        # core.ENTITY_ROOM.player.x = 20
        # core.ENTITY_ROOM.player.y = 0
        core.ENTITY_ROOM.player.items = [
            Player.Item.ID_FIST, 
            Player.Item.ID_PISTOL,
            Player.Item.ID_MISSILE,
            # Player.Item.ID_DASH_BOOTS,
            # Player.Item.ID_DOUBLE_JUMP,
            Player.Item.ID_PLANET_OBERON,
            Player.Item.ID_PLANET_REPTILIA
        ]

    def load_game(self, file_name):
        try:
            save_data = load(file_name)
        except IOError:
            raise

        stage = save_data[0]
        ammo  = save_data[1]
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

        core.ENTITY_ROOM.flags = flags
        core.ENTITY_ROOM.player = player
        core.ENTITY_ROOM._load_stage(stage)

    def new_game(self):
        core.ENTITY_ROOM.player = Player(0, 0)
        player = core.ENTITY_ROOM.player
        core.ENTITY_ROOM._load_stage("stage/oberon_landing_site.tmx")
        player.x = 944
        player.y = 112
        core.ENTITY_ROOM.camera.snap(player.x, player.y, True)

    def save_game(self, file_name):
        data = []

        data.append(core.ENTITY_ROOM.stage.path)
        data.append(core.ENTITY_ROOM.player.ammo)
        data.append(core.ENTITY_ROOM.player.items)
        data.append(core.ENTITY_ROOM.event_flags)

        save(data, file_name)

    def render(self):
        self.current_state.render()
        if GC.DEBUG and Input.down('g'):
            off_x = 0 - core.ENTITY_ROOM.camera.x % 16
            off_y = 0 - core.ENTITY_ROOM.camera.y % 16
            Graphics.set_color(50, 50, 50)
            Graphics.debug_draw_grid(16, 16, off_x, off_y)

    def update(self):
        if GC.DEBUG:
            if Input.pressed('q'):
                print core.ENTITY_ROOM.player.items

        # Update entities
        if Input.pressed('escape'):
            GC.quit()
        elif GC.DEBUG and Input.pressed('F1'):
            self.load_game('debug.sav')
            print 'Game Loaded'
        elif GC.DEBUG and Input.pressed('1'):
            self.save_game('debug.sav')
            print 'Game Saved'
        elif Input.pressed('F2'):
            GC.toggle_fullscreen()
        else:
            self.current_state.update()


class GameRoom(EntityRoom):

    ACTIVE_ZONE_SIZE = (384, 240)  # GC.view_size * 1.5
    
    # If player moves at 2.5/s then they will pass the active zone in 25 cycles. Therefore
    # the active zone must be updated every 24 cycles to prevent the player from interracting
    # with an inactive entity.
    ACTIVITY_UPDATE_WAIT_TIME = 24

    STATE_RUNNING = 0
    STATE_PAUSED = 1
    STATE_CHANGING_STAGES = 2
    
    def __init__(self):
        EntityRoom.__init__(self)

        self._zone_refresh_timer = GameRoom.ACTIVITY_UPDATE_WAIT_TIME
        self._running = True

        self.triggered_events = []

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

    def pause(self):
        self._running = True
        for entity in self.entities:
            try:
                entity.sprite.pause()
            except AttributeError:
                pass  # sprite is not of SpriteMap

    def resume(self):
        self._running = False
        for entity in self.entities:
            try:
                entity.sprite.resume()
            except AttributeError:
                pass  # sprite is not of SpriteMap

    def change_stage(self, path):
        self.pause()
        GC.world.change_state(ROOM_TRANSITION_STATE, path)

    def clear(self):
        EntityRoom.clear(self)
        self._BACKGROUND_LAYERS = []
        self._BACKGROUND_LAYERS = []

    def close(self):
        self.clear()
        self.stage.clear()

    def render(self):
        # Update camera location
        self.camera.update()
        self.camera.translate()

        # Draw stage & entities
        self.background.render(self.camera.x, self.camera.y)

        for layer in self._BACKGROUND_LAYERS:
            self.stage.render_layer(layer)
        for entity in self.entities:
            if entity.visible and entity != self.player:
                entity.render()
        self.player.render()
        for layer in self._FOREGROUND_LAYERS:
            self.stage.render_layer(layer)

    def update(self):
        if self._running:
            # Update activity zone
            self._zone_refresh_timer -= 1
            if self._zone_refresh_timer <= 0:
                self._zone_refresh_timer = GameRoom.ACTIVITY_UPDATE_WAIT_TIME
                self._update_activity_zone()
            
            # Update entities
            if Input.pressed(config.KEY['INTERACT']):
                door = self.player.collides_group('door')
                if door:
                    self.change_stage(door[0].link)
                    return

            for entity in self.entities:
                # TODO add END_UPDATE event
                if entity.active:
                    entity.update()

    def _change_background(self):
        self.background.clear()
        get_image = AssetManager.get_image

        if self.planet['name'] == 'OBERON':
            if self.planet['outside']:
                self.background.add_layer(get_image('BACKGROUND_OBERON_OUTER'), 0.5, 0.5, True, True)
            else:
                self.background.add_layer(get_image('BACKGROUND_OBERON_INNER'), 0, 0, True, True)
        elif self.planet['name'] == 'REPTILIA':
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHEST'), 0.25, 0, True, independent=True)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHER'), 0, 0)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FAR'), 0.25, 0, True)

    def _update_activity_zone(self):
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
            if entity.collides_rect(active_zone) or \
               entity.group == 'boulder' or entity.group == 'solid':
                entity.active = True
            elif entity.group == 'projectile':
                entity.destroy()
            else:
                entity.active = False

    def _load_stage(self, path, debug_spawn=False):
        if GC.DEBUG:
            print '[LOG] stage path: ' + path

        # Load map
        prev_stage = self.stage
        new_stage = Stage()
        new_stage.load_tiled(path)

        if 'PLANET' in new_stage.properties:
            self.planet['name'] = new_stage.properties['PLANET'].upper()
        else:
            self.planet['name'] = ''
            if GC.DEBUG:
                print '[WARNING] planet unspecified'
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

                if OBJ.name == 'ARROW_TRAP':
                    direction = OBJ.properties['DIRECTION']
                    obj = ArrowTrap(OBJ.x, OBJ.y, direction)

                elif OBJ.name == 'BAT':
                    obj = Bat(OBJ.x, OBJ.y)

                elif OBJ.name == 'BOULDER_SPAWNER':
                    spawn_direction = OBJ.properties['DIRECTION']
                    obj = BoulderSpawner(OBJ.x, OBJ.y, spawn_direction)

                elif OBJ.name == 'BREAKABLE':
                    obj = BreakableTile(OBJ.x, OBJ.y)

                elif OBJ.name == 'BREAKABLE_REINFORCED':
                    obj = BreakableReinforcedTile(OBJ.x, OBJ.y, OBJ.w, OBJ.h)

                elif OBJ.name == 'CLIMB':
                    obj = AbsClimbable(OBJ.x, OBJ.y, OBJ.h)

                elif OBJ.name == 'DASHER':
                    initial_direction = OBJ.properties['DIRECTION']
                    obj = Dasher(OBJ.x, OBJ.y, initial_direction)

                elif OBJ.name == 'DOOR':
                    link = OBJ.properties['LINK']

                    obj = Door(OBJ.x, OBJ.y, link)

                    if link == prev_stage.path:
                        player_spawn_x = OBJ.x + 3
                        player_spawn_y = OBJ.y + 4

                elif OBJ.name == 'GOBLIN_IMP':
                    obj = GoblinImp(OBJ.x, OBJ.y)

                elif OBJ.name == 'GOBLIN_SWORDSMAN':
                    obj = GoblinSwordsman(OBJ.x, OBJ.y)

                elif OBJ.name == 'ITEM':
                    global_id = OBJ.properties['GLOBAL_ID']
                    item_type = OBJ.properties['ITEM_TYPE']
                    value = OBJ.properties['VALUE']

                    if global_id not in self.player.items:
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

                elif OBJ.name == 'RESOURCE_SLUG_HIVE':
                    orientation = OBJ.properties['ORIENTATION']
                    slug_direction = OBJ.properties['DIRECTION']
                    obj = ResourceSlugHive(OBJ.x, OBJ.y, orientation, slug_direction)

                elif OBJ.name == 'RETRACTABLE_DOOR':
                    obj = RetractableDoor(OBJ.x, OBJ.y, OBJ.w, OBJ.h)

                elif OBJ.name == 'SAVE_POINT':
                    obj = SaveStation(OBJ.x, OBJ.y)

                    if not player_spawn_x and not player_spawn_y:
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                elif OBJ.name == 'SHIP':
                    obj = Ship(OBJ.x, OBJ.y)

                    if prev_stage.path == 'stage/oberon_landing_site.tmx' or \
                       prev_stage.path == 'stage/reptilia.tmx':
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                elif OBJ.name == 'SIGN':
                    message = OBJ.properties['MESSAGE']
                    obj = SignPost(OBJ.x, OBJ.y, message)

                elif OBJ.name == 'SPIDER':
                    obj = Spider(OBJ.x, OBJ.y)
                
                elif OBJ.name == 'SPIKES':
                    obj = Spikes(OBJ.x, OBJ.y, OBJ.w)

                elif OBJ.name == 'SMALL_GOLEM':
                    obj = SmallGolem(OBJ.x, OBJ.y)

                elif OBJ.name == 'SKELETON':
                    obj = Skeleton(OBJ.x, OBJ.y)

                elif OBJ.name == 'SWITCH':
                    on_activate = OBJ.properties['ON_ACTIVATE']
                    obj = Switch(OBJ.x, OBJ.y, on_activate)

                elif OBJ.name == 'WATER':
                    obj = Water(OBJ.x, OBJ.y, OBJ.w, OBJ.h)

                elif OBJ.name == 'WEIGHT':
                    obj = Weight(OBJ.x, OBJ.y)

                elif OBJ.name == 'DEBUG_SPAWN':
                    if debug_spawn:
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
        pcx = self.player.x + Player.WIDTH / 2
        pcy = self.player.y + Player.HEIGHT / 2
        self.camera.snap(pcx, pcy, True)

        self._change_background()
        self._update_activity_zone()

