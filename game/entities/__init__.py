import peachy
from peachy import PC
from peachy.graphics import splice

from game.config import SAVE_FILE

from .enemy import Enemy
from .player import Player
from .projectile import Projectile
from .skeleton import Skeleton
from .goblin import *
from .utility import GRAVITY, MAX_GRAVITY, collision_resolution, \
    xcollides_solid, solid_below

try:
    from game.worlds import DECISION_STATE, MESSAGE_STATE, SHIP_STATE
except ImportError:
    pass

# TODO player cannot be hurt while punching
# TODO add enemy attack abstract base class?


def display_choice(message, callback):
    PC.world.change_state(DECISION_STATE, message, callback)


def display_message(message):
    PC.world.change_state(MESSAGE_STATE, message)


class AbsClimbable(peachy.Entity):

    def __init__(self, x, y, height):
        super().__init__(x, y)
        self.group = 'climbable'

        self.width = 16
        self.height = height

        self.bottom = self.y + height

    def render(self):
        peachy.graphics.set_color(0, 255, 0)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)


class ArrowTrap(peachy.Entity):

    ARROW_COOLDOWN = 90

    def __init__(self, x, y, direction):
        super().__init__(x, y)
        self.solid = True

        self.width = 16
        self.height = 16

        self.direction_x = 0
        if direction == 'LEFT':
            self.direction_x = -1
        else:
            self.direction_x = 1

        self.arrow_timer = 0

    def render(self):
        peachy.graphics.set_color(210, 180, 140)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def shoot(self):
        self.arrow_timer = ArrowTrap.ARROW_COOLDOWN
        arrow = ArrowTrap.Arrow(self, self.direction_x)
        self.container.add(arrow)

    def update(self):
        if self.arrow_timer > 0:
            self.arrow_timer -= 1
        else:
            player = self.container.get_name('player')

            pcy = player.y + (player.height / 2)
            scy = self.y + (self.height / 2)

            distance = abs(pcy - scy)
            if distance <= 32:
                self.shoot()

    '''
    in_sights = player.y + player.height > self.y and player.y < self.bottom

    if in_sights:
        if self.direction_x == -1 and \
           player.x + player.width < self or \
           self.direction_x == 1 and \
           player.x > self.x + self.width:
            self.shoot()
    '''

    class Arrow(Projectile):

        SPEED = 5
        LIFESPAN = -1

        def __init__(self, parent, direction):
            ax = parent.x + direction * parent.width
            super().__init__(parent, ax, parent.y + 6, direction, 0,
                             ArrowTrap.Arrow.SPEED,
                             ArrowTrap.Arrow.LIFESPAN)
            self.width = 10
            self.height = 4

        def render(self):
            peachy.graphics.set_color(255, 0, 0)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collision = self.collides_name('player')
            if collision:
                collision.take_damage(self, 1)
                self.destroy()

            collision = xcollides_solid(self)
            if len(collision) > 0:
                self.destroy()


class Bat(Enemy):

    ACCEL_SPEED = 0.05
    SPEED = 0.75

    def __init__(self, x, y):
        Enemy.__init__(self, x, y)
        self.width = 8
        self.height = 8
        self.health = 2
        self.invincibility_timer = 0

    def render(self):
        peachy.graphics.set_color(100, 100, 255)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        # TODO add aggro distance

        player = self.container.get_name('player')
        if player is not None:

            diff_x = player.x - self.x
            diff_y = player.y - self.y

            # Get target speed
            if abs(diff_x) > abs(diff_y):
                target_speed_x = Bat.SPEED if diff_x > 0 else -Bat.SPEED
                target_speed_y = diff_y / abs(diff_x)
            elif abs(diff_x) < abs(diff_y):
                target_speed_x = diff_x / abs(diff_y)
                target_speed_y = Bat.SPEED if diff_y > 0 else -Bat.SPEED
            else:
                target_speed_x = 1
                target_speed_y = 1

            # Move bat
            if self.velocity_x <= target_speed_x + Bat.ACCEL_SPEED:
                self.velocity_x += Bat.ACCEL_SPEED
            elif self.velocity_x >= target_speed_x - Bat.ACCEL_SPEED:
                self.velocity_x -= Bat.ACCEL_SPEED
            if self.velocity_y <= target_speed_y + Bat.ACCEL_SPEED:
                self.velocity_y += Bat.ACCEL_SPEED
            elif self.velocity_y > target_speed_y - Bat.ACCEL_SPEED:
                self.velocity_y -= Bat.ACCEL_SPEED

            temp_x += self.velocity_x
            temp_y += self.velocity_y

        _, self.x, self.y, _, _ = collision_resolution(self, temp_x, temp_y)

        if self.collides(player, self.x, self.y) and not self.invincible:
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 2)


