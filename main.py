import os
import random
import time
import pygame
import pytmx
import pytmx.util_pygame

pygame.init()

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600
DISPLAY_COLOR = pygame.Color(0, 0, 0)
DISPLAY_TICK_DELAY = 60

GAME_BOARD_X = DISPLAY_WIDTH / 1.5
GAME_BOARD_Y = DISPLAY_HEIGHT / 2
GAME_BOARD_TILE_WIDTH = 32
GAME_BOARD_TILE_HEIGHT = 32
GAME_BOARD_TILE_ALPHA_SELECTED = 127
GAME_BOARD_TILE_ALPHA_NORMAL = 255

GAME_BOARD_NUM_PIECES = 12

def load_image(filepath, alpha=False):
    """
    Loads an image from the filepath...
    """

    if not os.path.exists(filepath):
        raise RuntimeError("Failed to find image file: %s!" % filepath)

    image = pygame.image.load(filepath)
    return image.convert_alpha() if alpha else image.convert()

def load_map(filepath):
    """
    Loads a tmx file from the filepath...
    """

    if not os.path.exists(filepath):
        raise RuntimeError("Failed to find tmx file: %s!" % filepath)

    return pytmx.util_pygame.load_pygame(filepath)

class GameMouse(object):

    def __init__(self):
        self._pressed = (0, 0, 0)
        self._last_pressed = (0, 0, 0)
        self._pos = (0, 0)
        self._last_pos = (0, 0)

    @property
    def pressed(self):
        return self._pressed

    @pressed.setter
    def pressed(self, button1, button2, button3):
        self._pressed = (button1, button2, button3)

    @property
    def last_pressed(self):
        return self._last_pressed

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, x, y):
        self._pos = (x, y)

    @property
    def last_pos(self):
        return self._last_pos

    def tick(self):
        self._last_pressed = self._pressed
        self._last_pos = self._pos

        self._pressed = pygame.mouse.get_pressed()
        self._pos = pygame.mouse.get_pos()

class GameResources(object):

    def __init__(self):
        self._images = {}
        self._sounds = {}

    @property
    def images(self):
        return self._images

    @property
    def sounds(self):
        return self._sounds

    def setup(self):
        self._images["piece_black"] = load_image("checker_piece_black.png", True)
        self._images["piece_black_king"] = load_image("checker_piece_black_king.png", True)

    def get_image(self, name):
        try:
            return self._images[name].copy()
        except:
            raise RuntimeError("Failed to get unknown cached image: %s!" % name)

    def get_sound(self, name):
        try:
            return self._sounds[name].copy()
        except:
            raise RuntimeError("Failed to get unknown cached sound: %s!" % name)

class GameTile(object):

    def __init__(self):
        self._index = 0
        self._surface = None
        self._rect = None

        self._x = 0
        self._y = 0
        self._layer = 0

        self._selected = False
        self._piece = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, surface):
        self._surface = surface
        self._rect = surface.get_rect()

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect):
        self._rect = rect

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x
        self._rect.x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._rect.y = y

    @property
    def layer(self):
        return self._layer

    @layer.setter
    def layer(self, layer):
        self._layer = layer

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected):
        self._selected = selected

    @property
    def piece(self):
        return self._piece

    @piece.setter
    def piece(self, piece):
        self._piece = piece

    def tick(self):
        pass

class GamePiece(GameTile):

    def __init__(self, *args, **kwargs):
        GameTile.__init__(self, *args, **kwargs)

        self._tile = None
        self._blinking = False

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, tile):
        self._tile = tile

    @property
    def blinking(self):
        return self._blinking

    @tile.setter
    def blinking(self, blinking):
        self._blinking = blinking

    def tick(self):
        if self._selected:
            self._blinking = not self._blinking

        if self._blinking:
            self._surface.set_alpha(GAME_BOARD_TILE_ALPHA_SELECTED)
        else:
            self._surface.set_alpha(GAME_BOARD_TILE_ALPHA_NORMAL)

