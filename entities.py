import config
from abc import ABCMeta, abstractmethod
import core
from core import AssetManager, GC, Entity, Graphics, Input
from util import SpriteMap, splice_image

INVINCIBILITY_DURATION = 20
GRAVITY = 0.2


def display_message(message):
    GC.world.change_state('message', message)


class AbsEnemy(Entity):
    __metaclass__ = ABCMeta

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'enemy'

        self.health = 0
        self.invincible = False

        self.facing_x = 0
        self.facing_y = 0

    def take_damage(self, attacker, damage):
        if not self.invincible:
            self.health -= damage
            if self.health <= 0:
                self.destroy()


class AbsInteractable(Entity):
    __metaclass__ = ABCMeta

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'interactable'

    @abstractmethod
    def interact(self, player):
        return


class AbsProjectile(Entity):
    __metaclass__ = ABCMeta

    def __init__(self, parent, x, y, dx, dy, speed, lifespan=-1):
        Entity.__init__(self, x, y)
        self.group = 'projectile'
        
        self.parent = parent
        self.velocity_x = speed * dx
        self.velocity_y = speed * dy
        self.lifespan = lifespan

    def move(self):
        self.x += self.velocity_x
        self.y += self.velocity_y

    @abstractmethod
    def collision(self):
        """ Abstract method used to define how to handle collisions """
        return

    def update(self):
        self.move()
        self.collision()
        self.lifespan -= 1
        if self.lifespan == 0:
            self.active = False
            self.destroy()


class Bat(AbsEnemy):

    ACCEL_SPEED = 0.05
    SPEED = 0.75

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 8
        self.height = 8
        self.health = 2
        self.invincibility_timer = 0

    def render(self):
        Graphics.set_color(100, 100, 255)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        player = core.ENTITY_ROOM.player
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

        if self.collides(player) and not self.invincible:
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        AbsEnemy.take_damage(self, attacker, damage)
        if self.active and not self.invincible:
            knockback(self, attacker, 2)
            self.invincible = True
            self.invincibility_timer = INVINCIBILITY_DURATION


class BreakableTile(Entity):

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'breakable'

        self.solid = True
        self.width = 16
        self.height = 16

        self.sprite = AssetManager.get_image('BREAKABLE_TILE')

    def render(self):
        Graphics.draw_image(self.sprite, self.x, self.y)


class Dasher(AbsEnemy):

    ACCEL_SPEED = 0.05
    SPEED = 1
    
    def __init__(self, x, y, initial_direction):
        AbsEnemy.__init__(self, x, y)

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
        
        spritesheet = AssetManager.get_image('DASHER')

        if self.direction_y != 0:
            spritesheet = Graphics.rotate(spritesheet, 270)

        def hit_callback(self): self.sprite.play('NORMAL');

        self.sprite = SpriteMap(spritesheet, 16, 16)
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

        collision_occured, self.x, self.y, _, _ = collision_resolution(self, temp_x, temp_y)

        if collision_occured:
            self.direction_x *= -1
            self.direction_y *= -1
            self.velocity_x = 0
            self.velocity_y = 0

        player = core.ENTITY_ROOM.player
        if self.collides(player):
            player.take_damage(self, 1)


class Door(Entity):

    sprite = None

    def __init__(self, x, y, link):
        Entity.__init__(self, x, y)
        self.group = 'door'

        self.width = 16
        self.height = 16

        self.link = link

        if Door.sprite is None:
            Door.sprite = AssetManager.get_image('DOOR')

    def render(self):
        Graphics.draw_image(Door.sprite, self.x, self.y - 8)


