#include <iostream>
#include "tests.h"

using namespace std;

int main()
{
    double accel_bias[3] = {0.0, 0.0, 0.0};
    double gyro_bias[3] = {0.0, 0.0, 0.0};
    MPU6050 mpu(0x68);  // Initialize MPU6050 with address 0x68

    mpu.reset_mpu6050();
    calibrate_mpu6050(mpu, accel_bias, gyro_bias,5);
    calculate_angles(mpu,accel_bias,gyro_bias);
    mpu.sleep();
    return 0;
}
