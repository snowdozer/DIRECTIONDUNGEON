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
mult = 7

# PIXEL SIZE CONSTANTS
TILE = 4 * mult   # pixel size of a tile
SIDE = 2 * mult
MARG = 2 * mult   # pixel size of the margin between dungeons                  
WIDTH  = 6  # tile dimensions of a dungeon
HEIGHT = 6

SCREENLENGTH = TILE*HEIGHT*3 + SIDE + MARG*4
SCREENSIZE = (SCREENLENGTH, SCREENLENGTH)

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
dungX = [MARG, TILE*WIDTH + MARG*2, TILE*WIDTH*2 + MARG*3, TILE*WIDTH + MARG*2]
dungY = [TILE*WIDTH + MARG*2, MARG, TILE*WIDTH + MARG*2, TILE*WIDTH*2 + MARG*3]

# CENTERS THE DUNGEONS
for i in range(4):
    dungX[i] += SIDE

##############################
### SPRITES AND ANIMATIONS ###
##############################
### ANIMATION QUEUES ###
animQueue = []
animBypass = []
animLoop = []

### STATIC SPRITES ###
def loadSprite(path, mult):
    sprite = pygame.image.load(path) # load sprite

    w = sprite.get_width()           # resize sprite
    h = sprite.get_height()
    sprite = pygame.transform.scale(sprite, (w * mult, h * mult))

    sprite.convert()                 # convert sprite

    sprite.set_colorkey((0, 255, 0)) # transparentize sprite

    return sprite


# whoops nothing here


### ANIMATIONS ###
class Animation:
    def __init__ (self, last, filePath = None, width = 0, height = 0, mult = 0):
        self.frame = 0         # stores current frame number
        self.last = last       # index of the last frame in the animation

        if filePath:
            self.width  = width * mult # dimensions of a resized single frame
            self.height = height * mult

            # stores the animation spritesheet
            self.surface = loadSprite(filePath, mult)


    # DRAWS A SPECIFIC FRAME, BY CUTTING IT OUT FROM THE SURFACE
    def blitFrame(self, dest, position, frameNum = -1):
        if self.surface:
            if frameNum == -1:
                frameNum = self.frame

            frameRect = (0, self.height * frameNum, self.width, self.height)
            dest.blit(self.surface, position, frameRect)


# PLAYER
directionStrings = ["Left", "Up", "Right", "Down"]
playMovement = []
ghostMovement = []
for direction in directionStrings:
    anim = Animation(6, "images\\play" + direction + ".png", 12, 14, mult)
    playMovement.append(anim)

    anim = Animation(6, "images\\play" + direction + ".png", 12, 14, mult)
    anim.surface.set_alpha(100)
    ghostMovement.append(anim)

# idle doesn't have to be animation, but this just makes things easier
playIdle = Animation(1, "images\\playIdle.png",  12, 14, mult)
ghostIdle = Animation(1, "images\\playIdle.png",  12, 14, mult)
ghostIdle.surface.set_alpha(100)
playAnim = playIdle
ghostAnim = ghostIdle



# TILES (each tileset is a "frame")
tileEmpty = Animation(1, "images\\empty.png",   4, 4, mult)
tileWall  = Animation(1, "images\\wallTop.png", 4, 4, mult)
tileWallSide = Animation(1, "images\\wallSide.png", 4, 2, mult)
tileGoal  = Animation(1, "images\\goal.png",    4, 4, mult)
tileSwirl = Animation(1, "images\\swirl.png",   4, 4, mult)
TILEBLUE = 0
TILEGREEN = 1
TILEPURPLE = 2

# indexes each tile sprite
tiles = [None, tileEmpty, tileWall, tileGoal, tileSwirl]



# LEVEL
animRotate = Animation(18)
ROTATERADIUS = TILE*WIDTH + MARG
ROTATEMIDX = TILE*WIDTH + MARG*3
ROTATEMIDY = TILE*WIDTH + MARG*2
ANGLEINTERVAL = 90 / animRotate.last

animPlayDrop  = Animation(8)
PLAYDROPINTERVAL  = SIDE / animPlayDrop.last

animNextLevel = Animation(34)
DUNGSPEEDINTERVAL = SCREENLENGTH / animNextLevel.last / animNextLevel.last * 2
NEXTLEVELINTERVAL = SIDE / animNextLevel.last
LEVELSDOWN = 10  # how many levels below current level to show
SHADOWINTERVAL = 255 / (LEVELSDOWN - 1)
NEXTSHADOWINTERVAL = SHADOWINTERVAL / animNextLevel.last




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



