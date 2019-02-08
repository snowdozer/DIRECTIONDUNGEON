#########################
### DIRECTIONDUNGEON! ###
#########################
### todo
# levels with more objects (mainly walls) are laggier, but only in IDLE
# also black background when current level moves up
# camera                      DONE
# centerpiece
# movement animations         DONE, LEFT/RIGHT COULD BE IMPROVED
# dungeon rotation animation  DONE, MIGHT NEED TO BE FASTER THOUGH
# level clear animation       DONE? NEEDS A LOT OF CLEANUP, CAN LOOKER BETTER
# should bottom wall partially cover the bottom tile?
# different perspectives for each dungeon?
# keys?
# levels: probably 64, since it's 4 cubed, and because of 4 button menu
# main menu
# pause function?
# sounds, probably raindrop-py
# outsource music to mustardflu?  or maybe just have no music at all



################################################################################
###                    STUFF THAT IS ONLY LOADED ONCE                        ###
################################################################################
import math
import os
import sys
import copy
import pygame



#############################
### WINDOW INITIALIZATION ###
#############################
os.environ['SDL_VIDEO_CENTERED'] = '1' # centers the window on the screen

pygame.init()
pygame.display.set_caption('DIRECTIONDUNGEON!')  # window title

# CREATES THE INITIAL SCREEN BASED ON DESKTOP SIZE
mult = 8

# PIXEL SIZE CONSTANTS
TILE = 4 * mult   # pixel size of a tile
SIDE = 2 * mult   # pixel size of the side of a tile

MARG = 2 * mult   # pixel size of the margin between dungeons                  
WIDTH  = 5         # tile width of a dungeon
HEIGHT = 5         # tile height of a dungeon
DUNGW = TILE*WIDTH  # pixel width of a dungeon
DUNGH = TILE*HEIGHT # pixel height of a dungeon

SCREENLENGTH = DUNGH*3 + SIDE + MARG*4   # the size of the screen
SCREENSIZE = (SCREENLENGTH, SCREENLENGTH) # the size of the screen, tupled

postDisplay = pygame.display.set_mode(SCREENSIZE) # post-camera



###########################
### CONSTANTS AND STUFF ###
###########################
# DIRECTION CONSTANTS
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

# TILE TYPES
VOID = 0
EMPTY = 1
WALL = 2
GOAL = 3
SWIRL = 4



# DEFAULT DUNGEON POSITIONS AT A DUNGEON SIZE OF 6
dungX = [MARG, DUNGW + MARG*2, DUNGW*2 + MARG*3, DUNGW + MARG*2]
dungY = [DUNGH + MARG*2, MARG, DUNGH + MARG*2, DUNGH*2 + MARG*3]

# CENTERS THE DUNGEONS
for i in range(4):
    dungX[i] += SIDE

##############################
### SPRITES AND ANIMATIONS ###
##############################
### ANIMATION QUEUES ###
animQueue = []

### STATIC SPRITES ###
def loadSprite(path, mult):
    sprite = pygame.image.load(path) # load sprite

    w = sprite.get_width()           # resize sprite
    h = sprite.get_height()
    sprite = pygame.transform.scale(sprite, (w * mult, h * mult))

    sprite.convert()                 # convert sprite

    sprite.set_colorkey((0, 255, 0)) # transparentize sprite

    return sprite



### ANIMATIONS ###

# ANIMATION KINDS
SPRITE     = 1 # counts by ones, also has a spritesheet tied to it
COUNTER    = 2 # counts by ones
LINEAR     = 3 # counts by a defined value
QUADRATIC  = 4 # counts by a changing value, slow then speeds up
RQUADRATIC = 5 # counts by a changing value, fast then slows down

