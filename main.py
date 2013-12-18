#!/usr/bin/env python
from __future__ import print_function
import sys
import pyglet
# TODO: Is there a better place to put this stuff?
if 'nogldebug' in sys.argv:
    pyglet.options['debug_gl'] = False

from euclid import Vector3
from game.renderer import WINDOW
from game.board import BOARD

Z_AXIS = Vector3(0, 0, 1)

@WINDOW.event
def on_draw():
    WINDOW.clear()
    WINDOW.enable_3d()
    BOARD.draw()
    WINDOW.finish()


# TODO: Scroll to zoom
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
    # TODO: it's glitchy when at the very extremes
    if pyglet.window.mouse.RIGHT & buttons:
        cam = WINDOW.camera
        cam.position = cam.position.rotate_around(Z_AXIS, -dx / 64.)
        axis = cam.up.cross(cam.position)
        cam.position = cam.position.rotate_around(axis, dy / 64.)


def main():
    WINDOW.camera.position = Vector3(8, 0, 4)
    WINDOW.camera.looking_at = BOARD.position
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