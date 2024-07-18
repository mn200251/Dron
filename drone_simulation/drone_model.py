import numpy as np

class Drone():
    
    def __init__(self):
        initial_center = [100, 100, 100]
        radius = 5
        # drone frame offset, motor0_coordinates, motor1_coordinates, motor2_coordinates, motor3_coordinates
        # motor0 is on +x axis, motor1 is on +y axis, motor2 is on -x axis, motor3 is on -y axis
        self.coordinates = np.array([
            [initial_center[0], initial_center[0] + radius, initial_center[0], initial_center[0] - radius, initial_center[0]],
            [initial_center[1], initial_center[1], initial_center[1] + radius, initial_center[1], initial_center[0] - radius],
            [initial_center[2], initial_center[2], initial_center[2], initial_center[2], initial_center[2]],
            [1, 1, 1, 1, 1]
        ])
    
    def get_pos(self):
        return self.coordinates
    
    def dist_from(self, frame_origin):
        return np.sqrt(((self.coordinates[:3, 0] - frame_origin) ** 2).sum())

drone = Drone()

if __name__ == "__main__":
    print(drone.get_pos())
    a = np.array([1, -1, 0, 0])
    print(a.dot(drone.get_pos()))
    print(drone.dist_from(np.array([97, 96, 100])))