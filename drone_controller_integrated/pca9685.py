import math
from enum import Enum

import smbus
import time

# Registers/etc.
MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02  # not used
SUBADR2 = 0x03  # not used
SUBADR3 = 0x04  # not used
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

# Default I2C address for PCA9685
PCA9685_I2C_ADDRESS = 0x40
PCA9685_I2C_DEF_ALLCALL_PROXYADR = 0xE0  # Default AllCall i2c proxy address
PCA9685_I2C_DEF_SUB1_PROXYADR = 0xE2  # Default Sub1 i2c proxy address
PCA9685_I2C_DEF_SUB2_PROXYADR = 0xE4  # Default Sub2 i2c proxy address
PCA9685_I2C_DEF_SUB3_PROXYADR = 0xE8  # Default Sub3 i2c proxy address
PCA9685_I2C_RESET_ADDRESS = 0x00

# Mode1 register values
MODE1_RESTART = 0x80  # Restart bit for Mode1 register
MODE1_EXTCLK = 0x40  # External clock bit for Mode1 register
MODE1_AUTOINC = 0x20  # Auto-increment bit for Mode1 register
MODE1_SLEEP = 0x10  # Sleep mode bit for Mode1 register
MODE1_SUBADR1 = 0x08  # Sub-address 1 bit for Mode1 register
MODE1_SUBADR2 = 0x04  # Sub-address 2 bit for Mode1 register
MODE1_SUBADR3 = 0x02  # Sub-address 3 bit for Mode1 register
MODE1_ALLCALL = 0x01  # AllCall bit for Mode1 register

# Mode2 register values
MODE2_OUTDRV_TOTEMPOLE = 0x04  # Totem pole output driver
MODE2_INVRT = 0x10  # Invert output bit for Mode2 register
MODE2_OUTNE_TPHIGH = 0x01  # OUTNE totem pole high
MODE2_OUTNE_HIGHZ = 0x02  # OUTNE high impedance
MODE2_OCH_ONACK = 0x08  # Output change on acknowledge

# Special commands and values
SW_RESET = 0x06  # Software reset command for all devices (that support it)  on i2c
PWM_FULL = 0x1000  # Special value for full-on/full-off modes for LEDs
PWM_MASK = 0x0FFF  # Mask for 12-bit/4096 possible PWM positions

# Channel and LED-specific constants
CHANNEL_COUNT = 16  # Number of channels available
MIN_CHANNEL = 0  # Minimum channel index
MAX_CHANNEL = CHANNEL_COUNT - 1  # Maximum channel index (15)
ALL_LED_CHANNEL = -1  # Special value for ALLLED registers (used for all channels)



# Enum for Output Driver Control Mode
class PCA9685_OutputDriverMode(Enum):
    OpenDrain = 0  # Open-drain (direct connection) style output, useful for LEDs, low-power servos
    TotemPole = 1  # Push-pull (totem-pole) style output, useful for external drivers (default)
    Count = 2  # Internal use only
    Undefined = -1  # Internal use only
# There exist other setting but as they are not relevant they won't be listed


