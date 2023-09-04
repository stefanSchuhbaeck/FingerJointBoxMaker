from fingerJointBoxMaker.dimension import  Dim
from fingerJointBoxMaker.constrains import Constraint
from fingerJointBoxMaker.geometry import Line, Path, Orientation, Plane
from fingerJointBoxMaker.boxes.comon import Box
from fingerJointBoxMaker.boxes.simple_box import SimpleBox, SimpleBoxStraightTop
from fingerJointBoxMaker.constraints_impl import *

print_msg_f = None

def print_msg(msg: str):
    if print_msg_f is not None:
        print_msg_f(msg)
    print(msg)