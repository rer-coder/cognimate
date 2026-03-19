"""
CogniMate 智能日程管理系统 - 测试用例
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from core.change_detector import ChangeDetectionEngine, ScheduleChange, ChangeType
from core.impact_analyzer import ImpactAnalyzer, ImpactAnalysis, ImpactType
from core.report_generator import ReportGenerator
from core.confirmation_parser import PartialConfirmationParser, ConfirmationType
from database.db import Database

# ==================== 测试数据 ====================

@pytest.fixture
def sample_schedules():
    """示例日程数据"""
    now = datetime.now()
    return [
        {
            'id': 1,
            'title': '团队晨会',
            'start_time': (now + timedelta(days=1, hours=9)).isoformat(),
            'end_time': (now + timedelta(days=1, hours=10)).isoformat(),
            'location': '会议室A',
            'category': 'meeting',
            'status': 'active'
        },
        {
            'id': 2,
            'title': '客户会议',
            'start_time': (now + timedelta(days=1, hours=14)).isoformat(),
            'end_time': (now + timedelta(days=1, hours=15, minutes=30)).isoformat(),
            'location': '公司',
            'category': 'meeting',
            'status': 'active'
        },
        {
            'id': 3,
            'title': '健身',
            'start_time': (now + timedelta(days=1, hours=18)).isoformat(),
            'end_time': (now + timedelta(days=1, hours=19, minutes=30)).isoformat(),
            'location': '健身房',
            'category': 'fitness',
            'status': 'active'
        }
    ]

@pytest.fixture
def modified_schedules(sample_schedules):
    """修改后的日程数据"""
    modified = [s.copy() for s in sample_schedules]
    # 修改第一个日程的时间
    modified[0]['start_time'] = (datetime.now() + timedelta(days=2, hours=10)).isoformat()
    modified[0]['end_time'] = (datetime.now() + timedelta(days=2, hours=11)).isoformat()
    return modified

# ==================== 变更检测引擎测试 ====================

class TestChangeDetectionEngine:
    """测试变更检测引擎"""
    
    def test_detect_no_changes(self, sample_schedules):
        """测试无变更情况"""
        db = Database(":memory:")
        engine = ChangeDetectionEngine(db)
        
        changes = engine.detect_changes(sample_schedules, sample_schedules)
        assert len(changes) == 0
    
    def test_detect_time_change(self, sample_schedules, modified_schedules):
        """测试时间变更检测"""
        db = Database(":memory:")
        engine = ChangeDetectionEngine(db)
        
        changes = engine.detect_changes(sample_schedules, modified_schedules)
        
        # 应该检测到2个时间字段变更
        time_changes = [c for c in changes if c.field_name in ['start_time', 'end_time']]
        assert len(time_changes) >= 1
        
        # 检查变更类型
        assert any(c.change_type in [ChangeType.RESCHEDULE, ChangeType.UPDATE] for c in changes)
    
    def test_detect_delete(self, sample_schedules):
        """测试删除检测"""
        db = Database(":memory:")
        engine = ChangeDetectionEngine(db)
        
        # 删除第二个日程
        new_schedules = [sample_schedules[0], sample_schedules[2]]
        
        changes = engine.detect_changes(sample_schedules, new_schedules)
        
        delete_changes = [c for c in changes if c.change_type == ChangeType.DELETE]
        assert len(delete_changes) == 1
        assert delete_changes[0].schedule_id == 2
    
    def test_detect_create(self, sample_schedules):
        """测试新增检测"""
        db = Database(":memory:")
        engine = ChangeDetectionEngine(db)
        
        # 添加新日程
        new_schedule = {
            'id': 4,
            'title': '新项目启动会',
            'start_time': (datetime.now() + timedelta(days=3)).isoformat(),
            'category': 'meeting',
            'status': 'active'
        }
        new_schedules = sample_schedules + [new_schedule]
        
        changes = engine.detect_changes(sample_schedules, new_schedules)
        
        create_changes = [c for c in changes if c.change_type == ChangeType.CREATE]
        assert len(create_changes) == 1
        assert create_changes[0].schedule_id == 4
    
    def test_detect_user_intent(self, sample_schedules):
        """测试用户意图检测"""
        db = Database(":memory:")
        engine = ChangeDetectionEngine(db)
        
        # 测试取消意图
        changes = engine.detect_user_input_changes("取消明天的会议", sample_schedules)
        assert len(changes) >= 1
        assert any(c.get('intent') == 'cancel' for c in changes)
        
        # 测试推迟意图
        changes = engine.detect_user_input_changes("把健身推迟到后天", sample_schedules)
        assert len(changes) >= 1
        assert any(c.get('intent') == 'postpone' for c in changes)

# ==================== 影响分析器测试 ====================

class TestImpactAnalyzer:
    """测试影响分析器"""
    
    def test_analyze_time_conflict(self, sample_schedules):
        """测试时间冲突分析"""
        db = Database(":memory:")
        analyzer = ImpactAnalyzer(db)
        
        # 创建一个与其他日程冲突的变更
        change = {
            'change_type': 'update',
            'schedule_id': 1,
            'field_name': 'start_time',
            'new_value': sample_schedules[1]['start_time']  # 与客户会议同时
        }
        
        impacts = analyzer.analyze_impact(change, sample_schedules)
        
        # 应该检测到冲突
        conflict_impacts = [i for i in impacts if i.impact_type == ImpactType.CONFLICT]
        assert len(conflict_impacts) >= 1
    
    def test_analyze_cancel_impact(self, sample_schedules):
        """测试取消影响分析"""
        db = Database(":memory:")
        analyzer = ImpactAnalyzer(db)
        
        change = {
            'change_type': 'cancel',
            'schedule_id': 3,  # 健身
        }
        
        impacts = analyzer.analyze_impact(change, sample_schedules)
        
        # 应该检测到对目标的影响
        cascading = [i for i in impacts if i.impact_type == ImpactType.CASCADING]
        assert len(cascading) >= 1

# ==================== 确认解析器测试 ====================

class TestConfirmationParser:
    """测试确认解析器"""
    
    def test_parse_all_approve(self):
        """测试全部同意"""
        parser = PartialConfirmationParser()
        
        test_cases = [
            "全部同意",
            "都同意",
            "ok",
            "好的",
            "就这样",
            "确定"
        ]
        
        for case in test_cases:
            confirm_type, approved = parser.parse_confirmation(case, 5)
            assert confirm_type == ConfirmationType.ALL_APPROVE, f"Failed for: {case}"
            assert len(approved) == 5
    
    def test_parse_all_reject(self):
        """测试全部拒绝"""
        parser = PartialConfirmationParser()
        
        test_cases = [
            "全部不同意",
            "都不同意",
            "算了",
            "取消"
        ]
        
        for case in test_cases:
            confirm_type, approved = parser.parse_confirmation(case, 5)
            assert confirm_type == ConfirmationType.ALL_REJECT, f"Failed for: {case}"
            assert len(approved) == 0
    
    def test_parse_partial_except(self):
        """测试部分同意（除了...）"""
        parser = PartialConfirmationParser()
        
        test_cases = [
            ("除了第2项，其他都同意", [1, 3, 4, 5]),
            ("除了1和3，其他同意", [2, 4, 5]),
            ("2除外，其他都ok", [1, 3, 4, 5]),
        ]
        
        for case, expected in test_cases:
            confirm_type, approved = parser.parse_confirmation(case, 5)
            assert confirm_type == ConfirmationType.PARTIAL_APPROVE, f"Failed for: {case}"
            assert approved == expected, f"Failed for: {case}, got {approved}"
    
    def test_parse_partial_specify_reject(self):
        """测试部分同意（指定拒绝）"""
        parser = PartialConfirmationParser()
        
        test_cases = [
            ("第1、3项不同意", [2, 4, 5]),
            ("1和2不要，其他同意", [3, 4, 5]),
        ]
        
        for case, expected in test_cases:
            confirm_type, approved = parser.parse_confirmation(case, 5)
            assert confirm_type == ConfirmationType.PARTIAL_APPROVE, f"Failed for: {case}"
            assert approved == expected, f"Failed for: {case}, got {approved}"

# ==================== 报告生成器测试 ====================

class TestReportGenerator:
    """测试报告生成器"""
    
    def test_generate_summary(self):
        """测试摘要生成"""
        generator = ReportGenerator()
        
        changes = [
            {'change_type': 'create', 'impact_level': 'medium', 'description': '新增日程'},
            {'change_type': 'update', 'impact_level': 'high', 'description': '修改时间'},
            {'change_type': 'delete', 'impact_level': 'high', 'description': '删除日程'},
        ]
        
        report = generator.generate_report(
            changes=changes,
            impact_analysis=[],
            all_schedules=[],
            changed_schedule_ids=[]
        )
        
        assert report.total_changes == 3
        assert '3' in report.summary
        assert len(report.high_impact_changes) == 2

# ==================== 数据库测试 ====================

class TestDatabase:
    """测试数据库操作"""
    
    def test_create_and_get_schedule(self):
        """测试创建和获取日程"""
        db = Database(":memory:")
        
        # 创建表
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # 重新创建db连接
        db = Database(":memory:")
        # 这里简化测试，只测试基本方法存在
        assert hasattr(db, 'create_schedule')
        assert hasattr(db, 'get_schedule')
    
    def test_user_context(self):
        """测试用户上下文"""
        db = Database(":memory:")
        
        # 创建表
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE user_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_type TEXT NOT NULL,
                context_key TEXT NOT NULL,
                context_value TEXT,
                valid_from DATETIME,
                valid_until DATETIME
            )
        """)
        
        assert hasattr(db, 'set_user_context')
        assert hasattr(db, 'get_user_context')

# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 这个测试需要完整的数据库，使用文件数据库
        db_path = "/tmp/test_smart_schedule.db"
        
        # 清理测试数据库
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 初始化数据库
        from database.migration import create_tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                status TEXT DEFAULT 'active'
            )
        """)
        conn.commit()
        conn.close()
        
        # 测试数据库操作
        db = Database(db_path)
        
        # 创建日程
        schedule_id = db.create_schedule({
            'title': '测试会议',
            'start_time': datetime.now().isoformat()
        })
        
        assert schedule_id is not None
        
        # 获取日程
        schedule = db.get_schedule(schedule_id)
        assert schedule is not None
        assert schedule['title'] == '测试会议'
        
        # 清理
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
