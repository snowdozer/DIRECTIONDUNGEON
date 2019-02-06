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

import time
import math
import os
import sys
import copy
import pygame


os.environ['SDL_VIDEO_CENTERED'] = '1' # centers the window on the screen

# PYGAME INITIALIZATION
pygame.init()
SCENE = pygame.Surface((850, 850))              # pre-camera surface
DISPLAY = pygame.display.set_mode((850, 850))   # post-camera surface
pygame.display.set_caption('DIRECTIONDUNGEON!') # window title



### CONSTANTS AND STUFF ###
# DUNGEON CONSTANTS (each of the four 5x5 areas is called a "dungeon")
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

# TILE TYPES
EMPTY = 0
WALL = 1
GOAL = 2
SWIRL = 3

# PIXEL SIZE CONSTANTS
TILE = 50              # pixel size of a tile
MARG = TILE // 2       # pixel size of the margin between dungeons
DUNGSIZE = 5           # tile size of a dungeon
DUNG = TILE * DUNGSIZE # pixel size of a dungeon
# I guess you can change these???  it'll mess everything up but sure

# PIXEL POSITION CONSTANTS:
# MMMMMMMMMMMMM     This is a 3x3 dungeon, except represented by text.
# M...MTTTM...M     M represents a margin.
# M...MTTTM...M     T represents a tile.
# M...MTTTM...M     . represents a tile-sized space.
# MMMMMMMMMMMMM     The below equations represent how many Margins and how
# MTTTM...MTTTM     many Tiles there are before a certain wall.
# MTTTM...MTTTM
# MTTTM...MTTTM     Let's take the left wall of the right dungeon as an example.
# MMMMMMMMMMMMM     M...MTTTM...M
# M...MTTTM...M              ^ start of the left wall
# M...MTTTM...M     There are three Margins (M) and two dungeons (... or TTT)
# M...MTTTM...M     before this wall, so the equation is MARG * 3 + DUNG * 2.
# MMMMMMMMMMMMM

#               LEFT  UP               RIGHT                DOWN
defaultDungX = [MARG, MARG * 2 + DUNG, MARG * 3 + DUNG * 2, MARG * 2 + DUNG]
#               LEFT             UP    RIGHT            DOWN
defaultDungY = [MARG * 2 + DUNG, MARG, MARG * 2 + DUNG, MARG * 3 + DUNG * 2]



### LOAD IMAGES ###
# LOADS A SPRITE FROM FILE (also resizes it to 5x the size)
def loadSprite(filePath):
    file = pygame.image.load(filePath)
    
    w = file.get_width()
    h = file.get_height()
    file = pygame.transform.scale(file, (w * 5, h * 5))
    
    file.convert()
    file.set_colorkey((0, 255, 0))
    return file

# LOADS A LIST OF SPRITES FROM A FOLDER, FORMING AN ANIMATION
def loadAnimation(filePath):
    frames = []
    for file in os.listdir(filePath): # all frames in the animation's folder
        frames.append(loadSprite(filePath + file))
        
    return frames

# DOES SOME WACKY THINGS TO MAKE AN IMAGE TRANSPARENT
def ghostify(image):
    ghost = copy.copy(image)
    ghost.set_alpha(100)
    return(ghost)

# MAKES AN ANIMATION TRANSPARENT
def ghostifyAnim(anim):
    ghostAnim = []
    for image in anim:
        ghostAnim.append(ghostify(image))
        
    return(ghostAnim)

# PLAYER SPRITES
playerIdle  = loadSprite("images\\player.png")  
playerLeft  = loadAnimation("images\\moveLeft\\")
playerUp    = loadAnimation("images\\moveUp\\")
playerRight = loadAnimation("images\\moveRight\\")
playerDown  = loadAnimation("images\\moveDown\\")
playerSprite = playerIdle # stores which sprite is currently being drawn

ghostIdle  = ghostify(playerIdle)    # ghosts are just a transparent player
ghostLeft  = ghostifyAnim(playerLeft)
ghostUp    = ghostifyAnim(playerUp)
ghostRight = ghostifyAnim(playerRight)
ghostDown  = ghostifyAnim(playerDown)
ghostSprite  = ghostIdle

# TILE SPRITES
wallSprite  = loadSprite("images\\wall.png")    
emptySprite = loadSprite("images\\empty.png")
goalSprite  = loadSprite("images\\goal.png")
swirlSprite = loadSprite("images\\swirl.png")

