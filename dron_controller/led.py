import gpiod
import time
MOTOR1_PIN = 17
chip = gpiod.Chip("gpiochip4")
motor1_line = chip.get_line(MOTOR1_PIN)
motor1_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
try:
    while True:
        led_line.set_value(1)
        sleep(1)
        led_line.set_value(0)
        sleep(1)
finally:
    led_line.release()

