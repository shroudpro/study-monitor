import pytest
from app.schema.schemas import AbstractedState
from app.service.rule_engine import RuleEngine

@pytest.fixture
def engine():
    return RuleEngine()

def test_evaluate_away(engine):
    state = AbstractedState(isPresent=False)
    status, conf = engine.evaluate(state)
    assert status == "离开"

def test_evaluate_distracted(engine):
    # 人在位，但头大幅度偏离
    state = AbstractedState(isPresent=True, headTurnedAway=True)
    status, conf = engine.evaluate(state)
    assert status == "分心"

def test_evaluate_low_efficiency_head_down(engine):
    # 长时间低头趴睡
    state = AbstractedState(
        isPresent=True, 
        headDown=True, 
        stableDuration=6.0
    )
    status, conf = engine.evaluate(state)
    assert status == "低效"

    # 短时间低头 -> 未知或容忍
    state2 = AbstractedState(
        isPresent=True, 
        headDown=True, 
        stableDuration=2.0
    )
    status2, conf2 = engine.evaluate(state2)
    assert status2 == "未知"

def test_evaluate_low_efficiency_unstable(engine):
    # 疯狂乱动
    state = AbstractedState(isPresent=True, postureStable=False)
    status, conf = engine.evaluate(state)
    assert status == "低效"

def test_evaluate_focus(engine):
    # 完美的学习状态
    state = AbstractedState(
        isPresent=True,
        faceVisible=True,
        postureStable=True
    )
    status, conf = engine.evaluate(state)
    assert status == "专注"
