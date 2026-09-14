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
from agent_common.config_loader import config

# ==============================================================================
# 유틸리티 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "table_formatter": {
        "min_center_width_int": 5,        # 마크다운 :---: 중앙 정렬 최소 너비
        "min_default_width_int": 4,       # 마크다운 :--- 좌/우 정렬 최소 너비
        "center_colon_padding_int": 2,    # 마크다운 중앙 정렬 양쪽 콜론 수량
        "default_colon_padding_int": 1,   # 마크다운 좌/우 정렬 콜론 수량
    },
    "progress_tracker": {
        "interval_percent_int": 10,       # 진행률 마일스톤 기본 간격 (%)
        "default_task_name_str": "작업",  # 기본 작업 명칭 문자열
    },
}



class ProgressTracker:
    """
    배치 작업의 실시간 진행률(Progress) 추적, 설정 % 배수 마일스톤 판별 및 최종 결과 요약(Summary Report)을 출력하는 공용 유틸리티 클래스입니다.
    """

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
        self.logger: Any = logger_obj
        self.task_name_str: str = task_name_str or str(config.progress_tracker.default_task_name_str)
        self.start_time_float: float = start_time_float if start_time_float is not None else time.time()
        self.start_datetime_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ_STR)

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

        elapsed_float: float = time.time() - self.start_time_float
        progress_msg_str: str = (
            f"[{self.task_name_str} 진행상황] {self.current_count_int:,} / {self.total_items_int:,} 건 ({current_percent_float:.1f}%) "
            f"| 경과: {elapsed_float:.1f}s"
        )
        if details_str:
            progress_msg_str = f"{progress_msg_str} | {details_str}"

        if self.logger:
            if is_warn_milestone_bool:
                self._last_warn_milestone_int = (current_percent_int // interval_pct_int) * interval_pct_int
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
        :return: None
        :raises None: 예외를 발생시키지 않음
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


class TableFormatter:
    """
    모노스페이스 폰트(터미널, 콘솔, Airflow 로그) 및 마크다운 렌더러에서
    한글(전각)과 영문(반각)의 표시 폭(Display Width) 차이를 정밀 계산하여
    세로줄(|)이 완벽히 일치하도록 자동 맞춤 패딩하는 공용 테이블 포매터 유틸리티 클래스입니다.
    """

    @staticmethod
    def calculate_display_width(text_str: str) -> int:
        """
        문자열이 콘솔(모노스페이스 폰트)에서 차지하는 실제 표시 너비(Display Width)를 정밀 계산합니다.
        - 한글 음절, CJK 한자, 전각 기호: 2칸
        - 영문, 숫자, ASCII 기호, 박스 드로잉 트리 기호(├, ─, │, └): 1칸

        :param text_str: 표시 너비를 계산할 대상 문자열
        :return: 실제 화면 표시 너비 정수값
        :raises None: 예외를 발생시키지 않음
        """
        import unicodedata

        width_int: int = 0
        for char_str in text_str:
            east_asian_width_str: str = unicodedata.east_asian_width(char_str)
            if east_asian_width_str in ("W", "F"):
                width_int += 2
            elif east_asian_width_str == "A" and 0x2500 <= ord(char_str) <= 0x257F:
                width_int += 1
            else:
                width_int += 1
        return width_int

    @classmethod
    def format_markdown_table(
        cls,
        headers_list: list[str],
        rows_list: list[list[str]],
        alignments_list: Optional[list[str]] = None,
    ) -> list[str]:
        """
        헤더와 행 데이터 목록을 받아 각 열(Column)의 최대 표시 너비에 맞춰
        정렬 방향별 공백 패딩을 적용한 마크다운 테이블 행 문자열 리스트를 생성합니다.

        :param headers_list: 테이블 헤더 열 레이블 리스트
        :param rows_list: 데이터 행별 셀 문자열 리스트
        :param alignments_list: 각 열별 정렬 방식 리스트 ('left' / ':---', 'center' / ':---:', 'right' / '---:'). 미지정 시 전체 'left'
        :return: 세로줄(|) 정렬이 완료된 마크다운 테이블 행 문자열 리스트
        :raises None: 예외를 발생시키지 않음
        """
        columns_count_int: int = len(headers_list)
        if columns_count_int == 0:
            return []

        # 설정에서 테이블 포매터 너비 및 패딩 파라미터 직참조 (AGENTS.md 1.4.2)
        min_center_width_int: int = config.table_formatter.min_center_width_int
        min_default_width_int: int = config.table_formatter.min_default_width_int
        center_colon_padding_int: int = config.table_formatter.center_colon_padding_int
        default_colon_padding_int: int = config.table_formatter.default_colon_padding_int

        # 열별 정렬 표준화 ('left', 'center', 'right')
        normalized_alignments_list: list[str] = []
        for col_idx_int in range(columns_count_int):
            if alignments_list and col_idx_int < len(alignments_list):
                align_str: str = alignments_list[col_idx_int].strip()
                if align_str in (":---:", "center"):
                    normalized_alignments_list.append("center")
                elif align_str in ("---:", ":--:", "right"):
                    normalized_alignments_list.append("right")
                else:
                    normalized_alignments_list.append("left")
            else:
                normalized_alignments_list.append("left")

        # 각 열의 최대 표시 너비 계산 (최소 너비: center는 min_center_width_int, left/right는 min_default_width_int)
        col_widths_list: list[int] = []
        for col_idx_int in range(columns_count_int):
            header_str: str = headers_list[col_idx_int]
            min_required_width_int: int = (
                min_center_width_int
                if normalized_alignments_list[col_idx_int] == "center"
                else min_default_width_int
            )
            max_width_int: int = max(cls.calculate_display_width(header_str), min_required_width_int)
            for row_items_list in rows_list:
                if col_idx_int < len(row_items_list):
                    cell_text_str: str = row_items_list[col_idx_int]
                    max_width_int = max(max_width_int, cls.calculate_display_width(cell_text_str))
            col_widths_list.append(max_width_int)

        # 1. 헤더 행 서식화
        header_cells_list: list[str] = []
        for col_idx_int in range(columns_count_int):
            header_str = headers_list[col_idx_int]
            col_width_int: int = col_widths_list[col_idx_int]
            align_mode_str: str = normalized_alignments_list[col_idx_int]
            header_cells_list.append(cls._pad_cell(header_str, col_width_int, align_mode_str))
        header_row_str: str = "| " + " | ".join(header_cells_list) + " |"

        # 2. 구분선 행 서식화
        separator_cells_list: list[str] = []
        for col_idx_int in range(columns_count_int):
            col_width_int = col_widths_list[col_idx_int]
            align_mode_str = normalized_alignments_list[col_idx_int]
            if align_mode_str == "center":
                separator_cells_list.append(":" + "-" * (col_width_int - center_colon_padding_int) + ":")
            elif align_mode_str == "right":
                separator_cells_list.append("-" * (col_width_int - default_colon_padding_int) + ":")
            else:
                separator_cells_list.append(":" + "-" * (col_width_int - default_colon_padding_int))
        separator_row_str: str = "| " + " | ".join(separator_cells_list) + " |"

        # 3. 데이터 행 서식화
        result_rows_list: list[str] = [header_row_str, separator_row_str]
        for row_items_list in rows_list:
            row_cells_list: list[str] = []
            for col_idx_int in range(columns_count_int):
                cell_text_str = row_items_list[col_idx_int] if col_idx_int < len(row_items_list) else ""
                col_width_int = col_widths_list[col_idx_int]
                align_mode_str = normalized_alignments_list[col_idx_int]
                row_cells_list.append(cls._pad_cell(cell_text_str, col_width_int, align_mode_str))
            result_rows_list.append("| " + " | ".join(row_cells_list) + " |")

        return result_rows_list

    @classmethod
    def _pad_cell(cls, cell_text_str: str, target_width_int: int, align_mode_str: str) -> str:
        """
        셀 텍스트를 목표 표시 너비에 맞춰 지정된 정렬 모드로 공백 패딩합니다.

        :param cell_text_str: 패딩 대상 셀 문자열
        :param target_width_int: 목표 표시 너비
        :param align_mode_str: 정렬 방식 ('left', 'center', 'right')
        :return: 패딩이 완료된 셀 문자열
        :raises None: 예외를 발생시키지 않음
        """
        current_width_int: int = cls.calculate_display_width(cell_text_str)
        padding_spaces_int: int = max(0, target_width_int - current_width_int)

        if align_mode_str == "center":
            left_spaces_int: int = padding_spaces_int // 2
            right_spaces_int: int = padding_spaces_int - left_spaces_int
            return " " * left_spaces_int + cell_text_str + " " * right_spaces_int
        elif align_mode_str == "right":
            return " " * padding_spaces_int + cell_text_str
        else:
            return cell_text_str + " " * padding_spaces_int


__all__ = [
    "APP_DEFAULT_SCHEMA_DICT",
    "DateTimeUtils",
    "ProgressTracker",
    "TableFormatter",
]
