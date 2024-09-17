import numpy as np
import pygame
import physics_engine as pe


class Drone():
    
    GYRO_NOISE = True
    GYRO_NOISE_PERCENT = 0.01

    def __init__(self, drone_center, radius):
        # drone frame offset, motor0_coordinates, motor1_coordinates, motor2_coordinates, motor3_coordinates
        # motor0 is on +x axis, motor1 is on +y axis, motor2 is on -x axis, motor3 is on -y axis
        self.drone_center = np.array([drone_center[0], drone_center[1], drone_center[2], 1], dtype=float)
        self.motor_coordinates = np.array([
            np.array([drone_center[0] + radius, drone_center[1], drone_center[2], 1], dtype=float),
            np.array([drone_center[0], drone_center[1], drone_center[2] + radius, 1], dtype=float),
            np.array([drone_center[0] - radius, drone_center[1], drone_center[2], 1], dtype=float),
            np.array([drone_center[0], drone_center[0], drone_center[2] - radius, 1], dtype=float),
        ])
        
        self.parameter_loaded = False
        self.motor_power_per = np.array([0, 0, 0, 0], dtype=float)
        # max angle that it can rotate in one iteration
        self.max_motor_rotation_speed = 30
        self.translational_speed = np.array([0, 0, 0], dtype=float)
        self.angular_speed = np.array([0, 0, 0], dtype=float)
        self.thrust_vectors = None
        self.euler_angles = np.array([0, 0, 0], dtype=float)
        self.pd_params_integral = np.array([0, 0, 0], dtype=float)

        self.propeller_centers = self.motor_coordinates + np.array([0, -2.5, 0, 0], dtype=float)
        propeller_size = radius / 10.
        self.propellers = []
        for i in range(4):
            center = self.propeller_centers[i]
            frame_point1 = center + np.array([propeller_size, 0, 0, 0])
            frame_point2 = center + np.array([0, 0, propeller_size, 0])
            frame_point3 = center + np.array([-propeller_size, 0, 0, 0])
            frame_point4 = center + np.array([0, 0, -propeller_size, 0])
            new_propellers = [frame_point1, frame_point2, frame_point3, frame_point4]

            number_of_points = 32
            for j in range(number_of_points):
                phase = np.pi / number_of_points
                frequency = 2 * np.pi / number_of_points
                new_propellers.append(
                    center + np.array([propeller_size * np.cos(j * frequency + phase), 0,
                        propeller_size * np.sin(j * frequency + phase), 0])
                )

            self.propellers.append(new_propellers)
        
        self.propellers = np.array(self.propellers)

        self.radius = radius
        self.body_color = (120, 120, 120)
        self.motor_color = (255, 0, 0)
        self.propeller_color = (255, 0, 0)
        self.motor_sliders = dict()
    
    def get_drone_center(self):
        return self.drone_center

    def get_motor_coordinates(self):
        return self.motor_coordinates
    
    def add_motor_slider(self, index, slider):
        self.motor_sliders[index] = slider
    
    # frame_origin = np.array([x, y, z, 1])
    def dist_from(self, frame_origin):
        return np.sqrt(((self.drone_center - frame_origin) ** 2).sum())
    
    def rotate(self, angle, unit_vector):
        rotation_matrix = pe.rotation_matrix_factory(angle, unit_vector, True)
        self.motor_coordinates -= self.drone_center
        self.propeller_centers -= self.drone_center
        for i in range(4):
            self.motor_coordinates[i] = rotation_matrix.dot(self.motor_coordinates[i])
            self.propeller_centers[i] = rotation_matrix.dot(self.propeller_centers[i])
            for j in range(len(self.propellers[i])):
                self.propellers[i][j] -= self.drone_center
                self.propellers[i][j] = rotation_matrix.dot(self.propellers[i][j])
                self.propellers[i][j] += self.drone_center
        self.motor_coordinates += self.drone_center
        self.propeller_centers += self.drone_center
        try:
            # return eurler angles for this rotation
            return np.array([
                np.arctan2(rotation_matrix[2][1], rotation_matrix[2][2]),
                np.arctan2(-rotation_matrix[2][0], np.sqrt(np.square(rotation_matrix[2][1]) + np.square(rotation_matrix[2][2]))),
                np.arctan2(rotation_matrix[1][0], rotation_matrix[0][0]),
            ])
        except Exception as e:
            return np.array([0, 0, 0])

    
    def rotate_around_(self, rotation_center, angle, unit_vector):
        self.motor_coordinates += self.drone_center - rotation_center
        self.propeller_centers += self.drone_center - rotation_center
        self.rotate(angle, unit_vector)
        self.motor_coordinates -= self.drone_center - rotation_center
        self.propeller_centers -= self.drone_center - rotation_center
    
    def motor_set_power_percent(self, motor_index, force_percent):
        force_percent = min(1, force_percent)
        force_percent = max(-1, force_percent)
        self.motor_power_per[motor_index] = force_percent
    
    def calculate_forces(self):
        motor_thrust_magnitudes = np.cbrt((2 * pe.DroneParameters.rho * pe.DroneParameters.A) * np.square(self.motor_power_per))
        motor_square_angular_vel_contrib_magn = motor_thrust_magnitudes / pe.DroneParameters.k
        base_force_vectors = []
        for i in range(4):
            u = self.propellers[i][0] - self.propeller_centers[i]
            v = self.propellers[i][1] - self.propeller_centers[i]
            unit_vector = pe.cross_product(u, v)
            unit_vector = pe.normalize_vector(unit_vector)
            base_force_vectors.append(unit_vector[0:3])
        # pointing along negative y axis of the drone frame
        base_force_vectors = np.array(base_force_vectors, dtype=float)
        self.thrust_vectors = np.array([
            base_force_vectors[0] * motor_thrust_magnitudes[0],
            base_force_vectors[1] * motor_thrust_magnitudes[1],
            base_force_vectors[2] * motor_thrust_magnitudes[2],
            base_force_vectors[3] * motor_thrust_magnitudes[3]
        ])
        total_thrust = self.thrust_vectors.sum(axis=0)
        self.gravity_vector = pe.get_grav_vector()
        translational_friction = -pe.DroneParameters.kd * self.translational_speed
        translational_forces_sum = total_thrust + self.gravity_vector + translational_friction
        self.translational_speed = self.translational_speed + translational_forces_sum / pe.DroneParameters.m
        total_torque = np.array([
            pe.DroneParameters.L * pe.DroneParameters.k * (motor_square_angular_vel_contrib_magn[0] - motor_square_angular_vel_contrib_magn[2]),
            pe.DroneParameters.L * pe.DroneParameters.k * (motor_square_angular_vel_contrib_magn[1] - motor_square_angular_vel_contrib_magn[3]),
            pe.DroneParameters.b * (motor_square_angular_vel_contrib_magn * np.sign(self.motor_power_per)).sum()
        ])
        Ixx = pe.DroneParameters.I[0][0]
        Iyy = pe.DroneParameters.I[1][1]
        Izz = pe.DroneParameters.I[2][2]
        self.angular_speed = \
            np.array([total_torque[0] / Ixx, total_torque[1] / Iyy, total_torque[2] / Izz]) - np.array([
                (Iyy - Izz) * self.angular_speed[1] * self.angular_speed[2] / Ixx,
                (Izz - Ixx) * self.angular_speed[0] * self.angular_speed[2] / Iyy,
                (Ixx - Iyy) * self.angular_speed[0] * self.angular_speed[1] / Izz
            ])
    
    def translational_position_update(self):
        speed_factor = 1 / 6000
        translational_speen = np.insert(self.translational_speed * speed_factor, 3, np.array([0]), axis=0)
        self.drone_center += translational_speen
        self.motor_coordinates += translational_speen
        self.propeller_centers += translational_speen
        self.propellers += translational_speen

    def angular_position_update(self):
        angular_speed = self.angular_speed.copy()
        angular_speed[1], angular_speed[2] = angular_speed[2], angular_speed[1]
        self.rotate(pe.magnitude(angular_speed), pe.normalize_vector(angular_speed))
        for i in range(4):
            u = self.propellers[i][0] - self.propeller_centers[i]
            v = self.propellers[i][1] - self.propeller_centers[i]
            unit_vector = pe.cross_product(u, v)
            unit_vector = pe.normalize_vector(unit_vector)
            rotation_matrix = pe.rotation_matrix_factory(self.max_motor_rotation_speed * self.motor_power_per[i], unit_vector, True)
            self.propellers[i] -= self.propeller_centers[i]
            for j in range(len(self.propellers[i])):
                self.propellers[i][j] = rotation_matrix.dot(self.propellers[i][j])
            self.propellers[i] += self.propeller_centers[i]
    
    def update(self, physics=True):
        if not physics: self.angular_position_update()
        else:
            if not self.parameter_loaded:
                pe.load_parameters(); self.parameter_loaded = True
            self.calculate_forces()
            self.translational_position_update()
            self.angular_position_update()
    
    def pd(self):
        # Pd parameters
        Kd = 0.4; Kp = 3
        #Kd = 0.015 / 2; Kp = 0.003 / 2
        dt = 1 / 4
        # IGNORISATI OVO, NIJE TACNO
        # OVO TREBA NORMALNO DA SE KORISTI, MOJ SIMUlATOR IMA PROMENJENE OSE ZBOG
        # PYGAME-a - y osa pokazuje u smeru normalne -z ose, a z osa je normalna y-osa
        thrust_needed = pe.DroneParameters.m * pe.magnitude(pe.get_grav_vector()) \
            / np.cos(self.pd_params_integral[0]) / np.cos(self.pd_params_integral[1])
        #thrust_needed = pe.DroneParameters.m * pe.magnitude(pe.get_grav_vector()) \
            #/ np.cos(self.pd_params_integral[0]) / np.cos(self.pd_params_integral[2])

        error_fi = Kd * self.euler_angles[0] + Kp * self.pd_params_integral[0]
        error_theta = Kd * self.euler_angles[1] + Kp * self.pd_params_integral[1]
        error_psi = Kd * self.euler_angles[2] + Kp * self.pd_params_integral[2]
        Ixx = pe.DroneParameters.I[0][0]
        Iyy = pe.DroneParameters.I[1][1]
        Izz = pe.DroneParameters.I[2][2]
        # needed because of pygame switch
        Iyy, Izz = Izz, Iyy
        k = pe.DroneParameters.k
        b = pe.DroneParameters.b
        L = pe.DroneParameters.L
        square_angular_vel = np.full(shape=4, fill_value=thrust_needed / 4 / k, dtype=float)
        square_angular_vel += np.array([
            -(2 * b * error_fi * Ixx + error_psi * Izz * k * L) / (4 * b * k * L),
            (error_psi * Izz) / (4 * b) - (error_theta * Iyy) / (2 * k * L),
            -(-2 * b * error_fi * Ixx + error_psi * Izz * k * L) / (4 * b * k * L),
            (error_psi * Izz) / (4 * b) + (error_theta * Iyy) / (2 * k * L),
        ])
        self.pd_params_integral += self.euler_angles * dt

        thrusts = k * square_angular_vel
        powers = np.square(thrusts * thrusts * thrusts / (2 * pe.DroneParameters.rho * pe.DroneParameters.A))
        #powers = (4 * powers) / (powers.sum())

        # ovo sam sam namestao
        powers = np.sqrt(np.sqrt(np.sqrt(powers)))
        powers += 1.5 * (powers - powers.min())
        #powers *= np.sqrt(pe.magnitude(pe.get_grav_vector()))
        #powers *= thrust_needed

        #print(powers)
        for i in range(4):
            self.motor_set_power_percent(i, ((-1) ** (i + 1)) * powers[i])

        return np.array([
            0, ((-1) ** (0 + 1)) * powers[0],
            1, ((-1) ** (1 + 1)) * powers[1],
            2, ((-1) ** (2 + 1)) * powers[2],
            3, ((-1) ** (3 + 1)) * powers[3],
        ])


if __name__ == "__main__":
    drone = Drone(np.array([0, 0, 0], dtype=float), 5)
    #print(drone.get_drone_center())
    #print(drone.get_motor_coordinates())
    #print(drone.get_motor_coordinates())
    #print(drone.dist_from(np.array([97, 96, 100, 1])))
    drone.motor_set_power_percent(0, 0.3)
    drone.motor_set_power_percent(1, -0.4)
    drone.motor_set_power_percent(2, 0.5)
    drone.motor_set_power_percent(3, -0.7)
    drone.update()