# TofuApp/main.py
import sys
import os
import traceback
from datetime import datetime

# 添加当前目录和模块目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加 modules 目录到路径
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# 添加 converter 目录到路径
converter_dir = os.path.join(current_dir, 'modules', 'converter')
if converter_dir not in sys.path:
    sys.path.insert(0, converter_dir)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QMessageBox, QMenuBar, QMenu, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFont
from datetime import datetime

try:
    from data_manager import DataManager
    from theme_manager import ThemeManager
    from module_loader import ModuleLoader
except ImportError as e:
    print(f"导入模块失败: {e}")
    traceback.print_exc()
    print("尝试继续运行程序...")

class TofuApp(QMainWindow):
    """Tofu主应用程序"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tofu - 个人生产力工具")
        self.setGeometry(160, 50, 1600, 970)
        
        # 初始化管理器
        self.theme_manager = ThemeManager()
        self.data_manager = DataManager.get_instance()
        
        # 存储模块实例
        self.modules = {}
        
        # 创建UI
        self.setup_ui()
        
        # 加载设置
        self.load_settings()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各功能标签页
        self.create_modules()
        
        # 添加菜单和状态栏
        self.setup_menu()
        self.setup_status_bar()
        
        # 连接信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.theme_manager.theme_changed.connect(self.apply_theme)
    
    def create_modules(self):
        """创建所有功能模块"""
        modules_config = [
            # ("modules.process_design", "ProcessDesignWidget", "工艺设计", "⚙️"),
            ("modules.chemical_calculations", "ChemicalCalculationsWidget", "工程计算", "🔬"),
            ("modules.converter.converter_widget", "ConverterWidget", "换算器", "📐"),
            ("modules.pomodoro", "PomodoroTimer", "番茄时钟", "🍅"),
            ("modules.todo", "TodoManager", "待办事项", "✅"),
            ("modules.notes", "NotesWidget", "笔记", "📝"),
            ("modules.bookmarks", "BookmarksWidget", "书签", "🔖"),
            ("modules.important_dates", "ImportantDatesWidget", "重要日期", "📅"),
            ("modules.countdowns", "CountdownsWidget", "倒计时", "⏰"),
            ("modules.year_progress", "YearProgressWidget", "今年余额", "📊")
        ]
        
        for module_file, class_name, tab_name, icon in modules_config:
            try:
                widget = ModuleLoader.load_module(module_file, class_name, self, self.data_manager)
                tab_text = f"{icon} {tab_name}"
                self.tab_widget.addTab(widget, tab_text)
                self.modules[tab_name] = widget
                    
            except Exception as e:
                print(f"❌ 创建 {tab_name} 标签页失败: {e}")
                traceback.print_exc()
                error_widget = ModuleLoader.create_error_widget(f"{tab_name} 加载失败", str(e))
                self.tab_widget.addTab(error_widget, f"{icon} {tab_name}")
    
    def create_error_tab(self, tab_name, error_message):
        """创建错误标签页"""
        from PySide6.QtWidgets import QLabel
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        
        error_label = QLabel(f"{tab_name} 加载失败")
        error_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        error_layout.addWidget(error_label)
        
        detail_label = QLabel(error_message)
        detail_label.setStyleSheet("color: #666; font-size: 12px;")
        detail_label.setWordWrap(True)
        error_layout.addWidget(detail_label)
        
        self.tab_widget.addTab(error_widget, f"❌ {tab_name}")
    
    def setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📁 文件")
        
        backup_action = QAction("💾 备份数据", self)
        backup_action.triggered.connect(self.backup_data)
        file_menu.addAction(backup_action)
        
        refresh_action = QAction("🔄 刷新所有模块", self)
        refresh_action.triggered.connect(self.refresh_all_modules)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 主题菜单
        self.setup_theme_menu(menubar)
        
        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助")
        about_action = QAction("ℹ️ 关于 Tofu", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 调试菜单 (开发用)
        debug_menu = menubar.addMenu("🐛 调试")
        debug_data_action = QAction("📊 显示数据状态", self)
        debug_data_action.triggered.connect(self.show_data_status)
        debug_menu.addAction(debug_data_action)
    
    def setup_theme_menu(self, menubar):
        """设置主题菜单"""
        theme_menu = menubar.addMenu("🎨 主题")
        
        theme_names = self.theme_manager.get_theme_names()
        for theme_name in theme_names:
            theme_action = QAction(f"{self.get_theme_icon(theme_name)} {theme_name.capitalize()}主题", self)
            theme_action.triggered.connect(
                lambda checked, name=theme_name: self.theme_manager.set_theme(name)
            )
            theme_menu.addAction(theme_action)
    
    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 欢迎消息
        welcome_label = QLabel("Tofu - 您的个人生产力助手")
        status_bar.addWidget(welcome_label)
        
        # 主题信息
        status_bar.addPermanentWidget(QLabel(" | "))
        self.theme_label = QLabel(f"主题: {self.theme_manager.current_theme.capitalize()}")
        status_bar.addPermanentWidget(self.theme_label)
        
        # 数据管理器状态
        status_bar.addPermanentWidget(QLabel(" | "))
        self.data_status_label = QLabel("数据: 单例模式")
        status_bar.addPermanentWidget(self.data_status_label)
        
        # 时间显示
        status_bar.addPermanentWidget(QLabel(" | "))
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)
        
        # 启动时间更新
        self.update_time()
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
    
    def load_settings(self):
        """加载设置"""
        settings = self.data_manager.get_settings()
        saved_theme = settings.get("theme", "light")
        self.theme_manager.set_theme(saved_theme)
        
        # 应用字体设置
        self.setup_fonts()
        
    def setup_fonts(self):
        """设置字体"""
        app_font = QFont("Microsoft YaHei", 10)
        QApplication.setFont(app_font)
        
        title_font = QFont("Microsoft YaHei", 12, QFont.Bold)
        self.tab_widget.setFont(title_font)
    
    def get_theme_icon(self, theme_name):
        """获取主题图标"""
        icons = {"light": "☀️", "dark": "🌙", "blue": "🔵"}
        return icons.get(theme_name, "🎨")
    
    def apply_theme(self, theme_name):
        """应用主题"""
        self.setStyleSheet(self.theme_manager.get_theme())
        self.theme_label.setText(f"主题: {theme_name.capitalize()}")
        
        # 保存主题设置
        settings = self.data_manager.get_settings()
        settings["theme"] = theme_name
        self.data_manager.update_settings(settings)
        
    def update_time(self):
        """更新状态栏时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        if index >= 0:
            tab_name = self.tab_widget.tabText(index)
            self.statusBar().showMessage(f"当前标签页: {tab_name}", 3000)
            
            # 通知模块激活（如果模块支持）
            widget = self.tab_widget.widget(index)
            if hasattr(widget, 'on_activate'):
                widget.on_activate()
    
    def refresh_all_modules(self):
        """刷新所有模块"""
        refresh_count = 0
        for module_name, widget in self.modules.items():
            if hasattr(widget, 'refresh'):
                try:
                    widget.refresh()
                    refresh_count += 1
                except Exception as e:
                    print(f"❌ {module_name} 刷新失败: {e}")
        
        QMessageBox.information(self, "刷新完成", f"已刷新 {refresh_count} 个模块")
    
    def backup_data(self):
        """备份数据"""
        from resource_helper import backup_data_file
        if backup_data_file():
            QMessageBox.information(self, "备份成功", "数据备份已完成")
        else:
            QMessageBox.warning(self, "备份失败", "数据备份失败，请检查文件权限")
    
    def show_about(self):
        """显示关于信息 - 使用带滚动条的自定义对话框"""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QScrollArea, QLabel, QPushButton, QSizePolicy
        )
        from PySide6.QtCore import Qt
        
        about_text = """<h2>Tofu - 个人生产力工具</h2>
<h3>V2.1 标准版</h3><br>
<b>版本信息：</b><br>
v2.1 (2025-12-31)<br>
版权所有 © 2025 Tofu Team<br>
邮件：virmuran@163.com<br><br>

<b>关于作者：</b><br>
Tofu由独立开发者维护，致力于为用户提供简洁高效的个人生产力工具。<br><br>

<b>免责声明：</b><br>
本应用仅作学习用途，使用本应用造成的任何不良后果，本人概不负责。<br><br>

<b>核心功能：</b><br>
• 待办事项管理：高效管理您的日常任务<br>
• 笔记记录：随时记录重要信息<br>
• 番茄时钟：科学的时间管理方法<br>
• 工程计算：化工、工程相关计算工具<br>
• 单位换算：多种单位快速换算<br>
• 重要日期：提醒重要日程安排<br>
• 倒计时：重要事件的倒计时提醒<br><br>

<b>常见问题：</b><br>
<b>问题1：数据存储在哪里？安全吗？</b><br>
答：所有数据都保存在本地JSON文件中，位于应用程序所在目录的data文件夹中。数据在本地存储，不会上传到任何服务器。<br><br>

<b>问题2：是否需要联网？</b><br>
答：Tofu完全可以在离线环境下使用，所有功能都可以离线操作。只有在备份数据到云端时才需要联网。<br><br>

<b>问题3：如何备份和恢复数据？</b><br>
答：可以通过"文件"菜单中的"备份数据"功能进行备份。备份文件保存在应用程序所在目录的backup文件夹中。<br><br>

<b>问题4：支持多设备同步吗？</b><br>
答：目前版本支持本地数据存储，多设备同步功能正在开发中，后续版本会加入。<br><br>

<b>问题5：为什么需要获取本地存储权限？</b><br>
答：应用需要读写本地文件来保存您的待办事项、笔记等数据，因此需要存储权限。<br><br>

<b>问题6：软件是免费的吗？未来会收费吗？</b><br>
答：Tofu目前完全免费使用。未来可能会推出专业版功能，但基础功能会保持免费。<br><br>

<b>问题7：遇到问题如何联系开发者？</b><br>
答：可以通过邮件 virmuran@163.com 联系开发者，或者在GitHub仓库提交Issue。<br><br>

<b>数据安全承诺：</b><br>
1. 所有数据仅在本地存储，不会上传到任何服务器<br>
2. 不会收集用户的个人隐私信息<br>
3. 代码开源，欢迎审查<br>
4. 提供完整的备份和恢复功能<br><br>

<b>更新日志：</b><br>
<b>v2.1 (2025-12-31)</b><br>
1. 新增工程计算模块<br>
2. 优化单位换算器界面<br>
3. 修复番茄时钟的计时问题<br>
4. 提高数据加载速度<br><br>

<b>v2.0 (2025-11-30)</b><br>
1. 重构整体架构，采用模块化设计<br>
2. 新增主题切换功能<br>
3. 添加数据管理器，统一数据管理<br>
4. 优化用户界面<br><br>

<b>v1.0 (2025-10-31)</b><br>
1. 初始版本发布<br>
2. 包含基本待办事项和笔记功能<br>
3. 实现番茄时钟<br>
4. 添加书签管理<br><br>

<b>软件定位：</b><br>
Tofu致力于为用户提供轻量级、高效的个人生产力工具。我们相信好的工具应该简单易用，专注于提升用户的工作效率。通过模块化设计，Tofu可以在不增加复杂性的前提下，提供多种实用的功能。<br><br>

<b>温馨提示：</b><br>
• 定期备份数据以防丢失<br>
• 保持软件更新以获得最佳体验<br>
• 如有建议或问题，欢迎反馈"""
    
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("关于 Tofu")
        dialog.setMinimumSize(700, 500)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容标签
        content_label = QLabel()
        content_label.setTextFormat(Qt.TextFormat.RichText)
        content_label.setText(about_text)
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        content_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # 将标签添加到滚动区域
        scroll_area.setWidget(content_label)
        
        # 创建确定按钮
        button_box = QPushButton("确定")
        button_box.clicked.connect(dialog.accept)
        
        # 添加到布局
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 显示对话框
        dialog.exec()
    
    def show_data_status(self):
        """显示数据状态 (调试用)"""
        try:
            data_file = self.data_manager.data_file
            file_exists = os.path.exists(data_file)
            file_size = os.path.getsize(data_file) if file_exists else 0
            
            project_info = self.data_manager.get_project_info()
            report_counter = self.data_manager.get_report_counter()
            
            status_text = f"""数据文件状态:
位置: {data_file}
存在: {'是' if file_exists else '否'}
大小: {file_size} 字节

项目信息: {project_info}
报告计数器: {report_counter}

数据管理器实例 ID: {id(self.data_manager)}"""
            
            QMessageBox.information(self, "数据状态", status_text)
        except Exception as e:
            QMessageBox.warning(self, "数据状态错误", f"获取数据状态失败: {e}")
    
    def closeEvent(self, event):
        """关闭应用程序事件处理"""
        
        # 停止所有计时器
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        
        # 保存所有模块数据
        for module_name, widget in self.modules.items():
            if hasattr(widget, 'save_data'):
                try:
                    widget.save_data()
                except Exception as e:
                    print(f"❌ 保存 {module_name} 数据失败: {e}")
        
        # 保存主数据
        try:
            self.data_manager._save_data()
        except Exception as e:
            print(f"❌ 主数据保存失败: {e}")
        
        event.accept()

def main():
    """应用程序入口点"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("Tofu")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("TofuSoft")
    
    try:
        window = TofuApp()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "启动失败", f"应用程序启动失败:\n{str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())