class Item(AbsInteractable):

    def __init__(self, x, y, global_id, item_type, value):
        AbsInteractable.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.global_id = global_id
        self.item_type = item_type
        self.value = value

        sprites = splice_image(AssetManager.get_image('UPGRADES'), 16, 16)
        
        if item_type == 'HEALTH_UPGRADE':
            self.sprite = sprites[0]
        elif item_type == 'WEAPON':
            if self.global_id == Player.Weapon.ID_PISTOL:
                self.sprite = sprites[1]
            elif self.global_id == Player.Weapon.ID_MISSILE:
                self.sprite = sprites[2]

    def render(self):
        Graphics.draw_image(self.sprite, self.x, self.y)

    def interact(self, player):
        # TODO remove from global tracking class
        # Tracker.item_obtained[self.global_id]

        if self.item_type == 'HEALTH_UPGRADE':
            Player.MAX_HEALTH += int(self.value)
            player.health = Player.MAX_HEALTH
            display_message('HEALTH UPGRADE ACQUIRED: HP + ' + self.value)
        elif self.item_type == 'WEAPON':
            player.weapon.available.append(self.global_id)
            display_message('WEAPON ACQUIRED: ' + self.global_id)
        self.destroy()

    def update(self):
        if self.velocity_y < 6:
            self.velocity_y += GRAVITY
        temp_y = self.y + self.velocity_y
        _, _, self.y, _, self.velocity_y = collision_resolution(self, self.x, temp_y)


class MapEvent(Entity):

    def __init__(self, x, y, w, h, name, update_script):
        Entity.__init__(self, x, y)
        self.group = 'event'
        self.name = name
        self.width = w
        self.height = h

        self.update_script = update_script
        # TODO all of this


class MovingPlatform(Entity):

    SPEED = 1
    ZONE_SIZE = 2
    WAIT_TIME = 60

    # TODO Move to end when player is near end
    
    def __init__(self, start_x, start_y, end_x, end_y):
        Entity.__init__(self, start_x, start_y)

        self.width = 16
        self.height = 2

        self.start = (start_x, start_y)
        self.end = (end_x, end_y)

        self.solid = True

        self.player_riding = False
        self.reverse = False
        self.waiting = False

        self.sprite = AssetManager.get_image('MOVING_PLATFORM')

    def render(self):
        if GC.DEBUG and Input.down('g'):
            Graphics.set_color(242, 117, 8)
            Graphics.draw_rect(*self.start, width=self.width, height=self.height)
            Graphics.draw_rect(*self.end,  width=self.width, height=self.height)
        Graphics.draw_image(self.sprite, self.x, self.y)

    def update(self):
        if self.waiting:
            self.wait_timer -= 1
            if self.wait_timer > 0:
                return
            else:
                self.waiting = False

        player = core.ENTITY_ROOM.player

        active_zone = (self.x, self.y - MovingPlatform.ZONE_SIZE, self.width, MovingPlatform.ZONE_SIZE)
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
        if self.collides_solid(temp_x, temp_y):
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
            player_solid_collisions = player.collides_solid(player_temp_x, player_temp_y)
            for collision in player_solid_collisions:

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


class Platform(Entity):

    def __init__(self, x, y, width):
        Entity.__init__(self, x, y)
        self.group = 'platform'

        self.solid = True

        self.width = width
        self.height = 1

        self.ignore_player = False

    def render(self):
        Graphics.set_color(0, 0, 0)
        Graphics.draw_rect(self.x, self.y, self.width, self.height + 1)

    def update(self):
        if self.ignore_player:
            player = core.ENTITY_ROOM.player
            if not self.collides(player):
                self.ignore_player = False
    

