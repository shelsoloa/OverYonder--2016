from abc import ABCMeta, abstractmethod

import peachy
from peachy import PC

from .player import Player
import random


def drop(x, y, drop_rate=25, missile_rate=20):
    # 25% chance to drop
    success = random.randint(0, 99) < drop_rate
    if success:
        drop = None
        player = PC.world.entities.get_name('player')
        if Player.Item.ID_MISSILE in player.items:
            success = random.randint(0, 99) < missile_rate
            if success:
                drop = AmmoDrop(x, y)
            else:
                drop = HealthDrop(x, y)
        else:
            drop = HealthDrop(x, y)
        PC.world.entities.add(drop)


class AbsDrop(peachy.Entity):
    __metaclass__ = ABCMeta

    DURATION = 225  # 5 seconds

    def __init__(self, x, y):
        super().__init__(x, y)
        self.group = 'drop'
        self.width = 4
        self.height = 4
        self.lifespan = AbsDrop.DURATION

    @abstractmethod
    def perform_action(self, player):
        return

    def update(self):
        player = self.container.get_name('player')
        if self.collides(player, self.x, self.y):
            self.perform_action(player)

        self.lifespan -= 1
        if self.lifespan <= 0:
            self.destroy()


class AmmoDrop(AbsDrop):
    def __init__(self, x, y):
        AbsDrop.__init__(self, x, y)

    def render(self):
        peachy.graphics.set_color(200, 200, 200)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def perform_action(self, player):
        # TODO add missile ammo
        # if player.missiles < Player.MAX_AMMO:
        #     player.missiles += 1
        self.destroy()


class HealthDrop(AbsDrop):
    def __init__(self, x, y):
        AbsDrop.__init__(self, x, y)

    def render(self):
        peachy.graphics.set_color(0, 255, 0)
        peachy.graphics.draw_rect(self.x, self.y, self.width, self.height)

    def perform_action(self, player):
        if player.health < player.max_health:
            player.health += 1
        self.destroy()
