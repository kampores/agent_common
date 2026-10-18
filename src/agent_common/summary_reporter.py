# 작성일: 2026-10-18
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
배치 작업의 실행 메트릭, 처리 통계(성공/실패/제외) 및 소요 시간을 바탕으로
다국어 지원 80열 표준 마크다운 요약 리포트(Summary Report)를 생성 및 출력하는 공용 리포터 유틸리티 모듈입니다.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from agent_common.config_loader import config
from agent_common.table_formatter import TableFormatter
from agent_common.tool.date.date_time_utils import DateTimeUtils

# ==============================================================================
# 요약 리포터 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "summary_reporter": {
        "default_task_name_str": "작업",
        "report_title_template_str": "[{task_name_str} 작업 결과 요약 표]",
        "table_header_division_str": "구분",
        "table_header_detail_str": "세부 항목",
        "table_header_value_str": "내용 / 수치",
        "table_header_note_str": "비고",
        "category_time_str": "실행 시간",
        "category_count_str": "처리 건수",
        "category_perf_str": "처리 성능",
        "category_detail_str": "상세 정보",
        "label_work_datetime_str": "작업 일시",
        "label_total_count_str": "전체 건수 (Total)",
        "label_success_count_str": "├─ 처리 성공",
        "label_failure_count_str": "├─ 처리 실패",
        "label_excluded_count_str": "└─ 처리 제외",
        "label_throughput_str": "평균 처리 속도",
        "label_total_bytes_str": "총 전송 데이터량",
        "note_total_formula_str": "전체 = 성공 + 실패 + 제외",
        "note_average_rate_template_str": "평균 {rate_float:.2f} MB/s",
        "unit_items_str": "건",
        "unit_items_per_sec_str": "items/sec",
        "unit_minutes_seconds_template_str": "{minutes_int}분 {seconds_float:.1f}초 ({elapsed_float:.2f}초)",
        "unit_seconds_template_str": "{elapsed_float:.2f}초",
        "section_error_detail_template_str": "- 예외/오류 발생 세부 내역 (총 {total_errors_int:,}건):",
        "section_excluded_detail_template_str": "- 처리 제외 세부 내역 (총 {total_excluded_items_int:,}건):",
        "unclassified_failure_str": "기타 미분류 실패",
        "unclassified_excluded_str": "기타 미분류 제외",
    }
}