class Player(Entity):

    WIDTH = 10
    HEIGHT = 12

    MAX_HEALTH = 5

    MAX_SPEED = 2.5
    ACCEL_SPEED = 0.5
    JUMP_FORCE = 3.75

    DASH_DURATION = 20
    DASH_SPEED = 4

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.name = 'player'

        self.width = Player.WIDTH
        self.height = Player.HEIGHT

        self.sprite = Player.Sprite()

        self.weapon = Player.Weapon()
        self.items = []

        self.facing_x = 1
        self.facing_y = 0

        self.health = Player.MAX_HEALTH
        self.invincible = False

        self.dash_active = False
        self.dash_available = False
        self.dash_timer = 0

        self.double_jump_available = False

    def render(self):
        if GC.DEBUG and Input.down('g'):
            Graphics.set_color(255, 255, 255)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        if self.invincible:
            # TODO add blinking
            Graphics.set_color(0, 0, 255)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        self.sprite.validate(self)
        self.sprite.render(self.x, self.y)
    
    def take_damage(self, attacker, damage):
        if not self.invincible:
            self.health -= damage
            if self.health <= 0:
                self.destroy()

        if self.active and not self.invincible:  # still alive
            knockback(self, attacker, 4)
            self.invincible = True
            self.invincibility_timer = 60
        
    def update(self):
        temp_x = self.x
        temp_y = self.y

        has_solid_below = solid_below(self, temp_x, temp_y)

        # USER INPUT 
        KEYDOWN_DOWN = Input.down(config.KEY['DOWN'])
        KEYDOWN_LEFT = Input.down(config.KEY['LEFT'])
        KEYDOWN_RIGHT = Input.down(config.KEY['RIGHT'])
        KEYDOWN_UP = Input.down(config.KEY['UP'])
        KEYPRESSED_ATTACK = Input.pressed(config.KEY['ATTACK'])
        KEYPRESSED_CHANGE_WEAPON = Input.pressed(config.KEY['CHANGE_WEAPON'])
        KEYPRESSED_JUMP = Input.pressed(config.KEY['JUMP'])
        KEYPRESSED_INTERACT = Input.pressed(config.KEY['INTERACT'])
        KEYRELEASED_JUMP = Input.released(config.KEY['JUMP'])
        KEYPRESSED_DASH = Input.pressed(config.KEY['DASH'])

        # USER INPUT - State Timers
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        # USER INPUT - Interaction
        if KEYPRESSED_INTERACT:
            interactables = self.collides_group('interactable')
            if interactables:
                interactable = interactables[0]
                interactable.interact(self)

        # USER INPUT - Combat
        if self.weapon.active:
            self.weapon.update()

        if KEYPRESSED_CHANGE_WEAPON:
            self.weapon.cycle()
            self.sprite.change_set(self.weapon.current)

        if KEYPRESSED_ATTACK and not self.weapon.active:
            self.weapon.activate(self)

        # USER INPUT - Movement
        if self.velocity_x > Player.MAX_SPEED:
            self.velocity_x -= Player.ACCEL_SPEED * 2
        elif self.velocity_x < -Player.MAX_SPEED:
            self.velocity_x += Player.ACCEL_SPEED * 2
        if KEYDOWN_LEFT == KEYDOWN_RIGHT:
            if self.velocity_x != 0:
                if self.velocity_x > 0:
                    self.velocity_x -= Player.ACCEL_SPEED
                else:
                    self.velocity_x += Player.ACCEL_SPEED
        else:
            if KEYDOWN_LEFT and self.velocity_x > -Player.MAX_SPEED:
                self.velocity_x -= Player.ACCEL_SPEED
                self.facing_x = -1
            if KEYDOWN_RIGHT and self.velocity_x < Player.MAX_SPEED:
                self.velocity_x += Player.ACCEL_SPEED
                self.facing_x = 1

        if KEYDOWN_UP or KEYDOWN_DOWN:
            if KEYDOWN_UP:
                self.facing_y = -1
            if KEYDOWN_DOWN:
                if not has_solid_below:
                    self.facing_y = 1
        else:
            self.facing_y = 0

        # USER INPUT - Dash
        if Player.Item.ID_DASH_BOOTS in self.items:
            if not self.dash_available and not self.dash_active:
                if self.dash_timer > 0:
                    self.dash_timer -= 1
                else:
                    self.dash_available = has_solid_below
            if KEYPRESSED_DASH and self.dash_available and not self.dash_active:
                self.dash_active = True
                self.dash_timer = Player.DASH_DURATION
            if self.dash_active:
                self.velocity_x = Player.DASH_SPEED * self.facing_x
                self.dash_timer -= 1
                if self.dash_timer <= 0:
                    self.dash_active = False
                    self.dash_available = False
                    self.dash_timer = Player.DASH_DURATION / 4


        # USER INPUT - Jump
        if Player.Item.ID_DOUBLE_JUMP in self.items:
            if not self.double_jump_available:
                if has_solid_below:
                    self.double_jump_available = True

        if KEYDOWN_DOWN and KEYPRESSED_JUMP:
            platforms = self.collides_group('platform', self.x, self.y + 1)
            for platform in platforms:
                platform.ignore_player = True
        elif KEYPRESSED_JUMP:
            if has_solid_below: # standard jump
                self.velocity_y = -Player.JUMP_FORCE
                if Player.Item.ID_DASH_BOOTS in self.items:
                    self.dash_available = True
            elif KEYDOWN_LEFT and self.collides_solid(self.x - 1, self.y):  # wall jump - right
                self.velocity_x = Player.DASH_SPEED
                self.velocity_y = -Player.JUMP_FORCE
            elif KEYDOWN_RIGHT and self.collides_solid(self.x + 1, self.y):  # wall jump - left
                self.velocity_x = -Player.DASH_SPEED
                self.velocity_y = -Player.JUMP_FORCE
            elif self.double_jump_available:  # double jump
                self.velocity_y = -Player.JUMP_FORCE
                self.double_jump_available = False
        elif KEYRELEASED_JUMP:
            if self.velocity_y < 0:
                self.velocity_y /= 2

        # Gravity & Finalize
        if self.velocity_y < 6:
            self.velocity_y += GRAVITY
        if self.dash_active:
            self.velocity_y = 0

        temp_x += self.velocity_x
        temp_y += self.velocity_y
        
        # FINALIZE - Collision Detection
        c, temp_x, temp_y, self.velocity_x, self.velocity_y = collision_resolution(self, temp_x, temp_y)
        if c:
            self.dash_active = False

        # FINALIZE - Update Location
        self.x = temp_x
        self.y = temp_y

    class Item:  # ItemHandler
        ID_DASH_BOOTS = 'DASH'
        ID_DOUBLE_JUMP = 'DBLJ'
        ID_SUPER_SUIT = 'SUPS'

    class Sprite:

        def __init__(self):
            spritesheet = AssetManager.get_image('PLAYER')

            self.anim_name = 'IDLE'
            self.set_name = Player.Weapon.ID_NONE

            none_sprite = SpriteMap(spritesheet, 16, 16, origin_x=3, origin_y=4)
            none_sprite.add('ATTACK', [3, 4, 4, 4, 4, 4], 2, False)
            none_sprite.add('ATTACK_BELOW', [6, 6, 6, 6, 6], 2, False)
            none_sprite.add('ATTACK_UPWARDS', [5, 5, 5, 5, 5], 2, False)
            none_sprite.add('IDLE', [0])
            none_sprite.add('IDLE_LOOKING_UP', [10])
            none_sprite.add('JUMP_FALLING', [16])
            none_sprite.add('JUMP_LOOKING_DOWN', [16])
            none_sprite.add('JUMP_LOOKING_UP', [15])
            none_sprite.add('JUMP_RISING', [15])
            none_sprite.add('JUMP_STALL', [1])
            none_sprite.add('RUN', [3, 1, 3, 2], 8, True)
            none_sprite.add('RUN_LOOKING_UP', [13, 11, 13, 12], 8, True)
            none_sprite.play('IDLE')

            pist_sprite = SpriteMap(spritesheet, 16, 16, origin_x=1, origin_y=4)
            pist_sprite.add('IDLE', [20])
            pist_sprite.add('IDLE_LOOKING_UP', [24])
            pist_sprite.add('JUMP_FALLING', [21])
            pist_sprite.add('JUMP_LOOKING_DOWN', [27])
            pist_sprite.add('JUMP_LOOKING_UP', [25])
            pist_sprite.add('JUMP_RISING', [21])
            pist_sprite.add('JUMP_STALL', [21])
            pist_sprite.add('RUN', [23, 22, 23, 21], 8, True)
            pist_sprite.add('RUN_LOOKING_UP', [24, 25, 24, 26], 8, True)
            pist_sprite.play('IDLE')

            miss_sprite = SpriteMap(spritesheet, 16, 16, origin_x=1, origin_y=4)
            miss_sprite.add('IDLE', [30])
            miss_sprite.add('JUMP', [31])
            miss_sprite.add('RUN', [31, 30, 32, 30], 10, True)
            miss_sprite.play('IDLE')

            self.spritesets = {
                Player.Weapon.ID_NONE: none_sprite,
                Player.Weapon.ID_PISTOL: pist_sprite,
                Player.Weapon.ID_MISSILE: miss_sprite,
            }
            self.current_sprite = self.spritesets[self.set_name]

        def change_set(self, set_name):
            self.set_name = set_name
            self.current_sprite = self.spritesets[set_name]
            self.current_sprite.play('IDLE')

        def play(self, anim_name, flip_x=False, flip_y=False):
            self.anim_name = anim_name
            self.current_sprite.play(anim_name, flip_x, flip_y)

        def pause(self):
            self.current_sprite.pause()

        def stop(self):
            self.current_sprite.stop()

        def render(self, x, y):
            self.current_sprite.render(x, y)

        def validate(self, player):
            flip_x = player.facing_x == 1
            flip_required = flip_x != self.current_sprite.flipped_x

            if self.anim_name[:6] != 'ATTACK' or not player.weapon.active:
                if not solid_below(player, player.x, player.y):
                    if Input.down('down'):
                        self.play("JUMP_LOOKING_DOWN", flip_x)
                    elif Input.down('up'):
                        self.play('JUMP_LOOKING_UP', flip_x)
                    elif player.velocity_y < -0.5:
                        self.play("JUMP_RISING", flip_x)
                    elif player.velocity_y > 0.5:
                        self.play("JUMP_FALLING", flip_x)
                    else:
                        self.play("JUMP_STALL", flip_x)
                elif player.facing_y == -1:
                    if player.velocity_x != 0:
                        if self.anim_name != 'RUN_LOOKING_UP' or flip_required:
                            self.play('RUN_LOOKING_UP', flip_x)
                    elif self.anim_name != 'IDLE_LOOKING_UP' or flip_required:
                        self.play('IDLE_LOOKING_UP', flip_x)
                else:
                    if player.velocity_x != 0:
                        if self.anim_name != 'RUN' or flip_required:
                            self.play('RUN', flip_x)
                    elif self.anim_name != 'IDLE' or flip_required:
                        self.play('IDLE', flip_x)

    class Weapon:  # WeaponHandler

        ID_NONE = 'NONE'
        ID_PISTOL = 'PIST1'
        ID_PISTOL_LEVEL_TWO = 'PIST2'
        ID_PISTOL_LEVEL_THREE = 'PIST3'
        ID_MISSILE = 'MISS'
        ID_MISSILE_LEVEL_TWO = 'MISS2'

        def __init__(self):
            self.active = False
            self.cooldown = 0

            self.current = Player.Weapon.ID_NONE
            self.current_weapon_index = 0
            self.available = [ 
                Player.Weapon.ID_NONE # ,
                # Player.Weapon.ID_PISTOL,
                # Player.Weapon.ID_MISSILE
            ]

        def activate(self, player):
            facing_x = player.facing_x if player.facing_y == 0 else 0

            inst = None
            if self.current == Player.Weapon.ID_NONE:
                inst = Player.Punch(player, player.x, player.y, facing_x, player.facing_y)
                self.cooldown = Player.Punch.COOLDOWN
            elif self.current == Player.Weapon.ID_PISTOL:
                inst = Player.PeaBullet(player, player.x, player.y, facing_x, player.facing_y)
                self.cooldown = Player.PeaBullet.COOLDOWN
            elif self.current == Player.Weapon.ID_MISSILE:
                inst = Player.Missile(player, player.x, player.y, facing_x, player.facing_y)
                self.cooldown = Player.Missile.COOLDOWN
            else:
                if GC.DEBUG:
                    print '*ERROR* could not use weapon ' + self.current
                return

            core.ENTITY_ROOM.add(inst)
            self.active = True

        def cycle(self):
            self.current_weapon_index += 1
            if self.current_weapon_index >= len(self.available):
                self.current_weapon_index = 0
            self.current = self.available[self.current_weapon_index]

        def update(self):
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.active = False

    class PeaBullet(AbsProjectile):
        
        COOLDOWN = 3
        SPEED = 6
        LIFESPAN = 20

        def __init__(self, parent, x, y, direction_x, direction_y):
            AbsProjectile.__init__(self, parent, x, y, direction_x, direction_y, 
                                   Player.PeaBullet.SPEED, Player.PeaBullet.LIFESPAN)
            self.width = 12
            self.height = 12

        def render(self):
            Graphics.set_color(255, 0, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collisions = self.collides_multiple_groups(['breakable', 'enemy', 'switch', 'solid'])
            # TODO add collides solid
            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self, 1)
                    elif collision.group == 'switch':
                        collision.activate()
                    self.destroy()

    class Punch(Entity):

        COOLDOWN = 15
        LIFESPAN = 13
        THRUST = 9

        def __init__(self, parent, x, y, direction_x, direction_y):
            Entity.__init__(self, x, y)
            self.parent = parent
            self.width = 16
            self.height = 16
            self.direction_x = direction_x
            self.direction_y = direction_y
            self.lifespan = Player.Punch.LIFESPAN

            flip_x = direction_x == 1

            self.update_location()

            if direction_y != 0:
                if direction_y == -1:
                    parent.sprite.play('ATTACK_UPWARDS', flip_x)
                elif direction_y == 1:
                    parent.sprite.play('ATTACK_BELOW', flip_x)
            else:
                parent.velocity_x = Player.Punch.THRUST * direction_x
                parent.sprite.play('ATTACK', flip_x)

        def render(self):
            Graphics.set_color(255, 0, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def update(self):
            self.update_location()

            collisions = self.collides_multiple_groups(['breakable', 'enemy', 'solid', 'switch'])
            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self.parent, 1)
                    elif collision.group == 'switch':
                        collision.activate()
            
            self.lifespan -= 1
            if self.lifespan < 0:
                self.destroy()

        def update_location(self):
            self.x = self.parent.x
            self.y = self.parent.y

            if self.direction_y != 0:
                if self.direction_y == -1:
                    self.y -= self.height
                elif self.direction_y == 1:
                    self.y += self.parent.height
            else:
                if self.direction_x == -1:
                    self.x -= self.width
                elif self.direction_x == 1:
                    self.x += self.parent.width
                self.y += self.parent.height - self.height

    class Missile(AbsProjectile):
        
        COOLDOWN = 30
        SPEED = 10
        LIFESPAN = 40

        def __init__(self, parent, x, y, direction_x, direction_y):
            AbsProjectile.__init__(self, parent, x, y, direction_x, direction_y, 
                                   Player.Missile.SPEED, Player.Missile.LIFESPAN)
            if direction_x == 0:
                self.width = 10
                self.height = 16
            else:
                self.width = 16
                self.height = 10
            self.state = 'standard'

        def render(self):
            if self.state == 'standard':
                Graphics.set_color(255, 255, 255)
            elif self.state == 'exploding':
                Graphics.set_color(255, 70, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collisions = self.collides_multiple_groups(['breakable', 'enemy', 'solid', 'switch'])
            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self, 1)
                    elif collision.group == 'switch':
                        collision.activate()
                    self.explode()

        def update(self):
            if self.state == 'standard':
                self.move()
                self.collision()
            elif self.state == 'exploding':
                self.collision()

            self.lifespan -= 1
            if self.lifespan <= 0:
                if self.state == 'standard':
                    self.explode()
                else:
                    self.active = False
                    self.destroy()

        def explode(self):
            if self.state == 'standard':
                self.state = 'exploding'
                self.x -= self.width / 2
                self.y -= self.height / 2
                self.width *= 2
                self.height *= 2
                self.lifespan = 20


