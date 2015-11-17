import heapq
import os
import pygame
import core
from xml.dom.minidom import parseString
from core import AssetManager, GC, Graphics


def a_star_search(grid, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()

        if current == goal:
            break

        for neighbour in grid.neighbours(current):
            new_cost = cost_so_far[current] + grid.cost(current, neighbour)
            if neighbour not in cost_so_far or new_cost < cost_so_far[neighbour]:
                cost_so_far[neighbour] = new_cost
                priority = new_cost + a_star_heuristic(goal, neighbour)
                frontier.put(neighbour, priority)
                came_from[neighbour] = current

    # return came_from, cost_so_far
    current = goal
    path = [current]
    while current != start:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def a_star_heuristic(a, b):
    x1, y1 = a
    x2, y2 = b
    return abs(x1 - x2) + abs(y1 - y2)


def splice_image(image, frame_width, frame_height, margin_x=0, margin_y=0):
    x = 0
    y = 0

    sub_images = []

    src_width, src_height = image.get_size()

    while x + frame_width <= src_width and y + frame_height <= src_height:
        crop = pygame.Surface((frame_width, frame_height), flags=pygame.SRCALPHA)
        crop.blit(image, (0, 0), (x, y, frame_width, frame_height))

        sub_images.append(crop)

        x += frame_width + margin_x
        if x + frame_width > src_width:
            x = 0
            y += frame_height + margin_y

    return sub_images


def hex_to_rgb(val):
    # (#ffffff) -> (255, 255, 255)
    val = val.lstrip('#')
    lv = len(val)
    # Hell if I know how this works...
    return tuple(int(val[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def open_xml(path):
    try:
        xml_file = open(os.path.join(AssetManager.assets_path, path), 'r')
        data = xml_file.read()
        xml_file.close()
        return parseString(data)
    except IOError:
        print '[ERROR] could not load xml file: ' + path


class Camera(object):

    # TODO add smooth scrolling
    # TODO add shake
    
    def __init__(self, view_width, view_height):
        self.x = 0
        self.y = 0

        self.view_width = view_width
        self.view_height = view_height
        self.max_width = -1
        self.max_height = -1

        self.destination_x = 0
        self.destination_y = 0

    def center_on(self, center_x, center_y):
        self.x = center_x - self.view_width / 2
        self.y = center_y - self.view_height / 2

        if self.x < 0:
            self.x = 0
        elif self.x + self.view_width > self.max_width:
            self.x = self.max_width - self.view_width

        if self.y < 0:
            self.y = 0
        elif self.y + self.view_height > self.max_height:
            self.y = self.max_height - self.view_height

    def translate(self):
        Graphics.translate(self.x, self.y)

    def update(self):
        # TODO panning
        return


class Music(object):

    def __init__(self, source):
        self.source = source
        self.loaded = False
        self.paused = False
        self.playing = False

    def load(self):
        pygame.mixer.music.load(self.source)
        self.loaded = True
        self.paused = False
        self.playing = False

    def pause(self):
        if not self.loaded:
            return
        pygame.mixer.music.pause()
        self.paused = True
        self.playing = False

    def play(self):
        if not self.loaded:
            return
        pygame.mixer.music.play()
        self.paused = False
        self.playing = True

    def resume(self):
        if not self.loaded:
            return
        pygame.mixer.music.unpause()
        self.paused = False
        self.playing = True

    def stop(self):
        if not self.loaded:
            return
        pygame.mixer.music.stop()
        self.paused = False
        self.playing = False


class ParallaxBackground(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
    
    def add_layer(self, image, velocity_x, velocity_y, tile_horizontally=False, tile_vertically=False, independent=False):
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
        def __init__(self, parent, image, velocity_x, velocity_y, tile_x, tile_y, independent):
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


class PriorityQueue(object):
    
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class SoundEffect(object):

    def __init__(self, sound):
        self.sound = sound
        self.channel = None

    def play(self):
        if self.channel:
            if self.channel.get_sound() == self.sound:
                self.channel.stop()
        self.channel = self.sound.play()

    def playing(self):
        if self.channel:
            if self.channel.get_sound() == self.sound:
                return self.channel.get_busy()
        else:
            return False

    def stop(self):
        if self.channel:
            if self.channel.get_sound() == self.sound:
                self.channel.stop()
                self.channel = None



class Sprite(object):
    
    def __init__(self, source, origin_x=0, origin_y=0):
        self.source = source

        self.origin_x = origin_x
        self.origin_y = origin_y

        self.flipped_x = False
        self.flipped_y = False

    def render(self, x, y):
        x -= self.origin_x
        y -= self.origin_y

        args = 0

        if self.flipped_x:
            args = args | Graphics.FLIP_X
        if self.flipped_y:
            args = args | Graphics.FLIP_Y
        Graphics.draw_image(self.source, x, y, args)



class SpriteMap(object):

    def __init__(self, source, frame_width, frame_height, margin_x=0, margin_y=0, origin_x=0, origin_y=0):
        self.source = source

        self.name = ''
        self.flipped_x = False
        self.flipped_y = False
        self.paused = False

        self.animations = dict()
        self.frames = []

        self.current_animation = None
        self.current_frame = -1
        self.time_remaining = 0

        self.callback = None

        self.frames = splice_image(source, frame_width, frame_height, margin_x, margin_y)
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.origin_x = origin_x
        self.origin_y = origin_y

    def add(self, name, frames, frame_rate=0, loops=False, callback=None):
        animation = {
            "frames": frames,
            "frame_rate": frame_rate,
            "loops": loops,
            "callback": callback
        }
        self.animations[name] = animation

    def pause(self):
        self.paused = True

    def play(self, anim_name, flip_x=False, flip_y=False):
        if anim_name in self.animations:
            self.name = anim_name
            self.flipped_x = flip_x
            self.flipped_y = flip_y
            self.paused = False

            self.current_animation = self.animations[anim_name]
            self.current_frame = 0
            self.time_remaining = self.current_animation['frame_rate']
            self.callback = self.current_animation['callback']

    def render(self, x, y):
        self.step()

        x -= self.origin_x
        y -= self.origin_y

        if not self.paused:
            frame = self.current_animation['frames'][self.current_frame]
            args = 0
            
            if frame != -1:
                if self.flipped_x:
                    args = args | Graphics.FLIP_X
                if self.flipped_y:
                    args = args | Graphics.FLIP_Y
                Graphics.draw_image(self.frames[frame], x, y, args)

    def resume(self):
        self.paused = False

    def step(self):
        if not self.paused:
            if self.time_remaining > 0:     # only decrement when there is a running timer
                self.time_remaining -= 1
                
                if self.time_remaining <= 0:    # if timer has expired, move to the next frame
                    self.current_frame += 1

                    if self.current_frame >= len(self.current_animation['frames']):

                        # If on the final frame, either loop or remain static on
                        # the final frame
                        
                        if self.current_animation['loops']:
                            self.current_frame = 0
                            self.time_remaining = self.current_animation['frame_rate']
                        else:
                            self.current_frame -= 1
                            self.time_remaining = 0
                            if self.callback is not None:
                                self.callback()
                    else:
                        self.time_remaining = self.current_animation['frame_rate']

    def stop(self):
        self.paused = True
        self.current_frame = 0
        self.time_remaining = self.current_animation['frame_rate']


class Stage(object):

    def __init__(self):
        self.width = 0
        self.height = 0
        self.tile_width = 0
        self.tile_height = 0

        # TODO make layers in dict where layer_name is key
        self.layers = []
        self.objects = []
        self.tilesets = []
        self.tileset_images = []

        self.properties = {}

        self.path = ''

    def clear(self):
        del self.layers[:]
        del self.tilesets[:]
        del self.tileset_images[:]
        del self.objects[:]
        self.properties.clear()

    def load_tiled(self, path):
        xml = open_xml(path)
        stage_raw = xml.getElementsByTagName('map')[0]

        # Load base attributes

        self.tile_width = int(stage_raw.getAttribute('tilewidth'))
        self.tile_height = int(stage_raw.getAttribute('tileheight'))
        self.width = int(stage_raw.getAttribute('width')) * self.tile_width
        self.height = int(stage_raw.getAttribute('height')) * self.tile_height
        self.path = path

        map_properties = xml.getElementsByTagName('properties')
        if map_properties:
            for prop in map_properties[0].getElementsByTagName('property'):
                property_name = prop.getAttribute('name')
                property_value = prop.getAttribute('value')
                self.properties[property_name] = property_value

        # Load tilesets

        for tileset_raw in stage_raw.getElementsByTagName('tileset'):

            tileset = self._Tileset()
            tileset.name = tileset_raw.getAttribute('name')
            tileset.firstGID = int(tileset_raw.getAttribute('firstgid'))
            tileset.tilewidth = int(tileset_raw.getAttribute('tilewidth'))
            tileset.tileheight = int(tileset_raw.getAttribute('tileheight'))

            tileset.image = AssetManager.get_image(tileset.name)
            if tileset.image is None:
                image_raw = tileset_raw.getElementsByTagName('image')[0]
                source = image_raw.getAttribute('source')
                tileset.image = AssetManager.load_image(tileset.name, source)

            self.tileset_images += splice_image(tileset.image,
                                                tileset.tilewidth,
                                                tileset.tileheight)

            properties = tileset_raw.getElementsByTagName('property')
            for prop in properties:
                property_name = prop.getAttribute('name')
                property_value = prop.getAttribute('value')
                tileset.properties[property_name] = property_value

            self.tilesets.append(tileset)

        # Load layers and tiles

        for layer_raw in stage_raw.getElementsByTagName('layer'):

            layer = self._Layer()
            layer.name = layer_raw.getAttribute('name')
            layer.width = int(layer_raw.getAttribute('width')) * self.tile_width
            layer.height = int(layer_raw.getAttribute('height')) * self.tile_height

            tile_x = 0
            tile_y = 0

            for tile_raw in layer_raw.getElementsByTagName('tile'):
                tile_id = int(tile_raw.getAttribute('gid'))

                if tile_id > 0:
                    tile = self._Tile()
                    tile.x = tile_x
                    tile.y = tile_y
                    tile.gid = tile_id
                    layer.tiles.append(tile)

                tile_x += self.tile_width
                if tile_x == layer.width:
                    tile_x = 0
                    tile_y += self.tile_height

            properties = layer_raw.getElementsByTagName('property')
            for prop in properties:
                property_name = prop.getAttribute('name')
                property_value = prop.getAttribute('value')
                layer.properties[property_name] = property_value

            self.layers.append(layer)

        # Load objects

        for object_group in stage_raw.getElementsByTagName('objectgroup'):

            group = object_group.getAttribute('name')

            for object_raw in object_group.getElementsByTagName('object'):

                obj = self._Object()
                obj.group = group
                obj.name = object_raw.getAttribute('name')
                obj.x = int(object_raw.getAttribute('x'))
                obj.y = int(object_raw.getAttribute('y'))

                polygon = object_raw.getElementsByTagName('polygon')
                polyline = object_raw.getElementsByTagName('polyline')
                if polygon:
                    obj.is_polygon = True
                    obj.polygon_points = self.parse_tiled_polygon(polygon)
                elif polyline:
                    obj.is_polygon = True
                    obj.polygon_points = self.parse_tiled_polygon(polyline)
                else:
                    try:
                        obj.w = int(object_raw.getAttribute('width'))
                        obj.h = int(object_raw.getAttribute('height'))
                    except ValueError:
                        obj.w = 0
                        obj.h = 0


                properties = object_raw.getElementsByTagName('property')
                for prop in properties:
                    property_name = prop.getAttribute('name')
                    property_value = prop.getAttribute('value')
                    obj.properties[property_name] = property_value

                self.objects.append(obj)

    def parse_tiled_polygon(self, polygon):
        points = []
        points_raw = polygon[0].getAttribute('points').split()
        for raw_point in points_raw:
            points.append(map(int, raw_point.split(',')))
        return points

    # TODO improve map render performance
    #
    # Modify tiles to directly reference their image instead of holding a gid.
    # Don't try to draw every image

    def render(self):
        for layer in self.layers:
            for tile in layer.tiles:
                tile_image = self.tileset_images[tile.gid]
                Graphics.draw_image(tile_image, tile.x, tile.y)

    def render_layer(self, layer):
        for tile in layer.tiles:
            tile_image = self.tileset_images[tile.gid - 1]
            Graphics.draw_image(tile_image, tile.x, tile.y)

    def render_layer_name(self, layer_name):
        for layer in self.layers:
            if layer.name == layer_name:
                self.render_layer(layer)
                break

    class _Layer(object):
        def __init__(self):
            self.name = ''
            self.width = 0
            self.height = 0
            self.tiles = []
            self.properties = {}

        def __repr__(self):
            return "<Tiled Layer> " + self.name

    class _Object(object):
        def __init__(self):
            self.group = ''
            self.name = ''
            self.x = 0
            self.y = 0
            self.w = 0
            self.h = 0
            self.is_polygon = False
            self.polygon_points = []
            self.properties = {}

    class _Tile(object):
        def __init__(self):
            self.x = 0
            self.y = 0
            self.gid = 0

    class _Tileset(object):
        def __init__(self):
            self.name = ''
            self.firstgid = 0
            self.tilewidth = 0
            self.tileheight = 0
            self.properties = {}


class StagePathfindingGrid(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.obstructions = []

    def in_bounds(self, location):
        x, y = location
        if 0 <= x < self.width and 0 <= y < self.width:
            return True
        return False

    def cost(self, location, destination):
        x1, y1 = location
        x2, y2 = destination

        if (x1 - x2) == 0 or (y1 - y2) == 0:
            return 1
        else:
            return 1.5

    def passable(self, location):
        return location not in self.obstructions

    def neighbours_dep(self, location):
        x, y = location
        results = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        return results

    def neighbours(self, location):
        x, y = location
        results = []

        for translation in [(0, 1), (0, -1), (1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1)]:

            trans_x, trans_y = translation
            destination = (x + trans_x, y + trans_y)

            if self.passable(destination):

                if trans_x != 0 and trans_y != 0:
                    border_one = (x + trans_x, y)
                    border_two = (x, y + trans_y)
                    if self.passable(border_one) and self.passable(border_two):
                        results.append(destination)
                else:
                    results.append(destination)

        results = filter(self.in_bounds, results)
        return results
