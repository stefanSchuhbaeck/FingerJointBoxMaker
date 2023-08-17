from __future__ import annotations
import enum
from typing import Any, List, Tuple, Callable, Protocol


import numpy as np

from box.dimension import Dim
from box.constrains import Constraint

class Plane(enum.Enum):
    XY = 1
    XZ = 2
    YZ = 3


class Orientation(enum.Enum):
    Horizontal = 1
    Vertical = 2
    Other = 3

class LastLineConsumer(Protocol):

    def __call__(self, line: Line) -> Line:
        ...


class Line:

    def __init__(self, p1, p2, move_to: bool = False) -> None:
        self.line = np.array([p1, p2])
        if self.line.shape != (2,2):
            raise ValueError("expecetd (2,2) shape")
        if (p1 == p2).all():
            raise ValueError("line with length 0 not allowed.")

        self.dim: Dim = None
        self.move_to: bool = False

        if self.is_horizontal():
            self.orientation = Orientation.Horizontal
            self.level = self.start[1]
        elif self.is_vertical():
            self.orientation = Orientation.Vertical
            self.level = self.start[0]
        else:
            self.orientation = Orientation.Other
            self.level = np.nan

    def __str__(self) -> str:
        return f"<Line: [{self.start}, {self.end}] {self.orientation} dim: {self.length()}>"

    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def is_construction(self)-> bool:
        return self.move_to
    
    @property
    def is_real(self) -> bool:
        return not self.is_construction
    
    def set_as_construction_line(self) -> Line:
        self.move_to = True
        return self

    def points_as(self, point_creator):
        return point_creator(self.start), point_creator(self.end)

    def is_horizontal(self):
        return  self.end[1] == self.start[1]

    def is_vertical(self):
        return  self.end[0] == self.start[0]

    def length(self) -> float:
        return np.linalg.norm(self.line)

    def hash_key(self) -> tuple:
        return tuple(self.line.reshape(-1))

    @property
    def start(self):
        return self.line[0]

    @property
    def end(self):
        return self.line[1]


class EdgeTyp(enum.Enum):
    LENGTH_POSTIVE = 1
    LENGTH_NEGATIVE = -1
    WIDTH_POSTIVE = 2
    WIDTH_NEGATIVE = -2
    HEIGHT_POSITIVE = 3
    HEIGHT_NEGATIVE = -3

    def is_positive(self):
        return self.value > 0


class Edge():

    def __init__(self, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim) -> None:
        super().__init__()
        if finger_count.int_value == notch_count.int_value:
            raise ValueError(f"Invalid edge. finger and notch count cannot be the equal. got {finger_count} and {notch_count}")
        self.edge_type: EdgeTyp = None
        self.finger: Dim = finger
        self.finger_count: int = finger_count
        self.notch: Dim = notch
        self.notch_count: Dim = notch_count

    @classmethod
    def as_length(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim) -> None:
        ret = cls(finger, finger_count, notch, notch_count)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.LENGTH_POSTIVE
        else:
            ret.edge_type = EdgeTyp.LENGTH_NEGATIVE
        return ret

    @classmethod
    def as_width(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim) -> None:
        ret = cls(finger, finger_count, notch, notch_count)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.WIDTH_POSTIVE
        else:
            ret.edge_type = EdgeTyp.WIDTH_NEGATIVE
        return ret

    @classmethod
    def as_height(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim) -> None:
        ret = cls(finger, finger_count, notch, notch_count)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.HEIGHT_POSITIVE
        else:
            ret.edge_type = EdgeTyp.HEIGHT_NEGATIVE
        return ret

    def is_positive_edge(self):
        """An edge is postive if the number of fingers is greater than the number notches."""
        return self.finger_count > self.notch_count

    def as_positive(self) -> Edge:
        if self.is_positive_edge():
            return self
        else:
            return self.switch_type()

    def as_negative(self) -> Edge:
        if self.is_positive_edge():
            return self.switch_type()
        else:
            return self


    def switch_type(self) -> Edge:
        e =  Edge(
            finger=self.notch,
            finger_count=self.notch_count,
            notch=self.finger,
            notch_count=self.finger_count
            )
        e.edge_type = EdgeTyp(-1*(self.edge_type.value))
        return e

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Edge):
            return self.edge_type == other.edge_type and \
                self.finger == other.finger and \
                self.finger_count == other.finger_count and \
                self.notch == other.notch and \
                self.notch_count == other.notch_count
        return False

    @property
    def length(self) -> float:
        """Outside measurement of edge."""
        return self.finger.value * self.finger_count.int_value + self.notch.value * self.notch_count.int_value


class FaceType(enum.Enum):
    BOTTOM_TOP = 1
    FRONT_BACK = 2
    SIDE_LEFT_RIGHT = 3


