from functools import partial
from typing import List
import unittest


import sys
import os


sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../.."))
import numpy as np

from box.joint import SimpleBox
from box.geometry import Path, Line
from box.dimension import Dim
import box.transform as t
from box.edge import Edge, EdgeTyp
from box.face import Face

def line_list_to_points(lines: List[Line]):
    points = lines[0].line
    for line in lines[1:]:
        assert(all(points[-1] == line.start))
        points = np.append(points, [line.end], axis=0)
    return points


class TestFinger(unittest.TestCase):
    def setUp(self) -> None:
        self.e = Edge(
            finger=Dim(4),
            finger_count=Dim(10),
            notch=Dim(3),
            notch_count=Dim(9))
    
    def neg(self):
        return ( Dim(10), Dim(5), Dim(10), Dim(6))

    def pos(self):
        return ( Dim(10), Dim(6), Dim(10), Dim(5))

    def test_length(self):
        self.assertEqual(self.e.length, 4*10 + 3*9)
    
    def test_edge_type_default(self):
        self.assertEqual(self.e.edge_type, None)

    def test_sign_of_edge(self):
        self.assertTrue(self.e.is_positive_edge())

        self.e.notch_count = self.e.finger_count+3
        self.assertFalse(self.e.is_positive_edge())

    def test_invalid_edeg(self):
        try:
            e = Edge(Dim(10), Dim(10), Dim(10), Dim(10))
            self.fail("Edge invalid.")
        except ValueError as _:
            pass
    
    def test_length(self):
        length_p: Edge = Edge.as_length(*self.pos())
        self.assertEqual(length_p.edge_type, EdgeTyp.LENGTH_POSTIVE)
        self.assertTrue(length_p.is_positive_edge())

        length_n: Edge = Edge.as_length(*self.neg())
        self.assertEqual(length_n.edge_type,  EdgeTyp.LENGTH_NEGATIVE)
        self.assertFalse(length_n.is_positive_edge())

        self.assertEqual(length_p, length_n.as_positive())
        self.assertEqual(length_n, length_p.as_negative())

    def test_width(self):
            width_p: Edge = Edge.as_width(*self.pos())
            self.assertEqual(width_p.edge_type, EdgeTyp.WIDTH_POSTIVE)
            self.assertTrue(width_p.is_positive_edge())

            width_n: Edge = Edge.as_width(*self.neg())
            self.assertEqual(width_n.edge_type,  EdgeTyp.WIDTH_NEGATIVE)
            self.assertFalse(width_n.is_positive_edge())

            self.assertEqual(width_p, width_n.as_positive())
            self.assertEqual(width_n, width_p.as_negative())

    def test_height(self):
            height_p: Edge = Edge.as_height(*self.pos())
            self.assertEqual(height_p.edge_type, EdgeTyp.HEIGHT_POSITIVE)
            self.assertTrue(height_p.is_positive_edge())

            height_n: Edge = Edge.as_height(*self.neg())
            self.assertEqual(height_n.edge_type,  EdgeTyp.HEIGHT_NEGATIVE)
            self.assertFalse(height_n.is_positive_edge())

            self.assertEqual(height_p, height_n.as_positive())
            self.assertEqual(height_n, height_p.as_negative())


