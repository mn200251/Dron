import time
import threading
import gpiod
import atexit
import signal
import random
import ctypes
"""
-single_pwm_thread_one_motor_sleep_constant_pulse
-single_pwm_thread_one_motor_sleep_volatile_pulse

-four_pwm_thread_one_motor_sleep_constant_pulse
four_pwm_thread_one_motor_sleep_volatile_pulse

-single_pwm_thread_one_motor_busywait_constant_pulse
-single_pwm_thread_one_motor_busywait_volatile_pulse

-four_pwm_thread_one_motor_busywait_constant_pulse
four_pwm_thread_one_motor_busywait_volatile_pulse

-single_pwm_thread_four_motor_sleep_constant_pulse
single_pwm_thread_four_motor_sleep_volatile_pulse

-single_pwm_thread_four_motor_busywait_constant_pulse
single_pwm_thread_four_motor_busywait_volatile_pulse
"""

# Customize here pulse lengths as needed
MIN_PULSE_LENGTH = 1000  # Minimum pulse length in �s
MAX_PULSE_LENGTH = 2000  # Maximum pulse length in �s
PERIOD = 20000
SLEEP_ERROR = 100# Period in �s (50Hz frequency)
MICRO_TO_SEC= 1000000.0
NUM_THREADS = 4
NUM_SLEEPS = 5
# Define GPIO line numbers
SERVO_PINS = [17,27,22,23]

# Set up GPIO chip and line
chip = gpiod.Chip('gpiochip4')
lines = [chip.get_line(SERVO_PINS[0]),chip.get_line(SERVO_PINS[1]),chip.get_line(SERVO_PINS[2]),chip.get_line(SERVO_PINS[3])]

# Request output direction for the GPIO line
for line in lines:
    line.request(consumer="servo", type=gpiod.LINE_REQ_DIR_OUT)

# Initialize pulse_length with a default value
pulse_lengths = [MIN_PULSE_LENGTH] * NUM_THREADS
running = True

locks = [threading.Lock() for _ in range(NUM_THREADS)]
errors_first_sleep = [[] for _ in range(NUM_THREADS)]
errors_second_sleep = [[] for _ in range(NUM_THREADS)]

# Load the C standard library
libc = ctypes.CDLL('libc.so.6')

# Define usleep function
libc.usleep.argtypes = [ctypes.c_uint]
libc.usleep.restype = ctypes.c_int

def usleep(microseconds):
    libc.usleep(microseconds)

def busy_wait(duration_microseconds):
    end_time = time.time() + duration_microseconds / MICRO_TO_SEC
    while time.time() < end_time:
        pass

def pwm_thread_one_motor_sleep(index):
    global running
    while running:
        lines[index].set_value(1)

        # Measure the actual sleep time for the first sleep call

        with locks[index]:
            pulses = pulse_lengths[index]
        start_time = time.time()
        time.sleep(pulses / MICRO_TO_SEC)
        end_time = time.time()

        actual_sleep_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_sleep = actual_sleep_time - pulses
        errors_first_sleep[index].append(error_first_sleep)

        lines[index].set_value(0)

        # Measure the actual sleep time for the second sleep call
        start_time = time.time()
        time.sleep((PERIOD - pulses) / MICRO_TO_SEC)
        end_time = time.time()

        actual_sleep_time = (end_time - start_time) * MICRO_TO_SEC
        intended_sleep_time = (PERIOD - pulses)
        error_second_sleep = actual_sleep_time - intended_sleep_time
        errors_second_sleep[index].append(error_second_sleep)

    #print(f"Thread {index} finished")
def pwm_thread_one_motor_busywait(index):
    global running
    while running:
        lines[index].set_value(1)

        # Measure the actual busy wait time for the first busy wait call
        start_time = time.time()
        with locks[index]:
            pulses = pulse_lengths[index]
        busy_wait(pulses)
        end_time = time.time()

        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        intended_wait_time = pulses
        error_first_wait = actual_wait_time - intended_wait_time
        errors_first_sleep[index].append(error_first_wait)

        lines[index].set_value(0)

        # Measure the actual busy wait time for the second busy wait call
        start_time = time.time()
        busy_wait(PERIOD - pulses)
        end_time = time.time()

        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        intended_wait_time = (PERIOD - pulses)
        error_second_wait = actual_wait_time - intended_wait_time
        errors_second_sleep[index].append(error_second_wait)

    #print(f"Thread {index} finished")
