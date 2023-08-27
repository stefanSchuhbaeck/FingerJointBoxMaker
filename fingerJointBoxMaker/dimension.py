from __future__ import annotations
from dataclasses import dataclass, field
from numpy import abs

class AbsDimHashKey:

    def __init__(self, dim: Dim) -> None:
        self.dim = dim

    def __hash__(self) -> int:
        return hash((self.dim.abs_value, self.dim.name, self.dim.unit))

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, AbsDimHashKey):
            return self.dim.abs_equal(__value.dim)
        return False
    
    def __str__(self) -> str:
        return f"AbsDimHashKey({self.dim})"
    
    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class Dim:
    value: float
    name: str  = ""
    unit: str = "mm"

    @property
    def is_paramter(self):
        """A named dimension is a paramter that will be added to user defined paramters.
            Only dimentions with a name can be used in a `DistanceDimentsion` constraint.
        """
        return " " in self.name        

    @property
    def int_value(self):
        return int(self.value)
    
    @property
    def abs_value(self):
        return abs(self.value)
    
    @property
    def abs_hash(self) -> AbsDimHashKey:
        return AbsDimHashKey(self)
    
    def same_unit(self, other:Dim):
        return self.unit == other.unit
    
    def abs_equal(self, other: Dim) -> bool:
        return self.abs_value == other.abs_value and self.name == other.name and self.unit == other.unit

    def expresion(self):
        if self.is_paramter:
            return self.name
        else:
            return f"{self.value} {self.unit}"
    
    def expresion_abs(self):
        if self.is_paramter:
            return self.name
        else:
            return f"{self.abs_value} {self.unit}"
    
    def new_relative(self, value, name, unit=None) -> Dim:
        return Dim(
            value=self.value + value,
            name = name, 
            unit= unit if unit is not None else self.unit
            )
    
    def new_with_name_prefix(self, value: float, name_prefix, unit=None) -> Dim:
        ret = Dim(
            value=value, 
            name=f"{name_prefix}_{self.name}", 
            unit= unit if unit is not None else self.unit
            )
        return ret

    def __assert_compatable(self, other, opt):
        if (isinstance(other, Dim) and self.unit == other.unit):
            return True
        raise TypeError(f"'{opt}' not supported between '{type(self)}' instance with missmatching units. {self.unit} != {other.unit} ")
    
    def _combine_names(self, other: Dim, opt):
        out = []
        if " " in self.name.strip():
            out.append(f"({self.name})")
        else:
            out.append(self.name)
        if " " in other.name.strip():
            out.append(f"({other.name})")
        else:
            out.append(other.name)
        return f" {opt} ".join(out)
    
    def __mul__(self, other) -> Dim:
        if isinstance(other, (int, float)):
            return Dim(self.value * other, self.name, self.unit) 
        elif self.__assert_compatable(other, "*"):
            return Dim(self.value * other.value, self._combine_names(other, "*"), self.unit)
        else:
            raise TypeError(f" '*' not supported between instances of 'Dim' and '{type(other)}' ")
    
    def __rmul__(self, other) -> Dim:
        if isinstance(other, (int, float)):
            return Dim(other * self.value, self.name, self.unit) 
        elif self.__assert_compatable(other, "*"):
            return Dim(other.value * self.value, other._combine_names(self, "*"), self.unit)
        else:
            raise TypeError(f" '*' not supported between instances of 'Dim' and '{type(other)}' ")
    
    def __truediv__(self, other) -> Dim:
        if isinstance(other, (int, float)):
            return Dim(self.value/other, self.name, self.unit)
        elif self.__assert_compatable(other, "/"):
            return Dim(self.value/other.value, self._combine_names(other, "/"), self.unit)
        else:
            raise TypeError(f" '/' not supported between instances of 'Dim' and '{type(other)}' ")

    def __rtruediv__(self, other) -> Dim:
        if isinstance(other, (int, float)):
            return Dim(other/self.value, self.name, self.unit)
        elif  self.__assert_compatable(other, "/"):
            return Dim(other.value/self.value, other._combine_names(self, "/"), self.unit)
        else:
            raise TypeError(f" '/' not supported between instances of 'Dim' and '{type(other)}' ")

    def div_by(self, val:int) -> Dim:
        d: Dim = self/val
        d.name = f"{d.name}/{val}"
        return d
    
    def __add__(self, other) -> Dim:
        if isinstance(other, (float, int)):
            return Dim(self.value + other, self.name, self.unit)
        elif self.__assert_compatable(other, "+"):
            return Dim(self.value + other.value, self._combine_names(other, "+"), "mm")
        else:
            raise TypeError(f" '+' not supported between instances of 'Dim' and '{type(other)}' ")
    
    def __radd__(self, other) -> Dim:
        if isinstance(other, (float, int)):
            return Dim(other + self.value, self.name, self.unit)
        elif self.__assert_compatable(other, "+"):
            return Dim(other.value + self.value, other._combine_names(self, "+"), "mm")
        else:
            raise TypeError(f" '+' not supported between instances of 'Dim' and '{type(other)}' ")

    def __sub__(self, other) -> Dim:
        if isinstance(other, (float, int)):
            return Dim(self.value - other, self.name, self.unit)
        elif self.__assert_compatable(other, "-"):
            return Dim(self.value - other.value, self._combine_names(other, "-"), self.unit)
        else:
            raise TypeError(f" '-' not supported between instances of '{type(self)}' and '{type(other)}' ")

    def __rsub__(self, other) -> Dim:
        if isinstance(other, (float, int)):
            return Dim(other - self.value, self.name, self.unit)
        elif self.__assert_compatable(other, "-"):
            return Dim(other.value - self.value, other._combine_names(self, "-"), self.unit)
        else:
            raise TypeError(f" '-' not supported between instances of '{type(self)}' and '{type(other)}' ")

    
    def __neg__(self):
        return self * -1
    
    def __int__(self):
        if isinstance(self.value, int):
            return self.value
        raise TypeError("Dim object does not wrap an integer") 
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (int, float)):
            return self.value == other
        elif isinstance(other, Dim):
            return self.value == other.value and self.name == other.name and self.unit == other.unit
        else:
            raise TypeError (f"'==' not supported between instances of '{type(self)}' and '{type(other)}'")
    
    def __gt__(self, other: object) -> bool:
        if isinstance(other, (float, int)):
            return self.value > other
        elif isinstance(other, Dim):
            return self.value > other.value
        else:
            raise TypeError (f"'>' not supported between instances of '{type(self)}' and '{type(other)}'")

    def __lt__(self, other: object) -> bool:
        if isinstance(other, (float, int)):
            return self.value < other
        elif isinstance(other, Dim):
            return self.value < other.value
        else:
            raise TypeError (f"'<' not supported between instances of '{type(self)}' and '{type(other)}'")

    def as_abs_tuple(self) -> tuple:
        return (self.abs_value, self.name, self.unit)
    