class TestBox(unittest.TestCase):
     
    def setUp(self):
        self.length_finger_count=Dim(6, name="finger_count_l")
        self.width_finger_count=Dim(5, name="finger_count_w")
        self.height_finger_count=Dim(4, name="finger_cont_h")
        self.finger_dim=10.0
        self.thickness=Dim(3.0, name="d")
          
        self.box = SimpleBox.eqaul_from_finger_count(
            length_finger_count=self.length_finger_count,
            width_finger_count=self.width_finger_count,
            height_finger_count=self.height_finger_count,
            finger_dim=self.finger_dim,
            thickness=self.thickness
        )
    def test_edges(self):
        self.assertEqual(self.box.length.edge_type, EdgeTyp.LENGTH_POSTIVE)
        self.assertEqual(self.box.width.edge_type, EdgeTyp.WIDTH_POSTIVE)
        self.assertEqual(self.box.height.edge_type, EdgeTyp.HEIGHT_POSITIVE)

    def test_faces(self):
        edge1: Edge = self.box.faces[0].edge_1
        edge2: Edge = self.box.faces[0].edge_2
        self.assertEqual(edge1.finger.value , 10.0)
        self.assertEqual(edge1.finger_count.value, 6 )
        self.assertEqual(edge1.notch_count.value, 5 )
        self.assertEqual(edge2.finger.value , 10.0)
        self.assertEqual(edge2.finger_count.value, 5 )
        self.assertEqual(edge2.notch_count.value, 4 )

        edge1: Edge = self.box.faces[1].edge_1
        edge2: Edge = self.box.faces[1].edge_2
        self.assertEqual(edge1.finger.value , 10.0)
        self.assertEqual(edge1.finger_count.value, 5 )
        self.assertEqual(edge1.notch_count.value, 6 )
        self.assertEqual(edge2.finger.value , 10.0)
        self.assertEqual(edge2.finger_count.value, 3 )
        self.assertEqual(edge2.notch_count.value, 4 )

        edge1: Edge = self.box.faces[2].edge_1
        edge2: Edge = self.box.faces[2].edge_2
        self.assertEqual(edge1.finger.value , 10.0)
        self.assertEqual(edge1.finger_count.value, 3 )
        self.assertEqual(edge1.notch_count.value, 4 )
        self.assertEqual(edge2.finger.value , 10.0)
        self.assertEqual(edge2.finger_count.value, 4 )
        self.assertEqual(edge2.notch_count.value, 5 )

