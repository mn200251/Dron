#include "tests.h"

int mpu_basic_test() {
    MPU6050 mpu(0x68);  // Initialize MPU6050 with address 0x68

    mpu.reset_mpu6050();
    std::cout << "Temperature: " << mpu.get_temp() << " °C" << std::endl;

    double accel_data[3];
    uint8_t accel_range=mpu.read_accel_range();
    mpu.get_accel_data(accel_data,accel_range);
    std::cout << "Accelerometer data:" << std::endl;
    std::cout << "X: " << accel_data[0] << std::endl;
    std::cout << "Y: " << accel_data[1] << std::endl;
    std::cout << "Z: " << accel_data[2] << std::endl;

    double gyro_data[3];
    uint8_t gyro_range = mpu.read_gyro_range();
    mpu.get_gyro_data(gyro_data,gyro_range);
    std::cout << "Gyroscope data:" << std::endl;
    std::cout << "X: " << gyro_data[0] << std::endl;
    std::cout << "Y: " << gyro_data[1] << std::endl;
    std::cout << "Z: " << gyro_data[2] << std::endl;

    mpu.sleep(); // Set MPU6050 to sleep

    return 0;
}


void calibrate_mpu6050(MPU6050& mpu, double* acc_bias, double* gyroscope_bias, int duration = 5) {
    int num_samples = duration * 100;  // Taking 100 samples per second
    double accel_bias[3] = {0.0, 0.0, 0.0};
    double gyro_bias[3] = {0.0, 0.0, 0.0};
    uint8_t gyro_range = mpu.read_gyro_range();
    uint8_t accel_range=mpu.read_accel_range();

    for (int i = 0; i < num_samples; ++i) {
        double accel_data[3];
        double gyro_data[3];

        mpu.get_accel_data(accel_data,accel_range, false);
        mpu.get_gyro_data(gyro_data,gyro_range);

        accel_bias[0] += accel_data[0];
        accel_bias[1] += accel_data[1];
        accel_bias[2] += accel_data[2];

        gyro_bias[0] += gyro_data[0];
        gyro_bias[1] += gyro_data[1];
        gyro_bias[2] += gyro_data[2];

        usleep(10000); // Sleep for 10 000 microseconds between samples
    }

    accel_bias[0] /= num_samples;
    accel_bias[1] /= num_samples;
    accel_bias[2] /= num_samples;
    gyro_bias[0] /= num_samples;
    gyro_bias[1] /= num_samples;
    gyro_bias[2] /= num_samples;

    // Adjust the accelerometer bias to account for gravity on the Z-axis
    accel_bias[2] -= MPU6050::GRAVITIY_MS2;

    if (acc_bias != nullptr) {
        acc_bias[0] = accel_bias[0];
        acc_bias[1] = accel_bias[1];
        acc_bias[2] = accel_bias[2];
    }
    if (gyroscope_bias != nullptr) {
        gyroscope_bias[0] = gyro_bias[0];
        gyroscope_bias[1] = gyro_bias[1];
        gyroscope_bias[2] = gyro_bias[2];
    }

    // Print biases for debugging
    std::cout << "Accelerometer Bias: x=" << accel_bias[0] << ", y=" << accel_bias[1] << ", z=" << accel_bias[2] << std::endl;
    std::cout << "Gyroscope Bias: x=" << gyro_bias[0] << ", y=" << gyro_bias[1] << ", z=" << gyro_bias[2] << std::endl;
}

void calculate_angles(MPU6050& mpu, double* acc_bias, double* gyro_bias) {

    const double DT = 0.07;
    const double AA = 0.98;
    double gyroXangle = 0.0, gyroYangle = 0.0, gyroZangle = 0.0;
    double CFangleX = 0.0, CFangleY = 0.0;

    uint8_t gyro_range = mpu.read_gyro_range();
    uint8_t accel_range=mpu.read_accel_range();

    int cnt = 0;
    while (true) {
        cnt++;
        auto t1 = std::chrono::steady_clock::now();

        double accel_data[3];
        double gyro_data[3];

        mpu.get_accel_data(accel_data,accel_range, false);
        mpu.get_gyro_data(gyro_data,gyro_range);

        gyro_data[0] -= gyro_bias[0];
        gyro_data[1] -= gyro_bias[1];
        gyro_data[2] -= gyro_bias[2];

        accel_data[0] -= acc_bias[0];
        accel_data[1] -= acc_bias[1];
        accel_data[2] -= acc_bias[2];

        // Calculate angles from accelerometer
        double AccXangle = atan2(accel_data[0], sqrt(accel_data[1] * accel_data[1] + accel_data[2] * accel_data[2])) * 180.0 / M_PI;
        double AccYangle = atan2(accel_data[1], accel_data[2]) * 180.0 / M_PI;

        // Calculate angles from gyroscope
        gyroXangle += gyro_data[0] * DT;
        gyroYangle += gyro_data[1] * DT;
        gyroZangle += gyro_data[2] * DT;

        // Apply complementary filter
        CFangleX = AA * (CFangleX + gyro_data[0] * DT) + (1 - AA) * AccXangle;
        CFangleY = AA * (CFangleY + gyro_data[1] * DT) + (1 - AA) * AccYangle;

        if (cnt == 20) {
            std::cout << "Pitch (CFangleX): " << CFangleX << " degrees, Roll (CFangleY): " << CFangleY << " degrees" << std::endl;
            cnt = 0;
        }

        auto t2 = std::chrono::steady_clock::now();
        //duration is in seconds
        usleep(1000000*std::max(0.0, DT - std::chrono::duration<double>(t2 - t1).count()));
    }
}











