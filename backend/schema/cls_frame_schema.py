from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class TableInfo:
    part_name: Optional[str] = None
    part_number: Optional[str] = None
    composite_part_number: Optional[str] = None
    primitive_part_number: Optional[str] = None
    original_body_id: Optional[str] = None
    cutlist_body_id: Optional[str] = None
    description: Optional[str] = None
    item: Optional[str] = None
    length: Optional[str] = None
    part_type: Optional[str] = None
    qty: int = 0
    original_name: Optional[str] = None

@dataclass
class DocumentInfo:
    documentId: Optional[str] = None
    elementId: Optional[str] = None
    wvmType: Optional[str] = None
    wvmId: Optional[str] = None
    configuration: Optional[str] = None

@dataclass
class FrameQuantities:
    bom_qty: int = 0
    cut_list_qty: int = 0
    total_qty: int = 0


@dataclass
class FrameBodyInfo:
    table_info: TableInfo = field(default_factory=TableInfo)
    document_info: DocumentInfo = field(default_factory=DocumentInfo)
    body: Optional[str] = None
    profile: Optional[str] = None
    href: Optional[str] = None
    cutting_part_number: Optional[str] = None
    file_name: Optional[str] = None
    assembly_string: Optional[str] = None
    quantities: FrameQuantities = field(default_factory=FrameQuantities)
    