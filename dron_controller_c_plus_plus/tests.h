#ifndef TESTS_H
#define TESTS_H

#include <gpiod.h>
#include <iostream>
#include <unistd.h>
#include "mpu6050.h"

#define CONSUMER "blink-led"
#define LED_PIN 17

int led_test();

int mpu_test();

void calibrate_mpu6050(MPU6050& mpu, double* acc_bias, double* gyro_bias, int duration ) ;

void calculate_angles(MPU6050& mpu, double* acc_bias, double* gyro_bias);

#endif // TESTS_H