# CENTERPIECE SPIRTES
centerPillar = loadSprite("images\\centerPillar.png")
# pixel positions
centerPositions = [(295, 400), (400, 295), (485, 400), (400, 485)]
# normal sprites
centerGrey = [loadSprite("images\\centerLeft.png"),
              loadSprite("images\\centerUp.png"),
              loadSprite("images\\centerRight.png"),
              loadSprite("images\\centerDown.png")]
# wall of normal sprites
centerGreySides = [loadSprite("images\\centerLeftSide.png"),
                   loadSprite("images\\centerUpSide.png"),
                   loadSprite("images\\centerRightSide.png"),
                   loadSprite("images\\centerDownSide.png")]

# returns a new sprite with recolored surfaces
def recolor(surface, fromColor, toColor):
    newSurface = copy.copy(surface)
    pixels = pygame.PixelArray(newSurface)
    pixels = pixels.replace(fromColor, toColor)
    del pixels
    return newSurface

# the other sprites are just recolors of the originals
centerRed = []
centerWhite = []
for sprite in centerGrey:
    centerRed.append(recolor(sprite, (53, 53, 53), (147, 44, 44)))
    centerWhite.append(recolor(sprite, (53, 53, 53), (230, 230, 230)))
    
centerRedSides = []
centerWhiteSides = []
for sprite in centerGreySides:
    centerRedSides.append(recolor(sprite, (35, 35, 35), (87, 30, 30)))
    centerWhiteSides.append(recolor(sprite, (35, 35, 35), (212, 212, 212)))

# keeps track of current centerpiece colors
centerColor = [None, None, None, None]
centerColorSides = [None, None, None, None]



### CAMERA STUFF ###
camX = 0      # camera coordinates
camY = 0
camXLock = 0  # counts how long the camera should stay in a direction
camYLock = 0
CAMLIMIT = 45 # the furthest the camera should move



### ANIMATION STUFF ###
moveLock = 0  # makes sure you can only move every certain amount of frames

MOVELENGTH  = 8          # the length of the animation
moveFrame   = MOVELENGTH # stores what frame of the animation you're on
SWIRLLENGTH = 18          # dungeon rotation
swirlFrame  = SWIRLLENGTH

################################# you gotta do this later
WINANIMLENGTH = 80
winAnimFrame = 0

PLAYERGOALLENGTH = 20     # player sinking into goal hole
playerGoalFrame  = PLAYERGOALLENGTH
MOVECURRLENGTH = 30       # current level flying up after beating level
moveCurrFrame  = MOVECURRLENGTH
MOVENEXTLENGTH = 20       # next level moving up after beating level
moveNextFrame  = MOVENEXTLENGTH
LEVELWINLENGTH = PLAYERGOALLENGTH + MOVECURRLENGTH + MOVENEXTLENGTH
levelWinFrame  = LEVELWINLENGTH

CENTERPRESSLENGTH = 30    # centerpiece buttons being pressed
centerPressFrames = [CENTERPRESSLENGTH for x in range(4)]

# THE CIRCLE THAT THE DUNGEONS ROTATE ON
swirlRadius = TILE * 5 + MARG
swirlCenterX = TILE * 5 + MARG * 2
swirlCenterY = TILE * 5 + MARG * 2

clock = pygame.time.Clock() # a Clock keeps the framerate constant



### LOAD LEVELS (FROM FILES) ###
# the level files use these letters to represent the tiles
E = EMPTY
W = WALL
G = GOAL
S = SWIRL