class Boulder(peachy.Entity):

    SPEED = 2.5

    def __init__(self, x, y, direction):
        # TODO activity zone immune
        super().__init__(x, y)
        self.group = 'boulder'

        self.width = 32
        self.height = self.width
        self.dx = direction

        self.velocity_x = Boulder.SPEED * self.dx

    def render(self):
        peachy.graphics.set_color(50, 50, 50)
        peachy.graphics.draw_circle(self.x, self.y, self.width)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        # self.velocity_x = Boulder.SPEED * self.dx

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(self.container.get_name('player')):
            self.container.get_name('player').take_damage(self, 3)

        if self.velocity_x == 0 and self.velocity_y == 0:
            self.destroy()


class BoulderSpawner(peachy.Entity):

    SPAWN_DELAY = 80

    def __init__(self, x, y, direction):
        # TODO activity zone immune
        super().__init__(x, y)
        self.group = 'boulder'

        self.solid = True
        self.width = 16
        self.height = 32

        self.spawn_delay = BoulderSpawner.SPAWN_DELAY

        self.spawn_dx = 0
        if direction == 'LEFT':
            self.spawn_dx = -1
        elif direction == 'RIGHT':
            self.spawn_dx = 1

    def render(self):
        peachy.graphics.set_color(200, 200, 100)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.spawn_delay -= 1
        if self.spawn_delay < 0:
            self.spawn_delay = BoulderSpawner.SPAWN_DELAY
            boulder = Boulder(self.x + self.width * self.spawn_dx,
                              self.y, self.spawn_dx)
            self.container.add(boulder)


class BreakableTile(peachy.Entity):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.group = 'breakable'

        self.solid = True
        self.width = 16
        self.height = 16

        self.sprite = peachy.fs.get_image('BREAKABLE_TILE')

    def render(self):
        peachy.graphics.draw(self.sprite, self.x, self.y)


class BreakableReinforcedTile(peachy.Entity):

    def __init__(self, x, y, width, height):
        super().__init__(x, y)
        self.group = 'breakable-reinforced'

        self.width = width
        self.height = height
        self.solid = True

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)


class Dasher(Enemy):

    ACCEL_SPEED = 0.05
    SPEED = 1

    def __init__(self, x, y, initial_direction):
        Enemy.__init__(self, x, y)

        self.width = 16
        self.height = 16

        self.health = 3

        self.direction = ''
        self.direction_x = 0
        self.direction_y = 0

        if initial_direction == 'LEFT':
            self.direction = 'HORIZONTAL'
            self.direction_x = -1
        elif initial_direction == 'RIGHT':
            self.direction_x = 1
        elif initial_direction == 'UP':
            self.direction_y = -1
        elif initial_direction == 'DOWN':
            self.direction_y = 1

        spritesheet = peachy.fs.get_image('DASHER')

        if self.direction_y != 0:
            spritesheet = peachy.graphics.rotate(spritesheet, 270)

        # def hit_callback(self):
        #    self.sprite.play('NORMAL')

        self.sprite = peachy.graphics.SpriteMap(spritesheet, 16, 16)
        self.sprite.add('NORMAL', [0])
        self.sprite.add('HIT', [1], 10)
        self.sprite.play('NORMAL')

    def render(self):
        self.sprite.flipped_x = self.direction_x == 1
        self.sprite.flipped_y = self.direction_y == 1

        self.sprite.render(self.x, self.y)

    def update(self):
        if abs(self.velocity_x + Dasher.ACCEL_SPEED) < Dasher.SPEED:
            self.velocity_x += Dasher.ACCEL_SPEED * self.direction_x
        if abs(self.velocity_y + Dasher.ACCEL_SPEED) < Dasher.SPEED:
            self.velocity_y += Dasher.ACCEL_SPEED * self.direction_y

        temp_x = self.x + self.velocity_x
        temp_y = self.y + self.velocity_y

        collision_occured, self.x, self.y, _, _ = \
            collision_resolution(self, temp_x, temp_y)

        if collision_occured:
            self.direction_x *= -1
            self.direction_y *= -1
            self.velocity_x = 0
            self.velocity_y = 0

        player = self.container.get_name('player')
        if self.collides(player, self.x, self.y):
            player.take_damage(self, 1)


