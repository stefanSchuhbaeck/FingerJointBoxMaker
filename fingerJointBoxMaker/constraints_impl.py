from __future__ import annotations
from fingerJointBoxMaker.constrains import Constraint, Transform
from fingerJointBoxMaker.geometry import Line, Path
from fingerJointBoxMaker.dimension import Dim

import numpy as np
from numpy.typing import NDArray

from typing import Any, List, Protocol


class UserParamter:
    def __init__(self, dim:Dim) -> None:
        self.dim = dim
        
    def get_name(self) -> str:
        return Constraint.UserParameter

    def process(self, transfrom_f) -> Any:
        return transfrom_f(self.dim)

class OriginLockConstraint:
    def __init__(self, line:Line) -> None:
        self.line = line

    def get_name(self) -> str:
        return Constraint.OriginLock

    def process(self, transfrom_f) -> Any:
        return transfrom_f(self.line)


class DimenssionConstraint:

    def __init__(self, path: Path) -> None:
        self.path = path

    def get_name(self) -> str:
        return Constraint.GeoDimension
    
    def process(self, transfrom_F) -> Any:
        return transfrom_F(self.path)

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

    @classmethod
    def collect(cls, lines: List[Line]):
        e = cls()
        for l in lines:
            e(l)
        return e

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