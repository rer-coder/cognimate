"""
CogniMate 智能日程管理系统 - 数据库迁移脚本
创建所有必要的表结构
"""

import sqlite3
from datetime import datetime

def create_tables(db_path: str = "smart_schedule.db"):
    """创建所有数据库表"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. schedules 表 - 日程核心
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            location TEXT,
            category TEXT DEFAULT 'general',
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            recurrence_rule TEXT,
            source_type TEXT DEFAULT 'manual',
            source_id TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_time ON schedules(start_time, end_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_category ON schedules(category)")
    
    # 2. goals 表 - 长期目标
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            target_value REAL,
            current_value REAL DEFAULT 0,
            unit TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'active',
            priority INTEGER DEFAULT 1,
            schedule_pattern TEXT,
            linked_schedule_ids TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_end_date ON goals(end_date)")
    
    # 3. user_context 表 - 实时状态（位置、特殊事件）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_type TEXT NOT NULL,
            context_key TEXT NOT NULL,
            context_value TEXT,
            valid_from DATETIME,
            valid_until DATETIME,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'manual',
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_type ON user_context(context_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_key ON user_context(context_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_time ON user_context(valid_from, valid_until)")
    
    # 4. schedule_changes 表 - 变更历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_type TEXT NOT NULL,
            schedule_id INTEGER,
            goal_id INTEGER,
            field_name TEXT,
            old_value TEXT,
            new_value TEXT,
            change_reason TEXT,
            user_confirmation TEXT,
            impact_analysis TEXT,
            confirmed_at DATETIME,
            applied_at DATETIME,
            rolled_back_at DATETIME,
            status TEXT DEFAULT 'pending',
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (schedule_id) REFERENCES schedules(id),
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_status ON schedule_changes(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_schedule ON schedule_changes(schedule_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_changes_created ON schedule_changes(created_at)")
    
    # 5. location_rules 表 - 位置与日程关联规则
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS location_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_key TEXT NOT NULL,
            location_name TEXT,
            affected_categories TEXT,
            schedule_adjustments TEXT,
            active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 1,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. cron_sync_log 表 - Cron同步日志
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cron_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            schedule_id INTEGER,
            cron_expression TEXT,
            sync_status TEXT,
            error_message TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库表创建完成: {db_path}")
    return True

def insert_default_data(db_path: str = "smart_schedule.db"):
    """插入默认数据"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入默认位置规则
    default_rules = [
        ('company', '公司', 'meeting,collaboration', '{"reminder_offset": 10}'),
        ('hometown', '老家', 'work,meeting', '{"postpone_to": "next_week"}'),
        ('business_trip', '出差', 'local_activity,personal', '{"cancel": true}'),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO location_rules (location_key, location_name, affected_categories, schedule_adjustments)
        VALUES (?, ?, ?, ?)
    """, default_rules)
    
    conn.commit()
    conn.close()
    
    print("✅ 默认数据插入完成")

def migrate(db_path: str = "smart_schedule.db"):
    """执行完整迁移"""
    create_tables(db_path)
    insert_default_data(db_path)
    print(f"✅ 数据库迁移完成: {db_path}")

if __name__ == "__main__":
    migrate()
