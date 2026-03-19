#!/usr/bin/env python3
"""
数据库迁移脚本 - 扩展目标追踪功能
添加完成状态、进度追踪、打卡记录
"""

import sqlite3
import os

def migrate_database():
    """执行数据库迁移"""
    db_path = '/root/.openclaw/workspace-cognimate/cognimate.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🗄️  开始数据库迁移...")
    
    # 1. 扩展 schedules 表
    print("1. 扩展 schedules 表...")
    try:
        cursor.execute('''
            ALTER TABLE schedules ADD COLUMN completed BOOLEAN DEFAULT 0
        ''')
        cursor.execute('''
            ALTER TABLE schedules ADD COLUMN completed_at TIMESTAMP
        ''')
        cursor.execute('''
            ALTER TABLE schedules ADD COLUMN related_goal_id INTEGER
        ''')
        print("   ✅ schedules 表扩展完成")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("   ℹ️  schedules 表已扩展")
        else:
            print(f"   ❌ 错误: {e}")
    
    # 2. 扩展 goals 表
    print("2. 扩展 goals 表...")
    try:
        cursor.execute('''
            ALTER TABLE goals ADD COLUMN current_value TEXT
        ''')
        cursor.execute('''
            ALTER TABLE goals ADD COLUMN progress_percent INTEGER DEFAULT 0
        ''')
        cursor.execute('''
            ALTER TABLE goals ADD COLUMN start_date TEXT
        ''')
        print("   ✅ goals 表扩展完成")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("   ℹ️  goals 表已扩展")
        else:
            print(f"   ❌ 错误: {e}")
    
    # 3. 创建 daily_checkins 表
    print("3. 创建 daily_checkins 表...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                goal_id INTEGER,
                schedule_id INTEGER,
                completed BOOLEAN DEFAULT 0,
                note TEXT,
                checkin_type TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id),
                FOREIGN KEY (schedule_id) REFERENCES schedules(id)
            )
        ''')
        print("   ✅ daily_checkins 表创建完成")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 4. 创建 goal_progress 表（目标进度历史）
    print("4. 创建 goal_progress 表...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                progress_percent INTEGER,
                current_value TEXT,
                note TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        print("   ✅ goal_progress 表创建完成")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 5. 创建索引优化查询
    print("5. 创建索引...")
    try:
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedules_completed ON schedules(completed)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_checkins_date ON daily_checkins(date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_goal_progress_goal_id ON goal_progress(goal_id)
        ''')
        print("   ✅ 索引创建完成")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 数据库迁移完成！")
    print("\n新增功能：")
    print("  • 日程完成状态追踪")
    print("  • 目标进度百分比")
    print("  • 每日打卡记录")
    print("  • 目标进度历史")

if __name__ == "__main__":
    migrate_database()
