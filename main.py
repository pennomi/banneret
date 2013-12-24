#!/usr/bin/env python
from __future__ import print_function
import sys
import pyglet
# TODO: Is there a better place to put this stuff?

if 'nogldebug' in sys.argv:
    pyglet.options['debug_gl'] = False

from game.board import Board
from game.renderer import GameWindow3d
from game.states import MainMenu, GameHUD

from euclid import Vector3


def main():
    window = GameWindow3d(GameHUD, resizable=True)
    board = Board(window)
    window.gamestate.board = board
    window.camera.position = Vector3(8, 0, 4)
    window.camera.looking_at = board.position
    pyglet.app.run()

if __name__ == "__main__":
    if 'profile' in sys.argv:
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()
        main()
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.strip_dirs().sort_stats('time').print_stats(20)
    else:
        main()