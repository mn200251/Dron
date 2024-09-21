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
from connect_to_server import user_input
#from pca9685 import PCA9685, PCA9685_I2C_ADDRESS
#from mpu6050 import mpu6050




near_plane_center = np.array([0, 0, 50, 1], dtype=float)
orthographic_volume_size = np.array([50, 50, 50], dtype=float)

orthographic_volume_center = \
    near_plane_center + np.array([0, 0, orthographic_volume_size[2] / 2, 0], dtype=float)

ground_center = orthographic_volume_center + np.array([0, orthographic_volume_size[1] / 2, 0, 0])

MIN_MOTOR_FORCE = 1200
MAX_MOTOR_FORCE = 1500
drone = dm.Drone(orthographic_volume_center, 20, MIN_MOTOR_FORCE, MAX_MOTOR_FORCE)
ground = gm.Ground(ground_center, 2 * orthographic_volume_size[0], 2 * orthographic_volume_size[2], 2, 20)
pe.init_gravity_vector(ground)

def normalize_user_motor_input(x, y):
    float_zero = 0.000000001
    # when 10 should round [35, 55] to 45 for example
    # TO DO ???
    aim_help_angle_deg = 10
    if  np.abs(x) > float_zero and  np.abs(y) > float_zero:
        abs_angle_deg = np.abs(180 * np.arctan(y / x) / np.pi)
        if (45 - aim_help_angle_deg / 2 <= abs_angle_deg) \
            and (abs_angle_deg <= 45 + aim_help_angle_deg / 2):
            t = (np.abs(x) + np.abs(y)) / 2
            x = np.sign(x) * t; y = np.sign(y) * t
        print(f"angle = {180 * np.arctan(y / x) / np.pi}")
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

prev_user_data = dict()
running = True
pid_on = False
def user_input_handling():
    global user_input
    global prev_user_data
    # must set drone.motor_set_power_percent
    # not just return values, because of calculations
    # self.drone.motor_set_power_percent
    # for user input
    #print("user_input_here")
    if user_input.data and (user_input.data is not prev_user_data):
        prev_user_data = user_input.data
        print()
        print(user_input.data)
        print(normalize_user_motor_input(user_input.data["x_left"], user_input.data["y_left"]))
        print(normalize_user_motor_input(user_input.data["x_right"], user_input.data["y_right"]))

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
    if not pid_on: return None
    if curr_state.loop_cycle % curr_state.pid_sleep_time != 0:
        drone.pd()
        drone.euler_angles = np.array([0, 0, 0], dtype=float)
        curr_state.pid_activation_cycle += 1
    return None

def update(curr_state):
    drone.update()
    pid_reset_params(curr_state)
    read_sensor_data(curr_state)
    pid_action(curr_state)
    curr_state.loop_cycle += 1
    if curr_state.loop_cycle == curr_state.lcm:
        curr_state.loop_cycle = 0

"""

    !!!!!!!!!!!!!!!

    DODAVANJE NITI/PROCESA NA SENZOR/RACUNANJE MOZE DA SACUVA ~[1ms - 1.5ms] (mozda 2ms)


    -- senzor cita za 1.5ms i ziroskop i akcelometar
    -- racunanje traje ~ (1ms - 2ms)

"""

try:

    # initialization

    # SERVER CLIENT INITIALIZATION

    #camera_stream_process = multiprocessing.Process(target=start_server_connection)

    # CAMERA STREAMING INITIALIZATION

    #multiprocessing.freeze_support()

    #drone_client_process = multiprocessing.Process(target=start_server_connection)
    start_server_connection()
    #drone_client_process.start()


    # PWM INITIALIZATION
    #pca9685 = PCA9685(i2c_address=PCA9685_I2C_ADDRESS)
    #pca9685.reset()
    #pca9685.init()
    # channel=-1 -- all channel override
    
    # arm all motors, should be done when user enters 10 on type from app fix later??

    # motor idjevi su:
    #   4 prednji desni
    #   5 zadnji desni
    #   10 prednji levi
    #   11 zadnji levi
    channels=[4,5,10,11]

    # if user calls arm command: --- armovanje traje NEKOLIKO SEKUNDI
    #for ch in channels:
        #pca9685.arm_esc(ch)
    
    # SENSOR INITIALIZATION

    #mpu = mpu6050(0x68)
    #mpu.init()

    # provera da li se mpu lepo povezao
    #if not mpu.check_connection():
        #raise Exception("ERROR: sensor not connected")

    #mpu.reset_mpu6050()
    #bias_accelometer = mpu.calibrate_accelerometer()
    #bias_gyroscope = mpu.calibrate_gyroscope()
    
    # citanje opsega
    #accel_range = mpu.read_accel_range(True)
    #gyro_range = mpu.read_gyro_range(True)


    # citanje podataka sa senzora ovo staviti na odgovarajuce mesto kasnije: 
    """
    accel_data = mpu.get_accel_data(accel_range)
    print(accel_data['x'] - bias_accelometer['x'])
    print(accel_data['y'] - bias_accelometer['y'])
    print(accel_data['z'] - bias_accelometer['z'])
    gyro_data = mpu.get_gyro_data(gyro_range)
    print(gyro_data['x'] - bias_gyroscope['x'])
    print(gyro_data['y'] - bias_gyroscope['y'])
    print(gyro_data['z'] - bias_gyroscope['z'])
    """


    while running:
        new_motor_values = user_input_handling()
        if not running: break
        update(curr_state)
        
        # print(f"""
        # motor1: {drone.get_motor_pwm(0)}
        # motor2: {drone.get_motor_pwm(1)}
        # motor3: {drone.get_motor_pwm(2)}
        # motor4: {drone.get_motor_pwm(3)}
        # """)
        # use strategy here to update actual values
        #print(pid_updated_values)
        #if pid_updated_values:
            # set pwm here to pid_updated_values
            #pass
        #else:
            # set pwm here to new_motor_values
            #pass
        

        # ovako se gase motori na komandu korisnika

        # ovo nema za sad
        """
        if User wants to disarm: # something here -- disarm [turn off dugme]
            for ch in channels:     ## ovo je ako budemo imali blago ubijanje
                pca9685.set_channel_off(ch)     # OVO JE BRZO ? 750 us
        # mora na djojstiku da se drzi crveno dugme sekund da bi se ubili motori
        elif USER WANTS HARD RESET, KILL SIWTCH:
            pca9685.reset() ### posle ovoga mora da se opet inicijalizuje i svakako mora da se armuje
        elif drone disarmed and User wants to arm again: # ARMOVANJE TRAJE NEKOLIKO SEKUNDI
            for ch in channels:
                pca9685.arm_esc(ch)
        else if User in djojstik mode and sve radi kako treba: # nesto drugo, ako sve radi
            pca9685.set_ESC_PWM(channel[id_kanala], vrednost iz opsega [1000, 2000])
        """


finally:
    print("ERROR")
    # ugasi mpu (uspava ga, ode u low power mode)
    #mpu.bus.write_byte_data(mpu.address, mpu.PWR_MGMT_1, 0x40)

    #pca9685.reset() ### INSTANT ODMAH

    # posle reseta popravljanje: 
    # opet mora inicijalizacija
    # moralo bi ovo
    """
        pca9685.init()
        # channel=-1 -- all channel override
        
        # arm all motors, should be done when user enters 10 on type from app fix later??

        # motor idjevi su:
        #   4 prednji desni
        #   5 zadnji desni
        #   10 prednji levi
        #   11 zadnji levi
        channels=[4,5,10,11]
        for ch in channels:
            pca9685.arm_esc(ch)
    """