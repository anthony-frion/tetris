'''
Hello, and thank you for paying attention to my work !

This file is a fully functional tetris game : all you have to do is execute
it and a pygame window will show up.

You can use the arrow keys to move your polygons and the spacebar to make them
turn. You can also use ESC to pause the game.

This implementation of the game does not have all the features that you could
find on online games, but it is quite simple and shows the potential of pygame.

The code is not very long and should be understandable, so don't hesitate to
try to make some changes ;)

Enjoy !

'''

#Imported modules

import pygame as pg
from pygame.locals import *

import copy as cp
import random as rd
import time as t

# Global variables
# These do not include the pygame objects, which are defined later.

interval = .5 # The base time interval between two steps of the game
speed_mult = 0.95 # The number by which the time interval is multiplied after a row is completed

block_size = 18 # The number of pixels that each block represents
horizontal_size = 14 # The number of blocks on each row of the grid
vertical_size = 20 # The vertical size of the grid

left_offset = 10 # The number of pixels between the left side of the window and the grid
background_color = (255, 255, 255) # The background color (here it's white)
label_color = (0, 0, 0) # The color of the text (here it's black)

nb_sprites = 7 # The number ofdifferent polygons in the game

id_to_struct = {} # The link between the id of the 7 polygons and their spatial structures
id_to_struct[0] = [[1, 0, 0], [1, 1, 1]]
id_to_struct[1] = [[0, 1, 0], [1, 1, 1]]
id_to_struct[2] = [[1], [1], [1], [1]]
id_to_struct[3] = [[1, 1, 0], [0, 1, 1]]
id_to_struct[4] = [[1, 1], [1, 1]]
id_to_struct[5] = [[0, 1, 1], [1, 1, 0]]
id_to_struct[6] = [[0, 0, 1], [1, 1, 1]]

score_mult = 10 # The additional score for each completed row

# Auxilary functions

def fst(couple) :
    a, b = couple
    return a

def snd(couple) :
    a, b = couple
    return b

# Gets the coordinate at which an image should be blit on a background to appear at its center
def middle_coord(background_screen, image) :
    x1, y1 = background_screen.get_rect().size
    x2, y2 = image.get_rect().size
    return (x1 - x2) // 2, (y1 - y2) // 2

