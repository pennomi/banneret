import pyglet
from pyglet.gl import gl
from game.pieces import PieceList
from game.utils import Vector3
from game.renderer import Model, draw_highlight, color_at_point
from collections import deque

SURFACE_HEIGHT = 0.36
WHITE_HIGHLIGHT = (1.0, 1.0, 1.0, .75)
BLUE_HIGHLIGHT = (0.0, 0.0, 0.8, .75)
RED_HIGHLIGHT = (0.8, 0.0, 0.0, .75)


class Player(object):
    name = ""

    def __init__(self, name):
        self.name = name


class Board(object):
    """The global gameboard. You shouldn't ever instantiate this;
    Instead, just use the provided global BOARD object, below.
    """

    def __init__(self):
        # set up players
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = deque([player1, player2])
        self.active_player = self.players[0]

        # set up pieces
        self.pieces = PieceList()
        self.pieces.load_from_file('default', self.players)
        self.selected_piece = None

        # misc setup
        self.mouse = (0, 0)
        self._model = Model('board', Vector3(0, 0, -SURFACE_HEIGHT))
        self.cam = Vector3(8, 0, 4)
        pyglet.clock.schedule_interval(self.update, 1 / 60.)

    def update(self, dt):
        self.selected_piece = self.get_selected_piece()

    def click(self):
        piece = self.selected_piece
        if not piece:
            return
        my_pieces = self.pieces.filter(player=self.active_player)
        if piece in my_pieces.filter(moved=False):
            piece.move()
            return
        if not my_pieces.filter(moved=False):
            self.pass_turn()

    def pass_turn(self):
        self.players.append(self.players.popleft())
        self.active_player = self.players[0]
        for piece in self.pieces:
            piece.reset()

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
        my_pieces = self.pieces.filter(player=self.active_player)
        if self.selected_piece and self.selected_piece in my_pieces:
            draw_highlight(self.selected_piece.square_center, WHITE_HIGHLIGHT)

        for piece in my_pieces.filter(moved=False):
            draw_highlight(piece.square_center, BLUE_HIGHLIGHT)


BOARD = Board()