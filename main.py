#!/usr/bin/env python
from __future__ import print_function
import sys
import pyglet
# TODO: Is there a better place to put this stuff?
from game.utils import Vector3

if 'nogldebug' in sys.argv:
    pyglet.options['debug_gl'] = False

from pyglet import gl
from game.renderer import WINDOW
from game.board import BOARD


@WINDOW.event
def on_draw():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    WINDOW.enable_3d()

    # Draw stuff
    BOARD.draw()
    gl.glFinish()


# TODO: Move as many of these functions off to the window subclass as possible
# TODO: Scroll to zoom
@WINDOW.event
def on_mouse_motion(x, y, dx, dy):
    WINDOW.mouse.x, WINDOW.mouse.y = x, y


@WINDOW.event
def on_mouse_press(x, y, button, modifiers):
    if button in [pyglet.window.mouse.LEFT]:
        BOARD.click()
    for control in [BOARD.end_turn_btn]:
        if control.hit_test(x, y):
            control.on_mouse_press(x, y, button, modifiers)


@WINDOW.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    # Move cam when holding right and dragging
    if pyglet.window.mouse.RIGHT & buttons:
        WINDOW.camera.position.rotate_around_z(-dx / 2.)
        # TODO: rotate around camera.up
        z_angle = WINDOW.camera.position.angle_around_z
        WINDOW.camera.position.angle_around_z = 0
        WINDOW.camera.position.rotate_around_y(dy / 2.)
        WINDOW.camera.position.angle_around_z = z_angle


def main():
    WINDOW.camera.position = Vector3(8, 0, 4)
    WINDOW.camera.looking_at = BOARD._model.position
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