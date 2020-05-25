# Name: Pacman
# Creator: Maia Goldberg
# Date created: April.6/20
# Last modified: May.17/20
import pygame
import random
import math
# will make it easier to use pygame functions
from pygame.draw import line, circle, rect

# initializes the pygame module
pygame.init()
# creates a screen variable of the tile width/length * the number of rows/cols
screen = pygame.display.set_mode([552, 600])

# sets the frame rate of the program
clock = pygame.time.Clock()

# Constant colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# tuples of how the x/y coordinates will be changed to move one tile in that direction
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
STOP = (0, 0)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)
# used for  accessing the correct image
DIRECTIONS_STR = {UP: "up", DOWN: "down", LEFT: "left", RIGHT: "right"}
# Used when changing states
REVERSED_DIRECTIONS = {UP: DOWN, DOWN: UP, RIGHT: LEFT, LEFT: RIGHT, STOP: STOP}

# States
SCATTER = 0
CHASE = 1
SCARED = 2
EATEN = 3


def load_img(sprite_file):
    # loads in images and stores them in a dictionary correlating them to their direction
    sprites = {}
    for direction, value in DIRECTIONS_STR.items():  # value = the string of the direction
        img = pygame.image.load(sprite_file + "_" + value + ".png").convert_alpha()
        sprites[direction] = pygame.transform.scale(img, (Game.tile_size, Game.tile_size))
    sprites[STOP] = sprites[RIGHT]  # if the sprite is stopped it will use the image for when it's facing right
    return sprites


def load_sound(sound_file):  # imports sound files
    sound = pygame.mixer.Sound(sound_file + ".wav")
    return sound


def display_text(message, position):  # renders text and prints it on the screen
    text_display = Game.font.render(message, 10, WHITE)
    screen.blit(text_display, position)


class PacDot:
    POINTS = 10
    RADIUS = 2


class Energizer:
    POINTS = 50
    RADIUS = 4


class Cherry:
    def __init__(self, game):
        self.game = game
        self.generate_random_pos()
        self.points = 200

        # loads the image for cherry
        self.cherryLoad = pygame.image.load("cherry.png").convert_alpha()
        self.cherry_sprite = pygame.transform.scale(self.cherryLoad, (self.game.tile_size, self.game.tile_size))

    def draw(self):  # blits the sprite to the screen
        screen.blit(self.cherry_sprite, (self.x * self.game.tile_size, self.y * self.game.tile_size))

    def generate_random_pos(self):
        # generates a random x/y co-ordinate
        self.x = random.randint(0, 22)
        self.y = random.randint(0, 24)


