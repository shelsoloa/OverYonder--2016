import os
import platform
import pygame
import sys
from pygame.locals import *

ENTITY_ROOM = None


class GC(object):
    
    _window_surface = None
    _render_surface = None
    _scale = -1
    _title = ''

    view_size = (0, 0)
    window_size = (0, 0)
    world = None

    DEBUG = False

    @staticmethod
    def init(view_size, scale=1, title='Game', debug=False):

        os.environ['SDL_VIDEO_CENTERED'] = "1"

        try:
            pygame.display.init()
            pygame.font.init()
            pygame.joystick.init()
            pygame.mixer.init(44100, 16, 2, 512)
        except Exception:
            if pygame.display.get_init() is None or \
               pygame.font.get_init() is None:
                print "Could not initialize pygame core. Aborting."
                return -1
            else:
                print "Could not initialize pygame modules"

        '''
        pygame.mixer.pre_init(44100, 16, 2, 512)
        if platform.system() == 'Linux':
            pygame.display.init()
            pygame.font.init()
            # TODO fix Linux mixer (very low priority)
        else:
            pygame.init()
        '''

        # General initialization
        GC._title = title
        GC._scale = scale

        # Init joysticks
        # TODO Fix joystick functionality
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
            Input.joystick_raw.append(pygame.joystick.Joystick(i))
            Input.joystick_raw[i].init()
            Input.joystick.append({
                'AXIS': [], 
                'BUTTON': [] 
            })

        # Init display
        pygame.display.set_caption(title)

        GC.view_size = view_size
        GC.window_size = (view_size[0] * scale, view_size[1] * scale)
        
        GC._window_surface = pygame.display.set_mode(GC.window_size)
        GC._render_surface = pygame.Surface(GC.view_size)
        
        Graphics._MAIN_CONTEXT = GC._render_surface
        Graphics.set_context(GC._render_surface)

        # Init debug
        if debug:
            GC.DEBUG = True
            print platform.system()

    @staticmethod
    def run():
        game_timer = pygame.time.Clock()
        Input.poll_keyboard()

        running = True

        try:
            while running:

                # Parse events
                for event in pygame.event.get():
                    if event.type == QUIT:
                        running = False

                # Update
                Input.poll_keyboard()
                GC.world.update()

                # Render - Draw World
                GC._render_surface.fill((0, 0, 0))
                GC.world.render()

                # Render - Transformations
                # TODO speed up scaling somehow
                render_size = GC.window_size
                pygame.transform.scale(GC._render_surface, render_size, GC._window_surface)

                # Render - Finalize
                pygame.display.flip()

                # Maintain 45 fps
                game_timer.tick(45)
                if GC.DEBUG:
                    fps = round(game_timer.get_fps())
                    pygame.display.set_caption(GC._title + ' {' + str(fps) + '}')
            
            GC.world.exit()
            pygame.quit()

        except:
            import traceback
            print "[ERROR] Unexpected error. Over Yonder will now shutdown."
            traceback.print_exc()
            sys.exit()

    @staticmethod
    def toggle_fullscreen():
        screen = pygame.display.get_surface()
        caption = pygame.display.get_caption()
        
        flags = screen.get_flags()
        bits = screen.get_bitsize()

        pygame.display.quit()
        pygame.display.init()

        if flags^FULLSCREEN:
            monitor_info = pygame.display.Info()

            ratio = min(float(monitor_info.current_w) / float(GC.view_size[0]),
                        float(monitor_info.current_h) / float(GC.view_size[1]))

            window_width = int(GC.view_size[0] * ratio)
            window_height = int(GC.view_size[1] * ratio)
            
            GC.window_size = (window_width, window_height)
        else:
            GC.window_size = (GC.view_size[0] * GC._scale, GC.view_size[1] * GC._scale)
        pygame.display.set_caption(*caption)

        GC._window_surface = pygame.display.set_mode(GC.window_size, flags^FULLSCREEN, bits)
        GC._render_surface = pygame.Surface(GC.view_size)


        Graphics._MAIN_CONTEXT = GC._render_surface
        Graphics.set_context(GC._render_surface)

    @staticmethod
    def quit():
        pygame.event.post(pygame.event.Event(QUIT))


