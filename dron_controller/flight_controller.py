import time
import threading
import gpiod
import atexit
import signal

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs
PERIOD = 20000  # Period in µs (50Hz frequency)

MILLI_TO_SEC= 1000000.0

# Define GPIO line numbers
MOTOR_1_PIN = 17
MOTOR_2_PIN = 27
MOTOR_3_PIN = 22
MOTOR_4_PIN = 23

# Set up GPIO chip and line
chip = gpiod.Chip('gpiochip4')
line_motor_1 = chip.get_line(MOTOR_1_PIN)
line_motor_2 = chip.get_line(MOTOR_2_PIN)
line_motor_3 = chip.get_line(MOTOR_3_PIN)
line_motor_4 = chip.get_line(MOTOR_4_PIN)

# Request output direction for the GPIO line
line_motor_1.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)
line_motor_2.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)
line_motor_3.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)
line_motor_4.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)

# Initialize pulse_length with a default value
pulse_length_motor_1 = MIN_PULSE_LENGTH
pulse_length_motor_2 = MIN_PULSE_LENGTH
pulse_length_motor_3 = MIN_PULSE_LENGTH
pulse_length_motor_4 = MIN_PULSE_LENGTH

running = True
lock = threading.Lock()
def pwm_thread():
    global pulse_length_motor_1,pulse_length_motor_2,pulse_length_motor_3,pulse_length_motor_4, running

    while running:
        # Start every period with 1 on all line
        line_motor_1.set_value(1)
        line_motor_2.set_value(1)
        line_motor_3.set_value(1)
        line_motor_4.set_value(1)
        # Read pulse lengths safely
        with lock:
            pulses =[ pulse_length_motor_1, pulse_length_motor_2, pulse_length_motor_3,pulse_length_motor_4]
        pulses.sort()

        # CLear line and await next  - Marko samo za tebe sekvencijalno a ne loop
        time.sleep(pulses[0] / MILLI_TO_SEC)
        line_motor_1.set_value(0)
        time.sleep(pulses[1]-pulses[0] / MILLI_TO_SEC)
        line_motor_2.set_value(0)
        time.sleep(pulses[2]-pulses[1] / MILLI_TO_SEC)
        line_motor_3.set_value(0)
        time.sleep(pulses[3] - pulses[2] / MILLI_TO_SEC)
        line_motor_4.set_value(0)

        # Wait out the rest of the period
        time.sleep((PERIOD - pulses[3]) / MILLI_TO_SEC)
    print("Nit gotova")