class PressurePlate(Entity):

    def __init__(self, x, y, on_activate, on_deactivate):
        Entity.__init__(self, x, y)
        self.width = 16
        self.height = 4

        self.pressed_down = False

        self.on_activate = on_activate
        self.on_deactivate = on_deactivate

    def render(self):
        Graphics.set_color(255, 120, 0)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def activate(self):
        exec self.on_activate

    def deactivate(self):
        exec self.on_deactivate

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


class RetractableDoor(Entity):
    
    def __init__(self, x, y, height):
        Entity.__init__(self, x, y)
        self.width = 16
        self.height = height

        self.solid = True

    def render(self):
        Graphics.set_color(200, 200, 200)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def open(self):
        self.solid = False
        self.visible = False

    def close(self):
        self.solid = True
        self.visible = True


class SaveStation(AbsInteractable):
    
    def __init__(self, x, y):
        AbsInteractable.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.sprite = AssetManager.get_image('SAVE_STATION')

    def render(self):
        Graphics.draw_image(self.sprite, self.x, self.y)

    def interact(self, player):
        display_message('saving under construction')


class SignPost(AbsInteractable):

    def __init__(self, x, y, message):
        AbsInteractable.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.message = message

        self.sprite = AssetManager.get_image('SIGN_POST')
    
    def render(self):
        Graphics.draw_image(self.sprite, self.x, self.y)

    def interact(self, player):
        display_message(self.message)


