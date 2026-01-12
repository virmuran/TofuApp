from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QComboBox, QGridLayout, QMessageBox,
    QFrame, QScrollArea, QDialog, QSpinBox, QButtonGroup,
    QFileDialog, QDialogButtonBox
)
from PySide6.QtGui import QFont, QDoubleValidator
from PySide6.QtCore import Qt
import math
import re
from datetime import datetime


class 气体标态转压缩态(QWidget):
    """气体标准状态转压缩状态（左右布局优化版）"""
    
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
        """设置左右布局的气体状态转换UI"""
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
            "将气体从标准状态(0°C, 101.325kPa)转换为实际状态(压缩状态)，用于工程设计和设备选型。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(description)
        
        # 2. 输入参数组 - 使用GridLayout实现整齐的布局
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
        
        # 标准状态流量
        flow_label = QLabel("标准状态流量 (Nm³/h):")
        flow_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        flow_label.setStyleSheet(label_style)
        input_layout.addWidget(flow_label, row, 0)
        
        self.flow_input = QLineEdit()
        self.flow_input.setPlaceholderText("例如: 1000")
        self.flow_input.setValidator(QDoubleValidator(0.1, 1000000.0, 6))
        self.flow_input.setFixedWidth(input_width)
        input_layout.addWidget(self.flow_input, row, 1)
        
        # 流量输入不需要下拉，替换为提示标签
        self.flow_hint = QLabel("直接输入标准状态流量")
        self.flow_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.flow_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.flow_hint, row, 2)
        
        row += 1
        
        # 标准状态定义
        standard_label = QLabel("标准状态:")
        standard_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        standard_label.setStyleSheet(label_style)
        input_layout.addWidget(standard_label, row, 0)
        
        self.standard_combo = QComboBox()
        self.standard_combo.addItems([
            "- 请选择标准状态 -",
            "0°C, 101.325 kPa (国际标准)",
            "15°C, 101.325 kPa (欧美标准)",
            "20°C, 101.325 kPa (中国标准)",
            "自定义标准状态"
        ])
        self.standard_combo.setFixedWidth(input_width)
        self.standard_combo.currentTextChanged.connect(self.on_standard_changed)
        input_layout.addWidget(self.standard_combo, row, 1)
        
        # 标准状态提示标签
        self.standard_hint = QLabel("选择标准状态定义")
        self.standard_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.standard_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.standard_hint, row, 2)
        
        row += 1
        
        # 自定义标准状态（隐藏时占用一行但不显示）
        self.custom_standard_group = QGroupBox("自定义标准状态")
        self.custom_standard_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #95a5a6;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                color: #7f8c8d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        custom_layout = QGridLayout(self.custom_standard_group)
        
        # 标准温度
        std_temp_label = QLabel("标准温度 (°C):")
        std_temp_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        std_temp_label.setStyleSheet(label_style)
        custom_layout.addWidget(std_temp_label, 0, 0)
        
        self.std_temp_input = QLineEdit()
        self.std_temp_input.setPlaceholderText("例如: 0")
        self.std_temp_input.setValidator(QDoubleValidator(-50.0, 100.0, 6))
        self.std_temp_input.setFixedWidth(input_width)
        custom_layout.addWidget(self.std_temp_input, 0, 1)
        
        # 标准温度提示
        self.std_temp_hint = QLabel("输入标准温度")
        self.std_temp_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.std_temp_hint.setFixedWidth(combo_width)
        custom_layout.addWidget(self.std_temp_hint, 0, 2)
        
        # 标准压力
        std_pressure_label = QLabel("标准压力 (kPa):")
        std_pressure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        std_pressure_label.setStyleSheet(label_style)
        custom_layout.addWidget(std_pressure_label, 1, 0)
        
        self.std_pressure_input = QLineEdit()
        self.std_pressure_input.setPlaceholderText("例如: 101.325")
        self.std_pressure_input.setValidator(QDoubleValidator(50.0, 200.0, 6))
        self.std_pressure_input.setFixedWidth(input_width)
        custom_layout.addWidget(self.std_pressure_input, 1, 1)
        
        # 标准压力提示
        self.std_pressure_hint = QLabel("输入标准压力")
        self.std_pressure_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.std_pressure_hint.setFixedWidth(combo_width)
        custom_layout.addWidget(self.std_pressure_hint, 1, 2)
        
        # 将自定义标准状态组添加到主布局
        input_layout.addWidget(self.custom_standard_group, row, 0, 1, 3)
        self.custom_standard_group.setVisible(False)
        
        row += 1
        
        # 实际状态压力
        actual_pressure_label = QLabel("实际状态压力 (kPa):")
        actual_pressure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        actual_pressure_label.setStyleSheet(label_style)
        input_layout.addWidget(actual_pressure_label, row, 0)
        
        self.actual_pressure_input = QLineEdit()
        self.actual_pressure_input.setPlaceholderText("例如: 500")
        self.actual_pressure_input.setValidator(QDoubleValidator(0.1, 10000.0, 6))
        self.actual_pressure_input.setFixedWidth(input_width)
        input_layout.addWidget(self.actual_pressure_input, row, 1)
        
        # 压力输入不需要下拉，替换为提示标签
        self.pressure_hint = QLabel("直接输入实际压力值")
        self.pressure_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.pressure_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.pressure_hint, row, 2)
        
        row += 1
        
        # 实际状态温度
        actual_temp_label = QLabel("实际状态温度 (°C):")
        actual_temp_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        actual_temp_label.setStyleSheet(label_style)
        input_layout.addWidget(actual_temp_label, row, 0)
        
        self.actual_temp_input = QLineEdit()
        self.actual_temp_input.setPlaceholderText("例如: 20")
        self.actual_temp_input.setValidator(QDoubleValidator(-50.0, 500.0, 6))
        self.actual_temp_input.setFixedWidth(input_width)
        input_layout.addWidget(self.actual_temp_input, row, 1)
        
        # 温度输入不需要下拉，替换为提示标签
        self.temp_hint = QLabel("直接输入实际温度值")
        self.temp_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.temp_hint.setFixedWidth(combo_width)
        input_layout.addWidget(self.temp_hint, row, 2)
        
        row += 1
        
        # 气体压缩因子
        compress_label = QLabel("气体压缩因子 Z:")
        compress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        compress_label.setStyleSheet(label_style)
        input_layout.addWidget(compress_label, row, 0)
        
        self.compress_input = QLineEdit()
        self.compress_input.setPlaceholderText("例如: 1.0")
        self.compress_input.setReadOnly(True)
        self.compress_input.setText("1.0")
        self.compress_input.setFixedWidth(input_width)
        input_layout.addWidget(self.compress_input, row, 1)
        
        self.compress_combo = QComboBox()
        self.compress_combo.addItems([
            "- 请选择压缩因子 -",
            "1.0 - 理想气体",
            "0.9 - 轻微可压缩气体",
            "0.8 - 中等可压缩气体",
            "自定义压缩因子"
        ])
        self.compress_combo.setFixedWidth(combo_width)
        self.compress_combo.currentTextChanged.connect(self.on_compress_changed)
        input_layout.addWidget(self.compress_combo, row, 2)
        
        left_layout.addWidget(input_group)
        
        # 3. 计算按钮
        calculate_btn = QPushButton("🧮 转换状态")
        calculate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        calculate_btn.clicked.connect(self.convert_gas_state)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        calculate_btn.setMinimumHeight(50)
        left_layout.addWidget(calculate_btn)
        
        # 4. 下载按钮布局
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
        
        # 5. 在底部添加拉伸因子
        left_layout.addStretch()
        
        # 右侧：结果显示区域 (占1/3宽度)
        right_widget = QWidget()
        right_widget.setMinimumWidth(400)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # 结果显示
        self.result_group = QGroupBox("📤 转换结果")
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
    
    def on_standard_changed(self, text):
        """处理标准状态选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.custom_standard_group.setVisible(False)
            return
            
        if "自定义" in text:
            self.custom_standard_group.setVisible(True)
        else:
            self.custom_standard_group.setVisible(False)
    
    def on_compress_changed(self, text):
        """处理压缩因子选择变化"""
        # 检查是否选择了空值选项
        if text.startswith("-") or not text.strip():
            self.compress_input.clear()
            self.compress_input.setReadOnly(True)
            self.compress_input.setPlaceholderText("请选择压缩因子")
            return
            
        if "自定义" in text:
            self.compress_input.setReadOnly(False)
            self.compress_input.setPlaceholderText("输入自定义值")
            self.compress_input.clear()
        else:
            self.compress_input.setReadOnly(True)
            try:
                # 从文本中提取数字
                import re
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    compress_value = float(match.group(1))
                    self.compress_input.setText(f"{compress_value:.1f}")
            except:
                pass
    
    def get_standard_conditions(self):
        """获取标准状态条件"""
        text = self.standard_combo.currentText()
        
        # 检查是否为空值选项
        if text.startswith("-") or not text.strip():
            # 如果没有选择，返回国际标准
            return 0.0, 101.325
        
        if "自定义" in text:
            try:
                std_temp = float(self.std_temp_input.text() or 0)
                std_pressure = float(self.std_pressure_input.text() or 0)
                return std_temp, std_pressure
            except ValueError:
                return 0.0, 101.325  # 默认国际标准
        elif "0°C" in text:
            return 0.0, 101.325
        elif "15°C" in text:
            return 15.0, 101.325
        elif "20°C" in text:
            return 20.0, 101.325
        else:
            return 0.0, 101.325  # 默认国际标准
    
    def convert_gas_state(self):
        """转换气体状态"""
        try:
            # 获取输入值
            std_flow = float(self.flow_input.text() or 0)
            actual_pressure = float(self.actual_pressure_input.text() or 0)
            actual_temp = float(self.actual_temp_input.text() or 0)
            compress_factor = float(self.compress_input.text() or 0)
            
            std_temp, std_pressure = self.get_standard_conditions()
            
            # 验证输入
            if not all([std_flow, actual_pressure, actual_temp is not None]):
                QMessageBox.warning(self, "输入错误", "请填写所有必需参数")
                return
            
            # 转换为绝对温度和绝对压力
            std_temp_k = std_temp + 273.15
            actual_temp_k = actual_temp + 273.15
            
            std_pressure_abs = std_pressure
            actual_pressure_abs = actual_pressure
            
            # 计算实际状态流量
            # 使用理想气体状态方程: P1·V1/T1 = P2·V2/T2 (考虑压缩因子)
            actual_flow = std_flow * (std_pressure_abs / actual_pressure_abs) * (actual_temp_k / std_temp_k) * compress_factor
            
            # 计算密度变化
            # 密度与压力成正比，与温度成反比
            std_density_factor = 1.0  # 相对密度
            actual_density_factor = std_density_factor * (actual_pressure_abs / std_pressure_abs) * (std_temp_k / actual_temp_k) / compress_factor
            
            # 显示结果 - 使用格式化的输出
            result = f"""═══════════