##############
### LEVELS ###
##############
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
    buildLevel = [[[] for x in range(WIDTH)] for x in range(4)]
    for row in range(HEIGHT):    # creates up dungeon
        for col in range(WIDTH):
            buildLevel[   UP][col].append(levelFile.pop(0))

    for row in range(HEIGHT):    # creates left and right; they occupy same line
        for col in range(WIDTH):
            buildLevel[ LEFT][col].append(levelFile.pop(0))

        for col in range(WIDTH):
            buildLevel[RIGHT][col].append(levelFile.pop(0))

    for row in range(HEIGHT):    # finally, creates down
        for col in range(WIDTH):
            buildLevel[ DOWN][col].append(levelFile.pop(0))

    # ADDS THE LEVEL TO THE LEVEL LIST
    levels.append([copy.deepcopy(buildLevel), copy.copy(buildSet)])



# RETURNS THE TILE TYPE AT A SPECIFIC POINT IN THE LEVEL
def tileAt(dung, x, y, levelOff = 0):
    # levelOff can be changed to find tiles in a different level
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        return levels[levelNum + levelOff][0][dung][x][y]

    else:  # anything out of bounds
        return VOID



#######################
### MISC / UNSORTED ###
#######################
clock = pygame.time.Clock()
TAHOMA = pygame.font.SysFont("Tahoma", 10)
running = True



################################################################################
###                                MENU ..?                                  ###
################################################################################
preDisplay = newSurf(SCREENSIZE)  # pre-camera surface



# levelNum can be changed later with the level select
levelNum = 0
if levelNum == 0:
    playDung = 0
    playX = 2
    playY = 2

else:
    # find the goal in the prevoius level and starts the player from there
    for dungNum, dung in enumerate(levels[levelNum - 1][0]):
        for x, col in enumerate(dung):
            for y, tile in enumerate(col):
                if tile == GOAL:
                    playDung = dungNum
                    playX = x
                    playY = y



# PREDRAWS THE SIDES OF ALL THE LEVELS
sideSurfs = []
for dung in range(4):
    # loop through bottom tiles of next levels and draw them
    sideSurf = newSurf((WIDTH * TILE, len(levels) * SIDE))

    levNum = len(levels)
    for level in reversed(levels):
        levNum -= 1
        sideLayout = level[0]
        sideTileSet = level[1]

        for x in range(WIDTH):
            y = HEIGHT - 1

            tile = sideLayout[dung][x][y]

            if tile == WALL:
                position = pixelPos(None, x, levNum / 2)
                tileWallSide.blitFrame(sideSurf, position, sideTileSet)

            elif tile != VOID:
                position = pixelPos(None, x, levNum / 2 - 0.5)
                tiles[tile].blitFrame(sideSurf, position, sideTileSet)

    sideSurfs.append(sideSurf)




