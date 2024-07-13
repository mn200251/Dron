#ifndef MPU6050_H
#define MPU6050_H

#include <cstdint>
#include <stdexcept>
#include <unistd.h>
#include <cmath>
#include <iostream>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <chrono>

class MPU6050 {
public:
    static constexpr double GRAVITIY_MS2 = 9.80665;

    // Scale Modifiers
    static constexpr double ACCEL_SCALE_MODIFIER_2G = 16384.0;
    static constexpr double ACCEL_SCALE_MODIFIER_4G = 8192.0;
    static constexpr double ACCEL_SCALE_MODIFIER_8G = 4096.0;
    static constexpr double ACCEL_SCALE_MODIFIER_16G = 2048.0;

    static constexpr double GYRO_SCALE_MODIFIER_250DEG = 131.0;
    static constexpr double GYRO_SCALE_MODIFIER_500DEG = 65.5;
    static constexpr double GYRO_SCALE_MODIFIER_1000DEG = 32.8;
    static constexpr double GYRO_SCALE_MODIFIER_2000DEG = 16.4;

    // Pre-defined ranges
    static constexpr uint8_t ACCEL_RANGE_2G = 0x00;
    static constexpr uint8_t ACCEL_RANGE_4G = 0x08;
    static constexpr uint8_t ACCEL_RANGE_8G = 0x10;
    static constexpr uint8_t ACCEL_RANGE_16G = 0x18;

    static constexpr uint8_t GYRO_RANGE_250DEG = 0x00;
    static constexpr uint8_t GYRO_RANGE_500DEG = 0x08;
    static constexpr uint8_t GYRO_RANGE_1000DEG = 0x10;
    static constexpr uint8_t GYRO_RANGE_2000DEG = 0x18;

    static constexpr uint8_t FILTER_BW_256 = 0x00;
    static constexpr uint8_t FILTER_BW_188 = 0x01;
    static constexpr uint8_t FILTER_BW_98 = 0x02;
    static constexpr uint8_t FILTER_BW_42 = 0x03;
    static constexpr uint8_t FILTER_BW_20 = 0x04;
    static constexpr uint8_t FILTER_BW_10 = 0x05;
    static constexpr uint8_t FILTER_BW_5 = 0x06;

    // MPU-6050 Registers
    static constexpr uint8_t PWR_MGMT_1 = 0x6B;
    static constexpr uint8_t PWR_MGMT_2 = 0x6C;
    static constexpr uint8_t ACCEL_XOUT0 = 0x3B;
    static constexpr uint8_t ACCEL_YOUT0 = 0x3D;
    static constexpr uint8_t ACCEL_ZOUT0 = 0x3F;
    static constexpr uint8_t TEMP_OUT0 = 0x41;
    static constexpr uint8_t GYRO_XOUT0 = 0x43;
    static constexpr uint8_t GYRO_YOUT0 = 0x45;
    static constexpr uint8_t GYRO_ZOUT0 = 0x47;
    static constexpr uint8_t ACCEL_CONFIG = 0x1C;
    static constexpr uint8_t GYRO_CONFIG = 0x1B;
    static constexpr uint8_t MPU_CONFIG = 0x1A;

    MPU6050(uint8_t address);
    ~MPU6050();

    double get_temp();

    void set_accel_range(uint8_t accel_range);
    int8_t read_accel_range(bool raw = false);
    void get_accel_data(double* accel_data, uint8_t gyro_range, bool g = false);

    void set_gyro_range(uint8_t gyro_range);
    void set_filter_range(uint8_t filter_range = FILTER_BW_256);
    int16_t read_gyro_range(bool raw = false);
    void get_gyro_data(double* gyro_data,uint8_t gyro_range);

    void get_all_data(double* accel_data, double* gyro_data, double* temp);

    void reset_mpu6050();
    void disable_temp_sensor();
    void enable_temp_sensor();

    void sleep();

private:
    uint8_t address;
    int file;

    uint8_t read_byte_data(uint8_t reg);
    void write_byte_data(uint8_t reg, uint8_t value);
    int16_t read_i2c_word(uint8_t reg);
};

#endif // MPU6050_H
