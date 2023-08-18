from __future__ import annotations
from typing import Any, List
import numpy as np


from dataclasses import dataclass, field

from box.dimension import Dim
from box.constrains import Constraint, Transform
from box.geometry import Edge, Face, Line, Orientation, Path, Plane
from box.transform import reflect_on_x_axis

class ColiniarConstraint:

    def __init__(self, lines: List[Line]) -> None:
        self.lines: List[Line] = lines

    def apply_transform(self, transform: Transform) -> Constraint:
        new_lines = [l.transform(transform) for l in self.lines]
        return ColiniarConstraint(new_lines)

    def get_name(self) -> str:
        return Constraint.Coliniear

    def process(self, transform_F) -> Any:
        return transform_F(self.lines)

class HorizontalConstrain:

    def __init__(self, *lines) -> None:
        self.lines: List[Line] = lines
    
    def apply_transform(self, transform: Transform) -> Constraint:
        new_lines = [l.transform(transform) for l in self.lines]
        return HorizontalConstrain(*new_lines)

    def get_name(self) -> str:
        return Constraint.Horizontal
    
    def process(self, transform_F) -> Any:
        return transform_F(self.lines)

class VerticalConstrain:

    def __init__(self, *lines) -> None:
        self.lines: List[Line] = lines

    def apply_transform(self, transform: Transform) -> Constraint:
        new_lines = [l.transform(transform) for l in self.lines]
        return VerticalConstrain(*new_lines)

    def get_name(self) -> str:
        return Constraint.Vertical
    
    def process(self, transform_F) -> Any:
        return transform_F(self.lines)

class PerpendicularConstraint:
    def __init__(self, l1: Line, l2: Line) -> None:
        self.l1: Line = l1
        self.l2: Line = l2

    def apply_transform(self, transform: Transform) -> Constraint:
        return PerpendicularConstraint(
            self.l1.transform(transform), 
            self.l2.transform(transform))
    
    def get_name(self) -> str:
        return  Constraint.Perpendicular
    
    def process(self, transform_f) -> Any:
        return transform_f(self.l1, self.l2)
        

class EqualConstraint:

    def __init__(self, base_line: Line = None, lines: List[Line]=None) -> None:
        self.base_line: Line = base_line
        self.lines: List[Line] = [] if lines is None else lines
    
    def apply_transform(self, transform: Transform) -> Constraint:
        return EqualConstraint(
            self.base_line.transform(transform), 
            [l.transform(transform) for l in self.lines])
    
    def get_name(self) -> str:
        return  Constraint.EqualConstraint
    
    def process(self, transform_f) -> Any:
        return transform_f(self.base_line, self.lines)
    
    def __call__(self, line: Line) -> Line:
        """collect lines which are equal, while taking the frist as the base line"""
        if self.base_line is None:
            self.base_line = line
        else:
            if self.base_line.dim.abs_equal(line.dim):
                line.dim = None
                self.lines.append(line)
            else:
                raise ValueError("Lines are not equal.")
        
        return line


@dataclass
class SimpleBox: 
    
    length: Edge
    width: Edge 
    height: Edge 
    faces: List[Face]
    thickness: Dim = field(default=Dim(3.0, "thickness", "mm"))
    kerf: Dim = field(default=Dim(0.1, "kerf", "mm"))

    _paths: List[Path] = field(init=False, default=list)

    @classmethod
    def eqaul_from_finger_count(cls, length_finger_count: Dim, width_finger_count: Dim, height_finger_count: Dim, finger_dim: float, thickness: Dim):
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
        
        faces = [
            Face(length.as_positive(), width.as_positive(), thickness, build_bottom_top, name="bottom_top", plane=Plane.XY),
            Face(length.as_negative(), height.as_negative(), thickness, build_front_back, name="front_back", plane=Plane.XZ),
            Face(height.as_negative(), width.as_negative(), thickness, build_sides_left_right, name="sides_left_right", plane=Plane.YZ)
        ]
        
        return cls(
            length=length,
            width=width,
            height=height,
            faces=faces,
            thickness=thickness,
        )
    
    def build_face(self, face: Face) -> Path:
        p: Path = face.build_path()
        return p


