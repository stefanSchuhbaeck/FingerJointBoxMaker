from __future__ import annotations
from typing import Any, Protocol
import numpy as np

class Transform(Protocol):

    def __call__(self, points: np.array) -> np.array:
        """applay transfrom `mat` on `points` of the form (2, -1). Returns transformed points"""
        ...


class Constraint(Protocol):

    Coliniear = "coliniear"
    GeoDimension = "dim"
    Perpendicular = "perpendicualr"
    EqualConstraint = "EqualConstraint"
    Horizontal = "Horizontal"
    Vertical = "Vertical"
    CreatePoint = "createPoint"

    def apply_transform(self, transform: Transform) -> Constraint:
        ...

    def get_name(self) -> str:
        ...

    def process(self, transform_F) -> Any:
        ...

