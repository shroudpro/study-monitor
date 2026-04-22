import pytest
from app.schema.schemas import DetectionItem, AbstractedState
from app.service.state_service import StateService

@pytest.fixture
def state_service():
    return StateService()

def create_mock_person_with_keypoints(kpts_config):
    """辅助方法生成包含被修改关键点的 person detection"""
    # 填满 17个点，默认都看不到
    keypoints = [[0.0, 0.0, 0.0] for _ in range(17)]
    for idx, conf in kpts_config.items():
        keypoints[idx] = conf
    return DetectionItem(className="person", confidence=0.9, bbox=[0,0,1,1], keypoints=keypoints)

def test_abstract_is_present(state_service):
    # 没人的情况
    state = state_service.abstract([])
    assert not state.isPresent
    
    # 没人脸的普通人
    det = create_mock_person_with_keypoints({})
    state = state_service.abstract([det])
    assert state.isPresent
    assert not state.faceVisible

def test_abstract_face_visible(state_service):
    # 鼻子和眼睛可见 => faceVisible
    det = create_mock_person_with_keypoints({
        0: [0.5, 0.5, 0.8], # nose
        1: [0.45, 0.45, 0.8], # left eye
    })
    state = state_service.abstract([det])
    assert state.faceVisible

def test_abstract_head_turned_away(state_service):
    # 一只耳朵可见，另一只完全不可见，属于大幅度侧脸
    det = create_mock_person_with_keypoints({
        0: [0.5, 0.5, 0.3], # 鼻子不可见/不太可见
        3: [0.3, 0.5, 0.9], # 左耳清楚可见
        4: [0.7, 0.5, 0.1], # 右耳不可见
    })
    state = state_service.abstract([det])
    assert state.headTurnedAway
    assert not state.faceVisible

def test_abstract_head_down(state_service):
    # 鼻子Y坐标基本挨着肩膀中点Y坐标
    det = create_mock_person_with_keypoints({
        0: [0.5, 0.6, 0.8], # nose Y=0.6
        5: [0.3, 0.61, 0.8], # L shoulder Y=0.61
        6: [0.7, 0.61, 0.8], # R shoulder Y=0.61
    })
    state = state_service.abstract([det])
    # 由于距离 < 0.05
    assert state.headDown

def test_abstract_posture_stable(state_service):
    # 连续多帧传入几乎不动的位置
    for _ in range(6):
        det = create_mock_person_with_keypoints({
            0: [0.5, 0.2, 0.8], 
            5: [0.3, 0.5, 0.8], 
            6: [0.7, 0.5, 0.8], 
        })
        state = state_service.abstract([det])
    
    assert state.postureStable

    # 突然大动
    det = create_mock_person_with_keypoints({
        0: [0.8, 0.8, 0.8], 
        5: [0.6, 0.9, 0.8], 
        6: [1.0, 0.9, 0.8], 
    })
    state = state_service.abstract([det])
    assert not state.postureStable
