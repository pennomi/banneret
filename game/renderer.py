from __future__ import print_function
from weakref import proxy, WeakValueDictionary
import pyglet
import sys
from pyglet import gl
from euclid import Vector3
from game import interface


###############################################################################
# Pyglet Window subclass
###############################################################################
class GameWindow3d(pyglet.window.Window):
    class Mouse(object):
        x, y = 0, 0

    class Camera(object):
        up = Vector3(0, 0, 1)
        looking_at = Vector3(0, 0, 0)
        position = Vector3(1, 0, 0)

        def look(self):
            gl.glLoadIdentity()
            data = list(self.position) + list(self.looking_at) + list(self.up)
            gl.gluLookAt(*data)

    def __init__(self, StartingGameStateClass, *args, **kwargs):
        # update kwargs
        kwargs['config'] = gl.Config(
            sample_buffers=1,    # For antialiasing
            samples=4,           # number of antialiasing samples
            depth_size=16,       # ???
            double_buffer=True,  # Render and swap
        )
        kwargs['resizable'] = True
        super(GameWindow3d, self).__init__(*args, **kwargs)

        # init mouse and camera
        self.mouse = self.Mouse()
        self.camera = self.Camera()

        # init fps counter
        # TODO: make this a label instead.
        if 'fps' in sys.argv:
            pyglet.clock.schedule_interval(
                lambda dt: print(pyglet.clock.get_fps()), 1)

        # set the starting game state
        self.gamestate = StartingGameStateClass(self)

    def set_state(self, NewStateClass, *args, **kwargs):
        # TODO: this will handle the animation triggers, callbacks, etc.
        for w in self.gamestate.controls.values():
            w.cleanup()
        self.gamestate = NewStateClass(self, *args, **kwargs)

    def on_draw(self):
        self.clear()
        self.enable_3d()
        self.gamestate.draw_3d()
        self.enable_2d()
        self.gamestate.draw_2d()
        gl.glFinish()

    def on_mouse_press(self, x, y, button, modifiers):
        self.gamestate.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.gamestate.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse.x, self.mouse.y = x, y

    def enable_3d(self):
        gl.glViewport(0, 0, self.width, self.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluPerspective(60., self.width / float(self.height), .1, 1000.)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        # update the camera
        self.camera.look()
        # TODO: probably find a better place to enable and configure these
        # TODO TODO: Just use shader-based lighting anyway.
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION,
                     (gl.GLfloat * 4)(0, 0, 100, 1))

    def enable_2d(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(0.0, self.width, 0.0, self.height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_LIGHTING)


CHARACTER_WHITELIST = set("0123456789 -+/*")


class BaseGameState(object):
    """Common, game-independent functionality for GameStates."""
    def __init__(self, window):
        self.window = proxy(window)
        self.controls = WeakValueDictionary()
        self.camera_look_at = Vector3(0, 0, 0)

    def load_interface(self, filename):
        # TODO: refactor this to be not... stupid. Probably should invoke
        # parser helper functions contained in interface.py
        filename = 'skins/interfaces/default/{}'.format(filename)
        with open(filename, 'r') as infile:
            data = infile.readlines()
        current_control = None
        for line in [_ for _ in data if _.strip() and not _.startswith('#')]:
            if line.startswith('    ') or line.startswith('\t'):
                key, value = line.split(':')
                key, value = key.strip(), value.strip()
                if key in ['x', 'y', 'w', 'h']:
                    value = value.replace('window.midleft.y', str(
                        self.window.height / 2))
                    if len(set(value) - CHARACTER_WHITELIST):
                        raise AttributeError(
                            "Invalid characters specified in calculation for {}"
                            "".format(key))
                    setattr(current_control, key, eval(value))
                elif key in ['text', 'texture']:
                    setattr(current_control, key, value)
                elif key == 'id':
                    self.controls[value] = current_control
                else:
                    raise AttributeError(
                        "Invalid key `{}` specified for interface element."
                        "".format(key))
            else:
                ControlClass = getattr(interface, line.strip())
                current_control = ControlClass(self.window)

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def draw_3d(self):
        pass

    def draw_2d(self):
        for w in self.controls.values():
            w.draw()

    def __del__(self):
        print("__del__ Deleted old game state")


###############################################################################
# Convenience Functions
###############################################################################
def color_at_point(x, y):
    a = (gl.GLubyte * 3)(0)
    gl.glReadPixels(x, y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, a)
    return list(a)


###############################################################################
# Simple primitives for easy use
###############################################################################
def draw_highlight(xy, color):
    center = Vector3(xy[0], xy[1], 0.01)
    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_BLEND)
    gl.glColor4f(*color)
    points = ('v3f', (
        center.x + .5, center.y - .5, center.z,
        center.x + .5, center.y + .5, center.z,
        center.x - .5, center.y + .5, center.z,
        center.x - .5, center.y - .5, center.z,
    ))
    v = pyglet.graphics.vertex_list(len(points[1]) / 3, points)
    v.draw(gl.GL_QUADS)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_TEXTURE_2D)
