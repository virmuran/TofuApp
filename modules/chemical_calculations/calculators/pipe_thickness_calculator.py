from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog, QSpinBox, QButtonGroup, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator
import math
import re
from datetime import datetime


class 管道壁厚(QWidget):
    """管道壁厚计算器（左右布局优化版）"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        
        # 使用传入的数据管理器或创建新的
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            self.init_data_manager()
            
        # 先初始化 material_database
        self.material_database = {}
        self.setup_material_database()  # 先调用这个
        self.setup_ui()  # 然后调用 setup_ui
    
    def init_data_manager(self):
        """初始化数据管理器 - 使用单例模式"""
        try:
            from data_manager import DataManager
            self.data_manager = DataManager.get_instance()
            print("使用共享的数据管理器实例")
        except Exception as e:
            print(f"数据管理器初始化失败: {e}")
            self.data_manager = None
            
    def setup_ui(self):
        """设置左右布局的管道壁厚计算UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧：输入参数区域 (占2/3宽度)
        left_widget = QWidget()
        left_widget.setMaximumWidth(900)  # 限制最大宽度
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        # 1. 首先添加说明文本
        description = QLabel(
            "根据ASME B31.3等标准计算管道壁厚，支持MPa(g)表压单位，包含详细的焊接接头系数和材料数据库。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 计算标准选择
        standard_group = QGroupBox("📏 计算标准")
        standard_group.setStyleSheet("""
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
        standard_layout = QHBoxLayout(standard_group)
        
        self.standard_combo = QComboBox()
        self.standard_combo.addItems([
            "ASME B31.3 - 工艺管道",
            "GB/T 20801 - 压力管道规范",
            "GB 50316 - 工业金属管道设计规范",
            "SH/T 3059 - 石油化工管道设计"
        ])
        self.standard_combo.setFixedWidth(300)
        standard_layout.addWidget(self.standard_combo)
        standard_layout.addStretch()
        
        left_layout.addWidget(standard_group)
        
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
        
        # 第一列：参数名称（右对齐）
        # 第二列：输入框（固定宽度）
        # 第三列：下拉菜单/按钮（固定宽度）
        
        row = 0
        
        # 设计压力
        pressure_label = QLabel("设计压力 P(MPa(g)):")
        pressure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pressure_label.setStyleSheet(label_style)
        input_layout.addWidget(pressure_label, row, 0)
        
        pressure_unit_layout = QHBoxLayout()
        self.pressure_input = QLineEdit()
        self.pressure_input.setPlaceholderText("例如: 1.0")
        self.pressure_input.setValidator(QDoubleValidator(0.01, 100.0, 3))
        self.pressure_input.setText("1.0")
        self.pressure_input.setFixedWidth(input_width)
        pressure_unit_layout.addWidget(self.pressure_input)
        
        input_layout.addLayout(pressure_unit_layout, row, 1)
        
        # 压力提示
        self.pressure_hint = QLabel("1 MPa = 10 bar")
        self.pressure_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.pressure_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.pressure_hint, row, 2)
        
        row += 1
        
        # 设计温度
        temp_label = QLabel("设计温度 T(°C):")
        temp_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        temp_label.setStyleSheet(label_style)
        input_layout.addWidget(temp_label, row, 0)
        
        temp_unit_layout = QHBoxLayout()
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("例如: 150")
        self.temp_input.setValidator(QDoubleValidator(-200.0, 800.0, 1))
        self.temp_input.setText("180")
        self.temp_input.setFixedWidth(input_width)
        temp_unit_layout.addWidget(self.temp_input)
        
        input_layout.addLayout(temp_unit_layout, row, 1)
        
        # 温度提示
        self.temp_hint = QLabel("直接输入温度值")
        self.temp_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.temp_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.temp_hint, row, 2)
        
        row += 1
        
        # 管道外径
        diameter_label = QLabel("管道外径 D(mm):")
        diameter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        diameter_label.setStyleSheet(label_style)
        input_layout.addWidget(diameter_label, row, 0)
        
        diameter_unit_layout = QHBoxLayout()
        self.diameter_input = QLineEdit()
        self.diameter_input.setPlaceholderText("例如: 114.3")
        self.diameter_input.setValidator(QDoubleValidator(1.0, 2000.0, 2))
        self.diameter_input.setText("108")
        self.diameter_input.setFixedWidth(input_width)
        diameter_unit_layout.addWidget(self.diameter_input)
        
        input_layout.addLayout(diameter_unit_layout, row, 1)
        
        self.diameter_combo = QComboBox()
        self.setup_diameter_options()
        self.diameter_combo.setFixedWidth(combo_width)
        self.diameter_combo.currentTextChanged.connect(self.on_diameter_changed)
        input_layout.addWidget(self.diameter_combo, row, 2)
        
        row += 1
        
        # 焊接接头系数
        weld_label = QLabel("焊接接头系数 Ej:")
        weld_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        weld_label.setStyleSheet(label_style)
        input_layout.addWidget(weld_label, row, 0)
        
        weld_unit_layout = QHBoxLayout()
        self.weld_input = QLineEdit()
        self.weld_input.setPlaceholderText("例如: 1.0")
        self.weld_input.setValidator(QDoubleValidator(0.1, 1.0, 3))
        self.weld_input.setText("1.0")
        self.weld_input.setFixedWidth(input_width)
        weld_unit_layout.addWidget(self.weld_input)
        
        input_layout.addWidget(self.weld_input, row, 1)
        
        self.weld_combo = QComboBox()
        self.setup_weld_factor_options()
        self.weld_combo.setFixedWidth(combo_width)
        self.weld_combo.currentTextChanged.connect(self.on_weld_factor_changed)
        input_layout.addWidget(self.weld_combo, row, 2)
        
        row += 1
        
        # 许用应力
        stress_label = QLabel("许用应力 S(MPa):")
        stress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        stress_label.setStyleSheet(label_style)
        input_layout.addWidget(stress_label, row, 0)
        
        self.stress_input = QLineEdit()
        self.stress_input.setPlaceholderText("自动填充")
        self.stress_input.setReadOnly(True)
        self.stress_input.setFixedWidth(input_width)
        input_layout.addWidget(self.stress_input, row, 1)
        
        self.material_combo = QComboBox()
        self.setup_material_options()
        self.material_combo.setFixedWidth(combo_width)
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        input_layout.addWidget(self.material_combo, row, 2)
        
        row += 1
        
        # 系数Y
        y_label = QLabel("系数 Y:")
        y_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        y_label.setStyleSheet(label_style)
        input_layout.addWidget(y_label, row, 0)
        
        self.y_input = QLineEdit()
        self.y_input.setPlaceholderText("自动计算")
        self.y_input.setReadOnly(True)
        self.y_input.setFixedWidth(input_width)
        input_layout.addWidget(self.y_input, row, 1)
        
        self.y_combo = QComboBox()
        self.setup_y_factor_options()
        self.y_combo.setFixedWidth(combo_width)
        self.y_combo.currentTextChanged.connect(self.on_y_factor_changed)
        input_layout.addWidget(self.y_combo, row, 2)
        
        row += 1
        
        # 减薄量C1
        thinning_label = QLabel("减薄量 C₁(mm):")
        thinning_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        thinning_label.setStyleSheet(label_style)
        input_layout.addWidget(thinning_label, row, 0)
        
        thinning_unit_layout = QHBoxLayout()
        self.thinning_input = QLineEdit()
        self.thinning_input.setPlaceholderText("例如: 0.50")
        self.thinning_input.setValidator(QDoubleValidator(0.0, 10.0, 2))
        self.thinning_input.setText("0.50")
        self.thinning_input.setFixedWidth(input_width)
        thinning_unit_layout.addWidget(self.thinning_input)
        
        input_layout.addLayout(thinning_unit_layout, row, 1)
        
        self.thinning_combo = QComboBox()
        self.thinning_combo.addItems([
            "0.00 mm - 无减薄",
            "0.25 mm - 轻微减薄",
            "0.50 mm - 标准减薄 ✅",
            "0.75 mm - 中等减薄",
            "1.00 mm - 较大减薄"
        ])
        self.thinning_combo.setFixedWidth(combo_width)
        self.thinning_combo.currentTextChanged.connect(self.on_thinning_changed)
        input_layout.addWidget(self.thinning_combo, row, 2)
        
        row += 1
        
        # 腐蚀裕量C2
        corrosion_label = QLabel("腐蚀裕量 C₂(mm):")
        corrosion_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        corrosion_label.setStyleSheet(label_style)
        input_layout.addWidget(corrosion_label, row, 0)
        
        corrosion_unit_layout = QHBoxLayout()
        self.corrosion_input = QLineEdit()
        self.corrosion_input.setPlaceholderText("例如: 0.05")
        self.corrosion_input.setValidator(QDoubleValidator(0.0, 10.0, 2))
        self.corrosion_input.setText("0.05")
        self.corrosion_input.setFixedWidth(input_width)
        corrosion_unit_layout.addWidget(self.corrosion_input)
        
        input_layout.addLayout(corrosion_unit_layout, row, 1)
        
        self.corrosion_combo = QComboBox()
        self.corrosion_combo.addItems([
            "0.00 mm - 无腐蚀",
            "0.05 mm - 轻微腐蚀 ✅",
            "0.10 mm - 一般腐蚀",
            "0.50 mm - 中等腐蚀",
            "1.00 mm - 较强腐蚀",
            "1.50 mm - 严重腐蚀",
            "2.00 mm - 非常严重腐蚀"
        ])
        self.corrosion_combo.setFixedWidth(combo_width)
        self.corrosion_combo.currentTextChanged.connect(self.on_corrosion_changed)
        input_layout.addWidget(self.corrosion_combo, row, 2)
        
        left_layout.addWidget(input_group)
        
        # 4. 计算按钮
        calculate_btn = QPushButton("🧮 计算壁厚")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.calculate_thickness)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219955;
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
        
        # 初始材料选择
        self.on_material_changed(self.material_combo.currentText())
        self.on_y_factor_changed(self.y_combo.currentText())
    
    def setup_material_database(self):
        """设置材料数据库"""
        # 材料许用应力数据库 (MPa)
        self.material_database = {
            # 碳钢
            "Q235-A (20°C)": {"stress": 113, "type": "碳钢", "temp": 20},
            "Q235-A (100°C)": {"stress": 113, "type": "碳钢", "temp": 100},
            "Q235-A (200°C)": {"stress": 113, "type": "碳钢", "temp": 200},
            "20# (20°C)": {"stress": 130, "type": "碳钢", "temp": 20},
            "20# (100°C)": {"stress": 130, "type": "碳钢", "temp": 100},
            "20# (200°C)": {"stress": 130, "type": "碳钢", "temp": 200},
            "20# (300°C)": {"stress": 130, "type": "碳钢", "temp": 300},
            "20# (350°C)": {"stress": 122, "type": "碳钢", "temp": 350},
            "20# (400°C)": {"stress": 111, "type": "碳钢", "temp": 400},
            "20# (425°C)": {"stress": 104, "type": "碳钢", "temp": 425},
            "20# (450°C)": {"stress": 97, "type": "碳钢", "temp": 450},
            
            # 不锈钢 - 按照截图中的格式
            "304(0Cr18Ni9) (20°C)": {"stress": 137, "type": "奥氏体不锈钢", "temp": 20},
            "304(0Cr18Ni9) (100°C)": {"stress": 137, "type": "奥氏体不锈钢", "temp": 100},
            "304(0Cr18Ni9) (200°C)": {"stress": 137, "type": "奥氏体不锈钢", "temp": 200},
            "304(0Cr18Ni9) (300°C)": {"stress": 137, "type": "奥氏体不锈钢", "temp": 300},
            "304(0Cr18Ni9) (350°C)": {"stress": 132, "type": "奥氏体不锈钢", "temp": 350},
            "304(0Cr18Ni9) (400°C)": {"stress": 132, "type": "奥氏体不锈钢", "temp": 400},
            "304(0Cr18Ni9) (425°C)": {"stress": 121, "type": "奥氏体不锈钢", "temp": 425},
            "304(0Cr18Ni9) (450°C)": {"stress": 121, "type": "奥氏体不锈钢", "temp": 450},
            "304(0Cr18Ni9) (500°C)": {"stress": 121, "type": "奥氏体不锈钢", "temp": 500},
            
            "316(0Cr17Ni12Mo2) (20°C)": {"stress": 130, "type": "奥氏体不锈钢", "temp": 20},
            "316(0Cr17Ni12Mo2) (100°C)": {"stress": 130, "type": "奥氏体不锈钢", "temp": 100},
            "316(0Cr17Ni12Mo2) (200°C)": {"stress": 130, "type": "奥氏体不锈钢", "temp": 200},
            "316(0Cr17Ni12Mo2) (300°C)": {"stress": 130, "type": "奥氏体不锈钢", "temp": 300},
            "316(0Cr17Ni12Mo2) (400°C)": {"stress": 125, "type": "奥氏体不锈钢", "temp": 400},
            "316(0Cr17Ni12Mo2) (500°C)": {"stress": 116, "type": "奥氏体不锈钢", "temp": 500},
            "316(0Cr17Ni12Mo2) (600°C)": {"stress": 101, "type": "奥氏体不锈钢", "temp": 600},
            
            # 合金钢
            "16Mn (20°C)": {"stress": 170, "type": "合金钢", "temp": 20},
            "16Mn (100°C)": {"stress": 170, "type": "合金钢", "temp": 100},
            "16Mn (200°C)": {"stress": 170, "type": "合金钢", "temp": 200},
            "16Mn (300°C)": {"stress": 170, "type": "合金钢", "temp": 300},
            "16Mn (350°C)": {"stress": 170, "type": "合金钢", "temp": 350},
            "16Mn (400°C)": {"stress": 163, "type": "合金钢", "temp": 400},
            "16Mn (450°C)": {"stress": 150, "type": "合金钢", "temp": 450},
            
            "15CrMo (20°C)": {"stress": 150, "type": "合金钢", "temp": 20},
            "15CrMo (100°C)": {"stress": 150, "type": "合金钢", "temp": 100},
            "15CrMo (200°C)": {"stress": 150, "type": "合金钢", "temp": 200},
            "15CrMo (300°C)": {"stress": 150, "type": "合金钢", "temp": 300},
            "15CrMo (400°C)": {"stress": 150, "type": "合金钢", "temp": 400},
            "15CrMo (450°C)": {"stress": 147, "type": "合金钢", "temp": 450},
            "15CrMo (500°C)": {"stress": 140, "type": "合金钢", "temp": 500},
            "15CrMo (550°C)": {"stress": 128, "type": "合金钢", "temp": 550},
        }
    
    def setup_diameter_options(self):
        """设置管道外径选项"""
        diameter_options = [
            "- 请选择管道外径 -",  # 添加空值选项
            "10.0 mm - DN6 [1/8\"]",
            "13.5 mm - DN8 [1/4\"]", 
            "17.2 mm - DN10 [3/8\"]",
            "21.3 mm - DN15 [1/2\"]",
            "26.9 mm - DN20 [3/4\"]",
            "33.7 mm - DN25 [1.00\"]",
            "42.4 mm - DN32 [1.25\"]",
            "48.3 mm - DN40 [1.50\"]",
            "60.3 mm - DN50 [2.00\"]",
            "76.1 mm - DN65 [2.50\"]",
            "88.9 mm - DN80 [3.00\"]",
            "101.6 mm - DN90 [3.50\"]",
            "108.0 mm - DN100 [4.00\"] ✅",
            "114.3 mm - DN100 [4.00\"]",
            "139.7 mm - DN125 [5.00\"]",
            "165.1 mm - DN150 [6.00\"]",
            "219.1 mm - DN200 [8.00\"]",
            "273.0 mm - DN250 [10.00\"]", 
            "323.9 mm - DN300 [12.00\"]"
        ]
        self.diameter_combo.addItems(diameter_options)
        # 设置默认值为DN100
        for i in range(self.diameter_combo.count()):
            if "108.0 mm" in self.diameter_combo.itemText(i):
                self.diameter_combo.setCurrentIndex(i)
                break
        
    def setup_weld_factor_options(self):
        """设置焊接接头系数选项"""
        weld_options = [
            "- 请选择焊接接头系数 -",
            "1.0 - 电熔焊 100%无损检测 双面对接焊 ✅",
            "0.9 - 电熔焊 100%无损检测 单面对接焊",
            "0.85 - 电熔焊 局部无损检测 双面对接焊",
            "0.8 - 电熔焊 局部无损检测 单面对接焊",
            "0.8 - 螺旋缝自动焊",
            "0.7 - 电熔焊 不作无损检测 双面对接焊",
            "0.6 - 电熔焊 不作无损检测 单面对接焊",
            "0.85 - 电阻焊 100%涡流检测",
            "0.65 - 电阻焊 不作无损检测",
            "0.6 - 加热炉焊 不作无损检测"
        ]
        self.weld_combo.addItems(weld_options)
        # 设置默认值
        self.weld_combo.setCurrentIndex(1)  # Ej=1.0
    
    def setup_y_factor_options(self):
        """设置系数Y选项"""
        y_options = [
            "- 请选择系数Y -",
            "0.4 - 铁素体钢 (温度≤482°C) ✅",
            "0.5 - 铁素体钢 (温度>482°C)",
            "0.4 - 奥氏体钢 (温度≤482°C)",
            "0.7 - 奥氏体钢 (温度>482°C)",
            "0.4 - 其他金属材料"
        ]
        self.y_combo.addItems(y_options)
        # 设置默认值
        self.y_combo.setCurrentIndex(1)  # Y=0.4
        
    def on_diameter_changed(self, text):
        """处理直径选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            return
            
        # 从文本中提取数值并填入输入框
        try:
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                diameter_value = float(match.group(1))
                self.diameter_input.setText(f"{diameter_value}")
        except:
            pass
    
    def setup_material_options(self):
        """设置材料选项"""
        materials = [
            "- 请选择材料 -",  # 添加空值选项
            "304(0Cr18Ni9) (20°C) - GB/T1277 奥氏体不锈钢 ✅",
            "304(0Cr18Ni9) (100°C) - GB/T1277 奥氏体不锈钢",
            "304(0Cr18Ni9) (200°C) - GB/T1277 奥氏体不锈钢",
            "304(0Cr18Ni9) (300°C) - GB/T1277 奥氏体不锈钢",
            "304(0Cr18Ni9) (350°C) - GB/T1277 奥氏体不锈钢",
            "304(0Cr18Ni9) (400°C) - GB/T1277 奥氏体不锈钢",
            "316(0Cr17Ni12Mo2) (20°C) - GB/T1220 奥氏体不锈钢",
            "316(0Cr17Ni12Mo2) (300°C) - GB/T1220 奥氏体不锈钢",
            "316(0Cr17Ni12Mo2) (500°C) - GB/T1220 奥氏体不锈钢",
            "20# (20°C) - GB/T699 优质碳素结构钢",
            "20# (200°C) - GB/T699 优质碳素结构钢",
            "20# (400°C) - GB/T699 优质碳素结构钢",
            "Q235-A (20°C) - GB/T700 一般结构用钢",
            "16Mn (20°C) - GB/T1591 低合金高强度钢",
            "16Mn (300°C) - GB/T1591 低合金高强度钢",
            "15CrMo (20°C) - GB/T3077 耐热钢",
            "15CrMo (500°C) - GB/T3077 耐热钢"
        ]
        self.material_combo.addItems(materials)
        # 设置默认值为304不锈钢
        self.material_combo.setCurrentIndex(1)
    
    def on_material_changed(self, text):
        """处理材料选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.stress_input.clear()
            return
            
        material_key = text.split(" - ")[0]
        if material_key in self.material_database:
            stress = self.material_database[material_key]["stress"]
            self.stress_input.setText(f"{stress}")
            
            # 根据材料类型自动设置系数Y
            material_type = self.material_database[material_key]["type"]
            design_temp = float(self.temp_input.text() or "20")
            
            if "奥氏体" in material_type:
                if design_temp <= 482:
                    y_value = 0.4
                    y_text = "0.4 - 奥氏体钢 (温度≤482°C)"
                else:
                    y_value = 0.7
                    y_text = "0.7 - 奥氏体钢 (温度>482°C)"
            else:  # 铁素体钢和其他
                if design_temp <= 482:
                    y_value = 0.4
                    y_text = "0.4 - 铁素体钢 (温度≤482°C) ✅"
                else:
                    y_value = 0.5
                    y_text = "0.5 - 铁素体钢 (温度>482°C)"
            
            self.y_input.setText(f"{y_value}")
            # 查找并设置对应的Y系数选项
            for i in range(self.y_combo.count()):
                if y_text in self.y_combo.itemText(i):
                    self.y_combo.setCurrentIndex(i)
                    break
    
    def on_weld_factor_changed(self, text):
        """处理焊接接头系数变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.weld_input.clear()
            return
            
        try:
            # 提取数值部分
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                weld_factor = float(match.group(1))
                self.weld_input.setText(f"{weld_factor}")
        except:
            pass
    
    def on_y_factor_changed(self, text):
        """处理系数Y变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.y_input.clear()
            return
            
        try:
            # 提取数值部分
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                y_factor = float(match.group(1))
                self.y_input.setText(f"{y_factor}")
        except:
            pass
    
    def on_thinning_changed(self, text):
        """处理减薄量变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.thinning_input.clear()
            return
            
        try:
            # 提取数值部分
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                thinning_value = float(match.group(1))
                self.thinning_input.setText(f"{thinning_value}")
        except:
            pass
    
    def on_corrosion_changed(self, text):
        """处理腐蚀裕量变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.corrosion_input.clear()
            return
            
        try:
            # 提取数值部分
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                corrosion_value = float(match.group(1))
                self.corrosion_input.setText(f"{corrosion_value}")
        except:
            pass
    
    def calculate_thickness(self):
        """计算管道壁厚"""
        try:
            # 获取输入值
            standard = self.standard_combo.currentText()
            design_pressure = float(self.pressure_input.text())  # MPa
            design_temp = float(self.temp_input.text())  # °C
            outer_diameter = float(self.diameter_input.text())  # mm
            allowable_stress = float(self.stress_input.text())  # MPa
            weld_factor = float(self.weld_input.text())
            y_factor = float(self.y_input.text())
            thinning_allowance = float(self.thinning_input.text())  # mm (减薄量C1)
            corrosion_allowance = float(self.corrosion_input.text())  # mm (腐蚀裕量C2)
            
            # 验证输入
            if not all([design_pressure, outer_diameter, allowable_stress, weld_factor, y_factor]):
                QMessageBox.warning(self, "输入错误", "请填写所有必需参数")
                return
            
            if design_pressure <= 0 or outer_diameter <= 0 or allowable_stress <= 0:
                QMessageBox.warning(self, "输入错误", "压力、直径和许用应力必须大于0")
                return
            
            # 根据ASME B31.3公式计算理论壁厚
            # t = P * D / (2 * S * E + 2 * P * Y) + C
            # 其中C是总附加量 = C1 + C2
            
            total_additional = thinning_allowance + corrosion_allowance
            
            # 计算理论壁厚 (mm) - 使用标准公式
            theoretical_thickness = (design_pressure * outer_diameter) / \
                                  (2 * allowable_stress * weld_factor + 2 * design_pressure * y_factor)
            
            # 计算设计壁厚 (包含总附加量)
            design_thickness = theoretical_thickness + total_additional
            
            # 计算最小要求壁厚
            minimum_required_thickness = theoretical_thickness + corrosion_allowance
            
            # 选择标准管壁厚
            standard_thickness = self.select_standard_thickness(design_thickness)
            
            # 计算实际应力
            actual_stress = design_pressure * (outer_diameter - 2 * standard_thickness) / \
                          (2 * standard_thickness * weld_factor)
            
            # 安全系数
            safety_factor = allowable_stress / actual_stress if actual_stress > 0 else 0
            
            # 计算重量增加百分比
            if standard_thickness > 0 and theoretical_thickness > 0:
                weight_increase = ((standard_thickness / theoretical_thickness) - 1) * 100
            else:
                weight_increase = 0
            
            # 显示结果
            result = self.format_results(
                standard, design_pressure, design_temp, outer_diameter, 
                allowable_stress, weld_factor, y_factor, 
                thinning_allowance, corrosion_allowance, total_additional,
                theoretical_thickness, minimum_required_thickness, design_thickness,
                standard_thickness, actual_stress, safety_factor, weight_increase
            )
            
            self.result_text.setText(result)
            
        except ValueError as e:
            QMessageBox.critical(self, "计算错误", f"参数输入格式错误: {str(e)}")
        except ZeroDivisionError:
            QMessageBox.critical(self, "计算错误", "参数不能为零")
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def select_standard_thickness(self, required_thickness):
        """选择标准壁厚"""
        # 标准壁厚系列 (mm) - 根据常用管道规格
        standard_thicknesses = [
            2.0, 2.3, 2.6, 2.9, 3.2, 3.6, 4.0, 4.5, 5.0, 5.6, 6.3, 
            7.1, 8.0, 8.8, 10.0, 11.0, 12.5, 14.2, 16.0, 17.5, 20.0,
            22.2, 25.0, 28.0, 30.0, 32.0, 36.0, 40.0, 45.0, 50.0
        ]
        
        for thickness in standard_thicknesses:
            if thickness >= required_thickness:
                return thickness
        
        # 如果需要的壁厚超过最大值，返回最大值
        return standard_thicknesses[-1]
    
    def format_results(self, standard, design_pressure, design_temp, outer_diameter,
                      allowable_stress, weld_factor, y_factor,
                      thinning_allowance, corrosion_allowance, total_additional,
                      theoretical_thickness, minimum_required_thickness, design_thickness,
                      standard_thickness, actual_stress, safety_factor, weight_increase):
        """格式化计算结果"""
        return f"""═══════════
📋 输入参数
══════════

    计算标准: {standard}
    设计压力 P: {design_pressure} MPa(g)
    设计温度 T: {design_temp} °C
    管道外径 D: {outer_diameter} mm
    焊接接头系数 Ej: {weld_factor}
    许用应力 S: {allowable_stress} MPa
    系数 Y: {y_factor}
    减薄量 C₁: {thinning_allowance:.2f} mm
    腐蚀裕量 C₂: {corrosion_allowance:.2f} mm
    总附加量 C: {total_additional:.2f} mm

══════════
📊 计算结果
══════════

    壁厚计算:
    • 理论计算壁厚 t₀: {theoretical_thickness:.2f} mm
    • 最小要求壁厚 t_min: {minimum_required_thickness:.2f} mm
    • 设计计算壁厚 t_d: {design_thickness:.2f} mm
    • 选用标准壁厚 t_n: {standard_thickness} mm

    强度校核:
    • 实际计算应力: {actual_stress:.1f} MPa
    • 安全系数: {safety_factor:.2f}
    • 强度状态: {'✅ 安全 (安全系数≥1.0)' if safety_factor >= 1.0 else '⚠️ 需重新设计 (安全系数<1.0)'}

    经济性分析:
    • 重量增加: {weight_increase:.1f} %
    • 壁厚余量: {standard_thickness - design_thickness:.2f} mm

    管道等级推荐:
    • Sch 10S: ~{standard_thickness * 0.6:.1f} mm
    • Sch 40S: ~{standard_thickness * 0.8:.1f} mm  
    • Sch 80S: ~{standard_thickness:.1f} mm
    • Sch 160: ~{standard_thickness * 1.4:.1f} mm

══════════
💡 计算说明
══════════

    • 采用标准壁厚计算公式: t = P×D / (2×S×E + 2×P×Y) + C
    • Y系数根据材料类型和设计温度确定
    • 减薄量C₁考虑制造公差和工艺减薄
    • 腐蚀裕量C₂根据介质腐蚀特性确定
    • 建议安全系数不小于1.0，重要管道建议1.5以上
    • 计算结果仅供参考，实际应用需经专业工程师审核"""
    
    def get_project_info(self):
        """获取工程信息 - 使用共享的项目信息"""
        try:
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
                report_number = self.data_manager.get_next_report_number("PTHICK")
            
            dialog = ProjectInfoDialog(self, saved_info, report_number)
            if dialog.exec() == QDialog.Accepted:
                info = dialog.get_info()
                # 验证必填字段
                if not info['project_name']:
                    QMessageBox.warning(self, "输入错误", "工程名称不能为空")
                    return self.get_project_info()  # 重新弹出对话框
                
                # 保存项目信息到数据管理器
                if self.data_manager:
                    # 保存所有项目信息（使用新版字段名）
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
            if not result_text or ("计算结果" not in result_text and "壁厚计算" not in result_text):
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            # 获取工程信息
            project_info = self.get_project_info()
            if not project_info:
                return None  # 用户取消了输入
            
            # 添加报告头信息
            report = f"""工程计算书 - 管道壁厚计算
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

    计算书编号: PT-{datetime.now().strftime('%Y%m%d')}-001
    版本: 1.0
    状态: 正式计算书

══════════
📝 备注说明
══════════

    1. 本计算书基于压力容器设计规范及相关标准
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
            default_name = f"管道壁厚计算书_{timestamp}.txt"
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
            default_name = f"管道壁厚计算书_{timestamp}.pdf"
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
                title = Paragraph("工程计算书 - 管道壁厚计算", chinese_style_heading)
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
            "📝": "",
            "📚": "",
            "✅": ""
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
    
    widget = 管道壁厚()
    widget.resize(1200, 800)
    widget.show()
    
    sys.exit(app.exec())