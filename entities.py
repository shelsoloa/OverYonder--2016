import config
import core
import random
from abc import ABCMeta, abstractmethod
from core import AssetManager, GC, Entity, Graphics, Input
from common import SpriteMap, splice_image

try:
    import states
except ImportError:
    print 'error'
    pass # circular dependency work around

# Entity constants
INVINCIBILITY_DURATION = 20
GRAVITY = 0.2
MAX_GRAVITY = 6

# TODO player cannot be hurt while punching
# TODO add enemy attack abstract base class?

def display_choice(message, callback):
    GC.world.change_state(states.DECISION_STATE, message, callback)

def display_message(message):
    GC.world.change_state(states.MESSAGE_STATE, message)


def drop(x, y, drop_rate=25, missile_rate=20):
    # 25% chance to drop
    success = random.randint(0, 99) < drop_rate
    if success:
        drop = None
        player = core.ENTITY_ROOM.player
        if Player.Item.ID_MISSILE in player.items:
            success = random.randint(0, 99) < missile_rate
            if success:
                drop = AmmoDrop(x, y)
            else:
                drop = HealthDrop(x, y)
        else:
            drop = HealthDrop(x, y)
        core.ENTITY_ROOM.add(drop)


class AbsClimbable(Entity):
    def __init__(self, x, y, height):
        Entity.__init__(self, x, y)
        self.group = 'climbable'

        self.width = 16
        self.height = height

        self.bottom = self.y + height

    def render(self):
        Graphics.set_color(0, 255, 0)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)


class AbsDrop(Entity):
    __metaclass__ = ABCMeta

    DURATION = 225  # 5 seconds

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'drop'
        self.width = 4
        self.height = 4
        self.lifespan = AbsDrop.DURATION

    @abstractmethod
    def perform_action(self, player):
        return

    def update(self):
        player = core.ENTITY_ROOM.player
        if self.collides(player):
            self.perform_action(player)
        
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.destroy()


class AbsEnemy(Entity):
    __metaclass__ = ABCMeta

    STATE_AGGRO = 'aggro'
    STATE_IDLE = 'idle'
    STATE_STUNNED = 'stun'

    def __init__(self, x, y):
        Entity.__init__(self, x, y)
        self.group = 'enemy'

        self.health = 0
        self.invincible = False
        self.invincibility_timer = 0

        self.facing_x = 0
        self.facing_y = 0

    def take_damage(self, attacker, damage):
        if not self.invincible:
            self.health -= damage
            if self.health <= 0:
                self.destroy()

    def _take_damage_and_knockback(self, attacker, damage, force):
        AbsEnemy.take_damage(self, attacker, damage)
        if self.active and not self.invincible:
            knockback(self, attacker, force)
            self.invincible = True
            self.invincibility_timer = INVINCIBILITY_DURATION


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


class AmmoDrop(AbsDrop):
    def __init__(self, x, y):
        AbsDrop.__init__(self, x, y)
    def render(self):
        Graphics.set_color(200, 200, 200)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)
    def perform_action(self, player):
        # TODO add missile ammo
        # if player.missiles < Player.MAX_AMMO:
        #     player.missiles += 1
        self.destroy()


class HealthDrop(AbsDrop):
    def __init__(self, x, y):
        AbsDrop.__init__(self, x, y)
    def render(self):
        Graphics.set_color(0, 255, 0)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)
    def perform_action(self, player):
        if player.health < player.max_health:
            player.health += 1
        self.destroy()


