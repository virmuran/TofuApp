# TofuApp/data_manager.py
import sqlite3
import uuid
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal
import os

class DataManager(QObject):
    """数据管理类，负责SQLite数据库操作 - 单例模式"""
    
    # 单例实例
    _instance = None
    _initialized = False
    
    # 定义信号
    data_changed = Signal(str)  # 数据变更信号，参数为变更的数据类型
    
    def __new__(cls, db_file=None):
        """单例模式的 __new__ 方法"""
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_file=None):
        """初始化方法 - 只执行一次"""
        if DataManager._initialized:
            return
            
        super().__init__()
        
        # 数据库文件路径（默认使用应用数据目录）
        if db_file is None:
            db_file = self._get_default_db_file_path()
        
        self.db_file = db_file
        self.conn = None
        self._init_database()  # 初始化数据库和表结构
        
        DataManager._initialized = True
    
    @classmethod
    def get_instance(cls, db_file=None):
        """获取单例实例的类方法"""
        if cls._instance is None:
            cls._instance = DataManager(db_file)
        return cls._instance
    
    def _get_default_db_file_path(self):
        """获取默认数据库文件路径"""
        try:
            from PySide6.QtCore import QStandardPaths
            app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not app_data_dir:
                app_data_dir = os.path.abspath(".")
            os.makedirs(app_data_dir, exist_ok=True)
            return os.path.join(app_data_dir, "tofu_data.db")
        except Exception:
            return os.path.join(os.path.abspath("."), "tofu_data.db")
    
    def _init_database(self):
        """初始化数据库连接和表结构"""
        try:
            # 建立数据库连接（不存在则自动创建）
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 支持按列名访问
            
            # 创建表结构
            cursor = self.conn.cursor()
            
            # 工程信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                project_number TEXT,
                project_name TEXT,
                subproject_name TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 报告计数器表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_counter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                count INTEGER DEFAULT 1
            )
            ''')
            
            # 设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT
            )
            ''')
            
            # 设备表（核心）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                equipment_id TEXT PRIMARY KEY,
                name TEXT,
                description_en TEXT,
                design_pressure REAL DEFAULT 0.0,
                design_temperature REAL DEFAULT 0.0,
                unique_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- 可扩展其他设备字段
                other_fields TEXT  -- 用JSON存储非结构化字段（可选）
            )
            ''')
            
            # 设备名称映射表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_name_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chinese_name TEXT UNIQUE,
                english_name TEXT
            )
            ''')
            
            # 物料表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                properties TEXT,  -- JSON格式存储物料属性
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # MSDS文档表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS msds_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_path TEXT,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 项目表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            print(f"✅ SQLite数据库初始化成功: {self.db_file}")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            traceback.print_exc()
    
    def _safe_float(self, value, default=0.0):
        """安全转换浮点数值（复用原有逻辑）"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                cleaned = value.strip()
                if cleaned.upper() in ['NT', 'N/A', 'NA', 'NULL', '-', '--', '']:
                    return default
                return float(cleaned)
            else:
                return default
        except (ValueError, TypeError):
            return default
    
    # ==================== 工程信息相关方法 ====================
    def get_project_info(self):
        """获取工程信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM project_info LIMIT 1')
        row = cursor.fetchone()
        if row:
            return {
                "company_name": row["company_name"] or "",
                "project_number": row["project_number"] or "",
                "project_name": row["project_name"] or "",
                "subproject_name": row["subproject_name"] or ""
            }
        return {
            "company_name": "",
            "project_number": "",
            "project_name": "",
            "subproject_name": ""
        }
    
    def update_project_info(self, project_info):
        """更新工程信息"""
        try:
            cursor = self.conn.cursor()
            # 先删除原有记录（单条），再插入新记录
            cursor.execute('DELETE FROM project_info')
            cursor.execute('''
            INSERT INTO project_info (company_name, project_number, project_name, subproject_name)
            VALUES (?, ?, ?, ?)
            ''', (
                project_info.get("company_name", ""),
                project_info.get("project_number", ""),
                project_info.get("project_name", ""),
                project_info.get("subproject_name", "")
            ))
            self.conn.commit()
            self.data_changed.emit("project_info")
            print(f"工程信息已保存: {project_info}")
            return True
        except Exception as e:
            print(f"❌ 更新工程信息失败: {e}")
            return False
    
    # ==================== 报告计数器相关方法 ====================
    def get_report_counter(self):
        """获取通用的报告计数器"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM report_counter LIMIT 1')
        row = cursor.fetchone()
        if row:
            return {"date": row["date"], "count": row["count"]}
        return {"date": "", "count": 0}
    
    def update_report_counter(self, counter):
        """更新通用的报告计数器"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM report_counter')
            cursor.execute('''
            INSERT INTO report_counter (date, count)
            VALUES (?, ?)
            ''', (counter.get("date", ""), counter.get("count", 1)))
            self.conn.commit()
            self.data_changed.emit("report_counter")
            print(f"报告计数器已更新: {counter}")
            return True
        except Exception as e:
            print(f"❌ 更新报告计数器失败: {e}")
            return False
    
    def get_next_report_number(self, prefix="PD"):
        """获取下一个报告编号"""
        today = datetime.now().strftime("%Y%m%d")
        counter = self.get_report_counter()
        
        if counter.get("date") != today:
            counter = {"date": today, "count": 1}
        else:
            counter["count"] = counter.get("count", 0) + 1
        
        self.update_report_counter(counter)
        report_number = f"{prefix}-{today}-{counter['count']:03d}"
        print(f"生成报告编号: {report_number}")
        return report_number
    
    # ==================== 设置相关方法 ====================
    def get_settings(self):
        """获取设置"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        rows = cursor.fetchall()
        settings = {row["key"]: row["value"] for row in rows}
        return settings
    
    def update_settings(self, settings):
        """更新设置"""
        try:
            cursor = self.conn.cursor()
            # 清空原有设置，批量插入新设置
            cursor.execute('DELETE FROM settings')
            for key, value in settings.items():
                cursor.execute('''
                INSERT INTO settings (key, value) VALUES (?, ?)
                ''', (key, str(value)))
            self.conn.commit()
            self.data_changed.emit("settings")
            print("设置已更新")
            return True
        except Exception as e:
            print(f"❌ 更新设置失败: {e}")
            return False
    
    # ==================== 设备相关方法 ====================
    def get_equipment_data(self) -> List[Dict]:
        """获取所有设备数据"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def add_equipment(self, equipment_data: Dict) -> bool:
        """添加/更新设备（兼容原有逻辑）"""
        try:
            # 数据清洗
            equipment_data['design_pressure'] = self._safe_float(equipment_data.get('design_pressure', 0))
            equipment_data['design_temperature'] = self._safe_float(equipment_data.get('design_temperature', 0))
            
            # 生成设备ID（如果不存在）
            if 'equipment_id' not in equipment_data or not equipment_data['equipment_id']:
                equipment_data['equipment_id'] = f"EQ_{uuid.uuid4().hex[:8].upper()}"
            
            # 更新时间
            equipment_data['updated_at'] = datetime.now().isoformat()
            if 'created_at' not in equipment_data:
                equipment_data['created_at'] = datetime.now().isoformat()
            
            cursor = self.conn.cursor()
            # 先尝试更新，无记录则插入（UPSERT）
            cursor.execute('''
            INSERT OR REPLACE INTO equipment (
                equipment_id, name, description_en, design_pressure, design_temperature,
                unique_code, created_at, updated_at, other_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipment_data['equipment_id'],
                equipment_data.get('name', ''),
                equipment_data.get('description_en', ''),
                equipment_data['design_pressure'],
                equipment_data['design_temperature'],
                equipment_data.get('unique_code', ''),
                equipment_data['created_at'],
                equipment_data['updated_at'],
                equipment_data.get('other_fields', '{}')  # 非结构化字段用JSON存储
            ))
            
            self.conn.commit()
            self.data_changed.emit("equipment")
            print(f"✅ 保存设备成功: {equipment_data['equipment_id']}")
            return True
        except Exception as e:
            print(f"❌ 添加设备失败: {e}")
            traceback.print_exc()
            return False
    
    def update_equipment(self, equipment_id: str, update_data: Dict) -> bool:
        """更新设备（指定ID）"""
        try:
            # 补充更新时间
            update_data['updated_at'] = datetime.now().isoformat()
            
            cursor = self.conn.cursor()
            # 构建更新语句（动态字段）
            update_fields = []
            values = []
            for key, value in update_data.items():
                if key not in ['equipment_id']:  # 主键不更新
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            values.append(equipment_id)
            
            if not update_fields:
                return True
            
            sql = f'''
            UPDATE equipment
            SET {', '.join(update_fields)}
            WHERE equipment_id = ?
            '''
            cursor.execute(sql, values)
            
            if cursor.rowcount == 0:
                print(f"⚠️ 设备未找到: {equipment_id}")
                return False
            
            self.conn.commit()
            self.data_changed.emit("equipment")
            print(f"🔄 更新设备成功: {equipment_id}")
            return True
        except Exception as e:
            print(f"❌ 更新设备失败: {e}")
            return False
    
    def delete_equipment(self, equipment_id: str) -> bool:
        """删除设备"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM equipment WHERE equipment_id = ?', (equipment_id,))
            
            if cursor.rowcount == 0:
                print(f"⚠️ 设备未找到: {equipment_id}")
                return False
            
            self.conn.commit()
            self.data_changed.emit("equipment")
            print(f"🗑️ 删除设备成功: {equipment_id}")
            return True
        except Exception as e:
            print(f"❌ 删除设备失败: {e}")
            return False
    
    def get_equipment_by_id(self, equipment_id: str) -> Optional[Dict]:
        """根据ID获取设备"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment WHERE equipment_id = ?', (equipment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_equipment_by_unique_code(self, unique_code: str) -> Optional[Dict]:
        """根据唯一编码获取设备"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM equipment WHERE unique_code = ?', (unique_code,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== 设备名称映射相关方法 ====================
    def get_equipment_name_mapping(self):
        """获取设备名称对照表"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT chinese_name, english_name FROM equipment_name_mapping')
        rows = cursor.fetchall()
        return {row["chinese_name"]: row["english_name"] for row in rows}
    
    def add_equipment_name_mapping(self, chinese_name, english_name):
        """添加设备名称对照"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO equipment_name_mapping (chinese_name, english_name)
            VALUES (?, ?)
            ''', (chinese_name, english_name))
            self.conn.commit()
            self.data_changed.emit("equipment_name_mapping")
            return True
        except Exception as e:
            print(f"❌ 添加名称映射失败: {e}")
            return False
    
    def remove_equipment_name_mapping(self, chinese_name):
        """移除设备名称对照"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM equipment_name_mapping WHERE chinese_name = ?', (chinese_name,))
            self.conn.commit()
            self.data_changed.emit("equipment_name_mapping")
            return True
        except Exception as e:
            print(f"❌ 移除名称映射失败: {e}")
            return False
    
    def get_english_name(self, chinese_name):
        """根据中文名称获取英文名称"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT english_name FROM equipment_name_mapping WHERE chinese_name = ?
        ''', (chinese_name,))
        row = cursor.fetchone()
        return row["english_name"] if row else ""
    
    # ==================== 物料/msds/项目 基础方法（保留原有接口） ====================
    def get_materials(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM materials')
        return [dict(row) for row in cursor.fetchall()]
    
    def add_material(self, material_data: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO materials (name, properties) VALUES (?, ?)
            ''', (material_data.get('name', ''), material_data.get('properties', '{}')))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 添加物料失败: {e}")
            return False
    
    def get_msds_documents(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM msds_documents')
        return [dict(row) for row in cursor.fetchall()]
    
    def add_msds_document(self, msds_data: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO msds_documents (title, file_path) VALUES (?, ?)
            ''', (msds_data.get('title', ''), msds_data.get('file_path', '')))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 添加MSDS失败: {e}")
            return False
    
    def get_projects(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM projects')
        return [dict(row) for row in cursor.fetchall()]
    
    def add_project(self, project_data: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO projects (name, description) VALUES (?, ?)
            ''', (project_data.get('name', ''), project_data.get('description', '')))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 添加项目失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接（程序退出时调用）"""
        if self.conn:
            self.conn.close()
            print("🔌 数据库连接已关闭")

# 程序退出时自动关闭连接（可选）
import atexit
atexit.register(lambda: DataManager.get_instance().close())