from os import environ
import numpy as np
import drone_model as dm
import physics_engine as pe
import ground_model as gm
import state_controller as sc

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
    # self.drone.motor_set_power_percent
    # for user input
    pass

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
        drone.euler_angles = 7

def pid_action(curr_state):
    if curr_state.loop_cycle % curr_state.pid_sleep_time == 0:
        if pid_on:
            drone.pd()
            drone.euler_angles = np.array([0, 0, 0], dtype=float)
        curr_state.pid_activation_cycle += 1

def update(curr_state):
    drone.update()
    pid_reset_params(curr_state)
    read_sensor_data(curr_state)
    curr_state.loop_cycle += 1
    if curr_state.loop_cycle == curr_state.lcm:
        curr_state.loop_cycle = 0

while running:
    user_input_handling()
    if not running: break
    update(curr_state)