import pickle
import pyglet
from pyglet import gl
from game.utils import Vector3

config = gl.Config(
    sample_buffers=1,    # For antialiasing
    samples=4,           # number of antialiasing samples
    depth_size=16,       # ???
    double_buffer=True,  # Render and swap
)
WINDOW = pyglet.window.Window(resizable=True, config=config)
SIZE = [0, 0]

###############################################################################
# Pyglet Window subclass
###############################################################################
# TODO: Subclass Window!


###############################################################################
# Configuration and setup
###############################################################################
def configure_gl_viewport(width, height):
    """Set the viewport up to use OpenGL. This must be called every time there
    is a change in window size.
    """
    SIZE[0], SIZE[1] = width, height
    #gl.glViewport(0, 0, width, height)
    #gl.glMatrixMode(gl.GL_PROJECTION)
    #gl.glLoadIdentity()
    #gl.gluPerspective(60., width / float(height), .1, 1000.)
    #gl.glMatrixMode(gl.GL_MODELVIEW)
    enable_3d()
    return pyglet.event.EVENT_HANDLED


def gl_setup():
    """Set up OpenGL. This only needs to be run once."""
    # TODO: Clean this out. A nice window subclass would be handy.
    # The RGBA screen-clearing color. Defaults to black.
    #gl.glClearColor(0.5, 0.5, 0.5, 1)
    #gl.glColor3f(1, 0, 0)  # This tints EVERYTHING
    #gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_CULL_FACE)

    # Wireframe draw mode
    #gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

    # Simple light setup
    gl.glEnable(gl.GL_LIGHTING)

    # Define a simple function to create ctypes arrays of floats:
    def vec(*args):
        return (gl.GLfloat * len(args))(*args)

    gl.glEnable(gl.GL_LIGHT0)   # add one light
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, vec(0, 0, 1, 1))
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, vec(1, 0.5, 0, 1))
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, vec(0, 1, 0, 1))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, vec(0, 5, 10, 1))

    #gl.glLightf(gl.GL_LIGHT0, gl.GL_CONSTANT_ATTENUATION, 1.0) # default is 1.0
    #gl.glLightf(gl.GL_LIGHT0, gl.GL_LINEAR_ATTENUATION, 0.1)
    #gl.glLightf(gl.GL_LIGHT0, gl.GL_QUADRATIC_ATTENUATION, 0.1)

    #gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
    #                vec(1.0, 1.0, 1.0, 1))
    #gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR,
    #                vec(1.0, 1.0, 1.0, 1))
    #gl.glMaterialf(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 90)

    gl.glEnable(gl.GL_TEXTURE_2D)


def enable_3d():
    gl.glViewport(0, 0, *SIZE)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluPerspective(60., SIZE[0] / float(SIZE[1]), .1, 1000.)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()  # TODO: is this needed?
    gl.glDepthFunc(gl.GL_LEQUAL)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_CULL_FACE)


def enable_2d():
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluOrtho2D(0.0, SIZE[0], 0.0, SIZE[1])
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gl.glTranslatef(0.375, 0.375, 0.0)  # TODO: What?
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glDisable(gl.GL_CULL_FACE)


###############################################################################
# Loading of 3d models
###############################################################################
TEXTURE_CACHE = {}
MODEL_CACHE = {}


def _load_texture(filename):
    try:
        return TEXTURE_CACHE[filename]
    except KeyError:
        img = pyglet.image.load(
            'resources/textures/{}'.format(filename)).texture
        TEXTURE_CACHE[filename] = img.texture
        return TEXTURE_CACHE[filename]


def _vlist_from_data(points):
    return pyglet.graphics.vertex_list(len(points[0][1]) / 3, *points)


def _load_model(filename):
    try:
        return MODEL_CACHE[filename]
    except KeyError:
        with open('resources/models/{}.pvl'.format(filename), 'rb') as infile:
            data = pickle.loads(infile.read())
        lists = {_load_texture(texture): _vlist_from_data(points)
                 for texture, points in data.items()}
        MODEL_CACHE[filename] = lists
        return MODEL_CACHE[filename]


class Model(object):
    position = None
    vertex_lists = None
    angle = 0
    pick_color = None  # for picking

    def __init__(self, data_path, position=None):
        if position is None:
            position = Vector3(0, 0, 0)
        self.vertex_lists = _load_model(data_path)  # models embed textures
        self.position = position

    def draw(self, scale=1):
        gl.glPushMatrix()
        gl.glTranslatef(*self.position)
        gl.glRotatef(self.angle, 0, 0, 1)
        gl.glScalef(scale, scale, scale)
        for texture, vlist in self.vertex_lists.items():
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture.id)
            vlist.draw(gl.GL_TRIANGLES)
        gl.glPopMatrix()

    def draw_for_picker(self, color, scale=1):
        # disable stuff
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_LIGHTING)
        gl.glColor3f(*color)
        gl.glPushMatrix()
        gl.glTranslatef(*self.position)
        gl.glRotatef(self.angle, 0, 0, 1)
        gl.glScalef(scale, scale, scale)
        for texture, vlist in self.vertex_lists.items():
            vlist.draw(gl.GL_TRIANGLES)
        gl.glPopMatrix()
        # re-enable stuff
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_TEXTURE_2D)


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


###############################################################################
# Button utils
# Based on http://www.pyglet.org/doc/programming_guide/media_player.py
# But seriously enhanced and fixed.
###############################################################################
def draw_rect(x, y, width, height):
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(x, y)
    gl.glVertex2f(x + width, y)
    gl.glVertex2f(x + width, y + height)
    gl.glVertex2f(x, y + height)
    gl.glEnd()


class Control(pyglet.event.EventDispatcher):
    x = y = 0
    width = height = 10

    def __init__(self, parent, x, y, w, h):
        super(Control, self).__init__()
        self.x, self.y, self.w, self.h = x, y, w, h
        self.parent = parent

    def hit_test(self, x, y):
        return (self.x < x < self.x + self.w and
                self.y < y < self.y + self.h)

    def capture_events(self):
        self.parent.push_handlers(self)

    def release_events(self):
        self.parent.remove_handlers(self)


class Button(Control):
    charged = False

    def draw(self):
        gl.glColor3f(0, 1, 1)
        if self.charged:
            gl.glColor3f(1, 0, 0)
        draw_rect(self.x, self.y, self.w, self.h)
        gl.glColor3f(0, 1, 1)
        self.draw_label()

    def on_mouse_press(self, x, y, button, modifiers):
        self.capture_events()
        self.charged = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.charged = self.hit_test(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        if self.hit_test(x, y):
            self.dispatch_event('on_press')
        self.charged = False
Button.register_event_type('on_press')


class TextButton(Button):
    def __init__(self, parent, text, x, y, w, h):
        super(TextButton, self).__init__(parent, x, y, w, h)
        self._label = pyglet.text.Label(text, anchor_x='center', anchor_y='center')

    def draw_label(self):
        self._label.x = self.x + self.w / 2
        self._label.y = self.y + self.h / 2
        self._label.draw()

    @property
    def text(self):
        return self._label.text
    @text.setter
    def text(self, text):
        self._label.text = text
