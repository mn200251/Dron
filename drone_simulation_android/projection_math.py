import numpy as np

class Projector():

    def __init__(
        self, canonical_near_plane_center=np.array([1, 1, 1]),
        near_plane_center=np.array([5, 5, 5, 1], dtype=float),
        canonical_volume_size=np.array([2, 2, 2], dtype=float),
        orthographic_volume_size=np.array([100, 100, 100], dtype=float),
        viewer_scene_distance=5
    ):
        self.canonical_near_plane_center = canonical_near_plane_center
        self.near_plane_center = near_plane_center
        # translate center of near plane matrix
        self.tcnpm = None
        
        self.canonical_volume_size = canonical_volume_size
        self.orthographic_volume_size = orthographic_volume_size
        # scale orthogonal volume to size of canonical matrix
        self.sc_orth2canonm = None

        self.viewer_scene_distance = viewer_scene_distance
        # transform frustom volume to orthographic matrix
        self.tfv2om = None


    # translate center of near plane matrix
    def get_tcnpm(self):
        if self.tcnpm is None:
            #self.near_plane_center = self.get_orth2canonm().dot(self.near_plane_center)
            self.tcnpm = np.array([
                [1, 0, 0, self.canonical_near_plane_center[0] - self.near_plane_center[0]],
                [0, 1, 0, self.canonical_near_plane_center[1] - self.near_plane_center[1]],
                [0, 0, 1, self.canonical_near_plane_center[2] - self.near_plane_center[2]],
                [0, 0, 0, 1],
            ])
        return self.tcnpm
    
    def set_canonical_volume_size(self, canonical_volume_size):
        self.canonical_volume_size = canonical_volume_size
        self.sc_orth2canonm = None
    
    # scale orthogonal volume to size of canonical matrix
    def get_orth2canonm(self):
        if self.sc_orth2canonm is None:
            self.sc_orth2canonm = np.array([
                [self.canonical_volume_size[0] / self.orthographic_volume_size[0], 0, 0, 0],
                [0, self.canonical_volume_size[1] / self.orthographic_volume_size[1], 0, 0],
                [0, 0, self.canonical_volume_size[2] / self.orthographic_volume_size[2], 0],
                [0, 0, 0, 1]
            ])
        return self.sc_orth2canonm
    
    # transform frustom volume to orthographic matrix
    def get_tfv2om(self):
        if self.tfv2om is None:
            self.tfv2om = np.array([
                [self.viewer_scene_distance, 0, 0, 0],
                [0, self.viewer_scene_distance, 0, 0],
                [0, 0, 2 * self.viewer_scene_distance + self.orthographic_volume_size[2], 
                -self.viewer_scene_distance * (self.viewer_scene_distance + self.orthographic_volume_size[2])],
                [0, 0, 1, 0]
            ])
        return self.tfv2om
    
    def p2_canonical(self, obj_in_frustom):
        #projected_obj = self.get_tcnpm().dot(self.get_orth2canonm().dot(self.get_tfv2om().dot(obj_in_frustom)))
        #projected_obj = self.get_tcnpm().dot(self.get_orth2canonm().dot(obj_in_frustom))
        m1 = self.get_tfv2om().dot(obj_in_frustom)
        m1 = m1 / m1[3]
        m2 = self.get_orth2canonm().dot(m1)
        m2 = m2 / m2[3]
        projected_obj = self.get_tcnpm().dot(m2)
        return projected_obj / projected_obj[3]
    





if __name__ == "__main__":
    pr = Projector()
    print(pr.get_tcnpm())
    print(pr.get_orth2canonm())
    print(pr.get_tfv2om())
    """print("test translation: ")
    print(pr.get_tcnpm().dot(np.array([5, 5, 5, 1])))
    print(pr.get_tcnpm().dot(np.array([100, 50, 15, 1])))
    print("test scaling: ")
    print(pr.get_orth2canonm().dot(np.array([5, 5, 5, 1])))
    print(pr.get_orth2canonm().dot(np.array([5, 5, 105, 1])))
    print(pr.get_orth2canonm().dot(np.array([-45, 55, 55, 1])))
    print(pr.get_orth2canonm().dot(np.array([100, 50, 15, 1])))"""
    print("test frustom transform: ")
    print(pr.p2_canonical(np.array([5, 5, 5, 1])))
    print(pr.p2_canonical(np.array([55, -45, 105, 1])))