class Door(peachy.Entity):

    sprite = None

    def __init__(self, x, y, link):
        super().__init__(x, y)
        self.group = 'door'

        self.width = 16
        self.height = 16

        self.link = link

        if Door.sprite is None:
            Door.sprite = peachy.fs.get_image('DOOR')

    def render(self):
        peachy.graphics.draw(Door.sprite, self.x, self.y - 8)


class Item(peachy.Entity):

    def __init__(self, x, y, global_id, item_type, value):
        super().__init__(x, y)
        self.group = 'interactable'
        self.width = 16
        self.height = 16

        self.global_id = global_id
        self.item_type = item_type
        self.value = value

        sprites = splice(peachy.fs.get_image('UPGRADES'), 16, 16)

        if item_type == 'HEALTH_UPGRADE':
            self.sprite = sprites[0]
        elif item_type == 'WEAPON':
            if self.global_id == Player.Item.ID_PISTOL:
                self.sprite = sprites[1]
            elif self.global_id == Player.Item.ID_MISSILE:
                self.sprite = sprites[2]
        else:
            self.sprite = None

    def render(self):
        if self.sprite is None:
            peachy.graphics.set_color(0, 0, 0)
        peachy.graphics.draw(self.sprite, self.x, self.y)

    def interact(self, player):
        player.items.append(self.global_id)

        if self.item_type == 'HEALTH_UPGRADE':
            player.max_health += 3
            player.health = player.max_health
            display_message('HEALTH UPGRADE ACQUIRED: HP + ' + self.value)
        elif self.item_type == 'WEAPON':
            display_message('WEAPON ACQUIRED: ' + self.global_id)
        self.destroy()

    def update(self):
        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY
        temp_y = self.y + self.velocity_y
        _, _, self.y, _, self.velocity_y = \
            collision_resolution(self, self.x, temp_y)


class MapEvent(peachy.Entity):

    def __init__(self, x, y, width, height, name, update_script):
        super().__init__(x, y)
        self.group = 'event'
        self.name = name
        self.width = width
        self.height = height

        self.update_script = update_script
        # TODO all of this


class MovingPlatform(peachy.Entity):

    SPEED = 1
    ZONE_SIZE = 2
    WAIT_TIME = 60

    # TODO Move to end when player is near end
    # TODO change from flags to states

    def __init__(self, start_x, start_y, end_x, end_y):
        super().__init__(start_x, start_y)

        self.width = 16
        self.height = 2

        self.start = (start_x, start_y)
        self.end = (end_x, end_y)

        self.solid = True

        self.player_riding = False
        self.reverse = False
        self.waiting = False
        self.wait_timer = 0

        self.sprite = peachy.fs.get_image('MOVING_PLATFORM')

    def render(self):
        if PC.debug and peachy.utils.Keys.down('g'):
            peachy.graphics.set_color(242, 117, 8)
            peachy.graphics.draw_rect(*self.start, self.width, self.height)
            peachy.graphics.draw_rect(*self.end, self.width, self.height)
        peachy.graphics.draw(self.sprite, self.x, self.y)

    def update(self):
        if self.waiting:
            self.wait_timer -= 1
            if self.wait_timer > 0:
                return
            else:
                self.waiting = False

        player = self.container.get_name('player')

        active_zone = (self.x, self.y - MovingPlatform.ZONE_SIZE, self.width,
                       MovingPlatform.ZONE_SIZE)
        if player is not None and player.collides_rect(active_zone):
            self.player_riding = True
            target_x, target_y = self.start if self.reverse else self.end
        else:
            if self.player_riding:
                self.wait()
            self.player_riding = False
            target_x, target_y = self.start

        temp_x, temp_y = self.move(self.x, self.y, target_x, target_y)

        # Collision detection
        if xcollides_solid(self, temp_x, temp_y):
            temp_x = self.x
            temp_y = self.y
            self.wait()
            self.reverse = not self.reverse

        diff_x = temp_x - self.x
        diff_y = temp_y - self.y

        # Move player
        if self.player_riding:
            player_temp_x = player.x
            player_temp_y = player.y

            if self.collides(player, temp_x, self.y):
                player_temp_x += diff_x
            elif self.collides_name(player, self.x, temp_y):
                player_temp_y += diff_y

            player_temp_x += diff_x
            player_temp_y += diff_y

            # Prevent pushing player into a solid
            player_collisions = xcollides_solid(player, player_temp_x,
                                                player_temp_y)
            for collision in player_collisions:

                # Make sure registered collision is not this MovingPlatform
                if collision is not self:
                    temp_x = self.x
                    temp_y = self.y
                    player_temp_x = player.x
                    player_temp_y = player.y

            player.x = player_temp_x
            player.y = player_temp_y

        # Update location
        self.x = temp_x
        self.y = temp_y
        if self.x == target_x and self.y == target_y and self.player_riding:
            self.wait()
            self.reverse = not self.reverse

    def move(self, temp_x, temp_y, target_x, target_y):
        if temp_x < target_x:
            temp_x += MovingPlatform.SPEED
        elif temp_x > target_x:
            temp_x -= MovingPlatform.SPEED
        elif temp_y < target_y:
            temp_y += MovingPlatform.SPEED
        elif temp_y > target_y:
            temp_y -= MovingPlatform.SPEED
        return temp_x, temp_y

    def wait(self):
        self.waiting = True
        self.wait_timer = MovingPlatform.WAIT_TIME


