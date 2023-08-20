import box.transform as t
from box.constrains import Constraint
from box.constraints_impl import UserParamter
from box.dimension import Dim
from box.edge import FingerJointEdge
from box.face import Face
from box.geometry import Path, PathConsumerByTransfrom, Plane
from box.boxes.comon import add_dimension_constraint


from dataclasses import dataclass, field
from functools import partial
from typing import List

from box.boxes.comon import Box
from box.boxes.comon import add_origin_offset, add_perpendicular_constraints, add_first_line_h_or_v_constraint, add_equal_constrains_instead_of_dimensions, add_sktech_offset





@dataclass
class SimpleBox(Box):

    length: FingerJointEdge
    width: FingerJointEdge
    height: FingerJointEdge
    bottom_top: Face
    front_back: Face
    left_right: Face
    post_transformations: dict = field(init=False)
    thickness: Dim = field(default=Dim(3.0, "thickness", "mm"))
    kerf: Dim = field(default=Dim(0.1, "kerf", "mm"))

    constraints :List[Constraint] = field(default_factory=list)

    _paths: List[Path] = field(init=False, default=list)

    @classmethod
    def eqaul_from_finger_count(
            cls,
            length_finger_count: Dim,
            width_finger_count: Dim,
            height_finger_count: Dim,
            finger_dim: float,
            thickness: Dim,
            kerf: Dim):

        length_f_dim: Dim = Dim(value=finger_dim, name="l_finger", unit="mm")
        length_n_dim: Dim = Dim(value=finger_dim, name="l_notch", unit="mm")

        width_f_dim: Dim = Dim(value=finger_dim, name="w_finger", unit="mm")
        width_n_dim: Dim = Dim(value=finger_dim, name="w_notch", unit="mm")

        height_f_dim: Dim = Dim(value=finger_dim, name="h_finger", unit="mm")
        height_n_dim: Dim = Dim(value=finger_dim, name="h_notch", unit="mm")

        user_para = [
            UserParamter(length_f_dim),
            UserParamter(length_n_dim),
            UserParamter(width_f_dim),
            UserParamter(width_n_dim),
            UserParamter(height_f_dim),
            UserParamter(height_n_dim),
            UserParamter(thickness)
        ]
        if kerf is not None:
            user_para.append(UserParamter(kerf))

        length = FingerJointEdge.as_length(
            finger=length_f_dim,
            finger_count=length_finger_count,
            notch=length_n_dim,
            notch_count=length_finger_count.new_relative(-1, "length_finger_count - 1"),
            thickness=thickness,
            kerf=kerf)

        width = FingerJointEdge.as_width(
            finger=width_f_dim,
            finger_count=width_finger_count,
            notch=width_n_dim,
            notch_count=width_finger_count.new_relative(-1, "width_finger_count - 1"),
            thickness=thickness,
            kerf=kerf)

        height = FingerJointEdge.as_height(
            finger=height_f_dim,
            finger_count=height_finger_count,
            notch=height_n_dim,
            notch_count=height_finger_count.new_relative(-1, "height_finger_count -1 "),
            thickness=thickness,
            kerf=kerf)

        return cls.from_edges(length, width, height, thickness, kerf, user_para=user_para)

    @classmethod
    def from_edges(
        cls,
        length: FingerJointEdge,
        width: FingerJointEdge,
        height: FingerJointEdge,
        thickness: Dim,
        kerf:Dim,
        user_para: List[Constraint] = ()
        ):

        return  cls(
            length=length,
            width=width,
            height=height,
            bottom_top=Face.full_joint_face(length.as_positive(), width.as_positive(), name="bottom_top", plane=Plane.XY),
            front_back=Face.full_joint_face(length.as_negative(), height.as_negative(), name="front_back", plane=Plane.XZ),
            left_right= Face.full_joint_face(width.as_negative(), height.as_positive(), name="sides_left_right", plane=Plane.YZ),
            thickness=thickness,
            kerf=kerf,
            constraints=user_para
        )


    def init_constrains(self):
        # set constraint order
        for f in self.faces:
            f.constraint_providers.append(add_perpendicular_constraints)
            if f.name == self.front_back.name:
                f.constraint_providers.append(partial(add_sktech_offset, offset_x=self.thickness))
            else:
                f.constraint_providers.append(add_sktech_offset)

            f.constraint_providers.append(add_equal_constrains_instead_of_dimensions)
            f.constraint_providers.append(add_dimension_constraint)
            f.constraint_providers.append(add_origin_offset)
            f.constraint_providers.append(add_first_line_h_or_v_constraint)


        # refelct transformation for fusion360 cooridnate system fix 
        # box.left_right.post_path_transforms.append(t.create_transform(t.mat_reflect_y))
        self.left_right.post_path_consumer.append(PathConsumerByTransfrom.from_mat(t.mat_rot_90))
        self.left_right.post_path_consumer.append(lambda x: x.reverse()) # reverse path 
        # refelct transformation for fusion360 cooridnate system fix (offset to alline joints)
        self.front_back.post_path_consumer.append(PathConsumerByTransfrom.from_mat(t.mat_shift(dx=self.thickness.value), t.mat_reflect_x)) # fusion360 fix

    @property
    def faces(self) -> List[Face]:
        return [self.bottom_top, self.front_back, self.left_right]



class SimpleBoxStraigtTop(SimpleBox):


    @classmethod
    def from_edges(
        cls,
        length: FingerJointEdge,
        width: FingerJointEdge,
        height: FingerJointEdge,
        thickness: Dim,
        kerf:Dim,
        user_para: List[Constraint] = ()
        ):

        return  cls(
            length=length,
            width=width,
            height=height,
            bottom_top=Face.full_joint_face(length.as_positive(), width.as_positive(), name="bottom_top", plane=Plane.XY),
            front_back=Face.straigth_top_face(length.as_negative(), height.as_negative(), name="front_back", plane=Plane.XZ),
            left_right= Face.straigth_top_face(width.as_negative(), height.as_positive(), name="sides_left_right", plane=Plane.YZ),
            thickness=thickness,
            kerf=kerf,
            constraints=user_para
        )