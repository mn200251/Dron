from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import numpy as np
import drone_model as dm
import projection_math as pm
import physics_engine as pe
import ground_model as gm
import slider_model as sm
from connect_to_server import start_server_connection
from connect_to_server import user_input

pygame.init()
pygame.font.init()
text_font = pygame.font.SysFont("Comic Sans MS", 15)
pygame.display.set_caption("drone simulator")
pygame.display.set_icon(pygame.image.load(".\drone_simulation\drone_icon.png"))

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
CONTROL_SCREEN_HEIGHT = 150
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + CONTROL_SCREEN_HEIGHT))
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

drone = dm.Drone(orthographic_volume_center, 20, pr)
ground = gm.Ground(ground_center, 2 * orthographic_volume_size[0], 2 * orthographic_volume_size[2], 2, 20, pr)
start_server_connection()

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
    curr_euler_angles = drone.rotate(rotation_angle, unit_vector)
    if drone.GYRO_NOISE:
        curr_euler_angles += curr_euler_angles * np.random.uniform(-drone.GYRO_NOISE_PERCENT, drone.GYRO_NOISE_PERCENT, 3)
    drone.euler_angles += curr_euler_angles
    if pygame.mouse.get_pressed()[2]:
        ground.rotate(rotation_angle, unit_vector)
        pe.init_gravity_vector(ground)

def normalize_user_motor_input(x, y):
    float_zero = 0.000000001
    # when 10 should round [35, 55] to 45 for example
    # TO DO ???
    aim_help_45_angle_deg = 45
    aim_help_0_and_90_angle_deg = 45
    if  np.abs(x) > float_zero and  np.abs(y) > float_zero:
        abs_angle_deg = np.abs(180 * np.arctan(y / x) / np.pi)
        
        if (0 - aim_help_0_and_90_angle_deg / 2 <= abs_angle_deg) \
            and (abs_angle_deg <= 0 + aim_help_0_and_90_angle_deg / 2):
            #print("angle = 0")
            return(x, 0)
        if (90 - aim_help_0_and_90_angle_deg / 2 <= abs_angle_deg) \
            and (abs_angle_deg <= 90 + aim_help_0_and_90_angle_deg / 2):
            #print("angle = 90")
            return(0, y)
        if (45 - aim_help_45_angle_deg / 2 <= abs_angle_deg) \
            and (abs_angle_deg <= 45 + aim_help_45_angle_deg / 2):
            t = (np.abs(x) + np.abs(y)) / 2
            x = np.sign(x) * t; y = np.sign(y) * t

        #print(f"angle = {180 * np.arctan(y / x) / np.pi}")
        vector_magnitude = np.sqrt(x ** 2 + y ** 2)
        max_projection_magnitude = max(np.abs(x), np.abs(y))
        normalized_x_delta_input = x * vector_magnitude / max_projection_magnitude
        normalized_y_delta_input = y * vector_magnitude / max_projection_magnitude
        return (normalized_x_delta_input, normalized_y_delta_input)
    elif np.abs(x) > float_zero and np.abs(y) <= float_zero:
        return (x, 0)
    elif np.abs(x) <= float_zero and np.abs(y) > float_zero:
        return (0, y)
    return (0, 0)

motor0_slider = sm.Slider((100, SCREEN_HEIGHT + CONTROL_SCREEN_HEIGHT / 5), text="motor 0 (-) power")
motor1_slider = sm.Slider((100, SCREEN_HEIGHT + CONTROL_SCREEN_HEIGHT / 2), text="motor 1 (+) power")
motor2_slider = sm.Slider((700, SCREEN_HEIGHT + CONTROL_SCREEN_HEIGHT / 5), text="motor 2 (-) power")
motor3_slider = sm.Slider((700, SCREEN_HEIGHT + CONTROL_SCREEN_HEIGHT / 2), text="motor 3 (+) power")
motor0_slider.set_motor_power_function(drone, 0, -1)
motor1_slider.set_motor_power_function(drone, 1, 1)
motor2_slider.set_motor_power_function(drone, 2, -1)
motor3_slider.set_motor_power_function(drone, 3, 1)
drone.add_motor_slider(0, motor0_slider)
drone.add_motor_slider(1, motor1_slider)
drone.add_motor_slider(2, motor2_slider)
drone.add_motor_slider(3, motor3_slider)



