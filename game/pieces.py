import json
from math import copysign
from random import uniform
from game.utils import Vector3
from game.renderer import Model, _load_texture
import game


class PieceList(list):
    """A list subclass that handles special filtering of pieces by various
    attributes:
        * player
        * moved
    """
    def filter(self, player=None, moved=None):
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
        return PieceList(sublist)

    def load_from_file(self, filename, players):
        path = 'resources/board_states/' + filename + '.board'
        with open(path, 'r') as infile:
            data = json.load(infile)
        for piece in data:
            P = getattr(game.pieces, piece['class'])
            player = players[piece['player']]
            x, y = piece['position']
            self.append(P(player, x, y))


class Piece(object):
    command_count = 0  # number of pieces this can command
    speed = 0  # number of movement squares
    rotation_angle = 360  # rotations must be a multiple of this number
    rotation_offset = 0  # number of degress offset it starts at
    # piece state
    moved = False
    rotated = False
    direction = None
    # rendering
    _model = None
    _texture_override = ""

    def __init__(self, player, x, y):
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
        # forward draw requests
        self.draw = self._model.draw
        self.draw_for_picker = self._model.draw_for_picker
        # generate a color key
        # TODO: always generate one that won't have rounding error
        self.color_key = (uniform(0, 1), 0, 0)
        self._color_key_processed = [int(round(_*255)) for _ in self.color_key]

    @property
    def direction(self):
        v = Vector3(1, 0, 0)
        v.angle_around_z = self._model.angle + self.rotation_offset
        return v
    @direction.setter
    def direction(self, v):
        # TODO: validate it's a legal direction
        self._model.angle = v.angle_around_z - self.rotation_offset

    @property
    def position(self):
        return self._model.position
    @position.setter
    def position(self, val):
        self._model.position = val

    def reset(self):
        self.moved = False
        self.rotated = False

    def move(self):
        # Make the vector have all 1s, 0s, and -1s.
        v = Vector3([round(_) for _ in self.direction])
        self.position += v * self.speed  # some pieces move faster
        self.moved = True

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


class D1(Piece):
    speed = 1
    rotation_angle = 90
    rotation_offset = 45
    _texture_override = "D1.jpg"