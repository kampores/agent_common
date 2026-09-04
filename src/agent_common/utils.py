# 작성일: 2026-08-16
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
프로젝트 전역에서 공통으로 사용하는 런타임 진행률 추적(ProgressTracker) 및 모니터링 유틸리티 모듈입니다.
"""

from __future__ import annotations

import time
from typing import Any, Optional

# DateTimeUtils 도구 클래스 임포트 및 하위 호환성 노출
from agent_common.tool.date.date_time_utils import DateTimeUtils


class ProgressTracker:
    """
    배치 작업의 실시간 진행률(Progress) 추적, 설정 % 배수 마일스톤 판별 및 최종 결과 요약(Summary Report)을 출력하는 공용 유틸리티 클래스입니다.
    """

    def __init__(
        self,
        total_items_int: int,
        interval_percent_int: int = 10,
        logger: Any = None,
        task_name_str: str = "작업",
        start_time_float: Optional[float] = None,
    ):
        """
        ProgressTracker 객체를 초기화합니다.

        :param total_items_int: 전체 처리 대상 총 건수
        :param interval_percent_int: WARNING 레벨로 승격 출력할 진행률 간격 (% 단위, 기본값: 10)
        :param logger: ProjectLogger 또는 logging.Logger 객체
        :param task_name_str: 작업 명칭 (로그 접두사 및 요약 제목용)
        :param start_time_float: 작업 시작 타임스탬프 (미지정 시 현재 시간)
        """
        self.total_items_int: int = max(0, total_items_int)
        self.interval_percent_int: int = max(1, min(100, interval_percent_int))
        self.logger: Any = logger
        self.task_name_str: str = task_name_str
        self.start_time_float: float = start_time_float if start_time_float is not None else time.time()
        self.start_datetime_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ)

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
        """
        self.current_count_int += max(1, count_int)
        if bytes_int > 0:
            self.total_bytes_int += bytes_int

        divisor_int: int = max(1, self.total_items_int)
        current_percent_float: float = (self.current_count_int / divisor_int) * 100.0
        current_percent_int: int = int(current_percent_float)

        # 지정된 interval_percent(예: 10%)의 배수 도달 여부 판별
        is_warn_milestone_bool: bool = (
            (current_percent_int >= self._last_warn_milestone_int + self.interval_percent_int)
            or (self.total_items_int > 0 and self.current_count_int >= self.total_items_int)
        )

        elapsed_float: float = time.time() - self.start_time_float
        progress_msg_str: str = (
            f"[{self.task_name_str} 진행상황] {self.current_count_int:,} / {self.total_items_int:,} 건 ({current_percent_float:.1f}%) "
            f"| 경과: {elapsed_float:.1f}s"
        )
        if details_str:
            progress_msg_str = f"{progress_msg_str} | {details_str}"

        if self.logger:
            if is_warn_milestone_bool:
                self._last_warn_milestone_int = (current_percent_int // self.interval_percent_int) * self.interval_percent_int
                self.logger.warning("progress_milestone", message=progress_msg_str)
            else:
                self.logger.info("progress_update", message=progress_msg_str)

    def log_summary(
        self,
        extra_lines_list: Optional[list[str]] = None,
        error_counts_dict: Optional[dict[str, int]] = None,
        excluded_counts_dict: Optional[dict[str, int]] = None,
    ) -> None:
        """
        작업 종료 시 로거(ProjectLogger)에 위임하여 최종 처리 결과 요약 리포트(Summary Report)를 출력합니다.

        :param extra_lines_list: 요약 블록에 추가할 커스텀 상세 정보 행 리스트 (옵션)
        :param error_counts_dict: 에러 코드별 발생 건수 딕셔너리 (옵션)
        :param excluded_counts_dict: 제외 코드별 발생 건수 딕셔너리 (옵션)
        """
        if self.logger and hasattr(self.logger, "log_summary"):
            self.logger.log_summary(
                tracker_obj=self,
                extra_lines_list=extra_lines_list,
                error_counts_dict=error_counts_dict,
                excluded_counts_dict=excluded_counts_dict,
            )
        elif self.logger:
            from agent_common.logger import ProjectLogger
            temp_logger = ProjectLogger(getattr(self.logger, "name", "ProgressTracker"))
            temp_logger.log_summary(
                tracker_obj=self,
                extra_lines_list=extra_lines_list,
                error_counts_dict=error_counts_dict,
                excluded_counts_dict=excluded_counts_dict,
            )
        else:
            elapsed_float: float = time.time() - self.start_time_float
            print(f"[{self.task_name_str} 작업 완료] 총 {self.total_items_int:,}건 중 {self.current_count_int:,}건 진행 (소요: {elapsed_float:.2f}초)")


__all__ = [
    "DateTimeUtils",
    "ProgressTracker",
]
