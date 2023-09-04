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
    parent.add_argument("-L", "--length", type=float, help="length in mm")
    parent.add_argument("-W", "--width", type=float, help="width in mm")
    parent.add_argument("-H", "--height", type=float, help="height in mm")
    parent.add_argument("-T", "--thickness", type=float, help="martial thickness in mm, Default(3.0)", default=3.0)

    sub_parser = parent.add_subparsers(title="Boxtypes")

    p: argparse.ArgumentParser = stackable_ns(
        sub_parser.add_parser("stackableBox", add_help=False, parents=[parent])
        )

    return parent.parse_args()


if __name__ == "__main__":
    ns: argparse.Namespace = build_parser()
    main(ns)