class Animation:
    def __init__ (self, lastFrame, kind, arg0 = None, arg1 = None,
                  arg2 = None, arg3 = None, arg4 = ()):
        self.frame = 0
        self.lastFrame = lastFrame
        self.kind = kind



        # SPRITE-BASED ANIMATION
        if kind == SPRITE:
            self.tied = arg4

            # define what the arguments mean
            filePath = arg0
            width = arg1
            height = arg2
            mult = arg3

            # apply the width, height, and spritesheet of the animation
            self.width = width * mult
            self.height = height * mult

            self.surface = loadSprite(filePath, mult)

        # VALUE-BASED ANIMATION
        else:
            # define what the arguments mean
            peakValue = arg0

            if arg1:
                self.tied = arg1
            else:
                self.tied = ()

            # create a counter based on the kind of animation
            if kind == LINEAR:
                self.lastValue = peakValue
                self.value = 0
                self.DIFF = peakValue / lastFrame

            elif kind == QUADRATIC or kind == RQUADRATIC:
                h = lastFrame
                k = peakValue
                a = k / h**2
                self.value = 0
                self.DIFF2 = a * 2

                if kind == QUADRATIC:
                    self.lastValue = peakValue
                    self.diff1 = a

                elif kind == RQUADRATIC:
                    # GOES THROUGH THE PARABOLA AND RECORDS THE PRE-VERTEX VALUE
                    # INEFFICIENT BUT I SPENT FOREVER TRYING SOMETHING ELSE
                    diff1 = a

                    for x in range (lastFrame - 1):
                        diff1 += self.DIFF2

                    self.firstDiff1 = diff1
                    self.diff1 = diff1


    # DRAWS A SPECIFIC FRAME, BY CUTTING IT OUT FROM THE SURFACE
    def blitFrame(self, dest, position, frameNum = -1):
        if frameNum == -1:
            frameNum = self.frame

        frameRect = (0, self.height * frameNum, self.width, self.height)
        dest.blit(self.surface, position, frameRect)


    # ADVANCES THE FRAME BY 1
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

        # forwards all tied animations
        for anim in self.tied:
            anim.nextFrame()


    # RESETS ANIMATION BACK TO FRAME 0
    def resetAnim(self):
        self.frame = 0

        # resets value on all animations but sprite-based ones
        if self.kind != SPRITE:
            self.value = 0

        if self.kind == QUADRATIC:
            self.diff1 = self.DIFF2 / 2

        elif self.kind == RQUADRATIC:
            self.diff1 = self.firstDiff1

        # resets all tied animations
        for anim in self.tied:
            anim.resetAnim()



# PLAYER
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

# idle doesn't have to be animation, but this just makes things easier
playIdle = Animation(0, SPRITE, "images\\playIdle.png",  12, 14, mult)
ghostIdle = Animation(0, SPRITE, "images\\playIdle.png",  12, 14, mult)
ghostIdle.surface.set_alpha(100)
playAnim = playIdle
ghostAnim = ghostIdle



# TILES (each tileset is a "frame")
tileEmpty = Animation(2, SPRITE, "images\\empty.png",   4, 4, mult)
tileWall  = Animation(2, SPRITE, "images\\wallTop.png", 4, 4, mult)
tileWallSide = Animation(2, SPRITE, "images\\wallSide.png", 4, 2, mult)
tileGoal  = Animation(2, SPRITE, "images\\goal.png",    4, 4, mult)
tileSwirl = Animation(2, SPRITE, "images\\swirl.png",   4, 4, mult)
TILEBLUE = 0
TILEGREEN = 1
TILEPURPLE = 2

# indexes each tile sprite
tiles = [None, tileEmpty, tileWall, tileGoal, tileSwirl]



# LEVEL
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



# RETURNS THE PIXEL POSITION ON THE SCREEN OF A TILE
def pixelPos(dung, x, y):
    if dung == None:
        x = x * TILE
        y = y * TILE
    else:
        x = dungX[dung] + x * TILE
        y = dungY[dung] + y * TILE

    return (x, y)

# CREATES A NEW LAYER, WITH COLORKEY TRANSPARENCY
def newSurf(dimensions):
    layer = pygame.Surface(dimensions)
    layer.set_colorkey((0, 255, 0))
    layer.fill((0, 255, 0))
    return layer



# DUNGEON SURFACES
curDungs = newSurf(SCREENSIZE)
dungRects = []
for dung in range(4):
    dungRects.append((dungX[dung], dungY[dung], DUNGW, DUNGH + SIDE))




