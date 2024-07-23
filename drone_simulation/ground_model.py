import numpy as np
import pygame
import physics_engine as pe

class Ground():
    
    def __init__(self, ground_center, width, length, max_height, number_of_points, projector=None):

        self.center = ground_center
        print(self.center)
        self.width = width
        self.length = length
        self.number_of_points = number_of_points
        self.pr = projector
        self.color = (100, 100, 100)
    
        hl = self.length / 2
        hw = self.width / 2
        self.bottom = self.center + np.array([0, 0, -hl, 0], dtype=float)
        self.top = self.center + np.array([0, 0, hl, 0], dtype=float)
        self.bottom_left = self.bottom + np.array([-hw, 0, 0, 0], dtype=float)
        self.bottom_right = self.bottom + np.array([hw, 0, 0, 0], dtype=float)
        self.top_left = self.top + np.array([-hw, 0, 0, 0], dtype=float)
        self.top_right = self.top + np.array([hw, 0, 0, 0], dtype=float)

        self.point_length_dist = self.length / (self.number_of_points - 1)
        self.point_width_dist = self.width / (self.number_of_points - 1)

        self.grid_x = np.full(shape=self.number_of_points, fill_value=self.point_width_dist, dtype=float)
        self.grid_x[0] = self.bottom_left[0]
        self.grid_x = self.grid_x.cumsum()
        self.grid_y = np.random.uniform(low=-max_height, high=0, size=self.number_of_points * self.number_of_points)
        self.grid_z = np.full(shape=self.number_of_points, fill_value=self.point_length_dist, dtype=float)
        self.grid_z[0] = self.bottom_left[2]
        self.grid_z = self.grid_z.cumsum()

        grid_xz = np.array(np.array(np.meshgrid(self.grid_x, self.grid_z)).T.reshape(-1, 2))
        self.points = np.insert(grid_xz, 1, self.grid_y, axis=1)
        self.points = np.insert(self.points, 3, np.full(shape=self.number_of_points * self.number_of_points, fill_value=1, dtype=float), axis=1)

        self.x_lines_begin = np.insert(self.grid_x.reshape(-1, 1), 1, np.full(shape=self.number_of_points, fill_value=self.center[1], dtype=float), axis=1)
        self.x_lines_end = np.insert(self.x_lines_begin, 2, np.full(shape=self.number_of_points, fill_value=self.top[2], dtype=float), axis=1)
        self.x_lines_begin = np.insert(self.x_lines_begin, 2, np.full(shape=self.number_of_points, fill_value=self.bottom[2], dtype=float), axis=1)
        self.x_lines_begin = np.insert(self.x_lines_begin, 3, np.full(shape=self.number_of_points, fill_value=1, dtype=float), axis=1)
        self.x_lines_end = np.insert(self.x_lines_end, 3, np.full(shape=self.number_of_points, fill_value=1, dtype=float), axis=1)

        self.z_lines_end = np.insert(self.grid_z.reshape(-1, 1), 0, np.full(shape=self.number_of_points, fill_value=self.center[1], dtype=float), axis=1)
        self.z_lines_begin = np.insert(self.z_lines_end, 0, np.full(shape=self.number_of_points, fill_value=self.top_left[0], dtype=float), axis=1)
        self.z_lines_end = np.insert(self.z_lines_end, 0, np.full(shape=self.number_of_points, fill_value=self.top_right[0], dtype=float), axis=1)
        self.z_lines_end = np.insert(self.z_lines_end, 3, np.full(shape=self.number_of_points, fill_value=1, dtype=float), axis=1)
        self.z_lines_begin = np.insert(self.z_lines_begin, 3, np.full(shape=self.number_of_points, fill_value=1, dtype=float), axis=1)
    
    def rotate(self, angle, unit_vector):
        rotation_matrix = pe.rotation_matrix_factory(angle, unit_vector, True)
        for i in range(len(self.points)):
            self.points[i] = rotation_matrix.dot(self.points[i])
    
    def rotate_ground(self, angle, unit_vector):
        self.points -= self.center
        self.rotate(angle, unit_vector)
        self.points += self.center
    
    def draw_to_(self, screen):

        """traversed = np.full(shape=self.number_of_points*self.number_of_points, fill_value=False, dtype=bool)
        points = self.points[self.points[:, 2].argsort()]
        if self.pr is not None:
            for i in range(len(points)):
                points[i] = self.pr.p2_canonical(points[i])"""
        
        #for i in range(len(points) - 1, -1, -1):
            #pygame.draw.circle(screen, self.color, (points[i][0], points[i][1]), 1)
            #traversed[i] = True
            #remp = points[~traversed]
            #dist = np.sort(np.square(remp - points[i]).sum(axis=1))
            #print(dist)
            #if 2 * i < len(points):
                #pygame.draw.line(screen, self.color, (points[i][0], points[i][1]), (points[i * 2][0], points[i * 2][1]))
        
        #if self.pr is not None:
            #x = self.pr.p2_canonical(self.grid_x)
            #z = self.pr.p2_canonical(self.grid_z)

        lines_x_begin = self.x_lines_begin[self.x_lines_begin[:, 2].argsort()]
        lines_x_end = self.x_lines_end[self.x_lines_end[:, 2].argsort()]
        lines_z_begin = np.zeros_like(self.z_lines_begin)
        lines_z_end = np.zeros_like(self.z_lines_end)
        if self.pr is not None:
            for i in range(len(self.x_lines_begin)):
                lines_x_begin[i] = self.pr.p2_canonical(lines_x_begin[i])
                lines_x_end[i] = self.pr.p2_canonical(lines_x_end[i])
                lines_z_begin[i] = self.pr.p2_canonical(self.z_lines_begin[i])
                lines_z_end[i] = self.pr.p2_canonical(self.z_lines_end[i])
        
        for i in range(len(self.x_lines_begin) - 1, -1, -1):
            pygame.draw.line(screen, self.color, tuple(lines_x_begin[i][0:2]), tuple(lines_x_end[i][0:2]))
            pygame.draw.line(screen, self.color, tuple(lines_z_begin[i][0:2]), tuple(lines_z_end[i][0:2]))
    



if __name__ == "__main__":
    a = Ground(np.array([0, 0, 0, 0], dtype=float), width=100, length=100, number_of_points=100)
    #print(a.points)