# Blits an image at the center of a background
def put_in_middle(background_screen, image) :
    x1, y1 = background_screen.get_rect().size
    x2, y2 = image.get_rect().size
    background_screen.blit(image, ((x1 - x2) // 2, (y1 - y2) // 2))


# The polygons that we manipulate in the game
# Their id corresponds to a given structure accord to the id_to_struct dict
# They also have a position, indicating the top left corner of the squares they occupy
class polygon :
    
    def __init__(self, id, position) :
        self.orientation = 0
        self.id = id
        self.struct = id_to_struct[id]
        self.block = sprites[id]
        self.position = position
        
    def setOrientation(self, orientation) :
        self.orientation = orientation
        
    def setPosition(self, i, j) :
        self.position = (i, j)
    
    # This doesn't give the attribute 'struct' which only depends on the id 
    # but takes into account the orientation of the polygon
    def getStruct(self) :
        if self.orientation%4 == 0 :
            return self.struct
        elif self.orientation%4 == 1 :
            result = []
            for k in range(len(self.struct[0])) :
                result.append([self.struct[i][k] for i in range(len(self.struct)-1, -1, -1)])
            return result
        elif self.orientation%4 == 2 :
            copy_struct = self.struct.copy()
            for i in range(len(copy_struct)) :
                copy_struct[i] = [copy_struct[i][k] for k in range(len(copy_struct[i]) - 1, -1, -1)]
            copy_struct.reverse()
            return copy_struct
        elif self.orientation%4 == 3 :
            result = []
            for k in range(len(self.struct[0])) :
                result.append([self.struct[i][k] for i in range(len(self.struct))])
            result.reverse()
            return result
    
    def getPosition(self) :
        return self.position
    
    def getBarycentre(self) :
        return (len(self.getStruct()[0]) // 2, len(self.getStruct()) // 2)
    
    # Returns all the squares of the grid that are occupied by a polygon
    def getOccupiedSlots(self) :
        occupied = []
        (a, b) = self.getPosition()
        for j in range(len(self.getStruct())) :
            for i in range(len(self.getStruct()[0])) :
                if self.getStruct()[j][i] == 1 :
                    occupied.append((a+i, b+j))
        return occupied
    

# The grid in which polygons evolve
# It contains a window, which is a pygame object used to make the graphics,
# as well as a matrix, which is just a list of list that contains the status
# of each square of the grid
class grid :
    
    def __init__(self, horizontal_size, vertical_size, sprite_size, window) :
        self.horizontal_size = horizontal_size
        self.vertical_size = vertical_size
        self.sprite_size = sprite_size
        self.window = window
        self.matrix = [[42 for x in range(horizontal_size)] for y in range(vertical_size)]
        self.sprites = cp.deepcopy(self.matrix)
        
    def getElement(self, i, j) :
        return self.matrix[j][i]
    
    def setElement(self, i, j, val) :
        self.matrix[j][i] = val
    
    # Checks if the row number y of the matrix is full
    def row_full(self, y) :
        x = 0
        while x < self.horizontal_size and self.matrix[y][x] != 42 :
            x += 1
        if x == self.horizontal_size :
            return True
        else :
            return False
    
    # Returns the list of full rows of the grid
    def full_rows(self) :
        full = []
        for y in range(vertical_size) :
            if self.row_full(y) :
                full.append(y)
        return full
    
    # Removes all the full rows of the grid
    def erase_full_rows(self) :
        output = 0
        j = len(self.matrix) - 1
        while j >= 0 :
            if self.row_full(j) :
                self.matrix.pop(j)
                self.matrix.insert(0, [42 for i in range(len(self.matrix[0]))])
                output += 1
            else :
                j -= 1
        return output
    
    # Updates the graphical representation of a given square of the grid
    def update_sprite(self, i, j) :
        if self.matrix[j][i] < nb_sprites :
            window.blit(sprites[self.matrix[j][i]], (left_offset + block_size*i, block_size*j))
        else :
            window.blit(background, (left_offset + block_size*i, block_size*j), pg.Rect(left_offset + block_size*i, block_size*j, block_size, block_size))
        self.sprites[j][i] = self.matrix[j][i]

    # Updates the full window of graphics according to the attribute 'matrix'
    # If the argument is False then it will check if a square actually has 
    # to be updated before updating it, which saves time
    def update_window(self, total=False) :
        for y in range(self.vertical_size) :
            for x in range(self.horizontal_size) :
                if self.sprites[y][x] != self.matrix[y][x] or total :
                    if self.matrix[y][x] < nb_sprites :
                        self.window.blit(sprites[self.matrix[y][x]], (left_offset + block_size*x, block_size*y))
                    else :
                        self.window.blit(background, (left_offset + block_size*x, block_size*y), pg.Rect(left_offset + block_size*x, block_size*y, block_size, block_size))
                    self.sprites[y][x] = self.matrix[y][x]
        
    # Clears the matrix and its graphical representation
    def clear_grid(self) :
        self.matrix = [[42 for x in range(horizontal_size)] for y in range(vertical_size)]
        self.update_window()

# The class that centralizes all the features of the game
# It has two attribute polygons : the active one and the next one to be active
# It also have a grid (previous class) in his attributes, as well as an integer
# representing the score and a float number representing the interval between two steps of the game
class tetris() :
    
    def __init__(self, game_grid, active_polygon, next_polygon) :
        self.game_grid = game_grid
        self.active_polygon = active_polygon
        self.next_polygon = next_polygon
        self.score = 0
        self.time_interval = interval
    
    # Updates the graphics only around the active polygon (which saves a lot of computational power)
    def updateWindowOnActive(self) :
        pos = self.active_polygon.getPosition()
        struct = self.active_polygon.getStruct()
        for j in range(-1, len(struct)) :
            for i in range(len(struct[0])) :
                self.game_grid.update_sprite(fst(pos) + i, snd(pos) + j)
                
    # Detects potential collisions between a given polygon and the rest of the grid
    def collisionDetection(self, pos, struct) :
        if len(struct[0]) + snd(pos) >= len(self.game_grid.matrix) - 1 :
            return False
        for i in range(len(struct[-1])) :
            if struct[-1][i] == 1 and game_grid.getElement(i + fst(pos), len(struct) + snd(pos)) != 42 :
                return False
        return True
        
    # Makes the active polygon go down
    # Returns 42 if this implies a game over, 0 if the active block can't go
    # further down and 1 otherwise
    def active_polygon_down(self) :
        pos = self.active_polygon.getPosition()
        self.active_polygon.setPosition(fst(pos), snd(pos)+1)
        pos = self.active_polygon.getPosition()
        struct = self.active_polygon.getStruct()
        if len(struct) + snd(pos) - 1 >= len(self.game_grid.matrix) :
            if snd(pos) == 1 :
                return 42
            return 0
        for i in range(len(struct[-1])) :
            if struct[-1][i] == 1 and game_grid.getElement(i + fst(pos), len(struct) + snd(pos) - 1) != 42 :
                if snd(pos) == 1 :
                    return 42
                return 0
        for j in range(len(struct)-2, -1, -1) :
            for i in range(len(struct[j])) :
                if struct[j][i] == 1 : 
                    if self.game_grid.getElement(fst(pos)+i, snd(pos)+j) != 42 and struct[j+1][i] == 0 :
                        if snd(pos) == 1 :
                            return 42
                        return 0 
        for j in range(len(struct)-1, -1, -1) :
            for i in range(len(struct[j])) :
                if struct[j][i] == 1 : 
                    self.game_grid.setElement(fst(pos)+i, snd(pos)+j-1, 42)
                    if self.game_grid.getElement(fst(pos)+i, snd(pos)+j) == 42 :
                        self.game_grid.setElement(fst(pos)+i, snd(pos)+j, self.active_polygon.id)
                    else :
                        if snd(pos) == 1 :
                            return 42
                        return 0 
        for j in range(-1, len(struct)) :
            for i in range(len(struct[0])) :
                game_grid.update_sprite(fst(pos) + i, snd(pos) + j)
        return 1
    
    # Rotates the active polygon.
    # Includes a detection of collisions with other blocks and the boundaries of the grid
    def active_polygon_turn(self) :
        pos = self.active_polygon.getPosition()
        struct = self.active_polygon.getStruct()
        bar = self.active_polygon.getBarycentre()
        fict_block = polygon(self.active_polygon.id, pos)
        fict_block.setOrientation(self.active_polygon.orientation+1)
        fict_struct = fict_block.getStruct()
        fict_bar = fict_block.getBarycentre()
        fict_pos = (fst(pos) + fst(bar) - fst(fict_bar), snd(pos) + snd(bar) - snd(fict_bar))
        if len(fict_struct) + snd(fict_pos) <= len(self.game_grid.matrix) :
            if len(struct) + fst(fict_pos) > len(self.game_grid.matrix[0]) :
                fict_pos = (len(self.game_grid.matrix[0]) - len(struct), snd(fict_pos))
            elif fst(fict_pos) < 0 :
                fict_pos = (0, snd(fict_pos))
            test = True
            occupied = self.active_polygon.getOccupiedSlots()
            for j in range(len(fict_struct)) :
                for i in range(len(fict_struct[j])) :
                    if (fst(fict_pos)+i, snd(fict_pos)+j) in occupied :
                        quarante_deux = 42
                    else :
                        if self.game_grid.getElement(fst(fict_pos)+i, snd(fict_pos)+j) != 42 and fict_struct[j][i] == 1 :
                            test = False
            if test :
                for j in range(len(struct)) :
                    for i in range(len(struct[0])) :
                        if struct[j][i] == 1 :
                            self.game_grid.setElement(fst(pos)+i, snd(pos)+j, 42)
                            self.game_grid.update_sprite(fst(pos)+i, snd(pos)+j)
                self.active_polygon.orientation += 1
                self.active_polygon.position = fict_pos
                pos = self.active_polygon.position
                struct = self.active_polygon.getStruct()
                for j in range(len(struct)) :
                    for i in range(len(struct[j])) :
                        if struct[j][i] == 1 :
                            self.game_grid.setElement(fst(pos)+i, snd(pos)+j, self.active_polygon.id)
                self.updateWindowOnActive()
        
    # Makes the block translate to the right if the argument is 1
    # and to the left it is -1
    def active_polygon_translate(self, nb) :
        pos = self.active_polygon.getPosition()
        struct = self.active_polygon.getStruct()
        test = True
        for j in range(len(struct)) :
            for i in range(len(struct[j])) :
                if i+nb < len(struct[j]) and i+nb >= 0 and struct[j][i+nb] == 1 :
                    quarante_deux = 42
                elif i+nb+fst(pos) < 0 or i+nb+fst(pos) >= len(self.game_grid.matrix[0]) or self.game_grid.getElement(fst(pos)+i+nb, snd(pos)+j) != 42 and struct[j][i] == 1 :
                    test = False
        if test :
            for j in range(len(struct)) :
                for i in range(len(struct[0])) :
                    if struct[j][i] == 1 :
                            self.game_grid.setElement(fst(pos)+i, snd(pos)+j, 42)
                            self.game_grid.update_sprite(fst(pos)+i, snd(pos)+j)
            self.active_polygon.setPosition(fst(pos)+nb, snd(pos))
            for j in range(len(struct)) :
                for i in range(len(struct[j])) :
                    if struct[j][i] == 1 :
                        self.game_grid.setElement(fst(pos)+i+nb, snd(pos)+j, self.active_polygon.id)
            self.updateWindowOnActive()
            
    # Updates the right side of the window, which contains information on
    # the score, speed of the game and next block
    def update_right(self) :
        label_score = font.render("Score : {}".format(self.score), 1, label_color)
        label_speed = font.render("Speed : {}".format(round(1 / self.time_interval, 2)), 1, label_color)
        label_next = font.render("Next :", 1, label_color)
        self.game_grid.window.fill(background_color, pg.Rect(270, 0, 330, 400))
        self.game_grid.window.blit(label_score, (320, 50))
        self.game_grid.window.blit(label_speed, (320, 100))
        self.game_grid.window.blit(label_next, (320, 150))
        struct = self.next_polygon.getStruct()
        bar = self.next_polygon.getBarycentre()
        for j in range(len(struct)) :
            for i in range(len(struct[j])) :
                if struct[j][i] == 1 :
                    self.game_grid.window.blit(sprites[self.next_polygon.id], (340 - fst(bar) + i*block_size, 200 - fst(bar) + j*block_size))
        
    # Iterates the game by making the active polygon go down and performing
    # all the required updates afterwards
    def game_iter(self) :
        status = self.active_polygon_down()
        if status == 42 :
            print("GAME OVER")
        if status == 0 :
            self.active_polygon = self.next_polygon
            next_id = rd.randint(0, nb_sprites - 1)
            self.next_polygon = polygon(next_id, (horizontal_size // 2, 0))
            output = self.game_grid.erase_full_rows()
            if output >= 1 :
                self.game_grid.update_window()
                self.score += score_mult * output
                self.time_interval *= speed_mult **output
            self.update_right()
            
        return status

pg.init() #Initialisation of pygame
window = pg.display.set_mode((600, 380)) # Initialisation of the game window
window.fill(background_color) # Initialisation of the background
pg.display.set_caption('Tetris') # Setting of the window's name
game_grid = grid(horizontal_size, vertical_size, block_size, window) # Initialisation of the grid
background = pg.image.load("white_BG.jpg").convert() # Initialisation of the grid background
game_over_screen = pg.image.load("game-over.png").convert_alpha() # Initialisation of the game over screen
pause = pg.image.load("pause.png").convert_alpha() # Initialisation of the pause image
font = pg.font.SysFont("Comic Sans MS", 30) # Initialisation of the font for labels

pg.key.set_repeat(100, 40) # Setting the reaction to a key being hold

game_grid.window.blit(background, (0,0), Rect(0, 0, 200, 387))
game_grid.window.blit(background, (200,0), Rect(330, 0, 70, 387))

# Initialisation of the sprites of polygons
blocks = pg.image.load('Blocks.png').convert() 
sprites = [pg.Surface((block_size, block_size)) for k in range(nb_sprites)]
for k in range(nb_sprites) :
    sprites[k].blit(blocks, (0, 0), pg.Rect(18*k, 0, block_size, block_size))

# Initialisation of the active and next polygons
active_polygon = polygon(rd.randint(0, nb_sprites - 1), (horizontal_size // 2 - 1, 0))
next_polygon = polygon(rd.randint(0, nb_sprites - 1), (horizontal_size // 2 - 1, 0))

# Initialisation of the game
game = tetris(game_grid, active_polygon, next_polygon)
game.update_right()
t0 = t.time()
keep = True
keep_game = True
keep_game_over = False
keep_pause = False
while keep :
    window.fill(background_color)
    game_grid.window.blit(background, (0,0), Rect(0, 0, 200, 387))
    game_grid.window.blit(background, (200,0), Rect(330, 0, 70, 387))
    game_grid.update_window(True)
    game.update_right()
    if keep_game :
        pg.time.Clock().tick(30)     
        for event in pg.event.get() : # Commands of the game
            if event.type == KEYDOWN and event.key == K_ESCAPE :
                window.fill(background_color)
                put_in_middle(game.game_grid.window, pause)
                keep_game = False
                keep_pause = True
            if event.type == KEYDOWN and event.key == K_SPACE :
                game.active_polygon_turn()
            if event.type == KEYDOWN and event.key == K_LEFT :
                game.active_polygon_translate(-1)
            if event.type == KEYDOWN and event.key == K_RIGHT :
                game.active_polygon_translate(1)
            if event.type == KEYDOWN and event.key == K_DOWN :
                game.game_iter()
            pg.display.flip()
        if t.time() - t0 > game.time_interval : # The game gets iterated after its attribute time has passed
            status = game.game_iter()
            if status == 42 :
                keep_game = False
                put_in_middle(game.game_grid.window, game_over_screen)
                label = font.render("Score : {}".format(game.score), 1, label_color)
                x, y = middle_coord(game.game_grid.window, label)
                game.game_grid.window.blit(label, (x, y+50))
                label2 = font.render("Press space to play again :)", 1, label_color)
                x, y = middle_coord(game.game_grid.window, label2)
                game.game_grid.window.blit(label2, (x, y+80))
                label3 = font.render("Press Escape to exit the game", 1, label_color)
                x, y = middle_coord(game.game_grid.window, label3)
                game.game_grid.window.blit(label3, (x, y+120))
                keep_game_over = True
            t0 = t.time()
        pg.display.flip()
    elif keep_game_over :
        pg.time.Clock().tick(30)     
        for event in pg.event.get() :
            if event.type == KEYDOWN and event.key == K_SPACE : # Restart the game
                game.game_grid.clear_grid()
                active_polygon = polygon(rd.randint(0, nb_sprites - 1), (horizontal_size // 2, 0))
                next_polygon = polygon(rd.randint(0, nb_sprites - 1), (horizontal_size // 2, 0))
                game = tetris(game_grid, active_polygon, next_polygon)
                keep_game_over = False
                keep_game = True
            if event.type == KEYDOWN and event.key == K_ESCAPE :
                keep_game_over = False
                keep = False
    elif keep_pause :
        pg.time.Clock().tick(30)     
        window.fill(background_color)
        put_in_middle(game.game_grid.window, pause)
        pg.display.flip()
        for event in pg.event.get() :
            if event.type == KEYDOWN and event.key == K_ESCAPE :
                keep_pause = False
                keep_game = True
        
pg.quit()
    













