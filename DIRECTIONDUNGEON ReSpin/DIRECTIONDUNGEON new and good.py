################################################################################
###                            DIRECTIONDUNGEON!                             ###
################################################################################

### LIST OF THINGS TO DO ###
# shadow looks a bit confusing?  make the levels below darker?
# fix goal clipping through player

# levels
# (probably 64, since it's 4 cubed, and because of 4 button menu)

# main menu, and that sick level select i thought of
# pause function...?

# sounds, ambient and raindrop-py
# music should be minimal and only at the start/end
# if not, though, outsource music to mustardflu?


### RANDOM IDEAS ###
# should the void cover the bottom tile halfway? to hint at a wall being there?
# different perspectives for each dungeon?
# keys/locks?
# pushable blocks?


################################################################################
###                    STUFF THAT IS ONLY LOADED ONCE                        ###
################################################################################

import os
import sys

import math
import random

import copy

import pygame



##################################
### CONSTANTS AND WINDOW SETUP ###
##################################

### GRAPHICAL CONSTANTS ###
# INITIAL WINDOW SETUP
os.environ['SDL_VIDEO_CENTERED'] = '1'           # centers window

pygame.init()
pygame.display.set_caption('DIRECTIONDUNGEON!')  # gives window a title

# PIXEL SIZE CONSTANTS
mult = 8            # pixel multiplier

TILE = 4 * mult     # size in pixels of a tile
SIDE = 2 * mult     # size in pixels of the side of a tile
MARG = 2 * mult     # size in pixels of the margin between dungeons

WIDTH  = 5          # width  in tiles of a dungeon
HEIGHT = 5          # height in tiles of a dungeon
DUNGW = TILE*WIDTH  # width  in pixels of a dungeon
DUNGH = TILE*HEIGHT # height in pixels of a dungeon

# AFTERWARDS WINDOW SETUP
# the size of the screen, based on how things are laid out
SCREENLENGTH = DUNGH*3 + MARG*4
SCREENSIZE = (SCREENLENGTH, SCREENLENGTH)

# initializes the display so that sprites can be loaded
postDisplay = pygame.display.set_mode(SCREENSIZE)



### GAMEPLAY CONSTANTS ###
# DIRECTION
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

# TILE TYPES
VOID = 0
EMPTY = 1
WALL = 2
WALLSIDE = 3 # only used in tilesheets, not used in level generation
GOAL = 4
SWIRL = 5

# DEFAULT DUNGEON POSITIONS
dungX = [MARG, DUNGW + MARG*2, DUNGW*2 + MARG*3, DUNGW + MARG*2]
dungY = [DUNGH + MARG*2, MARG, DUNGH + MARG*2, DUNGH*2 + MARG*3]



###############
### SPRITES ###
###############

### LOADS SPRITES ###
def loadSprite(path, mult):
    sprite = pygame.image.load(path) # load sprite

    w = sprite.get_width()           # resize sprite
    h = sprite.get_height()
    sprite = pygame.transform.scale(sprite, (w * mult, h * mult))

    sprite.convert()                 # convert sprite

    sprite.set_colorkey((0, 255, 0)) # transparentize sprite

    return sprite


### TILESHEETS ###
# VAR does not mean VARIABLE, it means VARIATIONS
class Tilesheet:
    def __init__(self, path, mult, varCount):
        self.surface = loadSprite(path, mult)

        # a tuple that stores the amount of variations for each tileType
        self.varCount = varCount


    # draws a tile based on its tileType and variant
    def drawTile(self, surf, pos, tile, variant):
        if tile == WALLSIDE:
            height = SIDE
        else:
            height = TILE

        # cuts out the tile from the tilesheet and draws it
        tileRect = ((tile - 1)*TILE, variant*TILE, TILE, height)
        surf.blit(self.surface, pos, tileRect)

# a test tilesheet.  multiple can be made
TESTSHEET = Tilesheet("images\\testSheet.png", mult, (0, 2, 2, 2, 0, 0))



