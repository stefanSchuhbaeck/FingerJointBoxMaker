from fingerJointBoxMaker.constrains import Constraint
from fingerJointBoxMaker.constraints_impl import UserParamter
from fingerJointBoxMaker.dimension import Dim
from fingerJointBoxMaker.edge import FingerJointEdge, StackableBottomTopEdge, FingerJointHolesEdge, StackableSideEdge
from fingerJointBoxMaker.face import Face
from fingerJointBoxMaker.geometry import Path, PathConsumerByTransfrom, Plane
from fingerJointBoxMaker.boxes.comon import add_dimension_constraint
import fingerJointBoxMaker.transform as t

from dataclasses import dataclass, field
from functools import partial
from typing import List

from fingerJointBoxMaker.boxes.comon import Box
from fingerJointBoxMaker.boxes.comon import add_origin_offset, add_perpendicular_constraints, add_first_line_h_or_v_constraint, add_equal_constrains_instead_of_dimensions, add_sktech_offset
from fingerJointBoxMaker.edge import EdgePathBuilder
from fingerJointBoxMaker.transform import Transform, create_transform, mat_reflect_x, mat_reflect_y, mat_shift, mat_rot_90
from fingerJointBoxMaker.face import FacePathBuilder

from fingerJointBoxMaker.export.plot import plot_path


@dataclass
class StackableBox(Box):

    front_face: Face
    side_face: Face
    bottom_face: Face

    def faces(self) -> List[Face]:
        return [self.front_face, self.side_face, self.bottom_face]

    @classmethod
    def create(cls, length: FingerJointEdge, width: FingerJointEdge, height: FingerJointEdge):

        # dependent edges
        length_p_holes: FingerJointHolesEdge = length.as_holes_edge()
        width_p_holes: FingerJointHolesEdge  = width.as_holes_edge()

        bottom_top_front_edge = StackableBottomTopEdge(
            stand_l=Dim(0.15*length.full_length), 
            stand_h=Dim(0.075*length.full_length), 
            edge_length=Dim(length.full_length)) # bottom, top with length.as_positive
        bottom_top_side_edge = StackableBottomTopEdge(
            stand_l=Dim(0.15*width.full_length), 
            stand_h=Dim(0.075*length.full_length), 
            # stand_h=Dim(0.075*width.full_length), 
            edge_length=Dim(width.full_length)) # bottom, top with length.as_positive
        
        # Bottom Face ( length-negative / width-negative) 
        # such that the bottom has all fingers 'inside"
        bottom_face  = Face.full_joint_face(
            e1= length.as_negative(),
            e2= width.as_negative(),
            name="Bottom",
            plane=Plane.XY
        )
        
        # FrontFace
        height_mixin: StackableSideEdge = StackableSideEdge.from_edge(e=height.as_positive(), stand_h=bottom_top_front_edge.stand_h)
        fb:FacePathBuilder = FacePathBuilder()      # bottom with stands for stacking
        fb.add(EdgePathBuilder(bottom_top_front_edge))
        # left side with notches
        fb.add(EdgePathBuilder(height_mixin)).left_side_transform()
        # top with same shape as bottom to allow stacking (no reflecting)
        fb.add(EdgePathBuilder(bottom_top_front_edge).add_transform_mat(mat_shift(dy=fb.last.length)).reverse_path())
        # right side with notches
        fb.add(EdgePathBuilder(height_mixin)).right_side_transform()
        # holes to fit bottom plate
        _e = EdgePathBuilder(length_p_holes).allow_concat().add_transform_mat(
            mat_shift(dy=(bottom_top_front_edge.stand_h + length_p_holes.thickness).value))
        fb.add(_e)
        front_face = Face(face_builder=fb, name="Front", plane=Plane.XZ)

        # SideFace
        height_mixin: StackableSideEdge = StackableSideEdge.from_edge(e=height.as_negative(), stand_h=bottom_top_front_edge.stand_h)
        fb:FacePathBuilder = FacePathBuilder()      # bottom with stands for stacking
        fb.add(EdgePathBuilder(bottom_top_side_edge))
        # left side with notches
        fb.add(EdgePathBuilder(height_mixin)).left_side_transform()
        # top with same shape as bottom to allow stacking (no reflecting)
        fb.add(EdgePathBuilder(bottom_top_side_edge).add_transform_mat(mat_shift(dy=fb.last.length)).reverse_path())
        # right side with notches
        fb.add(EdgePathBuilder(height_mixin)).right_side_transform()
        # holes to fit bottom plate
        _e = EdgePathBuilder(width_p_holes).allow_concat().add_transform_mat(
            mat_shift(dy=(bottom_top_side_edge.stand_h + width_p_holes.thickness).value))
        fb.add(_e)
        side_face = Face(face_builder=fb, name="Side", plane=Plane.XZ)

        return cls(front_face=front_face, side_face=side_face, bottom_face=bottom_face)


