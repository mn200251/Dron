import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import numpy as np
import drone_model as dm
import projection_math as pm
import physics_engine as pe
import ground_model as gm

pygame.init()
pygame.font.init()
text_font = pygame.font.SysFont("Comic Sans MS", 15)
pygame.display.set_caption("drone simulator")
pygame.display.set_icon(pygame.image.load("./drone_simulation/drone_icon.png"))

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bg_color = (255, 255, 255)

# SCREEN PARAMETERS
canonical_near_plane_center = np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0], dtype=float)
near_plane_center = np.array([0, 0, 50, 1], dtype=float)
#canonical_volume_size = np.array([2 * SCREEN_WIDTH, 2 * SCREEN_HEIGHT, 100], dtype=float)
zoom = 1
canonical_volume_size = np.array([zoom * SCREEN_WIDTH, zoom * SCREEN_HEIGHT, 100], dtype=float)
orthographic_volume_size = np.array([50, 50, 50], dtype=float)
viewer_scene_distance = 20
zoom_text_surface = text_font.render(f"zoom: {int(zoom * 100)}%", False, (0, 0, 0))

orthographic_volume_center = \
    near_plane_center + np.array([0, 0, orthographic_volume_size[2] / 2, 0], dtype=float)

ground_center = orthographic_volume_center + np.array([0, orthographic_volume_size[1] / 2, 0, 0])

pr = pm.Projector(
    canonical_near_plane_center=canonical_near_plane_center,
    near_plane_center=near_plane_center,
    canonical_volume_size=canonical_volume_size,
    orthographic_volume_size=orthographic_volume_size,
    viewer_scene_distance=viewer_scene_distance
)

#pe.load_parameters()

drone = dm.Drone(orthographic_volume_center, 20, pr)
ground = gm.Ground(ground_center, 2 * orthographic_volume_size[0], 2 * orthographic_volume_size[2], 2, 20, pr)


mouse_pos1 = None
def mouse_rotate():
    if mouse_pos1 is None or not pygame.mouse.get_pressed()[0]: return
    if mouse_pos1 == pygame.mouse.get_pos(): return
    mouse_pos2 = pygame.mouse.get_pos()
    drone_center = pr.p2_canonical(drone.drone_center)
    u = np.array([mouse_pos2[0] - drone_center[0], mouse_pos2[1] - drone_center[1], 40, 1])
    v = np.array([mouse_pos1[0] - drone_center[0], mouse_pos1[1] - drone_center[1], 40, 1])
    unit_vector = pe.cross_product(u, v)
    unit_vector = pe.normalize_vector(unit_vector)
    rotation_angle = np.log2(pe.angle_between_vectors(u, v))
    rotation_angle = max(min(rotation_angle, 1.5), 0.2)
    drone.rotate(rotation_angle, unit_vector)
    if pygame.mouse.get_pressed()[2]:
        ground.rotate(rotation_angle, unit_vector)

running = True
def user_input_handling():
    for event in pygame.event.get():
        global running; global zoom; global canonical_volume_size; global mouse_pos1; global zoom_text_surface
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1 and zoom < 3: zoom += 0.1
            if event.y == -1 and zoom > 0.2: zoom -= 0.1
            zoom_text_surface = text_font.render(f"zoom: {int(zoom * 100)}%", False, (0, 0, 0))
            canonical_volume_size = np.array([zoom * SCREEN_WIDTH, zoom * SCREEN_HEIGHT, 100], dtype=float)
            pr.set_canonical_volume_size(canonical_volume_size)
        if event.type == pygame.MOUSEBUTTONDOWN: mouse_pos1 = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONUP: mouse_pos1 = None
    if mouse_pos1 is not None: mouse_rotate()

def draw_simulator_state():
    screen.fill(bg_color)
    ground.draw_to_(screen)
    drone.draw_to_(screen)
    screen.blit(zoom_text_surface, (SCREEN_WIDTH - 100, 0))
    pygame.display.flip()

simulation_initialized = False
def initialize_simulation():
    global simulation_initialized
    if simulation_initialized: return
    simulation_initialized = True
    drone.rotate(-15, [0, 0, 1])
    drone.rotate(-15, [1, 0, 0])
    drone.rotate(-145, [0, 1, 0])

    #ground.rotate_ground(-15, [0, 0, 1])
    #ground.rotate_ground(15, [0, 0, 1])
    ground.rotate_ground(45, [0, 1, 0])
    ground.rotate_ground(15, [1, 0, 0])
    #ground.rotate(45, [0, 0, 1])
    #ground.rotate(45, [1, 0, 0])

def update():
    drone.rotate(-0.03, [0, 1, 0])
    #ground.rotate(-0.03, [0, 1, 0]) # cool ground rotation
    drone.rotate(-0.15, [1, 0, 0])
    #ground.rotate_ground(-0.03, [0, 1, 0])
    drone.motor_set_power_percent(0, -1)
    drone.motor_set_power_percent(1, 1)
    drone.motor_set_power_percent(2, -1)
    drone.motor_set_power_percent(3, 1)
    drone.update(physics=False)

initialize_simulation()
while running:
    user_input_handling()
    if not running: break
    update()
    draw_simulator_state()