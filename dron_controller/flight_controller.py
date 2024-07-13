import time
import threading
import gpiod
import atexit
import signal
from mpu6050 import mpu6050
from keyboard_client import variables, key_listener, read_variables

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs
PERIOD = 20000  # Period in µs (50Hz frequency)
MICRO_TO_SEC = 1000000.0
NUM_MOTORS = 4

MILLI_TO_SEC = 1000000.0

MOTOR_PINS = [17, 27, 22, 23]

# Set up GPIO chip and line
chip = gpiod.Chip('gpiochip4')
lines = [chip.get_line(MOTOR_PINS[i]) for i in range(NUM_MOTORS)]

# Request output direction for the GPIO line
for line in lines:
    line.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)

# Initialize pulse_length with a default value
pulse_lengths = [MIN_PULSE_LENGTH] * NUM_MOTORS
running = True

lock = threading.Lock()

# RAD - throttle settings -trenutno nemam pojma sta zapravo rade
throttle_idle: float = 0.1017  # the minumum throttle needed to apply to the four motors for them all to spin up, but not provide lift (idling on the ground)
throttle_governor: float = 0.1800  # the maximum throttle that can be applied. So, if the pilot is inputting 100% on the controller, it will max out at this. And every value below the pilot's 100% will be scaled linearly within the range of the idle throttle seen above and this governor throttle. If you do not wish to apply a governor (not recommended), set this to None.

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


def cleanup():
    global running
    running = False
    time.sleep(0.05)  # Give some time for the thread to exit its loop
    for line in lines:
        line.set_value(0)  # Ensure the pin is set to 0


def handle_exit(signum, frame):
    cleanup()
    exit(0)


def set_pulse_length(new_pulse_length, index):
    global pulse_lengths
    with lock:
        pulse_lengths[index] = new_pulse_length


def pwm_thread_all_motors_sleep():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with lock:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_MOTORS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        time.sleep(first_pulse_length / MICRO_TO_SEC)

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_MOTORS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            time.sleep(next_wait_time / MICRO_TO_SEC)

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        time.sleep(remaining_time / MICRO_TO_SEC)
    print("PWM control thread finished")


def normalize(value: float, original_min: float, original_max: float, new_min: float, new_max: float) -> float:
    """Normalizes (scales) a value to within a specific range."""
    return new_min + ((new_max - new_min) * ((value - original_min) / (original_max - original_min)))