class ArrowTrap(Entity):

    ARROW_COOLDOWN = 90

    def __init__(self, x, y, direction):
        Entity.__init__(self, x, y)
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
        Graphics.set_color(210, 180, 140)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def shoot(self):
        self.arrow_timer = ArrowTrap.ARROW_COOLDOWN
        arrow = ArrowTrap.Arrow(self, self.direction_x)
        core.ENTITY_ROOM.add(arrow)

    def update(self):
        if self.arrow_timer > 0:
            self.arrow_timer -= 1
        else:
            player = core.ENTITY_ROOM.player

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
            
    class Arrow(AbsProjectile):

        SPEED = 5
        LIFESPAN = -1

        def __init__(self, parent, direction):
            ax = parent.x + direction * parent.width
            AbsProjectile.__init__(self, parent, ax, parent.y + 6, direction, 0, 
                                   ArrowTrap.Arrow.SPEED, ArrowTrap.Arrow.LIFESPAN)
            self.width = 10
            self.height = 4

        def render(self):
            Graphics.set_color(255, 0, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def collision(self):
            collision = self.collides_name('player')
            if collision:
                collision.take_damage(self, 1)
                self.destroy()

            collision = xcollides_solid(self)
            if len(collision) > 0:
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

        # TODO add aggro distance

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
        self._take_damage_and_knockback(attacker, damage, 2)


class Boulder(Entity):

    SPEED = 2.5

    def __init__(self, x, y, direction):
        # TODO activity zone immune
        Entity.__init__(self, x, y)
        self.group = 'boulder'

        self.width = 32
        self.height = self.width
        self.dx = direction

        self.velocity_x = Boulder.SPEED * self.dx

    def render(self):
        Graphics.set_color(50, 50, 50)
        Graphics.draw_circle(self.x, self.y, self.width)

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

        if self.collides(core.ENTITY_ROOM.player):
            core.ENTITY_ROOM.player.take_damage(self, 3)

        if self.velocity_x == 0 and self.velocity_y == 0:
            self.destroy()


class BoulderSpawner(Entity):

    SPAWN_DELAY = 80

    def __init__(self, x, y, direction):
        # TODO activity zone immune
        Entity.__init__(self, x, y)
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
        Graphics.set_color(200, 200, 100)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.spawn_delay -= 1
        if self.spawn_delay < 0:
            self.spawn_delay = BoulderSpawner.SPAWN_DELAY
            boulder = Boulder(self.x + self.width * self.spawn_dx, self.y, self.spawn_dx)
            core.ENTITY_ROOM.add(boulder)


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


class BreakableReinforcedTile(Entity):

    def __init__(self, x, y, width, height):
        Entity.__init__(self, x, y)
        self.group = 'breakable-reinforced'

        self.width = width
        self.height = height
        self.solid = True

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)


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

        # def hit_callback(self):
        #    self.sprite.play('NORMAL')

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

        collision_occured, self.x, self.y, _, _ = \
            collision_resolution(self, temp_x, temp_y)

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


class GoblinImp(AbsEnemy):

    JUMP_COOLDOWN = 90
    AIR_SPEED = 2.75
    MOVE_SPEED = 0.5
    JUMP_SPEED = 2.25

    AGGRO_DISTANCE_X = 64
    AGGRO_DISTANCE_Y = 16

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.health = 5

        self.width = 8
        self.height = 8

        self.state = AbsEnemy.STATE_IDLE

        self.jumping = False
        self.jump_direction = 0
        self.jump_timer = 0

    def render(self):
        Graphics.set_color(197, 182, 128)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        has_solid_below = solid_below(self, temp_x, temp_y)
        player = core.ENTITY_ROOM.player

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == AbsEnemy.STATE_AGGRO:
            if self.jumping:
                if has_solid_below:
                    self.jumping = False
                else:
                    temp_x += GoblinImp.AIR_SPEED * self.jump_direction
            else:
                if temp_x < player.x:
                    temp_x += GoblinImp.MOVE_SPEED
                elif temp_x > player.x:
                    temp_x -= GoblinImp.MOVE_SPEED

            if self.jump_timer > 0:
                self.jump_timer -= 1
            elif has_solid_below:
                self.velocity_y = -GoblinImp.JUMP_SPEED
                self.jump_timer = GoblinImp.JUMP_COOLDOWN
                self.jumping = True
                if player.x > self.x + self.width:
                    self.jump_direction = 1
                elif player.x + player.width < self.x:
                    self.jump_direction = -1
                else:
                    self.jump_direction = 0
        
        elif self.state == AbsEnemy.STATE_IDLE:
            # TODO add wandering movement to simulate natural life etc etc
            player_distance_x = abs(self.x - player.x)
            player_distance_y = abs(self.y - player.y)

            if player_distance_x < GoblinImp.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinImp.AGGRO_DISTANCE_Y:
                self.state = AbsEnemy.STATE_AGGRO

        if self.velocity_x != 0:
            self.velocity_x += 0.25 if self.velocity_x < 0 else -0.25

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)
        
        if self.collides(player):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1.5)
        self.state = AbsEnemy.STATE_AGGRO


