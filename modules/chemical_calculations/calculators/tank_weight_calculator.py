from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog, QSpinBox, QButtonGroup, QGridLayout,
    QFileDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator
import math


class 罐体重量(QWidget):
    """罐体重量计算器（与压降计算UI完全一致）"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        
        # 使用传入的数据管理器或创建新的
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            self.init_data_manager()
        
        self.setup_ui()

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
        """设置与压降计算完全一致的UI布局"""
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
            "计算各种类型罐体的重量，包括空罐重量、液体重量和总重量。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 罐体类型选择
        type_group = QGroupBox("🏺 罐体类型")
        type_group.setStyleSheet("""
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
        type_layout = QHBoxLayout(type_group)
        
        self.type_button_group = QButtonGroup(self)
        
        tank_types = [
            ("锥体罐", "圆锥底垂直储罐"),
            ("平底罐", "平底垂直储罐"),
            ("椭圆底罐", "椭圆封头储罐"),
            ("卧式罐", "卧式圆柱储罐"),
            ("球罐", "球形储罐")
        ]
        
        for i, (type_name, tooltip) in enumerate(tank_types):
            btn = QPushButton(type_name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setFixedWidth(120)
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
            self.type_button_group.addButton(btn, i)
            type_layout.addWidget(btn)
        
        # 默认选择第一个
        self.type_button_group.button(0).setChecked(True)
        self.type_button_group.buttonClicked.connect(self.on_tank_type_changed)
        
        type_layout.addStretch()
        left_layout.addWidget(type_group)
        
        # 3. 输入参数组 - 使用GridLayout实现整齐的布局
        input_group = QGroupBox("📏 尺寸参数")
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
        self.input_layout = QGridLayout(input_group)
        self.input_layout.setVerticalSpacing(12)
        self.input_layout.setHorizontalSpacing(10)
        
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
        # 第三列：下拉菜单或提示标签（固定宽度）
        
        row = 0
        
        # 筒体外径 - 所有罐体类型都需要
        diameter_label = QLabel("筒体外径 D (mm):")
        diameter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        diameter_label.setStyleSheet(label_style)
        self.input_layout.addWidget(diameter_label, row, 0)
        
        self.diameter_input = QLineEdit()
        self.diameter_input.setPlaceholderText("例如: 3000")
        self.diameter_input.setValidator(QDoubleValidator(0.1, 50.0, 2))
        self.diameter_input.setText("")
        self.diameter_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.diameter_input, row, 1)
        
        self.diameter_hint = QLabel("直接输入直径值")
        self.diameter_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.diameter_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.diameter_hint, row, 2)
        
        row += 1
        
        # 筒体高度 - 锥体罐、平底罐、椭圆底罐需要
        self.height_label = QLabel("筒体高度 H (mm):")
        self.height_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.height_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.height_label, row, 0)
        
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("例如: 5000")
        self.height_input.setValidator(QDoubleValidator(0.1, 50.0, 2))
        self.height_input.setText("")
        self.height_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.height_input, row, 1)
        
        self.height_hint = QLabel("直接输入高度值")
        self.height_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.height_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.height_hint, row, 2)
        
        row += 1
        
        # 筒体壁厚 - 锥体罐、平底罐、椭圆底罐、卧式罐需要
        self.shell_thickness_label = QLabel("筒体壁厚 (mm):")
        self.shell_thickness_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.shell_thickness_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.shell_thickness_label, row, 0)
        
        self.shell_thickness_input = QLineEdit()
        self.shell_thickness_input.setPlaceholderText("例如: 6.0")
        self.shell_thickness_input.setValidator(QDoubleValidator(1.0, 100.0, 1))
        self.shell_thickness_input.setText("")
        self.shell_thickness_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.shell_thickness_input, row, 1)
        
        self.shell_thickness_hint = QLabel("直接输入壁厚值")
        self.shell_thickness_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.shell_thickness_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.shell_thickness_hint, row, 2)
        
        row += 1
        
        # 锥体高度 - 仅锥体罐需要
        self.cone_height_label = QLabel("锥体高度 h (mm):")
        self.cone_height_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cone_height_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.cone_height_label, row, 0)
        
        self.cone_height_input = QLineEdit()
        self.cone_height_input.setPlaceholderText("例如: 1200")
        self.cone_height_input.setValidator(QDoubleValidator(0.1, 10.0, 2))
        self.cone_height_input.setText("")
        self.cone_height_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.cone_height_input, row, 1)
        
        self.cone_height_hint = QLabel("直接输入锥体高度")
        self.cone_height_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.cone_height_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.cone_height_hint, row, 2)
        
        row += 1
        
        # 锥口直径 - 仅锥体罐需要
        self.nozzle_diameter_label = QLabel("锥口直径 d (mm):")
        self.nozzle_diameter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.nozzle_diameter_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.nozzle_diameter_label, row, 0)
        
        self.nozzle_diameter_input = QLineEdit()
        self.nozzle_diameter_input.setPlaceholderText("例如: 100")
        self.nozzle_diameter_input.setValidator(QDoubleValidator(0.01, 2.0, 3))
        self.nozzle_diameter_input.setText("")
        self.nozzle_diameter_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.nozzle_diameter_input, row, 1)
        
        self.nozzle_diameter_hint = QLabel("直接输入锥口直径")
        self.nozzle_diameter_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.nozzle_diameter_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.nozzle_diameter_hint, row, 2)
        
        row += 1
        
        # 筒体长度 - 仅卧式罐需要
        self.length_label = QLabel("筒体长度 L (mm):")
        self.length_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.length_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.length_label, row, 0)
        
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("例如: 5000")
        self.length_input.setValidator(QDoubleValidator(0.1, 50.0, 2))
        self.length_input.setText("")
        self.length_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.length_input, row, 1)
        
        self.length_hint = QLabel("直接输入长度值")
        self.length_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.length_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.length_hint, row, 2)
        
        row += 1
        
        # 液位高度 - 卧式罐、球罐需要
        self.liquid_level_label = QLabel("液位高度 h (mm):")
        self.liquid_level_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.liquid_level_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.liquid_level_label, row, 0)
        
        self.liquid_level_input = QLineEdit()
        self.liquid_level_input.setPlaceholderText("例如: 1000")
        self.liquid_level_input.setValidator(QDoubleValidator(0.0, 50.0, 2))
        self.liquid_level_input.setText("")
        self.liquid_level_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.liquid_level_input, row, 1)
        
        self.liquid_level_hint = QLabel("直接输入液位高度")
        self.liquid_level_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.liquid_level_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.liquid_level_hint, row, 2)
        
        row += 1
        
        # 球体壁厚 - 仅球罐需要
        self.sphere_thickness_label = QLabel("球体壁厚 (mm):")
        self.sphere_thickness_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sphere_thickness_label.setStyleSheet(label_style)
        self.input_layout.addWidget(self.sphere_thickness_label, row, 0)
        
        self.sphere_thickness_input = QLineEdit()
        self.sphere_thickness_input.setPlaceholderText("例如: 6.0")
        self.sphere_thickness_input.setValidator(QDoubleValidator(1.0, 100.0, 1))
        self.sphere_thickness_input.setText("")
        self.sphere_thickness_input.setFixedWidth(input_width)
        self.input_layout.addWidget(self.sphere_thickness_input, row, 1)
        
        self.sphere_thickness_hint = QLabel("直接输入壁厚值")
        self.sphere_thickness_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.sphere_thickness_hint.setFixedWidth(combo_width)
        self.input_layout.addWidget(self.sphere_thickness_hint, row, 2)
        
        left_layout.addWidget(input_group)
        
        # 4. 材料参数组
        material_group = QGroupBox("🔩 材料参数")
        material_group.setStyleSheet("""
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
        
        material_layout = QGridLayout(material_group)
        material_layout.setVerticalSpacing(12)
        material_layout.setHorizontalSpacing(10)
        
        label_style = """
            QLabel {
                font-weight: bold;
                padding-right: 10px;
            }
        """
        
        input_width = 400
        combo_width = 250
        
        row = 0

        # 罐体密度
        density_label = QLabel("罐体密度 (kg/m³):")
        density_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        density_label.setStyleSheet(label_style)
        material_layout.addWidget(density_label, row, 0)
        
        self.density_input = QLineEdit()
        self.density_input.setPlaceholderText("例如: 7930")
        self.density_input.setValidator(QDoubleValidator(100, 20000, 2))
        self.density_input.setText("")
        self.density_input.setFixedWidth(input_width)
        material_layout.addWidget(self.density_input, row, 1)
        
        self.material_combo = QComboBox()
        self.material_combo.addItems([
            "- 请选择材料 -",
            "304不锈钢 - 密度: 7930 kg/m³",
            "316不锈钢 - 密度: 7980 kg/m³", 
            "碳钢 - 密度: 7850 kg/m³",
            "玻璃钢（FRP） - 密度: 2000 kg/m³",
            "聚氯乙烯（PVC） - 密度: 1400 kg/m³",
            "聚乙烯(PE) - 密度: 970 kg/m³",
            "铝 - 密度: 2850 kg/m³",
            "钛合金 - 密度: 4510 kg/m³",
            "自定义材料"
        ])
        self.material_combo.setFixedWidth(combo_width)
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        material_layout.addWidget(self.material_combo, row, 2)
        
        row += 1
        
        # 液体密度
        liquid_density_label = QLabel("液体密度 (kg/m³):")
        liquid_density_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        liquid_density_label.setStyleSheet(label_style)
        material_layout.addWidget(liquid_density_label, row, 0)
        
        self.liquid_density_input = QLineEdit()
        self.liquid_density_input.setPlaceholderText("例如: 1000")
        self.liquid_density_input.setValidator(QDoubleValidator(0, 2000, 0))
        self.liquid_density_input.setText("")
        self.liquid_density_input.setFixedWidth(input_width)
        material_layout.addWidget(self.liquid_density_input, row, 1)
        
        self.liquid_density_hint = QLabel("水: 1000 kg/m³")
        self.liquid_density_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.liquid_density_hint.setFixedWidth(combo_width)
        material_layout.addWidget(self.liquid_density_hint, row, 2)
        
        left_layout.addWidget(material_group)
        
        # 5. 计算按钮
        calculate_btn = QPushButton("🧮 计算重量")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.calculate_weight)
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
        
        # 6. 下载按钮布局
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
        
        # 7. 清空按钮
        clear_btn = QPushButton("🗑️ 清空输入")
        clear_btn.clicked.connect(self.clear_inputs)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        left_layout.addWidget(clear_btn)
        
        # 在底部添加拉伸因子
        left_layout.addStretch()
        
        # 右侧：结果显示区域 (占1/3宽度)
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # 结果显示
        self.result_group = QGroupBox("📊 计算结果")
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
        
        # 设置初始状态 - 锥体罐
        self.on_tank_type_changed(self.type_button_group.checkedButton())
    
    def get_current_tank_type(self):
        """获取当前选择的罐体类型"""
        checked_button = self.type_button_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return "锥体罐"  # 默认值
    
    def on_tank_type_changed(self, button):
        """处理罐体类型变化 - 动态显示/隐藏参数行"""
        tank_type = button.text() if button else "锥体罐"
        
        # 隐藏所有特定参数行
        self.height_label.setVisible(False)
        self.height_input.setVisible(False)
        self.height_hint.setVisible(False)
        
        self.shell_thickness_label.setVisible(False)
        self.shell_thickness_input.setVisible(False)
        self.shell_thickness_hint.setVisible(False)
        
        self.cone_height_label.setVisible(False)
        self.cone_height_input.setVisible(False)
        self.cone_height_hint.setVisible(False)
        
        self.nozzle_diameter_label.setVisible(False)
        self.nozzle_diameter_input.setVisible(False)
        self.nozzle_diameter_hint.setVisible(False)
        
        self.length_label.setVisible(False)
        self.length_input.setVisible(False)
        self.length_hint.setVisible(False)
        
        self.liquid_level_label.setVisible(False)
        self.liquid_level_input.setVisible(False)
        self.liquid_level_hint.setVisible(False)
        
        self.sphere_thickness_label.setVisible(False)
        self.sphere_thickness_input.setVisible(False)
        self.sphere_thickness_hint.setVisible(False)
        
        # 根据罐体类型显示相应参数行
        if tank_type == "锥体罐":
            self.height_label.setVisible(True)
            self.height_input.setVisible(True)
            self.height_hint.setVisible(True)
            
            self.shell_thickness_label.setVisible(True)
            self.shell_thickness_input.setVisible(True)
            self.shell_thickness_hint.setVisible(True)
            
            self.cone_height_label.setVisible(True)
            self.cone_height_input.setVisible(True)
            self.cone_height_hint.setVisible(True)
            
            self.nozzle_diameter_label.setVisible(True)
            self.nozzle_diameter_input.setVisible(True)
            self.nozzle_diameter_hint.setVisible(True)
            
        elif tank_type == "平底罐":
            self.height_label.setVisible(True)
            self.height_input.setVisible(True)
            self.height_hint.setVisible(True)
            
            self.shell_thickness_label.setVisible(True)
            self.shell_thickness_input.setVisible(True)
            self.shell_thickness_hint.setVisible(True)
            
        elif tank_type == "椭圆底罐":
            self.height_label.setVisible(True)
            self.height_input.setVisible(True)
            self.height_hint.setVisible(True)
            
            self.shell_thickness_label.setVisible(True)
            self.shell_thickness_input.setVisible(True)
            self.shell_thickness_hint.setVisible(True)
            
        elif tank_type == "卧式罐":
            self.shell_thickness_label.setVisible(True)
            self.shell_thickness_input.setVisible(True)
            self.shell_thickness_hint.setVisible(True)
            
            self.length_label.setVisible(True)
            self.length_input.setVisible(True)
            self.length_hint.setVisible(True)
            
            self.liquid_level_label.setVisible(True)
            self.liquid_level_input.setVisible(True)
            self.liquid_level_hint.setVisible(True)
            
        elif tank_type == "球罐":
            self.liquid_level_label.setVisible(True)
            self.liquid_level_input.setVisible(True)
            self.liquid_level_hint.setVisible(True)
            
            self.sphere_thickness_label.setVisible(True)
            self.sphere_thickness_input.setVisible(True)
            self.sphere_thickness_hint.setVisible(True)
    
    def on_material_changed(self, text):
        """处理材料选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            return
            
        if "自定义" in text:
            # 自定义材料，不清空输入框，用户可以手动输入
            # 可以在这里可选地清除密度输入框或保持原值
            # self.density_input.clear()
            pass
        else:
            try:
                # 从文本中提取密度值
                import re
                match = re.search(r'密度:\s*(\d+)', text)
                if match:
                    density_value = float(match.group(1))
                    self.density_input.setText(f"{density_value}")
            except:
                pass
    
    def calculate_weight(self):
        """计算罐体重量"""
        try:
            tank_type = self.get_current_tank_type()
            diameter = float(self.diameter_input.text() or 0) / 1000
            material_density = float(self.density_input.text() or 0)
            liquid_density = float(self.liquid_density_input.text() or 0)
            
            # 验证输入
            if not all([diameter, material_density, liquid_density]):
                QMessageBox.warning(self, "输入错误", "请填写所有必需参数")
                return
            
            if tank_type == "锥体罐":
                height = float(self.height_input.text() or 0) / 1000
                shell_thickness = float(self.shell_thickness_input.text() or 0) / 1000
                cone_height = float(self.cone_height_input.text() or 0) / 1000
                nozzle_diameter = float(self.nozzle_diameter_input.text() or 0) / 1000
                
                # 计算锥体罐重量
                tank_weight = self.calculate_cone_tank_weight(
                    diameter, height, shell_thickness, cone_height, nozzle_diameter, material_density
                )
                
                # 计算液体重量
                liquid_weight = self.calculate_cone_liquid_weight(
                    diameter, height, cone_height, liquid_density
                )
                
            elif tank_type == "平底罐":
                height = float(self.height_input.text() or 0) / 1000
                shell_thickness = float(self.shell_thickness_input.text() or 0) / 1000
                
                # 计算平底罐重量
                tank_weight = self.calculate_flat_tank_weight(
                    diameter, height, shell_thickness, material_density
                )
                
                # 计算液体重量
                liquid_weight = self.calculate_flat_liquid_weight(
                    diameter, height, liquid_density
                )
                
            elif tank_type == "椭圆底罐":
                height = float(self.height_input.text() or 0) / 1000
                shell_thickness = float(self.shell_thickness_input.text() or 0) / 1000
                
                # 计算椭圆底罐重量
                tank_weight = self.calculate_elliptic_tank_weight(
                    diameter, height, shell_thickness, material_density
                )
                
                # 计算液体重量
                liquid_weight = self.calculate_elliptic_liquid_weight(
                    diameter, height, liquid_density
                )
                
            elif tank_type == "卧式罐":
                length = float(self.length_input.text() or 0) / 1000
                shell_thickness = float(self.shell_thickness_input.text() or 0) / 1000
                liquid_level = float(self.liquid_level_input.text() or 0) / 1000
                
                # 计算卧式罐重量
                tank_weight = self.calculate_horizontal_tank_weight(
                    diameter, length, shell_thickness, material_density
                )
                
                # 计算液体重量
                liquid_weight = self.calculate_horizontal_liquid_weight(
                    diameter, length, liquid_level, liquid_density
                )
                
            elif tank_type == "球罐":
                liquid_level = float(self.liquid_level_input.text() or 0) / 1000
                sphere_thickness = float(self.sphere_thickness_input.text() or 0) / 1000
                
                # 计算球罐重量
                tank_weight = self.calculate_sphere_tank_weight(
                    diameter, sphere_thickness, material_density
                )
                
                # 计算液体重量
                liquid_weight = self.calculate_sphere_liquid_weight(
                    diameter, liquid_level, liquid_density
                )
            else:
                raise ValueError("未知罐体类型")
            
            # 显示结果
            self.display_results(tank_type, tank_weight, liquid_weight, material_density, liquid_density)
            
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"请输入有效的数值: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def calculate_cone_tank_weight(self, D, H, t, h_cone, d, density):
        """计算锥体罐重量"""
        # 筒体体积 (圆柱侧面积 × 厚度)
        cylinder_area = math.pi * D * H
        cylinder_volume = cylinder_area * t
        
        # 锥体体积 (圆锥台侧面积 × 厚度)
        R_large = D / 2
        r_small = d / 2
        
        cone_slant_height = math.sqrt(h_cone**2 + (R_large - r_small)**2)
        cone_area = math.pi * (R_large + r_small) * cone_slant_height
        cone_volume = cone_area * t
        
        # 罐底面积 (平的)
        bottom_area = math.pi * (R_large**2)
        bottom_volume = bottom_area * t
        
        # 总重量
        total_volume = cylinder_volume + cone_volume + bottom_volume
        total_weight = total_volume * density
        
        return total_weight
    
    def calculate_cone_liquid_weight(self, D, H, h_cone, liquid_density):
        """计算锥体罐液体重量"""
        # 筒体部分液体体积
        cylinder_volume = math.pi * (D/2)**2 * H
        
        # 锥体部分液体体积
        cone_volume = (1/3) * math.pi * (D/2)**2 * h_cone
        
        total_volume = cylinder_volume + cone_volume
        liquid_weight = total_volume * liquid_density
        
        return liquid_weight
    
    def calculate_flat_tank_weight(self, D, H, t, density):
        """计算平底罐重量"""
        # 筒体侧面积
        cylinder_area = math.pi * D * H
        
        # 罐底面积 (平底)
        bottom_area = math.pi * (D/2)**2
        
        # 罐顶面积 (平的)
        top_area = bottom_area
        
        # 总表面积
        total_area = cylinder_area + bottom_area + top_area
        
        # 总重量
        total_volume = total_area * t
        total_weight = total_volume * density
        
        return total_weight
    
    def calculate_flat_liquid_weight(self, D, H, liquid_density):
        """计算平底罐液体重量"""
        total_volume = math.pi * (D/2)**2 * H
        liquid_weight = total_volume * liquid_density
        return liquid_weight
    
    def calculate_elliptic_tank_weight(self, D, H, t, density):
        """计算椭圆底罐重量"""
        # 筒体侧面积
        cylinder_area = math.pi * D * H
        
        # 椭圆封头面积
        head_area = 1.084 * math.pi * (D/2)**2
        total_head_area = 2 * head_area
        
        # 总表面积
        total_area = cylinder_area + total_head_area
        
        # 总重量
        total_volume = total_area * t
        total_weight = total_volume * density
        
        return total_weight
    
    def calculate_elliptic_liquid_weight(self, D, H, liquid_density):
        """计算椭圆底罐液体重量"""
        # 圆柱部分
        cylinder_volume = math.pi * (D/2)**2 * H
        
        # 椭圆封头体积
        head_volume = 0.1309 * D**3
        total_head_volume = 2 * head_volume
        
        total_volume = cylinder_volume + total_head_volume
        liquid_weight = total_volume * liquid_density
        return liquid_weight
    
    def calculate_horizontal_tank_weight(self, D, L, t, density):
        """计算卧式罐重量"""
        # 筒体侧面积
        cylinder_area = math.pi * D * L
        
        # 两个椭圆封头面积
        head_area = 1.084 * math.pi * (D/2)**2
        total_head_area = 2 * head_area
        
        # 总表面积
        total_area = cylinder_area + total_head_area
        
        # 总重量
        total_volume = total_area * t
        total_weight = total_volume * density
        
        return total_weight
    
    def calculate_horizontal_liquid_weight(self, D, L, h, liquid_density):
        """计算卧式罐液体重量"""
        if h == 0:
            total_volume = 0
        elif h >= D:
            total_volume = math.pi * (D/2)**2 * L
        else:
            # 部分充液计算
            R = D/2
            theta = 2 * math.acos((R - h) / R)
            segment_area = R**2 * (theta - math.sin(theta)) / 2
            total_volume = segment_area * L
        
        liquid_weight = total_volume * liquid_density
        return liquid_weight
    
    def calculate_sphere_tank_weight(self, D, t, density):
        """计算球罐重量"""
        # 球体表面积
        sphere_area = 4 * math.pi * (D/2)**2
        
        # 总重量
        total_volume = sphere_area * t
        total_weight = total_volume * density
        
        return total_weight
    
    def calculate_sphere_liquid_weight(self, D, h, liquid_density):
        """计算球罐液体重量"""
        if h == 0:
            total_volume = 0
        elif h >= D:
            total_volume = (4/3) * math.pi * (D/2)**3
        else:
            # 球冠体积
            R = D/2
            volume = (1/3) * math.pi * h**2 * (3*R - h)
            total_volume = volume
        
        liquid_weight = total_volume * liquid_density
        return liquid_weight
    
    def display_results(self, tank_type, tank_weight, liquid_weight, material_density, liquid_density):
        """显示计算结果"""
        total_weight = tank_weight + liquid_weight
        
        result_text = f"""═══════════
📋 输入参数
══════════

    罐体类型: {tank_type}
    罐体密度: {material_density:,} kg/m³
    液体密度: {liquid_density:,} kg/m³

══════════
📊 计算结果
══════════

    重量分析:
    • 罐体空重: {tank_weight:,.1f} kg
    • 液体重量: {liquid_weight:,.1f} kg
    • 总重量: {total_weight:,.1f} kg

    单位换算:
    • 罐体空重: {tank_weight/1000:,.3f} 吨
    • 液体重量: {liquid_weight/1000:,.3f} 吨
    • 总重量: {total_weight/1000:,.3f} 吨

══════════
💡 设计建议
══════════

    • 总重量: {total_weight/1000:,.2f} 吨
    • 建议吊装设备能力不小于总重量的1.2倍
    • 基础设计应同时考虑罐体空重和操作重量
    • 运输时需考虑最大总重量

══════════
📝 备注说明
══════════

    • 计算结果为理论值，实际重量可能因制造工艺、附件等因素有所不同
    • 罐体重量计算基于简化几何模型
    • 液体重量计算基于满液状态或指定液位高度
    • 结果仅供参考，实际应用请考虑安全系数
"""
        
        self.result_text.setText(result_text)
    
    def clear_inputs(self):
        """清空输入"""
        # 重置所有输入为默认值
        self.type_button_group.button(0).setChecked(True)
        self.on_tank_type_changed(self.type_button_group.button(0))
        
        # 尺寸参数
        self.diameter_input.setText("3.0")
        self.height_input.setText("5.0")
        self.shell_thickness_input.setText("6.0")
        self.cone_height_input.setText("1.2")
        self.nozzle_diameter_input.setText("0.1")
        self.length_input.setText("5.0")
        self.liquid_level_input.setText("1.0")
        self.sphere_thickness_input.setText("6.0")
        
        # 材料参数
        self.material_combo.setCurrentIndex(1)  # 304不锈钢
        self.liquid_density_input.setText("1000")
        
        # 清空结果
        self.result_text.clear()
    
    def get_project_info(self):
        """获取工程信息 - 与压降计算相同"""
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
                    self.project_input.setPlaceholderText("例如：化工厂储罐系统")
                    self.project_input.setText(self.default_info.get('project_name', ''))
                    project_layout.addWidget(project_label)
                    project_layout.addWidget(self.project_input)
                    layout.addLayout(project_layout)
                    
                    # 子项名称
                    subproject_layout = QHBoxLayout()
                    subproject_label = QLabel("子项名称:")
                    subproject_label.setFixedWidth(80)
                    self.subproject_input = QLineEdit()
                    self.subproject_input.setPlaceholderText("例如：原料储罐区")
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
                report_number = self.data_manager.get_next_report_number("TANK")
            
            dialog = ProjectInfoDialog(self, saved_info, report_number)
            if dialog.exec() == QDialog.Accepted:
                info = dialog.get_info()
                # 验证必填字段
                if not info['project_name']:
                    QMessageBox.warning(self, "输入错误", "工程名称不能为空")
                    return self.get_project_info()  # 重新弹出对话框
                
                # 保存项目信息到数据管理器
                if self.data_manager:
                    # 保存所有项目信息
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
            
            # 检查是否有计算结果
            if not result_text or ("计算结果" not in result_text and "重量" not in result_text):
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            # 获取工程信息
            project_info = self.get_project_info()
            if not project_info:
                return None  # 用户取消了输入
            
            # 添加报告头信息
            from datetime import datetime
            report = f"""工程计算书 - 罐体重量计算
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

    1. 本计算书基于几何模型及材料密度计算
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
            
            # 直接调用 generate_report
            report_content = self.generate_report()
            if report_content is None:  # 如果返回None，说明检查失败或用户取消
                return
                
            # 选择保存路径
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"罐体重量计算书_{timestamp}.txt"
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
            # 直接调用 generate_report
            report_content = self.generate_report()
            if report_content is None:  # 如果返回None，说明检查失败或用户取消
                return False
                
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"罐体重量计算书_{timestamp}.pdf"
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
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                        "/Library/Fonts/Arial Unicode.ttf",
                        "/System/Library/Fonts/Arial.ttf",
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
                                elif "msyh" in font_path.lower():
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
                        pdfmetrics.registerFont(TTFont('ChineseFont', 'Helvetica'))
                except:
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
                title = Paragraph("工程计算书 - 罐体重量计算", chinese_style_heading)
                story.append(title)
                story.append(Spacer(1, 0.2*inch))
                
                # 处理报告内容，替换特殊字符和表情
                processed_content = self.process_content_for_pdf(report_content)
                
                # 添加内容
                for line in processed_content.split('\n'):
                    if line.strip():
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
            "📏": "",
            "🔩": "",
            "🏺": "",
            "📝": "",
            "🏷️": "",
            "•": ""
        }
        
        # 替换表情图标
        for emoji, text in replacements.items():
            content = content.replace(emoji, text)
        
        # 替换单位符号
        content = content.replace("m³", "m3")
        content = content.replace("kg/m³", "kg/m3")
        
        return content


if __name__ == "__main__":
    # 测试代码
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    calculator = 罐体重量()
    calculator.resize(1200, 800)
    calculator.setWindowTitle("罐体重量计算器")
    calculator.show()
    
    sys.exit(app.exec())