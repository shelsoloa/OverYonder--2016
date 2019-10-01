import peachy
from peachy import PC
from peachy.utils import Key

from game import config

from .utility import GRAVITY, MAX_GRAVITY, collision_resolution, \
    solid_below, xcollides_solid, knockback

from .projectile import Projectile


class Player(peachy.Entity):

    WIDTH = 10
    HEIGHT = 12

    BASE_HEALTH = 5
    BASE_AMMO = 3

    CLIMB_SPEED = 2
    DASH_DURATION = 20
    DASH_SPEED = 4
    JUMP_SPEED = 3.75
    SWIM_SPEED = 2
    WALK_ACCEL_SPEED = 0.5
    WALK_MAX_SPEED = 2.5

    STATE_STANDARD = 'standard'
    STATE_CLIMBING = 'climbing'
    STATE_PUNCHING = 'punching'
    STATE_SWIMMING = 'swimming'

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = 'player'

        self.width = Player.WIDTH
        self.height = Player.HEIGHT

        self.state = Player.STATE_STANDARD

        self.sprite = Player.Sprite()

        self.items = [Player.Item.ID_FIST, Player.Item.ID_PLANET_OBERON]
        self.weapon = Player.Weapon()

        self.facing_x = 1
        self.facing_y = 0

        self.max_health = Player.BASE_HEALTH
        self.health = Player.BASE_HEALTH
        self.max_ammo = 0
        self.ammo = 0

        self.invincible = False
        self.invincibility_timer = 0

        self.dash_active = False
        self.dash_available = False
        self.dash_timer = 0

        self.double_jump_available = False

        self.climb_handle = None

        # self.sfx_timer_footstep = 0
        # self.sfx_footstep = Sound(AssetManager.get_sound("FOOTSTEP"))

    def change_state(self, new_state, handle=None):
        if new_state == Player.STATE_CLIMBING:
            if handle is None or handle.group != 'climbable':
                print('*ERROR* Object is not climbable"')
                return

            self.climb_handle = handle
            self.x = handle.x
            self.velocity_x = 0
            self.velocity_y = 0

            if Player.Item.ID_DASH_BOOTS in self.items:
                self.dash_active = False
                self.dash_available = True
                self.dash_timer = 0

            if Player.Item.ID_DOUBLE_JUMP in self.items:
                self.double_jump_available = True

        self.state = new_state

    def render(self):
        if PC.debug and Key.down('g'):
            peachy.graphics.set_color(255, 255, 255)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        if self.invincible:
            # TODO add blinking
            peachy.graphics.set_color(0, 0, 255)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        self.sprite.validate(self)
        self.sprite.render(self.x, self.y)

    def take_damage(self, attacker, damage):
        if self.state != Player.STATE_PUNCHING:
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

        submerged_line = temp_y - self.height / 2 + 1
        has_solid_below = solid_below(self, temp_x, temp_y)
        in_water = self.collides_group('water', temp_x, submerged_line)

        # GENERAL - Poll Key
        KEYDOWN_DOWN = Key.down(config.KEY['DOWN'])
        KEYDOWN_LEFT = Key.down(config.KEY['LEFT'])
        KEYDOWN_RIGHT = Key.down(config.KEY['RIGHT'])
        KEYDOWN_UP = Key.down(config.KEY['UP'])
        KEYPRESSED_ATTACK = Key.pressed(config.KEY['ATTACK'])
        KEYPRESSED_CHANGE_WEAPON = Key.pressed(config.KEY['CHANGE_WEAPON'])
        KEYPRESSED_JUMP = Key.pressed(config.KEY['JUMP'])
        KEYPRESSED_INTERACT = Key.pressed(config.KEY['INTERACT'])
        KEYRELEASED_JUMP = Key.released(config.KEY['JUMP'])
        KEYPRESSED_DASH = Key.pressed(config.KEY['DASH'])

        # GENERAL - Updates & Timers
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if Player.Item.ID_DOUBLE_JUMP in self.items:
            if not self.double_jump_available:
                if has_solid_below:
                    self.double_jump_available = True

        if self.weapon.active:
            self.weapon.update()

        # if self.sfx_timer_footstep > 0:
        #     self.sfx_timer_footstep -= 1

        # GENERAL - Change Weapon
        if KEYPRESSED_CHANGE_WEAPON:
            self.weapon.cycle(self.items)
            self.sprite.change_set(self.weapon.current)

        # STANDARD
        if self.state == Player.STATE_STANDARD:

            # STANDARD - USER INPUT - Interaction
            if KEYPRESSED_INTERACT:
                interactables = self.collides_group('interactable')
                if interactables:
                    interactable = interactables[0]
                    interactable.interact(self)

            # STANDARD - USER INPUT - Attack
            if KEYPRESSED_ATTACK and not self.weapon.active:
                self.weapon.activate(self)
                # TODO Play weapon sound

            # STANDARD - USER INPUT - Movement
            if self.velocity_x > Player.WALK_MAX_SPEED:
                self.velocity_x -= Player.WALK_ACCEL_SPEED * 2
            elif self.velocity_x < -Player.WALK_MAX_SPEED:
                self.velocity_x += Player.WALK_ACCEL_SPEED * 2

            if KEYDOWN_LEFT == KEYDOWN_RIGHT:
                if self.velocity_x != 0:
                    if self.velocity_x > 0:
                        self.velocity_x -= Player.WALK_ACCEL_SPEED
                    else:
                        self.velocity_x += Player.WALK_ACCEL_SPEED
            else:
                if KEYDOWN_LEFT and self.velocity_x > -Player.WALK_MAX_SPEED:
                    self.velocity_x -= Player.WALK_ACCEL_SPEED
                    self.facing_x = -1
                if KEYDOWN_RIGHT and self.velocity_x < Player.WALK_MAX_SPEED:
                    self.velocity_x += Player.WALK_ACCEL_SPEED
                    self.facing_x = 1
                # if has_solid_below and self.sfx_timer_footstep <= 0:
                #     self.sfx_footstep.play()
                #     self.sfx_timer_footstep = 15

            if KEYDOWN_UP or KEYDOWN_DOWN:
                if KEYDOWN_UP:
                    collides_climbable = self.collides_group('climbable')
                    if collides_climbable:
                        climb_handle = collides_climbable[0]
                        self.change_state(Player.STATE_CLIMBING, climb_handle)
                        return  # Do not continue with standard state
                    self.facing_y = -1
                if KEYDOWN_DOWN:
                    if not has_solid_below:
                        self.facing_y = 1
            else:
                self.facing_y = 0

            # STANDARD - USER INPUT - Dash
            if Player.Item.ID_DASH_BOOTS in self.items:
                if not self.dash_available and not self.dash_active:
                    if self.dash_timer > 0:
                        self.dash_timer -= 1
                    else:
                        self.dash_available = has_solid_below
                if KEYPRESSED_DASH and self.dash_available and \
                   not self.dash_active:
                    self.dash_active = True
                    self.dash_timer = Player.DASH_DURATION
                if self.dash_active:
                    self.velocity_x = Player.DASH_SPEED * self.facing_x
                    self.dash_timer -= 1
                    if self.dash_timer <= 0:
                        self.dash_active = False
                        self.dash_available = False
                        self.dash_timer = Player.DASH_DURATION / 4

            # STANDARD - USER INPUT - Jump
            if KEYDOWN_DOWN and KEYPRESSED_JUMP:  # Jump down from platform
                platforms = self.collides_group('platform', self.x, self.y + 1)
                if platforms:
                    for platform in platforms:
                        platform.solid = False
                elif has_solid_below:
                    self.velocity_y = -Player.JUMP_SPEED
                    if Player.Item.ID_DASH_BOOTS in self.items:
                        self.dash_available = True
            elif KEYPRESSED_JUMP:
                if has_solid_below:  # Standard jump
                    self.velocity_y = -Player.JUMP_SPEED
                    if Player.Item.ID_DASH_BOOTS in self.items:
                        self.dash_available = True
                elif self.double_jump_available:  # Double jump
                    self.velocity_y = -Player.JUMP_SPEED
                    self.double_jump_available = False
            elif KEYRELEASED_JUMP:
                if self.velocity_y < 0:
                    self.velocity_y /= 2

            # STANDARD - Gravity & Finalize
            if self.velocity_y < MAX_GRAVITY:
                self.velocity_y += GRAVITY
            if self.dash_active:
                self.velocity_y = 0

            if in_water:
                self.state = Player.STATE_SWIMMING

        # CLIMBING
        elif self.state == Player.STATE_CLIMBING:

            # CLIMBING - USER INPUT
            if KEYDOWN_UP:
                temp_y -= Player.CLIMB_SPEED
                if temp_y < self.climb_handle.y:
                    temp_y = self.climb_handle.y
            if KEYDOWN_DOWN:
                temp_y += Player.CLIMB_SPEED
                if temp_y > self.climb_handle.bottom:
                    self.change_state(Player.STATE_STANDARD)
            if KEYPRESSED_JUMP:
                self.velocity_y = -Player.JUMP_SPEED
                self.change_state(Player.STATE_STANDARD)

        # PUNCHING
        elif self.state == Player.STATE_PUNCHING:
            if self.velocity_x != 0:
                if self.velocity_x > 0:
                    self.velocity_x -= Player.WALK_ACCEL_SPEED
                else:
                    self.velocity_x += Player.WALK_ACCEL_SPEED

            if in_water:
                self.state = Player.STATE_SWIMMING

        # SWIMMING
        elif self.state == Player.STATE_SWIMMING:
            if self.velocity_x > Player.SWIM_SPEED:
                self.velocity_x -= Player.WALK_ACCEL_SPEED
            elif self.velocity_x < -Player.SWIM_SPEED:
                self.velocity_x += Player.WALK_ACCEL_SPEED

            if KEYDOWN_LEFT == KEYDOWN_RIGHT:
                if self.velocity_x != 0:
                    if self.velocity_x > 0:
                        self.velocity_x -= Player.WALK_ACCEL_SPEED
                    else:
                        self.velocity_x += Player.WALK_ACCEL_SPEED
            else:
                if KEYDOWN_LEFT and self.velocity_x > -Player.SWIM_SPEED:
                    self.velocity_x -= Player.WALK_ACCEL_SPEED
                    self.facing_x = -1
                if KEYDOWN_RIGHT and self.velocity_x < Player.SWIM_SPEED:
                    self.velocity_x += Player.WALK_ACCEL_SPEED
                    self.facing_x = 1

            if KEYPRESSED_JUMP:
                self.velocity_y = -Player.JUMP_SPEED

            if not in_water:
                self.state = Player.STATE_STANDARD
            else:
                water_apex = in_water[0].y

                if self.velocity_y >= 0:
                    self.velocity_y -= Player.WALK_ACCEL_SPEED
                    if self.velocity_y < 0:
                        self.velocity_y = -Player.WALK_ACCEL_SPEED

                if self.velocity_y > -2:
                    temp_y2 = temp_y + self.velocity_y + (self.height / 2)
                    if temp_y2 < water_apex and not KEYPRESSED_JUMP:
                        temp_y = water_apex - (self.height / 2)
                        self.velocity_y = 0

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        # FINALIZE - Collision Detection
        collision_occurred, temp_x, temp_y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

        if collision_occurred:
            self.dash_active = False

        # FINALIZE - Update Location
        self.x = temp_x
        self.y = temp_y

    class Item(list):  # ItemHandler
        ID_DASH_BOOTS = 'DASH'
        ID_DOUBLE_JUMP = 'DBLJ'
        ID_SUPER_SUIT = 'SUPS'

        ID_FIST = 'FIST'
        ID_PISTOL = 'PIST1'
        ID_PISTOL_LEVEL_TWO = 'PIST2'
        ID_PISTOL_LEVEL_THREE = 'PIST3'
        ID_MISSILE = 'MISS'
        ID_MISSILE_LEVEL_TWO = 'MISS2'

        ID_PLANET_OBERON = 'OBE'
        ID_PLANET_REPTILIA = 'REP'
        ID_PLANET_TEKTONIA = 'TEK'

    class Sprite(object):

        def __init__(self):
            spritesheet = peachy.fs.get_image('PLAYER')

            self.anim_name = 'IDLE'
            self.set_name = Player.Item.ID_FIST

            none_sprite = peachy.graphics.SpriteMap(spritesheet, 16, 16,
                                                    origin_x=3, origin_y=4)
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

            pist_sprite = peachy.graphics.SpriteMap(spritesheet, 16, 16,
                                                    origin_x=1, origin_y=4)
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

            miss_sprite = peachy.graphics.SpriteMap(spritesheet, 16, 16,
                                                    origin_x=1, origin_y=4)
            miss_sprite.add('IDLE', [30])
            miss_sprite.add('JUMP', [31])
            miss_sprite.add('RUN', [31, 30, 32, 30], 10, True)
            miss_sprite.play('IDLE')

            self.spritesets = {
                Player.Item.ID_FIST: none_sprite,
                Player.Item.ID_PISTOL: pist_sprite,
                Player.Item.ID_MISSILE: miss_sprite,
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

        def resume(self):
            self.current_sprite.resume()

        def stop(self):
            self.current_sprite.stop()

        def render(self, x, y):
            self.current_sprite.render(x, y)

        def validate(self, player):
            flip_x = player.facing_x == 1
            flip_required = flip_x != self.current_sprite.flipped_x

            if self.anim_name[:6] != 'ATTACK' or not player.weapon.active:
                if not solid_below(player, player.x, player.y):
                    if Key.down('down'):
                        self.play("JUMP_LOOKING_DOWN", flip_x)
                    elif Key.down('up'):
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

        def __init__(self):
            self.active = False
            self.cooldown = 0

            self.current = Player.Item.ID_FIST
            self.current_index = 0

        def activate(self, player):
            facing_x = player.facing_x if player.facing_y == 0 else 0

            attack = None

            if self.current == Player.Item.ID_FIST:
                attack = Player.Punch(player, player.x, player.y,
                                      facing_x, player.facing_y)

            elif self.current == Player.Item.ID_PISTOL:
                attack = Player.PeaBullet(player, player.x, player.y,
                                          facing_x, player.facing_y)

            elif self.current == Player.Item.ID_MISSILE:
                attack = Player.Missile(player, player.x, player.y,
                                        facing_x, player.facing_y)

            else:
                if PC.debug:
                    print('*ERROR* could not use weapon ' + self.current)
                return

            player.container.add(attack)
            self.active = True
            self.cooldown = attack.COOLDOWN

        def cycle(self, items):
            weapon_ids = [
                Player.Item.ID_FIST,
                Player.Item.ID_PISTOL,
                Player.Item.ID_MISSILE
            ]

            start = self.current_index - 1
            while start != self.current_index:
                self.current_index += 1
                if self.current_index >= len(items):
                    self.current_index = 0

                item = items[self.current_index]
                if item in weapon_ids:
                    break

            self.current = items[self.current_index]

        def update(self):
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.active = False

    class PeaBullet(Projectile):

        DAMAGE = 1
        COOLDOWN = 3
        SPEED = 6
        LIFESPAN = 20

        def __init__(self, parent, x, y, direction_x, direction_y):
            super().__init__(parent, x, y, direction_x, direction_y,
                             Player.PeaBullet.SPEED,
                             Player.PeaBullet.LIFESPAN)
            self.width = 12
            self.height = 12

        def render(self):
            peachy.graphics.set_color(255, 0, 0)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collisions = xcollides_solid(self, self.x, self.y) + \
                self.collides_groups(None, None, 'breakable', 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.member_of('breakable'):
                        collision.destroy()
                    elif collision.member_of('enemy'):
                        collision.take_damage(self, Player.PeaBullet.DAMAGE)
                    elif collision.member_of('switch'):
                        collision.activate()
                    self.destroy()

    class Punch(peachy.Entity):

        DAMAGE = 2
        COOLDOWN = 12
        LIFESPAN = 13
        THRUST = 9

        def __init__(self, parent, x, y, direction_x, direction_y):
            peachy.Entity.__init__(self, x, y)
            self.parent = parent
            self.width = 12
            self.height = 12
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

            parent.state = Player.STATE_PUNCHING
            # player.velocity_y will equal 0 after gravity
            parent.velocity_y = -GRAVITY

        def destroy(self):
            self.parent.state = Player.STATE_STANDARD
            super().destroy()

        def render(self):
            peachy.graphics.set_color(255, 0, 0)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def update(self):
            self.update_location()

            collisions = xcollides_solid(self, self.x, self.y) + \
                self.collides_groups(self.x, self.y, 'breakable', 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.member_of('breakable'):
                        collision.destroy()
                    elif collision.member_of('enemy'):
                        collision.take_damage(self, Player.Punch.DAMAGE)
                    elif collision.member_of('switch'):
                        collision.activate()
                    self.parent.velocity_x = 0

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

    class Missile(Projectile):

        DAMAGE = 4
        COOLDOWN = 30
        SPEED = 10
        LIFESPAN = 40

        def __init__(self, parent, x, y, direction_x, direction_y):
            super().__init__(parent, x, y, direction_x, direction_y,
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
                peachy.graphics.set_color(255, 255, 255)
            elif self.state == 'exploding':
                peachy.graphics.set_color(255, 70, 0)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collisions = xcollides_solid(self) + \
                self.collides_groups(None, None, 'breakable',
                                     'breakable-reinforced', 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.member_of('breakable'):
                        collision.destroy()
                    elif collision.member_of('enemy'):
                        collision.take_damage(self, Player.Missile.DAMAGE)
                    elif collision.member_of('switch'):
                        collision.activate()
                    elif collision.member_of('breakable-reinforced'):
                        collision.destroy()
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