class GoblinSpearman(AbsEnemy):
    # TODO complete this class if design makes sense

    SAFE_DISTANCE = -1
    STATE_PRE_ATTACK = 'prep'
    AGGRO_DISTANCE_X = 128
    AGGRO_DISTANCE_Y = 32

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.state = GoblinSpearman.STATE_IDLE
        self.state_timer = 0

    def render(self):
        if self.state == GoblinSpearman.STATE_PRE_ATTACK:
            Graphics.set_color(255, 0, 0)
        else:
            Graphics.set_color(197, 182, 128)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        player = core.ENTITY_ROOM.player

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == GoblinSwordsman.STATE_IDLE:
            player_distance_x = abs(temp_x - player.x)
            player_distance_y = abs(temp_y - player.y)

            if player_distance_x < GoblinSwordsman.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinSwordsman.AGGRO_DISTANCE_Y:
                self.state = AbsEnemy.STATE_AGGRO
        elif self.state == AbsEnemy.STATE_AGGRO:
            player_distance_x = abs(temp_x - player.x)
            if player_distance_x < GoblinSpearman.SAFE_DISTANCE:
                # Move towards player
                return
            elif player_distance_x > GoblinSpearman.SAFE_DISTANCE:
                # Move away from player
                return
            

class GoblinSwordsman(AbsEnemy):

    MOVE_SPEED = 1
    ACCEL_SPEED = 0.2

    AGGRO_DISTANCE_X = 124
    AGGRO_DISTANCE_Y = 64

    STATE_PRE_ATTACK = 'pre-attack'
    STATE_ATTACKING = 'attacking'

    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.health = 5

        self.state = AbsEnemy.STATE_IDLE
        self.state_timer = 0

    def render(self):
        if self.state == GoblinSwordsman.STATE_PRE_ATTACK:
            Graphics.set_color(255, 0, 0)
        else:
            Graphics.set_color(197, 182, 128)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        player = core.ENTITY_ROOM.player

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == AbsEnemy.STATE_IDLE:
            player_distance_x = abs(temp_x - player.x)
            player_distance_y = abs(temp_y - player.y)

            if player_distance_x < GoblinSwordsman.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinSwordsman.AGGRO_DISTANCE_Y:
                self.state = AbsEnemy.STATE_AGGRO

        elif self.state == GoblinSwordsman.STATE_PRE_ATTACK:
            self.state_timer -= 1
            if self.state_timer < 0:
                ax = self.x + 16 * self.facing_x
                core.ENTITY_ROOM.add(GoblinSwordsman.Attack(self, ax, self.y))
                self.state = GoblinSwordsman.STATE_ATTACKING
                self.state_timer = GoblinSwordsman.Attack.DURATION

        elif self.state == GoblinSwordsman.STATE_ATTACKING:
            self.state_timer -= 1
            if self.state_timer < 0:
                self.state = AbsEnemy.STATE_AGGRO

        elif self.state == AbsEnemy.STATE_AGGRO:
            if temp_x < player.x and self.velocity_x < GoblinSwordsman.MOVE_SPEED:
                self.facing_x = 1
                self.velocity_x += GoblinSwordsman.ACCEL_SPEED
            elif temp_x > player.x and self.velocity_x > -GoblinSwordsman.MOVE_SPEED:
                self.facing_x = -1
                self.velocity_x -= GoblinSwordsman.ACCEL_SPEED

            attack_rect = (0, 0, 0, 0)
            if self.facing_x == 1:
                attack_rect = (self.x + 16, self.y, 32, self.height)
            elif self.facing_x == -1:
                attack_rect = (self.x - 32, self.y, 32, self.height)

            if player.collides_rect(attack_rect):
                self.velocity_x = 0
                self.state = GoblinSwordsman.STATE_PRE_ATTACK
                self.state_timer = GoblinSwordsman.Attack.DURATION

        elif self.state == AbsEnemy.STATE_STUNNED:
            if self.velocity_x > 0:
                self.velocity_x -= GoblinSwordsman.ACCEL_SPEED
            elif self.velocity_x < 0:
                self.velocity_x += GoblinSwordsman.ACCEL_SPEED
            self.state_timer -= 1
            if self.state_timer < 0:
                self.state = AbsEnemy.STATE_AGGRO

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1)
        self.state = AbsEnemy.STATE_AGGRO  # AbsEnemy.STATE_STUNNED
        # self.state_timer = INVINCIBILITY_DURATION / 4
    
    class Attack(Entity):

        DAMAGE = 3
        DURATION = 30
        
        def __init__(self, parent, x, y):
            Entity.__init__(self, x, y)
            self.parent = parent
            self.width = 16
            self.height = 16
            self.lifespan = GoblinSwordsman.Attack.DURATION

        def render(self):
            Graphics.set_color(255, 0, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def update(self):
            if self.lifespan > 0:
                self.lifespan -= 1
                player = core.ENTITY_ROOM.player
                if self.collides(player):
                    player.take_damage(self, GoblinSwordsman.Attack.DAMAGE)
            else:
                self.destroy()


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
            if self.global_id == Player.Item.ID_PISTOL:
                self.sprite = sprites[1]
            elif self.global_id == Player.Item.ID_MISSILE:
                self.sprite = sprites[2]
        else:
            self.sprite = None

    def render(self):
        if self.sprite == None:
            Graphics.set_color(0, 0, 0)
        Graphics.draw_image(self.sprite, self.x, self.y)

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


class MapEvent(Entity):

    def __init__(self, x, y, width, height, name, update_script):
        Entity.__init__(self, x, y)
        self.group = 'event'
        self.name = name
        self.width = width
        self.height = height

        self.update_script = update_script
        # TODO all of this


class MovingPlatform(Entity):

    SPEED = 1
    ZONE_SIZE = 2
    WAIT_TIME = 60

    # TODO Move to end when player is near end
    # TODO change from flags to states
    
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
        self.wait_timer = 0

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
            player_solid_collisions = xcollides_solid(player, player_temp_x, player_temp_y)
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
        Entity.__init__(self, x, y)
        self.name = 'player'

        self.width = Player.WIDTH
        self.height = Player.HEIGHT

        self.state = Player.STATE_STANDARD
        
        self.sprite = Player.Sprite()

        self.items = [ Player.Item.ID_FIST, Player.Item.ID_PLANET_OBERON ]
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


    def change_state(self, new_state, handle=None):
        if new_state == Player.STATE_CLIMBING:
            if handle is None or handle.group != 'climbable':
                print "*ERROR* Object is not climbable"
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

        # GENERAL - Poll Keys 
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

        # USER INPUT - Change Weapon
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

            if KEYDOWN_UP or KEYDOWN_DOWN:
                if KEYDOWN_UP:
                    collides_climbable = self.collides_group('climbable')
                    if collides_climbable:
                        climb_handle = collides_climbable[0]
                        self.change_state(Player.STATE_CLIMBING, climb_handle)
                        return
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

            # STANDARD - USER INPUT - Jump
            if KEYDOWN_DOWN and KEYPRESSED_JUMP:  # Jump down from platform
                platforms = self.collides_group('platform', self.x, self.y + 1)
                if platforms:
                    for platform in platforms:
                        platform.ignore_player = True
                elif has_solid_below:
                    self.velocity_y = -Player.JUMP_SPEED
                    if Player.Item.ID_DASH_BOOTS in self.items:
                        self.dash_available = True
            elif KEYPRESSED_JUMP:
                if has_solid_below:  # Standard jump
                    self.velocity_y = -Player.JUMP_SPEED
                    if Player.Item.ID_DASH_BOOTS in self.items:
                        self.dash_available = True 

                # DEP - Wall Jump
                # elif KEYDOWN_LEFT and self.collides_solid(self.x - 1, self.y):  # Wall jump - right
                #     self.velocity_x = Player.DASH_SPEED
                #     self.velocity_y = -Player.JUMP_SPEED
                # elif KEYDOWN_RIGHT and self.collides_solid(self.x + 1, self.y):  # Wall jump - left
                #     self.velocity_x = -Player.DASH_SPEED
                #     self.velocity_y = -Player.JUMP_SPEED

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

    class Sprite:

        def __init__(self):
            spritesheet = AssetManager.get_image('PLAYER')

            self.anim_name = 'IDLE'
            self.set_name = Player.Item.ID_FIST

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
                if GC.DEBUG:
                    print '*ERROR* could not use weapon ' + self.current
                return
            
            core.ENTITY_ROOM.add(attack)
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

    class PeaBullet(AbsProjectile):
        
        DAMAGE = 1
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
            collisions = xcollides_solid(self) + \
                         self.collides_groups(None, None, 
                                              'breakable', 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self, Player.PeaBullet.DAMAGE)
                    elif collision.group == 'switch':
                        collision.activate()
                    self.destroy()

    class Punch(Entity):

        DAMAGE = 2
        COOLDOWN = 12
        LIFESPAN = 13
        THRUST = 9

        def __init__(self, parent, x, y, direction_x, direction_y):
            Entity.__init__(self, x, y)
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
            Entity.destroy(self)

        def render(self):
            Graphics.set_color(255, 0, 0)
            Graphics.draw_rect(self.x, self.y, self.width, self.height)

        def update(self):
            self.update_location()

            collisions = xcollides_solid(self) + \
                         self.collides_groups(None, None, 
                                 'breakable', 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self.parent, Player.Punch.DAMAGE)
                    elif collision.group == 'switch':
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

    class Missile(AbsProjectile):
        
        DAMAGE = 4
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
            collisions = xcollides_solid(self) + \
                         self.collides_groups(None, None,
                                 'breakable', 'breakable-reinforced', 
                                 'enemy', 'switch')

            for collision in collisions:
                if collision:
                    if collision.group == 'breakable':
                        collision.destroy()
                    elif collision.group == 'enemy':
                        collision.take_damage(self, Player.Missile.DAMAGE)
                    elif collision.group == 'switch':
                        collision.activate()
                    elif collision.group == 'breakable-reinforced':
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


class ResourceSlug(AbsEnemy):

    SPEED = 1

    def __init__(self, parent, x, y, dx, dy):
        AbsEnemy.__init__(self, x, y)
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
        AbsEnemy.destroy(self)

    def render(self):
        Graphics.set_color(255, 0, 125)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

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

        if self.collides(core.ENTITY_ROOM.player):
            core.ENTITY_ROOM.player.take_damage(self, 1)



class ResourceSlugHive(Entity):

    SPAWN_CAP = 5
    SPAWN_TIME = 135

    def __init__(self, x, y, facing_direction, slug_direction):
        Entity.__init__(self, x, y)
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
        Graphics.set_color(200, 64, 64)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        if self.spawn_timer > 0:
            self.spawn_timer -= 1
        elif self.spawn_count < ResourceSlugHive.SPAWN_CAP:
            slug = ResourceSlug(self, self.x, self.y,
                                self.slug_direction_x,
                                self.slug_direction_y)
            core.ENTITY_ROOM.add(slug)
            self.spawn_count += 1
            self.spawn_timer = ResourceSlugHive.SPAWN_TIME


class RetractableDoor(Entity):
    
    def __init__(self, x, y, width, height):
        Entity.__init__(self, x, y)
        self.width = width
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
        display_choice("Would you like to record your progress?", self.save)
                        
    def save(self, result):
        if result:
            GC.world.save_game(config.SAVE_FILE)
            print 'Game Saved'


class Ship(AbsInteractable):

    def __init__(self, x, y):
        AbsInteractable.__init__(self, x, y)
        self.width = 16
        self.height = 16

    def render(self):
        Graphics.set_color(255, 255, 255)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def interact(self, player):
        # Enter ShipMenuState
        GC.world.change_state(states.SHIP_STATE)


class SignPost(AbsInteractable):

    def __init__(self, x, y, message):
        AbsInteractable.__init__(self, x, y)
        self.width = 16
        self.height = 16

        self.message = message

        self.sprite = AssetManager.get_image('SIGN_POST')
    
    def render(self):
        if core.ENTITY_ROOM.planet['name'] != 'reptilia':
            Graphics.draw_image(self.sprite, self.x, self.y)

    def interact(self, player):
        display_message(self.message)


class Skeleton(AbsEnemy):

    BONE_COOLDOWN = 90
    SPEED = Player.WALK_MAX_SPEED + 0.5
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
        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y, = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(player):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 2)

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

            if abs(self.velocity_y) > MAX_GRAVITY:
                if self.velocity_y < 0:
                    self.velocity_y = -MAX_GRAVITY
                else:
                    self.velocity_y = MAX_GRAVITY


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

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

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


