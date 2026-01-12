# [file name]: calculators/fire_hydrant_calculator.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QLabel, QLineEdit, QComboBox, QPushButton, 
                              QTextEdit, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox, QTabWidget, QSpinBox,
                              QDoubleSpinBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDoubleValidator
import math

class 消火栓计算(QWidget):
    """消火栓计算器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🚒 消火栓系统计算")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 添加计算标签页
        self.calculation_tab = self.create_calculation_tab()
        self.tab_widget.addTab(self.calculation_tab, "📊 消火栓计算")
        
        # 添加标准说明标签页
        self.standard_tab = self.create_standard_tab()
        self.tab_widget.addTab(self.standard_tab, "📖 消防规范")
        
        main_layout.addWidget(self.tab_widget)
    
    def create_calculation_tab(self):
        """创建计算标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 建筑信息组
        building_group = QGroupBox("🏢 建筑信息")
        building_layout = QVBoxLayout(building_group)
        
        # 建筑类型和高度
        type_height_layout = QHBoxLayout()
        type_height_layout.addWidget(QLabel("建筑类型:"))
        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems([
            "民用建筑", "工业建筑", "仓库", "高层建筑", "超高层建筑", "地下建筑"
        ])
        self.building_type_combo.currentTextChanged.connect(self.on_building_type_changed)
        type_height_layout.addWidget(self.building_type_combo)
        
        type_height_layout.addWidget(QLabel("建筑高度 (m):"))
        self.building_height_input = QDoubleSpinBox()
        self.building_height_input.setRange(0, 500)
        self.building_height_input.setValue(24)
        self.building_height_input.setSuffix(" m")
        type_height_layout.addWidget(self.building_height_input)
        
        type_height_layout.addWidget(QLabel("建筑面积 (m²):"))
        self.building_area_input = QDoubleSpinBox()
        self.building_area_input.setRange(0, 1000000)
        self.building_area_input.setValue(5000)
        self.building_area_input.setSuffix(" m²")
        type_height_layout.addWidget(self.building_area_input)
        
        building_layout.addLayout(type_height_layout)
        
        # 危险等级和防火分区
        danger_layout = QHBoxLayout()
        danger_layout.addWidget(QLabel("火灾危险等级:"))
        self.danger_level_combo = QComboBox()
        self.danger_level_combo.addItems(["轻危险级", "中危险级Ⅰ级", "中危险级Ⅱ级", "严重危险级"])
        danger_layout.addWidget(self.danger_level_combo)
        
        danger_layout.addWidget(QLabel("防火分区数量:"))
        self.fire_zone_spin = QSpinBox()
        self.fire_zone_spin.setRange(1, 50)
        self.fire_zone_spin.setValue(1)
        danger_layout.addWidget(self.fire_zone_spin)
        
        building_layout.addLayout(danger_layout)
        
        layout.addWidget(building_group)
        
        # 消火栓参数组
        hydrant_group = QGroupBox("💧 消火栓参数")
        hydrant_layout = QVBoxLayout(hydrant_group)
        
        # 基本参数
        basic_params_layout = QHBoxLayout()
        basic_params_layout.addWidget(QLabel("同时使用水枪数:"))
        self.gun_count_spin = QSpinBox()
        self.gun_count_spin.setRange(1, 10)
        self.gun_count_spin.setValue(2)
        basic_params_layout.addWidget(self.gun_count_spin)
        
        basic_params_layout.addWidget(QLabel("水枪流量 (L/s):"))
        self.gun_flow_input = QDoubleSpinBox()
        self.gun_flow_input.setRange(2, 10)
        self.gun_flow_input.setValue(5)
        self.gun_flow_input.setSuffix(" L/s")
        basic_params_layout.addWidget(self.gun_flow_input)
        
        basic_params_layout.addWidget(QLabel("充实水柱 (m):"))
        self.water_column_input = QDoubleSpinBox()
        self.water_column_input.setRange(7, 17)
        self.water_column_input.setValue(13)
        self.water_column_input.setSuffix(" m")
        basic_params_layout.addWidget(self.water_column_input)
        
        hydrant_layout.addLayout(basic_params_layout)
        
        # 压力和管径
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("最不利点压力 (MPa):"))
        self.min_pressure_input = QDoubleSpinBox()
        self.min_pressure_input.setRange(0.1, 1.0)
        self.min_pressure_input.setValue(0.35)
        self.min_pressure_input.setSuffix(" MPa")
        pressure_layout.addWidget(self.min_pressure_input)
        
        pressure_layout.addWidget(QLabel("水泵扬程 (m):"))
        self.pump_head_input = QDoubleSpinBox()
        self.pump_head_input.setRange(10, 200)
        self.pump_head_input.setValue(80)
        self.pump_head_input.setSuffix(" m")
        pressure_layout.addWidget(self.pump_head_input)
        
        pressure_layout.addWidget(QLabel("主管直径 (mm):"))
        self.main_pipe_diameter_combo = QComboBox()
        self.main_pipe_diameter_combo.addItems(["100", "125", "150", "200"])
        self.main_pipe_diameter_combo.setCurrentText("150")
        pressure_layout.addWidget(self.main_pipe_diameter_combo)
        
        hydrant_layout.addLayout(pressure_layout)
        
        # 特殊选项
        options_layout = QHBoxLayout()
        self.auto_calc_check = QCheckBox("自动计算参数")
        self.auto_calc_check.setChecked(True)
        options_layout.addWidget(self.auto_calc_check)
        
        self.high_rise_check = QCheckBox("高层建筑")
        options_layout.addWidget(self.high_rise_check)
        
        self.sprinkler_check = QCheckBox("喷淋系统")
        options_layout.addWidget(self.sprinkler_check)
        
        hydrant_layout.addLayout(options_layout)
        
        layout.addWidget(hydrant_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("🚀 计算消火栓系统")
        self.calculate_btn.clicked.connect(self.calculate_hydrant_system)
        self.calculate_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; }")
        button_layout.addWidget(self.calculate_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_inputs)
        self.clear_btn.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; }")
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # 结果显示组
        result_group = QGroupBox("📈 计算结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(250)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        # 消火栓配置表
        config_group = QGroupBox("🔧 推荐配置")
        config_layout = QVBoxLayout(config_group)
        
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["项目", "推荐值", "说明"])
        config_layout.addWidget(self.config_table)
        
        layout.addWidget(config_group)
        
        return tab
    
    def on_building_type_changed(self, building_type):
        """建筑类型改变事件"""
        if building_type in ["高层建筑", "超高层建筑"]:
            self.high_rise_check.setChecked(True)
            self.building_height_input.setValue(50)
        else:
            self.high_rise_check.setChecked(False)
            self.building_height_input.setValue(24)
        
        # 自动设置危险等级
        if building_type == "仓库":
            self.danger_level_combo.setCurrentText("严重危险级")
        elif building_type in ["工业建筑", "高层建筑"]:
            self.danger_level_combo.setCurrentText("中危险级Ⅱ级")
        else:
            self.danger_level_combo.setCurrentText("中危险级Ⅰ级")
    
    def create_standard_tab(self):
        """创建标准说明标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 标准说明文本
        standard_text = QTextEdit()
        standard_text.setReadOnly(True)
        standard_text.setHtml(self.get_standard_html())
        layout.addWidget(standard_text)
        
        return tab
    
    def get_standard_html(self):
        """获取标准说明HTML内容"""
        return """
        <h2>📚 消火栓系统设计规范</h2>
        
        <h3>🔍 设计依据</h3>
        <ul>
            <li>GB 50016-2014《建筑设计防火规范》</li>
            <li>GB 50974-2014《消防给水及消火栓系统技术规范》</li>
            <li>GB 50084-2017《自动喷水灭火系统设计规范》</li>
        </ul>
        
        <h3>💧 消防用水量标准</h3>
        
        <h4>🏢 民用建筑</h4>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #3498db; color: white;">
            <th style="padding: 8px;">建筑类型</th>
            <th style="padding: 8px;">高度/体积</th>
            <th style="padding: 8px;">室外流量(L/s)</th>
            <th style="padding: 8px;">室内流量(L/s)</th>
            <th style="padding: 8px;">火灾延续时间(h)</th>
        </tr>
        <tr>
            <td style="padding: 8px;">普通住宅</td>
            <td style="padding: 8px;">≤21m</td>
            <td style="padding: 8px;">15</td>
            <td style="padding: 8px;">10</td>
            <td style="padding: 8px;">2</td>
        </tr>
        <tr>
            <td style="padding: 8px;">高层住宅</td>
            <td style="padding: 8px;">＞21m</td>
            <td style="padding: 8px;">15</td>
            <td style="padding: 8px;">20</td>
            <td style="padding: 8px;">2</td>
        </tr>
        <tr>
            <td style="padding: 8px;">办公楼</td>
            <td style="padding: 8px;">≤50m</td>
            <td style="padding: 8px;">20</td>
            <td style="padding: 8px;">15</td>
            <td style="padding: 8px;">2</td>
        </tr>
        </table>
        
        <h4>🏭 工业建筑</h4>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #e74c3c; color: white;">
            <th style="padding: 8px;">火灾危险等级</th>
            <th style="padding: 8px;">室外流量(L/s)</th>
            <th style="padding: 8px;">室内流量(L/s)</th>
            <th style="padding: 8px;">火灾延续时间(h)</th>
        </tr>
        <tr>
            <td style="padding: 8px;">轻危险级</td>
            <td style="padding: 8px;">15</td>
            <td style="padding: 8px;">10</td>
            <td style="padding: 8px;">2</td>
        </tr>
        <tr>
            <td style="padding: 8px;">中危险级Ⅰ级</td>
            <td style="padding: 8px;">20</td>
            <td style="padding: 8px;">15</td>
            <td style="padding: 8px;">2</td>
        </tr>
        <tr>
            <td style="padding: 8px;">中危险级Ⅱ级</td>
            <td style="padding: 8px;">25</td>
            <td style="padding: 8px;">20</td>
            <td style="padding: 8px;">2</td>
        </tr>
        <tr>
            <td style="padding: 8px;">严重危险级</td>
            <td style="padding: 8px;">30-40</td>
            <td style="padding: 8px;">25-30</td>
            <td style="padding: 8px;">3</td>
        </tr>
        </table>
        
        <h3>📏 消火栓布置要求</h3>
        <ul>
            <li><b>室内消火栓间距：</b>高层建筑≤30m，其他建筑≤50m</li>
            <li><b>保护半径：</b>水带长度×0.8 + 充实水柱水平投影</li>
            <li><b>充实水柱长度：</b>一般建筑≥7m，高层建筑≥13m</li>
            <li><b>出水压力：</b>0.35MPa（最不利点）</li>
            <li><b>水枪流量：</b>≥5L/s</li>
        </ul>
        
        <h3>🔧 管道设计要求</h3>
        <ul>
            <li><b>管材：</b>热镀锌钢管、不锈钢管等</li>
            <li><b>管径：</b>室内立管≥DN100，水平干管≥DN150</li>
            <li><b>流速限制：</b>一般≤2.5m/s，经济流速1.5-2.0m/s</li>
            <li><b>工作压力：</b>≤2.4MPa</li>
        </ul>
        
        <h3>⚠️ 注意事项</h3>
        <p>本计算工具仅供参考，实际工程设计应遵循最新国家标准和当地消防部门的要求。重要项目应聘请专业消防设计单位进行设计。</p>
        """
    
    def calculate_hydrant_system(self):
        """计算消火栓系统"""
        try:
            # 获取输入值
            building_type = self.building_type_combo.currentText()
            building_height = self.building_height_input.value()
            building_area = self.building_area_input.value()
            danger_level = self.danger_level_combo.currentText()
            fire_zones = self.fire_zone_spin.value()
            gun_count = self.gun_count_spin.value()
            gun_flow = self.gun_flow_input.value()
            water_column = self.water_column_input.value()
            min_pressure = self.min_pressure_input.value()
            pump_head = self.pump_head_input.value()
            main_diameter = int(self.main_pipe_diameter_combo.currentText())
            is_high_rise = self.high_rise_check.isChecked()
            has_sprinkler = self.sprinkler_check.isChecked()
            auto_calc = self.auto_calc_check.isChecked()
            
            # 自动计算参数
            if auto_calc:
                self.auto_calculate_parameters(building_type, building_height, danger_level)
            
            # 计算消防用水量
            total_flow = self.calculate_total_flow(gun_count, gun_flow, building_type, danger_level)
            
            # 计算管径和流速
            pipe_results = self.calculate_pipe_parameters(total_flow, main_diameter)
            
            # 计算水泵参数
            pump_results = self.calculate_pump_parameters(pump_head, total_flow, building_height)
            
            # 计算水箱容量
            tank_capacity = self.calculate_tank_capacity(total_flow, building_type, danger_level)
            
            # 计算消火栓数量
            hydrant_count = self.calculate_hydrant_count(building_area, building_type)
            
            # 显示结果
            self.display_results(total_flow, pipe_results, pump_results, tank_capacity, hydrant_count)
            
            # 更新配置表
            self.update_config_table(total_flow, pipe_results, pump_results, tank_capacity, hydrant_count)
            
        except Exception as e:
            QMessageBox.warning(self, "计算错误", f"计算过程中发生错误: {str(e)}")
    
    def auto_calculate_parameters(self, building_type, height, danger_level):
        """自动计算参数"""
        # 自动设置水枪数
        if building_type in ["高层建筑", "超高层建筑"]:
            self.gun_count_spin.setValue(4)
        elif building_type == "仓库":
            self.gun_count_spin.setValue(3)
        else:
            self.gun_count_spin.setValue(2)
        
        # 自动设置充实水柱
        if height > 24:
            self.water_column_input.setValue(13)
        else:
            self.water_column_input.setValue(10)
        
        # 自动设置最不利点压力
        if height > 50:
            self.min_pressure_input.setValue(0.45)
        else:
            self.min_pressure_input.setValue(0.35)
    
    def calculate_total_flow(self, gun_count, gun_flow, building_type, danger_level):
        """计算总消防用水量"""
        base_flow = gun_count * gun_flow
        
        # 根据建筑类型和危险等级调整
        flow_factors = {
            "民用建筑": 1.0,
            "工业建筑": 1.2,
            "仓库": 1.5,
            "高层建筑": 1.3,
            "超高层建筑": 1.5,
            "地下建筑": 1.2
        }
        
        danger_factors = {
            "轻危险级": 0.8,
            "中危险级Ⅰ级": 1.0,
            "中危险级Ⅱ级": 1.2,
            "严重危险级": 1.5
        }
        
        factor = flow_factors.get(building_type, 1.0) * danger_factors.get(danger_level, 1.0)
        total_flow = base_flow * factor
        
        # 最小流量限制
        min_flows = {
            "民用建筑": 10,
            "工业建筑": 15,
            "仓库": 20,
            "高层建筑": 20,
            "超高层建筑": 30,
            "地下建筑": 15
        }
        
        return max(total_flow, min_flows.get(building_type, 15))
    
    def calculate_pipe_parameters(self, total_flow, main_diameter):
        """计算管道参数"""
        # 计算流速
        area = math.pi * (main_diameter / 1000) ** 2 / 4  # m²
        flow_m3s = total_flow / 1000  # m³/s
        velocity = flow_m3s / area  # m/s
        
        # 计算沿程水头损失 (简化计算)
        length = 100  # 假设管道长度100m
        friction_factor = 0.02  # 摩擦系数
        head_loss = friction_factor * (length / (main_diameter / 1000)) * (velocity ** 2) / (2 * 9.81)
        
        return {
            "diameter": main_diameter,
            "velocity": velocity,
            "head_loss": head_loss,
            "recommended_diameter": self.get_recommended_diameter(total_flow)
        }
    
    def get_recommended_diameter(self, flow):
        """获取推荐管径"""
        if flow <= 15:
            return 100
        elif flow <= 25:
            return 125
        elif flow <= 40:
            return 150
        else:
            return 200
    
    def calculate_pump_parameters(self, pump_head, total_flow, building_height):
        """计算水泵参数"""
        # 计算所需扬程
        required_head = building_height + 10 + 5  # 建筑高度 + 最不利点高度 + 余量
        
        # 计算水泵功率
        efficiency = 0.75
        power_kw = (total_flow / 1000) * required_head * 9.81 / efficiency
        
        return {
            "required_head": required_head,
            "actual_head": pump_head,
            "power": power_kw,
            "flow": total_flow,
            "efficiency": efficiency
        }
    
    def calculate_tank_capacity(self, total_flow, building_type, danger_level):
        """计算消防水箱容量"""
        # 火灾延续时间 (小时)
        duration_factors = {
            "民用建筑": 2,
            "工业建筑": 2,
            "仓库": 3,
            "高层建筑": 2,
            "超高层建筑": 3,
            "地下建筑": 2
        }
        
        duration = duration_factors.get(building_type, 2)
        
        # 容量计算 (m³)
        capacity = total_flow * 3.6 * duration  # L/s * 3.6 = m³/h
        
        # 最小容量限制
        min_capacities = {
            "民用建筑": 12,
            "工业建筑": 18,
            "仓库": 36,
            "高层建筑": 18,
            "超高层建筑": 36,
            "地下建筑": 12
        }
        
        return max(capacity, min_capacities.get(building_type, 12))
    
    def calculate_hydrant_count(self, building_area, building_type):
        """计算消火栓数量"""
        # 消火栓保护面积 (m²)
        coverage_areas = {
            "民用建筑": 400,
            "工业建筑": 300,
            "仓库": 200,
            "高层建筑": 300,
            "超高层建筑": 250,
            "地下建筑": 200
        }
        
        coverage = coverage_areas.get(building_type, 300)
        count = math.ceil(building_area / coverage)
        
        # 最小数量限制
        min_counts = {
            "民用建筑": 2,
            "工业建筑": 3,
            "仓库": 4,
            "高层建筑": 4,
            "超高层建筑": 6,
            "地下建筑": 3
        }
        
        return max(count, min_counts.get(building_type, 2))
    
    def display_results(self, total_flow, pipe_results, pump_results, tank_capacity, hydrant_count):
        """显示计算结果"""
        result_text = f"""
        <h3>🚒 消火栓系统计算结果</h3>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 8px; font-weight: bold;">项目</td>
            <td style="padding: 8px;">计算结果</td>
            <td style="padding: 8px;">说明</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">总消防用水量</td>
            <td style="padding: 8px; color: #e74c3c; font-weight: bold;">{total_flow:.1f} L/s</td>
            <td style="padding: 8px;">同时使用水枪的总流量</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">主管道直径</td>
            <td style="padding: 8px;">DN{pipe_results['diameter']}</td>
            <td style="padding: 8px;">推荐: DN{pipe_results['recommended_diameter']}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">管道流速</td>
            <td style="padding: 8px; {'color: red;' if pipe_results['velocity'] > 2.5 else 'color: green;'}">
                {pipe_results['velocity']:.2f} m/s
            </td>
            <td style="padding: 8px;">{'⚠️ 流速偏高' if pipe_results['velocity'] > 2.5 else '✅ 流速正常'}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">水泵扬程</td>
            <td style="padding: 8px;">{pump_results['actual_head']:.0f} m</td>
            <td style="padding: 8px;">需求: {pump_results['required_head']:.0f} m</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">水泵功率</td>
            <td style="padding: 8px;">{pump_results['power']:.1f} kW</td>
            <td style="padding: 8px;">效率: {pump_results['efficiency']*100:.0f}%</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">消防水箱容量</td>
            <td style="padding: 8px;">{tank_capacity:.0f} m³</td>
            <td style="padding: 8px;">火灾延续时间用水量</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">消火栓数量</td>
            <td style="padding: 8px;">{hydrant_count} 个</td>
            <td style="padding: 8px;">按保护半径计算</td>
        </tr>
        </table>
        
        <h4>📋 设计建议</h4>
        <ul>
            <li>主管道建议采用DN{pipe_results['recommended_diameter']}管道</li>
            <li>水泵选型应满足{pump_results['required_head']:.0f}m扬程和{total_flow:.1f}L/s流量要求</li>
            <li>消防水箱容量不应小于{tank_capacity:.0f}m³</li>
            <li>消火栓布置间距应符合规范要求</li>
        </ul>
        """
        
        self.result_text.setHtml(result_text)
    
    def update_config_table(self, total_flow, pipe_results, pump_results, tank_capacity, hydrant_count):
        """更新配置表"""
        config_data = [
            ["消防用水量", f"{total_flow:.1f} L/s", "总设计流量"],
            ["主管道直径", f"DN{pipe_results['recommended_diameter']}", "推荐主管直径"],
            ["管道流速", f"{pipe_results['velocity']:.2f} m/s", "经济流速范围: 1.5-2.5 m/s"],
            ["水泵扬程", f"{pump_results['required_head']:.0f} m", "最小需求扬程"],
            ["水泵流量", f"{pump_results['flow']:.1f} L/s", "设计流量"],
            ["水箱容量", f"{tank_capacity:.0f} m³", "消防储水量"],
            ["消火栓数量", f"{hydrant_count} 个", "按保护面积计算"],
            ["充实水柱", f"{self.water_column_input.value()} m", "有效灭火长度"]
        ]
        
        self.config_table.setRowCount(len(config_data))
        for i, row_data in enumerate(config_data):
            for j, data in enumerate(row_data):
                item = QTableWidgetItem(data)
                item.setTextAlignment(Qt.AlignCenter)
                self.config_table.setItem(i, j, item)
        
        # 调整表格列宽
        header = self.config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
    
    def clear_inputs(self):
        """清空输入"""
        self.building_type_combo.setCurrentIndex(0)
        self.building_height_input.setValue(24)
        self.building_area_input.setValue(5000)
        self.danger_level_combo.setCurrentIndex(0)
        self.fire_zone_spin.setValue(1)
        self.gun_count_spin.setValue(2)
        self.gun_flow_input.setValue(5)
        self.water_column_input.setValue(13)
        self.min_pressure_input.setValue(0.35)
        self.pump_head_input.setValue(80)
        self.main_pipe_diameter_combo.setCurrentText("150")
        self.auto_calc_check.setChecked(True)
        self.high_rise_check.setChecked(False)
        self.sprinkler_check.setChecked(False)
        self.result_text.clear()
        self.config_table.setRowCount(0)

if __name__ == "__main__":
    # 测试代码
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = 消火栓计算()
    widget.resize(900, 700)
    widget.show()
    
    sys.exit(app.exec())