def pwm_thread_all_motors_busywait():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with locks[0]:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_THREADS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        start_time = time.time()
        busy_wait(first_pulse_length)
        end_time = time.time()

        # Calculate and record the error for the first motor
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_wait = actual_wait_time - first_pulse_length
        # if(error_first_wait<0):
        #     print(""+str(actual_wait_time)+" "+str(first_pulse_length)+" "+str(sorted_pulses))
        errors_first_sleep[0].append(abs(error_first_wait))

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_THREADS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            start_time = time.time()
            busy_wait(next_wait_time)
            end_time = time.time()

            # Calculate and record the error for the current motor
            actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
            error_next_wait = actual_wait_time - next_wait_time
            errors_first_sleep[i].append(abs(error_next_wait))

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Busy-wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        start_time = time.time()
        busy_wait(remaining_time)
        end_time = time.time()

        # Calculate and record the error for the remaining time
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_remaining_wait = actual_wait_time - remaining_time
        errors_second_sleep[0].append(abs(error_remaining_wait))  # Using errors_second_sleep[0] to store remaining time errors

    print("PWM control thread finished")
def pwm_thread_all_motors_sleep():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with locks[0]:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_THREADS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        start_time = time.time()
        time.sleep(first_pulse_length / MICRO_TO_SEC)
        end_time = time.time()

        # Calculate and record the error for the first motor
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_wait = actual_wait_time - first_pulse_length
        errors_first_sleep[0].append(error_first_wait)

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_THREADS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            start_time = time.time()
            time.sleep(next_wait_time / MICRO_TO_SEC)
            end_time = time.time()

            # Calculate and record the error for the current motor
            actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
            error_next_wait = actual_wait_time - next_wait_time
            errors_first_sleep[i].append(error_next_wait)

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Busy-wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        start_time = time.time()
        time.sleep(remaining_time / MICRO_TO_SEC)
        end_time = time.time()

        # Calculate and record the error for the remaining time
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_remaining_wait = actual_wait_time - remaining_time
        errors_second_sleep[0].append(error_remaining_wait)  # Using errors_second_sleep[0] to store remaining time errors

    print("PWM control thread finished")

def pwm_thread_all_motors_combined():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with locks[0]:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_THREADS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        start_time = time.time()
        time.sleep((first_pulse_length-SLEEP_ERROR )/ MICRO_TO_SEC)
        end_time = time.time()
        busy_wait( first_pulse_length  - (end_time - start_time) * MICRO_TO_SEC)
        end_time = time.time()

        # Calculate and record the error for the first motor
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_wait = actual_wait_time - first_pulse_length
        errors_first_sleep[0].append(abs(error_first_wait))

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_THREADS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            start_time = time.time()
            busy_wait(next_wait_time)
            end_time = time.time()

            # Calculate and record the error for the current motor
            actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
            error_next_wait = actual_wait_time - next_wait_time
            errors_first_sleep[i].append(abs(error_next_wait))

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Busy-wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        start_time = time.time()
        time.sleep((remaining_time - SLEEP_ERROR) / MICRO_TO_SEC)
        end_time = time.time()
        busy_wait( remaining_time - ( end_time - start_time) * MICRO_TO_SEC )
        end_time = time.time()

        # Calculate and record the error for the remaining time
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_remaining_wait = actual_wait_time - remaining_time
        errors_second_sleep[0].append(abs(error_remaining_wait)  )# Using errors_second_sleep[0] to store remaining time errors

    print("PWM control thread finished")

