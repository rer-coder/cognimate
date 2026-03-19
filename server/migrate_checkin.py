#!/usr/bin/env python3
"""
打卡系统数据库迁移脚本
创建checkins表用于记录用户打卡状态
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace-cognimate/cognimate.db'


def migrate_checkin_table():
    """创建打卡记录表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查表是否已存在
    cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='checkins'
    ''')
    
    if cursor.fetchone():
        print("✅ checkins 表已存在，跳过创建")
        conn.close()
        return
    
    # 创建打卡记录表
    cursor.execute('''
        CREATE TABLE checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            type TEXT NOT NULL,
            title TEXT,
            scheduled_time TIMESTAMP NOT NULL,
            actual_time TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT,
            reminder_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- 外键约束
            FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE SET NULL
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX idx_checkins_user_date 
        ON checkins(user_id, date(scheduled_time))
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_checkins_status 
        ON checkins(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_checkins_type 
        ON checkins(type)
    ''')
    
    # 创建触发器：自动更新 updated_at
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_checkin_timestamp 
        AFTER UPDATE ON checkins
        BEGIN
            UPDATE checkins SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END
    ''')
    
    conn.commit()
    conn.close()
    print("✅ checkins 表创建成功")


def migrate_reminders_table():
    """更新reminders表，添加checkin_id关联"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='reminders'
    ''')
    
    if not cursor.fetchone():
        # 创建reminders表
        cursor.execute('''
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'default',
                type TEXT NOT NULL,
                title TEXT,
                scheduled_time TIMESTAMP NOT NULL,
                message TEXT,
                is_sent BOOLEAN DEFAULT 0,
                checkin_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (checkin_id) REFERENCES checkins(id) ON DELETE SET NULL
            )
        ''')
        print("✅ reminders 表创建成功")
    else:
        # 检查是否需要添加checkin_id列
        cursor.execute('PRAGMA table_info(reminders)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'checkin_id' not in columns:
            cursor.execute('''
                ALTER TABLE reminders 
                ADD COLUMN checkin_id INTEGER 
                REFERENCES checkins(id) ON DELETE SET NULL
            ''')
            print("✅ reminders 表已更新，添加 checkin_id 列")
    
    conn.commit()
    conn.close()


def migrate_checkin_history_table():
    """创建打卡历史统计表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='checkin_stats'
    ''')
    
    if cursor.fetchone():
        print("✅ checkin_stats 表已存在，跳过创建")
        conn.close()
        return
    
    cursor.execute('''
        CREATE TABLE checkin_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            date TEXT NOT NULL,
            total_count INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0,
            missed_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            completion_rate REAL DEFAULT 0.0,
            streak_days INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_id, date)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX idx_checkin_stats_user_date 
        ON checkin_stats(user_id, date)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ checkin_stats 表创建成功")


def verify_migration():
    """验证迁移结果"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['checkins', 'reminders', 'checkin_stats']
    
    print("\n📊 迁移验证结果:")
    print("-" * 40)
    
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} 条记录")
    
    # 显示表结构
    print("\n📋 checkins 表结构:")
    cursor.execute('PRAGMA table_info(checkins)')
    for row in cursor.fetchall():
        print(f"    {row[1]} ({row[2]})")
    
    conn.close()
    print("\n✅ 数据库迁移完成！")


def rollback():
    """回滚迁移（仅用于测试）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DROP TABLE IF EXISTS checkin_stats')
        cursor.execute('DROP TABLE IF EXISTS checkins')
        print("✅ 已回滚迁移")
    except Exception as e:
        print(f"⚠️ 回滚时出错: {e}")
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback()
    else:
        print("🔄 开始打卡系统数据库迁移...")
        migrate_checkin_table()
        migrate_reminders_table()
        migrate_checkin_history_table()
        verify_migration()