def build_bottom_top(
        length: Edge,
        width: Edge,
        thickness: Dim) -> Path:
    
    path: Path = Path().add_point(0., 0.)
   
    eq_finger_h = EqualConstraint()
    eq_notch_h = EqualConstraint()
    eq_thickness_v = EqualConstraint()    

    for _ in range(length.finger_count.int_value -1):
        path.h_dim(length.finger).consume_last(eq_finger_h)
        path.v_dim(-thickness).consume_last(eq_thickness_v)
        path.h_dim(length.notch).consume_last(eq_notch_h)
        path.v_dim(thickness).consume_last(eq_thickness_v)
    path.h_dim(length.finger).consume_last(eq_finger_h)

    eq_finger_v = EqualConstraint()
    eq_notch_v = EqualConstraint()
    eq_thickness_h = EqualConstraint()    


    for _ in range(width.finger_count.int_value -1):
        path.v_dim(-width.finger).consume_last(eq_finger_v)
        path.h_dim(-thickness).consume_last(eq_thickness_h)
        path.v_dim(-width.notch).consume_last(eq_notch_v)
        path.h_dim(thickness).consume_last(eq_thickness_h)
    path.v_dim(-width.finger).consume_last(eq_finger_v)


    for _ in range(length.finger_count.int_value -1):
        path.h_dim(-length.finger).consume_last(eq_finger_h)
        path.v_dim(thickness).consume_last(eq_thickness_v)
        path.h_dim(-length.notch).consume_last(eq_notch_h)
        path.v_dim(-thickness).consume_last(eq_thickness_v)
    path.h(-length.finger) # not constrained


    for _ in range(width.finger_count.int_value -1):
        path.v_dim(width.finger).consume_last(eq_finger_v)
        path.h_dim(thickness).consume_last(eq_thickness_h)
        path.v_dim(width.notch).consume_last(eq_notch_v)
        path.h_dim(-thickness).consume_last(eq_thickness_h)
    path.v(width.finger) # not constrained

    path.appen_constraint(eq_finger_h, eq_notch_h, eq_thickness_h)
    path.appen_constraint(eq_finger_v, eq_notch_v, eq_thickness_v)
    path.appen_constraint(HorizontalConstrain(path.lines[0]))

    # append perpendicluar constraints for all lines.
    for i in range(len(path.lines)-1):
        p1 = path.lines[i]
        p2 = path.lines[i+1]
        path.appen_constraint(PerpendicularConstraint(p1, p2))

    return path



def build_front_back(
        length: Edge,
        height: Edge,
        thickness: Dim
) -> Path:
    
    # path: Path = Path().add_point(thickness.value, 0.)

    path: Path = Path().add_point(0., 0.)
    path.h_dim(thickness).as_construciont_line()

    eq_thickness_v = EqualConstraint()
    eq_thickness_h = EqualConstraint()

    eq_f_v = EqualConstraint()
    eq_f_h = EqualConstraint()
    eq_f_small_v = EqualConstraint()

    eq_n_h = EqualConstraint()
    eq_n_v = EqualConstraint()
    eq_n_small_h = EqualConstraint()

    for i in range(length.finger_count.int_value):
        if i == 0:
            path.h_dim(length.notch - thickness).consume_last(eq_n_small_h)
        else:
            path.h_dim(length.notch).consume_last(eq_n_h)
        path.v_dim(thickness).consume_last(eq_thickness_v)
        path.h_dim(length.finger).consume_last(eq_f_h)
        path.v_dim(-thickness).consume_last(eq_thickness_v)
    path.h_dim(length.notch - thickness).consume_last(eq_n_small_h)

    for i in range(height.finger_count.int_value):
        if i == 0:
            path.v_dim(-(height.finger-thickness)).consume_last(eq_f_small_v)
        else:
            path.v_dim(-(height.finger)).consume_last(eq_f_v)
        path.h_dim(thickness).consume_last(eq_thickness_h)
        path.v_dim(-height.notch).consume_last(eq_n_v)
        path.h_dim(-thickness).consume_last(eq_thickness_h)
    path.v_dim(-(height.finger-thickness)).consume_last(eq_f_small_v)

    for i in range(length.finger_count.int_value):
        if i == 0:
            path.h_dim(-(length.notch-thickness)).consume_last(eq_n_small_h)
        else:
            path.h_dim(-length.notch).consume_last(eq_n_h)
        path.v_dim(-thickness).consume_last(eq_thickness_v)
        path.h_dim(-length.finger).consume_last(eq_f_h)
        path.v_dim(thickness).consume_last(eq_thickness_v)
    path.h(-(length.notch-thickness)) # not constrained

    for i in range(height.finger_count.int_value):
        if i == 0:
            path.v_dim(height.finger-thickness).consume_last(eq_f_small_v)
        else:
            path.v_dim(height.finger).consume_last(eq_f_v)
        path.h_dim(-thickness).consume_last(eq_thickness_h)
        path.v_dim(height.notch).consume_last(eq_n_v)
        path.h_dim(thickness).consume_last(eq_thickness_h)
    path.v(height.finger-thickness) # not constrained

    # append equal constraints (clears unnecessary dim constrains)
    path.appen_constraint(eq_thickness_h, eq_thickness_v, eq_f_h, eq_f_v, eq_f_small_v)
    path.appen_constraint(eq_n_h, eq_n_v, eq_n_small_h)
    path.appen_constraint(HorizontalConstrain(path.lines[0], path.lines[1]))

    # append perpendicluar constraints for all lines.
    # skip first construction line...
    for i in range(len(path.lines)-2):
        p1 = path.lines[i+1]
        p2 = path.lines[i+2]
        path.appen_constraint(PerpendicularConstraint(p1, p2))
    
    # fix for fusion 360 api fuckup with sktech coordinate systems
    path = path.transform(reflect_on_x_axis)

    return path


