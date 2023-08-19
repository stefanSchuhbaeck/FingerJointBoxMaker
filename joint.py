from __future__ import annotations
from typing import Dict, List
import numpy as np


from dataclasses import dataclass, field

from box.dimension import Dim, AbsDimHashKey
from box.geometry import Orientation, Path, Plane, Line
from box.transform import reflect_on_x_axis
import box.transform as t
from box.edge import Edge
from box.face import Face
from box.constraints_impl import EqualConstraint, HorizontalConstrain, PerpendicularConstraint


def add_perpendicular_constraints(path: Path, face: Face) -> Path:
    """Make all lines perpendicular to the next."""
    for i in range(len(path.lines)-2):
        p1 = path.lines[i+1]
        p2 = path.lines[i+2]
        path.append_constraint(PerpendicularConstraint(p1, p2))
    return path
 
def replace_dimensions_with_equal_constrains(path: Path, face: Face) -> Path:
    dim_dict: Dict[AbsDimHashKey, List[Line]] = {}
    for l in path.lines:
        if l.is_construction:
            continue
        if l.dim.abs_hash not in dim_dict:
            dim_dict.setdefault(l.dim.abs_hash,  [l])
        else:
            dim_dict[l.dim.abs_hash].append(l)
    
    for _, lines in dim_dict.items():
        path.append_constraint(EqualConstraint.collect(lines))
    return path


@dataclass
class SimpleBox: 
    
    length: Edge
    width: Edge 
    height: Edge 
    bottom_top: Face
    front_back: Face
    left_right: Face
    post_transformations: dict = field(init=False)
    thickness: Dim = field(default=Dim(3.0, "thickness", "mm"))
    kerf: Dim = field(default=Dim(0.1, "kerf", "mm"))

    _paths: List[Path] = field(init=False, default=list)

    @classmethod
    def eqaul_from_finger_count(
            cls, 
            length_finger_count: Dim, 
            width_finger_count: Dim, 
            height_finger_count: Dim, 
            finger_dim: float, 
            thickness: Dim):
        
        length_f_dim: Dim = Dim(value=finger_dim, name="l_finger", unit="mm")
        length_n_dim: Dim = Dim(value=finger_dim, name="l_notch", unit="mm")

        width_f_dim: Dim = Dim(value=finger_dim, name="w_finger", unit="mm")
        width_n_dim: Dim = Dim(value=finger_dim, name="w_notch", unit="mm")

        height_f_dim: Dim = Dim(value=finger_dim, name="h_finger", unit="mm")
        height_n_dim: Dim = Dim(value=finger_dim, name="h_notch", unit="mm")

        length = Edge.as_length(
            finger=length_f_dim, 
            finger_count=length_finger_count,
            notch=length_n_dim,
            notch_count=length_finger_count.new_relative(-1, "length_finger_count - 1"))
        
        width = Edge.as_width(
            finger=width_f_dim, 
            finger_count=width_finger_count,
            notch=width_n_dim,
            notch_count=width_finger_count.new_relative(-1, "width_finger_count - 1"))
        height = Edge.as_height(
            finger=height_f_dim, 
            finger_count=height_finger_count,
            notch=height_n_dim,
            notch_count=height_finger_count.new_relative(-1, "height_finger_count -1 "))

        return cls.from_edges(length, width, height, thickness)               

    @classmethod
    def from_edges(cls, length: Edge, width: Edge, height: Edge, thickness: Dim):
        box =  cls(
            length=length,
            width=width,
            height=height,
            bottom_top=Face(length.as_positive(), width.as_positive(), thickness, name="bottom_top", plane=Plane.XY),
            front_back=Face(length.as_negative(), height.as_negative(), thickness, name="front_back", plane=Plane.XZ),
            left_right= Face(height.as_positive(), width.as_negative(), thickness, name="sides_left_right", plane=Plane.YZ),
            thickness=thickness,
        )
        for f in box.faces:
            f.constraint_providers.append(add_perpendicular_constraints)
            f.constraint_providers.append(replace_dimensions_with_equal_constrains)
        box.left_right.post_path_transforms.append(t.create_transform(t.mat_reflect_y)) # fusion360 fix 
        box.front_back.post_path_transforms.append(t.create_transform(t.mat_shift(dx=thickness.value), t.mat_reflect_x)) # fusion360 fix
        
        return box

    @property
    def faces(self) -> List[Face]:
        return [self.bottom_top, self.front_back, self.left_right]
    
    def build_face(self, face: Face) -> Path:
        p: Path = face.build_path()
        return p
    


if __name__ == "__main__":
    pass