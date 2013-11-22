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

    gl.glViewport(0, 0, width, height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluPerspective(60., width / float(height), .1, 1000.)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED


def gl_setup():
    """Set up OpenGL. This only needs to be run once."""
    # TODO: Clean this out. I think a nice window subclass default to reuse
    #       would be handy.
    # The RGBA screen-clearing color. Defaults to black.
    #gl.glClearColor(0.5, 0.5, 0.5, 1)
    #gl.glColor3f(1, 0, 0)  # This tints EVERYTHING
    gl.glEnable(gl.GL_DEPTH_TEST)
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


###############################################################################
# Loading of 3d models
###############################################################################
TEXTURE_CACHE = {}
MODEL_CACHE = {}


def _load_texture(filename):
    try:
        return TEXTURE_CACHE[filename]
    except KeyError:
        img = pyglet.image.load('resources/textures/{}'.format(filename)).texture
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
def draw_rect(center, w, h, color):
    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_BLEND)
    gl.glColor4f(*color)
    points = ('v3f', (
        center.x + w/2., center.y - h/2., center.z,
        center.x + w/2., center.y + h/2., center.z,
        center.x - w/2., center.y + h/2., center.z,
        center.x - w/2., center.y - h/2., center.z,
    ))
    v = pyglet.graphics.vertex_list(len(points[1]) / 3, points)
    v.draw(gl.GL_QUADS)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_TEXTURE_2D)