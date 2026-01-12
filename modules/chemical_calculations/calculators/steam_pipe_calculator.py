from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QGridLayout, QMessageBox,
    QFrame, QButtonGroup, QFileDialog, QDialog, QDialogButtonBox
)
from PySide6.QtGui import QFont, QDoubleValidator
from PySide6.QtCore import Qt
import math
import re
from datetime import datetime


class 蒸汽管径流量(QWidget):
    """蒸汽管径和流量查询（左右布局优化版 - 统一UI风格）"""
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        
        # 使用传入的数据管理器或创建新的
        if data_manager is not None:
            self.data_manager = data_manager
        else:
            self.init_data_manager()
            
        self.setup_ui()
        self.setup_widget_references()
    
    def init_data_manager(self):
        """初始化数据管理器 - 使用单例模式"""
        try:
            from data_manager import DataManager
            self.data_manager = DataManager.get_instance()
            print("使用共享的数据管理器实例")
        except Exception as e:
            print(f"数据管理器初始化失败: {e}")
            self.data_manager = None
    
    def setup_widget_references(self):
        """设置控件引用 - 修复findChild问题"""
        # 通过对象名称来查找控件
        self.flow_label = None
        self.diameter_label = None
        
        # 查找标签
        for widget in self.findChildren(QLabel):
            text = widget.text()
            if "蒸汽流量" in text:
                self.flow_label = widget
            elif "管道内径" in text:
                self.diameter_label = widget
    
    def setup_ui(self):
        """设置左右布局的蒸汽管径和流量查询UI"""
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
            "根据蒸汽压力、温度和流量计算推荐管径，或根据管径计算最大蒸汽流量。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 计算模式选择 - 使用按钮组
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
            ("根据流量计算管径", "输入蒸汽流量，计算推荐管径"),
            ("根据管径计算流量", "输入管径，计算最大蒸汽流量")
        ]
        
        for i, (mode_name, tooltip) in enumerate(modes):
            btn = QPushButton(mode_name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setFixedWidth(200)  # 固定宽度
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
                    background-color: #e67e22;
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
        self.mode_buttons["根据流量计算管径"].setChecked(True)
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)
        
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
        
        # 蒸汽压力
        pressure_label = QLabel("蒸汽压力 (MPa):")
        pressure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pressure_label.setStyleSheet(label_style)
        input_layout.addWidget(pressure_label, row, 0)
        
        self.pressure_input = QLineEdit()
        self.pressure_input.setPlaceholderText("例如: 1.0")
        self.pressure_input.setValidator(QDoubleValidator(0.01, 20.0, 6))
        self.pressure_input.setFixedWidth(input_width)
        input_layout.addWidget(self.pressure_input, row, 1)
        
        self.pressure_combo = QComboBox()
        self.setup_pressure_options()
        self.pressure_combo.setFixedWidth(combo_width)
        self.pressure_combo.currentTextChanged.connect(self.on_pressure_changed)
        input_layout.addWidget(self.pressure_combo, row, 2)
        
        row += 1
        
        # 蒸汽温度
        temperature_label = QLabel("蒸汽温度 (°C):")
        temperature_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        temperature_label.setStyleSheet(label_style)
        input_layout.addWidget(temperature_label, row, 0)
        
        self.temperature_input = QLineEdit()
        self.temperature_input.setPlaceholderText("例如: 200")
        self.temperature_input.setValidator(QDoubleValidator(100.0, 600.0, 6))
        self.temperature_input.setFixedWidth(input_width)
        input_layout.addWidget(self.temperature_input, row, 1)
        
        self.temperature_combo = QComboBox()
        self.setup_temperature_options()
        self.temperature_combo.setFixedWidth(combo_width)
        self.temperature_combo.currentTextChanged.connect(self.on_temperature_changed)
        input_layout.addWidget(self.temperature_combo, row, 2)
        
        row += 1
        
        # 流量输入（管径计算模式）
        self.flow_label_widget = QLabel("蒸汽流量 (kg/h):")  # 使用不同的变量名
        self.flow_label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.flow_label_widget.setStyleSheet(label_style)
        input_layout.addWidget(self.flow_label_widget, row, 0)
        
        self.flow_input = QLineEdit()
        self.flow_input.setPlaceholderText("例如: 1000")
        self.flow_input.setValidator(QDoubleValidator(1.0, 100000.0, 6))
        self.flow_input.setFixedWidth(input_width)
        input_layout.addWidget(self.flow_input, row, 1)
        
        self.flow_combo = QComboBox()
        self.setup_flow_options()
        self.flow_combo.setFixedWidth(combo_width)
        self.flow_combo.currentTextChanged.connect(self.on_flow_changed)
        input_layout.addWidget(self.flow_combo, row, 2)
        
        row += 1
        
        # 管径输入（流量计算模式） - 隐藏初始状态
        self.diameter_label_widget = QLabel("管道内径 (mm):")  # 使用不同的变量名
        self.diameter_label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.diameter_label_widget.setStyleSheet(label_style)
        self.diameter_label_widget.setVisible(False)
        input_layout.addWidget(self.diameter_label_widget, row, 0)
        
        self.diameter_input = QLineEdit()
        self.diameter_input.setPlaceholderText("例如: 50")
        self.diameter_input.setValidator(QDoubleValidator(10.0, 1000.0, 6))
        self.diameter_input.setFixedWidth(input_width)
        self.diameter_input.setVisible(False)
        input_layout.addWidget(self.diameter_input, row, 1)
        
        self.diameter_combo = QComboBox()
        self.setup_diameter_options()
        self.diameter_combo.setFixedWidth(combo_width)
        self.diameter_combo.currentTextChanged.connect(self.on_diameter_changed)
        self.diameter_combo.setVisible(False)
        input_layout.addWidget(self.diameter_combo, row, 2)
        
        left_layout.addWidget(input_group)
        
        # 4. 计算按钮
        calculate_btn = QPushButton("🧮 计算")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.calculate_steam_pipe)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
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
        
        # 设置初始显示状态
        self.on_mode_changed("根据流量计算管径")
    
    def get_current_mode(self):
        """获取当前选择的计算模式"""
        checked_button = self.mode_button_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return "根据流量计算管径"  # 默认值
    
    def on_mode_changed(self, mode):
        """处理计算模式变化"""
        if isinstance(mode, QPushButton):
            mode = mode.text()
            
        if "根据管径计算流量" in mode:
            # 隐藏流量相关控件
            self.flow_label_widget.setVisible(False)
            self.flow_input.setVisible(False)
            self.flow_combo.setVisible(False)
            # 显示管径相关控件
            self.diameter_label_widget.setVisible(True)
            self.diameter_input.setVisible(True)
            self.diameter_combo.setVisible(True)
        else:
            # 显示流量相关控件
            self.flow_label_widget.setVisible(True)
            self.flow_input.setVisible(True)
            self.flow_combo.setVisible(True)
            # 隐藏管径相关控件
            self.diameter_label_widget.setVisible(False)
            self.diameter_input.setVisible(False)
            self.diameter_combo.setVisible(False)
    
    def setup_pressure_options(self):
        """设置蒸汽压力选项"""
        pressure_options = [
            "- 请选择蒸汽压力 -",
            "0.1 MPa - 低压蒸汽",
            "0.3 MPa - 低压蒸汽",
            "0.6 MPa - 中压蒸汽",
            "1.0 MPa - 中压蒸汽",
            "1.6 MPa - 高压蒸汽",
            "2.5 MPa - 高压蒸汽",
            "4.0 MPa - 超高压蒸汽",
            "自定义压力"
        ]
        self.pressure_combo.addItems(pressure_options)
        self.pressure_combo.setCurrentIndex(0)
    
    def setup_temperature_options(self):
        """设置蒸汽温度选项"""
        temperature_options = [
            "- 请选择蒸汽温度 -",
            "100°C - 饱和蒸汽",
            "120°C - 饱和蒸汽",
            "150°C - 饱和蒸汽",
            "180°C - 饱和蒸汽",
            "200°C - 过热蒸汽",
            "250°C - 过热蒸汽",
            "300°C - 过热蒸汽",
            "400°C - 高温蒸汽",
            "自定义温度"
        ]
        self.temperature_combo.addItems(temperature_options)
        self.temperature_combo.setCurrentIndex(0)
    
    def setup_flow_options(self):
        """设置蒸汽流量选项"""
        flow_options = [
            "- 请选择流量范围 -",
            "小流量: 10-100 kg/h",
            "中等流量: 100-1000 kg/h",
            "大流量: 1000-10000 kg/h",
            "超大流量: 10000-100000 kg/h",
            "自定义流量"
        ]
        self.flow_combo.addItems(flow_options)
        self.flow_combo.setCurrentIndex(0)
    
    def setup_diameter_options(self):
        """设置管道内径选项"""
        diameter_options = [
            "- 请选择管道内径 -",
            "DN15 - 15 mm",
            "DN20 - 20 mm",
            "DN25 - 25 mm",
            "DN32 - 32 mm",
            "DN40 - 40 mm",
            "DN50 - 50 mm",
            "DN65 - 65 mm",
            "DN80 - 80 mm",
            "DN100 - 100 mm",
            "DN125 - 125 mm",
            "DN150 - 150 mm",
            "DN200 - 200 mm",
            "DN250 - 250 mm",
            "DN300 - 300 mm",
            "自定义管径"
        ]
        self.diameter_combo.addItems(diameter_options)
        self.diameter_combo.setCurrentIndex(0)
    
    def on_pressure_changed(self, text):
        """处理压力选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.pressure_input.clear()
            self.pressure_input.setPlaceholderText("输入压力值")
            self.pressure_input.setReadOnly(False)
            return
            
        if "自定义" in text:
            self.pressure_input.setReadOnly(False)
            self.pressure_input.setPlaceholderText("输入自定义压力")
            self.pressure_input.clear()
        else:
            self.pressure_input.setReadOnly(True)
            try:
                # 从文本中提取数字
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    pressure_value = float(match.group(1))
                    self.pressure_input.setText(f"{pressure_value:.1f}")
            except:
                pass
    
    def on_temperature_changed(self, text):
        """处理温度选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.temperature_input.clear()
            self.temperature_input.setPlaceholderText("输入温度值")
            self.temperature_input.setReadOnly(False)
            return
            
        if "自定义" in text:
            self.temperature_input.setReadOnly(False)
            self.temperature_input.setPlaceholderText("输入自定义温度")
            self.temperature_input.clear()
        else:
            self.temperature_input.setReadOnly(True)
            try:
                # 从文本中提取数字
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    temperature_value = float(match.group(1))
                    self.temperature_input.setText(f"{temperature_value:.0f}")
            except:
                pass
    
    def on_flow_changed(self, text):
        """处理流量选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.flow_input.clear()
            self.flow_input.setPlaceholderText("输入流量值")
            self.flow_input.setReadOnly(False)
            return
            
        if "自定义" in text:
            self.flow_input.setReadOnly(False)
            self.flow_input.setPlaceholderText("输入自定义流量")
            self.flow_input.clear()
        else:
            self.flow_input.setReadOnly(True)
            try:
                # 从文本中提取数字范围
                match = re.search(r'(\d+\.?\d*)-(\d+\.?\d*)', text)
                if match:
                    min_val = float(match.group(1))
                    max_val = float(match.group(2))
                    avg_val = (min_val + max_val) / 2
                    self.flow_input.setText(f"{avg_val:.0f}")
            except:
                pass
    
    def on_diameter_changed(self, text):
        """处理管径选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.diameter_input.clear()
            self.diameter_input.setPlaceholderText("输入管径值")
            self.diameter_input.setReadOnly(False)
            return
            
        if "自定义" in text:
            self.diameter_input.setReadOnly(False)
            self.diameter_input.setPlaceholderText("输入自定义管径")
            self.diameter_input.clear()
        else:
            self.diameter_input.setReadOnly(True)
            try:
                # 从文本中提取数字
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    diameter_value = float(match.group(1))
                    self.diameter_input.setText(f"{diameter_value:.0f}")
            except:
                pass
    
    def calculate_steam_pipe(self):
        """计算蒸汽管径或流量"""
        try:
            # 获取输入值
            mode = self.get_current_mode()
            pressure = float(self.pressure_input.text() or 0)
            temperature = float(self.temperature_input.text() or 0)
            
            # 验证输入
            if not pressure or not temperature:
                QMessageBox.warning(self, "输入错误", "请填写蒸汽压力和温度")
                return
            
            # 计算蒸汽密度
            steam_density = self.calculate_steam_density(pressure, temperature)
            specific_volume = 1 / steam_density if steam_density > 0 else 0
            
            if "根据流量计算管径" in mode:
                flow_rate = float(self.flow_input.text() or 0)
                if not flow_rate:
                    QMessageBox.warning(self, "输入错误", "请填写蒸汽流量")
                    return
                
                # 推荐蒸汽流速
                recommended_velocity = 25.0
                
                # 质量流量转换为体积流量
                volume_flow = (flow_rate / 3600) * specific_volume
                
                # 计算所需管径
                required_area = volume_flow / recommended_velocity
                required_diameter = math.sqrt(4 * required_area / math.pi) * 1000  # mm
                
                # 推荐标准管径
                standard_diameters = [15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300]
                recommended_diameter = min(standard_diameters, key=lambda x: abs(x - required_diameter))
                
                # 计算实际流速
                actual_area = math.pi * (recommended_diameter / 1000 / 2) ** 2
                actual_velocity = volume_flow / actual_area
                
                # 显示结果 - 使用格式化的输出
                result = self.format_diameter_result(
                    mode, pressure, temperature, steam_density, specific_volume,
                    flow_rate, volume_flow, required_diameter, recommended_diameter,
                    actual_velocity, required_area
                )
                
            else:  # 根据管径计算流量
                diameter = float(self.diameter_input.text() or 0)
                if not diameter:
                    QMessageBox.warning(self, "输入错误", "请填写管道内径")
                    return
                
                # 推荐蒸汽流速
                recommended_velocity = 25.0
                
                # 计算最大流量
                area = math.pi * (diameter / 1000 / 2) ** 2
                volume_flow = area * recommended_velocity
                max_flow_rate = volume_flow / specific_volume * 3600  # kg/h
                
                # 显示结果 - 使用格式化的输出
                result = self.format_flow_result(
                    mode, pressure, temperature, steam_density, specific_volume,
                    diameter, area, volume_flow, max_flow_rate, recommended_velocity
                )
            
            self.result_text.setText(result)
            
        except ValueError as e:
            QMessageBox.critical(self, "计算错误", f"参数输入格式错误: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def format_diameter_result(self, mode, pressure, temperature, steam_density, specific_volume,
                               flow_rate, volume_flow, required_diameter, recommended_diameter,
                               actual_velocity, required_area):
        """格式化管径计算结果"""
        return f"""═══════════
📋 输入参数
══════════

    计算模式: {mode}
    蒸汽压力: {pressure} MPa
    蒸汽温度: {temperature} °C
    蒸汽密度: {steam_density:.4f} kg/m³
    蒸汽比容: {specific_volume:.4f} m³/kg
    蒸汽流量: {flow_rate} kg/h

══════════
📊 计算结果
══════════

    流量分析:
    • 质量流量: {flow_rate} kg/h
    • 体积流量: {volume_flow*3600:.2f} m³/h
    • 体积流量: {volume_flow:.6f} m³/s

    管径分析:
    • 计算所需管径: {required_diameter:.1f} mm
    • 推荐标准管径: DN{recommended_diameter} ({recommended_diameter} mm)

    流速分析:
    • 推荐蒸汽流速: 25.0 m/s
    • 实际蒸汽流速: {actual_velocity:.1f} m/s
    • 流速状态: {"✓ 正常" if 20 <= actual_velocity <= 40 else "⚠ 注意"}

    技术参数:
    • 所需流通面积: {required_area:.6f} m²
    • 标准管流通面积: {math.pi * (recommended_diameter / 1000 / 2) ** 2:.6f} m²

══════════
💡 计算说明
══════════

    • 推荐蒸汽流速范围: 20-40 m/s
    • 低压蒸汽可取较低流速，高压蒸汽可取较高流速
    • 实际应用请考虑压力损失和管道材质
    • 对于长距离输送，建议选择较低流速以减小压降
    • 计算结果仅供参考，实际应用请考虑安全系数"""
    
    def format_flow_result(self, mode, pressure, temperature, steam_density, specific_volume,
                          diameter, area, volume_flow, max_flow_rate, recommended_velocity):
        """格式化流量计算结果"""
        return f"""═══════════
📋 输入参数
══════════

    计算模式: {mode}
    蒸汽压力: {pressure} MPa
    蒸汽温度: {temperature} °C
    蒸汽密度: {steam_density:.4f} kg/m³
    蒸汽比容: {specific_volume:.4f} m³/kg
    管道内径: {diameter} mm

══════════
📊 计算结果
══════════

    管道参数:
    • 管道内径: {diameter} mm
    • 流通面积: {area:.6f} m²

    流量分析:
    • 推荐蒸汽流速: {recommended_velocity} m/s
    • 最大蒸汽流量: {max_flow_rate:.0f} kg/h
    • 体积流量: {volume_flow*3600:.2f} m³/h

    不同流速对应流量:
    • 20 m/s (低流速): {volume_flow / recommended_velocity * 20 / specific_volume * 3600:.0f} kg/h
    • 25 m/s (标准流速): {max_flow_rate:.0f} kg/h
    • 30 m/s (较高流速): {volume_flow / recommended_velocity * 30 / specific_volume * 3600:.0f} kg/h
    • 40 m/s (高流速): {volume_flow / recommended_velocity * 40 / specific_volume * 3600:.0f} kg/h

══════════
💡 计算说明
══════════

    • 推荐蒸汽流速范围: 20-40 m/s
    • 实际流量应考虑压力损失和安全系数
    • 对于重要应用，建议进行详细的水力计算
    • 计算结果仅供参考，实际应用请考虑具体工况"""
    
    def calculate_steam_density(self, pressure_mpa, temperature_c):
        """计算蒸汽密度"""
        pressure_bar = pressure_mpa * 10
        
        if temperature_c < 200:
            density = 0.6 * pressure_bar / (temperature_c + 100)
        else:
            density = 0.5 * pressure_bar / (temperature_c + 150)
        
        return max(density, 0.1)
    
    def get_project_info(self):
        """获取工程信息 - 使用共享的项目信息"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QDialogButtonBox
            
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
                    self.project_input.setPlaceholderText("例如：化工厂蒸汽管道系统")
                    self.project_input.setText(self.default_info.get('project_name', ''))
                    project_layout.addWidget(project_label)
                    project_layout.addWidget(self.project_input)
                    layout.addLayout(project_layout)
                    
                    # 子项名称
                    subproject_layout = QHBoxLayout()
                    subproject_label = QLabel("子项名称:")
                    subproject_label.setFixedWidth(80)
                    self.subproject_input = QLineEdit()
                    self.subproject_input.setPlaceholderText("例如：主蒸汽管道")
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
                report_number = self.data_manager.get_next_report_number("STEAM")
            
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
            
            # 检查结果是否为空
            if not result_text or ("计算结果" not in result_text and "计算模式" not in result_text):
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            # 获取工程信息
            project_info = self.get_project_info()
            if not project_info:
                return None  # 用户取消了输入
            
            # 添加报告头信息
            report = f"""工程计算书 - 蒸汽管道计算
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

    计算书编号: STEAM-{datetime.now().strftime('%Y%m%d')}-001
    版本: 1.0
    状态: 正式计算书

══════════
📝 备注说明
══════════

    1. 本计算书基于蒸汽工程原理及相关标准规范
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
            default_name = f"蒸汽管道计算书_{timestamp}.txt"
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
            default_name = f"蒸汽管道计算书_{timestamp}.pdf"
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
                title = Paragraph("工程计算书 - 蒸汽管道计算", chinese_style_heading)
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
            "✓": "",
            "⚠": ""
        }
        
        # 替换表情图标
        for emoji, text in replacements.items():
            content = content.replace(emoji, text)
        
        # 替换单位符号
        content = content.replace("m³", "m3")
        content = content.replace("kg/m³", "kg/m3")
        content = content.replace("°C", "°C")
        
        return content


if __name__ == "__main__":
    # 测试代码
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    calculator = 蒸汽管径流量()
    calculator.resize(1200, 800)
    calculator.show()
    
    sys.exit(app.exec())