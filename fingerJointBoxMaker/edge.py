from __future__ import annotations
import enum
from typing import Any, Protocol, List, Tuple
from abc import ABC

from fingerJointBoxMaker.dimension import Dim
from fingerJointBoxMaker.geometry import Path, PathConsumer, PathBuilder, PathConsumerByTransfrom
from fingerJointBoxMaker.transform import Transform, create_transform
import logging

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
        

    def add_transform_mat(self, *mat) -> EdgePathBuilder:
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
    I_POSITIVE = 1      # Finger, full (old name length)
    I_NEGATIVE = -1    # Notch, minus thickness (old name length)
    II_POSITIVE = 2       # Finger, full (old name width)
    II_NEGATIVE = -2     # Notch, full (old name width)
    III_POSITIVE = 3     # Finger, minus thickness (old name heitgh)
    III_NEGATIVE = -3    # Notch, minus thickness (old name height)
    OTHER_POSITIVE = 4 
    OTHER_NEGATIVE = -4

    def is_positive(self):
        return self.value > 0
    def full_length(self):
        return self.value in [1, 2, -2]



def ratio_b_a(x: float, N: int, k:int, t: float) -> float:
    """Ratio of inner vs outter edge measurement  where `a` is 
    the measure at the start/end of the edge and `b` the inner value.
    ```
    Edge I+  the `+` indicates that the edge starts and ends with 
    a finger and I- starts with a notch. Note that I- is shorter 
    than I+ by 2*t because the space is needed for the other edge
    that is perpendicular to this one. 
    |     ._______.     ._______.     ._______.     |
    |     |       |     |       |     |       |     |
    *-----*       *-----*       *-----*       *-----*
    <--a--><--b--><--a--><--b--><--a--><--b--><--a-->
    
    <t>   ._______.     ._______.     ._______.   <t>
          |       |     |       |     |       |      
       *--*       *-----*       *-----*       *---*
       |                                          |

    I+ = a + b + ... + a  = N*a + (N-1)*a       (1)
    I- = a-t + b + a + b + ... + a-t = N*a -2*t + (N-1)*a (1b)
    with I+ - I- = 2*t
    Assume: 
    r = b/a   (2) and 
    a = k*t   (3), 
    where t is the material thickness and k is a factor k ={1, 2, 3, ...}
    
    Then with (1-3)
    I+ = N*k*t + (N-1)*r*k*t*
    

    given some length `x = I+ = N*k*t + (N-1)*r*k*t*` and specifying N, k and t
    the ratio r will be 
    N*k*t + (N-1)*r*k*t*  = x
    k*t*[ N + (N-1)* r]   = x
          N + (N-1)* r    = x/k*t
              (N-1)* r    = x/k*t -N
                     r    = x/(k*t*[N-1]) - N/(N-1)  (4)

    Note1: (4) will be the same for I- as I- = x -2*t and `-2*t` will cancel out with (1b)
    Note2: (4) will hold for II+/- and III+/- as well. 
    ```
    Args:
        x (float): expected length of ed
        N (int): number of fingers, for edge+,  or notches, if edge-
        k (int): factor that defines the length of `a = k * t`
        t (float): material thickness

    Returns:
        float: ratio of `r = a/b`
    """
    return x/(k*t*(N-1)) - N/(N-1)

def count_N_a(x: float, r: float, k:int, t: float) -> float:
    """Number of `a` elements in the edge.
    ```
    Edge I+  the `+` indicates that the edge starts and ends with 
    a finger and I- starts with a notch. Note that I- is shorter 
    than I+ by 2*t because the space is needed for the other edge
    that is perpendicular to this one. 
    |     ._______.     ._______.     ._______.     |
    |     |       |     |       |     |       |     |
    *-----*       *-----*       *-----*       *-----*
    <--a--><--b--><--a--><--b--><--a--><--b--><--a-->
    
    <t>   ._______.     ._______.     ._______.   <t>
          |       |     |       |     |       |      
       *--*       *-----*       *-----*       *---*
       |                                          |

    I+ = a + b + ... + a  = N*a + (N-1)*a       (1)
    I- = a-t + b + a + b + ... + a-t = N*a -2*t + (N-1)*a (1b)
    with I+ - I- = 2*t
    Assume: 
    r = b/a   (2) and 
    a = k*t   (3), 
    where t is the material thickness and k is a factor k ={1, 2, 3, ...}
    
    Then with (1-3)
    I+ = N*k*t + (N-1)*r*k*t*
    

    given some length `x = I+ = N*k*t + (N-1)*r*k*t*` and specifying r, k and t
    the ratio r will be 
    N*k*t + (N-1)*r*k*t*  = x
    k*t*[ N + (N-1)* r]   = x
          N + N*r -r      = x/k*t
              N*(1+r)     = x/k*t + r
              N           = x/(k*t*[1+r]) - r/(1+r)  (4)

    Note1: (4) will be the same for I- as I- = x -2*t and `-2*t` will cancel out with (1b)
    Note2: (4) will hold for II+/- and III+/- as well. 
    ```
    Args:
        x (float): expected length of edge
        r (float): ratio of `r = a/b`
        k (int): factor that defines the length of `a = k * t`
        t (float): material thickness

    Returns:
        float: number of fingers, for edge+, or notches, if edge-
    """
    return x/(k*t*(1+r)) - r/(1+r)


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
    
    @property
    def length(self) -> float:
        """Length of edge"""
        ...

    @property
    def full_length(self) -> float:
        """Full length of edge without thickness correction due to fitting"""
        return self.length()
    

