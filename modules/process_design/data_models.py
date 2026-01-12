# TofuApp/modules/process_design/data_models.py
"""
数据模型类 - 定义统一的数据结构
与主程序 DataManager 的数据格式兼容
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


@dataclass
class DataEntity:
    """所有数据实体的基类"""
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "unknown"
    updated_by: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于存储到 DataManager"""
        result = asdict(self)
        # 添加元类型信息，便于识别
        result['_type'] = self.__class__.__name__
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataEntity':
        """从字典创建实例"""
        # 移除 _type 字段
        data_copy = {k: v for k, v in data.items() if k != '_type'}
        return cls(**data_copy)


@dataclass
class MaterialProperty(DataEntity):
    """物料属性 - 与 DataManager 格式兼容"""
    material_id: str = ""
    name: str = ""
    cas_number: str = ""
    molecular_formula: str = ""
    molecular_weight: float = 0.0
    density: Optional[float] = None
    boiling_point: Optional[float] = None
    melting_point: Optional[float] = None
    flash_point: Optional[float] = None
    phase: str = ""
    hazard_class: str = ""
    notes: str = ""
    
    # 模块扩展数据
    module_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @classmethod
    def from_data_manager(cls, data: Dict[str, Any]) -> 'MaterialProperty':
        """从 DataManager 的数据格式创建"""
        # 转换字段名（如果需要）
        return cls(
            uid=data.get('uid', str(uuid.uuid4())),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            created_by=data.get('created_by', 'unknown'),
            updated_by=data.get('updated_by', 'unknown'),
            material_id=data.get('material_id', ''),
            name=data.get('name', ''),
            cas_number=data.get('cas_number', ''),
            molecular_formula=data.get('molecular_formula', ''),
            molecular_weight=float(data.get('molecular_weight', 0.0)),
            density=data.get('density'),
            boiling_point=data.get('boiling_point'),
            melting_point=data.get('melting_point'),
            flash_point=data.get('flash_point'),
            phase=data.get('phase', ''),
            hazard_class=data.get('hazard_class', ''),
            notes=data.get('notes', '')
        )


@dataclass
class UnifiedEquipment(DataEntity):
    """统一设备模型 - 与 DataManager 格式兼容"""
    equipment_id: str = ""  # 对应 DataManager 的 equipment_id
    name: str = ""
    equipment_type: str = ""
    unique_code: str = ""  # 对应 DataManager 的 unique_code
    model: str = ""
    manufacturer: str = ""
    
    # 技术参数（兼容 DataManager 的字段）
    design_pressure: float = 0.0
    design_temperature: float = 0.0
    capacity: str = ""
    specification: str = ""
    location: str = ""
    status: str = ""
    description: str = ""
    
    # 模块扩展数据
    module_extensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @classmethod
    def from_data_manager(cls, data: Dict[str, Any]) -> 'UnifiedEquipment':
        """从 DataManager 的设备数据创建"""
        return cls(
            uid=data.get('uid', str(uuid.uuid4())),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            created_by=data.get('created_by', 'unknown'),
            updated_by=data.get('updated_by', 'unknown'),
            equipment_id=data.get('equipment_id', ''),
            name=data.get('name', ''),
            equipment_type=data.get('type', ''),  # DataManager 使用 'type'
            unique_code=data.get('unique_code', ''),
            model=data.get('model', ''),
            manufacturer=data.get('manufacturer', ''),
            design_pressure=float(data.get('design_pressure', 0.0)),
            design_temperature=float(data.get('design_temperature', 0.0)),
            capacity=data.get('capacity', ''),
            specification=data.get('specification', ''),
            location=data.get('location', ''),
            status=data.get('status', ''),
            description=data.get('description', '')
        )
    
    def to_data_manager_dict(self) -> Dict[str, Any]:
        """转换为 DataManager 的格式"""
        return {
            'equipment_id': self.equipment_id,
            'name': self.name,
            'type': self.equipment_type,  # DataManager 使用 'type'
            'unique_code': self.unique_code,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'design_pressure': self.design_pressure,
            'design_temperature': self.design_temperature,
            'capacity': self.capacity,
            'specification': self.specification,
            'location': self.location,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'uid': self.uid,
            '_type': 'UnifiedEquipment'
        }


@dataclass
class MSDSDocument(DataEntity):
    """MSDS文档 - 与 DataManager 格式兼容"""
    msds_id: str = ""
    material_name: str = ""
    cas_number: str = ""
    supplier: str = ""
    version: str = ""
    effective_date: str = ""
    expiry_date: str = ""
    hazard_class: str = ""
    status: str = ""
    description: str = ""
    
    @classmethod
    def from_data_manager(cls, data: Dict[str, Any]) -> 'MSDSDocument':
        """从 DataManager 的 MSDS 数据创建"""
        return cls(
            uid=data.get('uid', str(uuid.uuid4())),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            created_by=data.get('created_by', 'unknown'),
            updated_by=data.get('updated_by', 'unknown'),
            msds_id=data.get('msds_id', ''),
            material_name=data.get('material_name', ''),
            cas_number=data.get('cas_number', ''),
            supplier=data.get('supplier', ''),
            version=data.get('version', ''),
            effective_date=data.get('effective_date', ''),
            expiry_date=data.get('expiry_date', ''),
            hazard_class=data.get('hazard_class', ''),
            status=data.get('status', ''),
            description=data.get('description', '')
        )


@dataclass
class ProcessProject(DataEntity):
    """工艺项目"""
    project_id: str = ""
    name: str = ""
    description: str = ""
    status: str = "planning"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    manager: str = ""
    members: List[str] = field(default_factory=list)


@dataclass
class ProcessRoute(DataEntity):
    """工艺路线"""
    route_id: str = ""
    name: str = ""
    product: str = ""
    description: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    notes: str = ""