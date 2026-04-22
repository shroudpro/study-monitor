"""
规则管理 API 路由

NOTE: MVP 中使用手动 JSON 方式管理规则，
后续接入 VLM 后支持自然语言规则配置。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import getDb
from app.model.models import BehaviorRule
from app.schema.schemas import RuleCreate, RuleUpdate, RuleResponse
from app.service.rule_engine import ruleEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=list[RuleResponse])
async def listRules(db: Session = Depends(getDb)):
    """获取所有规则列表"""
    rules = db.query(BehaviorRule).order_by(BehaviorRule.createdAt.desc()).all()
    return rules


@router.post("", response_model=RuleResponse)
async def createRule(rule: RuleCreate, db: Session = Depends(getDb)):
    """
    创建一条新规则

    创建后自动重新加载规则到引擎
    """
    dbRule = BehaviorRule(
        ruleName=rule.ruleName,
        conditionJson=rule.conditionJson,
        outputState=rule.outputState,
    )
    db.add(dbRule)
    db.commit()
    db.refresh(dbRule)

    # 重新加载规则到引擎
    _reloadRules(db)

    logger.info(f"创建规则: {rule.ruleName}")
    return dbRule


@router.put("/{ruleId}", response_model=RuleResponse)
async def updateRule(
    ruleId: int,
    ruleUpdate: RuleUpdate,
    db: Session = Depends(getDb),
):
    """更新规则"""
    dbRule = db.query(BehaviorRule).filter(BehaviorRule.id == ruleId).first()
    if not dbRule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if ruleUpdate.ruleName is not None:
        dbRule.ruleName = ruleUpdate.ruleName
    if ruleUpdate.conditionJson is not None:
        dbRule.conditionJson = ruleUpdate.conditionJson
    if ruleUpdate.outputState is not None:
        dbRule.outputState = ruleUpdate.outputState
    if ruleUpdate.enabled is not None:
        dbRule.enabled = ruleUpdate.enabled

    db.commit()
    db.refresh(dbRule)

    _reloadRules(db)

    return dbRule


@router.delete("/{ruleId}")
async def deleteRule(ruleId: int, db: Session = Depends(getDb)):
    """删除规则"""
    dbRule = db.query(BehaviorRule).filter(BehaviorRule.id == ruleId).first()
    if not dbRule:
        raise HTTPException(status_code=404, detail="规则不存在")

    db.delete(dbRule)
    db.commit()

    _reloadRules(db)

    return {"message": "规则已删除", "id": ruleId}


def _reloadRules(db: Session) -> None:
    """
    重新加载启用的规则到引擎内存

    NOTE: 每次规则变更后调用，确保引擎使用最新规则
    """
    enabledRules = (
        db.query(BehaviorRule)
        .filter(BehaviorRule.enabled.is_(True))
        .all()
    )
    ruleEngine.loadCustomRules([
        {
            "ruleName": r.ruleName,
            "conditionJson": r.conditionJson,
            "outputState": r.outputState,
        }
        for r in enabledRules
    ])
