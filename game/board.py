import pyglet
from game.utils import Vector3
from game.renderer import Model

SURFACE_HEIGHT = 0.36


class Player(object):
    name = ""

    def __init__(self, name):
        self.name = name


class Piece(object):
    command_count = 0  # number of pieces this can command
    speed = 1
    # piece state
    moved = False
    rotated = False
    direction = None
    # rendering
    _model = None

    def __init__(self, player, x, y):
        self.direction = Vector3(1, 0, 0)
        self._model = Model('square', position=Vector3(x - 3.5, y - 3.5,
                                                       SURFACE_HEIGHT))
        self.draw = self._model.draw  # forward draw requests


class Board(object):
    """The global gameboard. You shouldn't ever instantiate this;
    Instead, just use the provided global BOARD object, below.
    """

    def __init__(self):
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = [player1, player2]
        self.pieces = [
            Piece(player1, 0, 0),
            Piece(player2, 7, 6),
        ]
        self._model = Model('board')
        self.cam = Vector3(8, 0, 4)
        pyglet.clock.schedule_interval(self.update, 1 / 60.)

    def update(self, dt):
        pass

    def draw(self):
        for piece in self.pieces:
            piece.draw()
        self._model.draw()


BOARD = Board()