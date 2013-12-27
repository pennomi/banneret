from __future__ import print_function
from weakref import proxy
import pyglet
import sys
from pyglet import gl
from euclid import Vector3


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


class BaseGameState(object):
    def __init__(self, window):
        self.window = proxy(window)
        self.widgets = []
        self.camera_look_at = Vector3(0, 0, 0)

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def draw_3d(self):
        pass

    def draw_2d(self):
        for w in self.widgets:
            w.draw()


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
    hidden = False

    def __init__(self, parent, x, y, w, h):
        super(Control, self).__init__()
        self.x, self.y, self.w, self.h = x, y, w, h
        self.parent = parent

    def hit_test(self, x, y):
        return 0 < x - self.x < self.w and 0 < y - self.y < self.h

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

    def draw(self):
        if self.hidden:
            return
        super(TextButton, self).draw()
        self.draw_label()

    @property
    def text(self):
        return self._label.text
    @text.setter
    def text(self, text):
        self._label.text = text