📋 输入参数
═══════════

标准状态:
• 流量: {std_flow} Nm³/h
• 温度: {std_temp} °C ({std_temp_k:.2f} K)
• 压力: {std_pressure} kPa

实际状态:
• 压力: {actual_pressure} kPa
• 温度: {actual_temp} °C ({actual_temp_k:.2f} K)
• 压缩因子 Z: {compress_factor}

═══════════
📊 转换结果
═══════════

流量转换:
• 实际状态流量: {actual_flow:.2f} m³/h
• 实际状态流量: {actual_flow/60:.4f} m³/min

密度变化:
• 相对密度变化: {actual_density_factor:.4f} 倍

流量对比:
"""
            
            if actual_flow < std_flow:
                result += f"• 实际状态流量比标准状态小 {std_flow/actual_flow:.2f} 倍"
            else:
                result += f"• 实际状态流量比标准状态大 {actual_flow/std_flow:.2f} 倍"

            result += f"""

═══════════
🧮 计算公式
═══════════

Q_actual = Q_std × (P_std / P_actual) × (T_actual / T_std) × Z

其中:
• Q = 体积流量
• P = 绝对压力 (kPa)
• T = 绝对温度 (K)  
• Z = 压缩因子

详细计算:
{std_flow} × ({std_pressure_abs} / {actual_pressure_abs}) × ({actual_temp_k:.2f} / {std_temp_k:.2f}) × {compress_factor}
= {actual_flow:.2f} m³/h

