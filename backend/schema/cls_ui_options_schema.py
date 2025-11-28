from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HoleOptions:
    ignore_thickness_diameter_ratio: bool = False
    etch_undersize_holes: bool = False
    drill_undersize_holes: bool = False


@dataclass
class UserOptions:
    etch_component_part_number: bool = False
    etch_bend_line_marks: bool = False
    create_contact_sheet: bool = True
    create_csv_file: bool = True
    upload_results_to_onshape: bool = False
    multiplier: int = 1
    max_thickness: float = 1000
    supplier: Optional[str] = None
    hole_options: HoleOptions = field(default_factory=HoleOptions)