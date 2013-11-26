import json
from math import copysign
from random import randint
import weakref
from game.utils import Vector3
from game.renderer import Model, _load_texture
import game


class PieceList(list):
    """A list subclass that handles special filtering of pieces by various
    attributes:
        * player
        * moved
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
            direction.angle_around_z = piece['rotation']
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
    _texture_override = ""

    def __init__(self, board, player, x, y, direction):
        self.board = weakref.proxy(board)
        self.player = player  # TODO: weakref?
        # place the piece on the board
        center = Vector3(x - 3.5, y - 3.5, 0)
        # create and monkey patch the model
        self._model = Model('square', position=center)
        if not self._texture_override:
            raise ValueError("Subclass must provide a texture override.")
        v = {_load_texture(self._texture_override): v
             for v in self._model.vertex_lists.values()}
        self._model.vertex_lists = v
        # set the rotation
        self.direction = direction
        self.direction_target = self.direction
        # forward draw requests
        self.draw = self._model.draw
        self.draw_for_picker = self._model.draw_for_picker
        # generate a color key
        # TODO: Ensure this *never* collides (it definitely has a chance)
        self.color_key = (randint(1, 254) / 255.,
                          randint(1, 254) / 255.,
                          randint(1, 254) / 255.)
        self._color_key_processed = [int(round(_*255)) for _ in self.color_key]
        # set remaining_move to speed
        self.remaining_move = self.speed

    @property
    def direction_target(self):
        v = Vector3(1, 0, 0)
        v.angle_around_z = self._model.angle + self.rotation_offset
        v = v.__round__(2)
        return v
    @direction_target.setter
    def direction_target(self, v):
        # TODO: validate it's a legal direction
        self._model.angle = v.angle_around_z - self.rotation_offset

    @property
    def position(self):
        return self._model.position
    @position.setter
    def position(self, val):
        self._model.position = val

    @property
    def rotated(self):
        return self.direction.__round__(2) != self.direction_target.__round__(2)

    def rotate(self):
        new_direction = Vector3(self.direction_target)
        new_direction.angle_around_z += self.rotation_angle
        self.direction_target = new_direction

    def reset(self):
        self.moved = False
        self.rotated = False

    def move(self):
        # This is always an *attempted* move, so it's marked such.
        self.moved = True
        # Decrement the recursion counter or exit
        if self.remaining_move:
            self.remaining_move -= 1
        else:
            self.remaining_move = self.speed
            return
        # Make the vector have all 1s, 0s, and -1s.
        v = self.direction.__round__(0)
        # Check out of bounds
        target = self.position + v  # Only move one square at a time
        # adjust because board center is (0, 0)
        w, h = self.board.width / 2, self.board.height / 2
        if abs(target.x) > w or abs(target.y) > h:
            self.remaining_move = self.speed
            return
        # Check the board for pieces existing at the target
        for p in self.board.pieces[:]:
            if p.position == target:
                if p.player != self.player and p.direction != -self.direction:
                    self.board.pieces.remove(p)
                else:
                    self.remaining_move = self.speed
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
    _texture_override = "B0.jpg"


class O1(Piece):
    speed = 1
    rotation_angle = 90
    _texture_override = "O1.jpg"


class O2(Piece):
    speed = 2
    rotation_angle = 90
    _texture_override = "O2.jpg"


class D1(Piece):
    speed = 1
    rotation_angle = 90
    rotation_offset = 45
    _texture_override = "D1.jpg"