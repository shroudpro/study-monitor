import time

from app.service.timeline_service import TimelineService


def test_raw_state_duration_and_stable_switch():
    service = TimelineService()
    service.startSession()

    # 连续观测原始状态
    service.observeRaw("专注")
    time.sleep(0.01)
    raw_duration = service.observeRaw("专注")
    assert raw_duration > 0

    # 在窗口内持续输入，触发稳定态切换
    for _ in range(12):
        service.update("专注")
    assert service.currentState == "专注"
    assert service.stableDuration >= 0
