"""The class that keeps track of what widgets to display on the screen and
where to put them.
"""
from _weakref import proxy
from euclid import Vector3
import pyglet
from game.renderer import TextButton


# TODO: move this into renderer and subclass it into something Banneret-specific
class GameState(object):
    def __init__(self, window):
        self.window = proxy(window)
        self.widgets = []
        self.camera_look_at = Vector3(0, 0, 0)

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def draw_3d(self):
        self.board.draw()

    def draw_2d(self):
        for w in self.widgets:
            w.draw()


class MainMenu(GameState):
    def __init__(self, window):
        super(MainMenu, self).__init__(window)
        self.start_button = TextButton(self.window, "Start Game", 0, 0, 100, 100)
        self.widgets.append(self.start_button)


class SettingsMenu(GameState):
    pass


class GameHUD(GameState):
    # TODO: Scroll to zoom
    def on_mouse_press(self, x, y, button, modifiers):
        if button in [pyglet.window.mouse.LEFT]:
            self.board.click()
        for control in [self.board.end_turn_btn]:
            if control.hit_test(x, y):
                control.on_mouse_press(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        z = Vector3(0, 0, 1)
        # Move cam when holding right and dragging
        # TODO: it's glitchy when at the very extremes
        if pyglet.window.mouse.RIGHT & buttons:
            cam = self.window.camera
            cam.position = cam.position.rotate_around(z, -dx / 64.)
            axis = cam.up.cross(cam.position)
            cam.position = cam.position.rotate_around(axis, dy / 64.)

    def draw_2d(self):
        super(GameHUD, self).draw_2d()
        # Draw the GUI
        if not self.board.pieces.filter(player=self.board.active_player,
                                        moved=False):
            self.board.end_turn_btn.draw()
