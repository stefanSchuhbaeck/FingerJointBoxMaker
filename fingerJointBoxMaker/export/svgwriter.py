from __future__ import annotations
from typing import List
from fingerJointBoxMaker.boxes.stackable_box import StackableBox
from fingerJointBoxMaker.dimension import Dim
from fingerJointBoxMaker.edge import FingerJointEdge
from fingerJointBoxMaker.geometry import Path, Line

import svgwrite as svg
import svgwrite.path as spath
import numpy as np

from fingerJointBoxMaker.transform import create_transform, mat_shift

class PathExporter:

    def __init__(self, unit="") -> None:
        self.p = []
        self.closed = False
        self.unit = unit
    
    @property
    def is_closed(self):
        return self.closed
    
    def as_svg_path(self, **attrib) -> spath.Path:
        return spath.Path(self.p, **attrib)

    def as_hairline(self, **attrib) -> spath.Path:
        attrib.setdefault("fill", "none")
        attrib.setdefault("stroke", "#0000FF")
        attrib.setdefault("stroke-width", BoxDrawing.MIN_STROKE)
        return self.as_svg_path(**attrib)
    
    def _add(self, cmd:str, *xy) -> PathExporter:
        if len(xy) == 2:
            self.p.extend([cmd, f"{xy[0]}{self.unit}", f"{xy[1]}{self.unit}"])
        elif xy:
            self.p.extend([cmd, f"{xy}{self.unit}"])
        return self

    def M(self, x, y) -> PathExporter:
        return self._add("M", x, y)

    def m(self, x, y) -> PathExporter:
        return self._add("m", x, y)

    def L(self, x, y) -> PathExporter:
        return self._add("L", x, y)

    def l(self, x, y) -> PathExporter:
        return self._add("l", x, y)
    
    def H(self, x) -> PathExporter:
        return self._add("H", x)

    def h(self, x) -> PathExporter:
        return self._add("h", x)
    
    def V(self, y) -> PathExporter:
        return self._add("V", y)

    def v(self, y) -> PathExporter:
        return self._add("v", y)

    def Z(self) -> PathExporter:
        self.p.extend("Z")
        self.closed = True
        return self
    
    def z(self) -> PathExporter:
        self.p.extend("z")
        self.closed = True
        return self

    def l(self, x, y) -> PathExporter:
        return self.p.extend(["l", x, y])
    

    def parse_box_path(self, path: Path) -> PathExporter:
        self.M(*path.points[0])
        for line in path.lines:
            if line.is_construction:
                self.M(*line.end)
            else:
                self.L(*line.end)
        return self

class BoxDrawing:

    MIN_STROKE = 0.2645833333 

    def __init__(self, **svgargs) -> None:
        self.paths: List[Path] = []        
        self.names: List[str] = []
        self.svgargs = svgargs
        self.drawing: svg.Drawing = None
    
    def add(self, p: Path, name: str) -> BoxDrawing:
        self.paths.append(p)
        self.names.append(name)
        return self
    
    def _build_drawing(self):
        bound = self.bbox()
        px_to_mm = 0.2645833333 
        max_dim = (bound[1] + 30) 
        self.drawing = svg.Drawing(**self.svgargs, size=(f"{max_dim[0]}mm", f"{max_dim[1]}mm"), viewBox=f"0 0 {max_dim[0]} {max_dim[1]}")
    
    def bbox(self):
        bbox = np.concatenate([p.bounding_box() for p in self.paths])
        ret = bbox.min(axis=0)
        ret = np.append(ret, [bbox.max(axis=0)]).reshape((2,2))
        return ret
    
    def save(self):
        if self.drawing is None:
            self._build_drawing()
        for p, name in zip(self.paths, self.names):
            self.export_path(p, name=name)
        self.drawing.save(pretty=True, indent=2)

    def export_path(self, path: Path, name: str):
        p = PathExporter()
        p.parse_box_path(path).z()
        self.drawing.add(p.as_hairline(id=name))


if __name__ == "__main__":
    b = StackableBox.create(
        length=FingerJointEdge.create_I(Dim(50.0, "l"), k_factor=4, thickness=Dim(3.0, "t"), finger_count=3),
        width=FingerJointEdge.create_II(Dim(40.0, "l"), k_factor=3, thickness=Dim(3.0, "t"), finger_count=3),
        height=FingerJointEdge.create_III(Dim(30.0, "l"), k_factor=3, thickness=Dim(3.0, "t"), finger_count=3),
    )

    drawing: BoxDrawing = BoxDrawing(
            filename = "/home/sts/upstream/github.com/stefanSchuhbaeck/FingerJointBoxMaker/fingerJointBoxMaker/out/out2.svg", 
            profile="full"
        )



    
    t1 = create_transform(mat_shift(dx=30, dy=30))
    p_bottom = b.build_face(b.bottom_face).transform(t1)
    drawing.add(p_bottom, "bottom")


    t2 = create_transform(mat_shift(dx=30, dy=10+p_bottom.bounding_box()[1][1]))
    p_front1 = b.build_face(b.front_face).transform(t2)
    t2 = create_transform(mat_shift(dy=10+p_front1.height()))
    p_front2 = p_front1.transform(t2)

    drawing.add(p_front1, "front1")
    drawing.add(p_front2, "front2")

    p_side1 = b.build_face(b.side_face).transform(create_transform(mat_shift(dy=30, dx=15 + p_bottom.bounding_box()[1][0])))
    p_side2 = p_side1.transform(create_transform(mat_shift(dy=10+p_side1.height())))
    drawing.add(p_side1, "side1")
    drawing.add(p_side2, "side2")

    drawing.save()

