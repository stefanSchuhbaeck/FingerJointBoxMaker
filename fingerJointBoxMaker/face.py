from __future__ import annotations
import enum
from typing import Any, Dict, List, Protocol

from fingerJointBoxMaker.edge import FingerJointEdge, EdgePathBuilder, StraightLineEdge
from fingerJointBoxMaker.geometry import Path, Plane, Line, PathBuilder, PathConsumer

from fingerJointBoxMaker.transform import Transform, create_transform, mat_reflect_x, mat_reflect_y, mat_shift, mat_rot_90

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

    def __init__(self, *path_builder: EdgePathBuilder) -> None:
        self.path_builder: List[EdgePathBuilder] = path_builder
    
    def add(self, edge_path_builder: EdgePathBuilder) -> FacePathBuilder:
        self.path_builder.append(edge_path_builder)
        return self
    
    @property
    def last(self) -> EdgePathBuilder:
        return self.path_builder[-1] 
    
    def left_side_transform(self) -> EdgePathBuilder:
        """shift in x and rotate based on last added edge"""
        prev = self.path_builder[-2]
        curr = self.path_builder[-1]
        curr.add_transfrom_mat(mat_shift(dx=prev.length), mat_rot_90)
        return curr

    def top_side_transfrom(self) -> EdgePathBuilder:
        """refelct on x axis, shift in y and reverse path"""
        prev = self.path_builder[-2]
        curr = self.path_builder[-1]
        curr.add_transfrom_mat(mat_shift(dy=prev.length), mat_reflect_x).reverse_path()
        return curr
    
    def right_side_transfrom(self) -> EdgePathBuilder:
        """roate 90 reflect on x and revese path"""
        prev = self.path_builder[-2]
        curr = self.path_builder[-1]
        curr.add_transfrom_mat(mat_rot_90, mat_reflect_x).reverse_path()
        return curr

    
    def __call__(self) -> Path:
        print("Build Face:")
        path: Path = self.path_builder[0]()
        if len(self.path_builder) > 1:
            for idx, p_builder in enumerate(self.path_builder[1:]):
                print(f"build append path {idx+1}/{len(self.path_builder)}")
                _p: Path = p_builder()
                path = path.concat(_p)
        return path


class Face:

    @classmethod
    def full_joint_face(cls, e1: FingerJointEdge, e2: FingerJointEdge, name: str="Face", plane: Plane = Plane.XY):

        p1 = EdgePathBuilder(e1)
        p2 = EdgePathBuilder(e2).add_transfrom_mat(mat_shift(dx=e1.length), mat_rot_90)
        p3 = EdgePathBuilder(e1).add_transfrom_mat(mat_shift(dy=e2.length), mat_reflect_x).reverse_path()
        p4 = EdgePathBuilder(e2).add_transfrom_mat(mat_rot_90, mat_reflect_x).reverse_path()
        face_builder = FacePathBuilder(p1, p2, p3, p4)
        return cls(face_builder = face_builder, name=name, plane=plane)

    @classmethod
    def straigth_top_face(cls, e1: FingerJointEdge, e2: FingerJointEdge, name: str="Face", plane: Plane = Plane.XY):
        p1 = EdgePathBuilder(e1)
        p2 = EdgePathBuilder(e2).add_transfrom_mat(mat_shift(dx=e1.length), mat_rot_90)
        p3 = EdgePathBuilder(StraightLineEdge(e1.length)).add_transfrom_mat(mat_shift(dy=e2.length), mat_reflect_x).reverse_path()
        p4 = EdgePathBuilder(e2).add_transfrom_mat(mat_rot_90, mat_reflect_x).reverse_path()
        face_builder = FacePathBuilder(p1, p2, p3, p4)
        return cls(face_builder = face_builder, name=name, plane=plane)


    def __init__(self, face_builder: FacePathBuilder, name="Face", plane: Plane = Plane.XY) -> None:
        self.face_builder: FacePathBuilder = face_builder
        # self.edge_1: Edge = edge_1
        # self.edge_2: Edge = edge_2
        # self.thickness: float = thickness
        self.name = name
        self.constraint_providers: List[FaceConstraintProvider] = []
        self.post_path_consumer: List[PathConsumer] = []
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
        print(f"Build path for face '{self.name}'")
        path: Path = self.face_builder()

        for consumer in self.post_path_consumer:
            path = consumer(path)

        path = self.apply_constrains(path)

        return path
