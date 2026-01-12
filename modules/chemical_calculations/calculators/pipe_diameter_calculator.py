from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog, QSpinBox, QButtonGroup, QGridLayout,
    QFileDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator
import math
import re
from datetime import datetime


class 管径计算(QWidget):
    """管道直径计算器 - 基于表格数据（统一UI风格版）"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.fluid_ranges = {}
        self.fluid_data = {}
        
        # 使用传入的数据管理器或创建新的
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            self.init_data_manager()
        
        self.setup_ui()
        self.setup_fluid_ranges()
        self.setup_fluid_options()
        self.setup_mode_dependencies()

    def init_data_manager(self):
        """初始化数据管理器 - 使用单例模式"""
        try:
            from data_manager import DataManager
            self.data_manager = DataManager.get_instance()
            print("使用共享的数据管理器实例")
        except Exception as e:
            print(f"数据管理器初始化失败: {e}")
            self.data_manager = None
    
    def setup_fluid_ranges(self):
        """根据化工管路设计手册表1.3-1设置流体对应的参数范围"""
        # 饱和蒸汽
        self.fluid_ranges["饱和蒸汽"] = {
            "DN>200": {"velocity": (30, 40), "flow": (0, 0), "pressure": (0, 12), "flow_unit": "t/h"},
            "100<DN<200": {"velocity": (25, 35), "flow": (0, 0), "pressure": (0, 12), "flow_unit": "t/h"},
            "DN<100": {"velocity": (15, 30), "flow": (0, 0), "pressure": (0, 12), "flow_unit": "t/h"},
            "P<1MPa": {"velocity": (15, 20), "flow": (0, 0), "pressure": (0, 1), "flow_unit": "t/h"},
            "1MPa<P<4MPa": {"velocity": (20, 40), "flow": (0, 0), "pressure": (1, 4), "flow_unit": "t/h"},
            "4MPa<P<12MPa": {"velocity": (40, 60), "flow": (0, 0), "pressure": (4, 12), "flow_unit": "t/h"}
        }
        
        # 过热蒸汽
        self.fluid_ranges["过热蒸汽"] = {
            "DN>200": {"velocity": (40, 60), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"},
            "100<DN<200": {"velocity": (30, 50), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"},
            "DN<100": {"velocity": (20, 40), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"}
        }
        
        # 二次蒸汽
        self.fluid_ranges["二次蒸汽"] = {
            "二次蒸汽受利用时": {"velocity": (15, 30), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"},
            "二次蒸汽不利用时": {"velocity": (60, 60), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"}
        }
        
        # 高压乏汽
        self.fluid_ranges["高压乏汽"] = {
            "高压乏汽": {"velocity": (80, 100), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"}
        }
        
        # 乏汽
        self.fluid_ranges["乏汽"] = {
            "排气管,从受压容器排出": {"velocity": (80, 80), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"},
            "从无压容器排出": {"velocity": (15, 30), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"}
        }
        
        # 压缩气体
        self.fluid_ranges["压缩气体"] = {
            "真空": {"velocity": (5, 10), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"},
            "P≤0.3MPa": {"velocity": (8, 12), "flow": (0, 0), "pressure": (0, 0.3), "flow_unit": "Nm³/h"},
            "P=0.3~0.6MPa": {"velocity": (10, 20), "flow": (0, 0), "pressure": (0.3, 0.6), "flow_unit": "Nm³/h"},
            "P=0.6~1MPa": {"velocity": (10, 15), "flow": (0, 0), "pressure": (0.6, 1), "flow_unit": "Nm³/h"},
            "P=1~2MPa": {"velocity": (8, 12), "flow": (0, 0), "pressure": (1, 2), "flow_unit": "Nm³/h"},
            "P=2~3MPa": {"velocity": (3, 8), "flow": (0, 0), "pressure": (2, 3), "flow_unit": "Nm³/h"},
            "P=3~30MPa": {"velocity": (0.5, 3), "flow": (0, 0), "pressure": (3, 30), "flow_unit": "Nm³/h"}
        }
        
        # 氧气
        self.fluid_ranges["氧气"] = {
            "P=0~0.05MPa": {"velocity": (5, 10), "flow": (0, 0), "pressure": (0, 0.05), "flow_unit": "Nm³/h"},
            "P=0.05~0.6MPa": {"velocity": (6, 8), "flow": (0, 0), "pressure": (0.05, 0.6), "flow_unit": "Nm³/h"},
            "P=0.6~1MPa": {"velocity": (4, 6), "flow": (0, 0), "pressure": (0.6, 1), "flow_unit": "Nm³/h"},
            "P=2~3MPa": {"velocity": (3, 4), "flow": (0, 0), "pressure": (2, 3), "flow_unit": "Nm³/h"}
        }
        
        # 煤气
        self.fluid_ranges["煤气"] = {
            "管道长50~100m": {"velocity": (0.75, 3), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"},
            "P≤0.027MPa": {"velocity": (8, 12), "flow": (0, 0), "pressure": (0, 0.027), "flow_unit": "Nm³/h"},
            "P≤0.27MPa": {"velocity": (3, 12), "flow": (0, 0), "pressure": (0, 0.27), "flow_unit": "Nm³/h"}
        }
        
        # 半水煤气
        self.fluid_ranges["半水煤气"] = {
            "P=0.1~0.15MPa": {"velocity": (10, 15), "flow": (0, 0), "pressure": (0.1, 0.15), "flow_unit": "Nm³/h"}
        }
        
        # 天然气
        self.fluid_ranges["天然气"] = {
            "天然气": {"velocity": (30, 30), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"}
        }
        
        # 烟道气
        self.fluid_ranges["烟道气"] = {
            "烟道内": {"velocity": (3, 6), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"}
        }
        
        # 石灰窑窑气
        self.fluid_ranges["石灰窑窑气"] = {
            "管道内": {"velocity": (3, 4), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"}
        }
        
        # 氮气
        self.fluid_ranges["氮气"] = {
            "P=5~10MPa": {"velocity": (2, 5), "flow": (0, 0), "pressure": (5, 10), "flow_unit": "Nm³/h"},
            "P=20~30MPa": {"velocity": (5, 10), "flow": (0, 0), "pressure": (20, 30), "flow_unit": "Nm³/h"}
        }
        
        # 氢氮混合气
        self.fluid_ranges["氢氮混合气"] = {
            "P=真空": {"velocity": (15, 25), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"},
            "P<0.3MPa": {"velocity": (8, 15), "flow": (0, 0), "pressure": (0, 0.3), "flow_unit": "Nm³/h"},
            "P<0.6MPa": {"velocity": (10, 20), "flow": (0, 0), "pressure": (0, 0.6), "flow_unit": "Nm³/h"},
            "P<2MPa": {"velocity": (3, 8), "flow": (0, 0), "pressure": (0, 2), "flow_unit": "Nm³/h"},
            "P=22~150MPa": {"velocity": (5, 6), "flow": (0, 0), "pressure": (22, 150), "flow_unit": "Nm³/h"}
        }
        
        # 氨气
        self.fluid_ranges["氨气"] = {
            "气体": {"velocity": (10, 25), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "Nm³/h"},
            "液体": {"velocity": (1.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"}
        }
        
        # 乙炔气
        self.fluid_ranges["乙炔气"] = {
            "P<0.15MPa": {"velocity": (4, 8), "flow": (0, 0), "pressure": (0, 0.15), "flow_unit": "Nm³/h"},
            "P<2.5MPa": {"velocity": (4, 4), "flow": (0, 0), "pressure": (0, 2.5), "flow_unit": "Nm³/h"}
        }
        
        # 乙烯气
        self.fluid_ranges["乙烯气"] = {
            "P<0.01MPa": {"velocity": (3, 4), "flow": (0, 0), "pressure": (0, 0.01), "flow_unit": "Nm³/h"}
        }
        
        # 水及粘度相似的液体
        self.fluid_ranges["水及粘度相似的液体"] = {
            "P=0.1~0.3MPa": {"velocity": (0.5, 2), "flow": (0, 0), "pressure": (0.1, 0.3), "flow_unit": "m³/h"},
            "P≤1MPa": {"velocity": (0.5, 3), "flow": (0, 0), "pressure": (0, 1), "flow_unit": "m³/h"},
            "P≤8MPa": {"velocity": (2, 3), "flow": (0, 0), "pressure": (0, 8), "flow_unit": "m³/h"},
            "P≤20~30MPa": {"velocity": (2, 3.5), "flow": (0, 0), "pressure": (20, 30), "flow_unit": "m³/h"},
            "往复式泵吸入管": {"velocity": (0.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "往复式泵排出管": {"velocity": (1, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "离心泵吸入管（常温）": {"velocity": (1.5, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "离心泵排出管（70~110℃）": {"velocity": (0.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "离心泵排出管": {"velocity": (1.5, 3), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "高压离心泵排出管": {"velocity": (3, 3.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "齿轮泵吸入管": {"velocity": (0, 1), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "齿轮泵排出管": {"velocity": (1, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 自来水
        self.fluid_ranges["自来水"] = {
            "主管P=0.3MPa": {"velocity": (1.5, 3.5), "flow": (0, 0), "pressure": (0.3, 0.3), "flow_unit": "m³/h"},
            "支管P=0.3MPa": {"velocity": (1, 1.5), "flow": (0, 0), "pressure": (0.3, 0.3), "flow_unit": "m³/h"}
        }
        
        # 锅炉给水
        self.fluid_ranges["锅炉给水"] = {
            "P>0.8MPa": {"velocity": (1.2, 3.5), "flow": (0, 0), "pressure": (0.8, 10), "flow_unit": "m³/h"}
        }
        
        # 蒸汽冷凝水
        self.fluid_ranges["蒸汽冷凝水"] = {
            "蒸汽冷凝水": {"velocity": (0.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 冷凝水
        self.fluid_ranges["冷凝水"] = {
            "自流": {"velocity": (0.2, 0.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 过热水
        self.fluid_ranges["过热水"] = {
            "过热水": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 海水，微碱水
        self.fluid_ranges["海水，微碱水"] = {
            "P<0.6MPa": {"velocity": (1.5, 2.5), "flow": (0, 0), "pressure": (0, 0.6), "flow_unit": "m³/h"}
        }
        
        # 粘度较大的液体
        self.fluid_ranges["粘度较大的液体"] = {
            "粘度0.05Pa·s DN25": {"velocity": (0.5, 0.9), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.05Pa·s DN50": {"velocity": (0.7, 1.0), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.05Pa·s DN100": {"velocity": (1.0, 1.6), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.1Pa·s DN25": {"velocity": (0.3, 0.6), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.1Pa·s DN50": {"velocity": (0.5, 0.7), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.1Pa·s DN100": {"velocity": (0.7, 1.0), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度0.1Pa·s DN200": {"velocity": (1.2, 1.6), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度1Pa·s DN25": {"velocity": (0.1, 0.2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度1Pa·s DN50": {"velocity": (0.16, 0.25), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度1Pa·s DN100": {"velocity": (0.25, 0.35), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "粘度1Pa·s DN200": {"velocity": (0.35, 0.55), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 液氨
        self.fluid_ranges["液氨"] = {
            "P=真空": {"velocity": (0.05, 0.3), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "t/h"},
            "P≤0.6MPa": {"velocity": (0.3, 0.8), "flow": (0, 0), "pressure": (0, 0.6), "flow_unit": "t/h"},
            "P≤2MPa": {"velocity": (0.8, 1.5), "flow": (0, 0), "pressure": (0, 2), "flow_unit": "t/h"}
        }
        
        # 氢氧化钠
        self.fluid_ranges["氢氧化钠"] = {
            "浓度0~30%": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "浓度30%~50%": {"velocity": (1.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "浓度50%~73%": {"velocity": (1.2, 1.2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 四氯化碳
        self.fluid_ranges["四氯化碳"] = {
            "浓度88%~93%（铅管）": {"velocity": (1.2, 1.2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "93%~100%（铬铁管、钢管）": {"velocity": (1.2, 1.2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 硫酸
        self.fluid_ranges["硫酸"] = {
            "硫酸": {"velocity": (1.2, 1.2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 盐酸
        self.fluid_ranges["盐酸"] = {
            "（衬胶管）": {"velocity": (1.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 氯化钠
        self.fluid_ranges["氯化钠"] = {
            "带有固体": {"velocity": (2, 4.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "无固体": {"velocity": (1.5, 1.5), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 排除废水
        self.fluid_ranges["排除废水"] = {
            "排除废水": {"velocity": (0.4, 0.8), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 泥状混合物
        self.fluid_ranges["泥状混合物"] = {
            "浓度15%": {"velocity": (2.5, 3), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "浓度25%": {"velocity": (3, 4), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"},
            "浓度65%": {"velocity": (2.5, 3), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 乙二醇
        self.fluid_ranges["乙二醇"] = {
            "乙二醇": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 苯乙烯
        self.fluid_ranges["苯乙烯"] = {
            "苯乙烯": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 二溴乙烯
        self.fluid_ranges["二溴乙烯"] = {
            "玻璃管": {"velocity": (1, 1), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 二氯乙烷
        self.fluid_ranges["二氯乙烷"] = {
            "二氯乙烷": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
        
        # 三氯乙烷
        self.fluid_ranges["三氯乙烷"] = {
            "三氯乙烷": {"velocity": (2, 2), "flow": (0, 0), "pressure": (0, 0), "flow_unit": "m³/h"}
        }
    
    def setup_ui(self):
        """设置UI界面 - 统一风格布局"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧：输入参数区域 (占2/3宽度)
        left_widget = QWidget()
        left_widget.setMaximumWidth(900)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        # 1. 说明文本
        description = QLabel(
            "根据流体类型和计算条件计算管道直径或流量，依据《化工管路设计手册》表1.3-1推荐值。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 计算模式选择
        mode_group = QGroupBox("计算模式")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        mode_layout = QHBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup(self)
        self.mode_buttons = {}
        
        modes = [
            ("由流量计算管径", "已知流量，计算合适管径"),
            ("由管径计算流量", "已知管径，计算最大流量")
        ]
        
        for i, (mode_name, tooltip) in enumerate(modes):
            btn = QPushButton(mode_name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setFixedWidth(180)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 8px;
                    text-align: center;
                    color: black;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                    color: green;
                }
            """)
            self.mode_button_group.addButton(btn, i)
            mode_layout.addWidget(btn)
            self.mode_buttons[mode_name] = btn
        
        # 默认选择第一个
        self.mode_buttons["由流量计算管径"].setChecked(True)
        self.mode_button_group.buttonClicked.connect(self.on_mode_button_clicked)
        
        mode_layout.addStretch()
        left_layout.addWidget(mode_group)
        
        # 3. 输入参数组 - 使用GridLayout实现整齐的布局
        input_group = QGroupBox("📥 输入参数")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        
        # 使用GridLayout确保整齐排列
        input_layout = QGridLayout(input_group)
        input_layout.setVerticalSpacing(12)
        input_layout.setHorizontalSpacing(10)
        
        # 标签样式 - 右对齐
        label_style = """
            QLabel {
                font-weight: bold;
                padding-right: 10px;
            }
        """
        
        # 输入框和下拉菜单的固定宽度
        input_width = 400
        combo_width = 250
        
        row = 0
        
        # 流体类型
        fluid_label = QLabel("流体类型:")
        fluid_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fluid_label.setStyleSheet(label_style)
        input_layout.addWidget(fluid_label, row, 0)
        
        self.fluid_combo = QComboBox()
        self.setup_fluid_options()
        self.fluid_combo.setFixedWidth(input_width)
        self.fluid_combo.currentTextChanged.connect(self.on_fluid_changed)
        input_layout.addWidget(self.fluid_combo, row, 1)
        
        # 流体选择不需要额外提示，留空
        self.fluid_hint = QLabel("")
        self.fluid_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.fluid_hint, row, 2)
        
        row += 1
        
        # 计算条件
        condition_label = QLabel("计算条件:")
        condition_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        condition_label.setStyleSheet(label_style)
        input_layout.addWidget(condition_label, row, 0)
        
        self.condition_combo = QComboBox()
        self.condition_combo.setFixedWidth(input_width)
        self.condition_combo.currentTextChanged.connect(self.on_condition_changed)
        input_layout.addWidget(self.condition_combo, row, 1)
        
        # 条件提示标签
        self.condition_hint = QLabel("选择流体后出现")
        self.condition_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.condition_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.condition_hint, row, 2)
        
        row += 1
        
        # 压力
        pressure_label = QLabel("压力 (MPa):")
        pressure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pressure_label.setStyleSheet(label_style)
        input_layout.addWidget(pressure_label, row, 0)
        
        self.pressure_input = QLineEdit()
        self.pressure_input.setPlaceholderText("例如: 0.9")
        self.pressure_input.setValidator(QDoubleValidator(0.0, 30.0, 2))
        self.pressure_input.setFixedWidth(input_width)
        input_layout.addWidget(self.pressure_input, row, 1)
        
        # 压力范围标签
        self.pressure_range_label = QLabel("")
        self.pressure_range_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        self.pressure_range_label.setFixedWidth(combo_width)
        input_layout.addWidget(self.pressure_range_label, row, 2)
        
        row += 1
        
        # 流速
        velocity_label = QLabel("流速 (m/s):")
        velocity_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        velocity_label.setStyleSheet(label_style)
        input_layout.addWidget(velocity_label, row, 0)
        
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("例如: 35")
        self.velocity_input.setValidator(QDoubleValidator(0.1, 100.0, 2))
        self.velocity_input.setFixedWidth(input_width)
        input_layout.addWidget(self.velocity_input, row, 1)
        
        # 流速范围标签
        self.velocity_range_label = QLabel("")
        self.velocity_range_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        self.velocity_range_label.setFixedWidth(combo_width)
        input_layout.addWidget(self.velocity_range_label, row, 2)
        
        row += 1
        
        # 推荐流速按钮行
        self.velocity_recommend_btn = QPushButton("📏 获取推荐流速")
        self.velocity_recommend_btn.setFixedWidth(combo_width)
        self.velocity_recommend_btn.clicked.connect(self.set_recommended_velocity)
        self.velocity_recommend_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        # 放在第1列，占据1列宽度
        input_layout.addWidget(self.velocity_recommend_btn, row, 1, 1, 1)
        
        # 空白的提示标签占据第2列
        self.velocity_button_hint = QLabel("")
        self.velocity_button_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.velocity_button_hint, row, 2)
        
        row += 1
        
        # 流量输入 - 流量计算管径模式
        self.flow_label = QLabel("流量:")
        self.flow_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.flow_label.setStyleSheet(label_style)
        input_layout.addWidget(self.flow_label, row, 0)
        
        self.flow_input = QLineEdit()
        self.flow_input.setPlaceholderText("例如: 100")
        self.flow_input.setValidator(QDoubleValidator(0.1, 10000.0, 2))
        self.flow_input.setFixedWidth(input_width)
        input_layout.addWidget(self.flow_input, row, 1)
        
        # 流量范围标签
        self.flow_range_label = QLabel("")
        self.flow_range_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        self.flow_range_label.setFixedWidth(combo_width)
        input_layout.addWidget(self.flow_range_label, row, 2)
        
        row += 1
        
        # 推荐流量按钮行
        self.flow_recommend_btn = QPushButton("📏 获取推荐流量")
        self.flow_recommend_btn.setFixedWidth(combo_width)
        self.flow_recommend_btn.clicked.connect(self.set_recommended_flow)
        self.flow_recommend_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        input_layout.addWidget(self.flow_recommend_btn, row, 1, 1, 1)
        
        # 空白的提示标签
        self.flow_button_hint = QLabel("")
        self.flow_button_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.flow_button_hint, row, 2)
        
        row += 1
        
        # 管径输入 - 管径计算流量模式
        self.diameter_label = QLabel("管道内径 (mm):")
        self.diameter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.diameter_label.setStyleSheet(label_style)
        input_layout.addWidget(self.diameter_label, row, 0)
        
        self.diameter_input = QLineEdit()
        self.diameter_input.setPlaceholderText("例如: 80")
        self.diameter_input.setValidator(QDoubleValidator(1.0, 2000.0, 1))
        self.diameter_input.setFixedWidth(input_width)
        input_layout.addWidget(self.diameter_input, row, 1)
        
        self.diameter_combo = QComboBox()
        self.setup_diameter_options()
        self.diameter_combo.setFixedWidth(combo_width)
        self.diameter_combo.currentTextChanged.connect(self.on_diameter_changed)
        input_layout.addWidget(self.diameter_combo, row, 2)
        
        row += 1
        
        # 密度显示
        density_label = QLabel("密度 (kg/m³):")
        density_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        density_label.setStyleSheet(label_style)
        input_layout.addWidget(density_label, row, 0)
        
        self.density_input = QLineEdit()
        self.density_input.setPlaceholderText("自动计算")
        self.density_input.setReadOnly(True)
        self.density_input.setFixedWidth(input_width)
        input_layout.addWidget(self.density_input, row, 1)
        
        # 密度提示标签
        self.density_hint = QLabel("根据流体自动计算")
        self.density_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.density_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.density_hint, row, 2)
        
        left_layout.addWidget(input_group)
        
        # 4. 计算按钮
        calculate_btn = QPushButton("🧮 开始计算")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.calculate)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        calculate_btn.setMinimumHeight(50)
        left_layout.addWidget(calculate_btn)
        
        # 5. 下载按钮布局
        download_layout = QHBoxLayout()
        download_txt_btn = QPushButton("📄 下载计算书(TXT)")
        download_txt_btn.clicked.connect(self.download_txt_report)
        download_txt_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)

        download_pdf_btn = QPushButton("📊 下载计算书(PDF)")
        download_pdf_btn.clicked.connect(self.generate_pdf_report)
        download_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        download_layout.addWidget(download_txt_btn)
        download_layout.addWidget(download_pdf_btn)
        left_layout.addLayout(download_layout)
        
        # 6. 在底部添加拉伸因子
        left_layout.addStretch()
        
        # 右侧：结果显示区域 (占1/3宽度)
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # 结果显示
        self.result_group = QGroupBox("📤 计算结果")
        self.result_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        result_layout = QVBoxLayout(self.result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 8px;
                background-color: #f8f9fa;
                min-height: 500px;
            }
        """)
        result_layout.addWidget(self.result_text)
        
        right_layout.addWidget(self.result_group)
        
        # 将左右两部分添加到主布局
        main_layout.addWidget(left_widget, 2)  # 左侧占2/3
        main_layout.addWidget(right_widget, 1)  # 右侧占1/3
        
        # 设置默认值
        self.set_default_values()
    
    def setup_mode_dependencies(self):
        """设置计算模式的依赖关系"""
        # 初始状态 - 由流量计算管径
        self.on_mode_changed("由流量计算管径")
    
    def on_mode_button_clicked(self, button):
        """处理计算模式按钮点击"""
        mode_text = button.text()
        self.on_mode_changed(mode_text)

    def get_current_mode(self):
        """获取当前选择的计算模式"""
        checked_button = self.mode_button_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return "由流量计算管径"  # 默认值
    
    def on_mode_changed(self, mode):
        """处理计算模式变化"""
        if mode == "由流量计算管径":
            # 显示流量输入，隐藏管径输入
            self.flow_label.setVisible(True)
            self.flow_input.setVisible(True)
            self.flow_range_label.setVisible(True)
            self.flow_recommend_btn.setVisible(True)
            self.flow_button_hint.setVisible(True)
            self.diameter_label.setVisible(False)
            self.diameter_input.setVisible(False)
            self.diameter_combo.setVisible(False)
        else:  # "由管径计算流量"
            # 显示管径输入，隐藏流量输入
            self.flow_label.setVisible(False)
            self.flow_input.setVisible(False)
            self.flow_range_label.setVisible(False)
            self.flow_recommend_btn.setVisible(False)
            self.flow_button_hint.setVisible(False)
            self.diameter_label.setVisible(True)
            self.diameter_input.setVisible(True)
            self.diameter_combo.setVisible(True)
    
    def setup_fluid_options(self):
        """设置流体选项"""
        # 更新流体选项列表
        fluid_options = [
            "- 请选择流体类型 -",  # 添加空选项
            "饱和蒸汽", "过热蒸汽", "二次蒸汽", "高压乏汽", "乏汽",
            "压缩气体", "氧气", "煤气", "半水煤气", "天然气", "烟道气", "石灰窑窑气",
            "氮气", "氢氮混合气", "氨气", "乙炔气", "乙烯气",
            "水及粘度相似的液体", "自来水", "锅炉给水", "蒸汽冷凝水", "冷凝水", "过热水",
            "海水，微碱水", "粘度较大的液体", "液氨", "氢氧化钠", "四氯化碳", "硫酸", "盐酸",
            "氯化钠", "排除废水", "泥状混合物", "乙二醇", "苯乙烯", "二溴乙烯", "二氯乙烷", "三氯乙烷"
        ]
        
        self.fluid_combo.clear()
        self.fluid_combo.addItems(fluid_options)
        
        # 设置流体数据字典（密度值）
        self.fluid_data = {
            # 蒸汽类
            "饱和蒸汽": 5.16,  # 0.9MPa(G)下的近似密度
            "过热蒸汽": 4.8,
            "二次蒸汽": 3.2,
            "高压乏汽": 6.5,
            "乏汽": 2.8,
            "压缩空气": 1.29,
            
            # 气体类 (20°C, 101.3kPa)
            "压缩气体": 1.29,
            "氧气": 1.43,
            "煤气": 0.6,
            "半水煤气": 0.75,
            "天然气": 0.7,
            "烟道气": 1.3,
            "石灰窑窑气": 1.35,
            "氮气": 1.25,
            "氢氮混合气": 0.3,
            "氨气": 0.77,
            "乙炔气": 1.17,
            "乙烯气": 1.26,
            
            # 液体类 (20°C)
            "水及粘度相似的液体": 1000,
            "自来水": 1000,
            "锅炉给水": 1000,
            "蒸汽冷凝水": 1000,
            "冷凝水": 1000,
            "过热水": 1000,
            "海水，微碱水": 1025,
            "粘度较大的液体": 1200,
            "液氨": 682,
            "氢氧化钠": 2130,
            "四氯化碳": 1594,
            "硫酸": 1830,
            "盐酸": 1200,
            "氯化钠": 2160,
            "排除废水": 1100,
            "泥状混合物": 1500,
            "乙二醇": 1115,
            "苯乙烯": 909,
            "二溴乙烯": 2179,
            "二氯乙烷": 1256,
            "三氯乙烷": 1320
        }
    
    def on_fluid_changed(self, text):
        """处理流体选择变化"""
        # 检查是否为空选项
        if text.startswith("-") or not text.strip():
            self.condition_combo.clear()
            self.condition_combo.addItem("- 请先选择流体类型 -")
            self.density_input.clear()
            self.velocity_range_label.setText("")
            self.pressure_range_label.setText("")
            self.flow_range_label.setText("")
            self.condition_hint.setText("选择流体后出现")
            return
            
        # 更新条件选项
        self.update_condition_options(text)
        
        # 更新密度
        self.update_density(text)
        
        # 更新提示
        self.condition_hint.setText("根据流体显示可选条件")
        
        # 更新参数范围和推荐值
        self.update_parameter_ranges()
    
    def update_condition_options(self, fluid):
        """根据流体更新条件选项"""
        self.condition_combo.blockSignals(True)  # 防止触发多次事件
        self.condition_combo.clear()
        
        # 添加空选项
        self.condition_combo.addItem("- 请选择计算条件 -")
        
        if fluid in self.fluid_ranges:
            conditions = list(self.fluid_ranges[fluid].keys())
            self.condition_combo.addItems(conditions)
        
        self.condition_combo.blockSignals(False)
    
    def update_density(self, fluid):
        """更新密度值"""
        if fluid in self.fluid_data:
            density = self.fluid_data[fluid]
            self.density_input.setText(f"{density:.2f}")
        else:
            self.density_input.setText("")
    
    def on_condition_changed(self, text):
        """处理条件变化 - 更新参数范围和推荐值"""
        # 检查是否为空选项
        if text.startswith("-") or not text.strip():
            self.velocity_range_label.setText("")
            self.pressure_range_label.setText("")
            self.flow_range_label.setText("")
            return
            
        if text:  # 确保不是空文本
            self.update_parameter_ranges()
            self.condition_hint.setText("已选择计算条件")
    
    def update_parameter_ranges(self):
        """更新参数范围和推荐值标签"""
        fluid = self.fluid_combo.currentText()
        condition = self.condition_combo.currentText()
        
        # 检查是否选择了空选项
        if fluid.startswith("-") or condition.startswith("-"):
            return
            
        if fluid in self.fluid_ranges and condition in self.fluid_ranges[fluid]:
            ranges = self.fluid_ranges[fluid][condition]
            
            # 更新流速范围标签（但不自动填入数值）
            vel_min, vel_max = ranges["velocity"]
            self.velocity_range_label.setText(f"推荐范围: {vel_min}~{vel_max} m/s")
            
            # 更新压力范围
            pressure_min, pressure_max = ranges["pressure"]
            if pressure_min == pressure_max and pressure_min > 0:
                self.pressure_range_label.setText(f"固定值: {pressure_min} MPa")
                self.pressure_input.setText(f"{pressure_min}")
                self.pressure_input.setReadOnly(True)
            elif pressure_min > 0 or pressure_max > 0:
                self.pressure_range_label.setText(f"适用范围: {pressure_min}~{pressure_max} MPa")
                self.pressure_input.setReadOnly(False)
            else:
                self.pressure_range_label.setText("")
                self.pressure_input.setReadOnly(False)
            
            # 更新流量标签和范围
            flow_unit = ranges["flow_unit"]
            self.flow_label.setText(f"流量 ({flow_unit}):")
            
            # 如果有流量范围，显示范围
            flow_min, flow_max = ranges["flow"]
            if flow_min > 0 or flow_max > 0:
                self.flow_range_label.setText(f"流量范围: {flow_min}~{flow_max} {flow_unit}")
            else:
                self.flow_range_label.setText("")
    
    def setup_diameter_options(self):
        """设置管道内径选项"""
        diameter_options = [
            "- 请选择管道内径 -",  # 添加空选项
            "6.0 mm - DN6 [1/8\"]",
            "7.8 mm - DN8 [1/4\"]", 
            "10.3 mm - DN10 [3/8\"]",
            "15.8 mm - DN15 [1/2\"]",
            "21.0 mm - DN20 [3/4\"]",
            "26.6 mm - DN25 [1.00\"]",
            "35.1 mm - DN32 [1.25\"]",
            "40.9 mm - DN40 [1.50\"]",
            "52.5 mm - DN50 [2.00\"]",
            "62.7 mm - DN65 [2.50\"]",
            "77.9 mm - DN80 [3.00\"]",
            "90.1 mm - DN90 [3.50\"]",
            "102.3 mm - DN100 [4.00\"]",
            "128.2 mm - DN125 [5.00\"]",
            "154.1 mm - DN150 [6.00\"]",
            "202.7 mm - DN200 [8.00\"]",
            "254.5 mm - DN250 [10.00\"]", 
            "303.3 mm - DN300 [12.00\"]"
        ]
        self.diameter_combo.addItems(diameter_options)
        # 设置默认值为空选项
        self.diameter_combo.setCurrentIndex(0)
    
    def on_diameter_changed(self, text):
        """处理直径选择变化"""
        # 检查是否为空选项
        if text.startswith("-") or not text.strip():
            self.diameter_input.clear()
            return
            
        try:
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                diameter_value = float(match.group(1))
                self.diameter_input.setText(f"{diameter_value}")
        except:
            pass
    
    def set_recommended_velocity(self):
        """设置推荐流速"""
        fluid = self.fluid_combo.currentText()
        condition = self.condition_combo.currentText()
        
        # 检查是否选择了空选项
        if fluid.startswith("-") or condition.startswith("-"):
            QMessageBox.warning(self, "选择错误", "请先选择流体类型和计算条件")
            return
            
        if fluid in self.fluid_ranges and condition in self.fluid_ranges[fluid]:
            vel_min, vel_max = self.fluid_ranges[fluid][condition]["velocity"]
            recommended = (vel_min + vel_max) / 2
            self.velocity_input.setText(f"{recommended:.2f}")
            self.velocity_range_label.setText(f"已设置推荐值: {recommended:.2f} m/s")
    
    def set_recommended_flow(self):
        """设置推荐流量"""
        fluid = self.fluid_combo.currentText()
        condition = self.condition_combo.currentText()
        
        # 检查是否选择了空选项
        if fluid.startswith("-") or condition.startswith("-"):
            QMessageBox.warning(self, "选择错误", "请先选择流体类型和计算条件")
            return
            
        if fluid in self.fluid_ranges and condition in self.fluid_ranges[fluid]:
            ranges = self.fluid_ranges[fluid][condition]
            flow_min, flow_max = ranges["flow"]
            
            # 如果有流量范围，设置推荐值
            if flow_min > 0 or flow_max > 0:
                recommended = (flow_min + flow_max) / 2
                self.flow_input.setText(f"{recommended:.1f}")
                self.flow_range_label.setText(f"已设置推荐值: {recommended:.1f} {ranges['flow_unit']}")
            else:
                QMessageBox.information(self, "提示", "当前条件下无推荐的流量范围")
    
    def set_default_values(self):
        """设置默认值"""
        # 初始化下拉框默认选项
        self.fluid_combo.setCurrentIndex(0)  # 请选择流体类型
        self.diameter_combo.setCurrentIndex(0)  # 请选择管道内径
    
    def calculate(self):
        """执行计算"""
        try:
            # 获取当前模式
            mode = self.get_current_mode()
            
            # 获取输入参数
            fluid = self.fluid_combo.currentText()
            condition = self.condition_combo.currentText()
            
            # 验证流体选择
            if fluid.startswith("-") or not fluid.strip():
                QMessageBox.warning(self, "选择错误", "请选择流体类型")
                return
            
            # 验证计算条件选择
            if condition.startswith("-") or not condition.strip():
                QMessageBox.warning(self, "选择错误", "请选择计算条件")
                return
            
            # 获取数值输入
            pressure_text = self.pressure_input.text()
            velocity_text = self.velocity_input.text()
            density_text = self.density_input.text()
            
            # 验证数值输入
            if not velocity_text:
                QMessageBox.warning(self, "输入错误", "请输入流速")
                return
            
            velocity = float(velocity_text)
            
            # 设置默认值用于计算
            pressure = 0.0
            if pressure_text:
                pressure = float(pressure_text)
            
            density = 1000.0  # 默认密度
            if density_text:
                density = float(density_text)
            
            # 验证参数范围
            self.validate_parameters(fluid, condition, velocity, pressure)
            
            if mode == "由流量计算管径":
                # 由流量计算管径
                flow_text = self.flow_input.text()
                if not flow_text:
                    QMessageBox.warning(self, "输入错误", "请输入流量")
                    return
                
                flow_rate = float(flow_text)
                diameter_mm = self.calculate_diameter_from_flow(flow_rate, velocity, density, fluid, condition)
                self.show_diameter_result(fluid, condition, flow_rate, velocity, 
                                        diameter_mm, density, pressure, mode)
            else:
                # 由管径计算流量
                diameter_mm = float(self.diameter_input.text() or 0)
                if not diameter_mm:
                    QMessageBox.warning(self, "输入错误", "请输入管道内径")
                    return
                
                flow_rate = self.calculate_flow_from_diameter(diameter_mm, velocity, density, fluid, condition)
                self.show_flow_result(fluid, condition, diameter_mm, velocity, 
                                    flow_rate, density, pressure, mode)
                
        except ValueError as e:
            QMessageBox.critical(self, "输入错误", f"参数格式错误: {str(e)}")
        except ZeroDivisionError:
            QMessageBox.critical(self, "计算错误", "密度或流速不能为零")
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def validate_parameters(self, fluid, condition, velocity, pressure):
        """验证参数是否在推荐范围内"""
        if fluid in self.fluid_ranges and condition in self.fluid_ranges[fluid]:
            ranges = self.fluid_ranges[fluid][condition]
            
            # 验证流速
            vel_min, vel_max = ranges["velocity"]
            if velocity < vel_min or velocity > vel_max:
                QMessageBox.warning(self, "输入警告", 
                                  f"当前流速 {velocity} m/s 不在推荐范围内 ({vel_min}~{vel_max} m/s)")
            
            # 验证压力
            pressure_min, pressure_max = ranges["pressure"]
            if pressure_min > 0 and (pressure < pressure_min or pressure > pressure_max):
                QMessageBox.warning(self, "输入警告", 
                                  f"当前压力 {pressure} MPa 不在推荐范围内 ({pressure_min}~{pressure_max} MPa)")
    
    def calculate_diameter_from_flow(self, flow_rate, velocity, density, fluid, condition):
        """由流量计算管径，使用手册公式"""
        # 获取流量单位
        flow_unit = self.fluid_ranges[fluid][condition]["flow_unit"]
        
        # 将流量转换为kg/h
        if flow_unit == "t/h":
            W = flow_rate * 1000  # t/h → kg/h
        elif flow_unit == "m³/h":
            W = flow_rate * density  # m³/h → kg/h
        elif flow_unit == "Nm³/h":
            # 对于压缩空气，1 Nm³ = 1.293 kg
            W = flow_rate * 1.293  # Nm³/h → kg/h
        else:
            W = flow_rate * 1000  # 默认按t/h处理
        
        # 使用手册公式计算管径
        diameter_mm = 18.81 * (W ** 0.5) * (velocity ** -0.5) * (density ** -0.5)
        return diameter_mm
    
    def calculate_flow_from_diameter(self, diameter_mm, velocity, density, fluid, condition):
        """由管径计算流量，使用手册公式"""
        # 获取流量单位
        flow_unit = self.fluid_ranges[fluid][condition]["flow_unit"]
        
        # 使用手册公式反推质量流量 (kg/h)
        W = (diameter_mm / 18.81) ** 2 * velocity * density
        
        # 根据流量单位转换
        if flow_unit == "t/h":
            flow_rate = W / 1000  # kg/h → t/h
        elif flow_unit == "m³/h":
            flow_rate = W / density  # kg/h → m³/h
        elif flow_unit == "Nm³/h":
            # 对于压缩空气，1 Nm³ = 1.293 kg
            flow_rate = W / 1.293  # kg/h → Nm³/h
        else:
            flow_rate = W / 1000  # 默认按t/h处理
        
        return flow_rate
    
    def show_diameter_result(self, fluid, condition, flow_rate, velocity, diameter_mm, density, pressure, mode):
        """显示管径计算结果"""
        # 获取流量单位
        flow_unit = self.fluid_ranges[fluid][condition]["flow_unit"]
        
        # 将流量转换为kg/h用于公式显示
        if flow_unit == "t/h":
            W = flow_rate * 1000
        elif flow_unit == "m³/h":
            W = flow_rate * density
        elif flow_unit == "Nm³/h":
            W = flow_rate * 1.293
        else:
            W = flow_rate * 1000
        
        # 推荐标准管径
        standard_diameters = [6, 8, 10, 15, 20, 25, 32, 40, 50, 65, 80, 100, 
                            125, 150, 200, 250, 300, 350, 400, 450, 500]
        
        # 找到最接近的标准管径
        closest_diam = min(standard_diameters, key=lambda x: abs(x - diameter_mm))
        
        result = f"""═══════════
📋 输入参数
══════════

    计算模式: {mode}
    流体类型: {fluid}
    计算条件: {condition}
    压力: {pressure} MPa(G)
    流量: {flow_rate} {flow_unit}
    流速: {velocity} m/s
    密度: {density:.2f} kg/m³

══════════
📊 计算结果
══════════

    理论计算管径: {diameter_mm:.1f} mm

    推荐标准管径: DN{closest_diam}
    • 实际流速: {self.calculate_actual_velocity(flow_rate, closest_diam, density, fluid, condition):.2f} m/s

══════════
🧮 计算公式 (HG/T 20570.6—1995)
══════════

    d = 18.81 × W^0.5 × u^-0.5 × ρ^-0.5

    其中:
    d = 管道内径, mm
    W = 质量流量 = {W:.0f} kg/h
    u = 流速 = {velocity} m/s
    ρ = 密度 = {density:.2f} kg/m³

    计算过程:
    d = 18.81 × ({W:.0f}^0.5) × ({velocity}^-0.5) × ({density:.2f}^-0.5)
    = 18.81 × {W**0.5:.2f} × {velocity**-0.5:.4f} × {density**-0.5:.4f}
    = {diameter_mm:.1f} mm

══════════
💡 工程建议
══════════

    • 推荐使用标准管径 DN{closest_diam}
    • 考虑管道材质、压力等级和安装条件
    • 计算结果仅供参考，实际选择需考虑具体工况"""
        
        self.result_text.setText(result)
    
    def show_flow_result(self, fluid, condition, diameter_mm, velocity, flow_rate, density, pressure, mode):
        """显示流量计算结果"""
        # 获取流量单位
        flow_unit = self.fluid_ranges[fluid][condition]["flow_unit"]
        
        # 将流量转换为kg/h用于公式显示
        if flow_unit == "t/h":
            W = flow_rate * 1000
        elif flow_unit == "m³/h":
            W = flow_rate * density
        elif flow_unit == "Nm³/h":
            W = flow_rate * 1.293
        else:
            W = flow_rate * 1000
        
        result = f"""══════════
📋 输入参数
══════════

    计算模式: {mode}
    流体类型: {fluid}
    计算条件: {condition}
    压力: {pressure} MPa(G)
    管道内径: {diameter_mm} mm
    流速: {velocity} m/s
    密度: {density:.2f} kg/m³

══════════
📊 计算结果
══════════

    理论计算流量:
    • {flow_rate:.2f} {flow_unit}"""

    # 根据流量单位显示不同的转换
        if flow_unit == "t/h":
            result += f"""
    • {flow_rate * 1000:.0f} kg/h
    • {flow_rate * 1000 / 3600:.2f} kg/s"""
        elif flow_unit == "m³/h":
            result += f"""
    • {flow_rate * 1000:.0f} L/h
    • {flow_rate / 3600:.4f} m³/s"""
        elif flow_unit == "Nm³/h":
            result += f"""
    • {flow_rate * 1.293:.0f} kg/h
    • {flow_rate * 1.293 / 3600:.2f} kg/s"""

        result += f"""

══════════
🧮 计算公式 (HG/T 20570.6—1995)
══════════

    由管径计算流量的反推公式:
    W = (d / 18.81)^2 × u × ρ

    其中:
    d = 管道内径 = {diameter_mm} mm
    u = 流速 = {velocity} m/s
    ρ = 密度 = {density:.2f} kg/m³
    W = 质量流量, kg/h

    计算过程:
    W = ({diameter_mm} / 18.81)^2 × {velocity} × {density:.2f}
    = {diameter_mm/18.81:.2f}^2 × {velocity} × {density:.2f}
    = {(diameter_mm/18.81)**2:.2f} × {velocity} × {density:.2f}
    = {W:.0f} kg/h
    = {flow_rate:.2f} {flow_unit}

══════════
💡 工程建议
══════════

    • 当前流速和流量在推荐范围内
    • 根据实际流量需求调整管道尺寸或流速
    • 计算结果仅供参考，实际应用请考虑安全系数"""
        
        self.result_text.setText(result)
    
    def calculate_actual_velocity(self, flow_rate, diameter_mm, density, fluid, condition):
        """计算实际流速"""
        # 获取流量单位
        flow_unit = self.fluid_ranges[fluid][condition]["flow_unit"]
        
        # 将流量转换为kg/s
        if flow_unit == "t/h":
            flow_kg_s = flow_rate * 1000 / 3600  # t/h → kg/s
        elif flow_unit == "m³/h":
            flow_kg_s = flow_rate * density / 3600  # m³/h → kg/s
        elif flow_unit == "Nm³/h":
            # 对于压缩空气，Nm³/h需要转换为kg/s
            flow_kg_s = flow_rate * 1.293 / 3600
        else:
            flow_kg_s = flow_rate * 1000 / 3600  # 默认按t/h处理
        
        area = math.pi * ((diameter_mm / 1000) / 2) ** 2
        return flow_kg_s / (density * area)
    
    def get_project_info(self):
        """获取工程信息 - 使用共享的项目信息"""
        try:
            from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                        QLineEdit, QPushButton, QDialogButtonBox)
            
            class ProjectInfoDialog(QDialog):
                def __init__(self, parent=None, default_info=None, report_number=""):
                    super().__init__(parent)
                    self.default_info = default_info or {}
                    self.report_number = report_number
                    self.setWindowTitle("工程信息")
                    self.setFixedSize(400, 350)
                    self.setup_ui()
                    
                def setup_ui(self):
                    layout = QVBoxLayout(self)
                    
                    # 标题
                    title_label = QLabel("请输入工程信息")
                    title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
                    layout.addWidget(title_label)
                    
                    # 公司名称
                    company_layout = QHBoxLayout()
                    company_label = QLabel("公司名称:")
                    company_label.setFixedWidth(80)
                    self.company_input = QLineEdit()
                    self.company_input.setPlaceholderText("例如：XX建筑工程有限公司")
                    self.company_input.setText(self.default_info.get('company_name', ''))
                    company_layout.addWidget(company_label)
                    company_layout.addWidget(self.company_input)
                    layout.addLayout(company_layout)
                    
                    # 工程编号
                    number_layout = QHBoxLayout()
                    number_label = QLabel("工程编号:")
                    number_label.setFixedWidth(80)
                    self.project_number_input = QLineEdit()
                    self.project_number_input.setPlaceholderText("例如：2024-PD-001")
                    self.project_number_input.setText(self.default_info.get('project_number', ''))
                    number_layout.addWidget(number_label)
                    number_layout.addWidget(self.project_number_input)
                    layout.addLayout(number_layout)
                    
                    # 工程名称
                    project_layout = QHBoxLayout()
                    project_label = QLabel("工程名称:")
                    project_label.setFixedWidth(80)
                    self.project_input = QLineEdit()
                    self.project_input.setPlaceholderText("例如：化工厂管道系统")
                    self.project_input.setText(self.default_info.get('project_name', ''))
                    project_layout.addWidget(project_label)
                    project_layout.addWidget(self.project_input)
                    layout.addLayout(project_layout)
                    
                    # 子项名称
                    subproject_layout = QHBoxLayout()
                    subproject_label = QLabel("子项名称:")
                    subproject_label.setFixedWidth(80)
                    self.subproject_input = QLineEdit()
                    self.subproject_input.setPlaceholderText("例如：主生产区管道")
                    self.subproject_input.setText(self.default_info.get('subproject_name', ''))
                    subproject_layout.addWidget(subproject_label)
                    subproject_layout.addWidget(self.subproject_input)
                    layout.addLayout(subproject_layout)
                    
                    # 计算书编号
                    report_number_layout = QHBoxLayout()
                    report_number_label = QLabel("计算书编号:")
                    report_number_label.setFixedWidth(80)
                    self.report_number_input = QLineEdit()
                    self.report_number_input.setText(self.report_number)
                    report_number_layout.addWidget(report_number_label)
                    report_number_layout.addWidget(self.report_number_input)
                    layout.addLayout(report_number_layout)
                    
                    # 按钮
                    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    button_box.accepted.connect(self.accept)
                    button_box.rejected.connect(self.reject)
                    layout.addWidget(button_box)
                    
                def get_info(self):
                    return {
                        'company_name': self.company_input.text().strip(),
                        'project_number': self.project_number_input.text().strip(),
                        'project_name': self.project_input.text().strip(),
                        'subproject_name': self.subproject_input.text().strip(),
                        'report_number': self.report_number_input.text().strip()
                    }
            
            # 从数据管理器获取共享的项目信息
            saved_info = {}
            if self.data_manager:
                saved_info = self.data_manager.get_project_info()
            
            # 获取下一个报告编号
            report_number = ""
            if self.data_manager:
                report_number = self.data_manager.get_next_report_number("PD")
            
            dialog = ProjectInfoDialog(self, saved_info, report_number)
            if dialog.exec() == QDialog.Accepted:
                info = dialog.get_info()
                # 验证必填字段
                if not info['company_name']:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "输入错误", "公司名称不能为空")
                    return self.get_project_info()  # 重新弹出对话框
                
                # 保存项目信息到数据管理器
                if self.data_manager:
                    # 只保存项目信息，不保存报告编号
                    info_to_save = {
                        'company_name': info['company_name'],
                        'project_number': info['project_number'],
                        'project_name': info['project_name'],
                        'subproject_name': info['subproject_name']
                    }
                    self.data_manager.update_project_info(info_to_save)
                    print("项目信息已保存")
                
                return info
            else:
                return None  # 用户取消了
                
        except Exception as e:
            print(f"获取工程信息失败: {e}")
            return None
    
    def generate_report(self):
        """生成计算书"""
        try:
            # 获取当前结果文本
            result_text = self.result_text.toPlainText()
            
            # 更宽松的检查条件：只要结果文本不为空且包含计算结果的关键字
            if not result_text or ("计算结果" not in result_text and "理论计算管径" not in result_text and "理论计算流量" not in result_text):
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            # 获取工程信息
            project_info = self.get_project_info()
            if not project_info:
                return None  # 用户取消了输入
            
            # 添加报告头信息
            report = f"""工程计算书 - 管道直径计算
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
计算工具: TofuSoft 工程计算模块
========================================

"""
            report += result_text
            
            # 添加工程信息部分
            report += f"""══════════
📋 工程信息
══════════

    公司名称: {project_info['company_name']}
    工程编号: {project_info['project_number']}
    工程名称: {project_info['project_name']}
    子项名称: {project_info['subproject_name']}
    计算日期: {datetime.now().strftime('%Y-%m-%d')}

══════════
🏷️ 计算书标识
══════════

    计算书编号: {project_info['report_number']}
    版本: 1.0
    状态: 正式计算书

══════════
📝 备注说明
══════════

    1. 本计算书基于《化工管路设计手册》及相关标准规范
    2. 计算结果仅供参考，实际应用需考虑安全系数
    3. 重要工程参数应经专业工程师审核确认
    4. 计算条件变更时应重新进行计算

---
生成于 TofuSoft 工程计算模块
"""
            return report
            
        except Exception as e:
            print(f"生成计算书失败: {e}")
            return None
    
    def download_txt_report(self):
        """下载TXT格式计算书"""
        try:
            import os
                
            # 直接调用 generate_report，它内部会进行检查
            report_content = self.generate_report()
            if report_content is None:  # 如果返回None，说明检查失败或用户取消
                return
                    
            # 选择保存路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"管道直径计算书_{timestamp}.txt"
            # 使用顶部导入的 QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存计算书", default_name, "Text Files (*.txt)"
            )
                
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "下载成功", f"计算书已保存到:\n{file_path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"保存计算书时发生错误: {str(e)}")
    
    def generate_pdf_report(self):
        """生成PDF格式计算书"""
        try:
            # 直接调用 generate_report，它内部会进行检查
            report_content = self.generate_report()
            if report_content is None:  # 如果返回None，说明检查失败或用户取消
                return False
                    
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"管道直径计算书_{timestamp}.pdf"
            # 使用顶部导入的 QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存PDF计算书", default_name, "PDF Files (*.pdf)"
            )
                
            if not file_path:
                return False
                
            # 尝试导入reportlab
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.units import inch
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                import os
                
                # 注册中文字体
                try:
                    # 尝试注册常见的中文字体
                    font_paths = [
                        # Windows 字体路径
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                        # macOS 字体路径
                        "/Library/Fonts/Arial Unicode.ttf",
                        "/System/Library/Fonts/Arial.ttf",
                        # Linux 字体路径
                        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                    ]
                    
                    chinese_font_registered = False
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            try:
                                if "simhei" in font_path.lower():
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                                    chinese_font_registered = True
                                    break
                                elif "simsun" in font_path.lower():
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                                    chinese_font_registered = True
                                    break
                                elif "msyh" in font_path.lower() or "microsoftyahei" in font_path.lower():
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                                    chinese_font_registered = True
                                    break
                                elif "arial unicode" in font_path.lower():
                                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                                    chinese_font_registered = True
                                    break
                            except:
                                continue
                    
                    if not chinese_font_registered:
                        # 如果没有找到系统字体，尝试使用 ReportLab 的默认字体（可能不支持中文）
                        pdfmetrics.registerFont(TTFont('ChineseFont', 'Helvetica'))
                except:
                    # 字体注册失败，使用默认字体
                    pass
                
                # 创建PDF文档
                doc = SimpleDocTemplate(file_path, pagesize=A4)
                styles = getSampleStyleSheet()
                
                # 创建支持中文的样式
                chinese_style_normal = ParagraphStyle(
                    'ChineseNormal',
                    parent=styles['Normal'],
                    fontName='ChineseFont',
                    fontSize=10,
                    leading=14,
                )
                
                chinese_style_heading = ParagraphStyle(
                    'ChineseHeading',
                    parent=styles['Heading1'],
                    fontName='ChineseFont',
                    fontSize=16,
                    leading=20,
                    spaceAfter=12,
                )
                
                story = []
                
                # 添加标题
                title = Paragraph("工程计算书 - 管道直径计算", chinese_style_heading)
                story.append(title)
                story.append(Spacer(1, 0.2*inch))
                
                # 处理报告内容，替换特殊字符和表情
                processed_content = self.process_content_for_pdf(report_content)
                
                # 添加内容
                for line in processed_content.split('\n'):
                    if line.strip():
                        # 处理特殊字符和空格
                        line = line.replace(' ', '&nbsp;')
                        line = line.replace('═', '=').replace('─', '-')
                        para = Paragraph(line, chinese_style_normal)
                        story.append(para)
                        story.append(Spacer(1, 0.05*inch))
                
                # 生成PDF
                doc.build(story)
                QMessageBox.information(self, "生成成功", f"PDF计算书已保存到:\n{file_path}")
                return True
                
            except ImportError:
                QMessageBox.warning(
                    self, 
                    "功能不可用", 
                    "PDF生成功能需要安装reportlab库\n\n请运行: pip install reportlab"
                )
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"生成PDF时发生错误: {str(e)}")
            return False
    
    def process_content_for_pdf(self, content):
        """处理内容，使其适合PDF显示"""
        # 替换表情图标为文字描述
        replacements = {
            "📋": "",
            "📊": "", 
            "🧮": "",
            "💡": "",
            "📤": "",
            "📥": "",
            "⚠️": "",
            "🔬": "",
            "📏": "",
            "🌪️": "",
            "💨": "",
            "🌫️": "",
            "⚡": "",
            "💧": "",
            "🔄": "",
            "🌬️": "",
            "🔧": "",
            "🚒": "",
            "⚖️": "",
            "🧊": "",
            "🧪": "",
            "🔩": "",
            "🛡️": "",
            "🔥": "",
            "⚗️": "",
            "🚨": "",
            "⚛️": "",
            "❄️": "",
            "📄": "",
            "📊": "",
            "•": "",
            "🏷️": "",
            "📝": ""
        }
        
        # 替换表情图标
        for emoji, text in replacements.items():
            content = content.replace(emoji, text)
        
        # 替换单位符号
        content = content.replace("m³", "m3")
        content = content.replace("g/100g", "g/100g")
        content = content.replace("kg/m³", "kg/m3")
        content = content.replace("Nm³/h", "Nm3/h")
        content = content.replace("Pa·s", "Pa.s")
        
        return content


if __name__ == "__main__":
    # 测试代码
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    calculator = 管径计算()
    calculator.resize(1200, 800)
    calculator.show()
    
    sys.exit(app.exec())