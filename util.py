import peachy


class GUI(object):
    # TODO move to new module

    HEALTH_POINT = None
    HEALTH_EMPTY = None

    @staticmethod
    def init():
        GUI.HEALTH_POINT = peachy.fs.get_image('HUD_HEALTH_FULL')
        GUI.HEALTH_EMPTY = peachy.fs.get_image('HUD_HEALTH_EMPTY')

    @staticmethod
    def draw_HUD():
        player = peachy.world.stage.player
        for i in range(player.max_health):
            if i >= player.health:
                img = GUI.HEALTH_EMPTY
            else:
                img = GUI.HEALTH_POINT
            peachy.graphics.draw(img, 8 + 4 * i, 12)