class AssetManager(object):

    assets_path = ''
    stored_fonts = dict()
    stored_images = dict()
    stored_sounds = dict()

    @staticmethod
    def get_font(asset_name):
        return AssetManager.stored_fonts.get(asset_name)

    @staticmethod
    def get_image(asset_name):
        return AssetManager.stored_images.get(asset_name)

    @staticmethod
    def get_sound(asset_name):
        return AssetManager.stored_sounds.get(asset_name)

    @staticmethod
    def load_font(asset_name, path, point_size):
        """Retrieves a font from the HDD"""

        path = path.lstrip('../')  # cannot rise outside of asset_path

        try:
            font = pygame.font.Font(os.path.join(AssetManager.assets_path, path), point_size)
            AssetManager.stored_fonts[asset_name] = font
            return font
        except IOError:
            # TODO incorporate default font
            print '[ERROR] could not load Font: ' + path

    @staticmethod
    def load_image(asset_name, path):
        """Retrieves an image from the HDD"""

        path = path.lstrip('../')  # cannot rise outside of asset_path

        try:
            image = pygame.image.load(os.path.join(AssetManager.assets_path, path))
            image.convert_alpha()
            AssetManager.stored_images[asset_name] = image
            return image
        except IOError:
            print '[ERROR] could not find Image: ' + path
            GC.quit()

    @staticmethod
    def load_sound(asset_name, path):
        """Retrieves a sound file from the HDD"""
        # TODO add linux support

        path = path.lstrip('../')  # cannot rise outside of asset_path

        try:
            sound = pygame.mixer.Sound(os.path.join(AssetManager.assets_path, path))
            AssetManager.stored_sounds[asset_name] = sound
            return sound
        except IOError:
            print '[ERROR] could not find Sound: ' + path
            sound = pygame.mixer.Sound()
            AssetManager.stored_sounds[asset_name] = sound
            return sound


class Entity(object):

    def __init__(self, x, y):
        self.group = ''           # Every entity belongs to a group
        self.name = ''            # Unique entities have a name (1/room)

        self.event_handle = None  # Used by events to access this entity, set on map load

        self.x = x                # x coordinate
        self.y = y                # y coordinate
        self.width = 0            # width (collision detection)
        self.height = 0           # height (collision detection)

        self.velocity_x = 0       # x-axis velocity
        self.velocity_y =  0      # y-axis velocity
        
        self.active = True        # If the entity is being updated
        self.visible = True       # If the entity is being rendered
        self.solid = False        # If the entity registers as a solid object (collision detection)

        self.sprite = None        # sprite used for rendering

    def destroy(self):
        global ENTITY_ROOM
        self.active = False
        ENTITY_ROOM.remove(self)

    # TODO change to validate_coordinates(self, x, y)
    def _check_bounds(self, x, y):
        if x is None or y is None:
            return (self.x, self.y)
        else:
            return (x, y)

    def collides(self, e, x=None, y=None):  
        x, y = self._check_bounds(x, y)

        if e is None or e == self:
            return False

        left_a = x
        right_a = x + self.width
        top_a = y
        bottom_a = y + self.height

        left_b = e.x
        right_b = e.x + e.width
        top_b = e.y
        bottom_b = e.y + e.height
        
        if (bottom_a <= top_b or top_a >= bottom_b or
                right_a <= left_b or left_a >= right_b):
            return False
        else:
            return True

    def collides_group(self, group, x=None, y=None):
        x, y = self._check_bounds(x, y)

        global ENTITY_ROOM

        collisions = []
        for entity in ENTITY_ROOM.entities:
            if entity == self or not entity.active:
                continue
            elif entity.group == group and self.collides(entity, x, y):
                collisions.append(entity)
        return collisions
    
    def collides_groups(self, x=None, y=None, *groups):
        # TODO convert to *args
        x, y = self._check_bounds(x, y)

        global ENTITY_ROOM

        collisions = []
        for entity in ENTITY_ROOM.entities:
            if entity == self or not entity.active:
                continue
            elif entity.group in groups and self.collides(entity, x, y):
                collisions.append(entity)
        return collisions
    
    def collides_name(self, name, x=None, y=None):
        x, y = self._check_bounds(x, y)

        global ENTITY_ROOM

        for entity in ENTITY_ROOM.entities:
            if entity.name == name and self.collides(entity, x, y):
                return entity
        return None

    def collides_point(self, point, x=None, y=None):
        x, y = self._check_bounds(x, y)

        px, py = point
        if x <= px <= x + self.width and y <= py <= y + self.height:
            return True
        else:
            return False

    def collides_rect(self, rect, x=None, y=None):
        x, y = self._check_bounds(x, y)

        rx, ry, rwidth, rheight = rect

        left_a = x
        right_a = x + self.width
        top_a = y
        bottom_a = y + self.height

        left_b = rx
        right_b = rx + rwidth
        top_b = ry
        bottom_b = ry + rheight
        
        if (bottom_a <= top_b or top_a >= bottom_b or
                right_a <= left_b or left_a >= right_b):
            return False
        else:
            return True

    def collides_solid(self, x=None, y=None):
        x, y = self._check_bounds(x, y)

        global ENTITY_ROOM
        
        collisions = []
        for entity in ENTITY_ROOM.entities:
            if entity == self or not entity.active:
                continue
            elif entity.solid and self.collides(entity, x, y):
                collisions.append(entity)
        return collisions
    
    def distance_from(self, entity):
        return abs((self.x - entity.x) + (self.y - entity.y))

    def render(self):
        return
            
    def update(self):
        return