def build_sides_left_right(
        height: Edge,
        width: Edge,
        thickness: float = 3.0
):
    path: Path = Path().add_point(thickness.value, 0.)

    eq_t_h = EqualConstraint()
    eq_t_v = EqualConstraint()
    
    eq_f_small_h = EqualConstraint()
    eq_f_v = EqualConstraint()
    eq_f_h = EqualConstraint()

    eq_n_h = EqualConstraint()
    eq_n_v = EqualConstraint()



    for i in range(height.finger_count.int_value-1):
        if i == 0:
            path.h_dim(height.finger-thickness).consume_last(eq_f_small_h)
        else:
            path.h_dim(height.finger).consume_last(eq_f_h)
        path.v_dim(-thickness).consume_last(eq_t_v)
        path.h_dim(height.notch).consume_last(eq_n_h)
        path.v_dim(thickness).consume_last(eq_t_v)
    path.h_dim(height.finger-thickness).consume_last(eq_f_small_h)

    for _ in range(width.finger_count.int_value):
        path.v_dim(-width.notch).consume_last(eq_n_v)
        path.h_dim(thickness).consume_last(eq_t_h)
        path.v_dim(-width.finger).consume_last(eq_f_v)
        path.h_dim(-thickness).consume_last(eq_t_h)
    path.v_dim(-width.notch).consume_last(eq_n_v)

    for i in range(height.finger_count.int_value-1):
        if i == 0:
            path.h_dim(-(height.finger-thickness)).consume_last(eq_f_small_h)
        else:
            path.h_dim(-height.finger).consume_last(eq_f_h)
        path.v_dim(thickness).consume_last(eq_t_v)
        path.h_dim(-height.notch).consume_last(eq_n_h)
        path.v_dim(-thickness).consume_last(eq_t_v)
    path.h(-(height.finger-thickness)) # not constrained

    for _ in range(width.finger_count.int_value):
        path.v_dim(width.notch).consume_last(eq_n_v)
        path.h_dim(-thickness).consume_last(eq_t_h)
        path.v_dim(width.finger).consume_last(eq_f_v)
        path.h_dim(thickness).consume_last(eq_t_h)
    path.v(width.notch) # not constrained

    path.appen_constraint(eq_t_h, eq_t_v)
    path.appen_constraint(eq_f_small_h, eq_f_v, eq_f_h)
    path.appen_constraint(eq_n_v, eq_n_h)
    path.appen_constraint(HorizontalConstrain(path.lines[0]))

    # append perpendicluar constraints for all lines.
    for i in range(len(path.lines)-1):
        p1 = path.lines[i]
        p2 = path.lines[i+1]
        path.appen_constraint(PerpendicularConstraint(p1, p2))
    
    return path


if __name__ == "__main__":
    pass