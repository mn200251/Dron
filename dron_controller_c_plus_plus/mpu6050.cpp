#include "mpu6050.h"



MPU6050::MPU6050(uint8_t address) : address(address), file(-1) {
    char filename[20];
    snprintf(filename, sizeof(filename), "/dev/i2c-1");

    file = open(filename, O_RDWR);
    if (file < 0) {
        throw std::runtime_error("Failed to open I2C bus");
    }

    if (ioctl(file, I2C_SLAVE, address) < 0) {
        throw std::runtime_error("Failed to acquire bus access and/or talk to slave");
    }

    // Wake up the MPU-6050 since it starts in sleep mode
    write_byte_data(PWR_MGMT_1, 0x00);
}

MPU6050::~MPU6050() {
    if (file >= 0) {
        close(file);
    }
}

double MPU6050::get_temp() {
    int16_t raw_temp = read_i2c_word(TEMP_OUT0);
    // Get the actual temperature using the formule given in the
    // MPU-6050 Register Map and Descriptions revision 4.2, page 30
    return (raw_temp / 340.0) + 36.53;
}

void MPU6050::set_accel_range(uint8_t accel_range) {
    write_byte_data(ACCEL_CONFIG, 0x00);
    write_byte_data(ACCEL_CONFIG, accel_range);
}

int8_t MPU6050::read_accel_range(bool raw) {
    uint8_t raw_data = read_byte_data(ACCEL_CONFIG);

    if (raw) {
        return raw_data;
    } else {
        switch (raw_data) {
            case ACCEL_RANGE_2G: return 2;
            case ACCEL_RANGE_4G: return 4;
            case ACCEL_RANGE_8G: return 8;
            case ACCEL_RANGE_16G: return 16;
            default: return -1;
        }
    }
}

void MPU6050::get_accel_data(double* accel_data, uint8_t accel_range, bool g) {
    int16_t x = read_i2c_word(ACCEL_XOUT0);
    int16_t y = read_i2c_word(ACCEL_YOUT0);
    int16_t z = read_i2c_word(ACCEL_ZOUT0);

    double accel_scale_modifier;

    switch (accel_range) {
        case ACCEL_RANGE_2G: accel_scale_modifier = ACCEL_SCALE_MODIFIER_2G; break;
        case ACCEL_RANGE_4G: accel_scale_modifier = ACCEL_SCALE_MODIFIER_4G; break;
        case ACCEL_RANGE_8G: accel_scale_modifier = ACCEL_SCALE_MODIFIER_8G; break;
        case ACCEL_RANGE_16G: accel_scale_modifier = ACCEL_SCALE_MODIFIER_16G; break;
        default: accel_scale_modifier = ACCEL_SCALE_MODIFIER_2G; break;
    }

    accel_data[0] = x / accel_scale_modifier;
    accel_data[1] = y / accel_scale_modifier;
    accel_data[2] = z / accel_scale_modifier;

    if (!g) {
        accel_data[0] *= GRAVITIY_MS2;
        accel_data[1] *= GRAVITIY_MS2;
        accel_data[2] *= GRAVITIY_MS2;
    }
}

void MPU6050::set_gyro_range(uint8_t gyro_range) {
    write_byte_data(GYRO_CONFIG, 0x00);
    write_byte_data(GYRO_CONFIG, gyro_range);
}

void MPU6050::set_filter_range(uint8_t filter_range) {
    uint8_t EXT_SYNC_SET = read_byte_data(MPU_CONFIG) & 0b00111000;
    write_byte_data(MPU_CONFIG, EXT_SYNC_SET | filter_range);
}

int16_t MPU6050::read_gyro_range(bool raw) {
    uint8_t raw_data = read_byte_data(GYRO_CONFIG);

    if (raw) {
        return raw_data;
    } else {
        switch (raw_data) {
            case GYRO_RANGE_250DEG: return 250;
            case GYRO_RANGE_500DEG: return 500;
            case GYRO_RANGE_1000DEG: return 1000;
            case GYRO_RANGE_2000DEG: return 2000;
            default: return -1;
        }
    }
}

void MPU6050::get_gyro_data(double* gyro_data,uint8_t gyro_range) {
    int16_t x = read_i2c_word(GYRO_XOUT0);
    int16_t y = read_i2c_word(GYRO_YOUT0);
    int16_t z = read_i2c_word(GYRO_ZOUT0);
    double gyro_scale_modifier;


    switch (gyro_range) {
        case GYRO_RANGE_250DEG: gyro_scale_modifier = GYRO_SCALE_MODIFIER_250DEG; break;
        case GYRO_RANGE_500DEG: gyro_scale_modifier = GYRO_SCALE_MODIFIER_500DEG; break;
        case GYRO_RANGE_1000DEG: gyro_scale_modifier = GYRO_SCALE_MODIFIER_1000DEG; break;
        case GYRO_RANGE_2000DEG: gyro_scale_modifier = GYRO_SCALE_MODIFIER_2000DEG; break;
        default: gyro_scale_modifier = GYRO_SCALE_MODIFIER_250DEG; break;
    }

    gyro_data[0] = x / gyro_scale_modifier;
    gyro_data[1] = y / gyro_scale_modifier;
    gyro_data[2] = z / gyro_scale_modifier;
}

void MPU6050::get_all_data(double* accel_data, double* gyro_data, double* temp) {
    *temp = get_temp();
    get_accel_data(accel_data,read_accel_range());
    get_gyro_data(gyro_data,read_gyro_range());
}

void MPU6050::reset_mpu6050() {
    write_byte_data(PWR_MGMT_1, 0x80);
    usleep(150000); // Wait for restart to finish
    write_byte_data(PWR_MGMT_1, 0x00); // Wake up the sensor
}

void MPU6050::disable_temp_sensor() {
    uint8_t current_value = read_byte_data(PWR_MGMT_1);
    //Set the TEMP_DIS bit (bit 3) to 1
    write_byte_data(PWR_MGMT_1, current_value | 0x08);
}

void MPU6050::enable_temp_sensor() {
    uint8_t current_value = read_byte_data(PWR_MGMT_1);
    //Set the TEMP_DIS bit (bit 3) to 0
    write_byte_data(PWR_MGMT_1, current_value & ~0x08);
}

void MPU6050::sleep() {
    // Set the sleep bit in the PWR_MGMT_1 register
    uint8_t current_reg_value = read_byte_data(0x6B);  // PWR_MGMT_1 register address is 0x6B
    uint8_t new_reg_value = current_reg_value | 0x40;  // Set bit 6 (value 0x40) to put MPU6050 to sleep
    write_byte_data(0x6B, new_reg_value);
}

uint8_t MPU6050::read_byte_data(uint8_t reg) {
    uint8_t buf[1] = { reg };
    if (write(file, buf, 1) != 1) {
        throw std::runtime_error("Failed to write to I2C bus");
    }

    if (read(file, buf, 1) != 1) {
        throw std::runtime_error("Failed to read from I2C bus");
    }

    return buf[0];
}

void MPU6050::write_byte_data(uint8_t reg, uint8_t value) {
    uint8_t buf[2] = { reg, value };
    if (write(file, buf, 2) != 2) {
        throw std::runtime_error("Failed to write to I2C bus");
    }
}

int16_t MPU6050::read_i2c_word(uint8_t reg) {
    uint8_t high = read_byte_data(reg);
    uint8_t low = read_byte_data(reg + 1);
    int16_t value = (high << 8) | low;

    if (value >= 0x8000) {
        return -((65535 - value) + 1);
    } else {
        return value;
    }
}


