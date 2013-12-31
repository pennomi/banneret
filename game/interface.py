"""Support for loading *.interface files."""
from pyglet import gl
import pyglet


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

    def __init__(self, parent, x=0, y=0, w=0, h=0):
        super(Control, self).__init__()
        self.x, self.y, self.w, self.h = x, y, w, h
        self.parent = parent
        self.parent.push_handlers(self)

    def hit_test(self, x, y):
        return 0 < x - self.x < self.w and 0 < y - self.y < self.h

    def cleanup(self):
        self.parent.remove_handlers(self)


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
    def __init__(self, parent, text="", x=0, y=0, w=0, h=0):
        super(TextButton, self).__init__(parent, x=x, y=y, w=w, h=h)
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