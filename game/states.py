"""The class that keeps track of what widgets to display on the screen and
where to put them.
"""
from weakref import proxy
from euclid import Vector3
import pyglet
import sys
from game.renderer import BaseGameState
from game.board import Board

BOARD = None


class GameState(BaseGameState):
    """The Banneret-specific base GameState."""
    def __init__(self, window):
        super(GameState, self).__init__(window)
        global BOARD
        if not BOARD:
            BOARD = Board(window)
        self.board = proxy(BOARD)

    def draw_3d(self):
        super(GameState, self).draw_3d()
        self.board.draw()


class MainMenuState(GameState):
    """Handle the main menu state."""
    def __init__(self, window):
        super(MainMenuState, self).__init__(window)
        self.load_interface('main.interface')
        self.views.start_game.on_press = (
            lambda: self.window.set_state(PlayGameState))
        # TODO this will eventually show a "Do you want to quit?" dialog
        self.views.exit.on_press = sys.exit


class PlayGameState(GameState):
    """Handle the playing of the game."""
    def __init__(self, window):
        super(PlayGameState, self).__init__(window)
        self.board.load_state('default')
        self.load_interface('play.interface')
        self.views.end_turn.on_press = self.board.pass_turn
        self.views.main_menu.on_press = (
            lambda: self.window.set_state(MainMenuState))

    # TODO: Scroll to zoom
    def on_mouse_press(self, x, y, button, modifiers):
        if button in [pyglet.window.mouse.LEFT]:
            self.board.click()

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
        # Update widget visibility
        self.views.end_turn.visible = not self.board.pieces.filter(
            player=self.board.active_player, moved=False)
        # Draw the GUI
        super(PlayGameState, self).draw_2d()
