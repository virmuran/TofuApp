# TofuApp/modules/process_design/data_adapter.py
"""
数据适配器 - 在 DataManager 和工艺设计模块之间转换数据
"""
from typing import List, Dict, Any, Optional
import traceback

from TofuApp.data_manager import DataManager

from .data_models import (
    MaterialProperty, UnifiedEquipment, MSDSDocument,
    ProcessProject, ProcessRoute
)


class DataAdapter:
    """数据适配器 - 连接 DataManager 和工艺设计模块"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    # ==================== 设备数据转换 ====================
    
    def get_all_equipment(self) -> List[UnifiedEquipment]:
        """从 DataManager 获取所有设备并转换为 UnifiedEquipment"""
        equipment_data = self.data_manager.get_equipment_data()
        equipment_list = []
        
        for eq_data in equipment_data:
            try:
                # 如果已经是 UnifiedEquipment 格式，直接转换
                if eq_data.get('_type') == 'UnifiedEquipment':
                    equipment = UnifiedEquipment.from_dict(eq_data)
                else:
                    # 否则使用兼容转换
                    equipment = UnifiedEquipment.from_data_manager(eq_data)
                
                equipment_list.append(equipment)
            except Exception as e:
                print(f"❌ 转换设备数据失败: {e}")
                traceback.print_exc()
        
        return equipment_list
    
    def save_equipment(self, equipment: UnifiedEquipment) -> bool:
        """保存设备到 DataManager"""
        try:
            # 转换为 DataManager 格式
            eq_data = equipment.to_data_manager_dict()
            
            # 保存到 DataManager
            return self.data_manager.add_equipment(eq_data)
        except Exception as e:
            print(f"❌ 保存设备失败: {e}")
            return False
    
    def update_equipment(self, equipment: UnifiedEquipment) -> bool:
        """更新设备"""
        try:
            eq_data = equipment.to_data_manager_dict()
            return self.data_manager.update_equipment(
                equipment.equipment_id, 
                eq_data
            )
        except Exception as e:
            print(f"❌ 更新设备失败: {e}")
            return False
    
    def get_equipment_by_id(self, equipment_id: str) -> Optional[UnifiedEquipment]:
        """根据ID获取设备"""
        eq_data = self.data_manager.get_equipment_by_id(equipment_id)
        if eq_data:
            return UnifiedEquipment.from_data_manager(eq_data)
        return None
    
    def get_equipment_by_code(self, equipment_code: str) -> Optional[UnifiedEquipment]:
        """根据编码获取设备"""
        eq_data = self.data_manager.get_equipment_by_unique_code(equipment_code)
        if eq_data:
            return UnifiedEquipment.from_data_manager(eq_data)
        return None
    
    # ==================== 物料数据转换 ====================
    
    def get_all_materials(self) -> List[MaterialProperty]:
        """获取所有物料"""
        materials_data = self.data_manager.get_materials()
        materials_list = []
        
        for mat_data in materials_data:
            try:
                if mat_data.get('_type') == 'MaterialProperty':
                    material = MaterialProperty.from_dict(mat_data)
                else:
                    material = MaterialProperty.from_data_manager(mat_data)
                
                materials_list.append(material)
            except Exception as e:
                print(f"❌ 转换物料数据失败: {e}")
        
        return materials_list
    
    def save_material(self, material: MaterialProperty) -> bool:
        """保存物料"""
        try:
            mat_data = material.to_dict()
            return self.data_manager.add_material(mat_data)
        except Exception as e:
            print(f"❌ 保存物料失败: {e}")
            return False
    
    def get_material_by_id(self, material_id: str) -> Optional[MaterialProperty]:
        """根据ID获取物料"""
        materials = self.get_all_materials()
        for material in materials:
            if material.material_id == material_id:
                return material
        return None
    
    # ==================== MSDS数据转换 ====================
    
    def get_all_msds(self) -> List[MSDSDocument]:
        """获取所有MSDS"""
        msds_data = self.data_manager.get_msds_documents()
        msds_list = []
        
        for msds_item in msds_data:
            try:
                if msds_item.get('_type') == 'MSDSDocument':
                    msds = MSDSDocument.from_dict(msds_item)
                else:
                    msds = MSDSDocument.from_data_manager(msds_item)
                
                msds_list.append(msds)
            except Exception as e:
                print(f"❌ 转换MSDS数据失败: {e}")
        
        return msds_list
    
    def save_msds(self, msds: MSDSDocument) -> bool:
        """保存MSDS"""
        try:
            msds_data = msds.to_dict()
            return self.data_manager.add_msds_document(msds_data)
        except Exception as e:
            print(f"❌ 保存MSDS失败: {e}")
            return False
    
    # ==================== 项目数据转换 ====================
    
    def get_all_projects(self) -> List[ProcessProject]:
        """获取所有项目"""
        projects_data = self.data_manager.get_projects()
        projects_list = []
        
        for proj_data in projects_data:
            try:
                if proj_data.get('_type') == 'ProcessProject':
                    project = ProcessProject.from_dict(proj_data)
                else:
                    project = ProcessProject.from_dict(proj_data)
                
                projects_list.append(project)
            except Exception as e:
                print(f"❌ 转换项目数据失败: {e}")
        
        return projects_list
    
    def save_project(self, project: ProcessProject) -> bool:
        """保存项目"""
        try:
            proj_data = project.to_dict()
            return self.data_manager.add_project(proj_data)
        except Exception as e:
            print(f"❌ 保存项目失败: {e}")
            return False
    
    # ==================== 数据统计 ====================
    
    def get_data_stats(self) -> Dict[str, int]:
        """获取数据统计"""
        return {
            'materials': len(self.get_all_materials()),
            'equipment': len(self.get_all_equipment()),
            'msds': len(self.get_all_msds()),
            'projects': len(self.get_all_projects())
        }