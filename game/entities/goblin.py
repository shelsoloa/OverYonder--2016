import peachy

from .enemy import Enemy
from .utility import MAX_GRAVITY, GRAVITY, collision_resolution, solid_below


class GoblinImp(Enemy):

    JUMP_COOLDOWN = 90
    AIR_SPEED = 2.75
    MOVE_SPEED = 0.5
    JUMP_SPEED = 2.25

    AGGRO_DISTANCE_X = 64
    AGGRO_DISTANCE_Y = 16

    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 5

        self.width = 8
        self.height = 8

        self.state = Enemy.STATE_IDLE

        self.jumping = False
        self.jump_direction = 0
        self.jump_timer = 0

    def render(self):
        peachy.graphics.set_color(197, 182, 128)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        has_solid_below = solid_below(self, temp_x, temp_y)
        player = self.container.get_name('player')

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == Enemy.STATE_AGGRO:
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

        elif self.state == Enemy.STATE_IDLE:
            # TODO add wandering movement to simulate natural life etc etc
            player_distance_x = abs(self.x - player.x)
            player_distance_y = abs(self.y - player.y)

            if player_distance_x < GoblinImp.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinImp.AGGRO_DISTANCE_Y:
                self.state = Enemy.STATE_AGGRO

        if self.velocity_x != 0:
            self.velocity_x += 0.25 if self.velocity_x < 0 else -0.25

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

        if self.collides(player, self.x, self.y):
            player.take_damage(self, 1)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1.5)
        self.state = Enemy.STATE_AGGRO


class GoblinSpearman(Enemy):
    # TODO complete this class if design makes sense

    SAFE_DISTANCE = -1
    STATE_PRE_ATTACK = 'prep'
    AGGRO_DISTANCE_X = 128
    AGGRO_DISTANCE_Y = 32

    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = 16
        self.height = 16

        self.state = GoblinSpearman.STATE_IDLE
        self.state_timer = 0

    def render(self):
        if self.state == GoblinSpearman.STATE_PRE_ATTACK:
            peachy.graphics.set_color(255, 0, 0)
        else:
            peachy.graphics.set_color(197, 182, 128)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def update(self):
        temp_x = self.x
        temp_y = self.y
        player = self.container.get_name('player')

        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        if self.state == GoblinSwordsman.STATE_IDLE:
            player_distance_x = abs(temp_x - player.x)
            player_distance_y = abs(temp_y - player.y)

            if player_distance_x < GoblinSwordsman.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinSwordsman.AGGRO_DISTANCE_Y:
                self.state = Enemy.STATE_AGGRO
        elif self.state == Enemy.STATE_AGGRO:
            player_distance_x = abs(temp_x - player.x)
            if player_distance_x < GoblinSpearman.SAFE_DISTANCE:
                # Move towards player
                return
            elif player_distance_x > GoblinSpearman.SAFE_DISTANCE:
                # Move away from player
                return


class GoblinSwordsman(Enemy):

    MOVE_SPEED = 1
    ACCEL_SPEED = 0.2

    AGGRO_DISTANCE_X = 124
    AGGRO_DISTANCE_Y = 64

    STATE_PRE_ATTACK = 'pre-attack'
    STATE_ATTACKING = 'attacking'

    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = 16
        self.height = 16

        self.health = 5

        self.state = Enemy.STATE_IDLE
        self.state_timer = 0

    def render(self):
        if self.state == GoblinSwordsman.STATE_PRE_ATTACK:
            peachy.graphics.set_color(255, 0, 0)
        else:
            peachy.graphics.set_color(197, 182, 128)
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
            player_distance_y = abs(temp_y - player.y)

            if player_distance_x < GoblinSwordsman.AGGRO_DISTANCE_X and \
               player_distance_y < GoblinSwordsman.AGGRO_DISTANCE_Y:
                self.state = Enemy.STATE_AGGRO

        elif self.state == GoblinSwordsman.STATE_PRE_ATTACK:
            self.state_timer -= 1
            if self.state_timer < 0:
                ax = self.x + 16 * self.facing_x
                self.container.add(GoblinSwordsman.Attack(self, ax, self.y))
                self.state = GoblinSwordsman.STATE_ATTACKING
                self.state_timer = GoblinSwordsman.Attack.DURATION

        elif self.state == GoblinSwordsman.STATE_ATTACKING:
            self.state_timer -= 1
            if self.state_timer < 0:
                self.state = Enemy.STATE_AGGRO

        elif self.state == Enemy.STATE_AGGRO:
            if self.velocity_x < GoblinSwordsman.MOVE_SPEED and \
               temp_x < player.x:
                self.facing_x = 1
                self.velocity_x += GoblinSwordsman.ACCEL_SPEED
            elif self.velocity_x > -GoblinSwordsman.MOVE_SPEED and \
                 temp_x > player.x:
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

        elif self.state == Enemy.STATE_STUNNED:
            if self.velocity_x > 0:
                self.velocity_x -= GoblinSwordsman.ACCEL_SPEED
            elif self.velocity_x < 0:
                self.velocity_x += GoblinSwordsman.ACCEL_SPEED
            self.state_timer -= 1
            if self.state_timer < 0:
                self.state = Enemy.STATE_AGGRO

        if self.velocity_y < MAX_GRAVITY:
            self.velocity_y += GRAVITY

        temp_x += self.velocity_x
        temp_y += self.velocity_y

        _, self.x, self.y, self.velocity_x, self.velocity_y = \
            collision_resolution(self, temp_x, temp_y)

    def take_damage(self, attacker, damage):
        self._take_damage_and_knockback(attacker, damage, 1)
        self.state = Enemy.STATE_AGGRO  # Enemy.STATE_STUNNED
        # self.state_timer = INVINCIBILITY_DURATION / 4

    class Attack(peachy.Entity):

        DAMAGE = 3
        DURATION = 30

        def __init__(self, parent, x, y):
            super().__init__(x, y)
            self.parent = parent
            self.width = 16
            self.height = 16
            self.lifespan = GoblinSwordsman.Attack.DURATION

        def render(self):
            peachy.graphics.set_color(255, 0, 0)
            peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

        def update(self):
            if self.lifespan > 0:
                self.lifespan -= 1
                player = self.container.get_name('player')
                if self.collides(player, self.x, self.y):
                    player.take_damage(self, GoblinSwordsman.Attack.DAMAGE)
            else:
                self.destroy()