# todo: simple edge that only contains staight lines?

class StraightLineEdge(Edge):

    def __init__(self, length: Dim|float) -> None:
        super().__init__()
        self._length: Dim|float = length
    
    @property
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
    def __init__(self, stand_l: Dim, stand_h: Dim, edge_length: Dim) -> None:
        super().__init__()
        self.stand_l: Dim = stand_l
        self.stand_h: Dim = stand_h
        self.edge_length: Dim = edge_length
    @property
    def length(self) -> float:
        return self.edge_length.value
    
    def build_path(self, path: Path) -> Path:
        val = self.stand_h.value/2
        stand_notch = self.edge_length - 2*self.stand_l - self.stand_h

        path.h_dim(self.stand_l)
        path.v(val)
        path.line_to_rel(val, val)
        path.h_dim(stand_notch)
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
    def create_by_length(cls, e_type: EdgeTyp, length: Dim, finger_notch_size: Dim,  finger_count: int, thickness: Dim, kerf: Dim=None) -> None:

        finger_count_dim: Dim = length.new_with_name_prefix(finger_count, "N", unit="")
        notch_count_dim: Dim = Dim(finger_count-1, name=f"{finger_count_dim.name} -1", unit="")

        ret = cls(finger_notch_size, finger_count_dim, finger_notch_size, notch_count_dim, thickness, kerf)
        if ret.is_positive_edge() and e_type.is_positive():
            ret.edge_type = e_type
        elif not e_type.is_positive():
            ret.edge_type = e_type
        else:
            raise ValueError(f"given edge type sign does not match the sign of created edge. Edge: {ret} with edge type: {ret.edge_type} but provided type was {e_type}")
        
        return ret
    @classmethod
    def create_by_length_relative(cls, e_type: EdgeTyp, length: Dim, k_factor:int, thickness: Dim, finger_count: int = None, ratio_ba: float = None, kerf: Dim=None) -> None:
        _finger_count = None
        if finger_count is not None:
            ratio_ba = ratio_b_a(x = length.value, N=finger_count, k=k_factor, t=thickness.value)
        elif ratio_ba is not None:
            _finger_count = count_N_a(x= length.value, r=ratio_ba, k=k_factor, t=thickness.value)
            finger_count = round(_finger_count)

        finger_dim : Dim = length.new_with_name_prefix(k_factor*thickness.value, "a")
        finger_count_dim: Dim = length.new_with_name_prefix(finger_count, "N", unit="")
        notch_dim : Dim= length.new_with_name_prefix(ratio_ba*k_factor*thickness.value, "b")
        notch_count_dim: Dim = Dim(finger_count-1, name=f"{finger_count_dim.name} -1", unit="")

        ret = cls(finger_dim, finger_count_dim, notch_dim, notch_count_dim, thickness, kerf)
        if ret.is_positive_edge() and e_type.is_positive():
            ret.edge_type = e_type
        elif not e_type.is_positive():
            ret.edge_type = e_type
        else:
            raise ValueError(f"given edge type sign does not match the sign of created edge. Edge: {ret} with edge type: {ret.edge_type} but provided type was {e_type}")
        
        if _finger_count is not None:
            logging.warning(f"calculated finger count is {_finger_count} and will be rounded to {finger_count}. Edge length will be {ret.full_length()}")

        return ret


    @classmethod
    def create_I_relative(cls, length: Dim, k_factor:int, thickness: Dim, finger_count: int = None, ratio_ba: float = None, kerf: Dim=None):
        """Create positive I+ edge with length and either finger_count by given ratio_ba or the other way around.
        Note: if ratio_ba is given the created edge will not have the exact length due to rounding errors for finger count."""
        return cls.create_by_length_relative(EdgeTyp.I_POSITIVE, length=length, k_factor=k_factor, thickness=thickness, finger_count=finger_count, ratio_ba=ratio_ba, kerf=kerf)
    @classmethod
    def create_I(cls, length: Dim, finger_notch_size: Dim, thickness: Dim, finger_count: int, kerf: Dim=None):
        return cls.create_by_length(EdgeTyp.I_POSITIVE, length=length, finger_notch_size=finger_notch_size, thickness=thickness, finger_count=finger_count, kerf=kerf)

    @classmethod
    def create_II_relative(cls, length: Dim, k_factor:int, thickness: Dim, finger_count: int = None, ratio_ba: float = None, kerf: Dim=None):
        """Create positive II+ edge with length and either finger_count by given ratio_ba or the other way around.
        Note: if ratio_ba is given the created edge will not have the exact length due to rounding errors for finger count."""
        return cls.create_by_length_relative(EdgeTyp.II_POSITIVE, length=length, k_factor=k_factor, thickness=thickness, finger_count=finger_count, ratio_ba=ratio_ba, kerf=kerf)
    @classmethod
    def create_II(cls, length: Dim, finger_notch_size: Dim, thickness: Dim, finger_count: int, kerf: Dim=None):
        return cls.create_by_length(EdgeTyp.II_POSITIVE, length=length, finger_notch_size=finger_notch_size, thickness=thickness, finger_count=finger_count, kerf=kerf)

    @classmethod
    def create_III_relative(cls, length: Dim, k_factor:int, thickness: Dim, finger_count: int = None, ratio_ba: float = None, kerf: Dim=None):
        """Create positive III+ edge with length and either finger_count by given ratio_ba or the other way around.
        Note: if ratio_ba is given the created edge will not have the exact length due to rounding errors for finger count."""
        return cls.create_by_length_relative(EdgeTyp.III_POSITIVE, length=length, k_factor=k_factor, thickness=thickness, finger_count=finger_count, ratio_ba=ratio_ba, kerf=kerf)
    @classmethod
    def create_III(cls, length: Dim, finger_notch_size: Dim, thickness: Dim, finger_count: int, kerf: Dim=None):
        return cls.create_by_length(EdgeTyp.III_POSITIVE, length=length, finger_notch_size=finger_notch_size, thickness=thickness, finger_count=finger_count, kerf=kerf)

    @classmethod
    def as_length(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.I_POSITIVE
        else:
            ret.edge_type = EdgeTyp.I_NEGATIVE
        return ret

    @classmethod
    def as_width(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.II_POSITIVE
        else:
            ret.edge_type = EdgeTyp.II_NEGATIVE
        return ret

    @classmethod
    def as_height(cls, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim=None) -> None:
        ret = cls(finger, finger_count, notch, notch_count, thickness, kerf)
        if ret.is_positive_edge():
            ret.edge_type = EdgeTyp.III_POSITIVE
        else:
            ret.edge_type = EdgeTyp.III_NEGATIVE
        return ret

    def as_holes_edge(self) ->FingerJointHolesEdge:
        return FingerJointHolesEdge.from_finger_joint_edge(self)

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
    
    @property
    def full_length(self) -> float:
        return (self.finger_count * self.finger.value + self.notch_count * self.notch.value).value
    
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

    @classmethod
    def from_finger_joint_edge(cls, e: FingerJointEdge):
        ret =  cls(e.finger, e.finger_count, e.notch, e.notch_count, e.thickness, e.kerf)
        ret.edge_type = e.edge_type
        return ret

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
            if self.is_positive_edge(): # positive edge: finger->notch->finger
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

class StackableSideEdge(FingerJointEdge):

    @classmethod
    def from_edge(cls, e: FingerJointEdge, stand_h: Dim) -> StackableSideEdge:
        return cls(
            stand_h = stand_h, 
            finger = e.finger,
            finger_count = e.finger_count,
            notch = e.notch,
            notch_count = e.notch_count,
            thickness = e.thickness,
            kerf = e.kerf,
        )

    def __init__(self, stand_h: Dim, finger: Dim, finger_count: Dim, notch: Dim, notch_count: Dim, thickness: Dim, kerf: Dim | None = None) -> None:
        super().__init__(finger, finger_count, notch, notch_count, thickness, kerf)
        self.stand_h: Dim = stand_h
        self.path_pre_processors.insert(0, self.append_start) 
    
    def append_start(self, path: Path) -> Path:
        path.h_dim(self.stand_h + self.thickness)
        return path
    
    @property
    def length(self) -> float:
        return super().length + self.stand_h.value + self.thickness.value
    
    @property
    def full_length(self) -> float:
        return super().full_length + self.stand_h.value + self.thickness.value

