
import time
import gpiod

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs

# Define GPIO line numbers
SERVO1_PIN = 17
SERVO2_PIN = 27

# Set up GPIO chip and line
chip = gpiod.Chip('gpiochip4')
motor1_line = chip.get_line(SERVO1_PIN)
motor2_line = chip.get_line(SERVO2_PIN)

# Request output direction for the GPIO line
motor1_line.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)
motor2_line.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)

def set_servo_pulse(pulse_length):
    #line.set_active(True)
    motor1_line.set_value(1)
    motor2_line.set_value(1)
    time.sleep(pulse_length / 1000000.0)
    #line.set_active(False)
    motor1_line.set_value(0)
    motor2_line.set_value(0)

def setup():
    print("READY - PLEASE SEND INSTRUCTIONS AS FOLLOWING :")
    print("\t0 : Send min throttle")
    print("\t1 : Send max throttle")
    print("\t2 : Run test function")

def calibrate_esc(pulse_length):
    set_servo_pulse(pulse_length)
    time.sleep(1)  # Assuming 5 seconds for calibration
    set_servo_pulse(MIN_PULSE_LENGTH)  # Back to minimum throttle

def test():

    MPL = MAX_PULSE_LENGTH
    for i in range(MIN_PULSE_LENGTH, MPL + 1, 5):
        print("Pulse length =", i)
        set_servo_pulse(i)
        time.sleep(0.2)

    print("STOP")
    set_servo_pulse(MIN_PULSE_LENGTH)  # Back to minimum throttle

def loop():
    while True:
        data = input("Enter command (0, 1, or 2): ")
        if data == '0':
            print("Sending minimum throttle")
            set_servo_pulse(MIN_PULSE_LENGTH)
        elif data == '1':
            print("Sending maximum throttle")
            set_servo_pulse(MAX_PULSE_LENGTH)
        elif data == '2':
            print("Running test function...")
            test()
        else: print("Invalid input")

if __name__ == "__main__":
    setup()
    loop()

