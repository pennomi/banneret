import pyglet
from game.utils import Vector3
from game.renderer import Model, _load_texture, draw_rect

SURFACE_HEIGHT = 0.36


class Player(object):
    name = ""

    def __init__(self, name):
        self.name = name


class Piece(object):
    command_count = 0  # number of pieces this can command
    speed = 0  # number of movement squares
    rotation_angle = 90  # rotations must be a multiple of this number
    rotation_offset = 0  # number of degress offset it starts at
    # piece state
    moved = False
    rotated = False
    direction = None
    # rendering
    _model = None
    _texture_override = ""

    def __init__(self, player, x, y):
        # place the piece on the board
        self.direction = Vector3(1, 0, 0)
        center = Vector3(x - 3.5, y - 3.5, SURFACE_HEIGHT)
        # create and monkey patch the model
        self._model = Model('square', position=center)
        v = {_load_texture(self._texture_override): v
             for v in self._model.vertex_lists.values()}
        self._model.vertex_lists = v
        self.draw = self._model.draw  # forward draw requests


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

    def __init__(self):
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = [player1, player2]
        self.pieces = [
            O1(player1, 0, 0),
            O1(player2, 7, 6),
        ]
        self._model = Model('board')
        self.cam = Vector3(8, 0, 4)
        pyglet.clock.schedule_interval(self.update, 1 / 60.)
        self.highlight_position = None

    def update(self, dt):
        self.highlight_square(0, 0)

    def highlight_square(self, x, y):
        # TODO: Many squares need highlighted at once with different colors
        self.highlight_position = Vector3(x-3.5, y-3.5, SURFACE_HEIGHT+.01)

    def draw(self):
        for piece in self.pieces:
            piece.draw(scale=0.8)
        self._model.draw()
        if self.highlight_position:
            draw_rect(self.highlight_position, 1, 1, (1.0, 1.0, 1.0, .75))


BOARD = Board()