##############
### LEVELS ###
##############
class Level:
    TILES = [None, tileEmpty, tileWall, tileGoal, tileSwirl]
    def __init__(self, layout, tileset):
        self.origLayout = layout
        self.layout = layout
        self.tileset = tileset

    def tileAt(self, dung, x, y):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            return self.layout[dung][x][y]
        else:
            return VOID

    def drawTile(self, surf, dung, col, row, x = None, y = None):
        if x == None and y == None:
            pos = pixelPos(dung, col, row)
        else:
            pos = (x, y)

        tile = self.tileAt(dung, col, row)


        if tile == WALL:
            tileWall.blitFrame(surf, pos, self.tileset)

            if self.tileAt(dung, col, row + 1) != WALL:
                pos = (pos[0], pos[1] + TILE)
                tileWallSide.blitFrame(surf, pos, self.tileset)

        elif tile != VOID:
            pos = (pos[0], pos[1] + SIDE)
            self.TILES[tile].blitFrame(surf, pos, self.tileset)

    def drawDung(self, surf, dung, x = None, y = None):
        for col in range(WIDTH):
            for row in range(HEIGHT):
                if x != None and y != None:
                    x = x + col*TILE
                    y = y + row*TILE
                self.drawTile(surf, dung, col, row, x, y)




# the level files use these letters to represent the tiles
V = VOID
E = EMPTY
W = WALL
G = GOAL
S = SWIRL

levels = []
for file in os.listdir("levels\\"):   # goes through each level file
    levelFile = open("levels\\" + file, "r")
    levelFile = levelFile.read()

    # SPLIT EACH LETTER IN THE FILE, AND CONVERT EACH INTO A NUMBER
    levelFile = levelFile.split()
    for x in range(len(levelFile)):
        levelFile[x] = eval(levelFile[x])

    # FIRST THING IS THE LEVEL'S TILESET
    buildSet = levelFile.pop(0)

    # BUILDS THE LEVEL BY POPPING OFF THE NUMBERS IN ORDER
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

    # ADDS THE LEVEL TO THE LEVEL LIST
    levels.append(Level(buildLayout, buildSet))



#######################
### MISC / UNSORTED ###
#######################
clock = pygame.time.Clock()
TAHOMA = pygame.font.SysFont("Tahoma", 10)
running = True
debugPressed = False

# BLITS A SEGMENT FROM SIDESURFS
def blitSide(surf, dung, x, y):
    segment = (0, sideY + SIDE * 4, DUNGW, SIDE * LEVELSDOWN + SIDE)
    surf.blit(sideSurfs[dung], (x, y), segment)



################################################################################
###                                MENU ..?                                  ###
################################################################################
preDisplay = newSurf(SCREENSIZE)  # pre-camera surface



# levelNum can be changed later with the level select
levelNum = 0
if levelNum == 0:
    playDung = RIGHT
    playCol = 0
    playRow = 2

else:
    # find the goal in the prevoius level and starts the player from there
    for dungNum, dung in enumerate(levels[levelNum - 1][0]):
        for x, col in enumerate(dung):
            for y, tile in enumerate(col):
                if tile == GOAL:
                    playDung = dungNum
                    playCol = x
                    playRow = y



# PREDRAWS THE SIDES OF ALL THE LEVELS
sideSurfs = []
for dung in range(4):
    sideSurf = newSurf((DUNGW, len(levels)*SIDE))

    y = len(levels) * SIDE
    for level in reversed(levels):
        for col in range(WIDTH):
            level.drawTile(sideSurf, dung, col, HEIGHT - 1, col*TILE, y)
        y -= SIDE

    sideSurfs.append(sideSurf)



