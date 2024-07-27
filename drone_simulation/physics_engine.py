import numpy as np
import re

# physical parameters for our drone
class Params:
    k = "k"     # thrust to square of angular velocity proportionality constant
    rho = "rho" # air density
    AP = "A"    # area swept by rotor
    kd = "kd"   # transpositional air friction proportionality constant
    b = "b"     # coeficient of air friction
    Cd = "Cd"   # drag coefficient
    R = "R"     # radius of the propeller in m
    A = "A"     # area of the propeller cross-section (area of a stationary propeller) in m^2
    m = "m"     # mass of drone in kg
    L = "L"     # distance from the center of quadcopter to the propellers
    I = "I"     # inertia matrix
DroneParameters = Params()

gravity_magnitude = 9.80665 / 2
gravity_vector = None


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

def magnitude(vec):
    return np.sqrt(np.array([vec[0] * vec[0], vec[1] * vec[1], vec[2] * vec[2]], dtype=float).sum())


def angle_between_vectors(u, v):
    return np.arccos(((u * v).sum() - 1) \
        / np.sqrt(np.array([u[0] * u[0], u[1] * u[1], u[2] * u[2]], dtype=float).sum()) \
        / np.sqrt(np.array([v[0] * v[0], v[1] * v[1], v[2] * v[2]], dtype=float).sum()))

def normalize_vector(v):
    if v.sum() == 0: return v
    v = v / magnitude(v)
    if len(v) >= 4: v[3] = 1
    return v

    
def init_gravity_vector(ground):
    global gravity_vector
    u = ground.bottom_left[0:3] - ground.center[0:3]
    v = ground.bottom_right[0:3] - ground.center[0:3]
    unit_vector = cross_product(u, v)[0:3]
    unit_vector = normalize_vector(unit_vector)
    gravity_vector = gravity_magnitude * -unit_vector

def get_grav_vector():
    return gravity_vector

def load_parameters(from_file="./drone_simulation/parameters.txt", show_params=True):
    ident_re = re.compile(r" *[a-zA-Z]+")
    irow_re = re.compile(r" *([+-]?\d+\.?\d*) *([+-]?\d+\.?\d*) *([+-]?\d+\.?\d*)")
    with open(from_file, "r") as f:
        for line in f.readlines():
            matched_ident_re = ident_re.match(line)
            if matched_ident_re is not None:
                param_name = matched_ident_re.group().strip()
                if param_name == "I": Params.__setattr__(DroneParameters, param_name, [])
                else:
                    value = re.compile(r"[+-]?\d+\.?\d*").findall(line)
                    if value != []: Params.__setattr__(DroneParameters, param_name, float(value[0]))
            else:
                matched_re = irow_re.match(line)
                if matched_re is not None:
                    DroneParameters.I.append([
                        float(matched_re.group(1)),
                        float(matched_re.group(2)),
                        float(matched_re.group(3))
                    ])
    DroneParameters.I = np.array(DroneParameters.I)
    DroneParameters.Cd = 0.279 * DroneParameters.m
    DroneParameters.b = DroneParameters.R ** 3 \
        * DroneParameters.rho * DroneParameters.Cd * DroneParameters.A / 2

    if show_params:
        for key in DroneParameters.__dict__:
            print(key + " = " + str(Params.__getattribute__(DroneParameters, key)))

if __name__ == "__main__":
    rotation_matrix = rotation_matrix_factory(0.05, np.array([0, 2, 2.7]) / np.sqrt(4 + 2.7**2))
    print(rotation_matrix)