# TofuApp/modules/process_design/process_design_widget.py
"""
工艺设计主部件 - 集成到主程序
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PySide6.QtCore import Qt
import traceback

# 导入工艺设计管理器
from .process_design_manager import global_process_design_manager

# 尝试从 tabs 包导入各个标签页
try:
    from .tabs import (
        EquipmentListTab, 
        ProcessFlowDiagramTab, 
        MaterialDatabaseTab,
        MSDSManagerTab,
        HeatBalanceTab,
        MassBalanceTab
    )
    print("✅ 成功从 tabs 模块导入所有标签页")
except ImportError as e:
    print(f"❌ 从 tabs 模块导入标签页失败: {e}")
    traceback.print_exc()
    
    # 设置各个标签页为 None
    EquipmentListTab = None
    ProcessFlowDiagramTab = None
    MaterialDatabaseTab = None
    MSDSManagerTab = None
    HeatBalanceTab = None
    MassBalanceTab = None


class ProcessDesignWidget(QWidget):
    """工艺设计模块主部件"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        # 使用全局工艺设计管理器
        self.data_manager = global_process_design_manager
        self.setup_ui()
        print("✅ ProcessDesignWidget 初始化完成")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 创建标签页
        self.create_tabs()
    
    def create_tabs(self):
        """创建各个标签页"""
        print("🔄 开始创建工艺设计标签页...")
        
        tabs_to_create = [
            ("⚙️ 设备清单", EquipmentListTab, "EquipmentListTab"),
            ("🎨 工艺流程图", ProcessFlowDiagramTab, "ProcessFlowDiagramTab"),
            ("🧪 物料数据库", MaterialDatabaseTab, "MaterialDatabaseTab"),
            ("📄 MSDS管理", MSDSManagerTab, "MSDSManagerTab"),
            ("🔥 热平衡", HeatBalanceTab, "HeatBalanceTab"),
            ("⚖️ 质量平衡", MassBalanceTab, "MassBalanceTab"),
        ]
        
        for tab_name, TabClass, class_name in tabs_to_create:
            if TabClass:
                try:
                    # 使用通用的创建方法
                    self.create_single_tab(tab_name, TabClass, class_name)
                except Exception as e:
                    print(f"❌ 创建{tab_name}标签页失败: {e}")
                    traceback.print_exc()
                    self.create_error_tab(tab_name, str(e))
            else:
                print(f"⚠️ {class_name} 不可用，跳过创建{tab_name}标签页")
                self.create_error_tab(tab_name, f"{class_name} 模块导入失败")
        
        print(f"📊 工艺设计模块标签页创建完成，共 {self.tab_widget.count()} 个标签页")
    
    def create_single_tab(self, display_name, TabClass, class_name):
        """通用方法创建单个标签页"""
        import inspect
        sig = inspect.signature(TabClass.__init__)
        params = list(sig.parameters.keys())
        
        if 'data_manager' in params and 'parent' in params:
            tab_instance = TabClass(data_manager=self.data_manager, parent=self)
        elif 'data_manager' in params:
            tab_instance = TabClass(data_manager=self.data_manager)
        elif 'parent' in params:
            tab_instance = TabClass(parent=self)
        else:
            tab_instance = TabClass()
        
        self.tab_widget.addTab(tab_instance, display_name)
        
        # 保存引用，方便后续调用方法
        attr_name = f"{class_name.lower().replace('tab', '')}_tab"
        setattr(self, attr_name, tab_instance)
        
        print(f"✅ 创建{display_name}标签页成功")
    
    def create_error_tab(self, tab_name, error_message):
        """创建错误标签页"""
        error_widget = QWidget()
        layout = QVBoxLayout(error_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        error_label = QLabel(f"{tab_name} 加载失败")
        error_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        layout.addWidget(error_label)
        
        detail_label = QLabel(error_message)
        detail_label.setStyleSheet("color: #666; font-size: 12px;")
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)
        
        self.tab_widget.addTab(error_widget, f"❌ {tab_name}")
    
    def save_data(self):
        """保存数据（保持接口兼容）"""
        success = True
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'save_data'):
                try:
                    if not widget.save_data():
                        success = False
                except Exception as e:
                    print(f"❌ 保存标签页{i}数据失败: {e}")
                    success = False
        return success
    
    def refresh(self):
        """刷新数据（保持接口兼容）"""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'refresh'):
                try:
                    widget.refresh()
                except Exception as e:
                    print(f"❌ 刷新标签页{i}数据失败: {e}")
    
    def on_activate(self):
        """模块激活时调用（保持接口兼容）"""
        # 可以在这里添加模块激活时的逻辑
        pass