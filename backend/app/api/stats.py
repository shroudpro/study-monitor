"""
统计相关 API 路由
"""

from fastapi import APIRouter

from app.schema.schemas import StatsResponse
from app.service.stats_service import statsService

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def getStats():
    """
    获取学习行为统计

    Returns:
        包含专注时长、分心次数、手机使用时长等统计指标
    """
    return statsService.getStats()

@router.post("/session/start")
async def startSession():
    from app.service.timeline_service import timelineService
    from app.service.state_service import stateService
    import time
    
    # 额外清空 state_service 的计时器，保证在点开始瞬间从头计算
    stateService._inactive_start = time.time()
    stateService._away_start = time.time()
    
    return statsService.startSession()

@router.post("/session/reset")
async def resetSession():
    return statsService.resetSession()

@router.post("/session/stop")
async def stopSession():
    return statsService.stopSession()