# 4 prednji desni
# 5 zadnji desni
# 10 prednji levi
# 11 zadnji levi
class PCA9685:
    def __init__(self, i2c_address=PCA9685_I2C_ADDRESS, bus=1):
        # I2C 7-bit address is B 1 A5 A4 A3 A2 A1 A0
        self.address = i2c_address
        self.bus = smbus.SMBus(bus)
        # Initialize the driver mode to undefined
        self._driver_mode = PCA9685_OutputDriverMode.Undefined

    def reset(self):
        """Reset the PCA9685 device."""
        self.bus.write_byte(PCA9685_I2C_RESET_ADDRESS, SW_RESET)

    def write_register(self, register, value):
        """Write a byte value to the specified register."""
        self.bus.write_byte_data(self.address, register, value)

    # Getter for _driver_mode
    def get_driver_mode(self):
        """Get the current driver mode."""
        return self._driver_mode

    # Setter for _driver_mode
    def set_driver_mode(self, mode):
        """Set the driver mode in MODE2 register"""
        if mode not in PCA9685_OutputDriverMode:
            raise ValueError("Invalid driver mode")

        current_mode2 = self.bus.read_byte_data(self.address, MODE2)

        if mode == PCA9685_OutputDriverMode.TotemPole:
            new_mode2 = current_mode2 | MODE2_OUTDRV_TOTEMPOLE
        else:
            new_mode2 = current_mode2 & ~MODE2_OUTDRV_TOTEMPOLE

        self.write_register(MODE2, new_mode2)
        self._driver_mode = mode

    def enable_auto_increment(self):
        """
        Enable the AUTO-INCREMENT feature in the MODE1 register of the PCA9685.
        """
        # Read the current value of the MODE1 register
        mode1_reg = self.read_register(MODE1)

        # Set the AUTO-INCREMENT bit (bit 5)
        mode1_reg |= MODE1_AUTOINC

        # Write the updated MODE1 register value back to the PCA9685
        self.write_register(MODE1, mode1_reg)

        # Optional: Wait for the PCA9685 to process the change
        time.sleep(0.001)  # 1 ms delay

    def set_pwm_frequency(self, pwm_frequency: float):
        """
                Set the PWM frequency of the PCA9685.

                This function calculates and sets the pre-scaler value required to achieve
                the desired PWM frequency. The PCA9685's oscillator can be configured to
                different frequencies by adjusting the pre-scaler value. It also handles the
                transition between sleep and active states of the oscillator.

                Args:
                    pwm_frequency (float): The desired PWM frequency in Hertz (Hz). The
                                           frequency must be between 24 Hz and 1526 Hz.

                Notes:
                    The function checks if the desired frequency is within the valid range.
                    If so, it calculates the appropriate pre-scaler value, writes it to the
                    PRESCALE register, and configures the MODE1 register to update the oscillator.

        """

        # Check if pwm (in HZ) goes outside the supported range
        if pwm_frequency < 24 or pwm_frequency > 1526:
            return

        # Calculate the pre-scaler value based on the desired PWM frequency
        pre_scaler_val = int((25000000.0 / (4096.0 * pwm_frequency)) - 1)
        if pre_scaler_val > 255:
            pre_scaler_val = 255
        if pre_scaler_val < 3:
            pre_scaler_val = 3

        # Debug output (if needed)
        print(f"PCA9685::setPWMFrequency pwmFrequency: {pwm_frequency}, preScalerVal: 0x{pre_scaler_val:X}")

        # Read the current value of the MODE1 register
        mode1_reg = self.read_register(MODE1)

        if not (mode1_reg & MODE1_SLEEP):
            mode1_reg = (mode1_reg & ~MODE1_RESTART) | MODE1_SLEEP

            # Set the SLEEP bit in MODE1 to be able to configure the pre-scaler
            self.write_register(MODE1, mode1_reg)

        # Write the pre-scaler value to the PRESCALE register
        self.write_register(PRESCALE, pre_scaler_val)

        mode1_reg= (mode1_reg & ~MODE1_SLEEP)
        # Write back to MODE1 register to clear the SLEEP bit and restart the oscillator
        self.write_register(MODE1,mode1_reg)

        # Wait again to ensure the oscillator has stabilized
        time.sleep(0.001)

        self.write_register(MODE1, (mode1_reg | MODE1_RESTART))


    def set_ESC_pwm_freq(self):
        """
                Set the PWM frequency for ESC (Electronic Speed Controller) to 50 Hz.

                This function is a specific implementation for setting the frequency suitable
                for controlling ESCs. The standard ESC frequency is 50 Hz.
        """
        self.set_pwm_frequency(50)

    def write_channel_pwm(self, channel: int, phase_begin: int, phase_end: int):
        """
                Write the PWM values to a specific channel.

                This function writes the PWM phase values to the registers of the PCA9685. It
                handles setting both the on and off times for the specified channel or all channels.

                Args:
                    channel (int): The channel number (0 to 15) or -1 for all channels.
                    phase_begin (int): The start time of the PWM signal (0 to 4095).
                    phase_end (int): The end time of the PWM signal (0 to 4095).

                Notes:
                    The values are masked to ensure they are within the 12-bit range (0 to 4095).
                    The appropriate register address is selected based on the channel.
        """

        # Ensure the values are within valid ranges
        phase_begin = phase_begin & 0x1FFF  # Mask to 13-bit
        phase_end = phase_end & 0x1FFF  # Mask to 13-bit

        # Calculate the register address based on the channel
        if channel != -1:  # Assuming -1 is used for ALLLED_CHANNEL
            reg_address = LED0_ON_L + (channel * 4)
        else:
            reg_address = ALL_LED_ON_L  # Use the ALLLED address for all channels

        # Convert values to low and high bytes
        phase_begin_low = phase_begin & 0xFF
        phase_begin_high = (phase_begin >> 8) & 0xFF
        phase_end_low = phase_end & 0xFF
        phase_end_high = (phase_end >> 8) & 0xFF

        # Write data to I2C bus
        self.bus.write_i2c_block_data(
            self.address,
            reg_address,
            [phase_begin_low, phase_begin_high, phase_end_low, phase_end_high]
        )

    def set_channel_on(self, channel: int):
        """
                Turn on the specified channel.

                This function sets the PWM signal to turn on the specified channel by writing
                the maximum value to the ON time and zero to the OFF time.

                Args:
                    channel (int): The channel number (0 to 15).

                Notes:
                    The channel number must be within the valid range (0 to 15).
                    It writes the full ON value (PWM_FULL) to the channel and sets OFF time to zero.
        """
        if channel < ALL_LED_CHANNEL or channel >= CHANNEL_COUNT:
            return

        # Start writing to the specified channel
        self.write_channel_pwm(channel, PWM_FULL, 0)  # FULL on, 0 off

    def set_channel_off(self, channel: int):
        """
                Turn off the specified channel.

                This function sets the PWM signal to turn off the specified channel by writing
                zero to the ON time and the maximum value to the OFF time.

                Args:
                    channel (int): The channel number (0 to 15).

                Notes:
                    The channel number must be within the valid range (0 to 15).
                    It writes zero to the ON time and the full OFF value (PWM_FULL) to the channel.
        """
        if channel < ALL_LED_CHANNEL or channel >= CHANNEL_COUNT:
            return

        # Start writing to the specified channel
        self.write_channel_pwm(channel, 0, PWM_FULL)  # 0 on, FULL off

    def set_channel_pwm(self, channel: int, pwm_amount: float):
        """
                Set the PWM signal for the specified channel based on the desired PWM amount.

                This function calculates the phase begin and end values based on the PWM amount
                (percentage of on time) and writes these values to the channel.

                Args:
                    channel (int): The channel number (0 to 15).
                    pwm_amount (int): The PWM amount as a percentage (0 to 100).

                Notes:
                    The channel number must be within the valid range (0 to 15).
                    The `pwm_amount` is used to determine the on and off phases of the PWM signal.
        """
        if channel < ALL_LED_CHANNEL or channel >= CHANNEL_COUNT:
            return

        # Get the phase begin and end values
        phase_begin, phase_end = self.get_phase_cycle(pwm_amount)

        # Start writing to the specified channel
        self.write_channel_pwm(channel, phase_begin, phase_end)

    def get_phase_cycle(self, pwm_amount: float) -> tuple:
        """Calculate the on and off phases for a given PWM amount.

        Args:
            channel (int): The channel number (0 to 15).
            pwm_amount (float): PWM amount as a percentage (0 to 100).

        Returns:
            tuple: (phase_begin, phase_end) where phase_begin is the start time
                   of the PWM signal and phase_end is the end time.
        """
        # Ensure pwm_amount is between 0 and 100
        pwm_amount = max(0.0, min(pwm_amount, 100.0))

        # Total range for the PWM signal (0 to 4095)
        total_range = 4095

        # Calculate the phase begin and end values
        phase_begin = 0
        phase_end = math.ceil((pwm_amount / 100.0) * total_range)

        # Ensure values are within the valid range
        phase_end = min(phase_end, total_range)
        phase_begin = max(phase_begin, 0)

        return phase_begin, phase_end

    def read_register(self, register: int) -> int:
        """Read a single byte from the specified register."""
        try:
            # Read a single byte from the specified register
            value = self.bus.read_byte_data(self.address, register)
            return value
        except Exception as e:
            if hasattr(self, '_debug') and self._debug:
                print(f"Error reading register {hex(register)}: {e}")
            return None

    PWM_PERIOD_US = 20000  # 20ms period for 50Hz frequency in microseconds
    PWM_MAX_VALUE = 4095.0  # 12-bit resolution maximum value
    PWM_SCALE_FACTOR = PWM_MAX_VALUE / PWM_PERIOD_US  # Scaling factor for converting microseconds to PWM values

    MIN_PULSE_LENGTH = 1000
    MAX_PULSE_LENGTH = 2000
    def set_ESC_PWM(self, channel: int, pulse_width_us: int):
        """Set the PWM for an ESC with a pulse width in microseconds.
            Expects that the frequency is 50Hz.
        Args:
            channel (int): The channel number (0 to 15).
            pulse_width_us (int): Pulse width in microseconds (1000 to 2000).

        Raises:
            ValueError: If pulse_width_us is not in the range [1000, 2000].
        """
        if pulse_width_us < self.MIN_PULSE_LENGTH or pulse_width_us > self.MAX_PULSE_LENGTH:
            print("Pulse width must be between 1000 and 2000 microseconds.")
            return

        # Calculate the phase values using the scaling factor
        pulse_width_ticks = math.ceil(pulse_width_us * self.PWM_SCALE_FACTOR)
        #print(pulse_width_ticks)
        # Set the PWM for the specified channel
        self.write_channel_pwm(channel,0, pulse_width_ticks)

    def arm_esc(self, channel):
        time.sleep(0.2)
        self.set_ESC_PWM(channel,1100)
        time.sleep(2)
        self.set_ESC_PWM(channel, self.MIN_PULSE_LENGTH)

    def calibrate_esc(self,channel):
        print("Hello! Welcome to the ESC throttle range calibration script")
        print("The Pi should be running on SEPARATE power from the ESC's")
        print("This is because the Pi needs to be able to set the throttle to 100% BEFORE the ESC's gain power")
        print(
            "To accomplish this, the Pi will need to be on a different power source (USB) while the ESC's are powered by the LiPo.")
        print("Please ensure that right now the ESC's are NOT powered on")
        print("Press enter to confirm this and when you are ready")
        input("")

        # Set up PWM's
        self.set_ESC_PWM(channel, self.MAX_PULSE_LENGTH)
        print("Set to max throttle (" + str(self.MAX_PULSE_LENGTH) + " ns)")

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
        self.set_ESC_PWM(channel, self.MIN_PULSE_LENGTH)

        # confirmation beeps
        print("You should now hear confirmation beeps")
        print("After you hear those, your ESC's are calibrated. You may power down :)")

        # program complete
        print("")
        print("Calibration complete! ")

    def init(self):
        """
            Just call this for the rest of setup :
                sets the frequency to 50Hz and starts oscillator
                sets the driver to totem ( hardware thing )
            For PWMcontrol call set_ESC_PWM
            For kill you can use : set_channel_off(-1)
            Thats the relevant part of the interface for you
        """
        self.set_driver_mode(PCA9685_OutputDriverMode.TotemPole)
        self.enable_auto_increment()
        self.set_ESC_pwm_freq()

    def check_device(self):
        """Check if the device is a PCA9685 by reading the MODE1 register."""
        try:
            mode1 = self.bus.read_byte_data(self.address, MODE1)
            # After reset, MODE1 should be 0x11 (assuming auto-increment enabled, and all other defaults)
            if mode1 == 0x11:
                return True
            else:
                return False
        except IOError:
            # If there's an I2C error, it means the device is not responding
            return False

    def read_channel_pwm(self, channel):
        """Read the PWM ON and OFF values for a specific channel."""
        if channel < 0 or channel >= 16:
            raise ValueError("Channel must be between 0 and 15")

        if channel != -1:  # Assuming -1 is used for ALLLED_CHANNEL
            reg_base = LED0_ON_L + (channel * 4)
        else:
            reg_base = ALL_LED_ON_L  # Use the ALLLED address for all channels
        on_l = self.read_register(reg_base)
        on_h = self.read_register(reg_base + 1)
        off_l = self.read_register(reg_base + 2)
        off_h = self.read_register(reg_base + 3)

        on = (on_h << 8) | on_l
        off = (off_h << 8) | off_l

        return on, off

