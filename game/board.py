import math
from random import uniform
import weakref
import pyglet
from pyglet.gl import gl
from game.utils import Vector3
from game.renderer import Model, _load_texture, draw_rect, draw_line, SIZE, intersection_for_point

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
        self.pick_color = [int(round(_ * 255)) for _ in self.color_key]


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
    #rays = []
    highlight_position = None

    def __init__(self):
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
        self.highlight_position = None
        selected_piece = self.calculate_selected_piece()
        if not selected_piece:
            return
        self.highlight_square(selected_piece._model.position.x,
                              selected_piece._model.position.y)

    def highlight_square(self, x, y):
        # TODO: Many squares need highlighted at once with different colors
        self.highlight_position = Vector3(int(x)+.5, int(y)+.5, .01)

    def calculate_selected_piece(self):
        """Via a pre-rendering pass, """
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for piece in self.pieces:
            piece.draw_for_picker(color=piece.color_key, scale=0.8)
        if self.mouse:
            a = (gl.GLubyte * 3)(0)
            gl.glReadPixels(self.mouse[0], self.mouse[1], 1, 1, gl.GL_RGB,
                            gl.GL_UNSIGNED_BYTE, a)
            selected_color = list(a)
            for piece in self.pieces:
                if piece.pick_color == selected_color:
                    return piece

    def draw(self):
        for piece in self.pieces:
            piece.draw(scale=0.8)
        self._model.draw()
        if self.highlight_position:
            draw_rect(self.highlight_position, 1, 1, (1.0, 1.0, 1.0, .75))
        #for ray in self.rays:
        #    draw_line(*ray)


BOARD = Board()