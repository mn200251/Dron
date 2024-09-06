"""
This program handles the communication over I2C
between a Raspberry Pi and a MPU-6050 Gyroscope / Accelerometer combo.

Released under the MIT License
Copyright (c) 2015, 2016, 2017, 2021 Martijn (martijn@mrtijn.nl) and contributers

https://github.com/m-rtijn/mpu6050
"""
import time
import smbus

class mpu6050:

    # Global Variables
    GRAVITIY_MS2 = 9.80665
    address = None
    bus = None

    # Scale Modifiers
    ACCEL_SCALE_MODIFIER_2G = 16384.0
    ACCEL_SCALE_MODIFIER_4G = 8192.0
    ACCEL_SCALE_MODIFIER_8G = 4096.0
    ACCEL_SCALE_MODIFIER_16G = 2048.0

    GYRO_SCALE_MODIFIER_250DEG = 131.0
    GYRO_SCALE_MODIFIER_500DEG = 65.5
    GYRO_SCALE_MODIFIER_1000DEG = 32.8
    GYRO_SCALE_MODIFIER_2000DEG = 16.4

    # Pre-defined ranges
    ACCEL_RANGE_2G = 0x00
    ACCEL_RANGE_4G = 0x08
    ACCEL_RANGE_8G = 0x10
    ACCEL_RANGE_16G = 0x18

    GYRO_RANGE_250DEG = 0x00
    GYRO_RANGE_500DEG = 0x08
    GYRO_RANGE_1000DEG = 0x10
    GYRO_RANGE_2000DEG = 0x18

    FILTER_BW_256=0x00
    FILTER_BW_188=0x01
    FILTER_BW_98=0x02
    FILTER_BW_42=0x03
    FILTER_BW_20=0x04
    FILTER_BW_10=0x05
    FILTER_BW_5=0x06

    # MPU-6050 Registers
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C
    WHO_AM_I = 0x75

    ACCEL_XOUT0 = 0x3B
    ACCEL_YOUT0 = 0x3D
    ACCEL_ZOUT0 = 0x3F

    TEMP_OUT0 = 0x41

    GYRO_XOUT0 = 0x43
    GYRO_YOUT0 = 0x45
    GYRO_ZOUT0 = 0x47

    ACCEL_CONFIG = 0x1C
    GYRO_CONFIG = 0x1B
    MPU_CONFIG = 0x1A

    def __init__(self, address, bus=1):
        self.address = address
        self.bus = smbus.SMBus(bus)
        # Wake up the MPU-6050 since it starts in sleep mode
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x00)

    # I2C communication methods

    def read_i2c_word(self, register):
        """Read two i2c registers and combine them.

        register -- the first register to read from.
        Returns the combined read results.
        """
        # Read the data from the registers
        high = self.bus.read_byte_data(self.address, register)
        low = self.bus.read_byte_data(self.address, register + 1)

        value = (high << 8) + low

        if (value >= 0x8000):
            return -((65535 - value) + 1)
        else:
            return value

    # MPU-6050 Methods

    def get_temp(self):
        """Reads the temperature from the onboard temperature sensor of the MPU-6050.

        Returns the temperature in degrees Celcius.
        """
        raw_temp = self.read_i2c_word(self.TEMP_OUT0)

        # Get the actual temperature using the formule given in the
        # MPU-6050 Register Map and Descriptions revision 4.2, page 30
        actual_temp = (raw_temp / 340.0) + 36.53

        return actual_temp

    def set_accel_range(self, accel_range):
        """Sets the range of the accelerometer to range.

        accel_range -- the range to set the accelerometer to. Using a
        pre-defined range is advised.
        """
        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, 0x00)

        # Write the new range to the ACCEL_CONFIG register
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, accel_range)

    def read_accel_range(self, raw = False)-> int:
        """Reads the range the accelerometer is set to.

        If raw is True, it will return the raw value from the ACCEL_CONFIG
        register
        If raw is False, it will return an integer: -1, 2, 4, 8 or 16. When it
        returns -1 something went wrong.
        """
        raw_data = self.bus.read_byte_data(self.address, self.ACCEL_CONFIG)

        if raw is True:
            return raw_data
        elif raw is False:
            if raw_data == self.ACCEL_RANGE_2G:
                return 2
            elif raw_data == self.ACCEL_RANGE_4G:
                return 4
            elif raw_data == self.ACCEL_RANGE_8G:
                return 8
            elif raw_data == self.ACCEL_RANGE_16G:
                return 16
            else:
                return -1

    def get_accel_data(self,accel_range:int, g = False):
        """Gets and returns the X, Y and Z values from the accelerometer.

        If g is True, it will return the data in g
        If g is False, it will return the data in m/s^2
        Returns a dictionary with the measurement results.
        """
        x = self.read_i2c_word(self.ACCEL_XOUT0)
        y = self.read_i2c_word(self.ACCEL_YOUT0)
        z = self.read_i2c_word(self.ACCEL_ZOUT0)

        accel_scale_modifier = None

        if accel_range == self.ACCEL_RANGE_2G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
        elif accel_range == self.ACCEL_RANGE_4G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_4G
        elif accel_range == self.ACCEL_RANGE_8G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_8G
        elif accel_range == self.ACCEL_RANGE_16G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_16G
        else:
            print("Unkown range - accel_scale_modifier set to self.ACCEL_SCALE_MODIFIER_2G")
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G

        x = x / accel_scale_modifier
        y = y / accel_scale_modifier
        z = z / accel_scale_modifier

        if g is True:
            return {'x': x, 'y': y, 'z': z}
        elif g is False:
            x = x * self.GRAVITIY_MS2
            y = y * self.GRAVITIY_MS2
            z = z * self.GRAVITIY_MS2
            return {'x': x, 'y': y, 'z': z}

    def set_gyro_range(self, gyro_range):
        """Sets the range of the gyroscope to range.

        gyro_range -- the range to set the gyroscope to. Using a pre-defined
        range is advised.
        """
        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_byte_data(self.address, self.GYRO_CONFIG, 0x00)

        # Write the new range to the ACCEL_CONFIG register
        self.bus.write_byte_data(self.address, self.GYRO_CONFIG, gyro_range)

    def set_filter_range(self, filter_range=FILTER_BW_256):
        """Sets the low-pass bandpass filter frequency"""
        # Keep the current EXT_SYNC_SET configuration in bits 3, 4, 5 in the MPU_CONFIG register
        EXT_SYNC_SET = self.bus.read_byte_data(self.address, self.MPU_CONFIG) & 0b00111000
        return self.bus.write_byte_data(self.address, self.MPU_CONFIG,  EXT_SYNC_SET | filter_range)


    def read_gyro_range(self, raw = False) -> int:
        """Reads the range the gyroscope is set to.

        If raw is True, it will return the raw value from the GYRO_CONFIG
        register.
        If raw is False, it will return 250, 500, 1000, 2000 or -1. If the
        returned value is equal to -1 something went wrong.
        """
        raw_data = self.bus.read_byte_data(self.address, self.GYRO_CONFIG)

        if raw is True:
            return raw_data
        elif raw is False:
            if raw_data == self.GYRO_RANGE_250DEG:
                return 250
            elif raw_data == self.GYRO_RANGE_500DEG:
                return 500
            elif raw_data == self.GYRO_RANGE_1000DEG:
                return 1000
            elif raw_data == self.GYRO_RANGE_2000DEG:
                return 2000
            else:
                return -1

    def get_gyro_data(self,gyro_range:int):
        """Gets and returns the X, Y and Z values from the gyroscope.

        Returns the read values in a dictionary.
        """
        x = self.read_i2c_word(self.GYRO_XOUT0)
        y = self.read_i2c_word(self.GYRO_YOUT0)
        z = self.read_i2c_word(self.GYRO_ZOUT0)

        gyro_scale_modifier = None

        if gyro_range == self.GYRO_RANGE_250DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
        elif gyro_range == self.GYRO_RANGE_500DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
        elif gyro_range == self.GYRO_RANGE_1000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
        elif gyro_range == self.GYRO_RANGE_2000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
        else:
            print("Unkown range - gyro_scale_modifier set to self.GYRO_SCALE_MODIFIER_250DEG")
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG

        x = x / gyro_scale_modifier
        y = y / gyro_scale_modifier
        z = z / gyro_scale_modifier

        return {'x': x, 'y': y, 'z': z}

    def get_all_data(self):
        """Reads and returns all the available data."""
        gyro_range = self.read_gyro_range(True)
        accel_range = self.read_accel_range(True)
        temp = self.get_temp()
        accel = self.get_accel_data(accel_range)
        gyro = self.get_gyro_data(gyro_range)

        return [accel, gyro, temp]

    # Aleksandra dodaci
    def check_connection(self):
        who_am_i = self.bus.read_byte_data(self.address, self.WHO_AM_I)
        return who_am_i == 0x68

    def disable_accelerometer(self):
        current_value = self.bus.read_byte_data(self.address, self.PWR_MGMT_2)
        new_value = current_value | 0x38  # Set STBY_XA,STBY_YA,STBY_YA
        # Disable X, Y, and Z axes of the accelerometer
        self.bus.write_byte_data(self.address, self.PWR_MGMT_2, new_value)

    def enable_accelerometer(self):
        current_value = self.bus.read_byte_data(self.address, self.PWR_MGMT_2)
        new_value = current_value & ~0x38  # Clear STBY_XA,STBY_YA,STBY_YA
        # Enable X, Y, and Z axes of the accelerometer
        self.bus.write_byte_data(self.address, self.PWR_MGMT_2, new_value)

    def reset_mpu6050(self):
        # Write a reset command to the PWR_MGMT_1 register
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x80)
        # Wait for the reset to complete (recommended 100 milliseconds)
        time.sleep(0.15)
        # Wake up the MPU-6050 by writing 0 to the PWR_MGMT_1 register
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x00)

    def disable_temp_sensor(self):
        """Disables the temperature sensor by setting the TEMP_DIS bit in the PWR_MGMT_1 register."""
        current_value = self.bus.read_byte_data(self.address, self.PWR_MGMT_1)
        new_value = current_value | 0x08  # Set the TEMP_DIS bit (bit 3) to 1
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, new_value)

    def enable_temp_sensor(self):
        """Enables the temperature sensor by clearing the TEMP_DIS bit in the PWR_MGMT_1 register."""
        current_value = self.bus.read_byte_data(self.address, self.PWR_MGMT_1)
        new_value = current_value & ~0x08  # Clear the TEMP_DIS bit (bit 3) to 0
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, new_value)

    import time

    def calibrate_accelerometer(self, duration=5):
        """
        Calibrate the accelerometer biases.

        :param self: The mpu6050 object.
        :param duration: The duration in seconds to average the readings over.
        :return: A dictionary with the calculated biases for the accelerometer.
        """
        num_samples = duration * 100  # Taking 100 samples per second
        accel_bias = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        accel_range = self.read_accel_range(True)

        for _ in range(num_samples):
            accel_data = self.get_accel_data(accel_range)
            accel_bias['x'] += accel_data['x']
            accel_bias['y'] += accel_data['y']
            accel_bias['z'] += accel_data['z']
            time.sleep(0.01)  # Sleep for 10 milliseconds between samples

        accel_bias['x'] /= num_samples
        accel_bias['y'] /= num_samples
        accel_bias['z'] /= num_samples

        # Adjust the accelerometer bias to account for gravity on the Z-axis
        accel_bias['z'] -= self.GRAVITIY_MS2

        return accel_bias

    def calibrate_gyroscope(self, duration=5):
        """
        Calibrate the gyroscope biases.

        :param self: The mpu6050 object.
        :param duration: The duration in seconds to average the readings over.
        :return: A dictionary with the calculated biases for the gyroscope.
        """
        num_samples = duration * 100  # Taking 100 samples per second
        gyro_bias = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        gyro_range = self.read_gyro_range(True)

        for _ in range(num_samples):
            gyro_data = self.get_gyro_data(gyro_range)
            gyro_bias['x'] += gyro_data['x']
            gyro_bias['y'] += gyro_data['y']
            gyro_bias['z'] += gyro_data['z']
            time.sleep(0.01)  # Sleep for 10 milliseconds between samples

        gyro_bias['x'] /= num_samples
        gyro_bias['y'] /= num_samples
        gyro_bias['z'] /= num_samples

        return gyro_bias



    
if __name__ == "__main__":
    mpu = mpu6050(0x68)
    mpu.reset_mpu6050()
    gyro_range = mpu.read_gyro_range(True)
    accel_range = mpu.read_accel_range(True)
    print(mpu.get_temp())
    accel_data = mpu.get_accel_data(gyro_range)
    print(accel_data['x'])
    print(accel_data['y'])
    print(accel_data['z'])
    gyro_data = mpu.get_gyro_data(accel_range)
    print(gyro_data['x'])
    print(gyro_data['y'])
    print(gyro_data['z'])
    mpu.bus.write_byte_data(mpu.address, mpu.PWR_MGMT_1, 0x40)