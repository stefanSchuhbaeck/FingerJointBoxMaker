from __future__ import annotations
from functools import partial
from typing import Dict, List
import numpy as np


from dataclasses import dataclass, field

from box.dimension import Dim, AbsDimHashKey
from box.geometry import Orientation, Path, Plane, Line, PathConsumerByTransfrom
from box.transform import reflect_on_x_axis
import box.transform as t
from box.edge import FingerJointEdge
from box.face import Face
from box.constraints_impl import EqualConstraint, UserParamter, DimenssionConstraint, OriginLockConstraint, VerticalConstrain, HorizontalConstrain, PerpendicularConstraint
from box.constrains import Constraint


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
        if l.is_construction or l.dim is None:
            continue
        if l.dim.abs_hash not in dim_dict:
            dim_dict.setdefault(l.dim.abs_hash,  [l])
        else:
            dim_dict[l.dim.abs_hash].append(l)
    
    for _, lines in dim_dict.items():
        path.append_constraint(EqualConstraint.collect(lines))
    return path

def sktech_offset(path: Path, face: Face,  offset_x: Dim = None, offset_y: Dim = None) -> Path:
    if offset_x is None and offset_y is None:
        pass
    else:
        offset = path.get_origin_offset()
        if (offset_x is not None and offset[0] != offset_x) or(offset_y is not None and offset[1] != offset_y):
            raise ValueError(f"Path offset provided does not match with path. offset_x: {offset_x} offset_x: {offset_x} path origin offset: {offset}")

        new_path = Path.zero()
        if offset_x is not None:
            new_path.h_dim(offset_x).as_construciont_line() 
            new_path.append_constraint(HorizontalConstrain(new_path.last_line()))
        if offset_y is not None:
            new_path.v_dim(offset_y).as_construciont_line()
            new_path.append_constraint(VerticalConstrain(new_path.last_line()))
        path = new_path.concat(path)
        
    return path


def add_origin_offset(path: Path, face: Face) -> Path:
    path.append_constraint(OriginLockConstraint(path.lines[0]))
    return path

def first_line_h_or_v(path: Path, face: Face) -> Path:
    for line in path.lines:
        if line.is_construction:
            continue
        else:
            if line.is_horizontal:
                path.append_constraint(HorizontalConstrain(line))
            else:
                path.append_constraint(VerticalConstrain(line))
            break
    return path

def add_dims(path: Path, face: Face) -> Path:
    path.append_constraint(DimenssionConstraint(path))
    return path

@dataclass
class SimpleBox: 
    
    length: FingerJointEdge
    width: FingerJointEdge 
    height: FingerJointEdge 
    bottom_top: Face
    front_back: Face
    left_right: Face
    post_transformations: dict = field(init=False)
    thickness: Dim = field(default=Dim(3.0, "thickness", "mm"))
    kerf: Dim = field(default=Dim(0.1, "kerf", "mm"))

    constraints :List[Constraint] = field(default_factory=list)

    _paths: List[Path] = field(init=False, default=list)

    @classmethod
    def eqaul_from_finger_count(
            cls, 
            length_finger_count: Dim, 
            width_finger_count: Dim, 
            height_finger_count: Dim, 
            finger_dim: float, 
            thickness: Dim,
            kerf: Dim):
        
        length_f_dim: Dim = Dim(value=finger_dim, name="l_finger", unit="mm")
        length_n_dim: Dim = Dim(value=finger_dim, name="l_notch", unit="mm")

        width_f_dim: Dim = Dim(value=finger_dim, name="w_finger", unit="mm")
        width_n_dim: Dim = Dim(value=finger_dim, name="w_notch", unit="mm")

        height_f_dim: Dim = Dim(value=finger_dim, name="h_finger", unit="mm")
        height_n_dim: Dim = Dim(value=finger_dim, name="h_notch", unit="mm")

        user_para = [
            UserParamter(length_f_dim),
            UserParamter(length_n_dim),
            UserParamter(width_f_dim),
            UserParamter(width_n_dim),
            UserParamter(height_f_dim),
            UserParamter(height_n_dim),
            UserParamter(thickness)
        ]
        if kerf is not None:
            user_para.append(kerf)

        length = FingerJointEdge.as_length(
            finger=length_f_dim, 
            finger_count=length_finger_count,
            notch=length_n_dim,
            notch_count=length_finger_count.new_relative(-1, "length_finger_count - 1"),
            thickness=thickness,
            kerf=kerf)
        
        width = FingerJointEdge.as_width(
            finger=width_f_dim, 
            finger_count=width_finger_count,
            notch=width_n_dim,
            notch_count=width_finger_count.new_relative(-1, "width_finger_count - 1"),
            thickness=thickness,
            kerf=kerf)
        
        height = FingerJointEdge.as_height(
            finger=height_f_dim, 
            finger_count=height_finger_count,
            notch=height_n_dim,
            notch_count=height_finger_count.new_relative(-1, "height_finger_count -1 "),
            thickness=thickness,
            kerf=kerf)

        return cls.from_edges(length, width, height, thickness, kerf, user_para=user_para)               

    @classmethod
    def from_edges(
        cls, 
        length: FingerJointEdge, 
        width: FingerJointEdge, 
        height: FingerJointEdge, 
        thickness: Dim, 
        kerf:Dim,
        user_para: List[Constraint] = None
        ):
        box =  cls(
            length=length,
            width=width,
            height=height,
            bottom_top=Face.full_joint_face(length.as_positive(), width.as_positive(), name="bottom_top", plane=Plane.XY),
            front_back=Face.straigth_top_face(length.as_negative(), height.as_negative(), name="front_back", plane=Plane.XZ),
            left_right= Face.straigth_top_face(width.as_negative(), height.as_positive(), name="sides_left_right", plane=Plane.YZ),
            thickness=thickness,
            kerf=kerf
        )
        if user_para is not None:
            box.constraints = user_para
            
        # set constraint order
        for f in box.faces:
            f.constraint_providers.append(add_perpendicular_constraints)
            if f.name == box.front_back.name:
                f.constraint_providers.append(partial(sktech_offset, offset_x=thickness))
            else:
                f.constraint_providers.append(sktech_offset)

            f.constraint_providers.append(replace_dimensions_with_equal_constrains)
            f.constraint_providers.append(add_dims)
            f.constraint_providers.append(add_origin_offset)
            f.constraint_providers.append(first_line_h_or_v)

        
        # refelct transformation for fusion360 cooridnate system fix 
        # box.left_right.post_path_transforms.append(t.create_transform(t.mat_reflect_y))
        box.left_right.post_path_consumer.append(PathConsumerByTransfrom.from_mat(t.mat_rot_90))
        box.left_right.post_path_consumer.append(lambda x: x.reverse()) # reverse path 
        # refelct transformation for fusion360 cooridnate system fix (offset to alline joints)
        box.front_back.post_path_consumer.append(PathConsumerByTransfrom.from_mat(t.mat_shift(dx=thickness.value), t.mat_reflect_x)) # fusion360 fix
        
        return box

    @property
    def faces(self) -> List[Face]:
        return [self.bottom_top, self.front_back, self.left_right]
    
    def build_face(self, face: Face) -> Path:
        p: Path = face.build_path()
        return p
    


if __name__ == "__main__":
    pass