class Skeleton(AbsEnemy):

    BONE_COOLDOWN = 90
    SPEED = Player.MAX_SPEED + 0.5
    SAFE_DISTANCE = 54

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 16
        self.height = 16
        
        self.health = 3

        self.bone_cooldown = Skeleton.BONE_COOLDOWN

        self.sprite = AssetManager.get_image('SKELETON')

    def render(self):
        if self.facing_x == 1:
            Graphics.draw_image(self.sprite, self.x, self.y)
        else:
            Graphics.draw_image(self.sprite, self.x, self.y, Graphics.FLIP_X)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        player = core.ENTITY_ROOM.player
        if player is None:
            return

        distance_from_player = abs(player.x - self.x)

        # Throw Bone
        self.bone_cooldown -= 1
        if self.bone_cooldown == 0:
            core.ENTITY_ROOM.add(Skeleton.Bone(self, player))
            self.bone_cooldown = Skeleton.BONE_COOLDOWN

        # Movement
        if distance_from_player < Skeleton.SAFE_DISTANCE:  # Move away
            if temp_x < player.x and solid_below(self, temp_x - Skeleton.SPEED, self.y):
                temp_x -= Skeleton.SPEED
                self.facing_x = -1
            elif temp_x > player.x and solid_below(self, temp_x + Skeleton.SPEED, self.y):
                temp_x += Skeleton.SPEED
                self.facing_x = 1

        elif distance_from_player > Skeleton.Bone.MAX_DISTANCE:  # Move towards
            if temp_x < player.x and solid_below(self, temp_x + Skeleton.SPEED, self.y):
                temp_x += Skeleton.SPEED
                self.facing_x = -1
            elif temp_x > player.x and solid_below(self, temp_x - Skeleton.SPEED, self.y):
                temp_x -= Skeleton.SPEED
                self.facing_x = 1

        if self.velocity_x != 0:
            self.velocity_x += 0.25 if self.velocity_x < 0 else -0.25

        # Gravity
        if self.velocity_y < 6:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y, = collision_resolution(self, temp_x, temp_y)

        if self.collides(player):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        AbsEnemy.take_damage(self, attacker, damage)
        if self.active and not self.invincible:
            knockback(self, attacker, 2)
            self.invincible = True
            self.invincibility_timer = INVINCIBILITY_DURATION

    class Bone(AbsProjectile):

        DURATION = 45
        POWER = 1
        WIDTH = 8
        HEIGHT = 8
        MAX_DISTANCE = 128

        def __init__(self, parent, target):

            x = parent.x + parent.width / 2 - Skeleton.Bone.WIDTH / 2
            y = parent.y + parent.width / 2 - Skeleton.Bone.HEIGHT / 2

            AbsProjectile.__init__(self, parent, x, y, 0, 0, 0)

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
            self.velocity_y = float((py + 0.5 * GRAVITY * Skeleton.Bone.DURATION * Skeleton.Bone.DURATION - self.y)
                                    / Skeleton.Bone.DURATION) * -1

        def render(self):
            Graphics.set_color(255, 255, 255)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            player = self.collides_name('player')
            if player is not None:
                player.take_damage(self, Skeleton.Bone.POWER)
                self.destroy()

        def move(self):
            self.velocity_y += GRAVITY
            self.x += self.velocity_x
            self.y += self.velocity_y

            if abs(self.velocity_y) > 6:
                if self.velocity_y < 0:
                    self.velocity_y = -6
                else:
                    self.velocity_y = 6