levels = []
for file in os.listdir("levels\\"): # loads all levels
    levelFile = open("levels\\" + file, "r")
    levelFile = levelFile.read()

    # SPLIT THE TILES IN THE FILE, AND CONVERT EACH INTO A NUMBER
    levelFile = levelFile.split()
    for x in range(len(levelFile)):
        levelFile[x] = eval(levelFile[x])

    # INITIATES LEVEL AS ALL 0's, dimensions are dungeon x row x column
    levelLoaded = [[[0, 0, 0, 0, 0] for row in range(5)] for dung in range(4)]

    # PULLS SLICES FROM THE FILE INTO THE LEVEL
    for row in range(5):        # up is on the first 5 rows
        levelLoaded[   UP][row] = levelFile[row*5 : (row + 1)*5]

    for row in range(5, 14, 2): # left and right share rows, so they alternate
        levelLoaded[ LEFT][(row - 5) // 2] = levelFile[row*5 : (row + 1)*5]
    for row in range(6, 15, 2):
        levelLoaded[RIGHT][(row - 5) // 2] = levelFile[row*5 : (row + 1)*5]

    for row in range(15, 20):   # bottom is on the last 5 rows
        levelLoaded[ DOWN][(row - 15)] = levelFile[row*5 : (row + 1)*5]

    levelLoaded += levelFile[100 : 103] # adds the starting position to the end
    levels.append(levelLoaded) # adds it to the level list
    
# SETS UP LEVEL 0
levelNum = 0
def resetLevel():
    global level
    global playerDung, playerCol, playerRow
    levelInfo = levels[levelNum]
    level = levelInfo[0 : 4]  # tiles are items 0-3
    playerDung = levelInfo[4] # player's starting position are items 4-6
    playerCol  = levelInfo[5]
    playerRow  = levelInfo[6]

    global camXLock, camYLock
    camXLock = 0
    camYLock = 0
    
resetLevel()



# DRAWING LEVELS
# a field of empty tiles
emptyDung = pygame.Surface((TILE*5, TILE*6))
for row in range(5):
    for col in range(5):
        emptyDung.blit(emptySprite, (col * TILE, row * TILE))

dungSurface = pygame.Surface((TILE*5, TILE*6))
def drawDung(dest, levelToDraw, dungNum, x, y):
    # initiates the surface
    global dungSurface
    dungSurface.fill((0, 0, 0))
    dungSurface.blit(emptyDung, (0, 0))

    # blits each tile
    for rowNum, row in enumerate(levelToDraw[dungNum]):
        for colNum, tile in enumerate(row):

            # calculate the tile's pixel position
            tileX = colNum * TILE
            tileY = rowNum * TILE

            if tile == WALL:
                dungSurface.blit( wallSprite, (tileX, tileY))
            elif tile == GOAL:
                dungSurface.blit( goalSprite, (tileX, tileY))
            elif tile == SWIRL:
                dungSurface.blit(swirlSprite, (tileX, tileY))

        if levelToDraw == level:
            if rowNum == playerRow:
                playerX = (playerCol - 1) * TILE
                playerY = (playerRow - 1) * TILE

                # drops the player during the win animation
                if moveCurrFrame != MOVECURRLENGTH:
                    playerY += playerGoalFrame * playerGoalMultiplier
                    
                # decides whether to draw the ghost or the real player
                if playerDung == dungNum:
                    dungSurface.blit(playerSprite, (playerX, playerY))
                else:
                    dungSurface.blit( ghostSprite, (playerX, playerY))

                # properly layers the empty tile below player during level win
                if moveCurrFrame != MOVECURRLENGTH and moveFrame == MOVELENGTH:
                    if playerRow != DUNGSIZE - 1:
                        if level[dungNum][playerRow + 1][playerCol] == EMPTY:
                            tileX = playerCol * TILE
                            tileY = (playerRow + 1) * TILE
                            dungSurface.blit(emptySprite, (tileX, tileY))

    dest.blit(dungSurface, (x, y))

nextLevel = pygame.Surface((850, 850))
dungX = copy.copy(defaultDungX)
dungY = copy.copy(defaultDungY)

#################
### GAME LOOP ###
#################
running = True
while running:
    
    ##############################
    ### INPUT AND CALCULATIONS ###
    ##############################

    # LOCKS YOU FROM MOVING WHILE YOU ARE MOVING
    if moveLock <= 0:
        keys = pygame.key.get_pressed()

        ### MOVEMENT ###
        triedToMove = True
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            
            # queries where the player wants to move to
            queryDung = LEFT
            queryCol  = playerCol - 1
            queryRow  = playerRow
            
            # starts the camera lock timer
            camXLock = 60

        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            queryDung = RIGHT # same for the other directions
            queryCol  = playerCol + 1
            queryRow  = playerRow
            camXLock = 60

        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            queryDung = UP
            queryCol  = playerCol
            queryRow  = playerRow - 1
            camYLock = 60

        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            queryDung = DOWN
            queryCol  = playerCol
            queryRow  = playerRow + 1
            camYLock = 60

        else:
            triedToMove = False

        if triedToMove:
            moveDir = queryDung # tracks direction the player tried to move
            
            centerPressFrames[moveDir] = 0 # starts centerpiece animation
            centerColor[moveDir] = centerRed[moveDir] # defaults color to red
            centerColor[moveDir].set_alpha(255)
            centerColorSides[moveDir] = centerRedSides[moveDir]
            centerColorSides[moveDir].set_alpha(255)
                    
            # move if the space is not out of bounds, and not a wall
            query = (queryDung, queryCol, queryRow)
            if -1 not in query and DUNGSIZE not in query:

                tileType = level[queryDung][queryRow][queryCol]
                if tileType != WALL:
                    
                    # start the movement animation and lock your movement
                    moveLock = 8
                    moveFrame = 0

                    # changes the red to white
                    centerColor[moveDir] = centerWhite[moveDir]
                    centerColor[moveDir].set_alpha(255)
                    centerColorSides[moveDir] = centerWhiteSides[moveDir]
                    centerColorSides[moveDir].set_alpha(255)
                    
                    # update the player to the queried position
                    playerDung = queryDung 
                    playerCol  = queryCol
                    playerRow  = queryRow

                    

                    ### DUNGEON ROTATION ###
                    if tileType == SWIRL:
                        level.insert(0, level[3])
                        del level[4]

                        # rotates the player
                        playerDung = (playerDung + 1) % 4

                        # starts dungeon rotation animation
                        swirlFrame = 0
                        moveLock  += SWIRLLENGTH
                        angleMultiplier = -1 # allows for S M O O T H rotation

                        
                            
                    ### LEVEL CLEAR ###
                    elif tileType == GOAL:
                        # stops program on last level
                        if levelNum == len(levels) - 1:
                            running = False
                            
                        # otherwise, load the next level
                        else:
                            # starts all the animations after beating a level
                            winAnimFrame = 0
                            playerGoalFrame = 0
                            moveCurrFrame = 0
                            moveNextFrame = 0
                            moveLock += PLAYERGOALLENGTH
                            moveLock += MOVECURRLENGTH
                            moveLock += MOVENEXTLENGTH

                            playerGoalMultiplier = 2
                            moveCurrMultiplier = -20
                            moveNextMultiplier = 3

                            nextY = 20

                            # pre-draws the next level
                            for dung in range(4):
                                drawDung(nextLevel, levels[levelNum + 1], dung, dungX[dung], dungY[dung])

                            # resets the camera
                            camXLock = 0
                            camYLock = 0



        # oh, and reset the level if r is pressed
        if keys[pygame.K_r]:
            resetLevel()

    else:
        # counts down until you are finally free to move again
        moveLock -= 1 

    # stops the game when the window is closed
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False



    ##############################
    ### ANIMATION CALCULATIONS ###
    ##############################

    ### FRAME COUNTING ### (these animations are in order of priority
    if moveFrame != MOVELENGTH: 
        moveFrame += 1

    elif swirlFrame != SWIRLLENGTH:
        swirlFrame += 1

    elif playerGoalFrame != PLAYERGOALLENGTH:
        playerGoalFrame += 1

    elif moveCurrFrame != MOVECURRLENGTH:
        moveCurrFrame += 1

        # resets player position after current level flies away
        if moveCurrFrame == MOVECURRLENGTH:
            playerDung = levels[levelNum + 1][4]
            playerCol = levels[levelNum + 1][5]
            playerRow = levels[levelNum + 1][6]

    elif moveNextFrame != MOVENEXTLENGTH:
        moveNextFrame += 1
                    
        # after the animation is done, increment the level
        if moveNextFrame == MOVENEXTLENGTH:
            levelNum += 1
            resetLevel()

    for dung in range(4): # centerpiece animation
        if centerPressFrames[dung] != CENTERPRESSLENGTH:
            centerPressFrames[dung] += 1
        else:
            centerColor[dung] = None
            centerColorSides[dung] = None

    # MOVEMENT ANIMATION               
    if moveFrame != MOVELENGTH:
        if moveDir == LEFT: # sets animation based on what move was made
            playerSprite = playerLeft[moveFrame]
            ghostSprite  =  ghostLeft[moveFrame]
            
        elif moveDir == RIGHT:
            playerSprite = playerRight[moveFrame]
            ghostSprite  =  ghostRight[moveFrame]

        elif moveDir == DOWN:
            playerSprite = playerDown[moveFrame]
            ghostSprite  =  ghostDown[moveFrame]

        elif moveDir == UP:
            playerSprite = playerUp[moveFrame]
            ghostSprite  =  ghostUp[moveFrame]
    else:
        playerSprite = playerIdle # resets animation to idle
        ghostSprite  = ghostIdle

    # CENTERPIECE ANIMATION
    for dung in range(4):
        if centerColor[dung]:
            alpha = 255 - centerPressFrames[dung] * 8
            centerColor[dung].set_alpha(alpha)
            centerColorSides[dung].set_alpha(alpha)
    
    # DUNGEON ROTATION ANIMATION
    if swirlFrame != SWIRLLENGTH:
        angleMultiplier += 0.24 # S M O O T H   A N I M A T I O N

        # circle calculations and stuff
        for dung in range(4):
            angle  = (dung + 1) * 90 % 360   # dungeon's original angle
            angle += swirlFrame * angleMultiplier # offset based on frame
            angle  = math.radians(angle)     # make it cos/sin-patable

            # calculate where it is on the circle based on its angle
            dungX[dung] = swirlCenterX + math.cos(angle) * swirlRadius
            dungY[dung] = swirlCenterY + math.sin(angle) * swirlRadius

    # LEVEL WIN MOVEMENT
    elif moveNextFrame != MOVENEXTLENGTH:
        if moveCurrFrame == MOVECURRLENGTH:
            moveNextMultiplier -= 0.3
            
        if moveCurrFrame != MOVECURRLENGTH:
            moveCurrMultiplier += 2
            
        # moves the next dungeon
        nextY = 0 + (MOVENEXTLENGTH - moveNextFrame) * moveNextMultiplier
        print(nextY)
        
        # moves the current dungeon
        for dung in range(4):
            dungY[dung] = defaultDungY[dung] - (moveCurrFrame * moveCurrMultiplier)
            
    else: # reset dungeon positions
        dungX = copy.copy(defaultDungX)
        dungY = copy.copy(defaultDungY)



    ##########################
    ### DRAWING EVERYTHING ###
    ##########################

    # DRAWS NEXT LEVEL DURING WIN ANIMATION
    if moveNextFrame != MOVENEXTLENGTH:
        # changes its transparency
        nextLevel.set_alpha(moveCurrFrame * 5 + moveNextFrame * 8)
        SCENE.blit(nextLevel, (0, nextY))

        # draws player falling from the sky
        for dung in range(4):
            playerX = defaultDungX[dung] + (playerCol - 1) * TILE
            playerY = defaultDungY[dung] + (playerRow - 1) * TILE
            playerY -= (MOVENEXTLENGTH - moveNextFrame) * 50

            if playerDung == dung:
                SCENE.blit(playerSprite, (playerX, playerY))
            else:
                SCENE.blit(ghostSprite, (playerX, playerY))



    # DUNGEONS (bottom dungeon is layered on top of the centerpiece)
    drawDung(SCENE, level,  LEFT, dungX[LEFT],  dungY[LEFT])
    drawDung(SCENE, level,    UP, dungX[UP],    dungY[UP])
    drawDung(SCENE, level, RIGHT, dungX[RIGHT], dungY[RIGHT])
    
    # CENTERPIECE
    for dung in range(4):
        SCENE.blit(centerGreySides[dung], centerPositions[dung])
        SCENE.blit(centerGrey[dung], centerPositions[dung])
        
        # draws the color arrow overtop of the grey arrow
        if centerColor[dung]:
            SCENE.blit(centerColorSides[dung], centerPositions[dung])
            SCENE.blit(centerColor[dung], centerPositions[dung])
            
        # draws centerpiece overtop of the up dungeon
        if dung == 1:
            SCENE.blit(centerPillar, (385, 370))

    # BOTTOM DUNGEON
    drawDung(SCENE, level, DOWN, dungX[DOWN], dungY[DOWN])



    ### CAMERA MOVEMENT ###
    if camXLock: # MOVES THE CAMERA ALONG X AXIS
        camXLock -= 1

        if moveDir == LEFT:
            camX -= (CAMLIMIT + camX) * 0.1
        elif moveDir == RIGHT:
            camX += (CAMLIMIT - camX) * 0.1
            
    elif camX != 0: # resets the x axis
        camX -= camX * 0.1

    if camYLock: # MOVES THE CAMERA ALONG Y AXIS
        camYLock -= 1

        if moveDir == UP:
            camY -= (CAMLIMIT + camY) * 0.1
        elif moveDir == DOWN:
            camY += (CAMLIMIT - camY) * 0.1
            
    elif camY != 0: # resets the y axis
        camY -= camY * 0.1



    ### RENDERING SCREEN ###
    DISPLAY.blit(SCENE, (-camX, -camY))
    pygame.display.flip()   # display the screen
    DISPLAY.fill((0, 0, 0)) # clear the screen
    SCENE.fill((0, 0, 0))
    clock.tick(60)          # keeps the FPS at 60
    #print(clock.get_fps())

# QUITTING STUFF
pygame.quit()
sys.exit()
