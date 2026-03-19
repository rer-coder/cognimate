# Feishu Direct Messenger
# 直接调用飞书 API 发送消息

import requests
import json
import time
import os
from datetime import datetime

# 从环境变量读取飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

class FeishuMessenger:
    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id or FEISHU_APP_ID
        self.app_secret = app_secret or FEISHU_APP_SECRET
        self.access_token = None
        self.token_expire_time = 0
        
    def _get_access_token(self):
        """获取飞书访问令牌"""
        if not self.app_id or not self.app_secret:
            print("[Feishu] 错误：未配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
            return None
            
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
            
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                self.access_token = data["tenant_access_token"]
                # 提前5分钟过期
                self.token_expire_time = time.time() + data["expire"] - 300
                print(f"[Feishu] Token获取成功，有效期至: {datetime.fromtimestamp(self.token_expire_time)}")
                return self.access_token
            else:
                error_msg = f"获取token失败: {data}"
                print(f"[Feishu] {error_msg}")
                return None
        except Exception as e:
            print(f"[Feishu] 获取token异常: {e}")
            return None
    
    def send_message(self, user_id, message):
        """发送文本消息给用户"""
        token = self._get_access_token()
        if not token:
            return False, "无法获取访问令牌"
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 确保 user_id 格式正确
        if not user_id.startswith("ou_"):
            user_id = f"ou_{user_id}"
            
        params = {
            "receive_id_type": "open_id"
        }
        
        payload = {
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": message})
        }
        
        try:
            print(f"[Feishu] 发送消息给用户: {user_id}")
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                print(f"[Feishu] 消息发送成功")
                return True, data.get("data", {})
            else:
                error_msg = f"发送失败: {data.get('msg', '未知错误')}"
                print(f"[Feishu] {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = f"发送异常: {str(e)}"
            print(f"[Feishu] {error_msg}")
            return False, error_msg

# 全局实例
_messenger = None

def get_messenger():
    """获取飞书信使实例"""
    global _messenger
    if _messenger is None:
        _messenger = FeishuMessenger()
    return _messenger

def send_message_to_user(user_id, message):
    """便捷函数：发送消息给用户"""
    messenger = get_messenger()
    return messenger.send_message(user_id, message)
