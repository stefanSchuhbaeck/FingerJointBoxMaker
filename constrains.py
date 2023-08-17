from typing import Any, Protocol


class Constraint(Protocol):

    Coliniear = "coliniear"
    GeoDimension = "dim"
    Perpendicular = "perpendicualr"
    EqualConstraint = "EqualConstraint"
    Horizontal = "Horizontal"
    Vertical = "Vertical"
    CreatePoint = "createPoint"


    def get_name(self) -> str:
        ...

    def process(self, transform_F) -> Any:
        ...