##################
### ANIMATIONS ###
##################

animQueue = []   # a queue that plays animations in order

### THE ANIMATION CLASS ###
# THERE ARE DIFFERENT TYPES OF ANIMATIONS
SPRITE     = 1 # based off of sprites rather than values
COUNTER    = 2 # counts by ones
LINEAR     = 3 # counts by a certain value
QUADRATIC  = 4 # counts by a changing value (slow then speeds up)
RQUADRATIC = 5 # counts by a changing value, reversed (fast then slows down)

class Animation:

    # I USE "args" BECAUSE SPRITE AND VALUE ANIMS TAKE DIFFERENT ARGUMENTS
    def __init__ (self, lastFrame, kind, arg0 = None, arg1 = None,
                                         arg2 = None, arg3 = None, arg4 = ()):
        #      kind: I couldn't use "type" because Python
        #     frame: counts up the frame number of the animation
        # lastFrame: the last frame number of the animation
        #     value: stores the value of the animation
        # peakValue: the highest/lowest point the value will reach
        #      tied: references any animations that play at the same time
        self.kind = kind

        self.frame = 0
        self.lastFrame = lastFrame


        ### SPRITE-BASED ANIMATION ###
        if kind == SPRITE:
            # DEFINE WHAT THE ARGUMENTS MEAN
            filePath  = arg0
            width     = arg1
            height    = arg2
            mult      = arg3
            self.tied = arg4

            # WIDTH AND HEIGHT USED TO "CUT OUT" CERTAIN FRAMES
            self.width = width * mult
            self.height = height * mult

            # STORES EVERY FRAME ON A SINGLE SURFACE
            self.surface = loadSprite(filePath, mult)


        ### VALUE-BASED ANIMATION ###
        else:
            # DEFINE WHAT THE ARGUMENTS MEAN
            peakValue = arg0
            if arg1:  # only defines tied animations when arg1 exists
                self.tied = arg1
            else:
                self.tied = ()

            # CREATES COUNTERS BASED ON THE TYPE OF ANIMATION
            if kind == LINEAR:
                self.lastValue = peakValue
                self.value = 0
                self.DIFF = peakValue / lastFrame

            elif kind == QUADRATIC or kind == RQUADRATIC:
                # wow look math, wow look parabolas
                h = lastFrame
                k = peakValue
                a = k / h**2
                self.value = 0
                self.DIFF2 = a * 2

                if kind == QUADRATIC:
                    self.lastValue = peakValue
                    self.diff1 = a

                elif kind == RQUADRATIC:
                    # goes through the parabola and records the pre-vertex value
                    # it's inefficient but I spent forever trying something else
                    diff1 = a

                    for x in range (lastFrame - 1):
                        diff1 += self.DIFF2

                    self.firstDiff1 = diff1
                    self.diff1 = diff1


    ### FUNCTIONS ###
    # DRAWS A SPECIFIC FRAME, BY CUTTING IT OUT FROM THE SURFACE (sprite only)
    def blitFrame(self, dest, position, frameNum = -1):
        if frameNum == -1:
            frameNum = self.frame

        frameRect = (0, self.height * frameNum, self.width, self.height)
        dest.blit(self.surface, position, frameRect)


    # ADVANCES THE FRAME
    def nextFrame(self):
        self.frame += 1

        if self.kind == LINEAR:
            self.value += self.DIFF

        elif self.kind == QUADRATIC:
            self.value += self.diff1
            self.diff1 += self.DIFF2

        elif self.kind == RQUADRATIC:
            self.value += self.diff1
            self.diff1 -= self.DIFF2

        # also advances each tied animation
        for anim in self.tied:
            anim.nextFrame()


    # RESETS ANIMATION BACK TO FRAME 0
    def resetAnim(self):
        self.frame = 0

        # self.value doesn't exist on SPRITES
        if self.kind != SPRITE:
            self.value = 0

        if self.kind == QUADRATIC:
            self.diff1 = self.DIFF2 / 2

        elif self.kind == RQUADRATIC:
            self.diff1 = self.firstDiff1

        # also resets all tied animations
        for anim in self.tied:
            anim.resetAnim()


