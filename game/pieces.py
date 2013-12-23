import json
from math import copysign
from random import randint
import weakref
import math

from euclid import Vector3
from pyglet import gl
from pyglet.graphics import Batch
from game.obj_batch import OBJ

import game


def roundvec(v, n=2):
    return Vector3(round(v.x, n), round(v.y, n), round(v.z, n))
X_AXIS = Vector3(1, 0, 0)
Z_AXIS = Vector3(0, 0, 1)


class PieceList(list):
    """A list subclass that handles special filtering of pieces by various
    attributes:
        * player
        * moved
        * can_rotate
        * rotated
        * command
    """
    def filter(self,
               player=None,
               moved=None,
               can_rotate=None,
               rotated=None,
               command=None):
        """Filter this list by the specified attributes, then return another
        PieceList.
        """
        sublist = self
        if player is not None:
            sublist = [_ for _ in sublist if _.player is player]
        if moved is not None:
            # If it has no speed, it can't be moved
            for _ in sublist:
                if _.speed == 0:
                    _.moved = True  # TODO: maybe better as a property?
            sublist = [_ for _ in sublist if _.moved == moved]
        if can_rotate is not None:
            if can_rotate:
                sublist = [_ for _ in sublist if _.rotation_angle < 360]
            else:
                sublist = [_ for _ in sublist if _.rotation_angle == 360]
        if rotated is not None:
            sublist = [_ for _ in sublist if _.rotated == rotated]
        if command is not None:
            if command:
                sublist = [_ for _ in sublist if _.command_count > 0]
            else:
                sublist = [_ for _ in sublist if _.command_count <= 0]

        return PieceList(sublist)

    def limit(self, n):
        return self[:n]

    def load_from_file(self, board, filename, players):
        path = 'resources/board_states/' + filename + '.board'
        with open(path, 'r') as infile:
            data = json.load(infile)
        for piece in data:
            P = getattr(game.pieces, piece['class'])
            player = players[piece['player']]
            x, y = piece['position']
            direction = Vector3(1, 0, 0)
            direction = direction.rotate_around(
                Z_AXIS, piece['rotation'] * math.pi / 180)
            self.append(P(board, player, x, y, direction))


class Piece(object):
    # TODO: Different piece color per player (duh)
    command_count = 0  # number of pieces this can command
    speed = 0  # number of movement squares
    rotation_angle = 360  # rotations must be a multiple of this number
    rotation_offset = 0  # number of degress offset it starts at
    # piece state
    moved = False  # TODO: this probably is no longer necessary
    # rendering
    _model = None

    def __init__(self, board, player, x, y, direction):
        self.board = weakref.proxy(board)
        self.player = player  # TODO: weakref?
        # place the piece on the board
        self.position = Vector3(x - 3.5, y - 3.5, 0)
        # load the model
        # TODO: Cached loading
        # TODO: Per-player loading
        model_filename = 'skins/pieces/default/models/player1/{}.obj'.format(
            self.__class__.__name__)
        self._obj = OBJ(model_filename,
                        texture_path='skins/pieces/default/textures/')
        self.batch = Batch()
        self._obj.add_to(self.batch)
        # set the rotation
        self.direction = direction
        self.old_direction = self.direction
        # TODO: is angle necessary anymore?
        self.angle = (self.direction.angle(X_AXIS)*180/math.pi -
                      self.rotation_offset)
        # generate a color key
        # TODO: Ensure this *never* collides (it definitely has a chance)
        self.color_key = (randint(1, 254) / 255.,
                          randint(1, 254) / 255.,
                          randint(1, 254) / 255.)
        self._color_key_processed = [int(round(_*255)) for _ in self.color_key]
        # set remaining_move to speed
        self.remaining_move = self.speed

    def draw(self, scale=1):
        gl.glPushMatrix()
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTranslatef(*self.position)
        gl.glRotatef(self.angle, 0, 0, 1)
        gl.glScalef(scale, scale, scale)
        self.batch.draw()
        gl.glPopMatrix()

    def draw_for_picker(self, scale=1):
        # disable stuff
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_LIGHTING)
        gl.glColor3f(*self.color_key)
        gl.glPushMatrix()
        gl.glTranslatef(*self.position)
        gl.glRotatef(self.angle, 0, 0, 1)
        gl.glScalef(scale, scale, scale)
        # This is a weird way of doing it, but hey, whatever
        for v1 in self.batch.group_map.values():
            for v2 in v1.values():
                v2.draw(gl.GL_TRIANGLES)
        gl.glPopMatrix()
        # re-enable stuff
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_TEXTURE_2D)

    @property
    def rotated(self):
        return roundvec(self.direction) != roundvec(self.old_direction)

    def rotate(self):
        self.direction = self.direction.rotate_around(
            Z_AXIS, self.rotation_angle * math.pi / 180)
        self.angle += self.rotation_angle

    def reset(self):
        self.moved = False
        self.remaining_move = self.speed
        self.old_direction = self.direction

    def move(self):
        # This is always an *attempted* move, so it's marked such.
        self.moved = True
        # Decrement the recursion counter or exit
        if self.remaining_move:
            self.remaining_move -= 1
        else:
            return
        # Make the vector have all 1s, 0s, and -1s.
        v = roundvec(self.direction, 0)
        # Check out of bounds
        target = self.position + v  # Only move one square at a time
        # Adjust because board center is (0, 0)
        w, h = self.board.width / 2, self.board.height / 2
        if abs(target.x) > w or abs(target.y) > h:
            return
        # Check the board for pieces existing at the target
        for p in self.board.pieces[:]:
            if p.position == target:
                engaged = roundvec(p.direction) == roundvec(-self.direction)
                can_capture = not engaged or p.rotation_angle == 360
                if p.player != self.player and can_capture:
                    self.board.pieces.remove(p)
                else:
                    return
        # All's clear! Move.
        self.position = target
        # Recurse
        self.move()

    @property
    def square_center(self):
        x, y = self.position.x, self.position.y
        return int(x) + copysign(.5, x), int(y) + copysign(.5, y)

    def matches_color(self, color):
        return self._color_key_processed == color


###############################################################################
# Specific Piece Subclasses
###############################################################################
class B0(Piece):
    command_count = 1


class O1(Piece):
    speed = 1
    rotation_angle = 90


class O2(Piece):
    speed = 2
    rotation_angle = 90


class D1(Piece):
    speed = 1
    rotation_angle = 90
    rotation_offset = 45


class D2(Piece):
    speed = 2
    rotation_angle = 90
    rotation_offset = 45


class A1(Piece):
    speed = 1
    rotation_angle = 45


class A2(Piece):
    speed = 2
    rotation_angle = 45