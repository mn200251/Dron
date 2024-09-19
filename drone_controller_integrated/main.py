from os import environ
import numpy as np
import drone_model as dm
import physics_engine as pe
import ground_model as gm
import state_controller as sc
import socket
import threading
import time
import multiprocessing
from connect_to_server import start_server_connection
from connect_to_server import normal_data





near_plane_center = np.array([0, 0, 50, 1], dtype=float)
orthographic_volume_size = np.array([50, 50, 50], dtype=float)

orthographic_volume_center = \
    near_plane_center + np.array([0, 0, orthographic_volume_size[2] / 2, 0], dtype=float)

ground_center = orthographic_volume_center + np.array([0, orthographic_volume_size[1] / 2, 0, 0])

drone = dm.Drone(orthographic_volume_center, 20)
ground = gm.Ground(ground_center, 2 * orthographic_volume_size[0], 2 * orthographic_volume_size[2], 2, 20)
pe.init_gravity_vector(ground)

running = True
pid_on = True
def user_input_handling():
    global normal_data
    # must set drone.motor_set_power_percent
    # not just return values, because of calculations
    # self.drone.motor_set_power_percent
    # for user input
    if (normal_data):
        print("user_input_here")
        print(normal_data)
    pass
    return None

# pid stuff
curr_state = sc.StateController()

def pid_reset_params(curr_state):
    if curr_state.pid_activation_cycle == curr_state.pid_reset_interval_factor:
        drone.pd_params_integral = np.array([0, 0, 0], dtype=float)
        curr_state.pid_activation_cycle = 0

def read_sensor_data(curr_state):
    if curr_state.loop_cycle % curr_state.sensor_measure_interval == 0:
        """
        curr_euler_angles = self.rotate(pe.magnitude(angular_speed), pe.normalize_vector(angular_speed))
        if self.GYRO_NOISE:
            curr_euler_angles += curr_euler_angles * np.random.uniform(-self.GYRO_NOISE_PERCENT, self.GYRO_NOISE_PERCENT, 3)
        self.euler_angles += curr_euler_angles
        """
        # get sensor data here
        drone.euler_angles = np.array([7, 7, 7])

def pid_action(curr_state):
    if not pid_on: return
    if curr_state.loop_cycle % curr_state.pid_sleep_time != 0:
        pid_updated_values = drone.pd()
        drone.euler_angles = np.array([0, 0, 0], dtype=float)
        curr_state.pid_activation_cycle += 1
        return pid_updated_values
    return None

def update(curr_state):
    drone.update()
    pid_reset_params(curr_state)
    read_sensor_data(curr_state)
    pid_updated_values = pid_action(curr_state)
    curr_state.loop_cycle += 1
    if curr_state.loop_cycle == curr_state.lcm:
        curr_state.loop_cycle = 0
    return pid_updated_values

def init():
    camera_stream_process = multiprocessing.Process(target=start_server_connection)


#init()
camera_stream_process = multiprocessing.Process(target=start_server_connection)
while running:
    new_motor_values = user_input_handling()
    if not running: break
    pid_updated_values = update(curr_state)
    # use strategy here to update actual values
    #if pid_updated_values:
        # set pwm here to pid_updated_values
        #pass
    #else:
        # set pwm here to new_motor_values
        #pass
