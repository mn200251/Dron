import numpy as np

def rotation_matrix_factory(angle, unit_vector, degrees=False):
    if degrees: angle = angle * np.pi / 180
    unit_vector =     axis_rotation_matrix = np.array([
        [np.cos(angle) + unit_vector[0] * unit_vector[0] * (1 - np.cos(angle)), unit_vector[0] * unit_vector[1] * (1 - np.cos(angle)) - unit_vector[2] * np.sin(angle), unit_vector[0] * unit_vector[2] * (1 - np.cos(angle)) + unit_vector[1] * np.sin(angle), 0],
        [unit_vector[1] * unit_vector[0] * (1 - np.cos(angle)) + unit_vector[2] * np.sin(angle), np.cos(angle) + unit_vector[1] * unit_vector[1] * (1 - np.cos(angle)), unit_vector[1] * unit_vector[2] * (1 - np.cos(angle)) - unit_vector[0] * np.sin(angle), 0],
        [unit_vector[2] * unit_vector[0] * (1 - np.cos(angle)) - unit_vector[1] * np.sin(angle), unit_vector[2] * unit_vector[1] * (1 - np.cos(angle)) + unit_vector[0] * np.sin(angle), np.cos(angle) + unit_vector[2] * unit_vector[2] * (1 - np.cos(angle)), 0],
        [0, 0, 0, 1]
    ])
    return axis_rotation_matrix

def cross_product(u, v):
    return np.array([u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0], 1], dtype=float)

def normalize_vector(v):
    if v.sum() == 0: return v
    v = v / np.sqrt(np.array([v[0] * v[0], v[1] * v[1], v[2] * v[2]], dtype=float).sum())
    v[3] = 1
    return v

if __name__ == "__main__":

    rotation_matrix = rotation_matrix_factory(0.05, np.array([0, 2, 2.7]) / np.sqrt(4 + 2.7**2))
    print(rotation_matrix)