class Spider(AbsEnemy):

    ACCEL_SPEED = 0.25
    MOVE_SPEED = 1.5

    STATE_DROPPING = 'dropping'

    AGGRO_DISTANCE_X = 16
    AGGRO_DISTANCE_Y = 128
    
    def __init__(self, x, y):
        AbsEnemy.__init__(self, x, y)
        self.width = 16
        self.height = 8
        self.health = 3
        self.state = AbsEnemy.STATE_IDLE

    def render(self):
        Graphics.set_color(0, 0, 255)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        player = core.ENTITY_ROOM.player

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == AbsEnemy.STATE_IDLE:
            player_distance_x = abs(temp_x - player.x)
            player_distance_y = player.y - temp_y  # Must be below

            if player_distance_x < Spider.AGGRO_DISTANCE_X and \
               0 < player_distance_y < Spider.AGGRO_DISTANCE_Y:
                self.state = Spider.STATE_DROPPING

        elif self.state == Spider.STATE_DROPPING:
            if solid_below(self, temp_x, temp_y):
                self.state = AbsEnemy.STATE_AGGRO

            if self.velocity_y < MAX_GRAVITY:
                self.velocity_y += GRAVITY

            if self.velocity_x != 0:
                self.velocity_x -= 0.25 if self.velocity_x > 0 else -0.25

        elif self.state == AbsEnemy.STATE_AGGRO:
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

        if self.collides(player):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1)
        self.state = Spider.STATE_DROPPING


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


