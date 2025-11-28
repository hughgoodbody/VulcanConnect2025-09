from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ParentDocumentDetails:
    parent_document_name: Optional[str] = None
    parent_element_name: Optional[str] = None
    parent_documentId: Optional[str] = None
    parent_configuration: Optional[str] = None
    parent_wvmId: Optional[str] = None
    parent_wvmType: Optional[str] = None
    parent_url: Optional[str] = None
    parent_thumbnail: Optional[str] = None


@dataclass
class OrderInfo:
    order_id: Optional[str] = None
    order_prefix: Optional[str] = None
    order_reference: Optional[str] = None
    customer_reference: Optional[str] = None
    supplier: Optional[str] = None
    process: Optional[str] = None
    to_delete: Optional[bool] = None


@dataclass
class DXFInformation:
    dxf_file_name: Optional[str] = None
    process_on_drawing: Optional[str] = None
    process_suffix: Optional[str] = None
    notes: Optional[str] = None
    pd6: Optional[str] = None
    partdata18: Optional[str] = None


@dataclass
class Operations:
    operations_2: Optional[str] = None
    operations: Optional[str] = None
    bend_operation: Optional[str] = None
    tap_operation: Optional[str] = None
    drill_operation: Optional[str] = None
    etch_operation: Optional[str] = None


@dataclass
class ManufacturingInfo:
    undersize_holes: Optional[str] = None
    etch_part_number: Optional[str] = None
    drill_template: Optional[str] = None


@dataclass
class SheetMetal:
    bend_line_marks: Optional[str] = None
    has_sheet_metal_step: bool = False
    is_sheet_metal: bool = False
    flat_pattern_id: Optional[str] = None


@dataclass
class Quantities:
    bom_quantity: int = 0
    ui_quantity_multiplier: int = 1
    ui_additional_qty: int = 0
    total_quantity: int = 0
    cut_list_qty: int = 0
    composite_qty: int = 0


@dataclass
class PartDetails:
    documentId: Optional[str] = None
    elementId: Optional[str] = None
    created_version_id: Optional[str] = None
    wvmId: Optional[str] = None
    wvmType: Optional[str] = None
    partId: Optional[str] = None
    partName: Optional[str] = None
    partNumber: Optional[str] = None
    part_url: Optional[str] = None
    part_thumbnail: Optional[str] = None
    composite_part_id: Optional[str] = None
    is_part_of_cut_list: bool = False
    cut_list_qty: int = 0
    document_name: Optional[str] = None
    element_name: Optional[str] = None
    configuration: Optional[str] = None
    material: Optional[str] = None
    thickness: Optional[float] = None


@dataclass
class GeometryInfo:
    largest_face: Optional[str] = None
    thickness: Optional[float] = None
    area: Optional[float] = None
    origin: Optional[str] = None
    normal: Optional[str] = None
    edge_perimeter: Optional[float] = None
    longest_edge: Optional[str] = None
    view_matrix: Optional[str] = None
    description: Optional[str] = None
    box_min_corner: Optional[str] = None
    box_max_corner: Optional[str] = None
    faces: List[str] = field(default_factory=list)
    edges: List[str] = field(default_factory=list)


@dataclass
class Misc:
    contact_sheet: Optional[str] = None
    csv_file: Optional[str] = None
    onshape_upload: bool = False
    max_thickness: float = 1000
    to_remove: bool = False
    has_variation: bool = False
    hole_data: List[str] = field(default_factory=list)


@dataclass
class CutListOrComposite:
    body_of_composite_id: List[str] = field(default_factory=list)
    is_part_of_cut_list: bool = False
    is_constituent_of_composite: bool = False


@dataclass
class FoundPartsInformation:
    parent_document_details: ParentDocumentDetails = field(default_factory=ParentDocumentDetails)
    order_info: OrderInfo = field(default_factory=OrderInfo)
    dxf_information: DXFInformation = field(default_factory=DXFInformation)
    operations: Operations = field(default_factory=Operations)
    manufacturing_info: ManufacturingInfo = field(default_factory=ManufacturingInfo)
    sheet_metal: SheetMetal = field(default_factory=SheetMetal)
    quantities: Quantities = field(default_factory=Quantities)
    part_details: PartDetails = field(default_factory=PartDetails)
    geometry_info: GeometryInfo = field(default_factory=GeometryInfo)
    misc: Misc = field(default_factory=Misc)
    cut_list_or_composite: CutListOrComposite = field(default_factory=CutListOrComposite)