class Graphics(object):

    _MAIN_CONTEXT = None  # A constant that holds the main render context

    context = None
    context_rect = None

    color = pygame.Color(0, 0, 0)
    font = None

    FLIP_X = 0x01
    FLIP_Y = 0x02

    translate_x = 0
    translate_y = 0
   
    @staticmethod
    def draw_image(image, x, y, args=0):
        x -= Graphics.translate_x
        y -= Graphics.translate_y
        
        bounds = image.get_rect().move(x, y)

        if bounds.colliderect(Graphics.context_rect):
            if args & Graphics.FLIP_X:
                image = pygame.transform.flip(image, True, False)
            if args & Graphics.FLIP_Y:
                image = pygame.transform.flip(image, False, True)

            Graphics.context.blit(image, (x, y))
    
    @staticmethod
    def draw_line(x1, y1, x2, y2):
        x1 -= Graphics.translate_x
        y1 -= Graphics.translate_y
        x2 -= Graphics.translate_x
        y2 -= Graphics.translate_y

        pygame.draw.line(Graphics.context, Graphics.color, (x1, y1), (x2, y2))

    @staticmethod
    def draw_circle(x, y, diameter):
        radius = diameter / 2

        x = int(x - Graphics.translate_x + radius)
        y = int(y - Graphics.translate_y + radius)

        pygame.draw.circle(Graphics.context, Graphics.color, (x, y), radius)


    @staticmethod
    def draw_rect(x, y, width, height):
        x -= Graphics.translate_x
        y -= Graphics.translate_y
        
        pygame.draw.rect(Graphics.context, Graphics.color, (x, y, width, height))

    @staticmethod   
    def draw_text(text, x, y, aa=False, center=False):
        text_surface = Graphics.font.render(text, aa, Graphics.color)
        text_rect = text_surface.get_rect()
        text_rect.x = x - Graphics.translate_x
        text_rect.y = y - Graphics.translate_y

        if center:
            text_rect.centerx = Graphics.context.get_rect().centerx

        Graphics.context.blit(text_surface, text_rect)

    @staticmethod
    def rotate(image, degree):
        return pygame.transform.rotate(image, degree)

    @staticmethod
    def set_color(r, g, b, a=255):
        if (0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255) and (0 <= a <= 255):
            # TODO fix alpha
            Graphics.color = pygame.Color(r, g, b, a)

    @staticmethod
    def set_context(context):
        Graphics.context = context
        Graphics.context_rect = context.get_rect()

    @staticmethod
    def translate(x, y):
        Graphics.translate_x = x
        Graphics.translate_y = y

    @staticmethod
    def translate_center(x, y):
        half_vw, half_vh = [v / 2 for v in GC.view_size]
        Graphics.translate_x = x - half_vw
        Graphics.translate_y = y - half_vh
    
    @staticmethod
    def debug_draw_grid(cell_width, cell_height, offset_x=0, offset_y=0):
        view_width, view_height = GC.view_size
        
        x = offset_x
        y = offset_y

        while x < view_width:
            Graphics.draw_line(x, offset_y, x, view_height)
            x += cell_width

        while y < view_height:
            Graphics.draw_line(offset_x, y, view_width, y)
            y += cell_height


