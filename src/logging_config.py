# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
하위 호환성을 위해 유지되는 agent_common.logging_config 모듈입니다.
새로운 코드에서는 agent_common.logger 모듈 사용을 권장합니다.
"""

from agent_common.logger import SingleLineFlattenFormatter, ProjectLogger

__all__ = ["SingleLineFlattenFormatter", "ProjectLogger"]
