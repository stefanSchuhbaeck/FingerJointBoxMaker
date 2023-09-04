
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List
from fingerJointBoxMaker.constraints_impl import DimenssionConstraint, EqualConstraint, HorizontalConstrain, OriginLockConstraint, PerpendicularConstraint, VerticalConstrain
from fingerJointBoxMaker.dimension import AbsDimHashKey, Dim

from fingerJointBoxMaker.face import Face
from fingerJointBoxMaker.geometry import Line, Path

@dataclass
class Box(ABC):

    def __post_init__(self):
        self.init_constrains()

    @property
    @abstractmethod
    def faces(self) -> List[Face]:
        ...
    

    def init_constrains(self):
        pass
    
    def build_face(self, face: Face) -> Path:
        p: Path = face.build_path()
        return p
    
    def build(self) -> List[Path]:
        return [self.build_face(f) for f in self.faces]


def add_perpendicular_constraints(path: Path, face: Face) -> Path:
    """Make all lines perpendicular to the next."""
    for i in range(len(path.lines)-2):
        p1 = path.lines[i+1]
        p2 = path.lines[i+2]
        path.append_constraint(PerpendicularConstraint(p1, p2))
    return path


def add_equal_constrains_instead_of_dimensions(path: Path, face: Face) -> Path:
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


def add_sktech_offset(path: Path, face: Face,  offset_x: Dim = None, offset_y: Dim = None) -> Path:
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


def add_first_line_h_or_v_constraint(path: Path, face: Face) -> Path:
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


def add_dimension_constraint(path: Path, face: Face) -> Path:
    path.append_constraint(DimenssionConstraint(path))
    return path
    

