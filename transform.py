import numpy as np
from functools import partial
from box.constrains import Transform


def transform_points(points: np.array, mat: np.array) -> np.array:
    if mat.shape != (2,2):
        raise ValueError(f"Expected (2,2) matrix for transformation got {mat.shape}")
    if points.shape[1] != 2:

        raise ValueError(f"Expected (-1,2) shaped list of points got {points.shape}")
    
    # [[xy], [xy], ....] -> [[xxxxxx], [yyyyyyy]]
    P = np.array(points).reshape((-1), order="F").reshape(2, -1)
    P_prime = mat.dot(P)
    # [[xxxxxx], [yyyyyyy]] ->[[xy], [xy], ....]
    points = P_prime.reshape(-1, order="F").reshape(-1, 2)
    return points

def _reflect_on_x_axis() -> Transform:
    matrix = np.array([
        [1, 0],
        [0, -1]
    ])
    return partial(transform_points, mat=matrix)

reflect_on_x_axis = _reflect_on_x_axis()