def example_on(pca9685,channel=0):
    mode1_value = pca9685.read_register(MODE1)
    # Print the value as binary
    if mode1_value is not None:
        print(f"MODE1 register value (bin): {mode1_value:08b}")
    else:
        print("Error reading MODE1 register.")

    p = pca9685.read_register(PRESCALE)
    # Print the value as binary
    mode2_value = pca9685.read_register(MODE2)
    # Print the value as binary
    if mode2_value is not None:
        print(f"MODE2 register value (bin): {mode2_value:08b}")
    else:
        print("Error reading MODE2 register.")

    if p is not None:
        print(f"PRESCALE register value (bin): {p:08b}")
    else:
        print("Error reading PRESCALE register.")
    print(pca9685.read_channel_pwm(channel))
    # Turn on LED on channel 0
    pca9685.set_channel_on(channel)

    print(pca9685.read_channel_pwm(channel))

    input("Press Enter to turn off the LED and exit...")

    # Turn off LED on channel 0
    pca9685.set_channel_off(channel)

def example_pwm_increasing(pca9685,channel=0):
# Start with a PWM value of 0
        pwm_amount = 0.5

        while pwm_amount <= 100:
            # Set the current PWM amount to the channel
            pca9685.set_channel_pwm(channel, pwm_amount)

            # Print the current PWM value for debugging purposes
            print(f"Channel {channel}: PWM set to {pwm_amount}%")

            # Wait for 1 second before increasing the PWM
            time.sleep(1)

            # Increase the PWM value by 5
            pwm_amount += 5

        pca9685.set_channel_pwm(channel, 0)

