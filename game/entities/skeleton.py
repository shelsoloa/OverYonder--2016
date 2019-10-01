import peachy
from .enemy import Enemy
from .player import Player
from .projectile import Projectile
from .utility import GRAVITY, MAX_GRAVITY, collision_resolution, solid_below


class Skeleton(Enemy):

    BONE_COOLDOWN = 90
    SPEED = Player.WALK_MAX_SPEED + 0.5
    SAFE_DISTANCE = 54

    def __init__(self, x, y):
        Enemy.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.health = 3

        self.bone_cooldown = Skeleton.BONE_COOLDOWN

        self.sprite = peachy.fs.get_image('SKELETON')

    def render(self):
        if self.facing_x == 1:
            peachy.graphics.draw(self.sprite, self.x, self.y)
        else:
            peachy.graphics.draw(self.sprite, self.x, self.y,
                                 peachy.graphics.FLIP_X)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        player = self.container.get_name('player')
        if player is None:
            return

        distance_from_player = abs(player.x - self.x)

        # Throw Bone
        self.bone_cooldown -= 1
        if self.bone_cooldown == 0:
            self.container.add(Skeleton.Bone(self, player))
            self.bone_cooldown = Skeleton.BONE_COOLDOWN

        # Movement
        if distance_from_player < Skeleton.SAFE_DISTANCE:  # Move away
            if solid_below(self, temp_x - Skeleton.SPEED, self.y) and \
               temp_x < player.x:
                temp_x -= Skeleton.SPEED
                self.facing_x = -1
            elif solid_below(self, temp_x + Skeleton.SPEED, self.y) and \
                 temp_x > player.x:
                temp_x += Skeleton.SPEED
                self.facing_x = 1

        elif distance_from_player > Skeleton.Bone.MAX_DISTANCE:  # Move towards
            if solid_below(self, temp_x + Skeleton.SPEED, self.y) and \
               temp_x < player.x:
                temp_x += Skeleton.SPEED
                self.facing_x = -1
            elif solid_below(self, temp_x - Skeleton.SPEED, self.y) and \
                 temp_x > player.x:
                temp_x -= Skeleton.SPEED
                self.facing_x = 1

        if self.velocity_x != 0:
            self.velocity_x += 0.25 if self.velocity_x < 0 else -0.25

        # Gravity
        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y, = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(player, self.x, self.y):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 2)

    class Bone(Projectile):

        DURATION = 45
        POWER = 1
        WIDTH = 8
        HEIGHT = 8
        MAX_DISTANCE = 128

        def __init__(self, parent, target):

            x = parent.x + parent.width / 2 - Skeleton.Bone.WIDTH / 2
            y = parent.y + parent.width / 2 - Skeleton.Bone.HEIGHT / 2

            super().__init__(parent, x, y, 0, 0, 0)

            self.width = Skeleton.Bone.WIDTH
            self.height = Skeleton.Bone.HEIGHT

            px = target.x + target.width / 2
            py = target.y + target.height / 2
            if abs(self.x - px) > Skeleton.Bone.MAX_DISTANCE:
                if target.x < self.x:
                    px = self.x - Skeleton.Bone.MAX_DISTANCE
                else:
                    px = self.x + Skeleton.Bone.MAX_DISTANCE

            self.velocity_x = float(px - self.x) / Skeleton.Bone.DURATION
            self.velocity_y = \
                float((py + 0.5 * GRAVITY * Skeleton.Bone.DURATION *
                      Skeleton.Bone.DURATION - self.y) /
                      Skeleton.Bone.DURATION) * -1

        def render(self):
            peachy.graphics.set_color(255, 255, 255)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            player = self.collides_name('player')
            if player is not None:
                player.take_damage(self, Skeleton.Bone.POWER)
                self.destroy()

        def move(self):
            self.velocity_y += GRAVITY
            self.x += self.velocity_x
            self.y += self.velocity_y

            if abs(self.velocity_y) > MAX_GRAVITY:
                if self.velocity_y < 0:
                    self.velocity_y = -MAX_GRAVITY
                else:
                    self.velocity_y = MAX_GRAVITY
