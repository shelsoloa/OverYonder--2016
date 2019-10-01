import peachy
from peachy import PC

from game.config import KEY, SAVE_FILE


class MainMenuWorld(peachy.World):
    def __init__(self):
        super().__init__('MAIN')
        self.options = ['NEW', 'CONTINUE', 'EXIT']
        self.current_selection = 0

    def select(self, option):
        if option == 'NEW':
            PC.engine.change_world('GAME')
            PC.engine.world.new_game()
        elif option == 'CONTINUE':
            PC.engine.change_world('GAME')

            try:
                PC.engine.world.load_game(SAVE_FILE)
            except IOError:
                print('save file does not exist.')
            else:
                PC.engine.world.new_game()
        elif option == 'DEBUG':
            PC.engine.change_world('GAME')
            PC.engine.world.start_debug()
        elif option == 'EXIT':
            PC.quit()

    def render(self):
        peachy.graphics.set_color(255, 255, 255)
        peachy.graphics.draw_text('OVER YONDER', 8, 8)

        for i in range(len(self.options)):
            if i == self.current_selection:
                peachy.graphics.set_color(0, 255, 0)
            else:
                peachy.graphics.set_color(255, 255, 255)
            option = self.options[i]
            y = 8 * (i + 4)
            peachy.graphics.draw_text(option, 12, y)

    def update(self):
        if peachy.utils.Key.pressed(KEY['UP']):
            self.current_selection -= 1
            if self.current_selection < 0:
                self.current_selection = len(self.options) - 1
        if peachy.utils.Key.pressed(KEY['DOWN']):
            self.current_selection += 1
            if self.current_selection >= len(self.options):
                self.current_selection = 0
        if peachy.utils.Key.pressed(KEY['SELECT']):
            self.select(self.options[self.current_selection])