class StandardSummaryReporter:
    """
    배치 작업의 실행 메트릭, 처리 통계(성공/실패/제외) 및 소요 시간을 바탕으로
    다국어 지원 80열 표준 마크다운 요약 리포트(Summary Report)를 생성 및 출력하는 공용 리포터 유틸리티 클래스입니다.
    """

    DEFAULT_SCHEMA_DICT: dict[str, Any] = APP_DEFAULT_SCHEMA_DICT

    def __init__(self, logger_obj: Any = None) -> None:
        """
        StandardSummaryReporter 객체를 초기화합니다.

        :param logger_obj: 리포트를 출력할 ProjectLogger 또는 logging.Logger 객체 (미지정 가능)
        """
        self.logger_obj: Any = logger_obj

    def build_summary_report(
        self,
        task_name_str: str = "",
        total_items_int: int = 0,
        success_count_int: int = 0,
        failure_count_int: int = 0,
        excluded_count_int: int = 0,
        start_time_float: Optional[float] = None,
        start_datetime_str: Optional[str] = None,
        total_bytes_int: int = 0,
        error_counts_dict: Optional[dict[str, int]] = None,
        excluded_counts_dict: Optional[dict[str, int]] = None,
        extra_lines_list: Optional[list[str]] = None,
        tracker_obj: Any = None,
        logger_obj: Any = None,
    ) -> str:
        """
        작업 실행 메트릭 또는 ProgressTracker 객체를 기반으로 최종 결과 요약 리포트(Summary Report) 문자열을 조립하여 반환합니다.

        :param task_name_str: 작업 명칭 (요약 리포트 제목용, 미지정 시 다국어 기본값 적용)
        :param total_items_int: 전체 처리 대상 건수
        :param success_count_int: 처리 성공 건수
        :param failure_count_int: 처리 실패 건수
        :param excluded_count_int: 처리 제외(Skip) 건수
        :param start_time_float: 작업 시작 타임스탬프 (미지정 시 현재 시간)
        :param start_datetime_str: 작업 시작 일시 문자열 (YYYY-MM-DD HH:MM:SS)
        :param total_bytes_int: 전송/처리된 총 바이트 수
        :param error_counts_dict: 에러 코드별 발생 건수 딕셔너리 (미지정 시 로거 자동 집계 사용)
        :param excluded_counts_dict: 제외 코드별 발생 건수 딕셔너리 (미지정 시 로거 자동 집계 사용)
        :param extra_lines_list: 요약 블록에 추가할 커스텀 상세 정보 행 리스트
        :param tracker_obj: 메트릭을 추출할 ProgressTracker 인스턴스 (지정 시 메트릭 인자 자동 추출)
        :param logger_obj: 통계 및 log_id_description을 조회할 로거 객체 (미지정 시 self.logger_obj 사용)
        :return: 80열 표준 마크다운 요약 리포트 텍스트 블록
        """
        eff_logger_obj: Any = logger_obj or self.logger_obj

        # 1. ProgressTracker 연동 시 메트릭 자동 추출
        if tracker_obj is not None:
            if not task_name_str and hasattr(tracker_obj, "task_name_str"):
                task_name_str = tracker_obj.task_name_str
            if total_items_int == 0 and hasattr(tracker_obj, "total_items_int"):
                total_items_int = tracker_obj.total_items_int
            if start_time_float is None and hasattr(tracker_obj, "start_time_float"):
                start_time_float = tracker_obj.start_time_float
            if start_datetime_str is None and hasattr(tracker_obj, "start_datetime_str"):
                start_datetime_str = tracker_obj.start_datetime_str
            if total_bytes_int == 0 and hasattr(tracker_obj, "total_bytes_int"):
                total_bytes_int = tracker_obj.total_bytes_int

        # 2. 로거 연동 시 누적 통계 자동 추출
        if eff_logger_obj is not None:
            if success_count_int == 0 and hasattr(eff_logger_obj, "success_count_int"):
                success_count_int = getattr(eff_logger_obj, "success_count_int", 0)
            if failure_count_int == 0 and hasattr(eff_logger_obj, "failure_count_int"):
                failure_count_int = getattr(eff_logger_obj, "failure_count_int", 0)
            if excluded_count_int == 0 and hasattr(eff_logger_obj, "excluded_count_int"):
                excluded_count_int = getattr(eff_logger_obj, "excluded_count_int", 0)
            if error_counts_dict is None and hasattr(eff_logger_obj, "get_error_counts"):
                error_counts_dict = eff_logger_obj.get_error_counts()
            if excluded_counts_dict is None and hasattr(eff_logger_obj, "get_excluded_counts"):
                excluded_counts_dict = eff_logger_obj.get_excluded_counts()

        # 3. 작업 명칭 확정
        effective_task_name_str: str = task_name_str or config.summary_reporter.default_task_name_str

        # 4. 시간 및 처리 성능 계산
        effective_start_time_float: float = start_time_float if start_time_float is not None else time.time()
        effective_start_datetime_str: str = start_datetime_str or DateTimeUtils.get_now_no_tz()
        elapsed_float: float = max(0.0, time.time() - effective_start_time_float)
        end_datetime_str: str = DateTimeUtils.get_now_no_tz()

        minutes_int: int = int(elapsed_float // 60)
        seconds_float: float = elapsed_float % 60
        if minutes_int > 0:
            time_display_str: str = config.summary_reporter.unit_minutes_seconds_template_str.format(
                minutes_int=minutes_int,
                seconds_float=seconds_float,
                elapsed_float=elapsed_float,
            )
        else:
            time_display_str: str = config.summary_reporter.unit_seconds_template_str.format(
                elapsed_float=elapsed_float,
            )

        # 5. 건수 수치 정합성 자동 보장 (전체 = 성공 + 실패 + 제외)
        calculated_sum_items_int: int = success_count_int + failure_count_int + excluded_count_int
        effective_total_items_int: int = calculated_sum_items_int if calculated_sum_items_int > 0 else total_items_int

        success_ratio_float: float = (
            (success_count_int / effective_total_items_int * 100.0) if effective_total_items_int > 0 else 0.0
        )
        failure_ratio_float: float = (
            (failure_count_int / effective_total_items_int * 100.0) if effective_total_items_int > 0 else 0.0
        )
        excluded_ratio_float: float = (
            (excluded_count_int / effective_total_items_int * 100.0) if effective_total_items_int > 0 else 0.0
        )

        rate_float: float = effective_total_items_int / max(0.001, elapsed_float)

        # 6. 마크다운 표 본문 데이터 구성
        table_headers_list: list[str] = [
            config.summary_reporter.table_header_division_str,
            config.summary_reporter.table_header_detail_str,
            config.summary_reporter.table_header_value_str,
            config.summary_reporter.table_header_note_str,
        ]
        unit_str: str = config.summary_reporter.unit_items_str
        table_data_rows_list: list[list[str]] = [
            [
                config.summary_reporter.category_time_str,
                config.summary_reporter.label_work_datetime_str,
                f"{effective_start_datetime_str} ~ {end_datetime_str}",
                time_display_str,
            ],
            [
                config.summary_reporter.category_count_str,
                config.summary_reporter.label_total_count_str,
                f"{effective_total_items_int:,} {unit_str}",
                config.summary_reporter.note_total_formula_str,
            ],
            [
                "",
                config.summary_reporter.label_success_count_str,
                f"{success_count_int:,} {unit_str}",
                f"{success_ratio_float:.1f}%",
            ],
            [
                "",
                config.summary_reporter.label_failure_count_str,
                f"{failure_count_int:,} {unit_str}",
                f"{failure_ratio_float:.1f}%",
            ],
            [
                "",
                config.summary_reporter.label_excluded_count_str,
                f"{excluded_count_int:,} {unit_str}",
                f"{excluded_ratio_float:.1f}%",
            ],
            [
                config.summary_reporter.category_perf_str,
                config.summary_reporter.label_throughput_str,
                f"{rate_float:.2f} {config.summary_reporter.unit_items_per_sec_str}",
                "",
            ],
        ]

        if total_bytes_int > 0:
            megabytes_value_float: float = total_bytes_int / (1024 * 1024)
            megabytes_rate_float: float = megabytes_value_float / max(0.001, elapsed_float)
            avg_rate_str: str = config.summary_reporter.note_average_rate_template_str.format(
                rate_float=megabytes_rate_float
            )
            table_data_rows_list.append(
                [
                    "",
                    config.summary_reporter.label_total_bytes_str,
                    f"{megabytes_value_float:.2f} MB",
                    avg_rate_str,
                ]
            )

        if extra_lines_list:
            for extra_line_str in extra_lines_list:
                cleaned_line_str: str = extra_line_str.strip().lstrip("-").strip()
                if ":" in cleaned_line_str:
                    item_key_str, item_value_str = cleaned_line_str.split(":", 1)
                    table_data_rows_list.append(
                        [
                            config.summary_reporter.category_detail_str,
                            item_key_str.strip(),
                            item_value_str.strip(),
                            "",
                        ]
                    )
                else:
                    table_data_rows_list.append(
                        [
                            config.summary_reporter.category_detail_str,
                            cleaned_line_str,
                            "",
                            "",
                        ]
                    )

        # 7. TableFormatter 를 통한 마크다운 표 렌더링
        formatted_table_rows_list: list[str] = TableFormatter.format_markdown_table(
            headers_list=table_headers_list,
            rows_list=table_data_rows_list,
            alignments_list=[":---", ":---", ":---", ":---"],
        )

        title_line_str: str = config.summary_reporter.report_title_template_str.format(
            task_name_str=effective_task_name_str
        )
        table_lines_list: list[str] = [
            "=" * 80,
            TableFormatter.pad_cell(cell_text_str=title_line_str, target_width_int=80, align_mode_str="center"),
            "=" * 80,
        ]
        table_lines_list.extend(formatted_table_rows_list)
        table_lines_list.append("=" * 80)

        # 8. 실패 및 제외 상세 내역 포맷팅
        effective_errors_dict: dict[str, int] = error_counts_dict if error_counts_dict is not None else {}
        effective_excluded_dict: dict[str, int] = excluded_counts_dict if excluded_counts_dict is not None else {}
        detail_lines_list: list[str] = []

        if effective_errors_dict:
            total_errors_int: int = sum(effective_errors_dict.values())
            detail_lines_list.append(
                config.summary_reporter.section_error_detail_template_str.format(
                    total_errors_int=total_errors_int
                )
            )
            for error_log_id_str, error_count_int in sorted(
                effective_errors_dict.items(), key=lambda item_tuple: (-item_tuple[1], item_tuple[0])
            ):
                description_str: str = ""
                if eff_logger_obj is not None and hasattr(eff_logger_obj, "get_log_id_description"):
                    description_str = eff_logger_obj.get_log_id_description(error_log_id_str)
                if description_str:
                    detail_lines_list.append(f"  * {error_log_id_str} ({description_str}): {error_count_int:,} {unit_str}")
                else:
                    detail_lines_list.append(f"  * {error_log_id_str}: {error_count_int:,} {unit_str}")
        elif failure_count_int > 0:
            detail_lines_list.append(
                config.summary_reporter.section_error_detail_template_str.format(
                    total_errors_int=failure_count_int
                )
            )
            detail_lines_list.append(
                f"  * {config.summary_reporter.unclassified_failure_str}: {failure_count_int:,} {unit_str}"
            )

        if effective_excluded_dict:
            total_excluded_items_int: int = sum(effective_excluded_dict.values())
            detail_lines_list.append(
                config.summary_reporter.section_excluded_detail_template_str.format(
                    total_excluded_items_int=total_excluded_items_int
                )
            )
            for excluded_log_id_str, excluded_count_int in sorted(
                effective_excluded_dict.items(), key=lambda item_tuple: (-item_tuple[1], item_tuple[0])
            ):
                description_str = ""
                if eff_logger_obj is not None and hasattr(eff_logger_obj, "get_log_id_description"):
                    description_str = eff_logger_obj.get_log_id_description(excluded_log_id_str)
                if description_str:
                    detail_lines_list.append(
                        f"  * {excluded_log_id_str} ({description_str}): {excluded_count_int:,} {unit_str}"
                    )
                else:
                    detail_lines_list.append(f"  * {excluded_log_id_str}: {excluded_count_int:,} {unit_str}")
        elif excluded_count_int > 0:
            detail_lines_list.append(
                config.summary_reporter.section_excluded_detail_template_str.format(
                    total_excluded_items_int=excluded_count_int
                )
            )
            detail_lines_list.append(
                f"  * {config.summary_reporter.unclassified_excluded_str}: {excluded_count_int:,} {unit_str}"
            )

        if detail_lines_list:
            table_lines_list.extend(detail_lines_list)
            table_lines_list.append("=" * 80)

        summary_block_str: str = "\n" + "\n".join(table_lines_list)
        return summary_block_str

    def log_summary(
        self,
        task_name_str: str = "",
        total_items_int: int = 0,
        success_count_int: int = 0,
        failure_count_int: int = 0,
        excluded_count_int: int = 0,
        start_time_float: Optional[float] = None,
        start_datetime_str: Optional[str] = None,
        total_bytes_int: int = 0,
        error_counts_dict: Optional[dict[str, int]] = None,
        excluded_counts_dict: Optional[dict[str, int]] = None,
        extra_lines_list: Optional[list[str]] = None,
        tracker_obj: Any = None,
        logger_obj: Any = None,
        level_str: str = "WARNING",
    ) -> None:
        """
        작업 실행 메트릭 또는 ProgressTracker 객체를 기반으로 최종 결과 요약 리포트(Summary Report)를 생성하여
        지정된 로그 레벨(기본값: WARNING)로 로깅합니다.

        :param task_name_str: 작업 명칭 (요약 리포트 제목용, 미지정 시 다국어 기본값 적용)
        :param total_items_int: 전체 처리 대상 건수
        :param success_count_int: 처리 성공 건수
        :param failure_count_int: 처리 실패 건수
        :param excluded_count_int: 처리 제외(Skip) 건수
        :param start_time_float: 작업 시작 타임스탬프 (미지정 시 현재 시간)
        :param start_datetime_str: 작업 시작 일시 문자열 (YYYY-MM-DD HH:MM:SS)
        :param total_bytes_int: 전송/처리된 총 바이트 수
        :param error_counts_dict: 에러 코드별 발생 건수 딕셔너리 (미지정 시 로거 자동 집계 사용)
        :param excluded_counts_dict: 제외 코드별 발생 건수 딕셔너리 (미지정 시 로거 자동 집계 사용)
        :param extra_lines_list: 요약 블록에 추가할 커스텀 상세 정보 행 리스트
        :param tracker_obj: 메트릭을 추출할 ProgressTracker 인스턴스 (지정 시 메트릭 인자 자동 추출)
        :param logger_obj: 리포트를 출력할 로거 객체 (미지정 시 self.logger_obj 사용)
        :param level_str: 출력할 로그 레벨 문자열 (기본값: 'WARNING')
        :return: None
        :raises None: 예외를 발생시키지 않음
        """
        eff_logger_obj: Any = logger_obj or self.logger_obj
        report_str: str = self.build_summary_report(
            task_name_str=task_name_str,
            total_items_int=total_items_int,
            success_count_int=success_count_int,
            failure_count_int=failure_count_int,
            excluded_count_int=excluded_count_int,
            start_time_float=start_time_float,
            start_datetime_str=start_datetime_str,
            total_bytes_int=total_bytes_int,
            error_counts_dict=error_counts_dict,
            excluded_counts_dict=excluded_counts_dict,
            extra_lines_list=extra_lines_list,
            tracker_obj=tracker_obj,
            logger_obj=eff_logger_obj,
        )

        if eff_logger_obj is not None:
            log_method_any: Any = getattr(eff_logger_obj, level_str.lower(), None)
            if callable(log_method_any):
                log_method_any("execution_summary_report", summary_str=report_str)
            else:
                logging.warning(report_str)
        else:
            logging.warning(report_str)
