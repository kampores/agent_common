# 작성일: 2026-08-16
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

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
        self.total_items_int: int = max(1, total_items_int)
        self.interval_percent_int: int = max(1, min(100, interval_percent_int))
        self.logger: Any = logger
        self.task_name_str: str = task_name_str
        self.start_time_float: float = start_time_float if start_time_float is not None else time.time()
        self.start_datetime_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ)

        self.current_count_int: int = 0
        self.success_count_int: int = 0
        self.failure_count_int: int = 0
        self.excluded_count_int: int = 0
        self.total_bytes_int: int = 0
        self._last_warn_milestone_int: int = 0

    def update(
        self,
        success_bool: bool = True,
        excluded_bool: bool = False,
        bytes_int: int = 0,
        details_str: str = "",
    ) -> None:
        """
        단일 아이템 처리 완료 시 호출하여 카운트를 갱신하고 레벨별 차등 로깅을 수행합니다.
        (일반 진행률: INFO 레벨, 지정 % 배수 마일스톤 및 완료 시점: WARNING 레벨)

        :param success_bool: 성공 여부
        :param excluded_bool: 제외 대상 여부 (예: 자산상태코드 09 등)
        :param bytes_int: 처리/전송된 데이터 바이트 수
        :param details_str: 추가 세부 정보 문자열 (옵션)
        """
        self.current_count_int += 1
        if excluded_bool:
            self.excluded_count_int += 1
        elif success_bool:
            self.success_count_int += 1
        else:
            self.failure_count_int += 1

        if bytes_int > 0:
            self.total_bytes_int += bytes_int

        current_percent_float: float = (self.current_count_int / self.total_items_int) * 100.0
        current_percent_int: int = int(current_percent_float)

        # 지정된 interval_percent(예: 10%)의 배수 도달 여부 판별
        is_warn_milestone_bool: bool = (
            (current_percent_int >= self._last_warn_milestone_int + self.interval_percent_int)
            or (self.current_count_int >= self.total_items_int)
        )

        elapsed_float: float = time.time() - self.start_time_float
        progress_msg_str: str = (
            f"[{self.task_name_str} 진행상황] {self.current_count_int:,} / {self.total_items_int:,} 건 ({current_percent_float:.1f}%) "
            f"- 성공: {self.success_count_int:,}, 실패: {self.failure_count_int:,}, 제외: {self.excluded_count_int:,} "
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

    def log_summary(self, extra_lines_list: Optional[list[str]] = None) -> None:
        """
        작업 종료 시 최종 처리 결과 요약 리포트(Summary Report) 블록을 WARNING 레벨로 출력합니다.

        :param extra_lines_list: 요약 블록에 추가할 커스텀 상세 정보 행 리스트 (옵션)
        """
        elapsed_float: float = time.time() - self.start_time_float
        end_datetime_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ)

        mins_int: int = int(elapsed_float // 60)
        secs_float: float = elapsed_float % 60
        time_display_str: str = f"{mins_int}분 {secs_float:.1f}초 ({elapsed_float:.2f}초)" if mins_int > 0 else f"{elapsed_float:.2f}초"

        lines_list: list[str] = [
            "=" * 80,
            f"                    [{self.task_name_str} 작업 결과 요약]",
            "=" * 80,
            f"- 작업 시작 / 종료 시간 : {self.start_datetime_str} ~ {end_datetime_str}",
            f"- 총 소요 시간          : {time_display_str}",
            "-" * 80,
            f"- 총 처리 대상 건수     : {self.total_items_int:,} 건",
            f"- 처리 성공 / 실패      : {self.success_count_int:,} 건 / {self.failure_count_int:,} 건",
            f"- 처리 제외 (Skip)      : {self.excluded_count_int:,} 건",
        ]

        if self.total_bytes_int > 0:
            mb_val_float: float = self.total_bytes_int / (1024 * 1024)
            mb_rate_float: float = mb_val_float / max(0.001, elapsed_float)
            lines_list.append(f"- 총 전송 데이터 용량   : {mb_val_float:.2f} MB (평균 {mb_rate_float:.2f} MB/s)")

        rate_float: float = self.current_count_int / max(0.001, elapsed_float)
        lines_list.append(f"- 평균 처리 속도        : {rate_float:.2f} items/sec")

        if extra_lines_list:
            lines_list.append("-" * 80)
            for line_str in extra_lines_list:
                lines_list.append(f"- {line_str}" if not line_str.startswith("-") else line_str)

        lines_list.append("=" * 80)

        summary_block_str: str = "\n" + "\n".join(lines_list)
        if self.logger:
            self.logger.warning("execution_summary_report", summary=summary_block_str)
        else:
            print(summary_block_str)


__all__ = [
    "DateTimeUtils",
    "ProgressTracker",
]