def pwm_thread_all_motors_combined_c():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with locks[0]:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_THREADS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        start_time = time.time()
        usleep(first_pulse_length-SLEEP_ERROR )
        end_time = time.time()
        busy_wait( first_pulse_length  - (end_time - start_time) * MICRO_TO_SEC)
        end_time = time.time()

        # Calculate and record the error for the first motor
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_wait = actual_wait_time - first_pulse_length
        errors_first_sleep[0].append(abs(error_first_wait))

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_THREADS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            start_time = time.time()
            busy_wait(next_wait_time)
            end_time = time.time()

            # Calculate and record the error for the current motor
            actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
            error_next_wait = actual_wait_time - next_wait_time
            errors_first_sleep[i].append(abs(error_next_wait))

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Busy-wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        start_time = time.time()
        usleep(remaining_time - SLEEP_ERROR)
        end_time = time.time()
        busy_wait( remaining_time - ( end_time - start_time) * MICRO_TO_SEC )
        end_time = time.time()

        # Calculate and record the error for the remaining time
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_remaining_wait = actual_wait_time - remaining_time
        errors_second_sleep[0].append(abs(error_remaining_wait)  )# Using errors_second_sleep[0] to store remaining time errors

    print("PWM control thread finished")


def pwm_thread_all_motors_sleep_c():
    global running
    while running:
        # Set GPIO high for all motors
        for line in lines:
            line.set_value(1)

        # Lock the pulse lengths to avoid concurrent modification
        with locks[0]:
            sorted_pulses = sorted((pulse_lengths[i], i) for i in range(NUM_THREADS))

        # Busy-wait for the first motor's pulse length
        first_pulse_length, first_index = sorted_pulses[0]
        start_time = time.time()
        usleep(int(first_pulse_length))
        end_time = time.time()

        # Calculate and record the error for the first motor
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_first_wait = actual_wait_time - first_pulse_length
        errors_first_sleep[0].append(error_first_wait)

        # Set GPIO low for the first motor
        lines[first_index].set_value(0)

        # Busy-wait for the subsequent motors' pulse lengths
        previous_pulse_length = first_pulse_length
        for i in range(1, NUM_THREADS):
            pulse_length, index = sorted_pulses[i]
            next_wait_time = pulse_length - previous_pulse_length

            start_time = time.time()
            usleep(int(next_wait_time ))
            end_time = time.time()

            # Calculate and record the error for the current motor
            actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
            error_next_wait = actual_wait_time - next_wait_time
            errors_first_sleep[i].append(error_next_wait)

            # Set GPIO low for the current motor
            lines[index].set_value(0)

            previous_pulse_length = pulse_length

        # Busy-wait for the rest of the period
        remaining_time = PERIOD - previous_pulse_length
        start_time = time.time()
        usleep(int(remaining_time))
        end_time = time.time()

        # Calculate and record the error for the remaining time
        actual_wait_time = (end_time - start_time) * MICRO_TO_SEC
        error_remaining_wait = actual_wait_time - remaining_time
        errors_second_sleep[0].append(error_remaining_wait)  # Using errors_second_sleep[0] to store remaining time errors

    print("PWM control thread finished")


def set_pulse_length(new_pulse_length, index):
    global pulse_lengths
    pulse_lengths[index] = new_pulse_length

def cleanup():
    global running
    running = False
    time.sleep(0.05)  # Give some time for the thread to exit its loop
    for line in lines:
        line.set_value(0)  # Ensure the pin is set to 0

def handle_exit(signum, frame):
    cleanup()
    exit(0)

def calculate_errors(errors):
    min_error = min(errors)
    max_error = max(errors)
    avg_error = sum(errors) / len(errors)
    return min_error, max_error, avg_error

def test_multiple_pwm_thread_one_motor(mode):
    global running

    running = True
    if mode==0:#sleep
        threads = [threading.Thread(target=pwm_thread_one_motor_sleep, args=(i,)) for i in range(NUM_THREADS)]
    elif mode==1:
        threads = [threading.Thread(target=pwm_thread_one_motor_busywait, args=(i,)) for i in range(NUM_THREADS)]
    else:
        print("Unknown mode")
    for thread in threads:
        thread.start()

    # Run the threads for around 5 seconds to collect error data
    for i in range(0,250):
        for i in range(NUM_THREADS):
            with locks[i]:
                pulse_lengths[i] = random.randint(MIN_PULSE_LENGTH, MAX_PULSE_LENGTH)
        time.sleep(PERIOD / MICRO_TO_SEC)


    # Stop the threads
    running = False
    for thread in threads:
        thread.join()


    # Calculate and print errors for each thread
    for i in range(NUM_THREADS):
        min_error_first, max_error_first, avg_error_first = calculate_errors(errors_first_sleep[i])
        min_error_second, max_error_second, avg_error_second = calculate_errors(errors_second_sleep[i])

        errors_first_sleep[i].clear()
        errors_second_sleep[i].clear()

        print(f"Thread {i} - First sleep - Min Error: {min_error_first:.6f} us, Max Error: {max_error_first:.6f} us, Avg Error: {avg_error_first:.6f} us")
        print(f"Thread {i} - Second sleep - Min Error: {min_error_second:.6f} us, Max Error: {max_error_second:.6f} us, Avg Error: {avg_error_second:.6f} us")