### PLAYER ANIMATIONS ###
# creates and loads all the ghost/player animations from file
directionStrings = ["Left", "Up", "Right", "Down"]
playMovement = []
ghostMovement = []
for direction in directionStrings:
    path =  "images\\play" + direction + ".png"

    # creates ghost animation, equal to the player animation except transparent
    tempGhostAnim = Animation(6, SPRITE, path, 12, 14, mult)
    tempGhostAnim.surface.set_alpha(100)
    ghostMovement.append(tempGhostAnim)

    # the ghost animation is then tied to the player animation
    tempPlayAnim = Animation(6, SPRITE, path, 12, 14, mult, [tempGhostAnim])
    playMovement.append(tempPlayAnim)

# idle doesn't have to be animation, but it just makes things easier
playIdle = Animation(0, SPRITE, "images\\playIdle.png",  12, 14, mult)
ghostIdle = Animation(0, SPRITE, "images\\playIdle.png",  12, 14, mult)
ghostIdle.surface.set_alpha(100)
playAnim = playIdle
ghostAnim = ghostIdle


### LEVEL ANIMATIONS ###
animRotate = Animation(18, QUADRATIC, 90)
ROTATERADIUS = DUNGW + MARG
ROTATEMIDX = DUNGW + MARG*3
ROTATEMIDY = DUNGH + MARG*2

animPlayDrop = Animation(8, LINEAR, SIDE)

# these two animations are "tied" together and will play at the same time
animNexLvlUp = Animation(34, RQUADRATIC, -SIDE)
animCurLvlUp = Animation(34, QUADRATIC, -SCREENLENGTH, [animNexLvlUp])

LEVELSDOWN = 10  # how many levels below current level to show
SHADOWINTERVAL = 255 / (LEVELSDOWN - 1)
NEXTSHADOWINTERVAL = SHADOWINTERVAL / animNexLvlUp.lastFrame



### MISC GRAPHICAL STUFF ###
# CREATES A NEW LAYER, WITH COLORKEY TRANSPARENCY
def newSurf(dimensions):
    layer = pygame.Surface(dimensions)
    layer.set_colorkey((0, 255, 0))
    layer.fill((0, 255, 0))
    return layer


# SURFACE WHERE EACH DUNGEON IS DRAWN TO
curDungs = newSurf((DUNGW * 4, DUNGH + SIDE))
dungRects = []  # used to cut out each dungeon from curDungs
for dung in range(4):
    dungRects.append((dung * DUNGW, 0, DUNGW, DUNGH + SIDE))


# BLITS DUNGEON SIDES FROM SIDESURFS
def blitSide(surf, dung, x, y):
    segment = (dung * DUNGW, sideY + SIDE*2, DUNGW, SIDE * LEVELSDOWN)
    surf.blit(sideSurfs, (x, y), segment)


# CAMERA
camX = 0
camY = 0
CAMLIMIT = mult * 2
CAMMAXFRAME = 60



##############
### LEVELS ###
##############

