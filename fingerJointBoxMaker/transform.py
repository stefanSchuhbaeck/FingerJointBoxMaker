import numpy as np
from functools import partial, reduce
from fingerJointBoxMaker.constrains import Transform


def transform_points(points: np.array, mat: np.array) -> np.array:
    # if mat.shape != (2,2):
        # raise ValueError(f"Expected (2,2) matrix for transformation got {mat.shape}")
    if points.shape[1] != 2:

        raise ValueError(f"Expected (-1,2) shaped list of points got {points.shape}")
    
    # [[xy], [xy], ....] -> [[xxxxxx], [yyyyyyy], [1111111]] (homogenoues coordinates)
    P = np.append(points.T, np.ones(points.shape[0])).reshape((3, -1))
    
    P_prime = np.matmul(mat, P)
    # [[xxxxxx], [yyyyyyy]] ->[[xy], [xy], ....]
    points = P_prime[:2].T
    return points

mat_reflect_x = np.array([
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, 1 ]
    ])

mat_reflect_y = np.array([
        [-1, 0, 0],
        [0, 1, 0],
        [0, 0, 1 ]
])

mat_rot_90 = np.array([
    [0, -1, 0],
    [1, 0, 0],
    [0, 0, 1]
])

def mat_rot(angle) -> np.array:
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])

def mat_shift(dx: float = 0., dy: float= 0.) -> np.array:
    return np.array([
        [1, 0, dx],
        [0, 1, dy],
        [0, 0, 1]
    ])

def create_transform(*mat: np.array) -> Transform:
    if len(mat) > 1:
        mat = reduce(np.matmul, mat)
    else:
        mat = mat[0]
    return partial(transform_points, mat=mat)

def _reflect_on_x_axis() -> Transform:
    return partial(transform_points, mat=mat_reflect_x)



reflect_on_x_axis = _reflect_on_x_axis()