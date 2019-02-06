import pygame
import sys
import os

os.environ['SDL_VIDEO_CENTERED'] = '1' # centers the window on the screen

pygame.init()
pygame.display.set_caption('DIRECTIONDUNGEON!')  # window title
postDisplay = pygame.display.set_mode((800, 800))
preDisplay = pygame.Surface((800, 800))

shadow = pygame.Surface((500, 1))
TAHOMA = pygame.font.SysFont("Tahoma", 10)

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    for x in range(4):
        alpha = 255
        for y in range(400):
            alpha -= 255 / 800
            shadow.set_alpha(alpha)
            preDisplay.blit(shadow, (0, y))


    postDisplay.blit(preDisplay, (0, 0))
    clock.tick(60)
    fps = TAHOMA.render(str(round(clock.get_fps())), False, (255, 255, 255))
    postDisplay.blit(fps, (10, 10))

    pygame.display.flip()
    preDisplay.fill((255, 255, 255))
    postDisplay.fill((255, 255, 255))