class Input(object):

    curr_key_state = []
    prev_key_state = []

    joystick = []
    joystick_raw = []
    
    @staticmethod
    def down(key):
        code = Input.get_key_code(key)
        if code != -1:
            return Input.curr_key_state[code]
        return False

    @staticmethod
    def pressed(key):
        if key == 'ANY':
            for code in range(len(Input.curr_key_state)):
                if Input.curr_key_state[code] and not Input.prev_key_state[code]:
                    return True
            return False
        elif key[:3] == 'JOY':
            return False
            # TODO add functionality for custom axes

            if len(Input.joystick) > 0:
                joystick = Input.joystick[0]

            code = key[4:]
            if code == 'UP':
                return False
            elif code == 'DOWN':
                return False
            elif code == 'LEFT':
                return False
            elif code == 'RIGHT':
                return False
            elif key[4:10] == 'BUTTON':
                result = False
                try:
                    code = int(key[10:])
                    result = joystick['BUTTON'][code] == 0
                except ValueError:
                    if GC.DEBUG:
                        print 'Cannot recognize JOY_BUTTON: {}'.format(key[10:])
                except IndexError:
                    if GC.DEBUG:
                        print 'Invalid JOY_BUTTON index: {}'.format(code)
                return result

        else:
            code = Input.get_key_code(key)
            if code != -1:
                return Input.curr_key_state[code] and not Input.prev_key_state[code]
            return False
    
    @staticmethod
    def released(key):
        code = Input.get_key_code(key)
        if code != -1:
            return not Input.curr_key_state[code] and Input.prev_key_state[code]
        return False

    @staticmethod
    def poll_joysticks():
        # TODO Must supress all output due to an annoying bug in pygame where 
        # SDL will print SDL_GET_BUTTON_XXX, everytime this method is called.
        return

        old_out = sys.stdout
        old_err = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

        for joy_i in range(len(Input.joystick_raw)):

            joy_raw = Input.joystick_raw[joy_i]
            joystick = Input.joystick[joy_i]

            axes = []
            axis_count = joy_raw.get_numaxes()
            for axis_i in range(axis_count):
                axis = joy_raw.get_axis(axis_i)
                axes.append(axis)
            joystick['AXIS'] = axes

            buttons = []
            button_count = joy_raw.get_numbuttons()
            for button_i in range(button_count):
                button = joy_raw.get_button(button_i)
                buttons.append(button)
            joystick['BUTTON'] = button

        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_out
        sys.stderr = old_err
    
    @staticmethod
    def poll_keyboard():
        Input.prev_key_state = Input.curr_key_state
        Input.curr_key_state = pygame.key.get_pressed()

        if len(Input.joystick_raw) > 0:
            Input.poll_joysticks()
    
    @staticmethod
    def get_key_code(key):
        if key == 'enter':
            return K_RETURN
        elif key == 'escape':
            return K_ESCAPE
        elif key == 'lshift':
            return K_LSHIFT
        elif key == 'space':
            return K_SPACE
        elif key == 'left':
            return K_LEFT
        elif key == 'right':
            return K_RIGHT
        elif key == 'up':
            return K_UP
        elif key == 'down':
            return K_DOWN

        elif key == '1':
            return K_1;
        elif key == '2':
            return K_2;
        elif key == '3':
            return K_3;
        elif key == '4':
            return K_4;
        elif key == '5':
            return K_5;
        elif key == '6':
            return K_6;
        elif key == '7':
            return K_7;
        elif key == '8':
            return K_8;
        elif key == '9':
            return K_9;
        elif key == '0':
            return K_0;

        elif key == 'F1':
            return K_F1;
        elif key == 'F2':
            return K_F2;
        elif key == 'F3':
            return K_F3;
        elif key == 'F4':
            return K_F4;
        elif key == 'F5':
            return K_F5;
        elif key == 'F6':
            return K_F6;
        elif key == 'F7':
            return K_F7;
        elif key == 'F8':
            return K_F8;
        elif key == 'F9':
            return K_F9;
        elif key == 'F10':
            return K_F10;
        elif key == 'F11':
            return K_F11;
        elif key == 'F12':
            return K_F12;

        elif key == 'a':
            return K_a
        elif key == 'b':
            return K_b
        elif key == 'c':
            return K_c
        elif key == 'd':
            return K_d
        elif key == 'e':
            return K_e
        elif key == 'f':
            return K_f
        elif key == 'g':
            return K_g
        elif key == 'h':
            return K_h
        elif key == 'i':
            return K_i
        elif key == 'j':
            return K_j
        elif key == 'k':
            return K_k
        elif key == 'l':
            return K_l
        elif key == 'm':
            return K_m
        elif key == 'n':
            return K_n
        elif key == 'o':
            return K_o
        elif key == 'p':
            return K_p
        elif key == 'q':
            return K_q
        elif key == 'r':
            return K_r
        elif key == 's':
            return K_s
        elif key == 't':
            return K_t
        elif key == 'u':
            return K_u
        elif key == 'v':
            return K_v
        elif key == 'w':
            return K_w
        elif key == 'x':
            return K_x
        elif key == 'y':
            return K_y
        elif key == 'z':
            return K_z
        else:
            return -1


