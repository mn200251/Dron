import pygame
import numpy as np
import drone_model as dm

pygame.init()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bg_color = (255, 255, 255)

camera_position = np.array([0, SCREEN_HEIGHT, 0, 1])
space_coordinate_system_base = np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 10, 1])

def create_projection_matrix(fov_angel, aspect, znear, zfar):
    return np.array([
        [aspect / np.tan(fov_angel / 2), 0, 0, 0],
        [0, 1 / np.tan(fov_angel / 2), 0, 0],
        [0, 0, zfar / (zfar - znear), - zfar * znear / (zfar - znear)],
        [0, 0, 1, 0]
    ])
projection_matrix =  create_projection_matrix(np.pi/4, 1, 0, 30)

def project_to_camera_screen(vector_in_camera_space):
    vector_in_camera_space = projection_matrix.dot(vector_in_camera_space)
    if vector_in_camera_space[3] > 0.00000001:
        vector_in_camera_space /= vector_in_camera_space[3]
    vector_in_camera_space += space_coordinate_system_base
    return np.array([camera_position[0] + vector_in_camera_space[0], camera_position[1] - vector_in_camera_space[1]])

origin = project_to_camera_screen(np.array([0, 0, 0, 1]))
base_x = project_to_camera_screen(np.array([50, 0, 0, 1]))
base_y = project_to_camera_screen(np.array([0, 50, 0, 1]))
base_z = project_to_camera_screen(np.array([0, 0, 50, 1]))

a = 50
A_raw = np.array([-a, 0, 0, 1.])
B_raw = np.array([a, 0, 0, 1.])
C_raw = np.array([0, a * np.sqrt(3), 0, 1.])
D_raw = np.array([0, a * np.sqrt(3) / 3, a * 2 * np.sqrt(6) / 3 , 1.])

zoffset = np.array([0, 0, a * np.sqrt(3) / 3, 0])
A_raw += zoffset
B_raw += zoffset
C_raw += zoffset
D_raw += zoffset

xrot_angle = 0
xrot_angle = xrot_angle * np.pi / 180
Rx = np.array([
    [1, 0, 0, 0],
    [0, np.cos(xrot_angle), -np.sin(xrot_angle), 0],
    [0, np.sin(xrot_angle), np.cos(xrot_angle), 0],
    [0, 0, 0, 1],
])

yrot_angle = 10
yrot_angle = yrot_angle * np.pi / 180
Ry = np.array([
    [np.cos(yrot_angle), 0, np.sin(yrot_angle), 0],
    [0, 1, 0, 0],
    [-np.sin(yrot_angle), 0, np.cos(yrot_angle), 0],
    [0, 0, 0, 1]
])

zrot_angle = 0
zrot_angle = zrot_angle * np.pi / 180
Rz = np.array([
    [np.cos(zrot_angle), -np.sin(zrot_angle), 0, 0],
    [np.sin(zrot_angle), np.cos(zrot_angle), 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])

rotation_matrix = Rx.dot(Ry.dot(Rz))


running = True
val = 250
cnt = val

A = project_to_camera_screen(A_raw)
B = project_to_camera_screen(B_raw)
C = project_to_camera_screen(C_raw)
D = project_to_camera_screen(D_raw)
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
    if not running: break

    if (cnt == 0):
        A_raw = rotation_matrix.dot(A_raw)
        B_raw = rotation_matrix.dot(B_raw)
        C_raw = rotation_matrix.dot(C_raw)
        D_raw = rotation_matrix.dot(D_raw)
        A = project_to_camera_screen(A_raw)
        B = project_to_camera_screen(B_raw)
        C = project_to_camera_screen(C_raw)
        D = project_to_camera_screen(D_raw)
        print("RAW  A,B,C,D:")
        print(A_raw)
        print(B_raw)
        print(C_raw)
        print(D_raw)
        cnt = val
    cnt -= 1
    if cnt == val - 1:
        print("A,B,C,D:")
        print(A)
        print(B)
        print(C)
        print(D)


    screen.fill(bg_color)
    pygame.draw.line(screen, (0, 0, 0), tuple(origin), tuple(base_x))
    pygame.draw.line(screen, (0, 0, 0), tuple(origin), tuple(base_y))
    pygame.draw.line(screen, (0, 0, 0), tuple(origin), tuple(base_z))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(B[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(B[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(C[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(B[:2]), tuple(C[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(B[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(C[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple((A[:2] + B[:2]) / 2), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple((A[:2] + B[:2]) / 2), tuple(C[:2]))
    pygame.display.flip()



