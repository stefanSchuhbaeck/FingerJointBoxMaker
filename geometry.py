from __future__ import annotations
import enum
from typing import Any, List, Tuple, Callable, Protocol
import copy

from numpy.typing import NDArray
import numpy as np

from box.dimension import Dim
from box.constrains import Constraint, Transform

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
            raise ValueError(f"expecetd (2,2) shape got {self.line.shape}")
        if (p1 == p2).all():
            raise ValueError("line with length 0 not allowed.")

        self.dim: Dim = None
        self.move_to: bool = move_to

        if self.is_horizontal():
            self.orientation = Orientation.Horizontal
            self.level = self.start[1]
        elif self.is_vertical():
            self.orientation = Orientation.Vertical
            self.level = self.start[0]
        else:
            self.orientation = Orientation.Other
            self.level = np.nan
    
    def reverse(self, copy = True) -> Line:
        if copy:
            l = Line(self.end, self.start)
            l.dim = self.dim
            l.move_to = self.move_to
            return l
        else:
            self.line = self.line[::-1]
            return self

    def transform(self, transform: Transform) -> Line:
        line = transform(points=self.line)
        new_line = Line(line[0], line[1], self.move_to)
        new_line.dim = self.dim
        return new_line        

    def __str__(self) -> str:
        _dim = " " if self.dim is None else "*"
        if self.is_construction:
            return f"<Line: [{self.start}, {self.end}]c {self.orientation} dim[{_dim}]: {self.length()}>"
        else:
            return f"<Line: [{self.start}, {self.end}]  {self.orientation} dim[{_dim}]: {self.length()}>"


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
        return np.linalg.norm(self.end - self.start)

    def hash_key(self) -> tuple:
        return tuple(self.line.reshape(-1))

    @property
    def start(self):
        return self.line[0]

    @property
    def end(self):
        return self.line[1]

class PathConsumer(Protocol):

    def __call__(self, path: Path) -> Path:
        """Consume path object and apply changes."""
        ...

class PathBuilder(Protocol):

    def __call__(self) -> Path:
        """Produce a path object of some sort"""
        ...

class PathConsumerByTransfrom():

    def __init__(self, transfrom: Transform) -> None:
        self.transfrom = transfrom

    def __call__(self, path: Path) -> Path:
        return path.transform(self.transfrom)


class Path:

    def __init__(self) -> None:
        self.points: np.array = np.array([[]])
        self.lines: List[Line] = []
        self.constraints: List[Constraint] = []
    
    @classmethod
    def zero(cls):
        p = cls().add_point(0., 0.)
        return p

    def copy(self) -> Path:
        return copy.deepcopy(self)

    def __len__(self) -> int:
        return len(self.points)
    
    def get_origin_offset(self) -> NDArray:
        return self.points[0] - np.array([0., 0.])
    
    def transform(self, t: Transform) -> Path:
        """Create copy of path with transform applied to `points`, `lines` and `constrains` (if the contain lines)"""
      
        points = t(points=np.array(self.points))
        lines = [l.transform(t) for l in self.lines]
        constraints = [c.apply_transform(t) for c in self.constraints]
        new_path = Path()
        new_path.points = points
        new_path.lines = lines
        new_path.constraints = constraints
        return  new_path

    def homogenous_poins(self) -> NDArray:
        return np.append(self.points.T, np.ones(self.points.T)).reshape((3, -1))


    def get_loction(self) -> NDArray:
        return  self.points[-1]
    
    def append_constraint(self, *args):
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

    def close_path(self) -> Path:
        if not self.is_closed():
            self.line_to(self.points[0])
        return self

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
        self.points = np.append(self.points, [self.points[-1] + p], axis=0)
        # self.points.append(self.points[-1] + p)

    def add_point(self, x, y):
        if self.points.shape == (1, 0):
            self.points = np.array([[x, y]])
        else:
            self.points = np.append(self.points, [[x, y]], axis=0)
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

    def line_to(self, *args):
        if len(args) == 2:
            p, _ = self._get_vec_dim(args[0], args[1])
        elif len(args) == 1 and isinstance(args[0], np.ndarray):
            p = args[0]
        else:
            ValueError()

        self.add_point(p[0], p[1])
        self._make_line()
        return self

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
    
    
    def remove_last_line(self) -> Path:
        l = self.lines[-1]
        del self.lines[-1]
        self.points = np.delete(self.points, -1, axis=0)
        return self

    def reverse(self, copy: bool = True) -> Path:
        if copy:
            points = self.points[::-1]
            lines = [l.reverse() for l in self.lines[::-1]]
            constrains = self.constraints[::-1]
            p = Path()
            p.points = points
            p.lines = lines
            p.constraints = constrains
            return p 
        else:
            self.points = self.points[::-1]
            self.lines = [l.reverse(copy=False) for l in self.lines[::-1]]
            self.constraints = self.constraints[::-1]
            return self
    
    def concat(self, path: Path, create_connecting_line: bool = False) -> Path:
        start_end_equal = all(self.points[-1] == path.points[0])

        if not create_connecting_line and not start_end_equal:
            raise ValueError("Paths do not have matching end-start points and create_connecting_line is false")

        p1: Path = self.copy()
        p2: Path = path.copy()
        if not start_end_equal:
            p1.line_to(p2.points[0])

        # path p1 and p2 have now an equal start/end  (reuse copy p1)
        p1.points = np.append(p1.points, p2.points[1:], axis=0)
        p1.lines  = [*p1.lines, *p2.lines]
        p1.constraints = [*p1.constraints, *p2.constraints]
        return p1 







