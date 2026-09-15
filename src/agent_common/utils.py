# 작성일: 2026-08-16
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
프로젝트 전역에서 공통으로 사용하는 런타임 진행률 추적(ProgressTracker),
시스템 및 세계 표준 타임존 해석(TimeUtils) 및 모니터링 유틸리티 모듈입니다.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

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


class TimeUtils:
    """
    호스트 시스템(OS/컨테이너) 로컬 타임존 동적 감지, 환경변수 설정 타임존,
    그리고 전 세계 표준 타임존 해석 및 datetime 객체 생성을 전담하는 코어 시간 인프라 유틸리티 클래스입니다.
    """

    # 전 세계 주요 표준 타임존 약어 및 UTC 기준 오프셋 시간 매핑 딕셔너리
    WORLD_TIMEZONE_OFFSETS_DICT: dict[str, int | float] = {
        # UTC 및 표준시
        "UTC": 0,
        "GMT": 0,
        "Z": 0,
        # 아시아 / 태평양
        "KST": 9,        # 한국 표준시 (UTC+9)
        "JST": 9,        # 일본 표준시 (UTC+9)
        "CST_ASIA": 8,   # 중국 표준시 (UTC+8, 베이징/상하이)
        "HKT": 8,        # 홍콩 표준시 (UTC+8)
        "SGT": 8,        # 싱가포르 표준시 (UTC+8)
        "IST": 5.5,      # 인도 표준시 (UTC+5:30)
        "ICT": 7,        # 인도차이나 표준시 (UTC+7, 방콕/하노이)
        "AEST": 10,      # 호주 동부 표준시 (UTC+10)
        "AEDT": 11,      # 호주 동부 서머타임 (UTC+11)
        "ACST": 9.5,     # 호주 중부 표준시 (UTC+9:30)
        "ACDT": 10.5,    # 호주 중부 서머타임 (UTC+10:30)
        "AWST": 8,       # 호주 서부 표준시 (UTC+8)
        "NZST": 12,      # 뉴질랜드 표준시 (UTC+12)
        "NZDT": 13,      # 뉴질랜드 서머타임 (UTC+13)
        # 유럽
        "CET": 1,        # 중앙유럽 표준시 (UTC+1)
        "CEST": 2,       # 중앙유럽 서머타임 (UTC+2)
        "WET": 0,        # 서유럽 표준시 (UTC+0)
        "WEST": 1,       # 서유럽 서머타임 (UTC+1)
        "EET": 2,        # 동유럽 표준시 (UTC+2)
        "EEST": 3,       # 동유럽 서머타임 (UTC+3)
        "BST": 1,        # 영국 서머타임 (UTC+1)
        "MSK": 3,        # 모스크바 표준시 (UTC+3)
        # 북미 (미국 / 캐나다)
        "EST": -5,       # 미국 동부 표준시 (UTC-5)
        "EDT": -4,       # 미국 동부 서머타임 (UTC-4)
        "CST": -6,       # 미국 중부 표준시 (UTC-6)
        "CDT": -5,       # 미국 중부 서머타임 (UTC-5)
        "MST": -7,       # 미국 산악 표준시 (UTC-7)
        "MDT": -6,       # 미국 산악 서머타임 (UTC-6)
        "PST": -8,       # 미국 태평양 표준시 (UTC-8)
        "PDT": -7,       # 미국 태평양 서머타임 (UTC-7)
        "AKST": -9,      # 알래스카 표준시 (UTC-9)
        "AKDT": -8,      # 알래스카 서머타임 (UTC-8)
        "HST": -10,      # 하와이 표준시 (UTC-10)
    }

    @classmethod
    def get_system_timezone(cls) -> timezone:
        """
        현재 코드가 실행 중인 OS/컨테이너 호스트 시스템의 실제 로컬 타임존 객체를 동적으로 감지하여 반환합니다.
        (배치 서버: KST, Airflow 파드: UTC 등 실행 환경에 맞는 실제 로컬 타임존 반영)

        :return: 호스트 시스템 로컬 타임존을 나타내는 timezone 객체 (감지 불가 시 timezone.utc)
        """
        local_datetime_obj: datetime = datetime.now().astimezone()
        local_offset_delta_obj: Optional[timedelta] = local_datetime_obj.utcoffset()
        if local_offset_delta_obj is not None:
            return timezone(local_offset_delta_obj)
        return timezone.utc

    @classmethod
    def get_system_timezone_offset_str(cls) -> str:
        """
        현재 호스트 시스템의 로컬 타임존 오프셋을 ISO 8601 콜론 형식('+09:00', '+00:00', '-05:00' 등)으로 반환합니다.

        :return: ISO 8601 형식의 시스템 타임존 오프셋 문자열
        """
        local_datetime_obj: datetime = datetime.now().astimezone()
        return cls.format_timezone_offset(local_datetime_obj)

    @classmethod
    def resolve_timezone(cls, tz_input_any: Optional[timezone | str | int | float] = None) -> timezone:
        """
        지정된 타임존 입력값(None, timezone 객체, 세계시간 약어 문자열, ISO 오프셋 문자열, 수치형 오프셋)을
        표준 timezone 객체로 해석하여 반환합니다.
        입력값이 None인 경우 업계/플랫폼 표준 환경변수(TZ)를 확인하고,
        환경변수 미지정 시 호스트 시스템의 로컬 타임존(get_system_timezone)을 자동 감지합니다.

        :param tz_input_any: 해석 대상 타임존 (None, timezone, str, int, float)
        :return: 해석 완료된 표준 timezone 객체
        :raises ValueError: 지원하지 않거나 유효하지 않은 타임존 형식 유입 시 발생
        """
        if tz_input_any is None:
            tz_env_str: Optional[str] = os.environ.get("TZ")
            if tz_env_str and tz_env_str.strip():
                return cls.resolve_timezone(tz_env_str.strip())
            return cls.get_system_timezone()

        if isinstance(tz_input_any, timezone):
            return tz_input_any

        if isinstance(tz_input_any, (int, float)):
            hours_int: int = int(tz_input_any)
            minutes_int: int = int(round((tz_input_any - hours_int) * 60))
            return timezone(timedelta(hours=hours_int, minutes=minutes_int))

        if isinstance(tz_input_any, str):
            clean_str: str = tz_input_any.strip()
            upper_str: str = clean_str.upper()

            if upper_str in ("SYSTEM", "LOCAL", "AUTO"):
                return cls.get_system_timezone()

            if upper_str in cls.WORLD_TIMEZONE_OFFSETS_DICT:
                offset_val = cls.WORLD_TIMEZONE_OFFSETS_DICT[upper_str]
                return cls.resolve_timezone(offset_val)

            sign_int: int = -1 if clean_str.startswith("-") else 1
            pure_digits_str: str = clean_str.replace(":", "").lstrip("+-")
            if pure_digits_str.isdigit():
                if len(pure_digits_str) <= 2:
                    return timezone(timedelta(hours=sign_int * int(pure_digits_str)))
                elif len(pure_digits_str) == 4:
                    parsed_hours_int: int = int(pure_digits_str[:2])
                    parsed_minutes_int: int = int(pure_digits_str[2:])
                    return timezone(timedelta(hours=sign_int * parsed_hours_int, minutes=sign_int * parsed_minutes_int))

            raise ValueError(f"유효하지 않은 타임존 오프셋 또는 규격 형식입니다: '{tz_input_any}'")

        raise ValueError(f"지원하지 않는 타임존 입력 타입입니다: {type(tz_input_any)}")

    @classmethod
    def format_timezone_offset(cls, dt_obj: datetime) -> str:
        """
        datetime 객체의 타임존 오프셋을 '+09:00', '-05:00', '+00:00' 형태의 표준 ISO 8601 콜론 구분 문자열로 반환합니다.

        :param dt_obj: 타임존 오프셋을 추출할 datetime 객체
        :return: '+HH:MM' 또는 '-HH:MM' 형태의 타임존 오프셋 문자열
        """
        offset_raw_str: str = dt_obj.strftime("%z")
        if len(offset_raw_str) == 5 and offset_raw_str[0] in "+-":
            return f"{offset_raw_str[:3]}:{offset_raw_str[3:]}"
        return "+00:00"

    @classmethod
    def parse_datetime(cls, dt_input_any: Any, default_tz_obj: Optional[timezone] = None) -> Optional[datetime]:
        """
        다양한 형태(datetime 객체, ISO 8601 일시 문자열, naive/aware 등)의 일시 값을 표준 비교 및 연산이 가능한
        timezone-aware datetime 객체로 정규화하여 반환합니다.
        문자열 끝의 'Z'는 '+00:00'(UTC)으로 변환되며, 타임존 오프셋이 누락된 naive datetime의 경우
        지정된 default_tz_obj(미지정 시 cls.resolve_timezone() 기본 타임존)를 부여합니다.

        :param dt_input_any: 파싱 및 정규화할 일시 객체 또는 문자열 (None 시 None 반환)
        :param default_tz_obj: naive datetime에 적용할 기본 timezone 객체 (미지정 시 자동 감지)
        :return: 정규화된 timezone-aware datetime 객체 (변환 실패 또는 빈 값일 경우 None)
        :raises None: 파싱 중 발생하는 형식 오류는 None으로 안전하게 처리
        """
        if dt_input_any is None:
            return None

        effective_tz_obj: timezone = default_tz_obj if default_tz_obj is not None else cls.resolve_timezone()

        if isinstance(dt_input_any, datetime):
            if dt_input_any.tzinfo is not None:
                return dt_input_any
            return dt_input_any.replace(tzinfo=effective_tz_obj)

        dt_str: str = str(dt_input_any).strip()
        if not dt_str or dt_str.lower() in ("none", "null", ""):
            return None

        clean_dt_str: str = dt_str.replace("Z", "+00:00")
        try:
            parsed_dt_obj: datetime = datetime.fromisoformat(clean_dt_str)
            if parsed_dt_obj.tzinfo is None:
                parsed_dt_obj = parsed_dt_obj.replace(tzinfo=effective_tz_obj)
            return parsed_dt_obj
        except (ValueError, TypeError):
            return None



