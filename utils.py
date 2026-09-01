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
        self.total_items_int: int = max(0, total_items_int)
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
        self.error_counts_dict: dict[str, int] = {}

    def record_error(self, error_type_str: str, count_int: int = 1) -> None:
        """
        발생한 예외 또는 에러 유형(클래스명 또는 에러 식별자)의 발생 건수를 누적 기록합니다.

        :param error_type_str: 에러/예외 유형 명칭 (예: JSONDecodeError, KeyError, ValueError 등)
        :param count_int: 누적할 발생 건수 (기본값: 1)
        """
        if not error_type_str:
            error_type_str = "UnknownError"
        clean_type_str: str = str(error_type_str).strip()
        self.error_counts_dict[clean_type_str] = self.error_counts_dict.get(clean_type_str, 0) + max(1, count_int)

    def merge_error_counts(self, other_error_counts_dict: dict[str, int]) -> None:
        """
        다른 ProgressTracker 또는 외부에서 수집된 에러 유형별 건수 딕셔너리를 현재 추적기에 병합합니다.

        :param other_error_counts_dict: 병합 대상 에러 유형별 발생 건수 딕셔너리
        """
        if not other_error_counts_dict:
            return
        for err_type_str, cnt_int in other_error_counts_dict.items():
            self.record_error(err_type_str, count_int=cnt_int)

    def update(
        self,
        success_bool: bool = True,
        excluded_bool: bool = False,
        bytes_int: int = 0,
        details_str: str = "",
        error_type_str: str = "",
    ) -> None:
        """
        단일 아이템 처리 완료 시 호출하여 카운트를 갱신하고 레벨별 차등 로깅을 수행합니다.
        (일반 진행률: INFO 레벨, 지정 % 배수 마일스톤 및 완료 시점: WARNING 레벨)

        :param success_bool: 성공 여부
        :param excluded_bool: 제외 대상 여부 (예: 자산상태코드 09 등)
        :param bytes_int: 처리/전송된 데이터 바이트 수
        :param details_str: 추가 세부 정보 문자열 (옵션)
        :param error_type_str: 실패 시 발생한 에러/예외 유형 명칭 (옵션)
        """
        self.current_count_int += 1
        if excluded_bool:
            self.excluded_count_int += 1
        elif success_bool:
            self.success_count_int += 1
        else:
            self.failure_count_int += 1
            if error_type_str:
                self.record_error(error_type_str)

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

    @staticmethod
    def _search_dict_recursive(target_dict_any: Any, target_key_str: str) -> str:
        """
        중첩된 딕셔너리 구조 내에서 특정 키(target_key_str)의 문자열 템플릿 값을 재귀 탐색합니다.

        :param target_dict_any: 탐색 대상 딕셔너리 또는 ReadOnlyConfig
        :param target_key_str: 탐색할 로그 식별 코드
        :return: 발견된 템플릿 문자열 (미존재 시 빈 문자열)
        """
        if not target_dict_any:
            return ""
        if isinstance(target_dict_any, dict) or hasattr(target_dict_any, "items"):
            dict_items = target_dict_any.items() if hasattr(target_dict_any, "items") else {}
            # 1. 직속 키 우선 검사
            for k_any, v_any in dict_items:
                if str(k_any).strip() == target_key_str and isinstance(v_any, str):
                    return v_any
            # 2. 하위 딕셔너리 재귀 탐색
            for _, v_any in dict_items:
                if isinstance(v_any, dict) or hasattr(v_any, "items"):
                    found_str: str = ProgressTracker._search_dict_recursive(v_any, target_key_str)
                    if found_str:
                        return found_str
        return ""

    def _build_context_kwargs(self) -> dict[str, str]:
        """
        현재 작업 태스크명, 로거명 및 설정 파일 정보를 종합하여 템플릿 치환용 컨텍스트 변수 사전을 동적으로 구성합니다.

        :return: 컨텍스트 변수 딕셔너리 (예: {'service_name': 'BigQuery', 'storage_type': 'GCS', 'client_name': 'BigQuery'})
        """
        context_dict: dict[str, str] = {}

        # 1. task_name_str 및 logger 이름 기반 대상 서비스/스토리지 감지
        cand_text_str: str = f"{self.task_name_str} {getattr(self.logger, 'logger', self.logger)}"

        # 대표 서비스 식별 (BigQuery, GCS, ECS, S3, Oracle, PostgreSQL, MySQL 등)
        for keyword_str in ["BigQuery", "GCS", "ECS", "S3", "Oracle", "PostgreSQL", "MySQL"]:
            if keyword_str.lower() in cand_text_str.lower():
                if keyword_str in ("BigQuery", "Oracle", "PostgreSQL", "MySQL"):
                    context_dict.setdefault("service_name", keyword_str)
                    context_dict.setdefault("client_name", keyword_str)
                elif keyword_str in ("GCS", "ECS", "S3"):
                    context_dict.setdefault("storage_type", keyword_str)

        # 2. ConfigLoader 설정 기반 보완 (설정 파일에 정의된 활성 인프라 감지)
        try:
            from agent_common.config_loader import ConfigLoader
            loader = ConfigLoader()
            settings_dict = loader.get_settings()

            if "service_name" not in context_dict:
                if "bigquery" in settings_dict and settings_dict.get("bigquery"):
                    context_dict["service_name"] = "BigQuery"
                elif "db" in settings_dict and settings_dict.get("db"):
                    context_dict["service_name"] = "데이터베이스"

            if "storage_type" not in context_dict:
                if "gcs" in settings_dict and settings_dict.get("gcs"):
                    context_dict["storage_type"] = "GCS"
                elif "ecs" in settings_dict and settings_dict.get("ecs"):
                    context_dict["storage_type"] = "ECS"
        except Exception:
            pass

        return context_dict

    def get_log_id_description(self, log_id_str: str) -> str:
        """
        로그 ID(메시지 코드)에 대응하는 직관적인 한글 설명 문자열을 logging_messages.yml 설정으로부터 동적으로 조회하고,
        현재 실행 컨텍스트(서비스명, 스토리지명 등)를 자동 치환하여 정제합니다.

        :param log_id_str: 로그 메시지 식별 코드
        :return: 정제된 한글 설명 문자열 (미매핑 시 빈 문자열)
        """
        raw_template_str: str = ""

        # 1. self.logger 객체가 get_log_msg를 지원하는 경우 우선 탐색
        if self.logger and hasattr(self.logger, "get_log_msg"):
            try:
                candidate_str: str = self.logger.get_log_msg("ERROR", log_id_str, default_str="")
                if candidate_str and candidate_str != log_id_str:
                    raw_template_str = candidate_str
            except Exception:
                pass

        # 2. ConfigLoader 설정을 통한 전역 logging_messages 재귀 탐색
        if not raw_template_str:
            try:
                from agent_common.config_loader import ConfigLoader
                loader = ConfigLoader()
                all_msgs_dict = loader.setting("logging_messages", {})
                raw_template_str = self._search_dict_recursive(all_msgs_dict, log_id_str)
            except Exception:
                pass

        if not raw_template_str:
            return ""

        # 3. 템플릿 문자열 정제: 상세 파라미터 구분자(:, [ 등) 이전의 핵심 요약문 추출
        import re
        title_str: str = raw_template_str.split(":")[0].split("[")[0].strip()

        # 4. 현재 작업 컨텍스트 변수(service_name, storage_type 등) 치환
        context_vars_dict: dict[str, str] = self._build_context_kwargs()
        for k_var_str, v_val_str in context_vars_dict.items():
            title_str = title_str.replace(f"{{{k_var_str}}}", v_val_str)

        # 5. 미치환 템플릿 변수({stage}, {ecs_key} 등) 제거
        cleaned_str: str = re.sub(r"\{[^}]*\}", "", title_str)

        # 6. 괄호, 따옴표, 잉여 특수문자 및 연속 공백 정제
        cleaned_str = re.sub(r"[\(\)\[\]\'\"]", "", cleaned_str)
        cleaned_str = re.sub(r"\s+", " ", cleaned_str).strip(" -:,")

        return cleaned_str

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

        if self.error_counts_dict:
            total_errors_int: int = sum(self.error_counts_dict.values())
            lines_list.append(f"- 예외/오류 발생 세부 내역 (총 {total_errors_int:,}건):")
            for err_log_id_str, err_cnt_int in sorted(self.error_counts_dict.items(), key=lambda x: (-x[1], x[0])):
                desc_str: str = self.get_log_id_description(err_log_id_str)
                if desc_str:
                    lines_list.append(f"  * {err_log_id_str} ({desc_str}): {err_cnt_int:,} 건")
                else:
                    lines_list.append(f"  * {err_log_id_str}: {err_cnt_int:,} 건")
        elif self.failure_count_int > 0:
            lines_list.append(f"- 예외/오류 발생 세부 내역 (총 {self.failure_count_int:,}건):")
            lines_list.append(f"  * 기타 미분류 실패: {self.failure_count_int:,} 건")

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