class SmallGolem(AbsEnemy):
    """ Walks towards the player"""

    SPEED = 1

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 10
        self.height = 10

        self.sprite = AssetManager.get_image('SMALL_GOLEM')

        self.facing_x = 0

    def render(self):
        if self.facing_x == 1:
            Graphics.draw_image(self.sprite, self.x, self.y)
        else:
            Graphics.draw_image(self.sprite, self.x, self.y, Graphics.FLIP_X)

    def update(self):
        temp_x = self.x
        temp_y = self.y

        player = core.ENTITY_ROOM.player

        if player.x < self.x:
            temp_x -= SmallGolem.SPEED
            self.facing_x = 1
        elif player.x > self.x + self.width:
            temp_x += SmallGolem.SPEED
            self.facing_x = -1

        if self.velocity_y < 6:
            self.velocity_y += GRAVITY
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = collision_resolution(self, temp_x, temp_y)

        if self.collides(player):
            player.take_damage(self, 1)


class Solid(Entity):

    def __init__(self, x, y, width, height, slanted=False, flip_x=False, flip_y=False):
        Entity.__init__(self, x, y)

        self.group = 'solid'
        self.width = width
        self.height = height

        self.solid = True
        if GC.DEBUG:
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
        if GC.DEBUG and Input.down('g'):
            Graphics.set_color(155, 155, 155)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)