class State(object):
    def __init__(self, world, name):
        self.world = world
        self.name = name

    def enter(self, previous_state, *args):
        return

    def exit(self, next_state, *args):
        return

    def render(self):
        return

    def update(self):
        return


class World(object):

    def __init__(self):
        self.states = {}
        self.current_state = None

    def change_state(self, state_name, *args):
        if state_name in self.states and \
           state_name != self.current_state.name:
            previous_state = self.current_state
            incoming_state = self.states[state_name]

            previous_state.exit(incoming_state, *args)
            incoming_state.enter(previous_state, *args)
            
            self.current_state = incoming_state
        else:
            print state_name in self.states
            print '[ERROR] change_state request invalid'

    def exit(self):
        ENTITY_ROOM.clear()
        if self.current_state is not None:
            self.current_state.exit(None)

    def update(self):
        return

    def render(self):
        return


class EntityRoom(object):

    def __init__(self):
        self.entities = []

    def add(self, entity):
        self.entities.append(entity)
        return entity

    def clear(self):
        del self.entities[:]

    def get_group(self, group_name):
        ents = []
        for e in self.entities:
            if e.group == group_name:
                ents.append(e)
        return ents

    def get_name(self, name):
        for e in self.entities:
            if e.name == name:
                return e

    def remove(self, entity):
        try:
            if entity in self.entities:
                self.entities.remove(entity)
        except ValueError:
            pass  # Do nothing

    def remove_group(self, group_name):
        for entity in self.entities:
            if entity.group == group_name:
                self.entities.remove(entity)

    def remove_name(self, entity_name):
        for entity in self.entities:
            if entity.name == entity_name:
                self.entities.remove(entity)
                break

    def render(self):
        return

    def update(self):
        return
