#########################
### DIRECTIONDUNGEON! ###
#########################
### todo
# camera                      DONE
# centerpiece
# movement animations         DONE, LEFT/RIGHT COULD BE IMPROVED
# dungeon rotation animation  DONE, MIGHT NEED TO BE FASTER THOUGH
# level clear animation
# should bottom wall partially cover the bottom tile?
# different perspectives for each dungeon?
# keys?
# levels: probably 64, since it's 4 cubed, and because of 4 button menu
# main menu
# pause function
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



### LOAD IMAGES ###
# LOADS A SPRITE FROM FILE (also resizes it to 5x the size)
def loadSprite(filePath):
    file = pygame.image.load(filePath)
    
    w = file.get_width()
    h = file.get_height()
    file = pygame.transform.scale(file, (w * 5, h * 5))
    
    file.convert_alpha()
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
    
    alphaSurface = pygame.Surface(ghost.get_rect().size, pygame.SRCALPHA)
    alphaSurface.fill((255, 255, 255, 100))
    
    ghost.blit(alphaSurface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return(ghost)

# MAKES AN ANIMATION TRANSPARENT
def ghostifyAnim(anim):
    ghostAnim = []
    for image in anim:
        ghostAnim.append(ghostify(image))
        
    return(ghostAnim)

playerIdle  = loadSprite("images\\player.png")  # player sprites
playerLeft  = loadAnimation("images\\moveLeft\\")
playerRight = loadAnimation("images\\moveRight\\")
playerDown  = loadAnimation("images\\moveDown\\")
playerUp    = loadAnimation("images\\moveUp\\")

ghostIdle  = ghostify(playerIdle)    # ghosts are just a transparent player
ghostLeft  = ghostifyAnim(playerLeft)
ghostRight = ghostifyAnim(playerRight)
ghostDown  = ghostifyAnim(playerDown)
ghostUp    = ghostifyAnim(playerUp)

wallSprite  = loadSprite("images\\wall.png")    # tile sprites
emptySprite = loadSprite("images\\empty.png")
goalSprite  = loadSprite("images\\goal.png")
swirlSprite = loadSprite("images\\swirl.png")

playerSprite = playerIdle # stores which sprite is currently being drawn
ghostSprite  = ghostIdle



### CONSTANTS AND STUFF ###
# DUNGEON CONSTANTS (each of the four 5x5 areas is called a "dungeon")
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

# TILE TYPES
E = 0 # EMPTY
W = 1 # WALL
G = 2 # GOAL
S = 3 # SWIRL

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
# MMMMMMMMMMMMM     The below equations represent how many Margins and how many
# MTTTM...MTTTM     Tiles there are before a certain wall.
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

dungX = copy.copy(defaultDungX)
dungY = copy.copy(defaultDungY)

# each dungeon gets drawn onto its own surface
dungSurfaces = [pygame.Surface((TILE * 5, TILE * 6)) for x in range(4)]



### ANIMATION STUFF ###
camX = 0      # camera coordinates
camY = 0
camXLock = 0  # counts how long the camera should stay in a direction
camYLock = 0
CAMLIMIT = 45 # the furthest the camera should move

moveLock = 0  # makes sure you can only move every certain amount of frames

MOVELENGTH  = 8          # the length of the animation
moveFrame   = MOVELENGTH # stores what frame of the animation you're on
SWIRLLENGTH = 18          # dungeon rotation
swirlFrame  = SWIRLLENGTH
PLAYERDROPLENGTH = 20
playerDropFrame  = PLAYERDROPLENGTH
PREVWINLENGTH = 20        # previous level flying up after beating level
prevWinFrame  = PREVWINLENGTH
CURRWINLENGTH = 20        # current level moving up after beating level
currWinFrame  = CURRWINLENGTH

prevLevel = None # stores the level that is flying up during win animation

# THE CIRCLE THAT THE DUNGEONS ROTATE ON
swirlRadius = TILE * 5 + MARG
swirlCenterX = TILE * 5 + MARG * 2
swirlCenterY = TILE * 5 + MARG * 2

clock = pygame.time.Clock() # a Clock keeps the framerate constant



### LOAD LEVELS (FROM FILES) ###
levels = []
for file in os.listdir("levels\\"): # loads all levels
    levelFile = open("levels\\" + file, "r")
    levelFile = levelFile.read()

    # SPLIT THE TILES IN THE FILE, AND CONVERT EACH INTO A NUMBER
    levelFile = levelFile.split()
    for x in range(len(levelFile)):
        levelFile[x] = eval(levelFile[x])

    # INITIATES LEVEL AS ALL 0's, dimensions are dungeon x row x column
    levelLoaded = [[[0, 0, 0, 0, 0] for row in range(5)] for dungeon in range(4)]

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

# GAME LOOP
running = True
while running:
    
    ##############################
    ### INPUT AND CALCULATIONS ###
    ##############################

    # LOCKS YOU FROM MOVING WHILE YOU ARE MOVING
    if moveLock <= 0:
        keys = pygame.key.get_pressed()

        ### MOVEMENT ###
        movement = True
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
            movement = False

        if movement:
            moveDir = queryDung # tracks direction the player tried to move

            # move if the space is not out of bounds, and not a wall
            query = (queryDung, queryCol, queryRow)
            if -1 not in query and DUNGSIZE not in query:

                tileType = level[queryDung][queryRow][queryCol]
                if tileType != W:
                    # start the movement animation and lock your movement
                    moveLock = 8
                    moveFrame = 0
                    
                    # update the player to the queried position
                    playerDung = queryDung 
                    playerCol  = queryCol
                    playerRow  = queryRow

                    

                    ### DUNGEON ROTATION ###
                    if tileType == S:
                        level.insert(0, level[3])
                        del level[4]

                        # rotates the player
                        playerDung = (playerDung + 1) % 4

                        # starts dungeon rotation animation
                        swirlFrame = 0
                        moveLock  += SWIRLLENGTH
                        angleMultiplier = -1 # allows for S M O O T H rotation

                        
                            
                    ### LEVEL CLEAR ###
                    elif tileType == G:
                        # stops program on last level
                        if levelNum == len(levels) - 1:
                            running = False
                            
                        # otherwise, load the next level
                        else:
                            # starts animation
                            prevLevel = level

                            playerDropFrame = 0
                            prevWinFrame = 0
                            currWinFrame = 0
                            moveLock += PREVWINLENGTH + CURRWINLENGTH

                            playerDropMultiplier = 2
                            prevLevelMultiplier = -20
                            currLevelMultiplier = 2
                            
                            # loads next level
                            levelNum += 1
                            resetLevel()



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



    #####################
    ### DRAWING STUFF ###
    #####################

    ### ANIMATION CALCULATIONS ###

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
            
        moveFrame += 1 # counts to the next frame

    else: # resets animation to idle
        playerSprite = playerIdle
        ghostSprite  = ghostIdle

        # starts rotation after movement
        if swirlFrame != SWIRLLENGTH:
            swirlFrame += 1

        elif playerDropFrame != PLAYERDROPLENGTH:
            playerDropFrame += 1

        else:
            # starts win animation after movement
            if prevWinFrame != PREVWINLENGTH:
                prevWinFrame += 1
                
            # moves current level after previous level is done moving
            else:
                if currWinFrame != CURRWINLENGTH:
                    currWinFrame += 1

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
            
    else: # reset dungeon positions
        dungX = copy.copy(defaultDungX)
        dungY = copy.copy(defaultDungY)



    ### DRAWING EVERYTHING ###

    # DRAWS EACH DUNGEON ON A SEPERATE SURFACE
    for dungNum, surface in enumerate(dungSurfaces):

        # draws all non-wall blocks first
        for rowNum, row in enumerate(level[dungNum]):
            for colNum, tile in enumerate(row):
                
                # calculate the tile's position
                tileX = colNum * TILE
                tileY = rowNum * TILE

                # draws sprite based on the tile type
                if tile == E:
                    surface.blit(emptySprite, (tileX, tileY))
                elif tile == G:
                    surface.blit( goalSprite, (tileX, tileY))
                elif tile == S:
                    surface.blit(swirlSprite, (tileX, tileY))

        # then draws all the walls, and the player
        for rowNum, row in enumerate(level[dungNum]):
            for colNum, tile in enumerate(row):
                tileX = colNum * TILE
                tileY = rowNum * TILE
                
                if tile == W:
                    surface.blit( wallSprite, (tileX, tileY))

            # player is drawn after the row is done to prevent clipping
            if rowNum == playerRow:
                playerX = (playerCol - 1) * TILE
                playerY = (playerRow - 1) * TILE
                
                # draws real player at the dungeon they're in
                if playerDung == dungNum:
                    surface.blit(playerSprite, (playerX, playerY))
                    
                # draws ghost player at every dungeon they're not in
                else:
                    surface.blit( ghostSprite, (playerX, playerY))

    # BLITS EACH DUNGEON TO THE SCENE
    for dung, surface in enumerate(dungSurfaces):
        xPos = dungX[dung]
        yPos = dungY[dung]

        # DURING WIN ANIMATION
        if currWinFrame != CURRWINLENGTH:
            # move the dungeon up (if the previous dungeon has already moved)
            yPos += (CURRWINLENGTH - currWinFrame) * currLevelMultiplier
            if currWinFrame:
                currLevelMultiplier -= 0.02

            # make it transparent, depending on the frame
            surface.set_alpha(prevWinFrame * 5 + currWinFrame * 8)
                
        SCENE.blit(surface, (xPos, yPos))
        surface.fill((0, 0, 0))



    # PREVIOUS LEVEL FLYING AWAY DURING WIN ANIMATION
    if prevWinFrame != PREVWINLENGTH:
        for dungNum, dung in enumerate(prevLevel):
            for rowNum, row in enumerate(dung):
                for colNum, tile in enumerate(row):
                    tileX = dungX[dungNum] + colNum * TILE
                    tileY = dungY[dungNum] + rowNum * TILE
                    tileY -= prevWinFrame * prevLevelMultiplier
                    
                    if tile == E:
                        SCENE.blit(emptySprite, (tileX, tileY))
                    elif tile == W:
                        SCENE.blit( wallSprite, (tileX, tileY))
                    elif tile == G:
                        SCENE.blit( goalSprite, (tileX, tileY))
                    elif tile == S:
                        SCENE.blit(swirlSprite, (tileX, tileY))
                        
            # player is drawn after the row is done to prevent clipping
            if rowNum == playerRow:
                playerX = (playerCol - 1) * TILE
                playerY = (playerRow - 1) * TILE

                if playerDropFrame != PLAYERDROPLENGTH:
                    playerY += playerDropFrame
                    print(playerY)
                
                # draws real player at the dungeon they're in
                if playerDung == dungNum:
                    surface.blit(playerSprite, (playerX, playerY))
                    
                # draws ghost player at every dungeon they're not in
                else:
                    surface.blit( ghostSprite, (playerX, playerY))
           
        prevLevelMultiplier += 3



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