### LEVEL CLASS ###
class Level:
    def __init__(self, layout, tileSheet):
        # origLayout: when resetting the level, revert to this.  don't modify
        #     layout: stores the layout of the level.  modify if you want
        #  tileSheet: stores which tilesheet the level is using
        #   tileVars: stores which sprite variant each tile uses
        self.origLayout = layout
        self.layout = layout
        self.tileSheet = tileSheet

        tileVars = [[[0, 0, 0, 0, 0] for x in range(WIDTH)] for x in range(4)]

        for dung in range(4):
            for col in range(WIDTH):
                for row in range(HEIGHT):
                    tile = self.tileAt(dung, col, row)
                    variant = random.randint(0, tileSheet.varCount[tile])
                    tileVars[dung][col][row] = variant

        self.tileVars = tileVars


    ### RETURNS THE TILE AT A SPECIFIC LOCATION ###
    def tileAt(self, dung, x, y):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            return self.layout[dung][x][y]

        # out of bounds tiles
        else:
            return VOID


    ### DRAWS A TILE FROM THE LEVEL ###
    def drawTile(self, surf, dung, col, row, x = None, y = None):
        # if no position arguments are given, use the default position
        if x == None and y == None:
            pos = (dungX[dung] + col * TILE, dungY[dung] + row * TILE)
        else:
            pos = (x, y)

        # pulls some variables from self
        tile      = self.tileAt(dung, col, row)
        tileSheet = self.tileSheet
        variant   = self.tileVars[dung][col][row]

        # wall tiles consist of two potential parts, and are drawn higher
        if tile == WALL:
            tileSheet.drawTile(surf, pos, WALL, variant)

            # draws side if tile below is not also a wall
            if self.tileAt(dung, col, row + 1) != WALL:
                pos = (pos[0], pos[1] + TILE)
                tileSheet.drawTile(surf, pos, WALLSIDE, variant)

        # all other tiles only consist of one part, and are drawn lower
        elif tile != VOID:
            pos = (pos[0], pos[1] + SIDE)
            tileSheet.drawTile(surf, pos, tile, variant)


    ### DRAWS AN ENTIRE DUNGEON ###
    def drawDung(self, surf, dung, posX = None, posY = None):
        # basically just loops through and draws each tile
        for col in range(WIDTH):
            for row in range(HEIGHT):

                # if no position arguments are given, use the default position
                if posX == None and posY == None:
                    x = dungX[dung] + col*TILE
                    y = dungY[dung] + row*TILE
                else:
                    x = posX + col*TILE
                    y = posY + row*TILE

                self.drawTile(surf, dung, col, row, x, y)



### LOADS THE LEVELS FROM FILE ###
# the level file uses singular letters to represent tiles
V = VOID
E = EMPTY
W = WALL
G = GOAL
S = SWIRL

# READ FILE
levels = []
levelFile = open("levels.txt", "r")
levelFile = levelFile.read().split()

# REMOVES THE LEVEL DESCRIPTIONS (level00, level01, level02 and so on)
for x in reversed(range(0, len(levelFile), WIDTH * HEIGHT * 4 + 2)):
    levelFile.pop(x)

# CONVERTS ALL THE STRINGS TO THEIR RESPECTIVE CONSTANTS
for x in range(len(levelFile)):
    levelFile[x] = eval(levelFile[x])

while levelFile:   # stops loading once there is nothing to load

    # FIRST ITEM SHOULD BE THE LEVEL'S TILESHEET
    buildSheet = levelFile.pop(0)

    # BUILDS THE LEVEL BY POPPING EACH ITEM OFF
    buildLayout = [[[] for x in range(WIDTH)] for x in range(4)]
    for row in range(HEIGHT):    # creates up dungeon
        for col in range(WIDTH):
            buildLayout[   UP][col].append(levelFile.pop(0))

    for row in range(HEIGHT):    # creates left and right; they occupy same line
        for col in range(WIDTH):
            buildLayout[ LEFT][col].append(levelFile.pop(0))

        for col in range(WIDTH):
            buildLayout[RIGHT][col].append(levelFile.pop(0))

    for row in range(HEIGHT):    # finally, creates down
        for col in range(WIDTH):
            buildLayout[ DOWN][col].append(levelFile.pop(0))

    # CREATES A LEVEL OBJECT AND ADDS IT TO THE LEVEL LIST
    levels.append(Level(buildLayout, buildSheet))



#######################
### MISC / UNSORTED ###
#######################
moveQueue = []  # keeps track of inputs
clock = pygame.time.Clock()                 # stabilizes fps
TAHOMA = pygame.font.SysFont("Tahoma", 10)  # font used for debug purposes
running = True        # game loop finishes once this is set to false
debugPressed = False  # tracks if the debug button is being pressed




