import fingerJointBoxMaker.transform as t
from fingerJointBoxMaker.constrains import Constraint
from fingerJointBoxMaker.constraints_impl import UserParamter
from fingerJointBoxMaker.dimension import Dim
from fingerJointBoxMaker.edge import FingerJointEdge, StackableBottomTopEdge, FingerJointHolesEdge
from fingerJointBoxMaker.face import Face
from fingerJointBoxMaker.geometry import Path, PathConsumerByTransfrom, Plane
from fingerJointBoxMaker.boxes.comon import add_dimension_constraint


from dataclasses import dataclass, field
from functools import partial
from typing import List

from fingerJointBoxMaker.boxes.comon import Box
from fingerJointBoxMaker.boxes.comon import add_origin_offset, add_perpendicular_constraints, add_first_line_h_or_v_constraint, add_equal_constrains_instead_of_dimensions, add_sktech_offset
from fingerJointBoxMaker.edge import EdgePathBuilder, stackable_side_edge
from fingerJointBoxMaker.transform import Transform, create_transform, mat_reflect_x, mat_reflect_y, mat_shift, mat_rot_90
from fingerJointBoxMaker.face import FacePathBuilder



@dataclass
class StackableBox(Box):

    @classmethod
    def create(cls):

        length: FingerJointEdge = FingerJointEdge
        widht: FingerJointEdge = None
        height: FingerJointEdge = None

        #Face
        bottom_top_front_edge = StackableBottomTopEdge() # bottom, top with length.as_positive
        bottom_top_side_edge = StackableBottomTopEdge() # bottom, top with width.as_positive

        hole_face = FingerJointHolesEdge()
        
        # Bottom Face ( length-negative / widht-negative) 
        # such taht the bottom has all fingers 'inside"
        bottom_face  = Face.full_joint_face(
            e1= length.as_negative(),
            e2= widht.as_negative(),
            name="Bottom",
            plane=Plane.XY
        )
        
        # FrontFace
        height_mixin: FingerJointEdge = stackable_side_edge(edge=height.as_negative(), stand_h=bottom_top_front_edge.stand_h)
        fb:FacePathBuilder = FacePathBuilder()
        # bottom with stands for stacking
        fb.add(EdgePathBuilder(bottom_top_front_edge))
        # left side with notches
        fb.add(EdgePathBuilder(height_mixin)).left_side_transform()
        # top with same shape as bootom to allow stacking
        fb.add(EdgePathBuilder(bottom_top_front_edge)).top_side_transfrom()
        # right side with notches
        fb.add(EdgePathBuilder(height_mixin)).right_side_transfrom()
        # holes to fit bottom plate
        _e = EdgePathBuilder(hole_face).allow_concat().add_transfrom_mat(
            mat_shift(dy=(bottom_top_front_edge.stand_h + hole_face.thickness).value))
        fb.add(_e)
        front_face = Face(face_builder=fb, name="Front", plane=Plane.XZ)

        # SideFace
        height_mixin: FingerJointEdge = stackable_side_edge(edge=height.as_positive(), stand_h=bottom_top_front_edge.stand_h)
        fb:FacePathBuilder = FacePathBuilder()

        # bottom with stands for stacking
        fb.add(EdgePathBuilder(bottom_top_side_edge))
        
        # left side with notches
        fb.add(EdgePathBuilder(height_mixin)).left_side_transform()
        
        # top with same shape as bootom to allow stacking
        fb.add(EdgePathBuilder(bottom_top_side_edge)).top_side_transfrom()
        
        # right side with notches
        fb.add(EdgePathBuilder(height_mixin)).right_side_transfrom()

        # holes to fit bottom plate
        _e = EdgePathBuilder(hole_face).allow_concat().add_transfrom_mat(
            mat_shift(dy=(bottom_top_side_edge.stand_h + hole_face.thickness).value))
        fb.add(_e)
        side_face = Face(face_builder=fb, name="Side", plane=Plane.YZ)