class TestDimensions(unittest.TestCase):

    def test_dim_arithmetic_int(self):
        d = Dim(3)
        self.assertEqual((d+10).value, 13)
        self.assertEqual((10+d).value, 13)

        self.assertEqual((d-1).value, 2)
        self.assertEqual((1-d).value, -2)
        
        self.assertEqual((d-10).value, -7)
        self.assertEqual((10-d).value, 7)

        self.assertEqual((d*.5).value, 3/2)
        self.assertEqual((.5*d).value, 3/2)

        self.assertEqual((d/2).value, 3/2)
        self.assertEqual((2/d).value, 2/3)

    def test_dim_arithmetic_float(self):
        d = Dim(3.0)
        self.assertEqual((d+10.).value, 13.)
        self.assertEqual((10.+d).value, 13.)

        self.assertEqual((d-1.).value, 2.)
        self.assertEqual((1.-d).value, -2.)
        
        self.assertEqual((d-10.).value, -7.)
        self.assertEqual((10.-d).value, 7.)

        self.assertEqual((d*.5).value, 3./2.)
        self.assertEqual((.5*d).value, 3./2.)

        self.assertEqual((d/2.).value, 3./2.)
        self.assertEqual((2./d).value, 2./3.)
    
    def test_dim_arithmetic_dim_add(self):
        d1 = Dim(1.0, "d1", "mm")
        d2 = Dim(2.0, "d2", "mm")

        self.assertEqual(d1+d2, Dim(3.0, "d1 + d2", "mm"))
        self.assertEqual(d2+d1, Dim(3.0, "d2 + d1", "mm"))
        self.assertEqual((d2+d1)+d1, Dim(4.0, "(d2 + d1) + d1", "mm"))
        self.assertEqual(d1 + (d2+d1), Dim(4.0, "d1 + (d2 + d1)", "mm"))
        self.assertEqual(d1+d2+d1, Dim(4.0, "(d1 + d2) + d1", "mm"))

        try: 
            ret = d1 + Dim(10, "d3", "m")
            self.fail("missmatch in unit shoudl fail")
        except TypeError as e:
            self.assertTrue("+" in e.args[0])
            self.assertTrue("mm != m" in e.args[0])


    def test_dim_arithmetic_dim_sub(self):
        d1 = Dim(1.0, "d1", "mm")
        d2 = Dim(2.0, "d2", "mm")

        self.assertEqual(d1-d2, Dim(-1.0, "d1 - d2", "mm"))
        self.assertEqual(d2-d1, Dim(1.0, "d2 - d1", "mm"))
        self.assertEqual((d2-d1)+d1, Dim(2.0, "(d2 - d1) + d1", "mm"))
        self.assertEqual(d1 - (d2-d1), Dim(0.0, "d1 - (d2 - d1)", "mm"))
        self.assertEqual(d1-d2-d1, Dim(-2.0, "(d1 - d2) - d1", "mm"))

        try: 
            ret = d1 - Dim(10, "d3", "m")
            self.fail("missmatch in unit shoudl fail")
        except TypeError as e:
            self.assertTrue("-" in e.args[0])
            self.assertTrue("mm != m" in e.args[0])

    def test_dim_arithmetic_dim_mult(self):
        d1 = Dim(2.0, "d1", "mm")
        d2 = Dim(3.0, "d2", "mm")

        self.assertEqual(d1*d2, Dim(6.0, "d1 * d2", "mm"))
        self.assertEqual(d2*d1, Dim(6.0, "d2 * d1", "mm"))
        self.assertEqual((d2*d1)*d1, Dim(12.0, "(d2 * d1) * d1", "mm"))
        self.assertEqual(d1 * (d2-d1), Dim(2.0, "d1 * (d2 - d1)", "mm"))
        self.assertEqual(d1*d2*d1, Dim(12.0, "(d1 * d2) * d1", "mm"))

        try: 
            ret = d1 * Dim(10, "d3", "m")
            self.fail("missmatch in unit shoudl fail")
        except TypeError as e:
            self.assertTrue("*" in e.args[0])
            self.assertTrue("mm != m" in e.args[0])

    def test_dim_arithmetic_dim_div(self):
        d1 = Dim(2.0, "d1", "mm")
        d2 = Dim(6.0, "d2", "mm")

        self.assertEqual(d1/d2, Dim(1/3, "d1 / d2", "mm"))
        self.assertEqual(d2/d1, Dim(6.0/2.0, "d2 / d1", "mm"))
        self.assertEqual((d2/d1)*d1, Dim(6.0, "(d2 / d1) * d1", "mm"))
        self.assertEqual(d1 / (d2/d1), Dim((2./(6./2.)), "d1 / (d2 / d1)", "mm"))
        self.assertEqual(d1/d2/d1, Dim((2./6./2.), "(d1 / d2) / d1", "mm"))

        try: 
            ret = d1 / Dim(10, "d3", "m")
            self.fail("missmatch in unit shoudl fail")
        except TypeError as e:
            self.assertTrue("/" in e.args[0])
            self.assertTrue("mm != m" in e.args[0])

