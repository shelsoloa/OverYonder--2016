import peachy
from .enemy import Enemy
from .utility import drop, solid_above, solid_below, solid_left, solid_right, \
    collision_resolution


class ResourceSlug(Enemy):

    SPEED = 1

    def __init__(self, parent, x, y, dx, dy):
        super().__init__(self, x, y)
        self.parent = parent
        self.width = 8
        self.height = 8

        self.health = 1
        self.dx = dx
        self.dy = dy

        self.moving = False
        self.rotation = 4

    def destroy(self):
        if self.parent:
            self.parent.spawn_count -= 1
        drop(self.x, self.y)
        Enemy.destroy(self)

    def render(self):
        peachy.graphics.set_color(255, 0, 125)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        self.rotation -= 1
        if self.rotation <= 0:
            if self.moving:
                self.rotation = 40
            else:
                self.rotation = 20
            self.moving = not self.moving

        if self.moving:
            temp_x += ResourceSlug.SPEED * self.dx
            temp_y += ResourceSlug.SPEED * self.dy

            if self.dx != 0:
                if not solid_above(self, temp_x, temp_y) and \
                   not solid_below(self, temp_x, temp_y):
                    self.dx = 0
                    if solid_above(self):
                        self.dy = -1
                    elif solid_below(self):
                        self.dy = 1
                elif self.dx == -1 and solid_left(self) or \
                        self.dx == 1 and solid_right(self):
                    temp_x = self.x
                    self.dx = 0
                    if solid_above(self):
                        self.dy = 1
                    elif solid_below(self):
                        self.dy = -1
            elif self.dy != 0:
                if not solid_left(self, temp_x, temp_y) and \
                   not solid_right(self, temp_x, temp_y):
                    self.dy = 0
                    if solid_left(self):
                        self.dx = -1
                    elif solid_right(self):
                        self.dx = 1

        _, self.x, self.y, _, _ = collision_resolution(self, temp_x, temp_y)

        if self.collides(self.container.get_name('player')):
            self.container.get_name('player').take_damage(self, 1)


class ResourceSlugHive(peachy.Entity):

    SPAWN_CAP = 5
    SPAWN_TIME = 135

    def __init__(self, x, y, facing_direction, slug_direction):
        super().__init__(x, y)
        self.width = 16
        self.height = 16

        self.facing_direction = facing_direction
        if facing_direction == 'LEFT' or facing_direction == 'RIGHT':
            self.width = 8
        else:
            self.height = 8

        self.slug_direction_x = 0
        self.slug_direction_y = 0
        if slug_direction == 'UP':
            self.slug_direction_y = -1
        elif slug_direction == 'DOWN':
            self.slug_direction_y = 1
        elif slug_direction == 'LEFT':
            self.slug_direction_x = -1
        elif slug_direction == 'RIGHT':
            self.slug_direction_x = 1

        self.spawn_timer = ResourceSlugHive.SPAWN_TIME / 2
        self.spawn_count = 0

    def render(self):
        peachy.graphics.set_color(200, 64, 64)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
        elif self.spawn_count < ResourceSlugHive.SPAWN_CAP:
            slug = ResourceSlug(self, self.x, self.y,
                                self.slug_direction_x,
                                self.slug_direction_y)
            self.container.add(slug)
            self.spawn_count += 1
            self.spawn_timer = ResourceSlugHive.SPAWN_TIME
