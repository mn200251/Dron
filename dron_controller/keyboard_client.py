import threading
import time
from pynput import keyboard

# Indices for each control variable
UP = 0
LEFT = 1
FORWARD = 2
ROTATE = 3
STATE = 4




# Array to keep track of active threads and their stop events
active_threads = [None, None, None, None]
update_time=0.025
min_value=1000
max_value=2000
default=1500
listener=None


# Lock for thread-safe updates
variables_lock = threading.Lock()
# Global variables array
variables = [default]*5

def read_variables():
    with variables_lock:
        return variables.copy()
def key_listener():
    global listener
    def on_press(key):
        increment = 5
        try:
            if key.char == 'w':
                start_variable(UP, increment)
            elif key.char == 's':
                start_variable(UP, -increment)
            elif key.char == 'a':
                start_variable(ROTATE, increment)
            elif key.char == 'd':
                start_variable(ROTATE, -increment)
            elif key.char.isdigit():
                set_state(int(key.char))
        except AttributeError:
            if key == keyboard.Key.left:
                start_variable(LEFT, increment)
            elif key == keyboard.Key.right:
                start_variable(LEFT, -increment)
            elif key == keyboard.Key.up:
                start_variable(FORWARD, increment)
            elif key == keyboard.Key.down:
                start_variable(FORWARD, -increment)

    def on_release(key):
        try:
            if key.char in ['w', 's']:
                stop_variable(UP)
            elif key.char in ['a', 'd']:
                stop_variable(ROTATE)
        except AttributeError:
            if key in [keyboard.Key.left, keyboard.Key.right]:
                stop_variable(LEFT)
            elif key in [keyboard.Key.up, keyboard.Key.down]:
                stop_variable(FORWARD)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener

def update_value(index, increment, stop_event):
    global variables
    while not stop_event.is_set():
        with variables_lock:
            if variables[index]<max_value and variables[index]>min_value:
                variables[index] += increment
            print(""+str(index)+": "+ str(variables[index]))
        time.sleep(update_time)


def start_variable(index, increment):
    global active_threads
    if active_threads[index] is None or not active_threads[index][0].is_alive():
        stop_event = threading.Event()
        thread = threading.Thread(target=update_value, args=(index, increment, stop_event))
        thread.daemon = True
        thread.start()
        active_threads[index] = (thread, stop_event)

def stop_variable(index):
    global variables
    with variables_lock:
        variables[index] = default
        print("" + str(index) + ": " + str(variables[index]))
    if active_threads[index] is not None:
        thread, stop_event = active_threads[index]
        stop_event.set()
        thread.join()
        active_threads[index] = None

def set_state(value):
    global variables
    with variables_lock:
        variables[STATE] = value
        print("" + str(STATE) + ": " + str(variables[STATE]))
    if value == 9:
        # Stop all active threads
        for index in range(len(active_threads)):
            if active_threads[index] is not None:
                thread, stop_event = active_threads[index]
                stop_event.set()
                thread.join()
                active_threads[index] = None

        # Disable the key listener
        if not listener is None:
            listener.stop()

if __name__ == "__main__":
    x=key_listener()
    print("is it blocking")
    x.join()

