from __future__ import annotations
import enum
from typing import Any, Protocol, List, Tuple
from abc import ABC

from box.dimension import Dim
from box.geometry import Path, PathConsumer, PathBuilder, PathConsumerByTransfrom
from box.transform import Transform, create_transform

class EdgePathBuilder:

    def __init__(self, edge: Edge) -> None:
        self.edge: Edge = edge
        self.path_consumer: List[PathConsumer] = []
        self.path_transforms: List[PathConsumerByTransfrom] = []
        self.callback_order: List[Tuple] = []
        self.concat_with_connecting_line: bool = False
    
    @property
    def length(self) -> float:
        return self.edge.length
    
    def add_path_consumer(self, consumer: PathConsumer) -> EdgePathBuilder:
        """append path consumer."""
        self.path_consumer.append(consumer)
        self.callback_order.append((self.path_consumer, len(self.path_consumer)-1))
        return self
    
    def reverse_path(self) -> EdgePathBuilder:
        return self.add_path_consumer(lambda x: x.reverse(copy=False))
    
    def allow_concat(self) -> EdgePathBuilder:
        self.concat_with_connecting_line = True 
        return self
        

    def add_transfrom_mat(self, *mat) -> EdgePathBuilder:
        return self.add_transfrom(create_transform(*mat))

    def add_transfrom(self, transfrom: Transform) -> EdgePathBuilder:
        """append transforms."""
        self.path_transforms.append(PathConsumerByTransfrom(transfrom))
        self.callback_order.append((self.path_transforms, len(self.path_transforms)-1))
        return self

    # path builder
    def __call__(self) -> Path:
        """create path"""
        path = self.edge.make_path()
        for calback, index in  self.callback_order:
            path = calback[index](path)
        return path


class EdgeTyp(enum.Enum):
    LENGTH_POSTIVE = 1      # Finger, full
    LENGTH_NEGATIVE = -1    # Notch, minus thickness
    WIDTH_POSTIVE = 2       # Finger, full
    WIDTH_NEGATIVE = -2     # Notch, full
    HEIGHT_POSITIVE = 3     # Finger, minus thickness
    HEIGHT_NEGATIVE = -3    # Notch, minus thickness
    OTHER_POSITIVE = 4 
    OTHER_NEGATIVE = -4

    def is_positive(self):
        return self.value > 0
    def full_length(self):
        return self.value in [1, 2, -2]



class Edge(ABC):

    def __init__(self) -> None:
        super().__init__()
        self.path_pre_processors : List[PathConsumer] = []
        self.path_post_processors : List[PathConsumer] = []
     
    def make_path(self) -> Path:
        p = Path.zero()
        for processor in self.path_pre_processors:
            p = processor(p)
        p = self.build_path(p)
        for processor in self.path_post_processors:
            p = processor(p)
        return p
    
    def build_path(self, path: Path) -> Path:
        ...
    
    def length(self) -> float:
        """Length of edge"""
        ...
    

# todo: simple edge that only contains staight lines?

class StraigtLineEdge(Edge):

    def __init__(self, length: Dim|float) -> None:
        super().__init__()
        self._length: Dim|float = length
    
    def length(self) -> float:
        if isinstance(self._length, Dim):
            return self._length.value
        else:
            return self._length

    def build_path(self, path: Path) -> Path:
        if isinstance(self._length, Dim):
            return path.h_dim(self._length)
        else:
            return path.h(self._length)

class StackableBottomTopEdge(Edge):
    def __init__(self, stand_l: Dim, stand_h: Dim, stand_notch: Dim) -> None:
        super().__init__()
        self.stand_l: Dim = stand_l
        self.stand_h: Dim = stand_h
        self.stand_notch: Dim = stand_notch
    
    def length(self) -> float:
        return self.stand_h.value*2 + self.stand_notch.value
    
    def build_path(self, path: Path) -> Path:
        val = self.stand_h.value/3

        path.h_dim(self.stand_l)
        path.v(val)
        path.line_to_rel(val, val)
        path.h_dim(self.stand_notch - 4*val)
        path.line_to_rel(val, -val)
        path.v(-val)
        path.h_dim(self.stand_l)
        return path

