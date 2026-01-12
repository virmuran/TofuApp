# TofuApp/modules/process_design/process_design_manager.py
"""
工艺设计管理器 - 基于主程序的 DataManager
"""
import sys
import os
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # TofuApp 根目录

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    print(f"📁 已添加根目录到路径: {root_dir}")

try:
    # 现在可以直接导入 data_manager
    from data_manager import DataManager
    print("✅ 成功导入 DataManager")
except ImportError as e:
    print(f"❌ 导入 DataManager 失败: {e}")
    print("尝试使用备用路径导入...")
    # 备用导入方案
    import importlib.util
    spec = importlib.util.spec_from_file_location("data_manager", os.path.join(root_dir, "data_manager.py"))
    if spec and spec.loader:
        data_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_manager_module)
        DataManager = data_manager_module.DataManager
        print("✅ 备用导入 DataManager 成功")
    else:
        raise

class ProcessDesignManager(QObject):
    """工艺设计管理器"""
    
    # 数据变更信号
    equipment_changed = Signal(str)  # equipment_id
    material_changed = Signal(str)   # material_id
    msds_changed = Signal(str)       # msds_id
    project_changed = Signal(str)    # project_id
    
    def __init__(self):
        super().__init__()
        # 获取主程序的 DataManager 实例
        self.main_data_manager = DataManager.get_instance()
        
        # 初始化演示数据
        self._init_demo_data()
        
        print("✅ ProcessDesignManager 初始化完成")
    
    def get_equipment_data(self):
        """获取设备数据（兼容方法）"""
        return self.get_all_equipment()
    
    def _init_demo_data(self):
        """初始化演示数据"""
        try:
            # 检查是否需要加载演示物料
            materials = self.get_all_materials()
            if not materials:
                self._load_demo_materials()
            
            # 检查是否需要加载演示设备
            equipment = self.get_all_equipment()
            if not equipment:
                self._load_demo_equipment()
                
        except Exception as e:
            print(f"❌ 初始化演示数据时出错: {e}")
    
    def _load_demo_materials(self):
        """加载演示物料数据"""
        try:
            demo_materials = [
                {
                    "material_id": "M-001",
                    "name": "甲醇",
                    "cas_number": "67-56-1",
                    "molecular_formula": "CH3OH",
                    "molecular_weight": 32.04,
                    "density": 0.791,
                    "boiling_point": 64.7,
                    "melting_point": -97.6,
                    "flash_point": 11,
                    "phase": "liquid",
                    "hazard_class": "易燃液体"
                },
                {
                    "material_id": "M-002",
                    "name": "水",
                    "cas_number": "7732-18-5",
                    "molecular_formula": "H2O",
                    "molecular_weight": 18.02,
                    "density": 1.0,
                    "boiling_point": 100.0,
                    "melting_point": 0.0,
                    "phase": "liquid",
                    "hazard_class": "无"
                },
                {
                    "material_id": "M-003",
                    "name": "二氧化碳",
                    "cas_number": "124-38-9",
                    "molecular_formula": "CO2",
                    "molecular_weight": 44.01,
                    "density": 1.98,
                    "boiling_point": -78.5,
                    "phase": "gas",
                    "hazard_class": "窒息性气体"
                }
            ]
            
            for material_data in demo_materials:
                self.main_data_manager.add_material(material_data)
            
            print(f"✅ 演示物料数据加载完成: {len(demo_materials)} 个物料")
            
        except Exception as e:
            print(f"❌ 加载演示物料数据失败: {e}")
    
    def _load_demo_equipment(self):
        """加载演示设备数据"""
        try:
            demo_equipment = [
                {
                    "equipment_id": "EQ-001",
                    "name": "反应器R-101",
                    "type": "reactor",
                    "unique_code": "R-101",
                    "model": "STR-1000",
                    "manufacturer": "ABC公司",
                    "design_pressure": 5.0,
                    "design_temperature": 250.0,
                    "capacity": "1000L",
                    "description": "甲醇合成反应器",
                    "status": "运行中"
                },
                {
                    "equipment_id": "EQ-002",
                    "name": "精馏塔C-101",
                    "type": "column",
                    "unique_code": "C-101",
                    "model": "DT-500",
                    "manufacturer": "XYZ公司",
                    "design_pressure": 0.5,
                    "design_temperature": 150.0,
                    "capacity": "500mm",
                    "description": "甲醇精馏塔",
                    "status": "运行中"
                },
            ]
            
            for equipment_data in demo_equipment:
                self.main_data_manager.add_equipment(equipment_data)
            
            print(f"✅ 演示设备数据加载完成: {len(demo_equipment)} 个设备")
            
        except Exception as e:
            print(f"❌ 加载演示设备数据失败: {e}")
    
    # ==================== 设备管理方法 ====================
    
    def get_all_equipment(self) -> List[Dict]:
        """获取所有设备"""
        return self.main_data_manager.get_equipment_data()
    
    def get_equipment_by_id(self, equipment_id: str) -> Optional[Dict]:
        """根据ID获取设备"""
        return self.main_data_manager.get_equipment_by_id(equipment_id)
    
    def get_equipment_by_code(self, equipment_code: str) -> Optional[Dict]:
        """根据编码获取设备"""
        return self.main_data_manager.get_equipment_by_unique_code(equipment_code)
    
    def save_equipment(self, equipment_data: Dict) -> bool:
        """保存设备"""
        success = self.main_data_manager.add_equipment(equipment_data)
        if success:
            self.equipment_changed.emit(equipment_data.get('equipment_id', ''))
        return success
    
    def update_equipment(self, equipment_id: str, update_data: Dict) -> bool:
        """更新设备"""
        success = self.main_data_manager.update_equipment(equipment_id, update_data)
        if success:
            self.equipment_changed.emit(equipment_id)
        return success
    
    def delete_equipment(self, equipment_id: str) -> bool:
        """删除设备"""
        success = self.main_data_manager.delete_equipment(equipment_id)
        if success:
            self.equipment_changed.emit(equipment_id)
        return success
    
    # ==================== 物料管理方法 ====================
    
    def get_all_materials(self) -> List[Dict]:
        """获取所有物料"""
        return self.main_data_manager.get_materials()
    
    def get_material_by_id(self, material_id: str) -> Optional[Dict]:
        """根据ID获取物料"""
        materials = self.get_all_materials()
        for material in materials:
            if material.get('material_id') == material_id:
                return material
        return None
    
    def save_material(self, material_data: Dict) -> bool:
        """保存物料"""
        success = self.main_data_manager.add_material(material_data)
        if success:
            self.material_changed.emit(material_data.get('material_id', ''))
        return success
    
    # ==================== MSDS管理方法 ====================
    
    def get_all_msds(self) -> List[Dict]:
        """获取所有MSDS"""
        return self.main_data_manager.get_msds_documents()
    
    def save_msds(self, msds_data: Dict) -> bool:
        """保存MSDS"""
        success = self.main_data_manager.add_msds_document(msds_data)
        if success:
            self.msds_changed.emit(msds_data.get('msds_id', ''))
        return success
    
    # ==================== 项目管理方法 ====================
    
    def get_all_projects(self) -> List[Dict]:
        """获取所有项目"""
        return self.main_data_manager.get_projects()
    
    def save_project(self, project_data: Dict) -> bool:
        """保存项目"""
        success = self.main_data_manager.add_project(project_data)
        if success:
            self.project_changed.emit(project_data.get('project_id', ''))
        return success
    
    # ==================== 数据统计 ====================
    
    def get_data_stats(self) -> Dict[str, int]:
        """获取数据统计"""
        return {
            'materials': len(self.get_all_materials()),
            'equipment': len(self.get_all_equipment()),
            'msds': len(self.get_all_msds()),
            'projects': len(self.get_all_projects())
        }
    
    def get_main_data_manager(self):
        """获取主 DataManager 实例"""
        return self.main_data_manager


# 全局管理器实例
global_process_design_manager = ProcessDesignManager()