class Spikes(Entity):
    def __init__(self, x, y, width):
        Entity.__init__(self, x, y)

        self.width = width
        self.height = 16
        self.visible = False

    def update(self):
        player = core.ENTITY_ROOM.player
        collisions = self.collides_group('enemy')
        collisions.append(player if self.collides(player) else None)

        for collision in collisions:
            if collision:
                collision.take_damage(self, 100)


class Switch(Entity):

    def __init__(self, x, y, on_activate):
        Entity.__init__(self, x, y)
        self.group = 'switch'

        self.width = 16
        self.height = 16
        self.solid = True

        self.activated = False
        self.on_activate = on_activate

        self.sprite = SpriteMap(AssetManager.get_image('SWITCH'), 16, 16)
        self.sprite.add('ON', [1])
        self.sprite.add('OFF', [0])
        

    def activate(self):
        if not self.activated:
            exec self.on_activate
            self.activated = True

    def render(self):
        self.sprite.play('ON' if self.activated else 'OFF')
        self.sprite.render(self.x, self.y)


class Weight(Entity):
    
    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'weight'

        self.width = 16
        self.height = 16
        self.solid = True

        self.sprite = AssetManager.get_image('WEIGHT')

    def render(self):
        Graphics.draw_image(self.sprite, self.x, self.y)

    def update(self):
        temp_y = self.y
        self.velocity_y += GRAVITY if self.velocity_y < 6 else 0
        temp_y += self.velocity_y
        _, self.x, self.y, _, _ = collision_resolution(self, self.x, temp_y)