class ProgressTracker:
    """
    배치 작업의 실시간 진행률(Progress) 추적 및 설정 % 배수 마일스톤 경고 로깅을 수행하는 공용 유틸리티 클래스입니다.
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


class TableFormatter:
    """
    모노스페이스 콘솔 및 마크다운 테이블에서 한글/한자 등 전각 문자의 2칸 표시 폭을
    정밀 계산하여 표 세로줄 컬럼 너비를 칼같이 맞춰주는 공용 테이블 포매터 유틸리티 클래스입니다.
    """

    @classmethod
    def calculate_display_width(cls, text_str: str) -> int:
        """
        문자열이 터미널/마크다운 뷰어에 표시될 때 차지하는 실제 시각적 컬럼 폭(Display Width)을 계산합니다.
        (ASCII 및 서유럽 반각 문자: 1칸, CJK 한글/한자/전각 기호: 2칸)

        :param text_str: 측정할 문자열
        :return: 시각적 셀 너비(칸 수)
        :raises None: 예외를 발생시키지 않음
        """
        import unicodedata
        total_width_int: int = 0
        for char_str in str(text_str):
            char_width_type_str: str = unicodedata.east_asian_width(char_str)
            # 'W'(Wide), 'F'(Fullwidth) 문자는 2칸 차지, 그 외(Narrow, Halfwidth, Neutral, Ambiguous)는 1칸
            if char_width_type_str in ("W", "F"):
                total_width_int += 2
            else:
                total_width_int += 1
        return total_width_int

    @classmethod
    def format_row(
        cls,
        cells_list: list[str],
        col_widths_list: list[int],
        alignments_list: Optional[list[str]] = None,
    ) -> str:
        """
        한 행(Row)의 셀 리스트와 목표 컬럼 너비 리스트를 전달받아
        정확한 공백 패딩을 적용한 마크다운 테이블 행 문자열('| cell1 | cell2 |')을 조립합니다.

        :param cells_list: 출력할 각 셀의 텍스트 리스트
        :param col_widths_list: 각 컬럼별 목표 시각적 표시 너비 리스트
        :param alignments_list: 각 컬럼별 정렬 방식 리스트 ('left', 'center', 'right', 미지정 시 전체 'left')
        :return: 정렬된 마크다운 테이블 행 문자열
        :raises None: 예외를 발생시키지 않음
        """
        aligned_cells_list: list[str] = []
        col_count_int: int = len(col_widths_list)

        for i in range(col_count_int):
            cell_str: str = cells_list[i] if i < len(cells_list) else ""
            width_int: int = col_widths_list[i]
            align_mode_str: str = alignments_list[i] if alignments_list and i < len(alignments_list) else "left"

            aligned_cell_str: str = cls.pad_cell(cell_str, width_int, align_mode_str)
            aligned_cells_list.append(aligned_cell_str)

        return "| " + " | ".join(aligned_cells_list) + " |"

    @classmethod
    def format_separator(
        cls,
        col_widths_list: list[int],
        alignments_list: Optional[list[str]] = None,
    ) -> str:
        """
        컬럼 너비 및 정렬 방식에 부합하는 마크다운 헤더 구분선('| :--- | :---: | ---: |')을 생성합니다.

        :param col_widths_list: 각 컬럼별 목표 시각적 표시 너비 리스트
        :param alignments_list: 각 컬럼별 정렬 방식 리스트
        :return: 마크다운 헤더 구분선 문자열
        :raises None: 예외를 발생시키지 않음
        """
        sep_parts_list: list[str] = []
        for i, width_int in enumerate(col_widths_list):
            align_mode_str: str = alignments_list[i] if alignments_list and i < len(alignments_list) else "left"
            if align_mode_str == "center":
                dashes_count_int: int = max(config.table_formatter.min_center_width_int, width_int)
                sep_parts_list.append(":" + "-" * (dashes_count_int - config.table_formatter.center_colon_padding_int) + ":")
            elif align_mode_str == "right":
                dashes_count_int = max(config.table_formatter.min_default_width_int, width_int)
                sep_parts_list.append("-" * (dashes_count_int - config.table_formatter.default_colon_padding_int) + ":")
            else:
                dashes_count_int = max(config.table_formatter.min_default_width_int, width_int)
                sep_parts_list.append(":" + "-" * (dashes_count_int - config.table_formatter.default_colon_padding_int))

        return "| " + " | ".join(sep_parts_list) + " |"

    @classmethod
    def pad_cell(
        cls,
        cell_text_str: str,
        target_width_int: int,
        align_mode_str: str = "left",
    ) -> str:
        """
        개별 셀 텍스트의 시각적 너비를 계산하여 목표 너비에 맞게 공백을 채워 넣습니다.

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
                config.table_formatter.min_center_width_int
                if normalized_alignments_list[col_idx_int] == "center"
                else config.table_formatter.min_default_width_int
            )
            max_width_int: int = max(cls.calculate_display_width(header_str), min_required_width_int)
            for row_items_list in rows_list:
                if col_idx_int < len(row_items_list):
                    cell_text_str: str = row_items_list[col_idx_int]
                    max_width_int = max(max_width_int, cls.calculate_display_width(cell_text_str))
            col_widths_list.append(max_width_int)

        header_row_str: str = cls.format_row(headers_list, col_widths_list, normalized_alignments_list)
        separator_row_str: str = cls.format_separator(col_widths_list, normalized_alignments_list)

        result_rows_list: list[str] = [header_row_str, separator_row_str]
        for row_items_list in rows_list:
            result_rows_list.append(cls.format_row(row_items_list, col_widths_list, normalized_alignments_list))

        return result_rows_list


__all__ = [
    "APP_DEFAULT_SCHEMA_DICT",
    "TimeUtils",
    "ProgressTracker",
    "TableFormatter",
]