while True:

    ############################################################################
    ###                   STUFF THAT RESETS EACH LEVEL                       ###
    ############################################################################
    camX = 0
    camY = 0

    layout = copy.deepcopy(levels[levelNum][0])
    tileSet =              levels[levelNum][1]


    ### PLAYER INPUT ###
    moveQueue = []


    ### DRAWING DUNGEONS ###
    dungLayer = newSurf(SCREENSIZE)  # current level's layer
    dungSurfs = []  # stores separate surface per dungeon
    nextLayer = newSurf((SCREENLENGTH, SCREENLENGTH + SIDE))


    ### ANIMATION STUFF ###
    # NEXT LEVEL
    nextLayY = 0 # resets next level animation
    dungLayY = 0
    dungSpeed = 0
    playYOffset = 0

    shadow = pygame.Surface((WIDTH * TILE, SIDE))  # fades the next levels out

    sideY = (levelNum + 1) * SIDE   # the yPos of the next level in sideSurfs



    # ROTATION
    angleOff = 0



    currAnim = None # stores the current single animation in animQueue





    # DRAWS THE CURRENT LEVEL
    for dung in range(4):

        # loop through each tile and draw it
        dungSurf = newSurf((WIDTH*TILE, HEIGHT*TILE + SIDE))
        for x in range(WIDTH):
            for y in range(HEIGHT):
                tile = tileAt(dung, x, y)
                
                # walls are special: placed normally, may have a side
                if tile == WALL:
                    position = pixelPos(None, x, y)
                    tileWall.blitFrame(dungSurf, position, tileSet)
                    
                    if tileAt(dung, x, y + 1) != WALL:
                        position = pixelPos(None, x, y + 1)
                        tileWallSide.blitFrame(dungSurf, position, tileSet)

                # all other tiles placed half a block lower
                elif tile != VOID:
                    position = pixelPos(None, x, y + 0.5)
                    tiles[tile].blitFrame(dungSurf, position, tileSet)

        dungSurfs.append(dungSurf)
        dungLayer.blit(dungSurf, (dungX[dung], dungY[dung]))



    # DRAWS THE NEXT LEVEL (almost the same code but eh who cares)
    # everything is drawn half a block down and directly onto a layer
    nextTileSet = levels[levelNum + 1][1]
    for dung in range(4):

        # loop through each tile and draw it
        for x in range(WIDTH):
            for y in range(HEIGHT):
                tile = tileAt(dung, x, y, 1)
                
                # walls are special: placed normally, may have a side
                if tile == WALL:
                    position = pixelPos(dung, x, y + 0.5)
                    tileWall.blitFrame(nextLayer, position, nextTileSet)

                    if tileAt(dung, x, y + 1, 1) != WALL:
                        position = pixelPos(dung, x, y + 1.5)
                        tileWallSide.blitFrame(nextLayer, position, nextTileSet)

                # all other tiles placed half a block lower
                elif tile != VOID:
                    position = pixelPos(dung, x, y + 1)
                    tiles[tile].blitFrame(nextLayer, position, nextTileSet)



    # DRAWS THE SIDES OF ALL THE NEXT LEVELS
    for dung in range(4):
        sideSurf = sideSurfs[dung]
        segment = (0, sideY, WIDTH*TILE, SIDE*LEVELSDOWN + SIDE)
        position = (dungX[dung], dungY[dung] + HEIGHT*TILE + SIDE)
        nextLayer.blit(sideSurf, position, segment)

        # draws shadows
        shadowAlpha = 0
        for layer in range(1, LEVELSDOWN + 1):
            shadowAlpha += SHADOWINTERVAL
            shadow.set_alpha(shadowAlpha)
            x = dungX[dung]
            y = dungY[dung] + HEIGHT*TILE + SIDE + layer*SIDE
            nextLayer.blit(shadow, (x, y))


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
            currAnim = animQueue[0]



            # FINAL FRAME THINGS
            if currAnim.frame == currAnim.last:
                currAnim.frame = 0  # reset frame to 0

                # specific to player movement
                if currAnim == playAnim:
                    playX = queryX       # update the player's position
                    playY = queryY

                    tile = tileAt(playDung, playX, playY)
                    if tile == SWIRL:
                        animQueue.append(animRotate)

                    elif tile == GOAL:
                        animQueue.append(animPlayDrop)
                        animQueue.append(animNextLevel)
                    
                    playAnim = playIdle  # reset the sprite to idle
                    ghostAnim = ghostIdle

                # specific to dungeon rotation
                elif currAnim == animRotate:
                    angleOff = 0

                    playDung = (playDung + 1) % 4 # rotates player
                    layout.insert(0, layout[3])   # rotates dungeon layout
                    del layout[4]

                # specific to next level transition
                elif currAnim == animNextLevel:
                    levelNum += 1
                    nextLevel = True
                    
                    # blits next dungeon one last time before it gets removed
                    nextLayY -= NEXTLEVELINTERVAL
                    preDisplay.blit(nextLayer, (0, nextLayY + SIDE))




                animQueue.remove(currAnim) # deletes animation from queue



            # ALL OTHER FRAMES
            else:
                currAnim.frame += 1

                # specific to dungeon rotation
                if currAnim == animRotate:
                    angleOff += ANGLEINTERVAL
                    dungLayer.fill((0, 255, 0))
                    nextLayer.fill((0, 255, 0))
                    for dung in range(4):
                        angle = (dung + 2) % 4 * 90
                        angle += angleOff
                        angle = math.radians(angle)

                        x = ROTATEMIDX + math.cos(angle) * ROTATERADIUS
                        y = ROTATEMIDY + math.sin(angle) * ROTATERADIUS

                        dungLayer.blit(dungSurfs[dung], (x, y))

                elif currAnim == animPlayDrop:
                    # each frame, moves player a fraction of half a block
                    playYOffset += PLAYDROPINTERVAL

                # specific to next level transition
                elif currAnim == animNextLevel:
                    # moves everything up

                    dungSpeed += DUNGSPEEDINTERVAL
                    dungLayY -= dungSpeed
                    nextLayY -= NEXTLEVELINTERVAL
                    playYOffset = nextLayY + SIDE

                    for dung, sideSurf in enumerate(sideSurfs):
                        # redraws the side layer
                        segment = (0, sideY, WIDTH * TILE, SIDE * LEVELSDOWN + SIDE)
                        position = (dungX[dung], dungY[dung] + HEIGHT * TILE + SIDE)
                        nextLayer.blit(sideSurf, position, segment)

                        # redraws the shadows
                        shadowAlpha = - NEXTSHADOWINTERVAL * currAnim.frame
                        for layer in range(1, LEVELSDOWN + 1):
                            shadowAlpha += SHADOWINTERVAL
                            shadow.set_alpha(shadowAlpha)
                            x = dungX[dung]
                            y = dungY[dung] + HEIGHT * TILE + SIDE + layer * SIDE
                            nextLayer.blit(shadow, (x, y))





        ### ALL ANIMATIONS THAT SKIP THE QUEUE ###
        # increments all animations instead of just the first
        for anim in reversed(animBypass):
            if anim.frame == anim.last:
                anim.frame = 0
                animBypass.remove(anim)

            else:
                anim.frame += 1

            

        ####################   
        ### CALCULATIONS ###
        ####################
        ### MOVEMENT ###
        # if an input was made and no animation is currently playing
        if moveQueue and animQueue == []:

            # start movement animation if you land on a non-wall/non-void tile
            moveDirection = moveQueue[0]
            queryX = playX
            queryY = playY
            if moveQueue[0] == LEFT:
                queryX -= 1

            elif moveQueue[0] == RIGHT:
                queryX += 1

            elif moveQueue[0] == UP:
                queryY -= 1

            elif moveQueue[0] == DOWN:
                queryY += 1

            if tileAt(moveDirection, queryX, queryY) not in [WALL, VOID]:
                playDung = moveDirection
                playAnim  = playMovement[moveDirection]
                ghostAnim = ghostMovement[moveDirection]
                animQueue.append(playAnim)
                
                # ghost skips queue so that it is simultaneous with movement
                animBypass.append(ghostAnim)

        


        ##########################
        ### DRAWING EVERYTHING ###
        ##########################

        # SIDE OF NEXT DUNGEONS & NEXT LEVEL
        preDisplay.blit(nextLayer, (0, nextLayY))

        # DUNGEONS
        preDisplay.blit(dungLayer, (0, dungLayY))

        # PLAYER
        # checks for walls that overlaps player
        checks = [[playAnim, 0, 1],
                  [playMovement[LEFT], -1, 1],
                  [playMovement[RIGHT], 1, 1]]

        for dung in range(4):
            position = pixelPos(dung, playX - 1, playY - 1)
            position = (position[0], position[1] + playYOffset)
            # draws player at thier dungeon, and ghosts at all the others
            if playDung == dung:
                playAnim.blitFrame(preDisplay, position)
            else:
                ghostAnim.blitFrame(preDisplay, position)



            # DRAWS TILES THAT SHOULD OVERLAP THE PLAYER
            # draws level over player during win animation
            if currAnim == animNextLevel:
                for dung in range(4):
                    # draw wall below player on next level
                    if tileAt(dung, playX, playY + 1, 1) == WALL:
                        position = pixelPos(dung, playX, playY + 1.5)
                        position = (position[0], position[1] + nextLayY + 1)

                        tileWall.blitFrame(preDisplay, position, nextTileSet)

                    # draw a segment of the current level above the player
                    if currAnim.frame < currAnim.last / 2:
                        x = dungX[dung] + playX * TILE
                        y = dungY[dung] + playY * TILE + TILE

                    else:
                        # makes top player be covered by bottom dungeon
                        x = dungX[dung] + playX * TILE
                        y = dungY[dung]

                    section = (x, y, TILE, HEIGHT * TILE)
                    preDisplay.blit(dungLayer, (x, y + dungLayY + 1), section)



            # draws blocks over player during normal movement
            else:
                # draws any walls that should overlap the player
                if playAnim == playMovement[DOWN]:
                    checks[0][2] = 2

                for i in checks:
                    x = playX + i[1]
                    y = playY + i[2]

                    if playAnim == i[0] and tileAt(dung, x, y) == WALL:
                        position = pixelPos(dung, x, y)

                        tileWall.blitFrame(preDisplay, position, tileSet)



        postDisplay.blit(preDisplay, (-camX, -camY))
        ### POST CAMERA ###
        pass



        ### DEBUGGING ###
        #print(animNextLevel.frame, dungLayer.get_alpha())
        fps = TAHOMA.render(str(round(clock.get_fps())), False, (255, 255, 255))
        debugText = TAHOMA.render(str(animNextLevel.frame), False, (255, 255, 255))
        postDisplay.blit(fps, (10, 10))
        postDisplay.blit(debugText, (10, 20))
        
        ### FINAL OUTPUT ###
        pygame.display.flip()        # display the screen
        
        preDisplay.fill((0, 0, 0))   # clear the screen
        postDisplay.fill((0, 0, 0)) 
        clock.tick(60)               # keeps the FPS at 60


        if not running: # exits loop when window closed
            break
        
    if not running:
        break

    

pygame.quit()
