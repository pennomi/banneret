#!/usr/bin/env python
from __future__ import print_function
import sys
import pyglet
# TODO: Is there a better place to put this stuff?
if 'nogldebug' in sys.argv:
    pyglet.options['debug_gl'] = False

from pyglet import gl
from pyglet.window import key

from game import renderer
from game.renderer import WINDOW
from game.board import BOARD


@WINDOW.event
def on_resize(width, height):
    return renderer.configure_gl_viewport(width, height)


if 'fps' in sys.argv:
    pyglet.clock.schedule_interval(lambda dt: print(pyglet.clock.get_fps()), 1)


@WINDOW.event
def on_draw():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # Move the camera
    gl.glLoadIdentity()
    position = list(BOARD.cam)
    looking_at = list(BOARD._model.position)
    up = [0, 0, 1]
    gl.gluLookAt(*(position + looking_at + up))

    # Draw stuff
    BOARD.draw()
    gl.glFinish()


@WINDOW.event
def on_key_press(symbol, modifiers):
    # TODO: smooth scroll and up/down
    if symbol in [key.LEFT, key.A]:
        BOARD.cam.rotate_around_z(-10)
    elif symbol in [key.RIGHT, key.D]:
        BOARD.cam.rotate_around_z(10)


def main():
    renderer.gl_setup()
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