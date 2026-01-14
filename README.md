# TofuSoft - 化工工程计算与工艺设计模块

TofuSoft 是一套基于 PyQt 开发的化工工程计算与工艺设计桌面应用模块，涵盖管道压降计算、制冷循环分析、离心泵汽蚀余量计算、工艺流程图绘制等核心化工工程功能，旨在为化工工程师提供便捷、专业的工程计算与设计工具。

## 🌟 功能模块

### 1. 化工计算模块 (`chemical_calculations`)
#### 1.1 管道压降计算 (`pressure_drop_calculator.py`)
- 生成标准化的管道压降计算书，包含工程信息、计算结果、版本标识等完整内容
- 计算书自动填充生成时间、工程编号、公司名称等关键信息
- 内置计算结果校验机制，确保仅在完成有效计算后生成计算书

#### 1.2 制冷循环计算 (`refrigeration_cycle_calculator.py`)
- 支持理想循环（无过冷过热）和实际循环（包含过冷过热）两种计算模式
- 计算蒸汽压缩制冷循环核心性能参数：制冷量、压缩功、COP（性能系数）等
- 可配置制冷剂类型、蒸发温度、冷凝温度、过冷度、过热度、质量流量、压缩机效率等参数
- 提供参数输入校验，限制合理的数值范围（如温度 -273~1000°C）

#### 1.3 离心泵汽蚀余量计算 (`npsha_calculator.py`)
- 计算离心泵可用汽蚀余量（NPSHa），评估泵的汽蚀性能
- 支持大气压力、液体饱和蒸汽压、吸入液面高度、管路损失、液体密度等参数配置
- 提供常用参数快捷选择（如标准大气压、不同温度下水的蒸汽压、常见液体密度）
- 可选输入泵必需汽蚀余量（NPSHr），辅助评估泵的运行安全性

### 2. 工艺设计模块 (`process_design`)
#### 2.1 工艺流程图设计 (`process_flow_diagram_tab.py`)
- 提供可视化的设备添加对话框，支持设备类型、名称、ID 自定义配置
- 自动生成唯一设备 ID（基于 UUID），避免重复
- 可配置设备基础属性：温度、压力、体积等工艺参数
- 设备添加后自动同步至工艺流程图场景，并发送设备添加信号供后续处理

#### 2.2 通用验证工具 (`validation_utils.py`)
- 文件名有效性验证：检查非法字符、Windows 保留文件名、长度限制等
- 保障文件操作的安全性和兼容性，避免因文件名问题导致的存储/读取失败

## 🛠️ 技术栈
- **核心框架**：Python + PyQt5（QWidget、QDialog、QLayout、QComboBox、QLineEdit 等）
- **计算基础**：流体力学原理、制冷循环热力学、离心泵汽蚀理论
- **辅助工具**：UUID（设备ID生成）、数据验证（QDoubleValidator）、日期时间处理

## 🚀 安装说明
### 环境要求
- Python 3.7+
- PyQt5 5.15+

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/your-username/tofusoft-chemical-engineering.git
cd tofusoft-chemical-engineering
```

2. 安装依赖
```bash
pip install pyqt5
```

3. 运行应用（示例）
```bash
# 以制冷循环计算模块为例
python TofuApp/modules/chemical_calculations/calculators/refrigeration_cycle_calculator.py
```

## 📖 使用说明
### 化工计算模块使用
1. 打开对应计算模块界面（如制冷循环计算器）
2. 在左侧输入区域配置计算参数（可选择预设值或自定义输入）
3. 点击「计算」按钮，右侧结果区域将展示详细计算结果
4. （仅压降计算）完成计算后可点击生成计算书，填写工程信息后导出标准化文档

### 工艺流程图设计使用
1. 进入工艺流程图设计标签页
2. 在画布指定位置触发「添加设备」操作，弹出设备配置对话框
3. 选择设备类型，填写设备名称（可选），确认/修改设备ID和工艺参数
4. 点击「确定」完成设备添加，设备将自动显示在流程图画布中

## 📂 目录结构
```
TofuApp/
├── modules/
│   ├── chemical_calculations/          # 化工计算核心模块
│   │   ├── calculators/
│   │   │   ├── pressure_drop_calculator.py  # 管道压降计算
│   │   │   ├── refrigeration_cycle_calculator.py  # 制冷循环计算
│   │   │   └── npsha_calculator.py  # NPSHa计算
│   ├── process_design/                 # 工艺设计模块
│   │   ├── tabs/
│   │   │   └── process_flow_diagram_tab.py  # 工艺流程图设计
│   │   └── utils/
│   │       └── validation_utils.py  # 通用验证工具
```

## 🤝 贡献指南
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交代码变更 (`git commit -m 'Add some feature'`)
4. 推送至分支 (`git push origin feature/your-feature`)
5. 提交 Pull Request

## 📄 许可证
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明
- 本工具的计算结果仅供工程参考，实际工程应用中需由专业工程师审核确认
- 计算模型基于通用化工原理及标准，特殊工况下需结合实际场景调整参数
- 使用者应根据具体工程需求验证计算结果的合理性和适用性
