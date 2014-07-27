"""Support for loading *.interface files."""
from pyglet import gl
import pyglet
from pyglet.sprite import Sprite

CHARACTER_WHITELIST = set("0123456789 -+/*")


def clean_value(v, window):
    v = v.replace('window.verticalcenter', str(window.height / 2))
    v = v.replace('window.horizontalcenter', str(window.height / 2))
    v = v.replace('window.left', "0")
    v = v.replace('window.bottom', "0")
    v = v.replace('window.top', str(window.height))
    v = v.replace('window.right', str(window.width))
    if len(set(v) - CHARACTER_WHITELIST):
        raise AttributeError("Invalid characters specified in calculation.")
    return v


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