class TestEdge(unittest.TestCase):

    def test_edge_shift_rot(self):
        e: Edge = Edge.as_length(Dim(10, "finger"), Dim(2, "finger_c"), Dim(5, "notch"), Dim(1, "notch_c"))
        self.assertTrue(e.is_positive_edge())
        path1 = e.make_path(Dim(3, "thickness"))
        points1 = np.array([0, 0, 10, 0, 10, 3, 15, 3, 15, 0, 25, 0], dtype=float)
        self.assertTrue(all(path1.points.reshape(-1) == points1))

        t_rot90 = t.create_transform(t.mat_rot_90)
        path2 = path1.transform(t_rot90)
        points2 = np.array([0, 0, 0, 10, -3, 10, -3, 15, 0, 15, 0, 25])
        self.assertTrue(all(path2.points.flatten() == points2))

        t_rot90_shift = t.create_transform(t.mat_shift(dx=e.length), t.mat_rot_90)
        path3 = path1.transform(t_rot90_shift)
        points3 = np.array([25, 0, 25, 10, 22, 10, 22, 15, 25, 15, 25, 25])
        self.assertTrue(all(path3.points.flatten() == points3))

    def test_path_concat_1(self):
        p1 = Path.zero()
        p2 = Path().add_point(1, 1)
        try:
            p1.concat(p2)
            self.fail("should not work")
        except ValueError as e:
            pass

    def test_remove_last(self):
        p1 = Path.zero()
        p1.line_to(2,2)
        p1.line_to(0, 2)
        self.assertTrue(all(np.array([0, 0, 2, 2, 0, 2]) == p1.points.flatten()), p1.points.flatten())
        p1.remove_last_line()
        self.assertTrue(all(np.array([0, 0, 2, 2]) == p1.points.flatten()), p1.points.flatten())

    def test_revese(self):
        p1 = Path.zero()
        p1.line_to(1,2)
        p1.line_to(3, 4)
        self.assertTrue(all(np.array([0., 0., 1., 2., 3., 4.]) == p1.points.flatten()), p1.points.flatten())
        p2 = p1.reverse()
        self.assertTrue(all(np.array([3., 4., 1., 2., 0., 0.]) == p2.points.flatten()), p2.points.flatten())
        self.assertTrue(all(np.array([3., 4., 1., 2., 0., 0.]) == line_list_to_points(p2.lines).flatten()), line_list_to_points(p2.lines).flatten())

        p1.reverse(copy=False)
        self.assertTrue(all(np.array([3., 4., 1., 2., 0., 0.]) == p1.points.flatten()), p1.points.flatten())
        self.assertTrue(all(np.array([3., 4., 1., 2., 0., 0.]) == line_list_to_points(p1.lines).flatten()), line_list_to_points(p1.lines).flatten())


    def test_closed(self):
        p1 = Path.zero()
        p1.line_to(2,2)
        p1.line_to(0, 2)
        self.assertFalse(p1.is_closed())
        p1.line_to(0, 0)
        self.assertTrue(p1.is_closed())
    
    def test_close(self):
        p1 = Path.zero().line_to(5,5).line_to(5, 0).close_path()
        self.assertTrue(p1.is_closed())

        p2 = Path().add_point(1,1).line_to(5,5).line_to(5, 0).close_path()
        self.assertTrue(p2.is_closed())

    def test_concat(self):
        p1 = Path.zero().line_to(5, 5).h_dim(Dim(5, "d1"))
        p2 = Path().add_point(10, 5).v_dim(Dim(-5, "d2")).line_to(12, -2)
        p3 = p1.concat(p2)
        self.assertTrue(all(np.array([0, 0, 5, 5, 10, 5, 10, 0, 12, -2]) == p3.points.flatten()), p3.points.flatten())
        line_points = line_list_to_points(p3.lines)
        self.assertTrue(all(np.array([0, 0, 5, 5, 10, 5, 10, 0, 12, -2]) == line_points.flatten()), line_points.flatten())

        self.assertEqual(p3.lines[1].dim, Dim(5, "d1"))
        self.assertEqual(p3.lines[2].dim, Dim(-5, "d2"))


    def test_path_concat(self):
        e1: Edge = Edge.as_length(Dim(10, "finger1"), Dim(2, "finger1_c"), Dim(5, "notch1"), Dim(1, "notch1_c"))
        e2: Edge = Edge.as_width(Dim(5, "finger2"), Dim(3, "finger2_c"), Dim(5, "notch"), Dim(2, "notch_c"))

        face =  Face(e1, e2, Dim(3, "thickness"), None)
        p = face.build_path()
        # todo test 
        print("hi")





def test_path_building():
    b = SimpleBox.eqaul_from_finger_count(
        length_finger_count=Dim(5, "length_finger_count", ""),
        width_finger_count=Dim(3, "width_finger_count", ""),
        height_finger_count=Dim(4, "height_finger", ""),
        finger_dim=10.0,
        thickness=Dim(3.0, name="thickness", unit="mm")
    )

    # for face in b.faces:
        # p = face.build_path()

    p = b.front_back.build_path()

    # return p
    print("hi")

if __name__ == "__main__":
    # unittest.main()
    p = test_path_building()
    # p2 = p.transform(reflect_on_x_axis)
    # # todo test transformation for lines and consstrains!

    print("hi")