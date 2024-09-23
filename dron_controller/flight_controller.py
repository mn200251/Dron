import time
import threading
from enum import Enum

import gpiod
import atexit
import signal
from mpu6050 import mpu6050
from keyboard_client import variables, key_listener, read_variables
from pca9685 import PCA9685, PCA9685_I2C_ADDRESS

class InstructionType(Enum):
    HEARTBEAT = 1
    START_RECORDING_VIDEO = 2
    STOP_RECORDING_VIDEO = 3
    START_RECORDING_MACRO = 4
    STOP_RECORDING_MACRO = 5
    GET_MACROS = 6
    START_MACRO = 7
    GET_VIDEOS = 8  # start the video download and request video using inedex
    DOWNLOAD_VIDEO = 9
    TURN_ON = 10
    JOYSTICK = 11
    GET_LINK = 12
    TURN_OFF = 13
    GET_STATUS = 14  # da proveri stanje jer neke instrukcije mozda nisu prosle npr pocni snimanje
    BACK = 15  # povratak iz browsinga videa/letova?
    PID_ON=16
    PID_OFF=17

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs
PERIOD = 20000  # Period in µs (50Hz frequency)
MICRO_TO_SEC = 1000000.0
NUM_MOTORS = 4

MILLI_TO_SEC = 1000000.0

# 4 prednji desni
# 5 zadnji desni
# 10 prednji levi
# 11 zadnji levi
MOTOR_PINS = [10,4,11,5]


running = True

lock = threading.Lock()

# RAD - throttle settings -trenutno nemam pojma sta zapravo rade
throttle_idle: float = 0.08  # the minumum throttle needed to apply to the four motors for them all to spin up, but not provide lift (idling on the ground)
throttle_governor: float = 0.75  # the maximum throttle that can be applied. So, if the pilot is inputting 100% on the controller, it will max out at this. And every value below the pilot's 100% will be scaled linearly within the range of the idle throttle seen above and this governor throttle. If you do not wish to apply a governor (not recommended), set this to None.

# Max attitude rate of change rates (degrees per second)
max_rate_roll: float = 30.0  # roll
max_rate_pitch: float = 30.0  # pitch
max_rate_yaw: float = 50.0  # yaw

# Desired Flight Controller Cycle time
# This is the number of times per second the flight controller will perform an adjustment loop (PID loop)
cycle_time_us: float = 4000  # 250Hz
cycle_time_seconds: float = 0.004

# RAD - PID Controller values
pid_roll_kp: float = 0.00043714285
pid_roll_ki: float = 0.00255
pid_roll_kd: float = 0.00002571429
pid_pitch_kp: float = pid_roll_kp
pid_pitch_ki: float = pid_roll_ki
pid_pitch_kd: float = pid_roll_kd
pid_yaw_kp: float = 0.001714287
pid_yaw_ki: float = 0.003428571
pid_yaw_kd: float = 0.0

def normalize(value: float, original_min: float, original_max: float, new_min: float, new_max: float) -> float:
    """Normalizes (scales) a value to within a specific range."""
    return new_min + ((new_max - new_min) * ((value - original_min) / (original_max - original_min)))


