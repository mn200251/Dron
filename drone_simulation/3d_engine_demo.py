import pygame
import numpy as np
import drone_model as dm
import projection_math as pm

pygame.init()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bg_color = (255, 255, 255)

pr = pm.Projector(
    canonical_near_plane_center=np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0]),
    near_plane_center=np.array([0, 0, 50, 1], dtype=float),
    #canonical_volume_size=np.array([SCREEN_WIDTH, SCREEN_HEIGHT, 50], dtype=float),
    canonical_volume_size=np.array([SCREEN_WIDTH, SCREEN_HEIGHT, 100], dtype=float),
    orthographic_volume_size=np.array([100, 100, 100], dtype=float),
    viewer_scene_distance=10
)








a = 50
A_raw = np.array([-a, 0, 0, 1.])
B_raw = np.array([a, 0, 0, 1.])
C_raw = np.array([0, a * np.sqrt(3), 0, 1.])
D_raw = np.array([0, a * np.sqrt(3) / 3, a * 2 * np.sqrt(6) / 3 , 1.])

offset = np.array([10, 50, a * np.sqrt(3) / 3, 0]) + np.array([0, 0, 50, 0])
A_raw += offset
B_raw += offset
C_raw += offset
D_raw += offset

xrot_angle = 10
xrot_angle = xrot_angle * np.pi / 180
Rx = np.array([
    [1, 0, 0, 0],
    [0, np.cos(xrot_angle), -np.sin(xrot_angle), 0],
    [0, np.sin(xrot_angle), np.cos(xrot_angle), 0],
    [0, 0, 0, 1],
])

yrot_angle = 0
yrot_angle = yrot_angle * np.pi / 180
Ry = np.array([
    [np.cos(yrot_angle), 0, np.sin(yrot_angle), 0],
    [0, 1, 0, 0],
    [-np.sin(yrot_angle), 0, np.cos(yrot_angle), 0],
    [0, 0, 0, 1]
])

