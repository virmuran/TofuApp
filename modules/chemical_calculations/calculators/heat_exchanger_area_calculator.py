from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QComboBox, QGridLayout, QTextEdit, QMessageBox, QDialog,
    QDialogButtonBox, QScrollArea, QSpinBox, QButtonGroup, QCheckBox,
    QFrame, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDoubleValidator
import math
import re
from datetime import datetime
from enum import Enum

# ==================== 枚举定义 ====================

class FlowArrangement(Enum):
    """流动方式枚举"""
    COUNTERCURRENT = "逆流"
    COCURRENT = "并流"

class HeatTransferMode(Enum):
    """传热模式枚举"""
    DIRECT = "直接计算法"
    FLUID_PARAMS = "流体参数法"
    STEAM_HEATING = "蒸汽加热法"
    INTELLIGENT = "智能选型"

# ==================== 主界面类 ====================

class 换热器面积(QWidget):
    """换热器面积计算器 - 统一UI风格版"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        
        # 初始化数据管理器
        self.data_manager = data_manager
        
        # 初始化数据
        self.specific_heat_data = self.setup_specific_heat_data()
        self.exchanger_types_data = self.setup_exchanger_types_data()
        self.flow_arrangements = list(FlowArrangement)
        self.steam_properties = {}  # 蒸汽物性数据缓存
        
        self.setup_ui()
        self.setup_mode_dependencies()
        
        # 连接信号
        self.mode_button_group.buttonClicked.connect(self.on_mode_button_clicked)
    
    def setup_specific_heat_data(self):
        """设置流体比热容数据 - 增加常用介质"""
        return {
            "水": 4.187,
            "95%乙醇": 2.51,
            "乙二醇": 2.35,
            "导热油": 2.9,
            "汽油": 2.22,
            "空气": 1.005,
            "氨气": 2.26,
            "苯": 1.36,
            "甲醇": 2.53,
            "盐水(20%)": 3.71
        }
    
    def setup_exchanger_types_data(self):
        """设置换热器类型数据 - 基于图片信息优化"""
        return {
            "管壳式换热器": {"k_range": (300, 1200), "desc": "结构简单，适应性强，耐高压"},
            "板式换热器": {"k_range": (2000, 7000), "desc": "传热效率高，结构紧凑"},
            "螺旋板式换热器": {"k_range": (500, 2200), "desc": "不易结垢，处理含固体颗粒"},
            "套管式换热器": {"k_range": (300, 800), "desc": "结构简单，耐高压"},
            "容积式加热器": {"k_range": (500, 1500), "desc": "蒸汽加热水专用，K=1160-3950"}
        }
    
    def calculate_steam_properties_from_gauge(self, pressure_gauge_MPa):
        """
        根据表压计算蒸汽物性参数
        输入：表压 (MPa)
        返回：饱和温度 (°C), 汽化潜热 (kJ/kg)
        """
        # 蒸汽表数据（表压MPa，饱和温度°C，汽化潜热kJ/kg）
        steam_data_gauge = [
            (0.0, 100.0, 2256.4),
            (0.1, 120.2, 2201.6),
            (0.2, 133.5, 2163.2),
            (0.3, 143.6, 2133.0),  # 常用压力点
            (0.4, 151.8, 2107.4),
            (0.5, 158.8, 2084.3),
            (0.6, 165.0, 2063.0),
            (0.7, 170.4, 2043.1),
            (0.8, 175.4, 2024.3),
            (0.9, 179.9, 2006.5),
            (1.0, 184.1, 1989.8)
        ]
        
        # 边界检查
        if pressure_gauge_MPa <= steam_data_gauge[0][0]:
            return {
                "saturation_temp": steam_data_gauge[0][1],
                "latent_heat": steam_data_gauge[0][2]
            }
        elif pressure_gauge_MPa >= steam_data_gauge[-1][0]:
            return {
                "saturation_temp": steam_data_gauge[-1][1],
                "latent_heat": steam_data_gauge[-1][2]
            }
        
        # 线性插值
        for i in range(len(steam_data_gauge)-1):
            P1, T1, r1 = steam_data_gauge[i]
            P2, T2, r2 = steam_data_gauge[i+1]
            
            if P1 <= pressure_gauge_MPa <= P2:
                factor = (pressure_gauge_MPa - P1) / (P2 - P1)
                T_sat = T1 + factor * (T2 - T1)
                latent_heat = r1 + factor * (r2 - r1)
                
                return {
                    "saturation_temp": round(T_sat, 1),
                    "latent_heat": round(latent_heat, 1)
                }
        
        # 默认返回100°C
        return {
            "saturation_temp": 100.0,
            "latent_heat": 2256.4
        }
    
    def setup_ui(self):
        """设置用户界面 - 与压降计算模块统一风格"""
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
            "基于《传热技术、设备与工业应用》原理，计算换热器传热面积，支持多种计算模式。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 然后添加计算模式选择
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
            ("直接计算", "已知热负荷、传热系数和温差"),
            ("流体参数", "根据流体进出口参数计算"),
            ("蒸汽加热", "使用蒸汽加热冷流体"),
            ("智能选型", "自动推荐换热器类型")
        ]
        
        for i, (mode_name, tooltip) in enumerate(modes):
            btn = QPushButton(mode_name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setFixedWidth(180)  # 固定宽度
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
        self.mode_buttons["直接计算"].setChecked(True)
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
        
        # 输入控件字典
        self.input_widgets = {}
        self.advanced_widgets = {}
        
        # 蒸汽加热专用控件
        self.steam_flow_label = None
        self.steam_temp_label = None
        
        left_layout.addWidget(input_group)
        
        # 4. 高级参数组
        advanced_group = QGroupBox("⚙️ 高级参数")
        advanced_group.setStyleSheet("""
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
        
        advanced_layout = QGridLayout(advanced_group)
        advanced_layout.setVerticalSpacing(10)
        advanced_layout.setHorizontalSpacing(10)
        
        # 安全系数
        safety_label = QLabel("安全系数:")
        safety_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        safety_label.setStyleSheet(label_style)
        advanced_layout.addWidget(safety_label, 0, 0)
        
        self.safety_factor_input = QLineEdit()
        self.safety_factor_input.setPlaceholderText("建议：1.10-1.30")
        self.safety_factor_input.setValidator(QDoubleValidator(1.0, 2.0, 2))
        self.safety_factor_input.setText("1.15")
        self.safety_factor_input.setFixedWidth(200)
        advanced_layout.addWidget(self.safety_factor_input, 0, 1)
        
        # 污垢系数
        fouling_label = QLabel("污垢系数 (m²·K/W):")
        fouling_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fouling_label.setStyleSheet(label_style)
        advanced_layout.addWidget(fouling_label, 0, 2)
        
        self.fouling_factor_input = QLineEdit()
        self.fouling_factor_input.setPlaceholderText("例如：0.0002")
        self.fouling_factor_input.setValidator(QDoubleValidator(0.00001, 0.01, 5))
        self.fouling_factor_input.setText("0.0002")
        self.fouling_factor_input.setFixedWidth(200)
        advanced_layout.addWidget(self.fouling_factor_input, 0, 3)
        
        left_layout.addWidget(advanced_group)
        
        # 5. 计算按钮
        calculate_btn = QPushButton("🧮 计算换热面积")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.calculate)
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
        
        # 7. 在底部添加拉伸因子，这样放大窗口时空白会出现在这里
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
    
    def setup_mode_dependencies(self):
        """设置计算模式的依赖关系"""
        # 初始状态 - 直接计算模式
        self.on_mode_changed("直接计算")
    
    def on_mode_button_clicked(self, button):
        """处理计算模式按钮点击"""
        mode_text = button.text()
        self.on_mode_changed(mode_text)
    
    def get_current_mode(self):
        """获取当前选择的计算模式"""
        checked_button = self.mode_button_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return "直接计算"
    
    def on_mode_changed(self, mode):
        """处理计算模式变化"""
        # 清除现有输入控件
        self.clear_widgets(self.input_layout)
        self.input_widgets.clear()
        
        # 标签样式
        label_style = """
            QLabel {
                font-weight: bold;
                padding-right: 10px;
            }
        """
        
        input_width = 400
        combo_width = 250
        
        row = 0
        
        if mode == "直接计算":
            self.setup_direct_calculation_mode(row, label_style, input_width, combo_width)
        elif mode == "流体参数":
            self.setup_fluid_parameters_mode(row, label_style, input_width, combo_width)
        elif mode == "蒸汽加热":
            self.setup_steam_heating_mode(row, label_style, input_width, combo_width)
        elif mode == "智能选型":
            self.setup_intelligent_selection_mode(row, label_style, input_width, combo_width)
    
    def setup_direct_calculation_mode(self, row, label_style, input_width, combo_width):
        """设置直接计算法界面"""
        # 热负荷 Q (kW)
        self.add_input_field(row, "热负荷 Q (kW):", "heat_load", "例如：1000", 
                            QDoubleValidator(0.1, 1000000, 1), input_width, label_style)
        row += 1

        # 温度参数
        temperatures = [
            ("热流体进口T1 (°C):", "hot_in_temp", "例如：90"),
            ("热流体出口T2 (°C):", "hot_out_temp", "例如：60"),
            ("冷流体进口t1 (°C):", "cold_in_temp", "例如：20"),
            ("冷流体出口t2 (°C):", "cold_out_temp", "例如：50")
        ]
        
        for label_text, key, placeholder in temperatures:
            self.add_input_field(row, label_text, key, placeholder,
                                QDoubleValidator(-273, 1000, 1), input_width, label_style)
            row += 1

        # 总传热系数
        self.add_k_value_section(row, input_width, combo_width, label_style)
        row += 1
        
        # 流动方式
        label = QLabel("流动方式:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["flow_arrangement"] = QComboBox()
        for arrangement in self.flow_arrangements:
            self.input_widgets["flow_arrangement"].addItem(arrangement.value)
        self.input_widgets["flow_arrangement"].setCurrentText("逆流")
        self.input_widgets["flow_arrangement"].setFixedWidth(combo_width)
        self.input_layout.addWidget(self.input_widgets["flow_arrangement"], row, 1)
    
    def setup_fluid_parameters_mode(self, row, label_style, input_width, combo_width):
        """设置流体参数法界面"""
        # 热流体参数
        hot_params = [
            ("热流体流量W1 (kg/h):", "hot_flow", "例如：5000"),
            ("热流体进口T1 (°C):", "hot_in_temp", "例如：90"),
            ("热流体出口T2 (°C):", "hot_out_temp", "例如：60")
        ]
        
        for label_text, key, placeholder in hot_params:
            self.add_input_field(row, label_text, key, placeholder,
                                QDoubleValidator(1, 1000000, 1) if "flow" in key else QDoubleValidator(-273, 1000, 1),
                                input_width, label_style)
            row += 1
        
        # 热流体比热容
        self.add_cp_section(row, "热流体比热容 Cp1 (kJ/kg·K):", "hot_cp", "hot_cp_combo", 
                           input_width, combo_width, label_style)
        row += 1

        # 冷流体参数
        cold_params = [
            ("冷流体流量W2 (kg/h):", "cold_flow", "例如：10000"),
            ("冷流体进口t1 (°C):", "cold_in_temp", "例如：20"),
            ("冷流体出口t2 (°C):", "cold_out_temp", "例如：50")
        ]
        
        for label_text, key, placeholder in cold_params:
            self.add_input_field(row, label_text, key, placeholder,
                                QDoubleValidator(1, 1000000, 1) if "flow" in key else QDoubleValidator(-273, 1000, 1),
                                input_width, label_style)
            row += 1
        
        # 冷流体比热容
        self.add_cp_section(row, "冷流体比热容 Cp2 (kJ/kg·K):", "cold_cp", "cold_cp_combo", 
                           input_width, combo_width, label_style)
        row += 1
        
        # 总传热系数
        self.add_k_value_section(row, input_width, combo_width, label_style)
        row += 1
        
        # 流动方式
        label = QLabel("流动方式:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["flow_arrangement"] = QComboBox()
        for arrangement in self.flow_arrangements:
            self.input_widgets["flow_arrangement"].addItem(arrangement.value)
        self.input_widgets["flow_arrangement"].setCurrentText("逆流")
        self.input_widgets["flow_arrangement"].setFixedWidth(combo_width)
        self.input_layout.addWidget(self.input_widgets["flow_arrangement"], row, 1)
    
    def setup_steam_heating_mode(self, row, label_style, input_width, combo_width):
        """设置蒸汽加热法界面"""
        # 计算类型选择
        label = QLabel("计算类型:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["calculation_type"] = QComboBox()
        self.input_widgets["calculation_type"].addItem("设计计算（计算蒸汽消耗）")
        self.input_widgets["calculation_type"].addItem("校核计算（给定蒸汽流量）")
        self.input_widgets["calculation_type"].setFixedWidth(combo_width)
        self.input_widgets["calculation_type"].currentTextChanged.connect(self.on_steam_calc_type_changed)
        self.input_layout.addWidget(self.input_widgets["calculation_type"], row, 1)
        
        row += 1
        
        # 蒸汽压力
        label = QLabel("蒸汽压力 (MPa):")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["steam_pressure"] = QLineEdit()
        self.input_widgets["steam_pressure"].setPlaceholderText("例如：0.3")
        self.input_widgets["steam_pressure"].setValidator(QDoubleValidator(0.01, 5.0, 3))
        self.input_widgets["steam_pressure"].setFixedWidth(input_width)
        self.input_widgets["steam_pressure"].textChanged.connect(self.update_steam_properties_display)
        self.input_layout.addWidget(self.input_widgets["steam_pressure"], row, 1)
        
        # 蒸汽温度显示
        self.steam_temp_label = QLabel("饱和温度: -- °C")
        self.steam_temp_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.input_layout.addWidget(self.steam_temp_label, row, 2)
        
        row += 1
        
        # 蒸汽流量（仅校核计算时显示）
        label = QLabel("蒸汽流量 (kg/h):")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["steam_flow"] = QLineEdit()
        self.input_widgets["steam_flow"].setPlaceholderText("仅校核计算需要")
        self.input_widgets["steam_flow"].setValidator(QDoubleValidator(1, 1000000, 1))
        self.input_widgets["steam_flow"].setFixedWidth(input_width)
        self.input_widgets["steam_flow"].setEnabled(False)
        self.input_layout.addWidget(self.input_widgets["steam_flow"], row, 1)
        
        self.steam_flow_label = QLabel("（设计计算自动计算）")
        self.steam_flow_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.input_layout.addWidget(self.steam_flow_label, row, 2)
        
        row += 1

        # 冷流体参数
        cold_params = [
            ("冷流体流量 (kg/h):", "cold_flow", "例如：270000"),
            ("冷流体进口t1 (°C):", "cold_in_temp", "例如：37"),
            ("冷流体出口t2 (°C):", "cold_out_temp", "例如：70")
        ]
        
        for label_text, key, placeholder in cold_params:
            self.add_input_field(row, label_text, key, placeholder,
                                QDoubleValidator(1, 1000000, 1) if "flow" in key else QDoubleValidator(-273, 1000, 1),
                                input_width, label_style)
            row += 1
        
        # 冷流体比热容
        self.add_cp_section(row, "冷流体比热容 Cp2 (kJ/kg·K):", "cold_cp", "cold_cp_combo", 
                           input_width, combo_width, label_style)
        row += 1
        
        # 总传热系数
        self.add_k_value_section(row, input_width, combo_width, label_style)
        
    def on_steam_calc_type_changed(self, text):
        """蒸汽计算类型变化处理"""
        if "校核计算" in text:
            self.input_widgets["steam_flow"].setEnabled(True)
            self.input_widgets["steam_flow"].setPlaceholderText("请输入蒸汽流量")
            if self.steam_flow_label:
                self.steam_flow_label.setText("请输入蒸汽流量")
        else:
            self.input_widgets["steam_flow"].setEnabled(False)
            self.input_widgets["steam_flow"].clear()
            self.input_widgets["steam_flow"].setPlaceholderText("仅校核计算需要")
            if self.steam_flow_label:
                self.steam_flow_label.setText("（设计计算自动计算）")
    
    def update_steam_properties_display(self):
        """更新蒸汽物性显示"""
        try:
            pressure_text = self.input_widgets["steam_pressure"].text().strip()
            if pressure_text:
                pressure_gauge = float(pressure_text)
                
                # 直接使用表压计算
                props = self.calculate_steam_properties_from_gauge(pressure_gauge)
                
                # 更新显示
                if self.steam_temp_label:
                    self.steam_temp_label.setText(
                        f"饱和温度: {props['saturation_temp']} °C\n"
                        f"汽化潜热: {props['latent_heat']} kJ/kg"
                    )
                
                # 保存供后续使用
                self.steam_properties = props
        except ValueError:
            if self.steam_temp_label:
                self.steam_temp_label.setText("饱和温度: -- °C\n汽化潜热: -- kJ/kg")
    
    def setup_intelligent_selection_mode(self, row, label_style, input_width, combo_width):
        """设置智能选型模式界面"""
        # 操作条件
        conditions = [
            ("操作压力 (MPa):", "operating_pressure", "例如：0.5"),
            ("操作温度 (°C):", "operating_temperature", "例如：100"),
            ("流量 (kg/h):", "flow_rate", "例如：5000")
        ]
        
        for label_text, key, placeholder in conditions:
            self.add_input_field(row, label_text, key, placeholder,
                                QDoubleValidator(0.01, 35.0, 2) if "pressure" in key else 
                                QDoubleValidator(1, 1000000, 1) if "flow" in key else 
                                QDoubleValidator(-273, 1000, 1),
                                input_width, label_style)
            row += 1
        
        # 流体类型
        label = QLabel("流体类型:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        fluid_types = ["水/液体", "气体", "蒸汽", "粘稠流体", "腐蚀性流体"]
        self.input_widgets["fluid_type"] = QComboBox()
        for fluid in fluid_types:
            self.input_widgets["fluid_type"].addItem(fluid)
        self.input_widgets["fluid_type"].setFixedWidth(combo_width)
        self.input_layout.addWidget(self.input_widgets["fluid_type"], row, 1)
        
        row += 1
        
        # 特殊条件
        self.input_widgets["fouling_tendency"] = QCheckBox("易结垢")
        self.input_widgets["fouling_tendency"].setStyleSheet("color: #2c3e50; padding: 5px;")
        self.input_layout.addWidget(self.input_widgets["fouling_tendency"], row, 1)
        
        self.input_widgets["high_pressure"] = QCheckBox("高压操作")
        self.input_widgets["high_pressure"].setStyleSheet("color: #2c3e50; padding: 5px;")
        self.input_layout.addWidget(self.input_widgets["high_pressure"], row, 2)
        
        row += 1
        
        self.input_widgets["corrosive"] = QCheckBox("腐蚀性")
        self.input_widgets["corrosive"].setStyleSheet("color: #2c3e50; padding: 5px;")
        self.input_layout.addWidget(self.input_widgets["corrosive"], row, 1)
        
        self.input_widgets["phase_change"] = QCheckBox("相变过程")
        self.input_widgets["phase_change"].setStyleSheet("color: #2c3e50; padding: 5px;")
        self.input_layout.addWidget(self.input_widgets["phase_change"], row, 2)
    
    def add_input_field(self, row, label_text, key, placeholder, validator, width, style):
        """添加输入字段辅助函数"""
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets[key] = QLineEdit()
        self.input_widgets[key].setPlaceholderText(placeholder)
        self.input_widgets[key].setValidator(validator)
        self.input_widgets[key].setFixedWidth(width)
        self.input_layout.addWidget(self.input_widgets[key], row, 1)
        
        # 添加提示标签
        hint_label = QLabel("直接输入值")
        hint_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        hint_label.setFixedWidth(250)
        self.input_layout.addWidget(hint_label, row, 2)
    
    def add_cp_section(self, row, label_text, cp_key, combo_key, input_width, combo_width, label_style):
        """添加比热容选择部分"""
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets[cp_key] = QLineEdit()
        self.input_widgets[cp_key].setPlaceholderText("输入或选择")
        self.input_widgets[cp_key].setValidator(QDoubleValidator(0.1, 20.0, 3))
        self.input_widgets[cp_key].setFixedWidth(input_width)
        self.input_layout.addWidget(self.input_widgets[cp_key], row, 1)
        
        self.input_widgets[combo_key] = QComboBox()
        self.input_widgets[combo_key].addItem("- 选择流体类型 -")
        for fluid in self.specific_heat_data.keys():
            self.input_widgets[combo_key].addItem(fluid)
        self.input_widgets[combo_key].setFixedWidth(combo_width)
        self.input_widgets[combo_key].currentTextChanged.connect(
            lambda text, cp_key=cp_key: self.on_cp_selected(text, self.input_widgets[cp_key])
        )
        self.input_layout.addWidget(self.input_widgets[combo_key], row, 2)
    
    def add_k_value_section(self, row, input_width, combo_width, label_style):
        """添加K值选择部分"""
        label = QLabel("总传热系数K (W/m²·K):")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(label_style)
        self.input_layout.addWidget(label, row, 0)
        
        self.input_widgets["k_value"] = QLineEdit()
        self.input_widgets["k_value"].setPlaceholderText("选择类型后推荐")
        self.input_widgets["k_value"].setValidator(QDoubleValidator(10, 10000, 1))
        self.input_widgets["k_value"].setFixedWidth(input_width)
        self.input_layout.addWidget(self.input_widgets["k_value"], row, 1)
        
        self.input_widgets["exchanger_type"] = QComboBox()
        self.input_widgets["exchanger_type"].addItem("- 选择换热器类型 -")
        for exchanger_type in self.exchanger_types_data.keys():
            self.input_widgets["exchanger_type"].addItem(exchanger_type)
        self.input_widgets["exchanger_type"].setFixedWidth(combo_width)
        self.input_widgets["exchanger_type"].currentTextChanged.connect(self.on_exchanger_type_changed)
        self.input_layout.addWidget(self.input_widgets["exchanger_type"], row, 2)
    
    def add_separator(self, row):
        """添加分隔线"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        self.input_layout.addWidget(line, row, 0, 1, 3)
    
    def clear_widgets(self, layout):
        """清除布局中的所有控件"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
    def on_cp_selected(self, text, lineedit):
        """处理比热容选择"""
        if text.startswith("-") or not text.strip():
            return
        
        if text in self.specific_heat_data:
            cp_value = self.specific_heat_data[text]
            lineedit.setText(f"{cp_value:.3f}")
    
    def on_exchanger_type_changed(self, text):
        """处理换热器类型选择变化"""
        if text.startswith("-") or not text.strip():
            return
        
        if text in self.exchanger_types_data:
            k_range = self.exchanger_types_data[text]["k_range"]
            recommended = (k_range[0] + k_range[1]) / 2
            
            # 更新K值输入框
            if "k_value" in self.input_widgets:
                self.input_widgets["k_value"].setText(f"{recommended:.0f}")
    
    def get_widget_value(self, key, default=None):
        """获取控件值"""
        if key in self.input_widgets:
            widget = self.input_widgets[key]
            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
                if text:
                    try:
                        return float(text)
                    except:
                        return text
            elif isinstance(widget, QComboBox):
                return widget.currentText()
            elif isinstance(widget, QCheckBox):
                return widget.isChecked()
        return default
    
    def get_advanced_value(self, key, default=None):
        """获取高级参数值"""
        if key == "safety_factor":
            text = self.safety_factor_input.text().strip()
            if text:
                try:
                    return float(text)
                except:
                    return default
            return default
        elif key == "fouling_factor":
            text = self.fouling_factor_input.text().strip()
            if text:
                try:
                    return float(text)
                except:
                    return default
            return default
        return default
    
    def validate_inputs(self, inputs, required_fields):
        """验证输入参数是否完整"""
        missing_fields = []
        for field in required_fields:
            value = inputs.get(field)
            if value is None or value == "":
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"请填写以下必需参数：{', '.join(missing_fields)}"
        return True, ""
    
    def calculate(self):
        """执行计算"""
        try:
            mode = self.get_current_mode()
            
            if mode == "直接计算":
                self.calculate_mode_0()
            elif mode == "流体参数":
                self.calculate_mode_1()
            elif mode == "蒸汽加热":
                self.calculate_mode_2()
            elif mode == "智能选型":
                self.perform_intelligent_selection()
            else:
                QMessageBox.warning(self, "计算错误", "请选择计算模式")
                
        except ValueError as e:
            QMessageBox.critical(self, "输入错误", f"参数输入格式错误: {str(e)}")
        except ZeroDivisionError:
            QMessageBox.critical(self, "计算错误", "参数不能为零")
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def calculate_mode_0(self):
        """模式0：直接计算法"""
        # 获取输入值
        Q_heat = self.get_widget_value("heat_load")  # kW
        K = self.get_widget_value("k_value")  # W/m²·K
        T1 = self.get_widget_value("hot_in_temp")  # °C
        T2 = self.get_widget_value("hot_out_temp")  # °C
        t1 = self.get_widget_value("cold_in_temp")  # °C
        t2 = self.get_widget_value("cold_out_temp")  # °C
        flow_arrangement = self.get_widget_value("flow_arrangement", "逆流")
        safety_factor = self.get_advanced_value("safety_factor", 1.15)
        
        # 验证输入
        required_fields = ["heat_load", "k_value", "hot_in_temp", "hot_out_temp", 
                          "cold_in_temp", "cold_out_temp"]
        inputs = {
            "heat_load": Q_heat, "k_value": K, "hot_in_temp": T1, 
            "hot_out_temp": T2, "cold_in_temp": t1, "cold_out_temp": t2
        }
        
        is_valid, error_msg = self.validate_inputs(inputs, required_fields)
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        # 数学公式计算
        try:
            # 热负荷单位转换: kW → W
            Q = Q_heat * 1000
            
            # 计算对数平均温差
            if flow_arrangement == "逆流":
                ΔT1 = T1 - t2
                ΔT2 = T2 - t1
            else:  # 并流
                ΔT1 = T1 - t1
                ΔT2 = T2 - t2
            
            if ΔT1 <= 0 or ΔT2 <= 0:
                raise ValueError(f"温度差出现负值：ΔT1={ΔT1:.1f}°C，ΔT2={ΔT2:.1f}°C")
            
            # 对数平均温差
            if abs(ΔT1 - ΔT2) < 1e-10:
                ΔT_m = ΔT1
            else:
                ΔT_m = (ΔT1 - ΔT2) / math.log(ΔT1 / ΔT2)
            
            # 传热面积
            A_theoretical = Q / (K * ΔT_m)
            A_design = A_theoretical * safety_factor
            
            # 计算面积裕度
            margin_percent = ((A_design / A_theoretical) - 1) * 100
            
            # 准备结果
            result_text = f"""═══════════
📋 输入参数
══════════

    计算模式: 直接计算法
    热负荷: {Q_heat:.1f} kW
    总传热系数: {K:.0f} W/(m²·K)
    热流体温度: {T1:.1f} → {T2:.1f} °C
    冷流体温度: {t1:.1f} → {t2:.1f} °C
    流动方式: {flow_arrangement}
    安全系数: {safety_factor:.2f}

══════════
📊 计算结果
══════════

    温差分析:
    • ΔT1 = {ΔT1:.1f} °C
    • ΔT2 = {ΔT2:.1f} °C
    • 对数平均温差 ΔT_m = {ΔT_m:.1f} °C

    面积计算:
    • 理论传热面积: {A_theoretical:.3f} m²
    • 设计传热面积: {A_design:.3f} m²
    • 面积裕量: {A_design - A_theoretical:.3f} m²
    • 面积裕度: {margin_percent:.1f}%

    单位换算:
    • 理论面积: {A_theoretical * 10.7639:.1f} ft²
    • 设计面积: {A_design * 10.7639:.1f} ft²

══════════
💡 计算说明
══════════

    • 使用对数平均温差法计算
    • 设计面积已考虑{safety_factor:.2f}倍安全系数
    • 面积裕度{margin_percent:.1f}%确保长期运行可靠性
    • 结果仅供参考，实际选型需考虑设备制造标准
"""
            
            self.result_text.setText(result_text)
            
        except ValueError as e:
            QMessageBox.warning(self, "计算错误", str(e))
    
    def calculate_mode_1(self):
        """模式1：流体参数法"""
        # 获取输入值
        W1 = self.get_widget_value("hot_flow")  # kg/h
        T1 = self.get_widget_value("hot_in_temp")  # °C
        T2 = self.get_widget_value("hot_out_temp")  # °C
        Cp1 = self.get_widget_value("hot_cp")  # kJ/kg·K
        W2 = self.get_widget_value("cold_flow")  # kg/h
        t1 = self.get_widget_value("cold_in_temp")  # °C
        t2 = self.get_widget_value("cold_out_temp")  # °C
        Cp2 = self.get_widget_value("cold_cp")  # kJ/kg·K
        K = self.get_widget_value("k_value")  # W/m²·K
        flow_arrangement = self.get_widget_value("flow_arrangement", "逆流")
        safety_factor = self.get_advanced_value("safety_factor", 1.15)
        
        # 验证输入
        required_fields = ["hot_flow", "hot_in_temp", "hot_out_temp", "hot_cp",
                          "cold_flow", "cold_in_temp", "cold_out_temp", "cold_cp", "k_value"]
        inputs = {
            "hot_flow": W1, "hot_in_temp": T1, "hot_out_temp": T2, "hot_cp": Cp1,
            "cold_flow": W2, "cold_in_temp": t1, "cold_out_temp": t2, "cold_cp": Cp2, 
            "k_value": K
        }
        
        is_valid, error_msg = self.validate_inputs(inputs, required_fields)
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        # 数学公式计算
        try:
            # 单位转换
            W1_kg_s = W1 / 3600  # kg/h → kg/s
            W2_kg_s = W2 / 3600
            Cp1_J = Cp1 * 1000  # kJ/kg·K → J/kg·K
            Cp2_J = Cp2 * 1000
            
            # 热负荷计算
            Q_hot = W1_kg_s * Cp1_J * (T1 - T2)  # W
            Q_cold = W2_kg_s * Cp2_J * (t2 - t1)  # W
            
            # 检查能量平衡
            if Q_hot > 0 and Q_cold > 0:
                balance_error = abs(Q_hot - Q_cold) / max(Q_hot, Q_cold) * 100
            else:
                balance_error = 100.0
            
            # 热平衡警告
            if balance_error > 15:
                reply = QMessageBox.warning(
                    self, 
                    "热负荷不平衡",
                    f"热平衡误差较大: {balance_error:.1f}%\n"
                    f"热侧放热: {Q_hot/1000:.1f} kW\n"
                    f"冷侧吸热: {Q_cold/1000:.1f} kW\n\n"
                    "是否继续计算？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 设计热负荷取较小值（安全原则）
            Q_design = min(Q_hot, Q_cold)
            
            # 计算对数平均温差
            if flow_arrangement == "逆流":
                ΔT1 = T1 - t2
                ΔT2 = T2 - t1
            else:  # 并流
                ΔT1 = T1 - t1
                ΔT2 = T2 - t2
            
            if ΔT1 <= 0 or ΔT2 <= 0:
                raise ValueError("温度差出现负值，请检查进出口温度设置")
            
            # 对数平均温差
            if abs(ΔT1 - ΔT2) < 1e-10:
                ΔT_m = ΔT1
            else:
                ΔT_m = (ΔT1 - ΔT2) / math.log(ΔT1 / ΔT2)
            
            # 传热面积
            A_theoretical = Q_design / (K * ΔT_m)
            A_design = A_theoretical * safety_factor
            
            # 准备结果
            result_text = f"""═══════════
📋 输入参数
══════════

    计算模式: 流体参数法
    热流体流量: {W1:.0f} kg/h
    热流体温度: {T1:.1f} → {T2:.1f} °C
    热流体比热容: {Cp1:.3f} kJ/(kg·K)
    冷流体流量: {W2:.0f} kg/h
    冷流体温度: {t1:.1f} → {t2:.1f} °C
    冷流体比热容: {Cp2:.3f} kJ/(kg·K)
    总传热系数: {K:.0f} W/(m²·K)
    流动方式: {flow_arrangement}
    安全系数: {safety_factor:.2f}

══════════
📊 计算结果
══════════

    热负荷分析:
    • 热流体放热量: {Q_hot/1000:.2f} kW
    • 冷流体吸热量: {Q_cold/1000:.2f} kW
    • 设计热负荷: {Q_design/1000:.2f} kW
    • 热平衡误差: {balance_error:.1f}%

    温差分析:
    • ΔT1 = {ΔT1:.1f} °C
    • ΔT2 = {ΔT2:.1f} °C
    • 对数平均温差 ΔT_m = {ΔT_m:.1f} °C

    面积计算:
    • 理论传热面积: {A_theoretical:.3f} m²
    • 设计传热面积: {A_design:.3f} m²
    • 面积裕量: {A_design - A_theoretical:.3f} m²

══════════
💡 计算说明
══════════

    • 采用较小热负荷值进行设计以确保安全
    • 安全系数{safety_factor:.2f}考虑污垢及运行波动
    • 推荐定期清洗维护以保证换热效率
"""
            
            self.result_text.setText(result_text)
            
        except ValueError as e:
            QMessageBox.warning(self, "计算错误", str(e))
    
    def calculate_mode_2(self):
        """模式2：蒸汽加热法 - 修正逻辑"""
        try:
            # 获取计算类型
            calculation_type = self.get_widget_value("calculation_type", "设计计算（计算蒸汽消耗）")
            is_design_calculation = "设计计算" in calculation_type
            
            # 获取输入值
            steam_pressure = self.get_widget_value("steam_pressure")  # MPa（表压）
            
            if not is_design_calculation:
                # 校核计算：获取蒸汽流量
                steam_flow = self.get_widget_value("steam_flow")
                if steam_flow is None:
                    QMessageBox.warning(self, "输入错误", "校核计算需要输入蒸汽流量")
                    return
            
            W2 = self.get_widget_value("cold_flow")  # kg/h
            t1 = self.get_widget_value("cold_in_temp")  # °C
            t2 = self.get_widget_value("cold_out_temp")  # °C
            Cp2 = self.get_widget_value("cold_cp")  # kJ/kg·K
            K = self.get_widget_value("k_value")  # W/m²·K
            safety_factor = self.get_advanced_value("safety_factor", 1.15)
            
            # 验证输入
            required_fields = ["steam_pressure", "cold_flow", "cold_in_temp", 
                            "cold_out_temp", "cold_cp", "k_value"]
            
            if not is_design_calculation:
                required_fields.append("steam_flow")
            
            inputs = {
                "steam_pressure": steam_pressure, 
                "cold_flow": W2, "cold_in_temp": t1, "cold_out_temp": t2, 
                "cold_cp": Cp2, "k_value": K
            }
            
            if not is_design_calculation:
                inputs["steam_flow"] = steam_flow
            
            is_valid, error_msg = self.validate_inputs(inputs, required_fields)
            if not is_valid:
                QMessageBox.warning(self, "输入错误", error_msg)
                return
            
            # 1. 计算蒸汽物性（使用表压）
            steam_props = self.calculate_steam_properties_from_gauge(steam_pressure)
            T_steam = steam_props["saturation_temp"]
            steam_latent_heat = steam_props["latent_heat"]  # kJ/kg
            
            # 2. 单位转换
            W2_kg_s = W2 / 3600  # kg/h → kg/s
            Cp2_J = Cp2 * 1000  # kJ/kg·K → J/kg·K
            steam_latent_heat_J = steam_latent_heat * 1000  # kJ/kg → J/kg
            
            # 3. 计算冷流体热负荷
            Q_cold = W2_kg_s * Cp2_J * (t2 - t1)  # W
            
            if is_design_calculation:
                # 设计计算：计算理论蒸汽消耗量
                steam_consumption = Q_cold * 3600 / steam_latent_heat_J  # kg/h
                Q_steam = steam_consumption / 3600 * steam_latent_heat_J  # W
                balance_error = 0.0  # 设计计算时假设完美平衡
                design_q = Q_cold
                steam_flow_used = steam_consumption
                calculation_note = "✅ 设计计算：根据冷流体需求计算蒸汽消耗"
            else:
                # 校核计算：使用输入的蒸汽流量
                steam_flow_kg_s = steam_flow / 3600  # kg/h → kg/s
                Q_steam = steam_flow_kg_s * steam_latent_heat_J  # W
                steam_consumption = steam_flow  # 使用输入的蒸汽流量
                
                # 计算热平衡误差
                if Q_steam > 0 and Q_cold > 0:
                    balance_error = abs(Q_steam - Q_cold) / max(Q_steam, Q_cold) * 100
                else:
                    balance_error = 100.0
                
                # 设计热负荷取较小值（安全原则）
                design_q = min(Q_steam, Q_cold)
                steam_flow_used = steam_flow
                calculation_note = f"🔍 校核计算：给定蒸汽流量{steam_flow:.0f} kg/h"
            
            # 4. 检查冷流体出口温度
            if t2 >= T_steam:
                QMessageBox.warning(self, "温度错误", 
                    f"冷流体出口温度{t2:.1f}°C不能高于蒸汽饱和温度{T_steam:.1f}°C")
                return
            
            # 5. 温差计算
            ΔT1 = T_steam - t1
            ΔT2 = T_steam - t2
            
            # 对数平均温差
            if abs(ΔT1 - ΔT2) < 1e-10:
                ΔT_m = ΔT1
            else:
                ΔT_m = (ΔT1 - ΔT2) / math.log(ΔT1 / ΔT2)
            
            # 6. 传热面积计算
            A_theoretical = design_q / (K * ΔT_m)
            A_design = A_theoretical * safety_factor
            
            # 7. 准备结果
            mode_text = "蒸汽加热法（设计计算）" if is_design_calculation else "蒸汽加热法（校核计算）"
            P_abs = steam_pressure + 0.101325  # 表压转绝对压力
            
            result_text = f"""═══════════
📋 输入参数
══════════

    计算模式: {mode_text}
    蒸汽压力: {steam_pressure:.3f} MPa（表压）
    蒸汽绝对压力: {P_abs:.3f} MPa（绝对）
{f"    蒸汽流量: {steam_flow_used:.0f} kg/h" if not is_design_calculation else ""}
    冷流体流量: {W2:.0f} kg/h
    冷流体温度: {t1:.1f} → {t2:.1f} °C
    冷流体比热容: {Cp2:.3f} kJ/(kg·K)
    总传热系数: {K:.0f} W/(m²·K)
    安全系数: {safety_factor:.2f}

══════════
📊 计算结果
══════════

    蒸汽参数:
    • 饱和温度: {T_steam:.1f} °C
    • 汽化潜热: {steam_latent_heat:.0f} kJ/kg

    热负荷分析:
    • 冷流体吸热量: {Q_cold/1000:.2f} kW
    • 蒸汽放热量: {Q_steam/1000:.2f} kW
    • 设计热负荷: {design_q/1000:.2f} kW
{f"    • 热平衡误差: {balance_error:.1f}%" if not is_design_calculation else ""}
    • 理论蒸汽消耗: {steam_consumption:.0f} kg/h

    温差分析:
    • ΔT1 (蒸汽-冷流体进口): {ΔT1:.1f} °C
    • ΔT2 (蒸汽-冷流体出口): {ΔT2:.1f} °C
    • 对数平均温差 ΔT_m = {ΔT_m:.1f} °C

    面积计算:
    • 理论传热面积: {A_theoretical:.3f} m²
    • 设计传热面积: {A_design:.3f} m²
    • 面积裕量: {A_design - A_theoretical:.3f} m²
    • 面积裕度: {((A_design/A_theoretical)-1)*100:.1f}%

══════════
💡 计算说明
══════════

    • 蒸汽压力为表压，绝对压力 = 表压 + 0.101325 MPa
    • 设计面积已考虑{safety_factor:.2f}倍安全系数
    • 面积裕度{((A_design/A_theoretical)-1)*100:.1f}%确保长期运行可靠性
    • 蒸汽加热器设计时需考虑冷凝水排放问题
"""
            
            self.result_text.setText(result_text)
            
        except ValueError as e:
            QMessageBox.warning(self, "计算错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"蒸汽加热计算失败: {str(e)}")
    
    def perform_intelligent_selection(self):
        """智能选型"""
        # 获取输入值
        pressure = self.get_widget_value("operating_pressure")  # MPa
        temperature = self.get_widget_value("operating_temperature")  # °C
        flow_rate = self.get_widget_value("flow_rate")  # kg/h
        fluid_type = self.get_widget_value("fluid_type", "水/液体")
        fouling_tendency = self.get_widget_value("fouling_tendency", False)
        high_pressure = self.get_widget_value("high_pressure", False)
        corrosive = self.get_widget_value("corrosive", False)
        phase_change = self.get_widget_value("phase_change", False)
        
        # 验证输入
        required_fields = ["operating_pressure", "operating_temperature", "flow_rate"]
        inputs = {
            "operating_pressure": pressure, 
            "operating_temperature": temperature, 
            "flow_rate": flow_rate
        }
        
        is_valid, error_msg = self.validate_inputs(inputs, required_fields)
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        # 智能选型逻辑
        recommendations = []
        
        for ex_type, data in self.exchanger_types_data.items():
            score = 0
            reasons = []
            
            # 压力适应性评分
            k_min, k_max = data["k_range"]
            pressure_limit = 10.0 if ex_type in ["管壳式换热器", "套管式换热器"] else 2.5
            
            if pressure <= pressure_limit:
                score += 3
                reasons.append(f"压力适应性好")
            elif pressure <= pressure_limit * 1.5:
                score += 1
                reasons.append(f"压力适应性一般")
            
            # 温度适应性评分
            temp_limit = 500 if ex_type == "管壳式换热器" else 200
            if temperature <= temp_limit:
                score += 3
                reasons.append(f"温度适应性好")
            
            # 流体类型匹配
            if "蒸汽" in fluid_type and "容积式" in ex_type:
                score += 2
                reasons.append("蒸汽加热专用")
            
            if "液体" in fluid_type and ex_type in ["板式换热器", "螺旋板式换热器"]:
                score += 1
                reasons.append("液体传热效率高")
            
            # 特殊条件处理
            if fouling_tendency and ex_type in ["螺旋板式换热器", "套管式换热器"]:
                score += 2
                reasons.append("防结垢设计")
            
            if high_pressure and ex_type in ["管壳式换热器", "套管式换热器"]:
                score += 2
                reasons.append("耐高压结构")
            
            if corrosive and ex_type in ["板式换热器"]:
                score += 1
                reasons.append("可选用耐蚀材料")
            
            if phase_change and ex_type == "管壳式换热器":
                score += 2
                reasons.append("相变传热适用")
            
            recommendations.append({
                "type": ex_type,
                "score": score,
                "reasons": reasons,
                "k_range": data["k_range"],
                "description": data["desc"]
            })
        
        # 排序并筛选
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        top_recommendations = [r for r in recommendations if r["score"] > 0][:4]
        
        # 准备结果
        result_text = f"""═══════════
📋 输入工况
══════════

    操作压力: {pressure:.2f} MPa
    操作温度: {temperature:.0f} °C
    流量: {flow_rate:.0f} kg/h
    流体类型: {fluid_type}
    特殊条件: {f"易结垢 " if fouling_tendency else ""}{f"高压 " if high_pressure else ""}{f"腐蚀性 " if corrosive else ""}{f"相变 " if phase_change else ""}

══════════
🏆 推荐换热器类型
══════════

"""
        
        if not top_recommendations:
            result_text += "❌ 未找到合适的换热器类型，请调整工况条件。\n"
        else:
            for i, rec in enumerate(top_recommendations, 1):
                score_percent = rec["score"] / 12 * 100
                result_text += f"{i}. {rec['type']} (匹配度: {score_percent:.0f}%)\n"
                result_text += f"   📊 传热系数范围: {rec['k_range'][0]}-{rec['k_range'][1]} W/(m²·K)\n"
                result_text += f"   📝 特点: {rec['description']}\n"
                if rec['reasons']:
                    result_text += f"   ✅ 推荐理由: {', '.join(rec['reasons'])}\n"
                result_text += "\n"
        
        result_text += """══════════
💡 选型建议
══════════

    通用原则:
    • 匹配度>80%的类型可作为首选
    • 考虑设备投资和运行维护成本
    • 腐蚀性介质需特别关注材料选择
    • 易结垢流体优先选择易清洗结构

    下一步:
    • 根据推荐类型返回相应模式进行详细计算
    • 咨询设备制造商获取具体技术参数
    • 考虑安装空间和管道布置限制
"""
        
        self.result_text.setText(result_text)
    
    # ==================== 报告生成功能 ====================
    
    def get_project_info(self):
        """获取工程信息"""
        try:
            # 简化的工程信息对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("工程信息")
            dialog.setFixedSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            title = QLabel("请输入工程信息")
            title.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
            layout.addWidget(title)
            
            company_layout = QHBoxLayout()
            company_label = QLabel("公司名称:")
            company_label.setFixedWidth(80)
            company_input = QLineEdit()
            company_input.setPlaceholderText("例如：XX工程公司")
            company_layout.addWidget(company_label)
            company_layout.addWidget(company_input)
            layout.addLayout(company_layout)
            
            project_layout = QHBoxLayout()
            project_label = QLabel("项目名称:")
            project_label.setFixedWidth(80)
            project_input = QLineEdit()
            project_input.setPlaceholderText("例如：化工厂换热系统")
            project_layout.addWidget(project_label)
            project_layout.addWidget(project_input)
            layout.addLayout(project_layout)
            
            designer_layout = QHBoxLayout()
            designer_label = QLabel("设计人员:")
            designer_label.setFixedWidth(80)
            designer_input = QLineEdit()
            designer_input.setPlaceholderText("例如：张工")
            designer_layout.addWidget(designer_label)
            designer_layout.addWidget(designer_input)
            layout.addLayout(designer_layout)
            
            date_layout = QHBoxLayout()
            date_label = QLabel("计算日期:")
            date_label.setFixedWidth(80)
            date_input = QLineEdit()
            date_input.setText(datetime.now().strftime('%Y-%m-%d'))
            date_input.setReadOnly(True)
            date_layout.addWidget(date_label)
            date_layout.addWidget(date_input)
            layout.addLayout(date_layout)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            if dialog.exec() == QDialog.Accepted:
                return {
                    'company_name': company_input.text().strip() or "未填写",
                    'project_name': project_input.text().strip() or "换热器设计",
                    'designer': designer_input.text().strip() or "设计人员",
                    'date': date_input.text()
                }
            else:
                return None
                    
        except Exception as e:
            print(f"获取工程信息失败: {e}")
            return {
                'company_name': "换热器设计",
                'project_name': "换热器计算",
                'designer': "设计人员",
                'date': datetime.now().strftime('%Y-%m-%d')
            }
    
    def generate_report(self):
        """生成计算书"""
        try:
            result_text = self.result_text.toPlainText()
            
            if not result_text or "计算结果" not in result_text:
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            project_info = self.get_project_info()
            if not project_info:
                return None
            
            current_mode = self.get_current_mode()
            
            report = f"""工程计算书 - 换热器面积计算
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
    项目名称: {project_info['project_name']}
    设计人员: {project_info['designer']}
    计算日期: {project_info['date']}

══════════
🏷️ 计算书标识
══════════

    计算书编号: HE-{datetime.now().strftime('%Y%m%d')}-001
    版本: 1.0
    状态: 正式计算书

══════════
📝 备注说明
══════════

    1. 本计算书基于《传热技术、设备与工业应用》原理
    2. 计算结果仅供参考，实际设计需考虑详细工况
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
            default_name = f"换热器面积计算书_{timestamp}.txt"
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
            default_name = f"换热器面积计算书_{timestamp}.pdf"
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
                title = Paragraph("工程计算书 - 换热器面积计算", chinese_style_heading)
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
            "⚙️": "",
            "🏷️": "",
            "📝": "",
            "🏆": "",
            "❌": "",
            "✅": "",
            "🔍": ""
        }
        
        # 替换表情图标
        for emoji, text in replacements.items():
            content = content.replace(emoji, text)
        
        # 替换单位符号
        content = content.replace("m²", "m2")
        content = content.replace("W/(m²·K)", "W/(m2·K)")
        content = content.replace("kJ/(kg·K)", "kJ/(kg·K)")
        
        return content


if __name__ == "__main__":
    # 测试代码
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    calculator = 换热器面积()
    calculator.resize(1200, 800)
    calculator.setWindowTitle("换热器面积计算器 v2.0")
    calculator.show()
    
    sys.exit(app.exec())