def collision_resolution(entity, temp_x, temp_y):
    vel_x = entity.velocity_x
    vel_y = entity.velocity_y

    collisions = entity.collides_solid(temp_x, temp_y)
    for collision in collisions:

        if not entity.collides(collision, temp_x, temp_y):
            continue

        elif collision.group == 'solid' and collision.slanted:
            
            # TODO fix snag at top of slope

            left = collision.intersection(temp_x)
            right = collision.intersection(temp_x + entity.width)

            if temp_y + entity.height > left or temp_y + entity.height > right:
                if collision.y < left < right:
                    temp_y = left - entity.height
                elif collision.y < right < left:
                    temp_y = right - entity.height
                else:
                    temp_y = collision.y - entity.height
                vel_y = 0

        elif collision.group == 'platform':

            if collision.ignore_player:
                continue

            if temp_y - entity.height - vel_y < collision.y and vel_y > 0:
                vel_y = 0
                temp_y = collision.y - entity.height

        elif not entity.collides(collision, temp_x, entity.y):
            if temp_y - entity.height - vel_y < collision.y and vel_y > 0:
                temp_y = collision.y - entity.height
            elif temp_y + vel_y > collision.y - collision.height and vel_y < 0:
                temp_y = collision.y + collision.height
            vel_y = 0

        elif not entity.collides(collision, entity.x, temp_y):
            if temp_x - entity.width - vel_x < collision.x and vel_x > 0:
                temp_x = collision.x - entity.width
            elif temp_x + vel_x > collision.x - collision.width and vel_x < 0:
                temp_x = collision.x + collision.width
            vel_x = 0

        else:
            temp_x = entity.x
            temp_y = entity.y
            vel_x = 0
            vel_y = 0
            break

    collision_occurred = len(collisions) > 0

    return collision_occurred, temp_x, temp_y, vel_x, vel_y


def knockback(entity, attacker, force):
    temp_x = entity.x
    temp_y = entity.y
    if attacker.x < entity.x:
        entity.velocity_x = force
    elif attacker.x > entity.x:
        entity.velocity_x = -force
    temp_x += entity.velocity_x * 4

    if attacker.y < entity.y:
        entity.velocity_y = force / 2
    elif attacker.y > entity.y:
        entity.velocity_y = -force / 2
    temp_y += entity.velocity_y * 2

    _, entity.x, entity.y, entity.velocity_x, entity.velocity_y = collision_resolution(entity, temp_x, temp_y)

    
def solid_below(entity, x, y):
    if entity.collides_solid(x, y + 1):
        return True
    else:
        return False
