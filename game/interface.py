"""Support for loading *.interface files."""
from pyglet import gl
import pyglet
from pyglet.sprite import Sprite


def draw_rect(x, y, width, height):
    """A convenience function to draw the button rectangle."""
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(x, y)
    gl.glVertex2f(x + width, y)
    gl.glVertex2f(x + width, y + height)
    gl.glVertex2f(x, y + height)
    gl.glEnd()


# TODO: Batch-based rendering for all these elements
class View(Sprite):
    def __init__(self, **kwargs):
        """All UI elements inherit from this base class."""
        self._window = kwargs.pop('window')
        self._window.push_handlers(self)
        image = pyglet.image.load(
            'skins/interfaces/default/textures/{}'.format(kwargs.pop('image')))
        self.id = kwargs.pop('id')
        super(View, self).__init__(image, **kwargs)

    def cleanup(self):
        self._window.remove_handlers(self)

    def __contains__(self, p):
        """Check if the point is within the boundaries."""
        return (0 < p[0] - self.x < self.width and
                0 < p[1] - self.y < self.height)


class Button(View):
    def __init__(self, **kwargs):
        self.charged = False
        super(Button, self).__init__(**kwargs)

    def on_mouse_press(self, x, y, button, modifiers):
        self.charged = (x, y) in self

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.charged = (x, y) in self

    def on_mouse_release(self, x, y, button, modifiers):
        if (x, y) in self and self.visible:
            self.on_press()
        self.charged = False

    def on_press(self):
        pass


class TextButton(Button):
    def __init__(self, **kwargs):
        self._label = pyglet.text.Label(
            kwargs.pop('text'), anchor_x='center', anchor_y='center')
        super(TextButton, self).__init__(**kwargs)

    def draw(self):
        super(TextButton, self).draw()
        if self.visible:
            self._label.x = self.x + self.width / 2
            self._label.y = self.y + self.height / 2
            self._label.draw()

    @property
    def text(self):
        return self._label.text
    @text.setter
    def text(self, value):
        self._label.text = value

'''
class Control(pyglet.event.EventDispatcher):
    """The base of all clickable widgets."""
    hidden = False

    def __init__(self, parent=None, x=0, y=0, w=0, h=0):
        super(Control, self).__init__()
        self.x, self.y, self.w, self.h = x, y, w, h
        #self.parent = parent
        #self.parent.push_handlers(self)

    def hit_test(self, x, y):
        """Check if the point is within the control area."""
        return 0 < x - self.x < self.w and 0 < y - self.y < self.h

    def cleanup(self):
        pass#self.parent.remove_handlers(self)


class Button(Control):
    charged = False

    def draw(self):
        gl.glColor3f(0, 1, 1)
        if self.charged:
            gl.glColor3f(1, 0, 0)
        draw_rect(self.x, self.y, self.w, self.h)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.hit_test(x, y):
            self.charged = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.charged = self.hit_test(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hit_test(x, y):
            self.dispatch_event('on_press')
        self.charged = False
Button.register_event_type('on_press')


class TextButton(Button):
    def __init__(self, parent=None, text="", x=0, y=0, w=0, h=0, **kwargs):
        super(TextButton, self).__init__(parent=None, x=x, y=y, w=w, h=h)
        self._label = pyglet.text.Label(text, anchor_x='center',
                                        anchor_y='center')

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
'''