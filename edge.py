from __future__ import annotations
import enum
from typing import Protocol

from box.dimension import Dim
from box.geometry import Path


class EdgeTyp(enum.Enum):
    LENGTH_POSTIVE = 1      # Finger, full
    LENGTH_NEGATIVE = -1    # Notch, minus thickness
    WIDTH_POSTIVE = 2       # Finger, full
    WIDTH_NEGATIVE = -2     # Notch, full
    HEIGHT_POSITIVE = 3     # Finger, minus thickness
    HEIGHT_NEGATIVE = -3    # Notch, minus thickness

    def is_positive(self):
        return self.value > 0
    def full_length(self):
        return self.value in [1, 2, -2]

class EdgeFoo(Protocol):
     def make_path(self) -> Path:
        ...

# todo: simple edge that only contains staight lines?

# todo: one kind of edge that build finger joints. 
class Edge(): 

    def __init__(self, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim = Dim(3, "thickness", "mm")) -> None:
        super().__init__()
        if finger_count.int_value == notch_count.int_value:
            raise ValueError(f"Invalid edge. finger and notch count cannot be the equal. got {finger_count} and {notch_count}")
        if abs(finger_count.int_value - notch_count.int_value) > 1:
            raise ValueError(f"Invalid edge. Finger and notch count must be off by one in either direction.")
        self.edge_type: EdgeTyp = None
        self.finger: Dim = finger
        self.finger_count: int = finger_count
        self.notch: Dim = notch
        self.notch_count: Dim = notch_count     ## todo notch count is dependent on finger count (off by one in either direction!.)
        self.thickness: Dim = thickness

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
        val =  self.finger.value * self.finger_count.int_value + self.notch.value * self.notch_count.int_value
        if self.edge_type.full_length():
            return val
        else:
            return val - 2*self.thickness.value
    
    def rep_count(self) -> int:
        """Number of path squences to draw"""
        if self.is_positive_edge():
            return self.finger_count.int_value -1
        else:
            return self.finger_count.int_value

    def make_path(self, thickness: Dim) -> Path:
        path: Path = Path.zero()

        for i in range(self.rep_count()):
            if self.is_positive_edge():
                if i == 0 and not self.edge_type.full_length():
                    path.h_dim(self.finger - thickness)
                else:
                    path.h_dim(self.finger)
                path.v_dim(thickness)
                path.h_dim(self.notch)
                path.v_dim(-thickness)
            else:
                if i == 0 and  not self.edge_type.full_length():
                    path.h_dim(self.notch - thickness)
                else:
                    path.h_dim(self.notch)
                path.v_dim(-thickness)
                path.h_dim(self.finger)
                path.v_dim(thickness)
        if self.is_positive_edge():
            if self.edge_type.full_length():
                path.h_dim(self.finger)
            else:
                path.h_dim(self.finger - thickness)
        else:
            if self.edge_type.full_length():
               path.h_dim(self.notch)
            else:
                path.h_dim(self.notch - thickness)
        return path

