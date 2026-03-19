"""
CogniMate 智能日程管理系统 - FastAPI路由
提供RESTful API接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from core.schedule_manager import ScheduleManager
from database.db import Database

# 创建FastAPI应用
app = FastAPI(
    title="CogniMate 智能日程管理系统",
    description="核心架构升级 - 数据库为唯一真相源",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化管理器
schedule_manager = ScheduleManager()

# ==================== Pydantic模型 ====================

class UserInputRequest(BaseModel):
    user_input: str = Field(..., description="用户输入文本")
    current_context: Optional[dict] = Field(None, description="当前上下文")

class ScheduleData(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    category: Optional[str] = "general"
    priority: Optional[int] = 1
    status: Optional[str] = "active"
    recurrence_rule: Optional[str] = None

class ProposeChangesRequest(BaseModel):
    old_schedules: List[ScheduleData]
    new_schedules: List[ScheduleData]

class ConfirmChangesRequest(BaseModel):
    batch_id: str = Field(..., description="变更批次ID")
    user_confirmation: str = Field(..., description="用户确认文本")

class LocationUpdateRequest(BaseModel):
    location: str = Field(..., description="新位置 (company/hometown/business_trip)")

class CreateScheduleRequest(BaseModel):
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = "general"
    priority: Optional[int] = 1

class UpdateScheduleRequest(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

# ==================== API端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "CogniMate 智能日程管理系统",
        "version": "2.0.0",
        "status": "running"
    }

@app.post("/analyze_impact", response_model=dict)
async def analyze_impact(request: UserInputRequest):
    """
    分析用户输入的影响
    
    检测用户输入中的变更意图，分析可能影响
    """
    try:
        result = schedule_manager.analyze_impact(request.user_input)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/propose_changes", response_model=dict)
async def propose_changes(request: ProposeChangesRequest):
    """
    生成变更建议
    
    对比新旧日程状态，检测变化并生成变更报告
    """
    try:
        # 转换Pydantic模型为字典
        old_schedules = [s.dict() for s in request.old_schedules]
        new_schedules = [s.dict() for s in request.new_schedules]
        
        result = schedule_manager.propose_changes(old_schedules, new_schedules)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm_changes", response_model=dict)
async def confirm_changes(request: ConfirmChangesRequest):
    """
    执行确认的变更
    
    解析用户确认，执行同意的变更并同步到Cron
    """
    try:
        result = schedule_manager.confirm_changes(
            request.batch_id,
            request.user_confirmation
        )
        return {
            "success": result.get('success', False),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/today", response_model=dict)
async def get_today_schedules():
    """
    获取今日日程（从数据库）
    
    核心原则：所有日程必须从数据库读取
    """
    try:
        schedules = schedule_manager.get_today_schedules()
        return {
            "success": True,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "count": len(schedules),
            "data": schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/range", response_model=dict)
async def get_schedules_range(
    start: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end: str = Query(..., description="结束日期 (YYYY-MM-DD)")
):
    """
    获取日期范围日程
    
    核心原则：所有日程必须从数据库读取
    """
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        
        schedules = schedule_manager.get_schedules_by_range(start_dt, end_dt)
        return {
            "success": True,
            "start_date": start,
            "end_date": end,
            "count": len(schedules),
            "data": schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_cron", response_model=dict)
async def sync_cron():
    """
    数据库同步到Cron
    
    核心原则：所有变更必须先更新数据库，再同步Cron
    """
    try:
        results = schedule_manager.sync_to_cron()
        success_count = len([r for r in results if r.get('status') == 'success'])
        failed_count = len([r for r in results if r.get('status') == 'failed'])
        
        return {
            "success": failed_count == 0,
            "total": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 位置感知API ====================

@app.post("/location/update", response_model=dict)
async def update_location(request: LocationUpdateRequest):
    """
    更新用户位置
    
    检测位置变化，自动分析对日程的影响
    """
    try:
        result = schedule_manager.update_location(request.location)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/location/current", response_model=dict)
async def get_current_location():
    """获取当前位置"""
    try:
        location = schedule_manager.db.get_current_location()
        return {
            "success": True,
            "location": location
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 日程CRUD API ====================

@app.post("/schedules", response_model=dict)
async def create_schedule(request: CreateScheduleRequest):
    """创建新日程"""
    try:
        schedule_data = request.dict(exclude_unset=True)
        schedule_id = schedule_manager.db.create_schedule(schedule_data)
        
        # 同步到Cron
        schedule = schedule_manager.db.get_schedule(schedule_id)
        schedule_manager.sync_to_cron([{'schedule_id': schedule_id}])
        
        return {
            "success": True,
            "message": "日程创建成功",
            "schedule_id": schedule_id,
            "data": schedule
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/{schedule_id}", response_model=dict)
async def get_schedule(schedule_id: int):
    """获取单个日程"""
    try:
        schedule = schedule_manager.db.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="日程不存在")
        
        return {
            "success": True,
            "data": schedule
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/schedules/{schedule_id}", response_model=dict)
async def update_schedule(schedule_id: int, request: UpdateScheduleRequest):
    """更新日程"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        success = schedule_manager.db.update_schedule(schedule_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="日程不存在或无需更新")
        
        # 同步到Cron
        schedule_manager.sync_to_cron([{'schedule_id': schedule_id}])
        
        schedule = schedule_manager.db.get_schedule(schedule_id)
        return {
            "success": True,
            "message": "日程更新成功",
            "data": schedule
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/schedules/{schedule_id}", response_model=dict)
async def delete_schedule(schedule_id: int):
    """删除日程（软删除）"""
    try:
        success = schedule_manager.db.delete_schedule(schedule_id, soft=True)
        
        if not success:
            raise HTTPException(status_code=404, detail="日程不存在")
        
        return {
            "success": True,
            "message": "日程已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 变更历史API ====================

@app.get("/schedules/{schedule_id}/history", response_model=dict)
async def get_schedule_history(schedule_id: int):
    """获取日程变更历史"""
    try:
        history = schedule_manager.get_schedule_history(schedule_id)
        return {
            "success": True,
            "schedule_id": schedule_id,
            "count": len(history),
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/changes/pending", response_model=dict)
async def get_pending_changes():
    """获取待确认的变更"""
    try:
        pending = schedule_manager.get_pending_confirmations()
        return {
            "success": True,
            "count": len(pending),
            "data": pending
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
