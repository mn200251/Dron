from pygame.locals import *
import statistics
import datetime
import pygame
import socket
import sys

target_host = "178.148.73.92"
target_port = 6969
#target_host = "192.168.1.26"
#target_port = 9999


pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

# Predefined some colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Screen information
SCREEN_WIDTH = 625
SCREEN_HEIGHT = 625

DRONE_IMAGE_SIZE = (100, 100)

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Dron kontrola")


class Drone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("drone.png")
        self.image = pygame.transform.scale(self.image, DRONE_IMAGE_SIZE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.LEFT = "L"
        self.RIGHT = "R"
        self.UP = "U"
        self.DOWN = "D"

        self.speed = 3

    def update(self, next_move):
        if self.rect.left > 0 \
        and next_move[0] == self.LEFT:
            self.rect.move_ip(-self.speed, 0)
        if self.rect.right < SCREEN_WIDTH \
        and next_move[0] == self.RIGHT:
            self.rect.move_ip(self.speed, 0)
        if self.rect.top > 0 \
        and next_move[0] == self.UP:
            self.rect.move_ip(0, -self.speed)
        if self.rect.bottom < SCREEN_HEIGHT \
        and next_move[0] == self.DOWN:
            self.rect.move_ip(0, self.speed)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


drone = Drone()

DISPLAYSURF.fill(WHITE)
drone.draw(DISPLAYSURF)
pygame.display.update()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((target_host, target_port))
client.send("drone".encode("utf-8"))
while True:
    try:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

        response = client.recv(4096).decode("utf-8")
        #response = input("Enter command: ")
        for control in response:
            drone.update(control)
        # drone.update(response)

        DISPLAYSURF.fill(WHITE)
        drone.draw(DISPLAYSURF)

        pygame.display.update()
    except:
        client.connect((target_host, target_port))
        client.send("drone".encode("utf-8"))