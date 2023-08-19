from __future__ import annotations
import enum
from typing import Dict, List, Protocol

from box.edge import Edge
from box.geometry import Path, Plane, Line

from box.transform import Transform, create_transform, mat_reflect_x, mat_reflect_y, mat_shift, mat_rot_90

class FaceConstraintProvider(Protocol):

    def __call__(self, path: Path, face: Face|None = None) -> Path:
        """Append constraints to path of face"""
        ...

class FaceType(enum.Enum):
    BOTTOM_TOP = 1
    FRONT_BACK = 2
    SIDE_LEFT_RIGHT = 3

class Face:

    def __init__(self, edge_1: Edge, edge_2: Edge, thickness:float, name="Face", plane: Plane = Plane.XY) -> None:
        self.edge_1: Edge = edge_1
        self.edge_2: Edge = edge_2
        self.thickness: float = thickness
        self.name = name
        self.constraint_providers: List[FaceConstraintProvider] = []
        self.post_path_transforms: List[Transform] = []
        self.plane: Plane = plane

    def apply_constrains(self, path: Path) -> Path:

        for provider in self.constraint_providers:
            path = provider(path=path, face=self)
        
        return path

    def build_path(self) -> Path:

        base_path_e1: Path = self.edge_1.make_path(self.thickness) # zero, in x-direction
        base_path_e2: Path = self.edge_2.make_path(self.thickness) # zero, in x-dircetion 


        rot90_shiftx_e1 = create_transform(mat_shift(dx=self.edge_1.length), mat_rot_90)
        reflectx_shifty_e2 = create_transform(mat_shift(dy=self.edge_2.length), mat_reflect_x )
        reflectx_rot90 = create_transform(mat_rot_90, mat_reflect_x) 

        paths = [
            base_path_e2.transform(rot90_shiftx_e1),
            base_path_e1.transform(reflectx_shifty_e2).reverse(copy=False),
            base_path_e2.transform(reflectx_rot90).reverse(copy=False)
            ]
        
        path = base_path_e1
        for p in paths:
            path = path.concat(p)

        for t in self.post_path_transforms:
            path = path.transform(t)

        path = self.apply_constrains(path)

        return path
