import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# For output
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def draw(self, screen, text_string):
        text_bmp = self.font.render(text_string, True, BLACK)
        screen.blit(text_bmp, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10
    
    def unindent(self):
        self.x -= 10


# Initialization
pygame.init()

size = [500, 700]
screen = pygame.display.set_mode(size)

pygame.display.set_caption("test")
pygame.joystick.init()

running = True
clock = pygame.time.Clock()
text_print = TextPrint()

# MAIN PROGRAM LOOP

while running:

    # event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.JOYBUTTONDOWN:
            print("Joystick button pressed.")
        if event.type == pygame.JOYBUTTONUP:
            print("Joystick button released.")

    # start render
    screen.fill(WHITE)
    text_print.reset()

    joystick_count = pygame.joystick.get_count()

    text_print.draw(screen, "Number of joysticks: " + str(joystick_count))
    text_print.indent()

    # for each joystick
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

        text_print.draw(screen, "Joystick " + str(i))
        text_print.indent()

        name = joystick.get_name()
        text_print.draw(screen, "Joystick name: " + str(name))

        axes = joystick.get_numaxes()
        text_print.draw(screen, "Number of axes: " + str(axes))
        text_print.indent()
        for i in range(axes):
            axis = joystick.get_axis(i)
            text_print.draw(screen, "Axis {} value: {:>6.3f}".format(i, axis))
        text_print.unindent()

        buttons = joystick.get_numbuttons()
        text_print.draw(screen, "Number of buttons: " + str(buttons))
        text_print.indent()
        for i in range(buttons):
            button = joystick.get_button(i)
            text_print.draw(screen, "Button {:>2} value: {}".format(i, button))
        text_print.unindent()

        hats = joystick.get_numhats()
        text_print.draw(screen, "Number of hats: " + str(hats))
        text_print.indent()
        for i in range(hats):
            hat = joystick.get_button(i)
            text_print.draw(screen, "Hat {} value: {}".format(i, str(hat)))
        text_print.unindent()

    pygame.display.flip()
    clock.tick(20)

pygame.quit()
