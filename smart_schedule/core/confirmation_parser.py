"""
CogniMate 智能日程管理系统 - 部分确认解析器
解析用户"哪些不同意"
"""

import re
from typing import List, Dict, Tuple, Set
from enum import Enum

class ConfirmationType(Enum):
    ALL_APPROVE = "all_approve"           # 全部同意
    ALL_REJECT = "all_reject"             # 全部不同意
    PARTIAL_APPROVE = "partial_approve"   # 部分同意
    UNCLEAR = "unclear"                   # 不明确

class PartialConfirmationParser:
    """部分确认解析器 - 解析用户的部分同意回复"""
    
    def __init__(self):
        # 同意关键词
        self.approve_keywords = [
            '同意', '可以', '好', '行', 'ok', '是的', '没错', '对的',
            '批准', '接受', 'apply', 'confirm', 'yes', 'y'
        ]
        
        # 拒绝关键词
        self.reject_keywords = [
            '不同意', '不要', '不行', '拒绝', '取消', '否决',
            'reject', 'no', 'deny', 'n', 'pass', '跳过'
        ]
        
        # 全部关键词
        self.all_keywords = ['全部', '所有', '一切', '都', 'every', 'all', '全部']
        
        # 数字匹配模式
        self.number_patterns = [
            r'第([\d,、，\s]+)项',  # 第1、2、3项
            r'([\d,、，\s]+)[项个]',  # 1、2、3项
            r'([\d,、，\s]+)(?:和|与|,|，|\s)',  # 1、2、3
            r'除了.*第?([\d,、，\s]+)',  # 除了第1、2
            r'([\d,、，\s]+)除外',  # 1、2除外
            r'([\d,、，\s]+)不',  # 1、2不
        ]
    
    def parse_confirmation(self, user_input: str, 
                          total_changes: int) -> Tuple[ConfirmationType, List[int]]:
        """
        解析用户确认回复
        
        Args:
            user_input: 用户输入
            total_changes: 变更总数
        
        Returns:
            (确认类型, 批准的变更索引列表)
        """
        user_input = user_input.strip().lower()
        
        # 1. 检查是否全部同意
        if self._is_all_approve(user_input):
            return ConfirmationType.ALL_APPROVE, list(range(1, total_changes + 1))
        
        # 2. 检查是否全部拒绝
        if self._is_all_reject(user_input):
            return ConfirmationType.ALL_REJECT, []
        
        # 3. 解析部分同意
        approved, rejected = self._parse_partial(user_input, total_changes)
        
        if approved or rejected:
            return ConfirmationType.PARTIAL_APPROVE, approved
        
        # 4. 无法解析
        return ConfirmationType.UNCLEAR, []
    
    def _is_all_approve(self, user_input: str) -> bool:
        """检查是否全部同意"""
        # 直接匹配"全部同意"等
        all_approve_patterns = [
            r'全部同意',
            r'所有.*同意',
            r'都.*同意',
            r'.*都[可以好行]',
            r'all.*(ok|approve|confirm|yes)',
            r'^ok$', r'^好的$', r'^可以$', r'^行$',
            r'就这样', r'就这么办', r'确定', r'确认'
        ]
        
        for pattern in all_approve_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        
        return False
    
    def _is_all_reject(self, user_input: str) -> bool:
        """检查是否全部拒绝"""
        all_reject_patterns = [
            r'全部不同意',
            r'所有.*不同意',
            r'都.*不同意',
            r'都.*不要',
            r'全.*取消',
            r'都.*拒绝',
            r'all.*(no|reject|deny)',
            r'都不',
            r'算了', r'取消', r'放弃'
        ]
        
        for pattern in all_reject_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        
        return False
    
    def _parse_partial(self, user_input: str, total_changes: int) -> Tuple[List[int], List[int]]:
        """
        解析部分同意
        
        Returns:
            (批准的索引列表, 拒绝的索引列表)
        """
        approved = set()
        rejected = set()
        
        # 模式1: "除了X，其他都同意" / "X除外，其他同意"
        except_match = re.search(r'除了.*?第?([\d,、，\s和与]+).{0,5}(?:其他|其余|剩下|其它).{0,5}(?:同意|可以|行|ok)', user_input)
        if except_match:
            except_indices = self._extract_numbers(except_match.group(1))
            rejected.update(except_indices)
            approved.update(i for i in range(1, total_changes + 1) if i not in except_indices)
            return sorted(approved), sorted(rejected)
        
        # 模式2: "除了X不同意，其他都同意"
        except_reject_match = re.search(r'除了.*?第?([\d,、，\s和与]+).{0,5}(?:不同|不要|拒绝)', user_input)
        if except_reject_match:
            except_indices = self._extract_numbers(except_reject_match.group(1))
            rejected.update(except_indices)
            approved.update(i for i in range(1, total_changes + 1) if i not in except_indices)
            return sorted(approved), sorted(rejected)
        
        # 模式3: "X、Y不同意，其他同意"
        reject_then_approve = re.search(r'第?([\d,、，\s和与]+)[项个]?.{0,3}(?:不同|不要|拒绝|取消)', user_input)
        if reject_then_approve:
            rejected_indices = self._extract_numbers(reject_then_approve.group(1))
            # 检查是否后面有"其他同意"
            if re.search(r'(其他|其余|其它).{0,5}(?:同意|可以|行)', user_input):
                rejected.update(rejected_indices)
                approved.update(i for i in range(1, total_changes + 1) if i not in rejected_indices)
                return sorted(approved), sorted(rejected)
        
        # 模式4: "X、Y同意，其他不同意"
        approve_then_reject = re.search(r'第?([\d,、，\s和与]+)[项个]?.{0,3}(?:同意|可以|行|ok)', user_input)
        if approve_then_reject:
            approved_indices = self._extract_numbers(approve_then_reject.group(1))
            # 检查是否后面有"其他不同意"
            if re.search(r'(其他|其余|其它).{0,5}(?:不同|不要|拒绝)', user_input):
                approved.update(approved_indices)
                rejected.update(i for i in range(1, total_changes + 1) if i not in approved_indices)
                return sorted(approved), sorted(rejected)
        
        # 模式5: 只列出不同意的项
        # "第1、3项不同意" 或 "1、2不同意" 或 "1和2不要"
        reject_patterns = [
            r'第?([\d,、，\s和与]+)[项个]?.*(?:不同|不要|拒绝|取消|跳过|pass)',
            r'(?:不要|取消|拒绝).*第?([\d,、，\s和与]+)',
        ]
        
        for pattern in reject_patterns:
            match = re.search(pattern, user_input)
            if match:
                rejected_indices = self._extract_numbers(match.group(1))
                rejected.update(rejected_indices)
                approved.update(i for i in range(1, total_changes + 1) if i not in rejected_indices)
                return sorted(approved), sorted(rejected)
        
        # 模式6: 只列出同意的项
        approve_patterns = [
            r'第?([\d,、，\s和与]+)[项个]?.*(?:同意|可以|行|ok|确定)',
        ]
        
        for pattern in approve_patterns:
            match = re.search(pattern, user_input)
            if match:
                approved_indices = self._extract_numbers(match.group(1))
                approved.update(approved_indices)
                return sorted(approved), sorted(rejected)
        
        return sorted(approved), sorted(rejected)
    
    def _extract_numbers(self, text: str) -> List[int]:
        """从文本中提取数字列表"""
        numbers = []
        
        # 匹配单个数字
        single_digits = re.findall(r'\d+', text)
        numbers.extend(int(d) for d in single_digits)
        
        return numbers
    
    def generate_confirmation_request(self, pending_changes: List[Dict]) -> str:
        """
        生成确认请求消息
        
        Args:
            pending_changes: 待确认的变更列表
        
        Returns:
            确认请求文本
        """
        if not pending_changes:
            return "没有待确认的变更。"
        
        lines = ["📋 **请确认以下变更：**\n"]
        
        for i, change in enumerate(pending_changes, 1):
            description = change.get('description', '')
            impact = change.get('impact_level', 'low')
            
            impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(impact, '⚪')
            lines.append(f"{impact_emoji} **{i}.** {description}")
        
        lines.append("\n💬 **回复示例：**")
        lines.append('  • "全部同意"')
        lines.append('  • "全部不同意"')
        lines.append('  • "除了第2项，其他同意"')
        lines.append('  • "第1、3项不同意"')
        
        return "\n".join(lines)
    
    def generate_partial_result_message(self, approved: List[int], 
                                        rejected: List[int],
                                        total: int) -> str:
        """
        生成部分确认结果消息
        
        Args:
            approved: 批准的变更索引
            rejected: 拒绝的变更索引
            total: 变更总数
        
        Returns:
            结果消息
        """
        lines = ["✅ **确认结果：**"]
        
        if approved:
            lines.append(f"  • 同意: 第 {', '.join(map(str, approved))} 项 ({len(approved)}/{total})")
        
        if rejected:
            lines.append(f"  • 不同意: 第 {', '.join(map(str, rejected))} 项 ({len(rejected)}/{total})")
        
        if not approved and not rejected:
            lines.append("  • 未识别到有效的确认指令")
        
        return "\n".join(lines)