def example_ESC_pwm_increasing(pca9685,channel=0):
    pulse_width_us = 1000
    while pulse_width_us <= 2000:
        # Set the current pulse width to the channel (1000 to 2000 μs range)
        pca9685.set_ESC_PWM(channel, pulse_width_us)

        # Print the current pulse width for debugging purposes
        print(f"Channel {channel}: ESC pulse width set to {pulse_width_us} μs")

        # Wait for 1 second before increasing the pulse width
        time.sleep(1)

        if pulse_width_us % 600 == 0:
            print(pca9685.read_channel_pwm(channel))
        # Increase the pulse width by 25 μs
        pulse_width_us += 25
    pca9685.set_channel_pwm(channel, 0)

def motor(pca9685,channel):
    pass

# Example usage:
if __name__ == "__main__":
    try:
        pca9685 = PCA9685(i2c_address=PCA9685_I2C_ADDRESS)

        pca9685.reset()

        pca9685.init()

        channels=[4,5,10,11]

        channel=-1

        pca9685.arm_esc(channel)

        # pca9685.set_ESC_PWM(-1,1100)
        time.sleep(2)
        while(True):
            length = int(input("Enter pulse length in µs(-1 for end):"))
            if(length==-1):
                break
            pca9685.set_ESC_PWM(channel,length)
            input("Press Enter to continue...")
            pca9685.set_ESC_PWM(channel,pca9685.MIN_PULSE_LENGTH)

        print("End")
        pca9685.set_channel_off(channel)


    except Exception as e:
        print(e)
        pca9685.reset()
