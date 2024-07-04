import time
import gpiod

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


def set_servo_high_temporarily(pulse_length):
    # line.set_active(True)
    line.set_value(1)
    time.sleep(pulse_length / 1000000.0)
    # line.set_active(False)
    line.set_value(0)


def toggle_servo_for_single_period(high_length):
    # line.set_active(True)
    line.set_value(1)
    time.sleep(high_length / 1000000.0)
    # line.set_active(False)
    line.set_value(0)
    time.sleep((PERIOD - high_length) / 1000000.0)


def setup():
    print("READY - PLEASE SEND INSTRUCTIONS AS FOLLOWING :")
    print("\t0 : Send min throttle")
    print("\t1 : Send max throttle")
    print("\t2 : Run test function")
    print("\t3 : Calibrate")
    print("\t4 : Arm")
    print("\t5 : Throttle")


# gledaj doc
# treba 3 sekunde da drzi max/min, perioda je 20ms => 150 loop
#nesto ne valja negde treba da ima vecu pauzu trrnutno podesi max ali ne stigne min
def calibrate_esc(x):
    #for i in range(0, 70):
    #toggle_servo_for_single_period((MAX_PULSE_LENGTH + MIN_PULSE_LENGTH) / 2)
    #for i in range(0, 10):
    #toggle_servo_for_single_period(MIN_PULSE_LENGTH)
    toggle_servo_for_single_period(MAX_PULSE_LENGTH)
    print("Max start")
    #for i in range(0, 800):
    #    toggle_servo_for_single_period(MAX_PULSE_LENGTH )
    print("Max done")
    #time.sleep(0.2 )
    print("Min start")
    for i in range(0, 200):
        toggle_servo_for_single_period(MIN_PULSE_LENGTH)
    print("Min done")
    

def arm_esc():
    time.sleep(0.2)
    toggle_servo_for_single_period((MAX_PULSE_LENGTH + MIN_PULSE_LENGTH) / 2)
    toggle_servo_for_single_period(MIN_PULSE_LENGTH)
    
def test():
    MPL = MAX_PULSE_LENGTH
    for i in range(MIN_PULSE_LENGTH, MPL + 1, 5):
        print("Pulse length =", i)
        set_servo_high_temporarily(i)
        time.sleep(0.02 - i / 1000000.0)

    print("STOP")
    set_servo_high_temporarily(MIN_PULSE_LENGTH)  # Back to minimum throttle


def loop():
    while True:
        data = input("Enter command : ")
        if data == '0':
            print("Sending minimum throttle")
            set_servo_high_temporarily(MIN_PULSE_LENGTH)
        elif data == '1':
            print("Sending maximum throttle")
            set_servo_high_temporarily(MAX_PULSE_LENGTH)
        elif data == '2':
            print("Running test function...")
            test()
        elif data == '3':
            print("Calibrating...")
            calibrate_esc(1)
            print("Calibrating done")
        elif data == '4':
            print("Arming...")
            arm_esc()
        elif data == '5':
            length= input("Enter pulse length (in µs):")
            for i in range(0, 100):
                toggle_servo_for_single_period(int(length))
            print("Done")
        else:
            print("Invalid input")


if __name__ == "__main__":
    setup()
    loop()



