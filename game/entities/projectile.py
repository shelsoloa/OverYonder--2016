import peachy


class Projectile(peachy.Entity):

    def __init__(self, parent, x, y, dx, dy, speed, lifespan=-1):
        super().__init__(x, y)
        self.group = 'projectile'

        self.parent = parent
        self.velocity_x = speed * dx
        self.velocity_y = speed * dy
        self.lifespan = lifespan

    def move(self):
        self.x += self.velocity_x
        self.y += self.velocity_y

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
