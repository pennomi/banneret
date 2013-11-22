from random import uniform
import weakref
import pyglet
from pyglet.gl import gl
from game.utils import Vector3
from game.renderer import Model, _load_texture, draw_rect, color_at_point
from math import copysign

SURFACE_HEIGHT = 0.36


class Player(object):
    name = ""

    def __init__(self, name):
        self.name = name


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
        self.player = weakref.proxy(player)
        # place the piece on the board
        self.direction = Vector3(1, 0, 0)
        center = Vector3(x - 3.5, y - 3.5, 0)
        # create and monkey patch the model
        self._model = Model('square', position=center)
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
    def position(self):
        return self._model.position
    @position.setter
    def position(self, val):
        self._model.position = val

    def matches_color(self, color):
        return self._color_key_processed == color


class O1(Piece):
    speed = 1
    _texture_override = "O1.jpg"


#class D1(Piece):
#    speed = 1
#    _texture_override = "D1.jpg"


class Board(object):
    """The global gameboard. You shouldn't ever instantiate this;
    Instead, just use the provided global BOARD object, below.
    """
    mouse = None

    def __init__(self):
        self.highlighted_positions = []
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = [player1, player2]
        self.pieces = [
            O1(player1, 0, 0),
            O1(player2, 7, 6),
        ]
        self._model = Model('board', Vector3(0, 0, -SURFACE_HEIGHT))
        self.cam = Vector3(8, 0, 4)
        pyglet.clock.schedule_interval(self.update, 1 / 60.)

    def update(self, dt):
        self.highlighted_positions = []
        # Operate on whatever the hovered piece is
        selected_piece = self.get_selected_piece()
        if not selected_piece:
            return
        x, y = selected_piece.position.x, selected_piece.position.y
        self.highlighted_positions.append(
            Vector3(int(x) + copysign(.5, x), int(y) + copysign(.5, y), .01))

    def get_selected_piece(self):
        """Via a rendering pass, find if the cursor is over any of the
        active pieces.
        """
        # make a colored rendering pass
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for piece in self.pieces:
            piece.draw_for_picker(color=piece.color_key, scale=0.8)
        # check for a matching color among pieces
        if not self.mouse:
            return None
        color = color_at_point(*self.mouse)
        for piece in self.pieces:
            if piece.matches_color(color):
                return piece
        return None

    def draw(self):
        for piece in self.pieces:
            piece.draw(scale=0.8)
        self._model.draw()
        for p in self.highlighted_positions:
            draw_rect(p, 1, 1, (1.0, 1.0, 1.0, .75))


BOARD = Board()