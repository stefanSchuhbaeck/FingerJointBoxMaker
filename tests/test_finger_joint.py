import unittest

import sys
import os

sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../.."))
import numpy as np

from box.joint import SimpleBox
from box.geometry import Edge, EdgeTyp, Path
from box.dimension import Dim
from box.transform import reflect_on_x_axis


class TestFinger(unittest.TestCase):
    def setUp(self) -> None:
        self.e = Edge(
            finger=Dim(4),
            finger_count=Dim(10),
            notch=Dim(3),
            notch_count=Dim(5))
    
    def neg(self):
        return ( Dim(10), Dim(5), Dim(10), Dim(6))

    def pos(self):
        return ( Dim(10), Dim(6), Dim(10), Dim(5))

    def test_length(self):
        self.assertEqual(self.e.length, 4*10 + 3*5)
    
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



def test_path_building():
    b = SimpleBox.eqaul_from_finger_count(
        length_finger_count=Dim(5, "length_finger_count", ""),
        width_finger_count=Dim(3, "width_finger_count", ""),
        height_finger_count=Dim(4, "height_finger", ""),
        finger_dim=10.0,
        thickness=Dim(3.0, name="thickness", unit="mm")
    )
    p = b.build_face(b.faces[1])
    return p
    print(p)

if __name__ == "__main__":
    # unittest.main()
    p = test_path_building()
    p2 = p.transform(reflect_on_x_axis)
    # todo test transformation for lines and consstrains!

    print("hi")