def test_one_pwm_thread_all_motors(mode):
    global running

    running = True
    if mode==0:#sleep
        thread = threading.Thread(target=pwm_thread_all_motors_sleep, args=())
    elif mode==1:#busywait
        thread = threading.Thread(target=pwm_thread_all_motors_busywait, args=())
    elif mode==2:#combined
        thread = threading.Thread(target=pwm_thread_all_motors_combined, args=())
    elif mode==3:#C/C++
        thread = threading.Thread(target=pwm_thread_all_motors_sleep_c, args=())
    elif mode == 4:  # C/C++
        thread = threading.Thread(target=pwm_thread_all_motors_combined_c, args=())
    else:
        print("Unknown mode")
    thread.start()

    # Run the threads for around 5 seconds to collect error data
    for i in range(0,250):
        for i in range(NUM_THREADS):
            with locks[i]:
                pulse_lengths[i] = random.randint(MIN_PULSE_LENGTH, MAX_PULSE_LENGTH)
        time.sleep(PERIOD / MICRO_TO_SEC)


    # Stop the thread
    running = False
    thread.join()


    # Calculate and print errors for each thread
    for i in range(NUM_SLEEPS-1):
        min_error_first, max_error_first, avg_error_first = calculate_errors(errors_first_sleep[i])
        errors_first_sleep[i].clear()
        print(f"Thread - {i}  sleep - Min Error: {min_error_first:.6f} us, Max Error: {max_error_first:.6f} us, Avg Error: {avg_error_first:.6f} us")
    min_error_second, max_error_second, avg_error_second = calculate_errors(errors_second_sleep[0])
    errors_second_sleep[0].clear()
    print(f"Thread - {NUM_SLEEPS-1}  sleep - Min Error: {min_error_second:.6f} us, Max Error: {max_error_second:.6f} us, Avg Error: {avg_error_second:.6f} us")


if __name__ == "__main__":
    # Emergency brake if the pins are on
    # for line in lines:
    #     line.set_value(0)
    # exit(1)
    print("This test is used to compare different implementations of pwm threading.")
    print("Conditions include handling four motors and with pulses ranging from 1000 to 2000 us.")
    print("(Busy waits can be shorter then asked times possibly due to the precision of the time.time()")
    print("\n")
    # Register the cleanup function to be called on program exit
    atexit.register(cleanup)

    # Register signal handlers for graceful exit on signals
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # print("Testing with four threads each handling a single pwm thread using sleep:")
    # test_multiple_pwm_thread_one_motor(0)
    # print("\n")
    # time.sleep(1)
    # print("Testing with four threads each handling a single pwm thread using busywait:")
    # test_multiple_pwm_thread_one_motor(1)
    # print("\n")
    # time.sleep(1)
    # print("Testing a single thread handling all pwm threading using sleep:")
    # test_one_pwm_thread_all_motors(0)
    # print("\n")
    # time.sleep(1)
    # print("Testing a single thread handling all pwm threading using  busywait:")
    # test_one_pwm_thread_all_motors(1)
    # print("\n")
    # time.sleep(1)
    # print("Testing a single thread handling all pwm threading using combined sleep and busy wait:")
    # test_one_pwm_thread_all_motors(2)
    # print("\n")
    # time.sleep(1)
    # print("Testing a single thread handling all pwm threading using usleep from C:")
    # test_one_pwm_thread_all_motors(3)
    # print("\n")
    # time.sleep(1)
    print("Testing a single thread handling all pwm threading using busywait and usleep from C:")
    test_one_pwm_thread_all_motors(4)
    print("\n")
    print("Test done.")