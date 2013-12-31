"""The class that keeps track of what widgets to display on the screen and
where to put them.
"""
from weakref import proxy
from euclid import Vector3
import pyglet
from game.interface import TextButton
from game.renderer import BaseGameState
from game.board import Board

BOARD = None


class GameState(BaseGameState):
    def __init__(self, window):
        super(GameState, self).__init__(window)
        global BOARD
        if not BOARD:
            BOARD = Board(window)
        self.board = proxy(BOARD)

    def on_mouse_press(self, x, y, button, modifiers):
        super(GameState, self).on_mouse_press(x, y, button, modifiers)
        # TODO: can't this be built into button so it works automagically?
        for control in self.controls.values():
            if control.hit_test(x, y):
                control.on_mouse_press(x, y, button, modifiers)

    def draw_3d(self):
        super(GameState, self).draw_3d()
        self.board.draw()


class MainMenuState(GameState):
    """Handle the main menu state."""
    def __init__(self, window):
        super(MainMenuState, self).__init__(window)
        self.load_interface('main.interface')
        self.controls["start_game"].on_press = lambda: self.window.set_state(PlayGameState)


class PlayGameState(GameState):
    def __init__(self, window):
        super(PlayGameState, self).__init__(window)
        self.board.load_state('default')

        # TODO: Reposition and resize when the window resizes, perhaps make
        #       this % based instead of absolute?
        position = (self.window.width - 50 - 100, 50, 100, 30)
        end_turn_btn = TextButton(self.window, "End Turn", *position)
        end_turn_btn.on_press = self.board.pass_turn
        self.controls["end_turn_btn"] = end_turn_btn
        main_menu_btn = TextButton(self.window, "Return to Main Menu", 0, 0, 200, 60)
        main_menu_btn.on_press = lambda: self.window.set_state(MainMenuState)
        self.controls["main_menu_btn"] = main_menu_btn

    # TODO: Scroll to zoom
    def on_mouse_press(self, x, y, button, modifiers):
        super(PlayGameState, self).on_mouse_press(x, y, button, modifiers)
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
        self.controls["end_turn_btn"].hidden = self.board.pieces.filter(
            player=self.board.active_player, moved=False)
        # Draw the GUI
        super(PlayGameState, self).draw_2d()