# todo: one kind of edge that build finger joints. 
class FingerJointEdge(Edge): 

    def __init__(
            self, 
            finger: Dim, 
            finger_count: Dim, 
            notch: Dim, 
            notch_count: Dim, 
            thickness: Dim,
            kerf: Dim|None = None) -> None:
        super().__init__()
        if finger_count.int_value == notch_count.int_value:
            raise ValueError(f"Invalid edge. finger and notch count cannot be the equal. got {finger_count} and {notch_count}")
        if abs(finger_count.int_value - notch_count.int_value) > 1:
            raise ValueError(f"Invalid edge. Finger and notch count must be off by one in either direction.")
        self.finger: Dim = finger
        self.finger_count: int = finger_count
        self.notch: Dim = notch
        self.notch_count: Dim = notch_count     ## todo notch count is dependent on finger count (off by one in either direction!.)
        self.thickness: Dim = thickness
        self.kerf = kerf
        if self.is_positive_edge():
            self.edge_type = EdgeTyp.OTHER_POSITIVE
        else:
            self.edge_type = EdgeTyp.OTHER_NEGATIVE

        self.path_transforms: List[Transform]

    @classmethod
    def as_length(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.LENGTH_POSTIVE
        else:
            ret.edge_type = EdgeTyp.LENGTH_NEGATIVE
        return ret

    @classmethod
    def as_width(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.WIDTH_POSTIVE
        else:
            ret.edge_type = EdgeTyp.WIDTH_NEGATIVE
        return ret

    @classmethod
    def as_height(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.HEIGHT_POSITIVE
        else:
            ret.edge_type = EdgeTyp.HEIGHT_NEGATIVE
        return ret

    def is_positive_edge(self):
        """An edge is postive if the number of fingers is greater than the number notches."""
        return self.finger_count > self.notch_count

    def as_positive(self) -> FingerJointEdge:
        if self.is_positive_edge():
            return self
        else:
            return self.switch_type()

    def as_negative(self) -> FingerJointEdge:
        if self.is_positive_edge():
            return self.switch_type()
        else:
            return self


    def switch_type(self) -> FingerJointEdge:
        e =  FingerJointEdge(
            finger=self.notch,
            finger_count=self.notch_count,
            notch=self.finger,
            notch_count=self.finger_count,
            thickness=self.thickness,
            kerf=self.kerf
            )
        e.edge_type = EdgeTyp(-1*(self.edge_type.value))
        return e

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FingerJointEdge):
            return self.edge_type == other.edge_type and \
                self.finger == other.finger and \
                self.finger_count == other.finger_count and \
                self.notch == other.notch and \
                self.notch_count == other.notch_count and \
                self.thickness == other.thickness and \
                self.kerf == other.kerf
        return False

    @property
    def length(self) -> float:
        """Outside measurement of edge."""
        if self.is_positive_edge():
            #finger-notch-finger...
            val = 2*self.get_finger(first_last=True).value + (self.finger_count.int_value -2)*self.get_finger(first_last=False).value + self.notch_count.int_value*self.get_notch(first_last=False).value
        else:
            #notch-finger-notch...
            val = 2*self.get_notch(first_last=True).value + (self.notch_count.int_value -2)*self.get_notch(first_last=False).value + self.finger_count.int_value*self.get_finger(first_last=False).value

        return val
    
    def rep_count(self) -> int:
        """Number of path squences to draw"""
        if self.is_positive_edge():
            return self.finger_count.int_value -1
        else:
            return self.finger_count.int_value
    
    def get_finger(self, first_last:bool) -> Dim:
        if self.is_positive_edge() or self.kerf is None: 
            # positive edge does not apply kerf correction. If negative edge but kerf is not set apply same rules 
            if first_last and not self.edge_type.full_length():
                ret = self.finger - self.thickness
            else:
                ret = self.finger
        else:
            # edge is negative and kerf is set. All fingers in a negative edge are the same, thus no discrimination with first_last needed.
            ret = self.finger - self.kerf

        return ret

    def get_notch(self, first_last: bool) -> Dim:
        if self.is_positive_edge() or self.kerf is None:
            # positive edge does not apply kerf correction. If negative edge but kerf is not set apply same rules 
            if first_last and not self.edge_type.full_length():
                ret = self.notch - self.thickness
            else:
                ret = self.notch
        else:
            if first_last:
                if not self.edge_type.full_length():
                    ret = self.notch - self.thickness + self.kerf.div_by(2)
                else:
                    ret = self.notch + self.kerf.div_by(2)
            else:
                ret = self.notch + self.kerf

        return ret

    def build_path(self, path: Path) -> Path:
        for i in range(self.rep_count()):
            if self.is_positive_edge(): # postive edge: finger->notch->finger
                path.h_dim(self.get_finger(i==0))
                path.v_dim(self.thickness)
                path.h_dim(self.get_notch(first_last=False)) # not the first element in path
                path.v_dim(-self.thickness)
            else: # negative edge: finger->notch->finger
                path.h_dim(self.get_notch(i==0))
                path.v_dim(-self.thickness)
                path.h_dim(self.get_finger(first_last=False)) # not the first element in path
                path.v_dim(self.thickness)
        if self.is_positive_edge():
            path.h_dim(self.get_finger(first_last=True))
        else:
            path.h_dim(self.get_notch(first_last=True))
        return path


class FingerJointHolesEdge(FingerJointEdge):

    def __init__(self, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim | None = None) -> None:
        super().__init__(finger, finger_count, notch, notch_count, thickness, kerf)

    def switch_type(self) -> FingerJointHolesEdge:
        e =  FingerJointHolesEdge(
            finger=self.notch,
            finger_count=self.notch_count,
            notch=self.finger,
            notch_count=self.finger_count,
            thickness=self.thickness,
            kerf=self.kerf
            )
        e.edge_type = EdgeTyp(-1*(self.edge_type.value))
        return e
    
    def _hole(self, path: Path) -> Path:
        """Create hole for finger at current position."""
        path.h_dim(self.get_notch(False))
        path.v_dim(self.thickness)
        path.h_dim(-self.get_notch(False))
        path.v_dim(-self.thickness)
        path.h_dim(self.get_notch(False)).as_construciont_line()
        return path
    
    def build_path(self, path: Path) -> Path:
        path: Path = Path.zero()

        for i in range(self.rep_count()):
            if self.is_positive_edge(): # postive edge: finger->notch->finger
                path.h_dim(self.get_finger(i==0)).as_construciont_line()
                path = self._hole(path) # hole
            else: # negative edge: finger->notch->finger
                path = self._hole(path)
                path.h_dim(self.get_finger(first_last=False)).as_construciont_line()
        if self.is_positive_edge():
            path.h_dim(self.get_finger(first_last=True)).as_construciont_line()
        else:
            path = self._hole(path)
        return path

def stackable_side_edge(edge: FingerJointEdge, stand_h: Dim) -> FingerJointEdge:

    def append_start(path: Path) -> Path:
        path.h_dim(stand_h + edge.thickness)
        return path
    edge.path_pre_processors.insert(0, append_start)
    return edge