def run(sharedDict) -> None:
    print("Starting the flight controller")
    time.sleep(3)

    # RAD - SET-up communication

    # Print settings that are important
    print("Roll PID: " + str(pid_roll_kp) + ", " + str(pid_roll_ki) + ", " + str(pid_roll_kd))
    print("Pitch PID: " + str(pid_pitch_kp) + ", " + str(pid_pitch_ki) + ", " + str(pid_pitch_kd))
    print("Yaw PID: " + str(pid_yaw_kp) + ", " + str(pid_yaw_ki) + ", " + str(pid_yaw_kd))

    # Set up MPU6050
    mpu = mpu6050(0x68)

    if not mpu.check_connection():
        print("Failed to connect to MPU6050.")
        # RAD - nekako obavesti korisnika

    # Set ranges to default values
    mpu.set_gyro_range(mpu.GYRO_RANGE_500DEG)
    mpu.set_filter_range(mpu.FILTER_BW_42)  # Set the low pass filter to 4 - mozda cemo menjati
    mpu.disable_temp_sensor()  # Disable temp since not in use
    mpu.disable_accelerometer()# Disable acc since not in use


    # Measure gyro bias
    print("Calibrating the gyroscope")
    gyro_bias = mpu.calibrate_gyroscope()
    gyro_range = mpu.read_gyro_range(True)

    # RAD - to be podesavanje moje nove plocice
    pca9685 = PCA9685(i2c_address=PCA9685_I2C_ADDRESS)

    pca9685.reset()

    pca9685.init()

    # Constants calculations
    max_throttle = throttle_governor if throttle_governor is not None else 1.0
    throttle_range: float = max_throttle - throttle_idle
    windup_guard: float = 150.0
    last_mode: bool = False  # the most recent mode the flight controller was in

    # State variables - PID related
    roll_last_integral: float = 0.0
    roll_last_error: float = 0.0
    pitch_last_integral: float = 0.0
    pitch_last_error: float = 0.0
    yaw_last_integral: float = 0.0
    yaw_last_error: float = 0.0

    # Awaits start command -arm ESCes- nisam sigurna da li treba 4u1 esciju?
    # ....
    print("press 1 to start, 2 to flight and 9 to end")
    while variables[4] != 1:
        time.sleep(0.5)

    print("-- BEGINNING FLIGHT CONTROL LOOP NOW --")
    try:
        while True:  # povremeno 1 za testiranje

            if sharedDict['type']==InstructionType.TURN_ON.value:
                pca9685.reset()
                pca9685.init()
                for i in MOTOR_PINS:
                    pca9685.arm_esc(MOTOR_PINS)
                sharedDict['type']= InstructionType.JOYSTICK.value
                roll_last_integral = 0.0
                roll_last_error = 0.0
                pitch_last_integral = 0.0
                pitch_last_error = 0.0
                yaw_last_integral = 0.0
                yaw_last_error = 0.0
            elif sharedDict['type']==InstructionType.TURN_OFF.value:
                pca9685.reset()
                sharedDict['type'] = InstructionType.JOYSTICK.value

            start = time.time()  # in s
            # Read gyro
            # RAD - potencijalno promene znaka u zavisnosti od toga kako montiramo
            gyro_data = mpu.get_gyro_data(gyro_range)
            # Remove the inherent deviation of the gyro
            #x roll
            #y pitch aka nos drona
            gyro_data['x'] -= -gyro_bias['x']
            gyro_data['y'] -= gyro_bias['y']
            gyro_data['z'] -= gyro_bias['z']


            # normalized input values
            input_throttle: float = sharedDict['z']
            input_pitch: float = 0#sharedDict['y'] * -1
            input_roll: float = 0#sharedDict['x']
            input_yaw: float = 0# sharedDict['rotation']  # between -1.0 and 1.0

            # calculate the adjusted desired throttle (above idle throttle, below governor throttle, scaled linearly)
            adj_throttle: float = throttle_idle + (throttle_range * input_throttle)

            # calculate errors - diff between the actual rates and the desired rates
            # "error" is calculated as setpoint (the goal) - actual
            error_rate_roll: float = (input_roll * max_rate_roll) - gyro_data['x']
            error_rate_pitch: float = (input_pitch * max_rate_pitch) - gyro_data['y']
            error_rate_yaw: float = (input_yaw * max_rate_yaw) - gyro_data['z']

            # roll PID calc
            roll_p: float = error_rate_roll * pid_roll_kp
            roll_i: float = roll_last_integral + (error_rate_roll * pid_roll_ki * cycle_time_seconds)
            roll_i = max(min(roll_i, windup_guard), -windup_guard)  # constrain within I-term limits
            roll_d: float = pid_roll_kd * (error_rate_roll - roll_last_error) / cycle_time_seconds
            pid_roll: float = roll_p + roll_i + roll_d

            # pitch PID calc
            pitch_p: float = error_rate_pitch * pid_pitch_kp
            pitch_i: float = pitch_last_integral + (error_rate_pitch * pid_pitch_ki * cycle_time_seconds)
            pitch_i = max(min(pitch_i, windup_guard), -windup_guard)  # constrain within I-term limits
            pitch_d: float = pid_pitch_kd * (error_rate_pitch - pitch_last_error) / cycle_time_seconds
            pid_pitch = pitch_p + pitch_i + pitch_d

            # yaw PID calc
            yaw_p: float = error_rate_yaw * pid_yaw_kp
            yaw_i: float = yaw_last_integral + (error_rate_yaw * pid_yaw_ki * cycle_time_seconds)
            yaw_i = max(min(yaw_i, windup_guard), -windup_guard)  # constrain within I-term limits
            yaw_d: float = pid_yaw_kd * (error_rate_yaw - yaw_last_error) / cycle_time_seconds
            pid_yaw = yaw_p + yaw_i + yaw_d

            # calculate throttle values
            # RAD- mozda ce trebati popravke znakova
            throttles = [0.0]*NUM_MOTORS
            throttles[0]: float = adj_throttle + pid_pitch + pid_roll - pid_yaw
            throttles[1]: float = adj_throttle + pid_pitch - pid_roll + pid_yaw
            throttles[2]: float = adj_throttle - pid_pitch + pid_roll + pid_yaw
            throttles[3]: float = adj_throttle - pid_pitch - pid_roll - pid_yaw

            print(throttles)
            # Adjust throttle according to input
            # RAD -  nevidjeno lupanje boga pitaj kako zapravo radi za throttle
            for t in range(4):
                thr=calculate_duty_cycle(throttles[t])
                pca9685.set_ESC_PWM(MOTOR_PINS[t],thr)

            print("")

            # Save state values for next loop
            roll_last_error = error_rate_roll
            pitch_last_error = error_rate_pitch
            yaw_last_error = error_rate_yaw
            roll_last_integral = roll_i
            pitch_last_integral = pitch_i
            yaw_last_integral = yaw_i


            end = time.time()

            # wait to make the hz correct
            elapsed = end - start
            if elapsed < cycle_time_seconds:
                time.sleep(cycle_time_seconds - elapsed)

        print("Flight controller stopped")
        exit(0)

    except Exception as e:  # something went wrong
        print("An error occured"+ str(e))
        # Stop the motors
        cleanup()

        exit(1)


def calculate_duty_cycle(throttle: float, dead_zone: float = 0.07) -> int:
    """Determines the appropriate PWM duty cycle, in nanoseconds, to use for an ESC controlling a BLDC motor"""

    ### SETTINGS (that aren't parameters) ###
    duty_ceiling: int = 2000000  # the maximum duty cycle (max throttle, 100%) is 2 ms, or 10% duty (0.10)
    duty_floor: int = 1000000  # the minimum duty cycle (min throttle, 0%) is 1 ms, or 5% duty (0.05). HOWEVER, I've observed some "twitching" at exactly 5% duty cycle. It is off, but occasionally clips above, triggering the motor temporarily. To prevent this, i'm bringing the minimum down to slightly below 5%
    ################

    # calcualte the filtered percentage (consider dead zone)
    range: float = 1.0 - dead_zone - dead_zone
    percentage: float = min(max((throttle - dead_zone) / range, 0.0), 1.0)

    dutyns: int = int(duty_floor + ((duty_ceiling - duty_floor) * percentage))

    # clamp within the range
    dutyns = max(duty_floor, min(dutyns, duty_ceiling))

    return int(dutyns/1000)

if __name__ == "__main__":
    run()