class Platform(peachy.Entity):

    def __init__(self, x, y, width):
        super().__init__(x, y)
        self.group = 'platform'

        self.width = width
        self.height = 2

        self.solid = True
        self.ignore_player = False

    def render(self):
        peachy.graphics.set_color(0, 0, 0)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height + 1)

    def update(self):
        if not self.solid:
            player = self.container.get_name('player')
            if not self.collides(player, self.x, self.y):
                self.solid = True


class PressurePlate(peachy.Entity):

    def __init__(self, x, y, on_activate, on_deactivate):
        super().__init__(x, y)
        self.width = 16
        self.height = 4

        self.pressed_down = False

        self.on_activate = on_activate
        self.on_deactivate = on_deactivate

    def render(self):
        peachy.graphics.set_color(255, 120, 0)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def activate(self):
        exec(self.on_activate)

    def deactivate(self):
        exec(self.on_deactivate)

    def update(self):
        is_pressed_down = False
        collisions = self.collides_solid()
        collisions.append(self.collides_name('player'))

        for c in collisions:
            if c:
                is_pressed_down = True
                break

        if self.pressed_down and not is_pressed_down:
            self.deactivate()
        elif not self.pressed_down and is_pressed_down:
            self.activate()

        self.pressed_down = is_pressed_down


class RetractableDoor(peachy.Entity):

    def __init__(self, x, y, width, height):
        super().__init__(x, y)
        self.width = width
        self.height = height

        self.solid = True

    def render(self):
        peachy.graphics.set_color(200, 200, 200)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def open(self):
        self.solid = False
        self.visible = False

    def close(self):
        self.solid = True
        self.visible = True


class SaveStation(peachy.Entity):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.group = 'interactable'
        self.width = 16
        self.height = 16

        self.sprite = peachy.fs.get_image('SAVE_STATION')

    def render(self):
        peachy.graphics.draw(self.sprite, self.x, self.y)

    def interact(self, player):
        display_choice("Would you like to record your progress?", self.save)

    def save(self, result):
        if result:
            PC.world.save_game(SAVE_FILE)
            print('Game Saved')


class Ship(peachy.Entity):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.group = 'interactable'
        self.width = 16
        self.height = 16

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def interact(self, player):
        # Enter ShipMenuState
        PC.world.change_state(SHIP_STATE)


class SignPost(peachy.Entity):

    def __init__(self, x, y, message):
        super().__init__(x, y)
        self.width = 16
        self.height = 16

        self.message = message

        self.sprite = peachy.fs.get_image('SIGN_POST')

    def render(self):
        if self.container.planet['name'] != 'reptilia':
            peachy.graphics.draw(self.sprite, self.x, self.y)

    def interact(self, player):
        display_message(self.message)


class SmallGolem(Enemy):
    """ Walks towards the player"""

    SPEED = 1

    def __init__(self, x, y):
        Enemy.__init__(self, x, y)
        self.width = 10
        self.height = 10

        self.sprite = peachy.fs.get_image('SMALL_GOLEM')

        self.facing_x = 0

    def render(self):
        if self.facing_x == 1:
            peachy.graphics.draw(self.sprite, self.x, self.y)
        else:
            peachy.graphics.draw(self.sprite, self.x, self.y,
                                 peachy.graphics.FLIP_X)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        player = self.container.get_name('player')

        if player.x < self.x:
            temp_x -= SmallGolem.SPEED
            self.facing_x = 1
        elif player.x > self.x + self.width:
            temp_x += SmallGolem.SPEED
            self.facing_x = -1

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(player, self.x, self.y):
            player.take_damage(self, 1)


