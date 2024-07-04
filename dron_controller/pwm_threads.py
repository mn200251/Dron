import time
import threading
import gpiod
import atexit
import signal

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in µs
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in µs
PERIOD = 20000  # Period in µs (50Hz frequency)

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

def set_pulse_length(new_pulse_length):
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

def main():
    global pulse_length, running

    # Register the cleanup function to be called on program exit
    atexit.register(cleanup)
    
    # Register signal handlers for graceful exit on signals
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Start the PWM in a separate thread
    thread = threading.Thread(target=pwm_thread)
    thread.start()

    # Main loop to handle user input
    try:
        while True:
            data = input("Enter pulse length (in µs) or 'exit' to quit: ")
            if data.lower() == 'exit':
                running = False
                thread.join()  # Wait for the PWM thread to finish
                break
            try:
                new_pulse_length = int(data)
                if MIN_PULSE_LENGTH <= new_pulse_length <= MAX_PULSE_LENGTH:
                    set_pulse_length(new_pulse_length)
                else:
                    print(f"Please enter a value between {MIN_PULSE_LENGTH} and {MAX_PULSE_LENGTH}.")
            except ValueError:
                print("Invalid input, please enter an integer.")
    except KeyboardInterrupt:
        pass

    # Ensure the cleanup is done even if the user interrupts with Ctrl+C
    cleanup()

if __name__ == "__main__":
    main()
