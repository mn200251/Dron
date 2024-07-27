import numpy as np
import pygame
import physics_engine as pe

class Drone():
    
    def __init__(self, drone_center, radius, projector=None):
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
        self.motor_forces_per = np.array([0, 0, 0, 0], dtype=float)
        # max angle that it can rotate in one iteration
        self.max_motor_rotation_speed = 30
        self.translational_speed = np.array([0, 0, 0], dtype=float)
        self.angular_speed = np.array([0, 0, 0], dtype=float)
        self.thrust_vectors = None

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

        self.pr = projector
        self.radius = radius
        self.body_color = (120, 120, 120)
        self.motor_color = (255, 0, 0)
        self.propeller_color = (255, 0, 0)
    
    def get_drone_center(self):
        return self.drone_center

    def get_motor_coordinates(self):
        return self.motor_coordinates
    
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
    
    def rotate_around_(self, rotation_center, angle, unit_vector):
        self.motor_coordinates += self.drone_center - rotation_center
        self.propeller_centers += self.drone_center - rotation_center
        self.rotate(angle, unit_vector)
        self.motor_coordinates -= self.drone_center - rotation_center
        self.propeller_centers -= self.drone_center - rotation_center
    
    def motor_set_power_percent(self, motor_index, force_percent):
        force_percent = min(1, force_percent)
        force_percent = max(-1, force_percent)
        self.motor_forces_per[motor_index] = force_percent
    
    def calculate_forces(self):
        #print(np.sign(self.motor_forces_per))
        motor_thrust_magnitudes = np.cbrt((2 * pe.DroneParameters.rho * pe.DroneParameters.A) * np.square(self.motor_forces_per))
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
            pe.DroneParameters.b * (motor_square_angular_vel_contrib_magn * np.sign(self.motor_forces_per)).sum()
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
        translational_speen[1], translational_speen[2] = translational_speen[2], translational_speen[1]
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
            rotation_matrix = pe.rotation_matrix_factory(self.max_motor_rotation_speed * self.motor_forces_per[i], unit_vector, True)
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
        

    def draw_to_(self, screen):
        body_width = 5
        motor_point_size = 2
        motor_width = 10
        thrust_scaling_factor = 15
        gravity_scaling_factor = 2.5
        motors = self.motor_coordinates[self.motor_coordinates[:, 2].argsort()]
        drone_center = self.drone_center

        thrust_force_end = None
        if self.thrust_vectors is not None:
            thrust_force_vectors = np.insert(thrust_scaling_factor * self.thrust_vectors, 3, np.full(shape=4, fill_value=0, dtype=float), axis=1)
            thrust_force_begin = self.propeller_centers + 2 * pe.normalize_vector(thrust_force_vectors[0])
            thrust_force_end = self.propeller_centers + thrust_force_vectors
            thrust_force_begin = thrust_force_begin[self.propeller_centers[:, 2].argsort()] 
            thrust_force_end = thrust_force_end[self.propeller_centers[:, 2].argsort()]
            gravity_force_vector = np.insert(gravity_scaling_factor * self.gravity_vector, 3, np.array([1]), axis=0)
            gravity_force_begin = self.drone_center + 2 * pe.normalize_vector(gravity_force_vector)
            gravity_force_end = self.drone_center + gravity_force_vector

        propeller_centers = self.propeller_centers[self.propeller_centers[:, 2].argsort()]

        pvals = np.array([
            [self.propellers[0, :, 2].min(), 0],
            [self.propellers[1, :, 2].min(), 1],
            [self.propellers[2, :, 2].min(), 2],
            [self.propellers[3, :, 2].min(), 3]
        ])
        propellers = self.propellers[pvals[pvals[:, 0].argsort()][:, 1].astype(int)]

        if self.pr is not None:
            for i in range(4):
                motors[i] = self.pr.p2_canonical(motors[i])
                propeller_centers[i] = self.pr.p2_canonical(propeller_centers[i])
                if self.thrust_vectors is not None:
                    thrust_force_begin[i] = self.pr.p2_canonical(thrust_force_begin[i])
                    thrust_force_end[i] = self.pr.p2_canonical(thrust_force_end[i])
                for j in range(len(propellers[i])):
                    propellers[i][j] = self.pr.p2_canonical(propellers[i][j])
            drone_center = self.pr.p2_canonical(drone_center)
            if self.thrust_vectors is not None:
                gravity_force_begin = self.pr.p2_canonical(gravity_force_begin)
                gravity_force_end = self.pr.p2_canonical(gravity_force_end)
        drone_center = tuple(drone_center[0:2])
        mmax = motors[:, 2].max()

        if self.thrust_vectors is not None:
            #print(gravity_force_begin)
            #print(gravity_force_end)
            pygame.draw.line(screen, (255, 0, 0), tuple(gravity_force_begin[0:2]), tuple(gravity_force_end[0:2]), 3)
        for i in range(3, -1, -1):
            motor_point_scaling = motor_point_size * motors[i][2] / mmax
            pygame.draw.circle(screen, self.motor_color, (motors[i][0], motors[i][1]), motor_point_scaling, motor_width)
            for j in range(len(propellers[i])):
                pygame.draw.circle(screen, self.motor_color, (propellers[i][j][0], propellers[i][j][1]), motor_point_scaling, motor_width)
            for j in range(4):
                pygame.draw.line(screen, self.propeller_color, tuple(propeller_centers[i][0:2]), tuple(propellers[i][j][0:2]), 4)
                if self.thrust_vectors is not None:
                    pygame.draw.line(screen, (0, 255, 0), tuple(thrust_force_begin[i][0:2]), tuple(thrust_force_end[i][0:2]), 3)
            pygame.draw.line(screen, self.body_color, tuple(motors[i][0:2]), drone_center, width=body_width)


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
    drone.update(physics=True)