═══════════
💡 应用说明
═══════════

• 标准状态通常指 0°C, 101.325 kPa
• 实际工程中需根据具体气体性质确定压缩因子
• 对于高压气体，压缩因子对结果影响显著
• 计算结果仅供参考，实际应用请考虑安全系数"""
            
            self.result_text.setText(result)
            
        except ValueError as e:
            QMessageBox.critical(self, "计算错误", f"参数输入格式错误: {str(e)}")
        except ZeroDivisionError:
            QMessageBox.critical(self, "计算错误", "压力或温度不能为零")
        except Exception as e:
            QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")

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
                report_number = self.data_manager.get_next_report_number("GASC")
            
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
            
            # 更宽松的检查条件
            if not result_text or ("转换结果" not in result_text):
                QMessageBox.warning(self, "生成失败", "请先进行计算再生成计算书")
                return None
                
            # 获取工程信息
            project_info = self.get_project_info()
            if not project_info:
                return None  # 用户取消了输入
            
            # 添加报告头信息
            report = f"""工程计算书 - 气体状态转换计算
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

    1. 本计算书基于理想气体状态方程及相关标准规范
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
            default_name = f"气体状态转换计算书_{timestamp}.txt"
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
            default_name = f"气体状态转换计算书_{timestamp}.pdf"
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
                title = Paragraph("工程计算书 - 气体状态转换计算", chinese_style_heading)
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
    
    converter = 气体标态转压缩态()
    converter.resize(1200, 800)
    converter.show()
    
    sys.exit(app.exec())