prev_user_data = dict()
running = True
pid_on = False
armed = False
def user_input_handling():
    global user_input
    global prev_user_data
    global pid_on
    global armed

    motor0_slider.changeValue()
    motor1_slider.changeValue()
    motor2_slider.changeValue()
    motor3_slider.changeValue()

    #print(user_input.data)
    if user_input.data and (user_input.data is not prev_user_data):
        prev_user_data = user_input.data
        if armed and ("NoInst" not in user_input.data):
            x_left, y_left = normalize_user_motor_input(user_input.data["x_left"], user_input.data["y_left"])
            x_left = -x_left # mirror x left
            x_right, y_right = normalize_user_motor_input(user_input.data["x_right"], user_input.data["y_right"])
            #print(f"left: ({x_left}, {y_left}), right: ({x_right}, {y_right})")
            drone.motor_change_power_percent(0, y_left, 0.08)
            drone.motor_change_power_percent(1, x_left, 0.08)
            drone.motor_change_power_percent(2, y_right, 0.08)
            drone.motor_change_power_percent(3, x_right, 0.08)
            drone.update_motor_sliders()
        
        if "pid" in user_input.data: pid_on = bool(user_input.data["pid"])

        #if user calls arm command: # --- armovanje traje NEKOLIKO SEKUNDI
        if "state" in user_input.data:
            if user_input.data["state"] == 10:
                armed = True
            if user_input.data["state"] == 13: # something here -- disarm [turn off dugme]
                armed = False

    for event in pygame.event.get():
        global running; global zoom; global canonical_volume_size
        global mouse_pos1; global zoom_text_surface
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                pid_on = not pid_on
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1 and zoom < 3: zoom += 0.1
            if event.y == -1 and zoom > 0.2: zoom -= 0.1
            zoom_text_surface = text_font.render(f"zoom: {int(zoom * 100)}%", False, (0, 0, 0))
            canonical_volume_size = np.array([zoom * SCREEN_WIDTH, zoom * SCREEN_HEIGHT, 100], dtype=float)
            pr.set_canonical_volume_size(canonical_volume_size)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos1 = pygame.mouse.get_pos()
            if mouse_pos1[1] > SCREEN_HEIGHT: mouse_pos1 = None
        if event.type == pygame.MOUSEBUTTONUP: mouse_pos1 = None
    if mouse_pos1 is not None: mouse_rotate()

def draw_simulator_state():
    screen.fill(bg_color)
    ground.draw_to_(screen)
    drone.draw_to_(screen)
    pygame.draw.line(screen, (0, 0, 0), (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT), 3)
    motor0_slider.render(screen)
    motor1_slider.render(screen)
    motor2_slider.render(screen)
    motor3_slider.render(screen)
    screen.blit(zoom_text_surface, (SCREEN_WIDTH - 100, 0))
    pygame.display.flip()

simulation_initialized = False
def initialize_simulation():
    global simulation_initialized
    if simulation_initialized: return
    simulation_initialized = True
    #drone.rotate(-15, [0, 0, 1])
    #drone.rotate(-15, [1, 0, 0])
    #drone.rotate(-145, [0, 1, 0])

    pe.init_gravity_vector(ground)
    #ground.rotate_ground(-15, [0, 0, 1])
    #ground.rotate_ground(15, [0, 0, 1])
    ground.rotate_ground(45, [0, 1, 0])
    ground.rotate_ground(15, [1, 0, 0])
    #ground.rotate(45, [0, 0, 1])
    #ground.rotate(45, [1, 0, 0])


pid_sleep_time = 10
pid_reset_interval_factor = 100
time_passed = 0
intervals_passed = 0
def update():
    global time_passed
    global intervals_passed
    #drone.rotate(-0.03, [0, 1, 0])
    #ground.rotate(-0.03, [0, 1, 0]) # cool ground rotation
    #drone.rotate(-0.15, [1, 0, 0])
    #ground.rotate_ground(-0.03, [0, 1, 0])
    #drone.motor_set_power_percent(0, -0.392)
    #drone.motor_set_power_percent(1, 0.392)
    #drone.motor_set_power_percent(2, -0.392)
    #drone.motor_set_power_percent(3, 0.392)
    drone.update()
    if pid_reset_interval_factor:
        drone.pd_params_integral = np.array([0, 0, 0], dtype=float)
    if time_passed == pid_sleep_time:
        if pid_on: drone.pd()
        time_passed = 0
        intervals_passed += 1
    time_passed += 1

initialize_simulation()
while running:
    user_input_handling()
    if not running: break
    update()
    draw_simulator_state()