while True:

    ############################################################################
    ###                   STUFF THAT RESETS EACH LEVEL                       ###
    ############################################################################
    camX = 0
    camY = 0

    curLvl = levels[levelNum]
    nexLvl = levels[levelNum + 1]



    ### PLAYER INPUT ###
    moveQueue = []


    ### DRAWING DUNGEONS ###
    curLay = newSurf(SCREENSIZE)  # current level's layer
    nexLay = newSurf((SCREENLENGTH, SCREENLENGTH + SIDE))


    ### ANIMATION STUFF ###
    # NEXT LEVEL
    nexLayY = 0 # resets next level animation
    curLayY = 0
    curSpeed = 0
    shadow = pygame.Surface((DUNGW, SIDE))  # fades the next levels out

    sideY = (levelNum + 1) * SIDE   # the yPos of the next level in sideSurfs

    # ROTATION
    angleOff = 0

    animCur = None



    # DRAWS BOTH THE CURRENT LEVEL AND THE NEXT LEVEL
    curDungs.fill((0, 255, 0))
    for dung in range(4):
        curLvl.drawDung(curDungs, dung)
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

                # sorts priority of directional keys currently being pressed
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    moveQueue.insert(0, LEFT)
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    moveQueue.insert(0, UP)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    moveQueue.insert(0, RIGHT)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    moveQueue.insert(0, DOWN)
                elif event.key == pygame.K_f:
                    debugPressed = True



            elif event.type == pygame.KEYUP:

                # finds what key was released
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

                # removes the listed key from the query
                if liftedKey in moveQueue:
                    moveQueue.remove(liftedKey)

            elif event.type == pygame.QUIT:
                running = False



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

                    # REDRAW THE DUNGEONS IN THEIR NEW POSITIONS
                    curLay.fill((0, 255, 0))
                    for dung in range(4):
                        curLvl.drawDung(curDungs, dung)
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


                    for dung, sideSurf in enumerate(sideSurfs):
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



        ####################
        ### CALCULATIONS ###
        ####################
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
                playAnim  = playMovement[moveDirection]
                ghostAnim = ghostMovement[moveDirection]
                animQueue.append(playAnim)




        ##########################
        ### DRAWING EVERYTHING ###
        ##########################

        # SIDE OF NEXT DUNGEONS & NEXT LEVEL
        preDisplay.blit(nexLay, (0, nexLayY + SIDE))

        # DUNGEONS
        preDisplay.blit(curLay, (0, curLayY))

        # PLAYER
        # checks for walls that overlaps player
        checks = [[playAnim, 0, 1],
                  [playMovement[LEFT], -1, 1],
                  [playMovement[RIGHT], 1, 1]]

        for dung in range(4):
            # CALCULATE THE PLAYER'S POSITION BASED ON THE CURRENT ANIMATION
            playX = dungX[dung] + (playCol - 1) * TILE
            playY = dungY[dung] + (playRow - 1) * TILE
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



            # draws player at thier dungeon, and ghosts at all the others
            if playDung == dung:
                playAnim.blitFrame(preDisplay, (playX, playY))
            else:
                ghostAnim.blitFrame(preDisplay, (playX, playY))



            # DRAWS BLOCKS THAT SHOULD OVERLAP THE PLAYER
            if animCur is animCurLvlUp:
                x = playX + TILE

                # draw wall below player on next level
                if nexLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                    y = playY + TILE + TILE

                    tileWall.blitFrame(preDisplay, (x, y), nexLvl.tileset)

                # draw a segment of the current level above the player
                if animCur.frame < animCur.lastFrame / 2:
                    if curLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                        y = playY + TILE + SIDE
                    else:
                        y = playY + TILE + TILE

                else:
                    # makes top player be covered by bottom dungeon
                    y = dungY[dung]

                section = (x, y, TILE, DUNGH)
                preDisplay.blit(curLay, (x, y + curLayY), section)

            elif animCur is animRotate:
                if curLvl.tileAt(dung, playCol, playRow + 1) == WALL:
                    x = playX + TILE
                    y = playY + TILE + TILE
                    tileWall.blitFrame(preDisplay, (x, y), curLvl.tileset)




            else:  # during normal movement

                # draws any walls that should overlap the player
                if playAnim == playMovement[DOWN]:
                    checks[0][2] = 2

                for i in checks:
                    x = playCol + i[1]
                    y = playRow + i[2]

                    if playAnim == i[0] and curLvl.tileAt(dung, x, y) == WALL:
                        position = pixelPos(dung, x, y)

                        tileWall.blitFrame(preDisplay, position, curLvl.tileset)



        postDisplay.blit(preDisplay, (-camX, -camY))
        ### POST CAMERA ###



        ### DEBUGGING ###
        #print(animNextLevel.frame, dungLayer.get_alpha())
        fps = TAHOMA.render(str(round(clock.get_fps())), False, (255, 255, 255))
        debug1 = TAHOMA.render(str(playY), False, (255, 255, 255))
        postDisplay.blit(fps, (10, 10))
        postDisplay.blit(debug1, (10, 20))
        if debugPressed:
            clockTick = 2
        else:
            clockTick = 60



        ### FINAL OUTPUT ###
        pygame.display.flip()        # display the screen

        preDisplay.fill((0, 0, 0))   # clear the screen
        postDisplay.fill((0, 0, 0))
        clock.tick(clockTick)        # keeps the FPS consistent 60


        if not running: # exits loop when window closed
            break

    if not running:
        break



pygame.quit()