zrot_angle = 10
zrot_angle = zrot_angle * np.pi / 180
Rz = np.array([
    [np.cos(zrot_angle), -np.sin(zrot_angle), 0, 0],
    [np.sin(zrot_angle), np.cos(zrot_angle), 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])

rotation_matrix = Rx.dot(Ry.dot(Rz))

A = pr.p2_canonical(A_raw)
B = pr.p2_canonical(B_raw)
C = pr.p2_canonical(C_raw)
D = pr.p2_canonical(D_raw)

th = 0.05
#u = np.array([0, 3, 4]) / np.sqrt(45)
#u = np.array([0, 2.5, 2.5]) / np.sqrt(2 * 2.5**2)
u = np.array([0, 2, 2.7]) / np.sqrt(4 + 2.7**2)
axis_rotation_matrix = np.array([
    [np.cos(th) + u[0] * u[0] * (1 - np.cos(th)), u[0] * u[1] * (1 - np.cos(th)) - u[2] * np.sin(th), u[0] * u[2] * (1 - np.cos(th)) + u[1] * np.sin(th), 0],
    [u[1] * u[0] * (1 - np.cos(th)) + u[2] * np.sin(th), np.cos(th) + u[1] * u[1] * (1 - np.cos(th)), u[1] * u[2] * (1 - np.cos(th)) - u[0] * np.sin(th), 0],
    [u[2] * u[0] * (1 - np.cos(th)) - u[1] * np.sin(th), u[2] * u[1] * (1 - np.cos(th)) + u[0] * np.sin(th), np.cos(th) + u[2] * u[2] * (1 - np.cos(th)), 0],
    [0, 0, 0, 1]
])
rotation_matrix = axis_rotation_matrix








a = 50
A2_raw = np.array([-a, 0, 0, 1.])
B2_raw = np.array([a, 0, 0, 1.])
C2_raw = np.array([0, a * np.sqrt(3), 0, 1.])
D2_raw = np.array([0, a * np.sqrt(3) / 3, a * 2 * np.sqrt(6) / 3 , 1.])

offset2 = np.array([-150, -25, a * np.sqrt(3) / 3, 0]) + np.array([0, 0, 50, 0])
A2_raw += offset2
B2_raw += offset2
C2_raw += offset2
D2_raw += offset2

A2 = pr.p2_canonical(A_raw)
B2 = pr.p2_canonical(B_raw)
C2 = pr.p2_canonical(C_raw)
D2 = pr.p2_canonical(D_raw)


#r = np.array([0, 2.5, 2.5]) / np.sqrt(2 * 2.5**2)
r = np.array([0, 2, 2.7]) / np.sqrt(4 + 2.7**2)
rotation_matrix2 = np.array([
    [np.cos(th) + r[0] * r[0] * (1 - np.cos(th)), r[0] * r[1] * (1 - np.cos(th)) - r[2] * np.sin(th), r[0] * r[2] * (1 - np.cos(th)) + r[1] * np.sin(th), 0],
    [r[1] * r[0] * (1 - np.cos(th)) + r[2] * np.sin(th), np.cos(th) + r[1] * r[1] * (1 - np.cos(th)), r[1] * r[2] * (1 - np.cos(th)) - r[0] * np.sin(th), 0],
    [r[2] * r[0] * (1 - np.cos(th)) - r[1] * np.sin(th), r[2] * r[1] * (1 - np.cos(th)) + r[0] * np.sin(th), np.cos(th) + r[2] * r[2] * (1 - np.cos(th)), 0],
    [0, 0, 0, 1]
])





origin = pr.p2_canonical(np.array([-70, -120, 50, 1]))
pbase_x = pr.p2_canonical(np.array([50, 0, 50, 1]))
pbase_y = pr.p2_canonical(np.array([0, 50, 50, 1]))
pbase_z = pr.p2_canonical(np.array([0, 0, 100, 1]))
nbase_x = pr.p2_canonical(np.array([-50, 0, 50, 1]))
nbase_y = pr.p2_canonical(np.array([0, -50, 50, 1]))
nbase_z = pr.p2_canonical(np.array([0, 0, 25, 1]))







cphere_coord = np.array([-150, 70, 100, 1], dtype=float)
cphere_coord2 = np.array([-180, 100, 100, 1], dtype=float)

cnt = 0
dif = 0
pc = (0, 0, 0)
pc2 = (0, 0, 0)


running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
    if not running: break

    cnt += 1
    if cnt == 100:
        #cphere_coord += np.array([50 * np.cos(dif), 0, 15*np.cos(dif), 0], dtype=float)
        cphere_coord += np.array([50 * np.cos(dif), 50 * np.cos(dif + np.pi/4), 15*np.cos(dif), 0], dtype=float)
        cphere_coord2 += np.array([-50 * np.cos(dif), 0, 25*np.cos(dif), 0], dtype=float)
        cnt = 0
        dif += np.pi/10
        #pc = pr.get_orth2canonm().dot(pr.get_tcnpm().dot(cphere_coord))
        pc = pr.p2_canonical(cphere_coord)
        pc2 = pr.p2_canonical(cphere_coord2)
        #print(pc)
        A_raw = rotation_matrix.dot(A_raw)
        B_raw = rotation_matrix.dot(B_raw)
        C_raw = rotation_matrix.dot(C_raw)
        D_raw = rotation_matrix.dot(D_raw)
        A2_raw = rotation_matrix.dot(A2_raw)
        B2_raw = rotation_matrix.dot(B2_raw)
        C2_raw = rotation_matrix.dot(C2_raw)
        D2_raw = rotation_matrix.dot(D2_raw)
        A = pr.p2_canonical(A_raw)
        B = pr.p2_canonical(B_raw)
        C = pr.p2_canonical(C_raw)
        D = pr.p2_canonical(D_raw)
        A2 = pr.p2_canonical(A2_raw)
        B2 = pr.p2_canonical(B2_raw)
        C2 = pr.p2_canonical(C2_raw)
        D2 = pr.p2_canonical(D2_raw)
    
    screen.fill(bg_color)
    pygame.draw.circle(screen, (255, 0, 0), (pc[0], pc[1]), pc[2], 2)
    pygame.draw.circle(screen, (0, 255, 0), (pc2[0], pc2[1]), pc2[2], 2)
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(B[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(C[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(A[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(B[:2]), tuple(C[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(B[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple(C[:2]), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple((A[:2] + B[:2]) / 2), tuple(D[:2]))
    pygame.draw.line(screen, (255, 0, 0), tuple((A[:2] + B[:2]) / 2), tuple(C[:2]))


    pygame.draw.line(screen, (0, 255, 0), tuple(A2[:2]), tuple(B2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple(A2[:2]), tuple(C2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple(A2[:2]), tuple(D2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple(B2[:2]), tuple(C2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple(B2[:2]), tuple(D2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple(C2[:2]), tuple(D2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple((A2[:2] + B2[:2]) / 2), tuple(D2[:2]))
    pygame.draw.line(screen, (0, 255, 0), tuple((A2[:2] + B2[:2]) / 2), tuple(C2[:2]))

    pygame.draw.line(screen, (0, 0, 255), (pc[0], pc[1]), (pc2[0], pc2[1]))

    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(pbase_x[0:2]))
    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(pbase_y[0:2]))
    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(pbase_z[0:2]))
    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(nbase_x[0:2]))
    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(nbase_y[0:2]))
    pygame.draw.line(screen, (0, 0, 250), tuple(origin[0:2]), tuple(nbase_z[0:2]))
    pygame.draw.line(screen, (0, 0, 0), (SCREEN_WIDTH / 2 - 50, SCREEN_HEIGHT / 2), (SCREEN_WIDTH / 2 + 50, SCREEN_HEIGHT / 2))
    pygame.draw.line(screen, (0, 0, 0), (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50), (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
    pygame.display.flip()

