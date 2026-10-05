# 작성일: 2026-08-16
# 설계자: 김유상
# 설계자 이메일: bakkus@daum.net

"""
배치 작업의 실시간 진행률(Progress) 추적, 남은 시간(ETA) 및 속도 계산,
설정 % 배수 마일스톤 경고 로깅을 전담하는 공용 진행률 추적 유틸리티 모듈입니다.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional

from agent_common.config_loader import config
from agent_common.time_utils import TimeUtils

# ==============================================================================
# 진행률 추적 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "progress_tracker": {
        "interval_percent_int": 10,       # 진행률 마일스톤 기본 간격 (%)
        "default_task_name_str": "작업",  # 기본 작업 명칭 문자열
    },
}


class ProgressTracker:
    """
    배치 작업의 실시간 진행률(Progress) 추적 및 설정 % 배수 마일스톤 경고 로깅을 수행하는 공용 유틸리티 클래스입니다.
    """

    # 설정 파일 자동 생성·보정 시 기록할 이 클래스의 기본 설정 스키마
    DEFAULT_SCHEMA_DICT: dict[str, Any] = APP_DEFAULT_SCHEMA_DICT

    def __init__(
        self,
        total_items_int: int,
        logger_obj: Any = None,
        task_name_str: Optional[str] = None,
        start_time_float: Optional[float] = None,
    ):
        """
        ProgressTracker 객체를 초기화합니다.
        진행률 마일스톤 간격 및 기본 작업 명칭은 config.progress_tracker 설정을 직접 참조합니다.

        :param total_items_int: 전체 처리 대상 총 건수
        :param logger_obj: ProjectLogger 또는 logging.Logger 객체
        :param task_name_str: 작업 명칭 (로그 접두사 및 요약 제목용, 미지정 시 config의 default_task_name_str 적용)
        :param start_time_float: 작업 시작 타임스탬프 (미지정 시 현재 시간)
        :return: None
        :raises None: 예외를 발생시키지 않음
        """
        self.total_items_int: int = max(0, total_items_int)
        self.logger_obj: Any = logger_obj
        self.task_name_str: str = task_name_str or str(config.progress_tracker.default_task_name_str)
        self.start_time_float: float = start_time_float if start_time_float is not None else time.time()
        # 시작 일시 포맷팅 (YYYY-MM-DD HH:MM:SS)
        now_dt_obj: datetime = datetime.now(TimeUtils.resolve_timezone())
        self.start_datetime_str: str = now_dt_obj.strftime("%Y-%m-%d %H:%M:%S")

        self.current_count_int: int = 0
        self.total_bytes_int: int = 0
        self._last_warn_milestone_int: int = 0

    def update(
        self,
        count_int: int = 1,
        bytes_int: int = 0,
        details_str: str = "",
    ) -> None:
        """
        단일 또는 배치 아이템 처리 시 호출하여 진행상황 카운트를 갱신하고 레벨별 차등 로깅을 수행합니다.
        (일반 진행률: INFO 레벨, 지정 % 배수 마일스톤 및 완료 시점: WARNING 레벨)

        :param count_int: 처리 진행 건수 (기본값: 1)
        :param bytes_int: 처리/전송된 데이터 바이트 수 (옵션)
        :param details_str: 추가 세부 정보 문자열 (옵션)
        :return: None
        :raises None: 예외를 발생시키지 않음
        """
        self.current_count_int += max(1, count_int)
        if bytes_int > 0:
            self.total_bytes_int += bytes_int

        divisor_int: int = max(1, self.total_items_int)
        current_percent_float: float = (self.current_count_int / divisor_int) * 100.0
        current_percent_int: int = int(current_percent_float)

        interval_pct_int: int = int(config.progress_tracker.interval_percent_int)

        # 지정된 interval_percent(예: 10%)의 배수 도달 여부 판별
        is_warn_milestone_bool: bool = (
            (current_percent_int >= self._last_warn_milestone_int + interval_pct_int)
            or (self.total_items_int > 0 and self.current_count_int >= self.total_items_int)
        )

        elapsed_seconds_float: float = max(0.001, time.time() - self.start_time_float)
        items_per_second_float: float = self.current_count_int / elapsed_seconds_float
        bytes_per_second_float: float = self.total_bytes_int / elapsed_seconds_float

        remaining_items_int: int = max(0, self.total_items_int - self.current_count_int)
        eta_seconds_float: float = (
            remaining_items_int / items_per_second_float
            if items_per_second_float > 0
            else 0.0
        )

        speed_mb_str: str = f"{bytes_per_second_float / (1024 * 1024):.2f} MB/s" if self.total_bytes_int > 0 else ""
        eta_str: str = f"{int(eta_seconds_float // 60)}m {int(eta_seconds_float % 60)}s"

        if is_warn_milestone_bool:
            self._last_warn_milestone_int = (current_percent_int // interval_pct_int) * interval_pct_int
            if self.logger_obj:
                msg_str = (
                    f"[{self.task_name_str} 진행률 마일스톤] "
                    f"진행: {self.current_count_int:,}/{self.total_items_int:,} ({current_percent_int}%) | "
                    f"속도: {items_per_second_float:.1f}건/s {speed_mb_str} | 남은시간(ETA): {eta_str}"
                )
                if details_str:
                    msg_str += f" | {details_str}"
                self.logger_obj.warning(msg_str)
        else:
            if self.logger_obj:
                msg_str = (
                    f"[{self.task_name_str}] {self.current_count_int:,}/{self.total_items_int:,} ({current_percent_int}%) | "
                    f"{items_per_second_float:.1f}건/s"
                )
                if speed_mb_str:
                    msg_str += f" ({speed_mb_str})"
                if details_str:
                    msg_str += f" | {details_str}"
                self.logger_obj.info(msg_str)


__all__ = [
    "APP_DEFAULT_SCHEMA_DICT",
    "ProgressTracker",
]
