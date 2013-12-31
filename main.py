#!/usr/bin/env python
import sys
from euclid import Vector3
import pyglet
# TODO: Is there a better place to put this stuff?

if 'nogldebug' in sys.argv:
    pyglet.options['debug_gl'] = False

from game.renderer import GameWindow3d
from game.states import MainMenuState


def main():
    window = GameWindow3d(MainMenuState, resizable=True)
    # TODO: camera should be set in the state
    window.camera.position = Vector3(8, 0, 4)
    window.camera.looking_at = window.gamestate.board.position
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