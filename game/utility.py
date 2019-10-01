import math
import peachy
from peachy import PC

from game import config
import heapq
import pickle


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
            if neighbour not in cost_so_far or \
               new_cost < cost_so_far[neighbour]:
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


def save(data, file_name):
    _file = None
    try:
        _file = open(file_name, 'wb')
        pickle.dump(data, _file)
        _file.close()
    except (IOError, pickle.PickleError):
        if _file is not None:
            _file.close()
        raise


def load(file_name):
    _file = None
    saved_data = None
    try:
        _file = open(file_name, 'rb')
        saved_data = pickle.load(_file)
        _file.close()
    except (IOError, pickle.PickleError):
        if _file is not None:
            _file.close()
        raise
    return saved_data


class Camera(peachy.utils.Camera):
    # TODO add shake
    CENTER_LOCKED = 'CENTER'
    LEFT_LOCKED = 'LEFT'
    RIGHT_LOCKED = 'RIGHT'
    MOVING = 'MOVING'
    Y_DELAY = 8

    def __init__(self, view_width, view_height):
        super().__init__(view_width, view_height, 1.5)
        self.status = Camera.CENTER_LOCKED
        self.previous_fx = 0
        self.y_delay = -1

    def update(self):
        player = PC.world.stage.player
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
                self.pan_x(target_x, False,
                           abs(player.velocity_x) +
                           abs(player.velocity_x * 0.25))
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

        looking_up = peachy.utils.Key.down(config.KEY['UP'])
        looking_down = peachy.utils.Key.down(config.KEY['DOWN'])

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


class CheckpointData(object):
    def __init__(self):
        self.stage = ''
        self.gadget = ''
        self.keys = []  # TODO
        self.open_doors = []  # TODO

    @staticmethod
    def generate(stage):
        checkpoint = CheckpointData()
        checkpoint.stage = stage.stage_data.path
        checkpoint.gadget = stage.player.gadget.name
        checkpoint.open_doors = []
        return checkpoint


class Graphic(peachy.Entity):
    ''' Display an image for a duration, then deletes it '''
    def __init__(self, x, y, image, duration):
        peachy.Entity.__init__(self, x, y)
        self.image = image
        self.duration = duration

    def render(self):
        peachy.graphics.draw(self.image, self.x, self.y)

    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.destroy()


class ParallaxBackground(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []

    def add_layer(self, image, velocity_x, velocity_y,
                  tile_horizontally=False, tile_vertically=False,
                  independent=False):
        layer = ParallaxBackground.Layer(self, image, velocity_x, velocity_y,
                                         tile_horizontally, tile_vertically,
                                         independent)
        self.layers.append(layer)

    def clear(self):
        self.layers = []

    def render(self, cam_x, cam_y):
        for layer in self.layers:
            if layer.velocity_x == 0 and layer.velocity_y == 0:
                layer.render(cam_x, cam_y)
            else:
                if layer.independent:
                    layer.move_independent()
                else:
                    layer.move_cam_dependent(cam_x, cam_y)
                layer.render(cam_x, cam_y)

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

        def move_cam_dependent(self, cam_x, cam_y):
            if self.velocity_x != 0:
                self.x = ((cam_x * self.velocity_x - PC.width) % self.width) * -1
            if self.velocity_y != 0:
                self.y = ((cam_y * self.velocity_y - PC.height) % self.height) * -1

        def render(self, cam_x, cam_y):
            if self.tile_x and self.tile_y:
                offset_x = cam_x - self.width
                while offset_x < self.parent.width + self.width + cam_x:
                    offset_y = cam_y - self.height
                    while offset_y < self.parent.height + self.height + cam_y:
                        peachy.graphics.draw(self.image, self.x + offset_x,
                                             self.y + offset_y)
                        offset_y += self.height
                    offset_x += self.width
            elif self.tile_x:
                offset_x = cam_x - self.width
                while offset_x < self.parent.width + self.width + cam_x:
                    peachy.graphics.draw(self.image, self.x + offset_x, cam_y)
                    offset_x += self.width
            elif self.tile_y:
                offset_y = cam_y - self.height
                while offset_y < self.parent.height + self.height + cam_y:
                    peachy.graphics.draw(self.image, cam_x, self.y + offset_y)
                    offset_y += self.height
            else:
                x = self.x + cam_x
                y = self.y + cam_y
                peachy.graphics.draw(self.image, x, y)


class ParallaxBG(object):

    def __init__(self, max_width, max_height):
        self.width = max_width
        self.height = max_height

        self.x = None
        self.y = None

        self.layers = []

    def create_layer(self, image, velocity, tile_x, tile_y):
        layer = ParallaxBG._Layer(self, image, velocity, tile_x, tile_y)
        self.layers.append(layer)
        return layer

    def render(self, x, y):
        for layer in self.layers:
            layer.move()
            layer.render(x, y)

    class _Layer(object):
        def __init__(self, parent, image, velocity, tile_x, tile_y):
            self.image = image
            self.width, self.height = self.image.get_size()
            self.velocity = velocity

            self.x = 0
            self.y = 0

            self.tile_x = tile_x
            self.tile_y = tile_y

            self.max_x = parent.width
            self.max_y = parent.height

        def move(self):
            self.x = (self.x + self.velocity.x) % self.width
            self.y = (self.y + self.velocity.y) % self.height

        def render(self, view_x, view_y, invert=False):
            if self.tile_x and self.tile_y:
                off_x = view_x - self.width
                while off_x < self.max_x + view_x + self.width:
                    off_y = view_y - self.height
                    while off_y < self.max_y + view_y + self.height:
                        peachy.graphics.draw(self.image, self.x + off_x,
                                             self.y + off_y)
                        off_y += self.height
                    off_x += self.width

            elif self.tile_x:
                off_x = view_x - self.width
                while off_x < self.max_x + view_x + self.width:
                    peachy.graphics.draw(self.image, self.x + off_x, view_y)
                    off_x += self.width

            elif self.tile_y:
                off_y = view_y - self.height
                while off_y < self.max_y + view_y + self.height:
                    peachy.graphics.draw(self.image, view_x, self.y + off_y)
                    off_y += self.width

            else:
                x = self.x + view_x
                y = self.y + view_y
                peachy.graphics.draw(self.image, x, y)


class Particle(peachy.Entity):
    """ NOTE: Remove from container.entities and add to container.particles
    to speed up get_group and get_name """

    def __init__(self, x, y, speed=1, angle=0, radius=0, lifespan=1,
                 color='#000000'):
        super().__init__(x, y)
        self.speed = speed
        self.angle = angle
        self.radius = radius
        self.lifespan = peachy.utils.Counter(0, lifespan)
        self.color = color

    def render(self):
        peachy.graphics.set_color(*self.color)
        peachy.graphics.draw_circle(self.x, self.y, self.radius)

    def update(self):
        if self.lifespan.advance():
            self.destroy()
        else:
            self.x += math.sin(self.angle) * self.speed
            self.y -= math.cos(self.angle) * self.speed


class PriorityQueue(object):
    # TODO This has something to do with A* but I don't know what.
    # I want to remove it.

    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class Rect(peachy.Entity):
    def __init__(self, x, y, width=None, height=None):
        if width is None or height is None:
            width = x
            height = y
            x = 0
            y = 0
        peachy.Entity.__init__(self, x, y)
        self.width = width
        self.height = height
