import os

import peachy
from peachy import PC

import game
from game import config, entities
from game.entities import Player
from game.utility import Camera, ParallaxBackground


class OverYonderRoom(peachy.Room):

    ACTIVE_ZONE_SIZE = (384, 240)  # PC.view_size * 1.5

    # If player moves at 2.5/s then they will pass the active zone in 25 cycles.
    # Therefore the active zone must be updated every 24 cycles to prevent the
    # player from interracting with an inactive entity.
    ACTIVITY_UPDATE_WAIT_TIME = 24

    STATE_RUNNING = 0
    STATE_PAUSED = 1
    STATE_CHANGING_STAGES = 2

    def __init__(self):
        super().__init__(self)

        self.player = None

        self.stage_data = None
        self.previous_stage = ''
        self.foreground_layers = []
        self.background_layers = []

        self.refresh_timer = OverYonderRoom.ACTIVITY_UPDATE_WAIT_TIME
        self.running = True

        self.triggered_events = []

        self.camera = Camera(PC.width, PC.height)
        self.background = ParallaxBackground(PC.width, PC.height)

        self.planet = {
            'name': '',
            'outside': False
        }

    def pause(self):
        self.running = True
        for entity in self.entities:
            try:
                entity.sprite.pause()
            except AttributeError:
                pass  # sprite is not of SpriteMap

    def resume(self):
        self.running = False
        for entity in self.entities:
            try:
                entity.sprite.resume()
            except AttributeError:
                pass  # sprite is not of SpriteMap

    def change_stage(self, path):
        self.pause()
        PC.world.change_state(game.worlds.ROOM_TRANSITION_STATE, path)

    def clear(self):
        super().clear()
        self.stage_data = None
        self.background_layers = []
        self.foreground_layers = []

    def close(self):
        self.clear()
        self.stage_data.clear()

    def render(self):
        # Update camera location
        self.camera.update()
        self.camera.translate()

        # Draw stage & entities
        self.background.render(self.camera.x, self.camera.y)

        for layer in self.background_layers:
            peachy.stage.render_layer(self.stage_data, layer)
        for entity in self.entities:
            if entity.visible and entity != self.player:
                entity.render()
        self.player.render()
        for layer in self.foreground_layers:
            peachy.stage.render_layer(self.stage_data, layer)

    def update(self):
        if self.running:
            # Update activity zone
            self.refresh_timer -= 1
            if self.refresh_timer <= 0:
                self.refresh_timer = OverYonderRoom.ACTIVITY_UPDATE_WAIT_TIME
                self._update_activity_zone()

            # Update entities
            if peachy.utils.Key.pressed(config.KEY['INTERACT']):
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
        get_image = peachy.fs.get_image

        if self.planet['name'] == 'OBERON':
            if self.planet['outside']:
                self.background.add_layer(get_image('BACKGROUND_OBERON_OUTER'),
                                          0.5, 0.5, True, True)
            else:
                self.background.add_layer(get_image('BACKGROUND_OBERON_INNER'),
                                          0, 0, True, True)
        elif self.planet['name'] == 'REPTILIA':
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHEST'),
                                      0.25, 0, True, independent=True)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FARTHER'),
                                      0, 0)
            self.background.add_layer(get_image('BACKGROUND_REPTILIA_FAR'),
                                      0.25, 0, True)

    def _update_activity_zone(self):
        arw, arh = OverYonderRoom.ACTIVE_ZONE_SIZE
        arx = (self.player.x + Player.WIDTH / 2) - arw / 2
        ary = (self.player.y + Player.HEIGHT / 2) - arh / 2

        if arx < 0:
            arx = 0
        elif arx > self.stage_data.width - arw:
            arx = self.stage_data.width - arw
        if ary < 0:
            ary = 0
        elif ary > self.stage_data.height - arh:
            ary = self.stage_data.height - arh

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
        if PC.debug:
            print('[LOG] stage path: ' + path)

        # Load map
        previous_stage = ''
        if self.stage_data:
            previous_stage = self.stage_data.name
        stage_data = peachy.stage.load_tiled_tmx('assets/' + path)
        stage_data.name = os.path.basename(stage_data.path)[:-4]

        if 'PLANET' in stage_data.properties:
            self.planet['name'] = stage_data.properties['PLANET'].upper()
        else:
            self.planet['name'] = ''
            if PC.debug:
                print('[WARNING] planet unspecified')
        if 'OUTSIDE' in stage_data.properties:
            self.planet['outside'] = bool(stage_data.properties['OUTSIDE'])
        else:
            self.planet['outside'] = False

        # Reset
        self.clear()

        # Parse layers
        for layer in stage_data.layers:
            name = layer.name[:10]
            if name == 'BACKGROUND':
                self.background_layers.append(layer)
            if name == 'FOREGROUND':
                self.foreground_layers.append(layer)

        # Parse objects
        player_spawn_x = None
        player_spawn_y = None

        for OBJ in stage_data.objects:

            if OBJ.group == 'SOLIDS':

                flip_x = False
                flip_y = False

                if OBJ.is_polygon:
                    x = OBJ.x
                    y = OBJ.y
                    w = 0
                    h = 0
                    flip_x = True

                    for point in OBJ.polygon_points:
                        if point.x != 0:
                            if w != 0:
                                flip_x = False
                            w = abs(point.x)
                        if point.y != 0:
                            h = abs(point.y)
                            if point.y < 0:
                                y -= h

                    self.add(entities.Solid(x, y, w, h, True, flip_x, flip_y))
                else:
                    self.add(entities.Solid(OBJ.x, OBJ.y, OBJ.w, OBJ.h))

            elif OBJ.group == 'OBJECTS':

                obj = None

                if OBJ.name == 'ARROW_TRAP':
                    direction = OBJ.properties['DIRECTION']
                    obj = entities.ArrowTrap(OBJ.x, OBJ.y, direction)

                elif OBJ.name == 'BAT':
                    obj = entities.Bat(OBJ.x, OBJ.y)

                elif OBJ.name == 'BOULDER_SPAWNER':
                    spawn_direction = OBJ.properties['DIRECTION']
                    obj = entities.BoulderSpawner(OBJ.x, OBJ.y, spawn_direction)

                elif OBJ.name == 'BREAKABLE':
                    obj = entities.BreakableTile(OBJ.x, OBJ.y)

                elif OBJ.name == 'BREAKABLE_REINFORCED':
                    obj = entities.BreakableReinforcedTile(OBJ.x, OBJ.y,
                                                           OBJ.w, OBJ.h)

                elif OBJ.name == 'CLIMB':
                    obj = entities.AbsClimbable(OBJ.x, OBJ.y, OBJ.h)

                elif OBJ.name == 'DASHER':
                    initial_direction = OBJ.properties['DIRECTION']
                    obj = entities.Dasher(OBJ.x, OBJ.y, initial_direction)

                elif OBJ.name == 'DOOR':
                    link = OBJ.properties['LINK']

                    obj = entities.Door(OBJ.x, OBJ.y, link)

                    link = os.path.basename(link)[:-4]
                    if link == previous_stage:
                        player_spawn_x = OBJ.x + 3
                        player_spawn_y = OBJ.y + 4

                elif OBJ.name == 'GOBLIN_IMP':
                    obj = entities.GoblinImp(OBJ.x, OBJ.y)

                elif OBJ.name == 'GOBLIN_SWORDSMAN':
                    obj = entities.GoblinSwordsman(OBJ.x, OBJ.y)

                elif OBJ.name == 'ITEM':
                    global_id = OBJ.properties['GLOBAL_ID']
                    item_type = OBJ.properties['ITEM_TYPE']
                    value = OBJ.properties['VALUE']

                    if global_id not in self.player.items:
                        obj = entities.Item(OBJ.x, OBJ.y,
                                            global_id, item_type, value)

                elif OBJ.name == 'MOVING_PLATFORM':
                    start_x = OBJ.x
                    start_y = OBJ.y
                    end_x = OBJ.x + OBJ.polygon_points[1].x
                    end_y = OBJ.y + OBJ.polygon_points[1].y

                    obj = entities.MovingPlatform(start_x, start_y,
                                                  end_x, end_y)

                elif OBJ.name == 'PLATFORM':
                    obj = entities.Platform(OBJ.x, OBJ.y, OBJ.w)

                elif OBJ.name == 'PRESSURE_PLATE':
                    on_activate = OBJ.properties['ON_ACTIVATE']
                    on_deactive = OBJ.properties['ON_DEACTIVATE']
                    obj = entities.PressurePlate(OBJ.x, OBJ.y + 12,
                                                 on_activate,
                                                 on_deactive)

                elif OBJ.name == 'RESOURCE_SLUG_HIVE':
                    orientation = OBJ.properties['ORIENTATION']
                    slug_direction = OBJ.properties['DIRECTION']
                    obj = entities.ResourceSlugHive(OBJ.x, OBJ.y,
                                                    orientation,
                                                    slug_direction)

                elif OBJ.name == 'RETRACTABLE_DOOR':
                    obj = entities.RetractableDoor(OBJ.x, OBJ.y,
                                                   OBJ.w, OBJ.h)

                elif OBJ.name == 'SAVE_POINT':
                    obj = entities.SaveStation(OBJ.x, OBJ.y)

                    if not player_spawn_x and not player_spawn_y:
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                elif OBJ.name == 'SHIP':
                    obj = entities.Ship(OBJ.x, OBJ.y)

                    if previous_stage == 'stage/oberon_landing_site.tmx' or \
                       previous_stage == 'stage/reptilia.tmx':
                        player_spawn_x = OBJ.x
                        player_spawn_y = OBJ.y

                elif OBJ.name == 'SIGN':
                    message = OBJ.properties['MESSAGE']
                    obj = entities.SignPost(OBJ.x, OBJ.y, message)

                elif OBJ.name == 'SPIDER':
                    obj = entities.Spider(OBJ.x, OBJ.y)

                elif OBJ.name == 'SPIKES':
                    obj = entities.Spikes(OBJ.x, OBJ.y, OBJ.w)

                elif OBJ.name == 'SMALL_GOLEM':
                    obj = entities.SmallGolem(OBJ.x, OBJ.y)

                elif OBJ.name == 'SKELETON':
                    obj = entities.Skeleton(OBJ.x, OBJ.y)

                elif OBJ.name == 'SWITCH':
                    on_activate = OBJ.properties['ON_ACTIVATE']
                    obj = entities.Switch(OBJ.x, OBJ.y, on_activate)

                elif OBJ.name == 'WATER':
                    obj = entities.Water(OBJ.x, OBJ.y, OBJ.w, OBJ.h)

                elif OBJ.name == 'WEIGHT':
                    obj = entities.Weight(OBJ.x, OBJ.y)

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
            self.player = entities.Player(0, 0)

        if player_spawn_x is not None and player_spawn_y is not None:
            self.player.x = player_spawn_x
            self.player.y = player_spawn_y
        self.add(self.player)

        if self.stage_data is not None:
            self.stage_data.clear()
        self.stage_data = stage_data

        self.camera.max_width = self.stage_data.width
        self.camera.max_height = self.stage_data.height
        pcx = self.player.x + entities.Player.WIDTH / 2
        pcy = self.player.y + entities.Player.HEIGHT / 2
        self.camera.snap(pcx, pcy, True)

        self._change_background()
        self._update_activity_zone()
