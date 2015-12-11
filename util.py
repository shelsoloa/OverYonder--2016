import config
import core
import common
from core import GC, AssetManager, Graphics, Input

class Camera(common.Camera):
    # TODO add shake
    CENTER_LOCKED = 'CENTER'
    LEFT_LOCKED = 'LEFT'
    RIGHT_LOCKED = 'RIGHT'
    MOVING = 'MOVING'
    Y_DELAY = 8

    def __init__(self, view_width, view_height):
        common.Camera.__init__(self, view_width, view_height, True, 1.5)
        self.status = Camera.CENTER_LOCKED
        self.previous_fx = 0
        self.y_delay = -1
    
    def update(self):
        player = core.ENTITY_ROOM.player
        pcx = player.x + player.width / 2
        pcy = player.y + player.height / 2

        OFFSET = self.view_width / 5
        ALIGN_LEFT = pcx - OFFSET * 3
        ALIGN_RIGHT = pcx - OFFSET * 2

        if self.previous_fx != player.facing_x:
            self.status = Camera.MOVING
            if player.facing_x == -1:
                self.target = Camera.LEFT_LOCKED
            elif player.facing_x == 1:
                self.target = Camera.RIGHT_LOCKED
            else:
                self.target = Camera.CENTER_LOCKED
            self.previous_fx = player.facing_x

        # Align camera vertically
        if self.status == Camera.MOVING:
            target_x = 0
            if self.target == Camera.LEFT_LOCKED:
                target_x = ALIGN_LEFT
            elif self.target == Camera.RIGHT_LOCKED:
                target_x = ALIGN_RIGHT

            if player.velocity_x != 0:
                self.pan_x(target_x, False, abs(player.velocity_x) + abs(player.velocity_x * 0.25))
            else:
                self.pan_x(target_x)

            if self.x == target_x:
                self.status = self.target

        elif self.status == Camera.CENTER_LOCKED:
            self.snap_x(pcx, True)

        elif self.status == Camera.LEFT_LOCKED:
            self.snap_x(ALIGN_LEFT)

        elif self.status == Camera.RIGHT_LOCKED:
            self.snap_x(ALIGN_RIGHT)

        # Align camera horizontally
        THIRD_HEIGHT = self.view_height / 3
        target_y = pcy - self.view_height / 2

        looking_up = Input.down(config.KEY['UP'])
        looking_down = Input.down(config.KEY['DOWN'])

        if looking_down or looking_up:
            if self.y_delay is None:
                self.y_delay = Camera.Y_DELAY
            elif self.y_delay <= 0:
                if looking_down:
                    target_y = pcy - THIRD_HEIGHT
                elif looking_up:
                    target_y = pcy - THIRD_HEIGHT * 2
            else:
                self.y_delay -= 1
        elif self.y_delay is not None:
            self.y_delay = None
        
        if pcy > self.y + THIRD_HEIGHT * 2:
            target_y = pcy - THIRD_HEIGHT * 2
            self.snap_y(target_y)
        elif pcy < self.y + THIRD_HEIGHT:
            target_y = pcy - THIRD_HEIGHT
            self.snap_y(target_y)

        self.pan_y(target_y, speed=1)


class GUI(object):
    # TODO move to new module

    HEALTH_POINT = None
    HEALTH_EMPTY = None

    @staticmethod
    def init():
        GUI.HEALTH_POINT = AssetManager.get_image('HUD_HEALTH_FULL')
        GUI.HEALTH_EMPTY = AssetManager.get_image('HUD_HEALTH_EMPTY')

    @staticmethod
    def draw_HUD():
        player = core.ENTITY_ROOM.player
        for i in xrange(player.max_health):
            if i >= player.health:
                img = GUI.HEALTH_EMPTY
            else:
                img = GUI.HEALTH_POINT
            Graphics.draw_image(img, 8 + 4 * i, 12)


class ParallaxBackground(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
    
    def add_layer(self, image, velocity_x, velocity_y, 
                  tile_horizontally=False, tile_vertically=False, 
                  independent=False):
        layer = ParallaxBackground.Layer(self, image, velocity_x, velocity_y, tile_horizontally, tile_vertically, independent)
        self.layers.append(layer)

    def clear(self):
        self.layers = []
    
    def render(self, camera_x, camera_y):
        for layer in self.layers:
            image = layer.image

            if layer.velocity_x == 0 and layer.velocity_y == 0:
                layer.render(camera_x, camera_y)
            else:
                if layer.independent:
                    layer.move_independent()
                else:
                    layer.move_camera_dependent(camera_x, camera_y)
                layer.render(camera_x, camera_y)

    class Layer():
        def __init__(self, parent, image, velocity_x, velocity_y, 
                     tile_x, tile_y, independent):
            self.parent = parent
            self.image = image
            self.size = image.get_size()
            self.width, self.height = self.size
            self.velocity_x = velocity_x
            self.velocity_y = velocity_y
            self.tile_x = tile_x
            self.tile_y = tile_y
            self.independent = independent

            self.x = 0
            self.y = 0

        def move_independent(self):
            self.x += self.velocity_x
            self.x = self.x % self.width
            self.y += self.velocity_y
            self.y = self.y % self.height

        def move_camera_dependent(self, camera_x, camera_y):
            if self.velocity_x != 0:
                self.x = ((camera_x * self.velocity_x - GC.view_size[0]) % self.width) * -1
            if self.velocity_y != 0:
                self.y = ((camera_y * self.velocity_y- GC.view_size[1]) % self.height) * -1

        def render(self, camera_x, camera_y):
            if self.tile_x and self.tile_y:
                offset_x = camera_x - self.width
                while offset_x < self.parent.width + self.width + camera_x:
                    offset_y = camera_y - self.height
                    while offset_y < self.parent.height + self.height + camera_y:
                        Graphics.draw_image(self.image, self.x + offset_x, self.y + offset_y)
                        offset_y += self.height
                    offset_x += self.width
            elif self.tile_x:
                offset_x = camera_x - self.width
                while offset_x < self.parent.width + self.width + camera_x:
                    Graphics.draw_image(self.image, self.x + offset_x, camera_y)
                    offset_x += self.width
            elif self.tile_y:
                offset_y = camera_y - self.height
                while offset_y < self.parent.height + self.height + camera_y:
                    Graphics.draw_image(self.image, camera_x, self.y + offset_y)
                    offset_y += self.height
            else:
                x = self.x + camera_x
                y = self.y + camera_y
                Graphics.draw_image(self.image, x, y)