class Game:
    # dictionary to hold information correlating character on map to type of edible
    edibles = {"*": PacDot, "@": Energizer}
    tile_size = 24
    start_noise = load_sound("start")
    font = pygame.font.SysFont('rockwell', 18)  # font used for on-screen text

    def __init__(self):
        self.done = False
        self.score = 0
        self.ticks = 0  # will be used to slow movement by only moving character after a certain amount of ticks
        self.level = 1
        # number of seconds in timed state multiplied by frames per second
        self.time_in_state = {SCATTER: 7 * 60, CHASE: 20 * 60, SCARED: 10 * 60}

        # instantiation of the character and passes them game
        self.pac = Pacman(self)
        self.blinky = Blinky(self)
        self.pinky = Pinky(self)
        self.inky = Inky(self)
        self.clyde = Clyde(self)

        self.charList = [self.blinky, self.pinky, self.inky, self.clyde, self.pac]
        # pac goes at the end of the list so all ghosts move before him

        self.cherry = Cherry(self)  # instantiation of the cherry
        self.caught_cherry = False  # will be used to ensure the cherry is only touched once
        self.display_start_screen = True
        self.play_start_noise = True

        self.maze = Maze()  # instantiation of the map
        self.maze.load_map()

    def draw_game(self):
        ts = self.tile_size

        # counter variables which will increase as it moves across the rows/columns
        y = 0
        for r in self.maze.tiles:
            x = 0
            for c in r:
                if c == "#":  # if there is a wall draw a rectangle
                    rect(screen, BLUE, (x * ts, y * ts, ts, ts), 0)
                else:
                    edible = self.edibles.get(c)  # checks if c(the symbol on the map) is in the edibles dictionary
                    if edible is not None:  # as long as it is(not none) will draw a circle
                        circle(screen, WHITE,
                               ((x * ts) + ts // 2,
                                (y * ts) + ts // 2,), edible.RADIUS, 0)
                x += 1
            y += 1

        # the cherry is only displayed if the score is higher than seven hundred
        # self.caught_cherry is used to ensure pacman can only touch the cherry once
        if self.score > 700 and not self.caught_cherry:
            if self.maze.tiles[self.cherry.y][self.cherry.x] != "_":
                # checks that if the space isn't empty a new position is generated
                self.cherry.generate_random_pos()
            else:
                self.cherry.draw()

    def play(self):
        self.done = False
        while not self.done:
            # makes the background the colour WHITE
            screen.fill(BLACK)
            self.pac.set_key()  # pre store user actions
            self.draw_game()
            self.game_text()

            # moves/draws the characters
            if self.display_start_screen:
                self.start_screen()
            else:
                for character in self.charList:
                    character.choose_state()
                    if (self.ticks % character.move_rate) == 0:
                        # used to slow down movement by only moving a character every 8(move_rate) ticks
                        character.move()
                    self.pac.check_intersect()
                    character.draw()

            if self.pac.lives < 1:
                # exits the loop since game has ended, that way when loop restarts a new game will be created
                return

            if self.maze.num_edibles == 0:  # if there are no more dots to be eaten on the screen
                self.level_up()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # when the ex button is pressed
                    self.end()

                # this line draws everything into the window all at once
            pygame.display.flip()
            # this line limits the frames per second to 60
            clock.tick(60)
            self.ticks += 1

    def end(self):
        # exits the program
        self.done = True
        pygame.quit()
        return True

    def reset_pos(self):
        # resets the characters to their original positions without resetting the whole game(score, lives, etc.)
        for character in self.charList:
            character.set_start_pos()

    def game_text(self):
        # draws text that will constantly displayed on the screen
        display_text("score: " + str(self.score), (1, 1))
        display_text("lives: " + str(self.pac.lives), (390, 1))
        display_text("level: " + str(self.level), (250, 1))

    def start_screen(self):
        # will display start text and play start noises
        display_text("READY!", (10.25 * self.tile_size, 11 * self.tile_size))
        if self.play_start_noise:  # ensures that the noise is only played once
            self.start_noise.play()
            self.play_start_noise = False
        if self.ticks > 4 * 60:  # keeps the text being displayed for 4 seconds
            self.display_start_screen = False

    def level_up(self):
        #  reloads the map and resets the characters to there original positions
        self.level += 1
        self.reset_pos()
        self.maze.tiles.clear()
        self.maze.load_map()
        self.maze.num_edibles = 212
        self.caught_cherry = False
        for character in self.charList:
            character.state = SCATTER

        # changes the amount of time spent in scatter depending on the level
        if 2 <= self.level <= 5:
            self.time_in_state[SCATTER] = 3
        elif self.level > 5:
            self.time_in_state[SCATTER] = 1


class Maze:
    MAP = """\
#######################
#**********#**********#
#@###*####*#*####*###@#
#*###*####*#*####*###*#
#*********************#
#*###*#*#######*#*###*#
#*****#*#######*#*****#
#####*#****#****#*#####
#####*#### # ####*#####
#####*#*********#*#####
#####*#_###G###_#*#####
_____*__#GGGGG#__*______
#####*#_#######_#*#####
#####*#*********#*#####
#####*#_#######_#*#####
#####*#_#######_#*#####
#**********#**********#
#*###*####*#*####*###*#
#@**#******_******#**@#
###*#*#*#######*#*#*###
#*****#****#****#*****#
#*########*#*########*#
#*########*#*########*#
#*********************#
#######################"""

    def __init__(self):
        self.width = 23
        self.height = 25
        self.tiles = []
        self.num_edibles = 212

    def load_map(self):
        # will break the string into a new list at every line break
        # will then break each character the row list into it's own item in the list
        # and adds the broken string to list tiles
        for r in self.MAP.split("\n"):
            self.tiles.append(list(r))

    def is_tile_wall(self, r, c):
        # checks if the given spot in the grid is a wall and return true or false
        return self.tiles[r][c] == "#"


class Character:
    def __init__(self, game):
        self.game = game
        self.direction = STOP
        self.change_state_time = 7 * 60
        self.set_start_pos()  # sets the position in the grid
        self.set_state(SCATTER)

    def move(self):
        self.direction = self.choose_direction()
        # stores the proposed movement ie. -1 in x is left
        move_x = self.direction[0]
        move_y = self.direction[1]

        # lets the characters loop around the screen
        new_x = (self.x + move_x) % self.game.maze.width
        if new_x < 0:
            new_x = self.game.maze.width
        new_y = (self.y + move_y) % self.game.maze.height
        if new_y < 0:
            new_y = self.game.maze.height

        # if the proposed position is not in a wall, the character is moved there
        if not self.game.maze.is_tile_wall(new_y, new_x):
            self.y, self.x = new_y, new_x
        else:
            # the character is stopped
            self.direction = STOP

    def draw(self):
        # changes which dictionary of pictures to look at depending on the state
        if self.state == SCARED:
            img = self.scared_sprites[self.direction]
        elif self.state == EATEN:
            img = self.eaten_sprites[self.direction]
        else:
            img = self.sprites[self.direction]

        # to make the sprite's movement smooth, the sprite is draw multiple incremanting the location it is drawn at
        # times the number of ticks between movement times it's direction
        # runs the moving forward animation if the next tile is not a wall
        animation_increment = self.game.ticks % self.move_rate
        if not self.game.maze.is_tile_wall(self.y + self.direction[1], self.x + self.direction[0]):
            screen.blit(img,
                        ((self.x * self.game.tile_size) + 3 * animation_increment * self.direction[0],
                         (self.y * self.game.tile_size) + 3 * animation_increment * self.direction[1]))
        else:
            # if it is then the sprite is just draw regularly
            screen.blit(img,
                        ((self.x * self.game.tile_size),
                         (self.y * self.game.tile_size)))

    def choose_state(self):
        # decides when to change states either by timer or location of the ghosts
        next_states = {SCATTER: CHASE, CHASE: SCATTER, SCARED: CHASE}

        if self.state in self.game.time_in_state:  # states that are timed:
            # if the timer has expired then switch to the next state
            if self.game.ticks >= self.change_state_time:
                self.set_state(next_states[self.state])

        elif self.state == EATEN:
            if self.game.maze.tiles[self.y][self.x] == "G":  # if they are in the ghost house
                self.set_state(SCATTER)

    def set_state(self, new_state):
        # changes the current state to the new state
        self.state = new_state
        if self.state in self.game.time_in_state:  # states that are timed:
            # sets the next time to change states
            self.change_state_time = self.game.ticks + self.game.time_in_state[self.state]
        if self.state == SCARED:
            self.game.pac.num_ghosts_eaten = 0


class Pacman(Character):
    sprites = load_img("pac")
    # since pac and the ghosts use the same states
    # but ghosts require different images depending on their states pac also requires other image dictionaries
    # so pac just gets three identical dictionaries since he always remains the same
    scared_sprites = sprites
    eaten_sprites = sprites

    move_rate = 8

    # loads in all of Pacman's noises
    chomp = load_sound("chomp")
    death_noise = load_sound("death")
    ghost_eat_noise = load_sound("eatghost")
    fruit_eat_noise = load_sound("eatfruit")

    def __init__(self, game):
        Character.__init__(self, game)
        self.key = None
        self.lives = 3
        self.has_intersected_ghost = False
        self.num_ghosts_eaten = 0

    def set_start_pos(self):
        # starting position of pacman
        self.x = 11
        self.y = 18

    def set_key(self):
        self.key = pygame.key.get_pressed()

    def choose_direction(self):
        # changes the direction based on the key that was pressed

        direction = self.direction
        if self.key[pygame.K_UP]:
            direction = UP
        elif self.key[pygame.K_DOWN]:
            direction = DOWN
        elif self.key[pygame.K_LEFT]:
            direction = LEFT
        elif self.key[pygame.K_RIGHT]:
            direction = RIGHT

        return direction

    def check_intersect(self):
        # checks if Pacman is in the same grid spot as an edible
        edible = self.game.edibles.get(self.game.maze.tiles[self.y][self.x])
        if edible is not None:
            if self.game.maze.tiles[self.y][self.x] == "@":  # if the edible is an energizer then change the state
                for character in self.game.charList:
                    character.set_state(SCARED)
            # then adds to points plays noises accordingly
            self.chomp.play()
            self.game.score += edible.POINTS
            self.game.maze.tiles[self.y][self.x] = "_"  # removes the edible from the screen
            self.game.maze.num_edibles -= 1

        # checks if Pacman is in the same grid spot as a cherry and it hasn't been caught yet
        if self.y == self.game.cherry.y and self.x == self.game.cherry.x and not self.game.caught_cherry:
            self.game.caught_cherry = True
            self.game.score += 200
            self.fruit_eat_noise.play()

        self.check_ghost_intersect()

    def check_ghost_intersect(self):
        self.has_intersected_ghost = False

        # checks if pac intersects with any character other than itself
        for character in self.game.charList:
            if character == self:
                continue
            if self.y == character.y and self.x == character.x and not self.has_intersected_ghost:
                self.has_intersected_ghost = True
                if character.state == SCARED:  # when he can eat ghosts
                    # double the number of points are given each time a ghost is eaten
                    self.num_ghosts_eaten += 1
                    self.game.score += 100 * (2 ** self.num_ghosts_eaten)
                    self.ghost_eat_noise.play()
                    character.set_state(EATEN)
                elif character.state == SCATTER or character.state == CHASE:  # when he cannot eat ghosts
                    character.direction = STOP  # stops the characters from moving
                    self.death_noise.play()
                    self.lives -= 1
                    self.game.reset_pos()
                    pygame.time.wait(2000)  # gives the player 2 seconds of break before the game starts again


class Ghost(Character):
    move_rate = 10
    scared_sprites = load_img("scared")
    eaten_sprites = load_img("eyes")

    def __init__(self, game):
        Character.__init__(self, game)
        self.game = game

    def choose_direction(self):
        self.set_target()

        lowest_dist = 10000000
        best_direction = STOP
        for direction in DIRECTIONS:
            if direction == REVERSED_DIRECTIONS[self.direction]:  # prevents ghosts from moving backwards
                continue
            x, y = self.x + direction[0], self.y + direction[1]
            if self.game.maze.is_tile_wall(y, x):  # prevents ghosts from moving into a wall
                continue
            else:
                # calls distance for all tiles which the ghost can move into from it's current position
                dist = self.distance(x, y)
                if dist < lowest_dist:
                    lowest_dist = dist
                    best_direction = direction
        # returns the direction with the shortest distance to it's target
        return best_direction

    def distance(self, x, y):
        # calculates the distance of a given position to the ghosts target
        dist = math.pow(self.targetY - y, 2) + math.pow(self.targetX - x, 2)
        return dist

    def set_target(self):
        decided = True
        if self.game.maze.tiles[self.y][self.x] == "G":
            # if the ghosts are in the ghost houses sets the position directly above such that they are forced to exit
            self.targetX = 11
            self.targetY = 4
        elif self.state == EATEN:
            # sends them to the ghost house
            self.targetX = 11
            self.targetY = 11
        elif self.state == SCARED:
            # makes them move in random directions
            self.targetX = random.randint(0, 22)
            self.targetY = random.randint(0, 24)
        else:
            decided = False
        return decided  # ensures that ghosts always have a target


class Blinky(Ghost):
    sprites = load_img("blinky")

    def __init__(self, game):
        Ghost.__init__(self, game)
        self.direction = UP

    def set_start_pos(self):
        # starting position on the map
        self.x = 11
        self.y = 10

    def set_target(self):
        if Ghost.set_target(self):
            return True
        decided = True
        if self.state == SCATTER:
            # if the state is scatter it will set the target to be it's corner on the map
            self.targetX = 24
            self.targetY = 1
        elif self.state == CHASE:
            # targets Pacman directly
            self.targetX = self.game.pac.x
            self.targetY = self.game.pac.y
        else:
            decided = False
        return decided  # ensures that ghosts always have a target


class Pinky(Ghost):
    sprites = load_img("pinky")

    def __init__(self, game):
        Ghost.__init__(self, game)

    def set_start_pos(self):
        # starting position on the map
        self.x = 11
        self.y = 11

    def set_target(self):
        if Ghost.set_target(self):
            return True
        decided = True
        if self.state == SCATTER:
            # if the state is scatter it will set the target to be it's corner on the map
            self.targetX = 1
            self.targetY = 1
        elif self.state == CHASE:
            #  targets 4 tiles ahead of Pacman in the direction he is traveling
            self.targetX = self.game.pac.x + 4 * self.game.pac.direction[0]
            self.targetY = self.game.pac.y + 4 * self.game.pac.direction[1]
        else:
            decided = False
        return decided  # ensures that ghosts always have a target


class Inky(Ghost):
    sprites = load_img("inky")

    def __init__(self, game):
        Ghost.__init__(self, game)

    def set_start_pos(self):
        # starting position on the map
        self.x = 10
        self.y = 11

    def set_target(self):
        if Ghost.set_target(self):
            return True
        decided = True
        if self.state == SCATTER:
            # if the state is scatter it will set the target to be it's corner on the map
            self.targetX = 24
            self.targetY = 22
        elif self.state == CHASE:
            # looks two tiles ahead of pacman and creates a vector from blinky
            vectorX = self.game.blinky.x - (self.game.pac.x + 2 * self.game.pac.direction[0])
            vectorY = self.game.blinky.y - (self.game.pac.y + 2 * self.game.pac.direction[1])
            # to that position then he doubles the length of that vector and targets that tile
            self.targetX = self.game.blinky.x + 2 * vectorX
            self.targetY = self.game.blinky.y + 2 * vectorY
        else:
            decided = False
        return decided  # ensures that ghosts always have a target


class Clyde(Ghost):
    sprites = load_img("clyde")

    def __init__(self, game):
        Ghost.__init__(self, game)

    def set_start_pos(self):
        # starting position on the map
        self.x = 12
        self.y = 11

    def set_target(self):
        if Ghost.set_target(self):
            return True
        decided = True
        if self.state == SCATTER:
            # if the state is scatter it will set the target to be it's corner on the map
            self.targetX = 1
            self.targetY = 22
        elif self.state == CHASE:
            # targets Pacman directly
            # but if he is within a distance of 8 from Pacman then he goes back to his scatter position
            self.targetX = self.game.pac.x
            self.targetY = self.game.pac.y
            if self.distance(self.x, self.y) < 64:
                self.targetX = 1
                self.targetY = 22
        else:
            decided = False
        return decided  # ensures that ghosts always have a target


while True:
    g = Game()
    g.play()
