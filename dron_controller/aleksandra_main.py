import time
import threading
import gpiod
import atexit
import signal

from pca9685 import PCA9685, PCA9685_I2C_ADDRESS
from mpu6050 import mpu6050

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs
PERIOD = 20000  # Period length in µs
# Define GPIO line numbers
SERVO_PIN = 17

# Set up GPIO chip and line
chip = gpiod.Chip('gpiochip4')
line = chip.get_line(SERVO_PIN)

# Request output direction for the GPIO line
line.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)

# Initialize pulse_length with a default value
pulse_length = MIN_PULSE_LENGTH
running = True


#OLD SOFTVARE PWM
def pwm_thread():
    global pulse_length, running
    while running:
        line.set_value(1)
        time.sleep(pulse_length / 1000000.0)
        line.set_value(0)
        time.sleep((PERIOD - pulse_length) / 1000000.0)
    print("Nit gotova")
def set_pulse_length(new_pulse_length: int):
    global pulse_length
    pulse_length = new_pulse_length
def cleanup():
    global running
    running = False
    time.sleep(0.05)  # Give some time for the thread to exit its loop
    line.set_value(0)  # Ensure the pin is set to 0
def handle_exit(signum, frame):
    cleanup()
    exit(0)



def setup():
    print("READY - PLEASE SEND INSTRUCTIONS AS FOLLOWING :")
    print("\t0 : Send min throttle")
    print("This command sets the throttle to the minimum level. This is useful for stopping the motor or setting a safe idle state.")
    print("\t1 : Send max throttle")
    print("This command sets the throttle to the maximum level. Use this carefully as it will make the motor run at full speed.")
    print("\t2 : Run test function")
    print("This command runs a test function to ensure the system is working correctly. It slowly increases the throttle until maximum.")
    print("\t3 : Calibrate")
    print("This command initiates the calibration process for the ESC. Calibration is essential to ensure the ESC correctly interprets the throttle range. Follow the instructions provided during calibration carefully.\n It only needs to be done once, just arming is enough for future use")
    print("\t4 : Arm")
    print("This command arms the ESC. Arming the ESC is necessary before it will respond to throttle commands. This is a safety feature to prevent accidental motor starts.")
    print("\t5 : Throttle")
    print("This command allows you to set the throttle to a specific value for a specified duration. This allows for precise control over the motor speed.")
    print("\t6 : Calibrate the sensor")
    print("This command allows you to set the throttle to a specific value. The exact method for specifying the throttle value will depend on how you implement the throttle control. This allows for precise control over the motor speed.")
    print("\t7 : Read the sensor")
    print("This command allows you to set the throttle to a specific value. The exact method for specifying the throttle value will depend on how you implement the throttle control. This allows for precise control over the motor speed.")
    print("\t8 : Stop")

def test(channel, pca9685):
    MPL = MAX_PULSE_LENGTH
    for i in range(MIN_PULSE_LENGTH, MPL + 1, 5):
        print("Pulse length =", i)
        pca9685.set_ESC_PWM(channel, i)
        time.sleep(PERIOD / 1000000.0)

    print("STOP")
    pca9685.set_ESC_PWM(channel, MIN_PULSE_LENGTH)  # Back to minimum throttle

def set_throttle_for_duration(pca9685, channel):
    length = input("Enter pulse length (in µs):")
    time_len = input("Enter time (in s):")
    prev = pulse_length
    set_pulse_length(int(length))
    time.sleep(int(time_len))
    set_pulse_length(prev)
    print("Done")

def calibrate_sensors(mpu):
    print("Calibrating...")
    bg = mpu.calibrate_gyroscope(1)
    ba = mpu.calibrate_accelerometer(1)
    print("Calibrating done")
    return ba, bg
def read_sensor_data(mpu, accel_range, gyro_range, ba, bg):
    print("Getting data...")
    accel_data = mpu.get_accel_data(accel_range)
    print("Accelerometer data:")
    print(accel_data['x'] - ba['x'])
    print(accel_data['y'] - ba['y'])
    print(accel_data['z'] - ba['z'])
    gyro_data = mpu.get_gyro_data(gyro_range)
    print("Gyro data:")
    print(gyro_data['x'] - bg['x'])
    print(gyro_data['y'] - bg['y'])
    print(gyro_data['z'] - bg['z'])

def loop(pca9685, mpu):
    global pulse_length, running
    gyro_range = mpu.read_gyro_range(True)
    accel_range = mpu.read_accel_range(True)
    bg = mpu.calibrate_gyroscope(1)
    ba = mpu.calibrate_accelerometer(1)
    channel =int( input("Enter channel you want to manipulate(-1 for all):"))

    while True:
        data = input("Enter command : ")
        if data == '0':
            print("Sending minimum throttle")
            pca9685.set_ESC_PWM(channel, MIN_PULSE_LENGTH)
        elif data == '1':
            print("Sending maximum throttle")
            pca9685.set_ESC_PWM(channel, MAX_PULSE_LENGTH)
        elif data == '2':
            print("Running test function...")
            test(channel,pca9685)
        elif data == '3':
            print("Calibrating...")
            pca9685.calibrate_esc(channel)
            print("Calibrating done")
        elif data == '4':
            print("Arming...")
            pca9685.arm_esc(channel)
        elif data == '5':
            set_throttle_for_duration(pca9685, channel)
        elif data == '6':
            ba, bg = calibrate_sensors(mpu)
        elif data == '7':
            read_sensor_data(mpu, accel_range, gyro_range, ba, bg)
        elif data == '8':
            pca9685.set_channel_pwm(channel, 0)
            break
        else:
            print("Invalid input")


if __name__ == "__main__":
    pca9685 = PCA9685(i2c_address=PCA9685_I2C_ADDRESS)

    pca9685.reset()

    pca9685.init()

    mpu = mpu6050(0x68)
    mpu.reset_mpu6050()
    mpu.init()
    setup()

    loop(pca9685,mpu)