################################################################################
###                                MENU ..?                                  ###
################################################################################
# the main display, pre-camera
preDisplay = newSurf((SCREENLENGTH, SCREENLENGTH + CAMLIMIT))

# the main display, post-camera
postDisplay = pygame.display.set_mode(SCREENSIZE)


# levelNum can be changed later with the level select
levelNum = 0
if levelNum == 0:
    playDung = RIGHT
    playCol = 0
    playRow = 2

# find the goal in the previous level and start the player from there
else:
    goalExists = False
    for dungNum, dung in enumerate(levels[levelNum - 1].layout):
        for x, col in enumerate(dung):
            for y, tile in enumerate(col):
                if tile == GOAL:
                    playDung = dungNum
                    playCol = x
                    playRow = y
                    goalExists = True

    # if somehow no goal was found, default to the middle of the level
    if not goalExists:
        playDung = LEFT
        playCol = 2
        playRow = 2


# PREDRAWS THE SIDES OF ALL THE LEVELS
# makes a surface that stores level sides for all four dungeons
sideSurfs = newSurf((DUNGW * 4, (len(levels) + 1)*SIDE + TILE+SIDE))

# draws the four dungeons for each level
y = len(levels) * SIDE
for level in reversed(levels):
    y -= SIDE
    for dung in range(4):
        for col in range(WIDTH):
            x = dung*DUNGW + col*TILE
            level.drawTile(sideSurfs, dung, col, HEIGHT-1, x, y)