class Water(Entity):

    def __init__(self, x, y, width, height):
        Entity.__init__(self, x, y)
        self.group = 'water'
        self.width = width
        self.height = height

    def render(self):
        Graphics.set_color(0, 0, 255)
        Graphics.draw_rect(self.x, self.y, self.width, self.height)


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
        self.velocity_y += GRAVITY if self.velocity_y < MAX_GRAVITY else 0
        temp_y += self.velocity_y
        _, self.x, self.y, _, _ = collision_resolution(self, self.x, temp_y)


def collision_resolution(entity, temp_x, temp_y):

    # TODO fix spacing. for some reason certain collisions allow for a gap in space etc

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

    temp_x += entity.velocity_x * 2
    if xcollides_solid(entity, temp_x, entity.y):
        temp_x = entity.x
        entity.velocity_x = 0

    if attacker.y < entity.y:
        entity.velocity_y = force / 2
    elif attacker.y > entity.y:
        entity.velocity_y = -force / 2

    temp_y += entity.velocity_y * 2
    if xcollides_solid(entity, entity.x, temp_y):
        temp_y = entity.y
        entity.velocity_y = 0

    _, entity.x, entity.y, entity.velocity_x, entity.velocity_y = \
        collision_resolution(entity, temp_x, temp_y)


def coordinate_checker(func):
    # TODO this is kind of messy/unnecassary. Could probably make it more elegant
    def inner(entity, x=None, y=None, *args): 
        if x == None or y == None:
            x = entity.x
            y = entity.y
        return func(entity, x, y, *args)
    return inner


@coordinate_checker
def xcollides_solid(entity, x, y):
    # collision detection procedure that includes slanted solids
    collisions_raw = entity.collides_solid(x, y)
    collisions = []
    for collision in collisions_raw:
        if collision.group == 'solid' and collision.slanted:
            left = collision.intersection(x)
            right = collision.intersection(x + entity.width)
            
            if y + entity.height > left or \
               y + entity.height > right:
                collisions.append(collision)
        else:
            collisions.append(collision)
    return collisions


@coordinate_checker
def solid_above(entity, x, y):
    return xcollides_solid(entity, x, y - 1)


@coordinate_checker
def solid_below(entity, x, y):
    return xcollides_solid(entity, x, y + 1)


@coordinate_checker
def solid_left(entity, x, y):
    return xcollides_solid(entity, x - 1, y)


@coordinate_checker
def solid_right(entity, x, y):
    return xcollides_solid(entity, x + 1, y)
