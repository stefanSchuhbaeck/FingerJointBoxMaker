from __future__ import annotations
import enum
from typing import Any, Dict, List, Protocol

from box.edge import Edge, EdgePathBuilder
from box.geometry import Path, Plane, Line, PathBuilder

from box.transform import Transform, create_transform, mat_reflect_x, mat_reflect_y, mat_shift, mat_rot_90

class FaceConstraintProvider(Protocol):

    def __call__(self, path: Path, face: Face|None = None) -> Path:
        """Append constraints to path of face"""
        ...


class FaceType(enum.Enum):
    BOTTOM_TOP = 1
    FRONT_BACK = 2
    SIDE_LEFT_RIGHT = 3

class FacePathBuilder:
    """Concatenate all paths genreated by the provided PathBuilders"""

    def __init__(self, *path_builder: PathBuilder) -> None:
        self.path_builder: List[Path] = path_builder
    
    def __call__(self) -> Path:
        path: Path = self.path_builder[0]()
        if len(self.path_builder) > 1:
            for p_builder in self.path_builder[1:]:
                _p: Path = p_builder()
                path = path.concat(_p)
        return path


class Face:

    @classmethod
    def full_joint_face(cls, e1: Edge, e2: Edge, name: str, plane: Plane = Plane.XY):

        p1 = EdgePathBuilder(e1)
        p2 = EdgePathBuilder(e2).add_transfrom_mat(mat_shift(dx=e1.length), mat_rot_90)
        p3 = EdgePathBuilder(e1).add_transfrom_mat(mat_shift(dy=e2.length), mat_reflect_x).add_path_consumer(lambda x: x.reverse(copy=False))
        p4 = EdgePathBuilder(e2).add_transfrom_mat(mat_rot_90, mat_reflect_x).add_path_consumer(lambda x: x.reverse(copy=False))
        face_builder = FacePathBuilder(p1, p2, p3, p4)
        return cls(face_builder = face_builder, name=name, plane=plane)


    def __init__(self, face_builder: FacePathBuilder, name="Face", plane: Plane = Plane.XY) -> None:
        self.face_builder: FacePathBuilder = face_builder
        # self.edge_1: Edge = edge_1
        # self.edge_2: Edge = edge_2
        # self.thickness: float = thickness
        self.name = name
        self.constraint_providers: List[FaceConstraintProvider] = []
        self.post_path_transforms: List[Transform] = []
        self.plane: Plane = plane

    def apply_constrains(self, path: Path) -> Path:

        for provider in self.constraint_providers:
            path = provider(path=path, face=self)
        
        return path

    def build_path(self) -> Path:

        # base_path_e1: Path = self.edge_1.make_path() # zero, in x-direction
        # base_path_e2: Path = self.edge_2.make_path() # zero, in x-dircetion 


        # rot90_shiftx_e1 = create_transform(mat_shift(dx=self.edge_1.length), mat_rot_90)
        # reflectx_shifty_e2 = create_transform(mat_shift(dy=self.edge_2.length), mat_reflect_x )
        # reflectx_rot90 = create_transform(mat_rot_90, mat_reflect_x) 

        # paths = [
        #     base_path_e2.transform(rot90_shiftx_e1),
        #     base_path_e1.transform(reflectx_shifty_e2).reverse(copy=False),
        #     base_path_e2.transform(reflectx_rot90).reverse(copy=False)
        #     ]
        
        # path = base_path_e1
        # for p in paths:
        #     path = path.concat(p)
        path: Path = self.face_builder()

        for t in self.post_path_transforms:
            path = path.transform(t)

        path = self.apply_constrains(path)

        return path