class GameBoard(object):

    def __init__(self, game, filepath):
        self._game = game

        self._x = 0
        self._y = 0

        self._pieces = {}
        self._piece_selected = None

        self._tmx_data = load_map(filepath)
        self._tmx_tile_data = { layer: {} for layer in range(len(self._tmx_data.layers)) }
        self._tmx_tile_selected = None

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, y):
        self._y = y

    def setup(self):
        for x in range(self._tmx_data.width):
            for y in range(self._tmx_data.height):
                for layer in range(len(self._tmx_data.layers)):
                    surface = self._tmx_data.get_tile_image(x, y, layer)

                    if not surface:
                        continue

                    self.place_tile(x, y, layer, surface)

        outer_tiles = list(self._tmx_tile_data[0].values())
        inner_tiles = list(self._tmx_tile_data[1].values())
        all_tiles = outer_tiles + inner_tiles

        x_modd = len(all_tiles) + GAME_BOARD_TILE_WIDTH
        y_modd = len(all_tiles) + GAME_BOARD_TILE_HEIGHT

        for tile in all_tiles:
            tile.x += self._x - x_modd
            tile.y += self._y - y_modd

        for index in range(GAME_BOARD_NUM_PIECES):
            self.place_piece(random.choice(inner_tiles), self._game.resources.get_image("piece_black"))

    def place_tile(self, x, y, layer, surface):
        tile = GameTile()
        tile.index = len(self._tmx_tile_data[layer]) + 1
        tile.surface = surface.copy()
        tile.x = x * GAME_BOARD_TILE_WIDTH
        tile.y = y * GAME_BOARD_TILE_HEIGHT
        tile.layer = layer

        self._tmx_tile_data[layer][tile.index] = tile

    def place_piece(self, tile, surface):
        piece = GamePiece()
        piece.index = len(self._pieces) + 1
        piece.surface = surface
        piece.x = tile.x
        piece.y = tile.y

        self._pieces[piece.index] = piece

        tile.piece = piece
        piece.tile = tile

    def clear_selected_tile(self):
        self._tmx_tile_selected.selected = False
        self._tmx_tile_selected.surface.set_alpha(GAME_BOARD_TILE_ALPHA_NORMAL)
        self._tmx_tile_selected = None

    def set_selected_tile(self, tile):
        self._tmx_tile_selected = tile
        self._tmx_tile_selected.selected = True
        self._tmx_tile_selected.surface.set_alpha(GAME_BOARD_TILE_ALPHA_SELECTED)

    def clear_selected_piece(self):
        self._piece_selected.selected = False
        self._piece_selected.blinking = False
        self._piece_selected = None

    def set_selected_piece(self, piece):
        self._piece_selected = piece
        self._piece_selected.selected = True

    def move_selected_piece(self, piece, tile):
        piece.x = tile.x
        piece.y = tile.y

        piece.tile.piece = None

        piece.tile = tile
        tile.piece = piece

        self.clear_selected_piece()

    def tick(self):
        for tile in self._tmx_tile_data[1].values():
            if tile.rect.collidepoint(*self._game.mouse.pos):
                if self._tmx_tile_selected:
                    self.clear_selected_tile()

                self.set_selected_tile(tile)
            else:
                if tile.selected:
                    self.clear_selected_tile()

        if self._game.mouse.pressed[0] and self._piece_selected and self._tmx_tile_selected and self._tmx_tile_selected.piece:
            self.clear_selected_piece()
            self.set_selected_piece(self._tmx_tile_selected.piece)

        if not self._game.mouse.last_pressed[0] and self._game.mouse.pressed[0] and not self._piece_selected and self._tmx_tile_selected and self._tmx_tile_selected.piece:
            self.set_selected_piece(self._tmx_tile_selected.piece)

        if not self._game.mouse.last_pressed[0] and self._game.mouse.pressed[0] and self._piece_selected and self._tmx_tile_selected and not self._tmx_tile_selected.piece:
            self.move_selected_piece(self._piece_selected, self._tmx_tile_selected)

        for piece in self._pieces.values():
            piece.tick()

    def draw(self, surface):
        for layer in self._tmx_tile_data:
            for tile in self._tmx_tile_data[layer].values():
                surface.blit(tile.surface, (tile.x, tile.y))

        for piece in self._pieces.values():
            surface.blit(piece.surface, (piece.x, piece.y))

class Game(object):

    def __init__(self):
        self._display = pygame.display.set_mode([DISPLAY_WIDTH, DISPLAY_HEIGHT])
        self._clock = pygame.time.Clock()
        self._mouse = GameMouse()
        self._resources = GameResources()
        self._shutdown = False

        self._board = GameBoard(self, "wood_board.tmx")
        self._board.x = GAME_BOARD_X
        self._board.y = GAME_BOARD_Y

    @property
    def mouse(self):
        return self._mouse

    @property
    def resources(self):
        return self._resources

    def setup(self):
        self._resources.setup()
        self._board.setup()

    def tick(self):
        self._mouse.tick()
        self._board.tick()

    def draw(self):
        self._board.draw(self._display)
        pygame.display.flip()

    def run(self):
        while not self._shutdown:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._shutdown = True
                    return

            self._display.fill(DISPLAY_COLOR)
            self._clock.tick(DISPLAY_TICK_DELAY)
            self.tick()
            self.draw()
            pygame.display.set_caption("%f" % self._clock.get_fps())

if __name__ == '__main__':
    game = Game()
    game.setup()
    game.run()
