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
        
        self.motor_forces_per = np.array([0, 0, 0, 0], dtype=float)
        # max angle that it can rotate in one iteration
        self.max_motor_rotation_speed = 30

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
    
    def motor_set_force_percent(self, motor_index, force_percent):
        force_percent = min(1, force_percent)
        force_percent = max(-1, force_percent)
        self.motor_forces_per[motor_index] = force_percent

    def update(self):
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

    def draw_to_(self, screen):
        body_width = 5
        motor_point_size = 2
        motor_width = 10
        motors = self.motor_coordinates[self.motor_coordinates[:, 2].argsort()]
        propeller_centers = self.propeller_centers[self.propeller_centers[:, 2].argsort()]

        pvals = np.array([
            [self.propellers[0, :, 2].min(), 0],
            [self.propellers[1, :, 2].min(), 1],
            [self.propellers[2, :, 2].min(), 2],
            [self.propellers[3, :, 2].min(), 3]
        ])
        propellers = self.propellers[pvals[pvals[:, 0].argsort()][:, 1].astype(int)]

        drone_center = self.drone_center
        if self.pr is not None:
            for i in range(4):
                motors[i] = self.pr.p2_canonical(motors[i])
                propeller_centers[i] = self.pr.p2_canonical(propeller_centers[i])
                for j in range(len(propellers[i])):
                    propellers[i][j] = self.pr.p2_canonical(propellers[i][j])
            drone_center = self.pr.p2_canonical(drone_center)
        drone_center = tuple(drone_center[0:2])
        mmax = motors[:, 2].max()

        for i in range(3, -1, -1):
            motor_point_scaling = motor_point_size * motors[i][2] / mmax
            pygame.draw.circle(screen, self.motor_color, (motors[i][0], motors[i][1]), motor_point_scaling, motor_width)
            for j in range(len(propellers[i])):
                pygame.draw.circle(screen, self.motor_color, (propellers[i][j][0], propellers[i][j][1]), motor_point_scaling, motor_width)
            for j in range(4):
                pygame.draw.line(screen, self.propeller_color, tuple(propeller_centers[i][0:2]), tuple(propellers[i][j][0:2]), 4)
            pygame.draw.line(screen, self.body_color, tuple(motors[i][0:2]), drone_center, width=body_width)


if __name__ == "__main__":
    drone = Drone(np.array([0, 0, 0], dtype=float), 5)
    print(drone.get_drone_center())
    print(drone.get_motor_coordinates())
    print(drone.get_motor_coordinates())
    print(drone.dist_from(np.array([97, 96, 100, 1])))