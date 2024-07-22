from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import numpy as np
import drone_model as dm
import projection_math as pm
import physics_engine as pe

pygame.init()
pygame.display.set_caption("drone simulator")
pygame.display.set_icon(pygame.image.load("./drone_simulation/drone_icon.png"))

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bg_color = (255, 255, 255)

# SCREEN PARAMETERS
canonical_near_plane_center = np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0], dtype=float)
near_plane_center = np.array([0, 0, 50, 1], dtype=float)
canonical_volume_size = np.array([SCREEN_WIDTH, SCREEN_HEIGHT, 100], dtype=float)
orthographic_volume_size = np.array([50, 50, 50], dtype=float)
viewer_scene_distance = 10

orthographic_volume_center = \
    near_plane_center + np.array([0, 0, orthographic_volume_size[2] / 2, 0], dtype=float)

pr = pm.Projector(
    canonical_near_plane_center=canonical_near_plane_center,
    near_plane_center=near_plane_center,
    canonical_volume_size=canonical_volume_size,
    orthographic_volume_size=orthographic_volume_size,
    viewer_scene_distance=viewer_scene_distance
)

drone = dm.Drone(orthographic_volume_center, 50, pr)

def draw_simulator_state():
    screen.fill(bg_color)
    drone.draw_to_(screen)
    pygame.display.flip()

drone.rotate(-15, [0, 0, 1])
drone.rotate(-15, [1, 0, 0])
drone.rotate(-145, [0, 1, 0])

running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
    if not running: break

    drone.rotate(-0.03, [0, 1, 0])
    #drone.rotate(-0.15, [1, 0, 0])
    drone.motor_set_force_percent(0, -1)
    drone.motor_set_force_percent(1, 1)
    drone.motor_set_force_percent(2, -1)
    drone.motor_set_force_percent(3, 1)
    drone.update()

    draw_simulator_state()