class Path:

    def __init__(self) -> None:
        self.points: List[np.array] = []
        self.lines: List[Line] = []
        self.constraints: List[Constraint] = []

    def __len__(self) -> int:
        return len(self.points)

    def get_loction(self) -> np.array():
        return  self.points[-1]
    
    def appen_constraint(self, *args):
        for c in args:
            self.constraints.append(c)

    def last_line(self) -> Line:
        return self.lines[-1]
    
    def as_construciont_line(self) -> Path:
        """Will set the last added to the path as a construction line"""
        return self.consume_last(lambda x: x.set_as_construction_line())

    def consume_last(self, func: LastLineConsumer) -> Path:
        line: Line = func(self.last_line())
        self.lines[-1] = line
        return self

    def get_current_level(self, orientation: Orientation) -> float:
        if orientation == Orientation.Horizontal:
            # line from east to west, thus same y
            return self.get_loction()[1]
        elif orientation == Orientation.Vertical:
            # line south to north, thus same x
            return self.get_loction()[0]
        else:
            raise ValueError("Expected horizontal or vertical") 

    @property
    def line_count(self):
        return len(self.lines)

    def is_closed(self) -> bool:
        return len(self) > 1 and all(self.points[0] == self.points[-1])

    def clear(self):
        self.points.clear()

    def _make_line(self, dim: Dim|None=None):
        if len(self.points) < 1:
            raise ValueError("path must contain at least to points to create a line")
        line = Line(self.points[-2], self.points[-1])
        line.dim = dim
        self.lines.append(line)
        return Line

    def add_to_last(self, p: np.array):
        if len(self.points) == 0:
            raise ValueError("Path has no initial point")
        self.points.append(self.points[-1] + p)

    def add_point(self, x, y):
        self.points.append(np.array([x, y]))
        return self

    def _get_vec_dim(self, x, y) -> Tuple[np.array, Dim|None]:
        _dim = None
        if isinstance(x, (int, float)):
            _x = x
        elif isinstance(x, Dim):
            _x = x.value
            _dim = x
        else:
            raise TypeError(f"Expected int, float or Dim got {type(x)}")
        
        if isinstance(y, (int, float)):
            _y = y
        elif isinstance(y, Dim):
            _y = y.value
            if _dim is not None:
                raise RuntimeError("expcetd at most one 'Dim' object. Got 2.")
            _dim = y
        else:
            raise TypeError(f"Expected int, float or Dim got {type(x)}")
    

        return np.array([_x, _y]), _dim

    def h(self, v: float|Dim):
        """horizontal line from last point with length equal to the absolute value of `v` 
        Method takes float or Dim object but does not append the Dim object to the line.
        Use `h_dim` for this.
        """
        p, _ = self._get_vec_dim(v, 0.0)
        self.add_to_last(p)
        self._make_line()
        return self
    
    def h_dim(self, v: Dim):
        """horizontal line from last point with length equal to the absolute value of `v` 
        Method takes Dim object and will `raise` if not provided. The creaed line will 
        receive the `Dim` object for constraints procesing later on. 
        """
        p, dim = self._get_vec_dim(v, 0.0)
        self.add_to_last(p)
        if dim is None:
            raise ValueError("Expcetd a dimension")
        self._make_line(dim)
        return self


    def v(self, v:float|Dim):
        """vertical line from last point with length equal to absolute value of `v`
        Method takes float or Dim object but does not append the Dim object to the line.
        Use `v_dim` for this.
        """
        p, _ = self._get_vec_dim(0., v)
        self.add_to_last(p)
        self._make_line()
        return self

    def v_dim(self, v:Dim):
        """vertical line from last point with length equal to absolute value of `v`
        Method takes Dim object and will `raise` if not provided. The creaed line will 
        receive the `Dim` object for constraints procesing later on. 
        """
        p, dim = self._get_vec_dim(0., v)
        self.add_to_last(p)
        if dim is None:
            raise ValueError("Expcetd a dimension")
        self._make_line(dim)
        return self


    def get_lines_at_level(
            self, 
            level: float, 
            orientation: Orientation, 
            since_line: int = 0, 
            constraint_f: Callable[[List[Line]], Constraint] = None):
        """Retrieve list of lines which are at the `level` based on the set orientation. If orientation 
        is Horizontal, than level corresponds withthe x-value of the line. For vertical the y-value is used.
        If `since_line` is not set all lines are checked for orientaion and level.
        """
        if since_line > self.line_count or since_line < 0:
            raise ValueError(f"since_line must be within interval [0, {self.line_count}), i.e number of lines in path.")
        out = []
        for i in range(since_line, self.line_count):
            line = self.lines[i]
            if line.orientation == orientation and line.level == level:
                out.append(line)
        if constraint_f is not None:
            self.constraints.append(constraint_f(out))
        return out
    



class Face:

    def __init__(self, edge_1: Edge, edge_2: Edge, thickness:float, _path_func, name="Face", plane: Plane = Plane.XY) -> None:
        self.edge_1: Edge = edge_1
        self.edge_2: Edge = edge_2
        self.thickness: float = thickness
        self._path_func  = _path_func
        self.name = name
        self.plane: Plane = plane

    def build_path(self) -> Path:
        return self._path_func(
            self.edge_1,
            self.edge_2,
            self.thickness,
        )


