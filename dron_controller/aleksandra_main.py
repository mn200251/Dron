import time
import threading
import gpiod
import atexit
import signal

from pca9685 import PCA9685, PCA9685_I2C_ADDRESS

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

def pwm_thread():
    global pulse_length, running
    while running:
        line.set_value(1)
        time.sleep(pulse_length / 1000000.0)
        line.set_value(0)
        time.sleep((PERIOD - pulse_length) / 1000000.0)
    print("Nit gotova")

def set_pulse_length_old(new_pulse_length:int):
    global pulse_length
    pulse_length = new_pulse_length
def set_pulse_length(new):
    if softvare_pwm:
        set_pulse_length_old(new)
    else:
        pca9685.set_ESC_PWM(channel,new)

def set_pwm_a_bit_higher_then_max():
    pca9685.set_channel_pwm(0,11)
    print(pca9685.read_channel_pwm(0))
def cleanup():
    global running
    running = False
    time.sleep(0.05)  # Give some time for the thread to exit its loop
    line.set_value(0)  # Ensure the pin is set to 0

def handle_exit(signum, frame):
    cleanup()
    exit(0)


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
    print("This command sets the throttle to the minimum level. This is useful for stopping the motor or setting a safe idle state.")
    print("\t1 : Send max throttle")
    print("This command sets the throttle to the maximum level. Use this carefully as it will make the motor run at full speed.")
    print("\t2 : Run test function")
    print("This command runs a test function to ensure the system is working correctly. The specific details of the test will depend on the implementation of the test function.")
    print("\t3 : Calibrate")
    print("This command initiates the calibration process for the ESC. Calibration is essential to ensure the ESC correctly interprets the throttle range. Follow the instructions provided during calibration carefully.\n It only needs to be done once, just arming is enough for future use")
    print("\t4 : Arm")
    print("This command arms the ESC. Arming the ESC is necessary before it will respond to throttle commands. This is a safety feature to prevent accidental motor starts.")
    print("\t5 : Throttle")
    print("This command allows you to set the throttle to a specific value. The exact method for specifying the throttle value will depend on how you implement the throttle control. This allows for precise control over the motor speed.")
    print("\t6 : Stop")


# gledaj doc
# treba 3 sekunde da drzi max/min, perioda je 20ms => 150 loop
#nesto ne valja negde treba da ima vecu pauzu trrnutno podesi max ali ne stigne min
def calibrate_esc(x):
    print("Hello! Welcome to the ESC throttle range calibration script")
    print("The Pi should be running on SEPARATE power from the ESC's")
    print("This is because the Pi needs to be able to set the throttle to 100% BEFORE the ESC's gain power")
    print(
        "To accomplish this, the Pi will need to be on a different power source (USB) while the ESC's are powered by the LiPo.")
    print("Please ensure that right now the ESC's are NOT powered on")
    print("Press enter to confirm this and when you are ready")
    input("")

    # Set up PWM's
    set_pulse_length(MAX_PULSE_LENGTH)
    print("Set to max throttle (" + str(MAX_PULSE_LENGTH) + " ns)")

    # now ready to power on ESC's
    print("We are now ready to power on the ESC's")
    print("When you power on the ESC's, you will hear a sequence of 3 raising beeps series")
    print("Press enter on your keyboard BEFORE the last beep. (during the 3 beep period).")
    print("I will then go from the max throttle to the min throttle.")
    print(
        "After this, you will hear a confirmation descending beep(s) to confirm that the max and min throttle position "
        "have been saved. Finally 2 single beeps to confirm the arming of the motors.")
    print("Ok, ready to continue?")
    print("1. Plug the power in")
    print("2. Wait for the 3-beep sequence to start")
    print("3. Before the 3th beep, press enter on your keyboard.")

    # min throttle
    print("")
    input("Hit ENTER before the fourth beep! Waiting for enter...")

    # send min throttle
    set_pulse_length(MIN_PULSE_LENGTH)

    # confirmation beeps
    print("You should now hear confirmation beeps")
    print("After you hear those, your ESC's are calibrated. You may power down :)")

    # program complete
    print("")
    print("Calibration complete! ")
    

def arm_esc():
    time.sleep(0.2)
    set_pulse_length(1100)
    time.sleep(2)
    set_pulse_length(MIN_PULSE_LENGTH)
def test():
    MPL = MAX_PULSE_LENGTH
    for i in range(MIN_PULSE_LENGTH, MPL + 1, 5):
        print("Pulse length =", i)
        set_pulse_length(i)
        time.sleep(PERIOD/1000000.0)

    print("STOP")
    set_pulse_length(MIN_PULSE_LENGTH )  # Back to minimum throttle


def loop():
    global pulse_length, running
    while True:
        data = input("Enter command : ")
        if data == '0':
            print("Sending minimum throttle")
            set_pulse_length(MIN_PULSE_LENGTH )
        elif data == '1':
            print("Sending maximum throttle")
            set_pulse_length(MAX_PULSE_LENGTH )
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
            time_len = input("Enter time (in s):")
            prev=pulse_length
            set_pulse_length(int(length))
            time.sleep(int(time_len))
            set_pulse_length(prev)
            print("Done")
        elif data == '6':
            if softvare_pwm:
                running = False
                thread.join()
            else:
                pca9685.set_channel_pwm(channel,0)
            break
        else:
            print("Invalid input")

channel=-1
softvare_pwm=False
if __name__ == "__main__":
    if softvare_pwm:
        # Register the cleanup function to be called on program exit
        atexit.register(cleanup)

        # Register signal handlers for graceful exit on signals
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        # Start the PWM in a separate thread
        thread = threading.Thread(target=pwm_thread)
        thread.start()
    else:
        pca9685 = PCA9685(i2c_address=PCA9685_I2C_ADDRESS)

        pca9685.reset()

        pca9685.init()


    setup()

    loop()




