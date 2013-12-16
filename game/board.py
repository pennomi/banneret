from __future__ import unicode_literals, print_function
import pyglet
from pyglet import gl
from game.pieces import PieceList
from euclid import Vector3
from game.renderer import (Model, draw_highlight, color_at_point, TextButton,
                           WINDOW)
from collections import deque

SURFACE_HEIGHT = 0.36
# TODO: maybe just brighten the highlight on hover?
WHITE_HIGHLIGHT = (1.0, 1.0, 1.0, .75)
BLUE_HIGHLIGHT = (0.0, 0.0, 0.7, .75)
GREEN_HIGHLIGHT = (0.0, 0.7, 0.0, .75)
RED_HIGHLIGHT = (0.7, 0.0, 0.0, .75)


class Player(object):
    name = ""

    def __init__(self, name):
        self.name = name


class Board(object):
    """The global gameboard. You shouldn't ever instantiate this;
    Instead, just use the provided global BOARD object, below.
    """
    width, height = 8, 8
    game_over = False

    def __init__(self):
        # set up players
        player1 = Player('Thane')
        player2 = Player('Stacey')
        self.players = deque([player1, player2])
        self.active_player = self.players[0]

        # set up pieces
        self.pieces = PieceList()
        self.pieces.load_from_file(self, 'default', self.players)
        self.selected_piece = None

        # misc setup
        self._model = Model('board', Vector3(0, 0, -SURFACE_HEIGHT))
        pyglet.clock.schedule_interval(self.update, 1 / 60.)

        # TODO: Reposition and resize when the window resizes, perhaps make
        #       this % based instead of absolute?
        position = (WINDOW.width - 50 - 100, 50, 100, 30)
        self.end_turn_btn = TextButton(WINDOW, "End Turn", *position)
        self.end_turn_btn.on_press = self.pass_turn

    def update(self, dt):
        self.selected_piece = self.get_selected_piece()
        self.check_victory()  # TODO: call in a more efficient place.

    def check_victory(self):
        # check victory
        for player in self.players:
            if not self.pieces.filter(player=player, command=True):
                for piece in self.pieces.filter(player=player):
                    self.pieces.remove(piece)
        my_pieces = self.pieces.filter(player=self.active_player)
        if len(self.pieces) == len(my_pieces):
            print("Player has emerged victorious!")
            self.game_over = True
            # TODO: Some sort of dialog

    def click(self):
        if self.game_over:
            return
        # setup
        piece = self.selected_piece
        if not piece:
            return
        my_pieces = self.pieces.filter(player=self.active_player)
        # process moves
        if piece in my_pieces.filter(moved=False):
            piece.move()
            return
        if my_pieces.filter(moved=False):
            return  # don't process rotation until we're done moving
        # process rotation
        commanders = my_pieces.filter(command=True)
        rotate_limit = sum(piece.command_count for piece in commanders)
        rotated = my_pieces.filter(rotated=True)
        remaining_rotates = rotate_limit - len(rotated)
        if ((remaining_rotates > 0 and
             piece in my_pieces.filter(can_rotate=True)) or
                piece in rotated):
            # TODO: reverse rotate on right-click?
            piece.rotate()

    def pass_turn(self):
        self.players.append(self.players.popleft())
        self.active_player = self.players[0]
        for piece in self.pieces:
            piece.reset()

    def get_selected_piece(self):
        """Via a special rendering pass, find if the cursor is over any of the
        active pieces.
        """
        WINDOW.enable_3d()

        # make a specially colored rendering pass
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        for piece in self.pieces:
            piece.draw_for_picker(color=piece.color_key, scale=0.8)
        # check for a matching color among pieces
        color = color_at_point(WINDOW.mouse.x, WINDOW.mouse.y)
        for piece in self.pieces:
            if piece.matches_color(color):
                return piece
        return None

    def draw(self):
        # draw board and pieces
        self._model.draw()
        for piece in self.pieces:
            piece.draw(scale=0.8)

        # highlight the squares under the right pieces
        my_pieces = self.pieces.filter(player=self.active_player)
        if self.selected_piece and self.selected_piece in my_pieces:
            draw_highlight(self.selected_piece.square_center, WHITE_HIGHLIGHT)
            # TODO: instead draw an arrow of where it will move

        still_to_move = my_pieces.filter(moved=False)
        if still_to_move:
            for piece in still_to_move:
                draw_highlight(piece.square_center, BLUE_HIGHLIGHT)
        else:
            commanders = my_pieces.filter(command=True)
            rotate_limit = sum(piece.command_count for piece in commanders)
            rotated = my_pieces.filter(rotated=True)
            for piece in commanders.limit(rotate_limit - len(rotated)) + rotated:
                draw_highlight(piece.square_center, GREEN_HIGHLIGHT)

        # Draw the GUI
        if not my_pieces.filter(moved=False):
            WINDOW.enable_2d()
            self.end_turn_btn.draw()

BOARD = Board()