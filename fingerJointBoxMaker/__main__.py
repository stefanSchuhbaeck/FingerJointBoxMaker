import argparse
import os
import sys
from typing import Protocol, TextIO
from fingerJointBoxMaker.boxes.stackable_box import stackable_ns
from fingerJointBoxMaker.export.svgwriter import BoxDrawing


class SvgSaver(Protocol):

    def __call__(self, drawing: BoxDrawing, path: str|TextIO):
        pass


def main(ns:argparse.Namespace):
    drawing: BoxDrawing = ns.main(ns)
    drawing.save(ns.output)

def build_parser():
    parent = argparse.ArgumentParser(
        prog="FingerJointBoxMaker",
    )
    parent.add_argument("-o", "--output",  help="Save output csv in path. Default standard out.", required=False, default=sys.stdout)

    #equal finger/notch setup
    parent.add_argument("--bound", type=float, help="width length height  (space separated)", nargs=3)
    parent.add_argument("--finger-count", dest="finger_counts", help="up to 3 integers giving the number of finger for length, width and height", nargs="*")
    parent.add_argument("--finger-default-count", dest="finger_default", default=3, help="default number of fingers for each edge")
    parent.add_argument("-T", "--thickness", type=float, help="martial thickness in mm, Default(3.0)", default=3.0)
    parent.set_defaults(notch_count=_notch_count)

    sub_parser = parent.add_subparsers(title="Boxtypes")

    p: argparse.ArgumentParser = stackable_ns(
        sub_parser.add_parser("stackableBox", add_help=False, parents=[parent])
        )

    return parent.parse_args()


def _notch_count(ns: argparse.Namespace, i):
    if ns.finger_counts is not None and len(ns.finger_counts) > i:
        return ns.finger_counts[i]
    else:
        return ns.finger_default




if __name__ == "__main__":
    ns: argparse.Namespace = build_parser()
    main(ns)