### PER-LEVEL LOOP ###
while True:

    ############################################################################
    ###                   STUFF THAT RESETS EACH LEVEL                       ###
    ############################################################################

    ### DRAWING LEVELS ###
    curLvl = levels[levelNum]  # stores reference to current level
    nexLvl = levels[levelNum + 1]  # stores reference to next level
    curLay = newSurf(SCREENSIZE)   # current level's layer
    nexLay = newSurf((SCREENLENGTH, SCREENLENGTH + SIDE))

    # a black surface used to fade the level sides out
    shadow = pygame.Surface((DUNGW, SIDE))


    ### ANIMATION STUFF ###
    # NEXT LEVEL
    nexLayY = 0  # resets y values
    curLayY = 0
    sideY = (levelNum + 2) * SIDE
    angleOff = 0

    animCur = None


    ### PREDRAWS BOTH THE CURRENT LEVEL AND THE NEXT LEVEL ###
    curDungs.fill((0, 255, 0))
    for dung in range(4):
        curLvl.drawDung(curDungs, dung, dung * DUNGW, 0)
        curLay.blit(curDungs, (dungX[dung], dungY[dung]), dungRects[dung])

        x = dungX[dung]
        y = dungY[dung] + DUNGH + SIDE
        blitSide(nexLay, dung, x, y)

        # DRAWS SHADOWS
        shadowAlpha = 0
        for layer in range(1, LEVELSDOWN + 2):
            shadowAlpha += SHADOWINTERVAL
            shadow.set_alpha(shadowAlpha)
            x = dungX[dung]
            y = dungY[dung] + DUNGH + layer * SIDE
            nexLay.blit(shadow, (x, y))

        # DRAWS THE NEXT LEVEL
        nexLvl.drawDung(nexLay, dung)


    # MISC
    camXLock = 0    # reset camera
    camYLock = 0

    # stores player's current position for when reset key is pressed
    startCol = playCol
    startRow = playRow
    startDung = playDung



    ############################################################################
    ###                           GAMEPLAY LOOP                              ###
    ############################################################################

    nextLevel = False
    while not nextLevel:

        ##############
        ### EVENTS ###
        ##############
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:

                # inserts inputs into the moveQueue
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    moveQueue.insert(0, LEFT)
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    moveQueue.insert(0, UP)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    moveQueue.insert(0, RIGHT)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    moveQueue.insert(0, DOWN)

                # debug key
                elif event.key == pygame.K_f:
                    debugPressed = True

                # resets level
                elif event.key == pygame.K_r and animQueue == []:
                    # resets camera
                    camXLock = 0
                    camYLock = 0

                    # resets layout and redraws dungeons
                    curLvl.layout = curLvl.origLayout
                    for dung in range(4):
                        curLvl.drawDung(curDungs, dung, dung * DUNGW, 0)
                        position = (dungX[dung], dungY[dung])
                        curLay.blit(curDungs, position, dungRects[dung])

                    # resets player
                    playCol = startCol
                    playRow = startRow
                    playDung = startDung



            elif event.type == pygame.KEYUP:

                # removes inputs from the moveQueue
                liftedKey = 0
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    liftedKey = LEFT
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    liftedKey = UP
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    liftedKey = RIGHT
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    liftedKey = DOWN

                elif event.key == pygame.K_f:
                    debugPressed = False

                if liftedKey in moveQueue:
                    moveQueue.remove(liftedKey)

            elif event.type == pygame.QUIT:
                running = False



        #############
        ### INPUT ###
        #############

        ### MOVEMENT ###
        # if an input was made and no animation is currently playing
        if moveQueue and animQueue == []:

            # start movement animation if you land on a non-wall/non-void tile
            moveDirection = moveQueue[0]
            queryX = playCol
            queryY = playRow
            if moveQueue[0] == LEFT:
                queryX -= 1

            elif moveQueue[0] == RIGHT:
                queryX += 1

            elif moveQueue[0] == UP:
                queryY -= 1

            elif moveQueue[0] == DOWN:
                queryY += 1

            if curLvl.tileAt(moveDirection, queryX, queryY) not in [WALL, VOID]:
                playDung = moveDirection
                playAnim = playMovement[moveDirection]
                ghostAnim = ghostMovement[moveDirection]

                # a quick fix for the animation not showing the first frame
                playAnim.frame = -1
                ghostAnim.frame = -1

                animQueue.append(playAnim)

        if moveQueue:
            camDir = moveQueue[0]
            if camDir == LEFT or camDir == RIGHT:
                camXLock = CAMMAXFRAME
            elif camDir == UP or camDir == DOWN:
                camYLock = CAMMAXFRAME



        ##################
        ### ANIMATIONS ###
        ##################

        ### ALL QUEUED ANIMATIONS ###
        # increments these animations one at a time
        if animQueue:
            animCur = animQueue[0]

            # LAST FRAME STUFF
            if animCur.frame == animCur.lastFrame:
                animCur.resetAnim()

                # SPECIFIC TO PLAYER MOVEMENT
                if animCur is playAnim:
                    playCol = queryX       # update the player's position
                    playRow = queryY

                    tile = curLvl.tileAt(playDung, playCol, playRow)
                    if tile == SWIRL:
                        animQueue.append(animRotate)

                    elif tile == GOAL:
                        animQueue.append(animPlayDrop)
                        animQueue.append(animCurLvlUp)

                    playAnim = playIdle  # reset the sprite to idle
                    ghostAnim = ghostIdle



                # SPECIFIC TO DUNGEON ROTATION
                elif animCur is animRotate:
                    # put player in new dung
                    playDung = (playDung + 1) % 4

                    # update layour
                    curLvl.layout.insert(0, curLvl.layout[3])
                    del curLvl.layout[4]

                    curLvl.tileVars.insert(0, curLvl.tileVars[3])
                    del curLvl.tileVars[4]

                    # REDRAW THE DUNGEONS IN THEIR NEW POSITIONS
                    curDungs.fill((0, 255, 0))
                    curLay.fill((0, 255, 0))
                    for dung in range(4):
                        curLvl.drawDung(curDungs, dung, dung * DUNGW, 0)
                        position = (dungX[dung], dungY[dung])
                        curLay.blit(curDungs, position, dungRects[dung])



                # SPECIFIC TO PLAYER DROP DURING NEXT LEVEL TRANSITION
                elif animCur is animPlayDrop:
                    # skips a frame of animation
                    animQueue.remove(animCur)
                    continue

                # SPECIFIC TO NEXT LEVEL TRANSITION
                elif animCur is animCurLvlUp:
                    levelNum += 1
                    nextLevel = True

                    # exits game loop and goes to the next level
                    animQueue.remove(animCur)
                    break

                animQueue.remove(animCur) # deletes animation from queue



            # ALL OTHER FRAMES
            else:
                # INCREMENT FRAME AND VALUES
                animCur.nextFrame()



                # SPECIFIC TO DUNGEON ROTATION
                if animCur is animRotate:
                    curLay.fill((0, 255, 0))

                    # CALCULATES WHERE ON THE CIRCLE TO DRAW THE LEVEL
                    for dung in range(4):
                        angle = (dung + 2) % 4 * 90
                        angle += animCur.value
                        angle = math.radians(angle)

                        x = ROTATEMIDX + math.cos(angle) * ROTATERADIUS
                        y = ROTATEMIDY + math.sin(angle) * ROTATERADIUS

                        curLay.blit(curDungs, (x, y), dungRects[dung])

                    # DRAWS THE PLAYER THERE



                # SPECIFIC TO NEXT LEVEL TRANSITION
                elif animCur is animCurLvlUp:
                    # moves everything up

                    curLayY = round(animCurLvlUp.value)
                    nexLayY = round(animNexLvlUp.value)


                    for dung in range(4):
                        # redraws the side layer
                        x = dungX[dung]
                        y = dungY[dung] + DUNGH + SIDE
                        blitSide(nexLay, dung, x, y)

                        # redraws the shadows
                        shadowAlpha = - NEXTSHADOWINTERVAL * animCur.frame
                        for layer in range(1, LEVELSDOWN + 2):
                            shadowAlpha += SHADOWINTERVAL
                            shadow.set_alpha(shadowAlpha)
                            x = dungX[dung]
                            y = dungY[dung] + DUNGH + layer * SIDE
                            nexLay.blit(shadow, (x, y))



        ##########################
        ### DRAWING EVERYTHING ###
        ##########################

        ### SIDE OF NEXT DUNGEONS & NEXT LEVEL ###
        preDisplay.blit(nexLay, (0, nexLayY + SIDE))

        ### DUNGEONS ###
        preDisplay.blit(curLay, (0, curLayY))

        ### PLAYER ###
        for dung in range(4):
            playX = dungX[dung] + (playCol - 1) * TILE
            playY = dungY[dung] + (playRow - 1) * TILE

            ### CHANGE THE PLAYER'S POSITION BASED ON THE CURRENT ANIMATION ###
            if animCur is animPlayDrop:
                playY += animPlayDrop.value

            elif animCur is animCurLvlUp:
                playY += nexLayY + SIDE

                if nexLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                    y = playY + TILE

            elif animCur is animRotate:
                angle = (dung + 2) % 4 * 90
                angle += animRotate.value
                angle = math.radians(angle)

                playX = ROTATEMIDX + math.cos(angle) * ROTATERADIUS
                playY = ROTATEMIDY + math.sin(angle) * ROTATERADIUS

                playX += (playCol - 1) * TILE
                playY += (playRow - 1) * TILE


            ### DRAW THE PLAYER (and the ghosts) ###
            if playDung == dung:
                playAnim.blitFrame(preDisplay, (playX, playY))
            else:
                ghostAnim.blitFrame(preDisplay, (playX, playY))


            ### DRAWS BLOCKS THAT SHOULD OVERLAP THE PLAYER (and ghosts)###
            if animCur is animPlayDrop:

                # draws block directly below player.  no exceptions
                if nexLvl.tileAt(dung, playCol, playRow + 1):
                    curLvl.drawTile(preDisplay, dung, playCol, playRow + 1)


            elif animCur is animCurLvlUp:
                x = playX + TILE

                # draws block beneath player on next level
                if nexLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                    y = playY + TILE + TILE

                    nexLvl.drawTile(preDisplay, dung, playCol, playRow + 1, x, y)

                # draws the column of blocks that overlap the player
                # during first half, only draw blocks below the player
                if animCur.frame < animCur.lastFrame / 2:

                    # a wall will start higher up from the other blocks
                    if curLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                        y = playY + TILE + SIDE
                    else:
                        y = playY + TILE + TILE

                # during second half, top ghost is covered by bottom dungeon
                else:
                    # so draw the entire column
                    y = dungY[dung]

                section = (x, y, TILE, DUNGH)
                preDisplay.blit(curLay, (x, y + curLayY), section)


            elif animCur is animRotate:

                # draws block beneath player
                if curLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                    x = playX + TILE
                    y = playY + TILE + TILE
                    nexLvl.drawTile(preDisplay, dung, playCol, playRow + 1, x, y)


            else:   # normal movement

                # IF A WALL IS BELOW YOU, IT SHOULD COVER YOU
                # check two blocks below instead of one when moving down
                if playAnim is playMovement[DOWN]:
                    row = 2
                else:
                    row = 1

                # if there is a wall below, it should cover the player
                if curLvl.tileAt(dung, playCol, playRow + row) == WALL:
                    curLvl.drawTile(preDisplay, dung, playCol, playRow + row)


                # LEFT/RIGHT MOVEMENT REQUIRES A SECOND BLOCK TO BE DRAWN
                # because your sprite extends in that direction
                col = None
                if playAnim is playMovement[LEFT]:
                    col = -1
                elif playAnim is playMovement[RIGHT]:
                    col = 1

                # draw the other tile that covers the player
                if col:
                    if curLvl.tileAt(dung, playCol+col, playRow+1) == WALL:
                        curLvl.drawTile(preDisplay, dung, playCol + col, playRow + 1)



        ### CAMERA MOVEMENT ###
        # MOVES THE CAMERA ALONG X AXIS
        if camXLock:
            camXLock -= 1

            if camDir == LEFT:
                camX -= (CAMLIMIT + camX) * 0.1
            elif camDir == RIGHT:
                camX += (CAMLIMIT - camX) * 0.1

        elif -0.2 > camX or camX > 0.2:  # smooths the movement back, until 0.2
            camX -= camX * 0.1

        else:                            # resets the camera to 0
            camX = 0


        # MOVES THE CAMERA ALONG Y AXIS, BASICALLY THE SAME AS X
        if camYLock:
            camYLock -= 1

            if camDir == UP:
                camY -= (CAMLIMIT + camY) * 0.1
            elif camDir == DOWN:
                camY += (CAMLIMIT - camY) * 0.1

        elif -0.2 > camY or camY > 0.2:
            camY -= camY * 0.1

        else:
            camY = 0


        postDisplay.blit(preDisplay, (-camX, -camY))



        ### POST CAMERA ###
        # there's nothing here lol


        ### DEBUGGING ###
        #print(animNextLevel.frame, dungLayer.get_alpha())
        fps = TAHOMA.render(str(round(clock.get_fps())), False, (255, 255, 255))
        debug1 = TAHOMA.render(str(levelNum * 20), False, (255, 255, 255))
        postDisplay.blit(fps, (10, 10))
        postDisplay.blit(debug1, (10, 20))
        if debugPressed:
            clockTick = 2   # slow down game when the debug button is pressed
        else:
            clockTick = 60


        ### FINAL OUTPUT ###
        pygame.display.flip()        # display the screen

        preDisplay.fill((0, 0, 0))   # clear the screen
        postDisplay.fill((0, 0, 0))

        clock.tick(clockTick)        # keeps the FPS at a consistent 60



        # exits loops when window is closed
        if not running:
            break

    if not running:
        break



pygame.quit()