class Solid(peachy.Entity):

    def __init__(self, x, y, width, height,
                 slanted=False, flip_x=False, flip_y=False):
        super().__init__(x, y)

        self.group = 'solid'
        self.width = width
        self.height = height

        self.solid = True
        if PC.debug:
            self.visible = True
        else:
            self.visible = False

        self.slanted = slanted
        self.flip_x = flip_x
        self.flip_y = flip_y

    def intersection(self, line_x):

        line_x = line_x - self.x
        slope = float(float(self.height) / float(self.width))
        intersection = float(line_x * slope)

        if self.flip_x:
            intersection = self.height - intersection

        # TODO add functionality for upside-down slopes
        # if self.flip_y:

        if intersection < 0:
            return self.y + self.height
        elif intersection > self.height:
            return self.y
        else:
            return self.y + self.height - intersection

    def render(self):
        # For DEBUG purposes only
        if PC.debug and peachy.utils.Keys.down('g'):
            peachy.graphics.set_color(155, 155, 155)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)


class Spider(Enemy):

    ACCEL_SPEED = 0.25
    MOVE_SPEED = 1.5

    STATE_DROPPING = 'dropping'

    AGGRO_DISTANCE_X = 16
    AGGRO_DISTANCE_Y = 128

    def __init__(self, x, y):
        Enemy.__init__(self, x, y)
        self.width = 16
        self.height = 8
        self.health = 3
        self.state = Enemy.STATE_IDLE

    def render(self):
        peachy.graphics.set_color(0, 0, 255)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        player = self.container.get_name('player')

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == Enemy.STATE_IDLE:
            player_distance_x = abs(temp_x - player.x)
            player_distance_y = player.y - temp_y  # Must be below

            if player_distance_x < Spider.AGGRO_DISTANCE_X and \
               0 < player_distance_y < Spider.AGGRO_DISTANCE_Y:
                self.state = Spider.STATE_DROPPING

        elif self.state == Spider.STATE_DROPPING:
            if solid_below(self, temp_x, temp_y):
                self.state = Enemy.STATE_AGGRO

            if self.velocity_y < MAX_GRAVITY:
                self.velocity_y += GRAVITY

            if self.velocity_x != 0:
                self.velocity_x -= 0.25 if self.velocity_x > 0 else -0.25

        elif self.state == Enemy.STATE_AGGRO:
            if temp_x < player.x and self.velocity_x < Spider.MOVE_SPEED:
                self.facing_x = 1
                self.velocity_x += Spider.ACCEL_SPEED
            elif temp_x > player.x and self.velocity_x > -Spider.MOVE_SPEED:
                self.facing_x = -1
                self.velocity_x -= Spider.ACCEL_SPEED

            if self.velocity_y < MAX_GRAVITY:
                self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(player, self.x, self.y):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1)
        self.state = Spider.STATE_DROPPING


class Spikes(peachy.Entity):
    def __init__(self, x, y, width):
        super().__init__(x, y)

        self.width = width
        self.height = 16
        self.visible = False

    def update(self):
        player = self.container.get_name('player')
        collisions = self.collides_group('enemy')
        if self.collides(player, self.x, self.y):
            collisions.append(player)

        for collision in collisions:
            if collision:
                collision.take_damage(self, 100)


class Switch(peachy.Entity):

    def __init__(self, x, y, on_activate):
        super().__init__(x, y)
        self.group = 'switch'

        self.width = 16
        self.height = 16
        self.solid = True

        self.activated = False
        self.on_activate = on_activate

        self.sprite = peachy.graphics.SpriteMap(peachy.fs.get_image('SWITCH'),
                                                16, 16)
        self.sprite.add('ON', [1])
        self.sprite.add('OFF', [0])

    def activate(self):
        if not self.activated:
            exec(self.on_activate)
            self.activated = True

    def render(self):
        self.sprite.play('ON' if self.activated else 'OFF')
        self.sprite.render(self.x, self.y)


class Water(peachy.Entity):

    def __init__(self, x, y, width, height):
        super().__init__(x, y)
        self.group = 'water'
        self.width = width
        self.height = height

    def render(self):
        peachy.graphics.set_color(0, 0, 255)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)


class Weight(peachy.Entity):

    def __init__(self, x, y):
        super().__init__(x, y)
        self.group = 'weight'

        self.width = 16
        self.height = 16
        self.solid = True

        self.sprite = peachy.fs.get_image('WEIGHT')

    def render(self):
        peachy.graphics.draw(self.sprite, self.x, self.y)

    def update(self):
        temp_y = self.y
        self.velocity_y += GRAVITY if self.velocity_y < MAX_GRAVITY else 0
        temp_y += self.velocity_y
        _, self.x, self.y, _, _ = collision_resolution(self, self.x, temp_y)