def run() -> None:
    print("Starting the flight controller")
    time.sleep(3)

    # RAD - SET-up communication
    # RAD -....
    client = key_listener()

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
    mpu.set_filter_range(mpu.FILTER_BW_20)  # Set the low pass filter to 4 - mozda cemo menjati
    mpu.disable_temp_sensor()  # Disable temp since not in use
    mpu.disable_accelerometer()  # Disable acc since not in use

    # Measure gyro bias
    gyro_bias = mpu.calibrate_gyroscope()
    gyro_range = mpu.read_gyro_range(True)

    # RAD - to be podesavanje moje nove plocice
    # Set up pwm thread
    # Register the cleanup function to be called on program exit
    atexit.register(cleanup)
    # Register signal handlers for graceful exit on signals
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    thread = threading.Thread(target=pwm_thread_all_motors_sleep, args=())
    thread.start()

    # Constants calculations
    max_throttle = throttle_governor if throttle_governor is not None else 1.0
    throttle_range: float = max_throttle - throttle_idle
    i_limit: float = 150.0
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
    print("press 1 to start")
    while variables[0] != 1:
        time.sleep(0.5)

    print("-- BEGINNING FLIGHT CONTROL LOOP NOW --")
    try:
        while 1:  # povremeno 1 za testiranje
            start = time.time()  # in s
            # Read gyro
            # RAD - potencijalno promene znaka u zavisnosti od toga kako montiramo
            gyro_data = mpu.get_gyro_data(gyro_range)
            # Remove the inherent deviation of the gyro
            gyro_data['x'] -= gyro_bias['x']
            gyro_data['y'] -= gyro_bias['y']
            gyro_data['z'] -= gyro_bias['z']

            input = read_variables()

            # normalize all input values
            # UP = 0
            # LEFT = 1
            # FORWARD = 2
            # ROTATE = 3
            # STATE = 4
            input_throttle: float = normalize(input[0], 1000.0, 2000.0, 0.0, 1.0)  # between 0.0 and 1.0
            input_pitch: float = (normalize(input[2], 1000.0, 2000.0, -1.0, 1.0)) * -1
            # -1 for user comfort sake
            # between -1.0 and 1.0. We multiply by -1 because... If the pitch is "full forward" (i.e. 75), that means we want a NEGATIVE pitch (when a plane pitches it's nose down, that is negative, not positive. And when a place pitches it's nose up, pulling back on the stick, it's positive, not negative.) Thus, we need to flip it.
            input_roll: float = normalize(input[1], 1000.0, 2000.0, -1.0, 1.0)  # between -1.0 and 1.0
            input_yaw: float = normalize(input[3], 1000.0, 2000.0, -1.0, 1.0)  # between -1.0 and 1.0

            if input[4] == 1:  # standby mode - switch in "up" or OFF position

                # turn motors off completely
                for i in range(NUM_MOTORS):
                    set_pulse_length(0, i)

                # reset PID's
                roll_last_integral = 0.0
                roll_last_error = 0.0
                pitch_last_integral = 0.0
                pitch_last_error = 0.0
                yaw_last_integral = 0.0
                yaw_last_error = 0.0

                # set last mode
                last_mode = False  # False means standby mode
            elif input[4] == 2:  # flight mode (idle props at least)

                # if last mode was standby (we JUST were turned onto flight mode), perform a check that the throttle isn't high. This is a safety mechanism
                # this prevents an accident where the flight mode switch is turned on but the throttle position is high, which would immediately apply heavy throttle to each motor, shooting it into the air.
                if last_mode == False:  # last mode we were in was standby mode. So, this is the first frame we are going into flight mode
                    if input_throttle > 0.05:  # if throttle is > 5%
                        print("Throttle was set to " + str(
                            input_throttle) + " as soon as flight mode was entered. Throttle must be at 0% when flight mode begins (safety check).")
                    break
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
                roll_i = max(min(roll_i, i_limit), -i_limit)  # constrain within I-term limits
                roll_d: float = pid_roll_kd * (error_rate_roll - roll_last_error) / cycle_time_seconds
                pid_roll: float = roll_p + roll_i + roll_d

                # pitch PID calc
                pitch_p: float = error_rate_pitch * pid_pitch_kp
                pitch_i: float = pitch_last_integral + (error_rate_pitch * pid_pitch_ki * cycle_time_seconds)
                pitch_i = max(min(pitch_i, i_limit), -i_limit)  # constrain within I-term limits
                pitch_d: float = pid_pitch_kd * (error_rate_pitch - pitch_last_error) / cycle_time_seconds
                pid_pitch = pitch_p + pitch_i + pitch_d

                # yaw PID calc
                yaw_p: float = error_rate_yaw * pid_yaw_kp
                yaw_i: float = yaw_last_integral + (error_rate_yaw * pid_yaw_ki * cycle_time_seconds)
                yaw_i = max(min(yaw_i, i_limit), -i_limit)  # constrain within I-term limits
                yaw_d: float = pid_yaw_kd * (error_rate_yaw - yaw_last_error) / cycle_time_seconds
                pid_yaw = yaw_p + yaw_i + yaw_d

                # calculate throttle values
                throttles = []
                throttles[0]: float = adj_throttle + pid_pitch + pid_roll - pid_yaw
                throttles[1]: float = adj_throttle + pid_pitch - pid_roll + pid_yaw
                throttles[2]: float = adj_throttle - pid_pitch + pid_roll + pid_yaw
                throttles[3]: float = adj_throttle - pid_pitch - pid_roll - pid_yaw

                # Adjust throttle according to input
                # RAD -  nevidjeno lupanje boga piatj kako zapravo radi za throttle
                for t in throttles:
                    set_pulse_length(MIN_PULSE_LENGTH + t * (MAX_PULSE_LENGTH - MIN_PULSE_LENGTH))

                # Save state values for next loop
                roll_last_error = error_rate_roll
                pitch_last_error = error_rate_pitch
                yaw_last_error = error_rate_yaw
                roll_last_integral = roll_i
                pitch_last_integral = pitch_i
                yaw_last_integral = yaw_i

                # set last mode
                last_mode = True  # True = flight mode (props spinning, pid active, motors receiving power commands, etc)
            elif input[4]==9:
                print("Controller je iskljucen")
                cleanup()
                exit(0)
            else:  # the input from channel 5 is unexpected
                print(
                    "Channel 5 input '" + str(input[4]) + "' not valid. Is the transmitter turned on and connected?")

                # mark end time
            end = time.time()

            # wait to make the hz correct
            elapsed = end - start
            if elapsed < cycle_time_seconds:
                time.sleep(cycle_time_seconds - elapsed)







    except Exception as e:  # something went wrong

        # Stop the motors
        cleanup()

        exit(1)
