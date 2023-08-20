from box.dimension import  Dim
from box.constrains import Constraint
from box.geometry import Line, Path, Orientation, Plane
from box.boxes.comon import Box
from box.boxes.simple_box import SimpleBox, SimpleBoxStraigtTop
from box.constraints_impl import *

print_msg_f = None

def print_msg(msg: str):
    if print_msg_f is not None:
        print_msg_f(msg)
    print(msg)