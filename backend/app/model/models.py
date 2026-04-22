"""
ORM 数据模型定义

对应概要设计 2.4 节的三张表：
- BehaviorLog: 行为日志表
- BehaviorRule: 规则配置表
- SemanticLog: 语义解释日志表
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from app.database import Base


class BehaviorLog(Base):
    """
    行为日志表 — 记录每次状态变更
    """
    __tablename__ = "behavior_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    state = Column(String(20), nullable=False)
    duration = Column(Integer, default=0)

class StudySession(Base):
    """
    学习会话表 — 记录每次完整学习周期的统计数据
    """
    __tablename__ = "study_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(50), nullable=False, unique=True)
    startTime = Column(DateTime, default=datetime.now)
    endTime = Column(DateTime)
    totalDuration = Column(Integer, default=0)
    focusDuration = Column(Integer, default=0)
    distractedDuration = Column(Integer, default=0)
    lowEfficiencyDuration = Column(Integer, default=0)
    awayDuration = Column(Integer, default=0)
    distractedCount = Column(Integer, default=0)


class BehaviorRule(Base):
    """
    规则配置表 — 存储用户定义的行为判定规则
    """
    __tablename__ = "behavior_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruleName = Column(String(100), nullable=False)
    conditionJson = Column(Text, nullable=False)
    outputState = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.now)


class SemanticLog(Base):
    """
    语义解释日志表 — 记录 VLM 生成的状态解释
    """
    __tablename__ = "semantic_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionId = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    state = Column(String(20), nullable=False)
    explanation = Column(Text, nullable=False)
    source = Column(String(20), default="template")


class NlRuleParseLog(Base):
    """
    自然语言规则解析日志表
    """
    __tablename__ = "nl_rule_parse_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    inputText = Column(Text, nullable=False)
    parsedJson = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
