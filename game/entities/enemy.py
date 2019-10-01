import peachy
from .utility import INVINCIBILITY_DURATION, knockback


class Enemy(peachy.Entity):

    STATE_AGGRO = 'aggro'
    STATE_IDLE = 'idle'
    STATE_STUNNED = 'stun'

    def __init__(self, x, y):
        super().__init__(x, y)
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
        Enemy.take_damage(self, attacker, damage)
        if self.active and not self.invincible:
            knockback(self, attacker, force)
            self.invincible = True
            self.invincibility_timer = INVINCIBILITY_DURATION
