import time
from mpu6050 import mpu6050
import math


def calibrate_mpu6050(mpu, duration=5):
    """
    Calibrate the accelerometer and gyroscope biases.

    :param mpu: The mpu6050 object.
    :param duration: The duration in seconds to average the readings over.
    :return: A dictionary with the calculated biases for accelerometer and gyroscope.
    """
    num_samples = duration * 100  # Taking 100 samples per second
    accel_bias = {'x': 0.0, 'y': 0.0, 'z': 0.0}
    gyro_bias = {'x': 0.0, 'y': 0.0, 'z': 0.0}

    gyro_range = mpu.read_gyro_range(True)
    accel_range = mpu.read_accel_range(True)

    for _ in range(num_samples):
        accel_data = mpu.get_accel_data(accel_range)
        gyro_data = mpu.get_gyro_data(gyro_range)

        accel_bias['x'] += accel_data['x']
        accel_bias['y'] += accel_data['y']
        accel_bias['z'] += accel_data['z']

        gyro_bias['x'] += gyro_data['x']
        gyro_bias['y'] += gyro_data['y']
        gyro_bias['z'] += gyro_data['z']

        time.sleep(0.01)  # Sleep for 10 milliseconds between samples

    accel_bias['x'] /= num_samples
    accel_bias['y'] /= num_samples
    accel_bias['z'] /= num_samples
    gyro_bias['x'] /= num_samples
    gyro_bias['y'] /= num_samples
    gyro_bias['z'] /= num_samples

    # Adjust the accelerometer bias to account for gravity on the Z-axis
    accel_bias['z'] -= mpu.GRAVITIY_MS2

    return {'accel_bias': accel_bias, 'gyro_bias': gyro_bias}


def init(mpu):
    # Set ranges to default values
    mpu.set_accel_range(mpu.ACCEL_RANGE_2G)
    mpu.set_gyro_range(mpu.GYRO_RANGE_250DEG)

    # Set the low pass filter to 5
    mpu.set_filter_range(mpu.FILTER_BW_5)

    # Disable temp since not in use
    mpu.disable_temp_sensor()


def read_and_write_mpu6050_data(mpu):
    # Calibrate biases for accelerometer and gyroscope
    biases = calibrate_mpu6050(mpu)
    accel_bias = biases['accel_bias']
    gyro_bias = biases['gyro_bias']
    print(f"Accelerometer Bias: {accel_bias}")
    print(f"Gyroscope Bias: {gyro_bias}")

    gyro_range = mpu.read_gyro_range(True)
    accel_range = mpu.read_accel_range(True)

    while True:
        # Get the current accel and gyro data
        accel_data = mpu.get_accel_data(accel_range,g=False)  # Get accelerometer data in m/s²
        gyro_data = mpu.get_gyro_data(gyro_range)

        # Remove the inherent deviation of the gyro
        gyro_data['x'] -= gyro_bias['x']
        gyro_data['y'] -= gyro_bias['y']
        gyro_data['z'] -= gyro_bias['z']

        # Apply accelerometer bias correction
        accel_data['x'] -= accel_bias['x']
        accel_data['y'] -= accel_bias['y']
        accel_data['z'] -= accel_bias['z']

        # Print or write the data (currently printing to console)
        print(f"Accel Data: {accel_data}, Gyro Data: {gyro_data}")

        # Wait for 1 second
        time.sleep(1)


def calculate_angles(mpu, biases):
    # Initialize variables for angles
    pitch = 0.0
    roll = 0.0
    DT = 0.02
    AA = 0.98
    gyroXangle = 0.0
    gyroYangle = 0.0
    gyroZangle = 0.0
    CFangleX = 0.0
    CFangleY = 0.0

    accel_bias = biases['accel_bias']
    gyro_bias = biases['gyro_bias']
    cnt = 0

    gyro_range = mpu.read_gyro_range(True)
    accel_range = mpu.read_accel_range(True)
    # Main loop to continuously update angles
    while True:
        cnt += 1
        t1 = time.time()
        # Get accelerometer and gyroscope data
        accel_data = mpu.get_accel_data(accel_range,g=False)  # Get accelerometer data in m/s²
        gyro_data = mpu.get_gyro_data(gyro_range)

        # Remove the inherent deviation of the gyro
        gyro_data['x'] -= gyro_bias['x']
        gyro_data['y'] -= gyro_bias['y']
        gyro_data['z'] -= gyro_bias['z']

        # Apply accelerometer bias correction
        accel_data['x'] -= accel_bias['x']
        accel_data['y'] -= accel_bias['y']
        accel_data['z'] -= accel_bias['z']

        # Calculate the angles from the gyro
        gyroXangle += gyro_data['x'] * DT
        gyroYangle += gyro_data['y'] * DT
        gyroZangle += gyro_data['z'] * DT

        # Convert Accelerometer values to degrees
        AccXangle = math.degrees(math.atan2(accel_data['x'], math.sqrt(accel_data['y'] ** 2 + accel_data['z'] ** 2)))
        AccYangle = math.degrees(math.atan2(accel_data['y'], accel_data['z']))

        # Apply the complementary filter
        CFangleX = AA * (CFangleX + gyro_data['x'] * DT) + AccXangle - AA * AccXangle
        CFangleY = AA * (CFangleY + gyro_data['y'] * DT) + AccYangle - AA * AccYangle

        if cnt == 10:
            # Print or use the angles
            print(f"Pitch (CFangleX): {CFangleX:.2f} degrees, Roll (CFangleY): {CFangleY:.2f} degrees")
            cnt = 0

        t2 = time.time()
        time.sleep(max(0, DT - t2 + t1))


def marko_ideja(mpu, biases):
    # Initialize variables for angles
    pitch = 0.0
    roll = 0.0
    DT = 0.02
    AA = 0.98
    gyroXangle = 0.0
    gyroYangle = 0.0
    gyroZangle = 0.0
    CFangleX = 0.0
    CFangleY = 0.0

    accel_bias = biases['accel_bias']
    gyro_bias = biases['gyro_bias']
    cnt = 0
    # Main loop to continuously update angles
    while True:
        cnt += 1
        t1 = time.time()
        # Get accelerometer and gyroscope data
        accel_data = mpu.get_accel_data(g=False)  # Get accelerometer data in m/s²
        gyro_data = mpu.get_gyro_data()

        # Remove the inherent deviation of the gyro
        gyro_data['x'] -= gyro_bias['x']
        gyro_data['y'] -= gyro_bias['y']
        gyro_data['z'] -= gyro_bias['z']

        # Apply accelerometer bias correction
        accel_data['x'] -= accel_bias['x']
        accel_data['y'] -= accel_bias['y']
        accel_data['z'] -= accel_bias['z']

        f = math.sqrt(accel_data['y'] ** 2 + accel_data['z'] ** 2 + accel_data['y'] ** 2)
        alfa = math.degrees(math.acos(max(min(f / mpu.GRAVITIY_MS2, 1), -1)))

        if cnt == 10:
            # Print or use the angles
            print(f"Angle:  {alfa:.2f} degrees")
            cnt = 0

        t2 = time.time()
        time.sleep(max(0, DT - t2 + t1))


# Example usage:
mpu = mpu6050(0x68)
mpu.reset_mpu6050()
init(mpu)
time.sleep(1)
bias = calibrate_mpu6050(mpu)
print(bias)
calculate_angles(mpu, bias)