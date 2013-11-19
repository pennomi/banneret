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

    #gl.glColor3f(1, 0, 0)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnable(gl.GL_CULL_FACE)

    # Wireframe draw mode
    #gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

    ## Simple light setup
    #gl.glEnable(gl.GL_LIGHTING) # enable lighting

    # Define a simple function to create ctypes arrays of floats:
    def vec(*args):
        return (gl.GLfloat * len(args))(*args)

    gl.glEnable(gl.GL_LIGHT0)   # add one light
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, vec(0, 0, 1, 1))
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, vec(1, 0.5, 0, 1))
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, vec(0, 1, 0, 1))
    #gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, vec(0, 2, 0, 1))

    #gl.glLightf(gl.GL_LIGHT0, gl.GL_CONSTANT_ATTENUATION, 1.0) # default is 1.0
    #gl.glLightf(gl.GL_LIGHT0, gl.GL_LINEAR_ATTENUATION, 0.1)
    gl.glLightf(gl.GL_LIGHT0, gl.GL_QUADRATIC_ATTENUATION, 0.1)

    #gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
    #                vec(1.0, 1.0, 1.0, 1))
    #gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR,
    #                vec(1.0, 1.0, 1.0, 1))
    #gl.glMaterialf(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 90)

    # enable texturing
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

    def __init__(self, data_path, position=None):
        if position is None:
            position = Vector3(0, 0, 0)
        self.vertex_lists = _load_model(data_path)  # models embed textures
        self.position = position

    def draw(self):
        for texture, vlist in self.vertex_lists.items():
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture.id)
            gl.glPushMatrix()
            gl.glTranslatef(*self.position)
            gl.glRotatef(self.angle, 0, 0, 1)
            vlist.draw(gl.GL_TRIANGLES)
            gl.glPopMatrix()