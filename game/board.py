from random import uniform
import weakref
import pyglet
from pyglet.gl import gl
from game.utils import Vector3
from game.renderer import Model, _load_texture, draw_highlight, color_at_point
from math import copysign

SURFACE_HEIGHT = 0.36
WHITE_HIGHLIGHT = (1.0, 1.0, 1.0, .75)
BLUE_HIGHLIGHT = (0.0, 1.0, 0.0, .75)


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
        self.player = player
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

    @property
    def square_center(self):
        x, y = self.position.x, self.position.y
        return int(x) + copysign(.5, x), int(y) + copysign(.5, y)

    def matches_color(self, color):
        return self._color_key_processed == color


class O1(Piece):
    speed = 1
    _texture_override = "O1.jpg"


#class D1(Piece):
#    speed = 1
#    _texture_override = "D1.jpg"


class PieceList(list):
    def filter(self, player=None, moved=None):
        sublist = self
        if player:
            sublist = [_ for _ in sublist if _.player is player]
        if moved:
            sublist = [_ for _ in sublist if _.moved == moved]
        return PieceList(sublist)


class Board(object):
    """The global gameboard. You shouldn't ever instantiate this;
    Instead, just use the provided global BOARD object, below.
    """

    def __init__(self):
        # set up players
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = [player1, player2]
        self.current_player = self.players[0]

        # set up pieces
        self.pieces = PieceList([
            O1(player1, 0, 0),
            O1(player2, 7, 6),
        ])
        self.selected_piece = None

        # misc setup
        self.mouse = (0, 0)
        self._model = Model('board', Vector3(0, 0, -SURFACE_HEIGHT))
        self.cam = Vector3(8, 0, 4)
        pyglet.clock.schedule_interval(self.update, 1 / 60.)

    def update(self, dt):
        self.selected_piece = self.get_selected_piece()

    def get_selected_piece(self):
        """Via a rendering pass, find if the cursor is over any of the
        active pieces.
        """
        # make a colored rendering pass
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for piece in self.pieces:
            piece.draw_for_picker(color=piece.color_key, scale=0.8)
        # check for a matching color among pieces
        color = color_at_point(*self.mouse)
        for piece in self.pieces:
            if piece.matches_color(color):
                return piece
        return None

    def draw(self):
        # draw board
        self._model.draw()

        # draw pieces
        for piece in self.pieces:
            piece.draw(scale=0.8)

        # highlight the squares under the right pieces
        my_pieces = self.pieces.filter(player=self.current_player)
        if self.selected_piece and self.selected_piece in my_pieces:
            draw_highlight(self.selected_piece.square_center, WHITE_HIGHLIGHT)

        for piece in my_pieces.filter(moved=False):
            draw_highlight(piece.square_center, BLUE_HIGHLIGHT)


BOARD = Board()