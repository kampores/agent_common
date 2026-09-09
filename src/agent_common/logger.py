# 작성일: 2026-08-08
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""앱과 스크립트의 표준 로깅 및 포매팅 기능을 제공하는 공용 로깅 모듈입니다."""

from __future__ import annotations

import logging
from logging import Logger
from collections.abc import Callable
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_common.config_loader import ConfigLoader

__all__ = [
    "SingleLineFlattenFormatter",
    "ProjectLogger",
    "Logger",
    "get_log_msg",
    "APP_DEFAULT_SCHEMA_DICT",
]


# ==============================================================================
# 로깅 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "logging": {
        "language_str": "KO",
        "level_str": "INFO",
        "format_str": "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d %(caller)s] %(message)s",
        "datefmt_str": "%Y-%m-%d %H:%M:%S",
        "file_logging_bool": True,
        "log_file_str": "logs/link/out/%Y/%m/%d/{log_level}/{app_name}_out_%Y%m%dT%H%M%S.log",
        "progress_interval_percent_int": 1,
        "print_deleted_pks_bool": False,
    }
}



class SingleLineFlattenFormatter(logging.Formatter):
    """
    로그 레코드 및 예외 추적(Traceback) 데이터를 포맷팅하는 공용 커스텀 로깅 포매터 클래스.
    (여러 줄 읽기를 지원하는 로그 수집기 환경에 맞춰 멀티라인 포맷팅을 지원합니다.)
    """

    def flatten_to_single_line(self, text: str) -> str:
        """텍스트 내부의 개행 문자(\n, \r)를 공백으로 변환합니다 (하위 호환성 유지용)."""
        return text.replace("\n", " ").replace("\r", " ")

    def format(self, record: logging.LogRecord) -> str:
        # 0. 로거 이름(name) 통일: ProjectLogger에 등록된 애플리케이션 이름이 있으면 우선 적용
        if ProjectLogger._app_name_str:
            record.name = ProjectLogger._app_name_str

        # 1. 호출 스택 프레임(Stack Frame) 탐색을 통한 클래스명(className) 및 caller 자동 추출
        class_name_str: str = ""
        try:
            import sys
            frame = sys._getframe()
            best_match_frame = None
            while frame:
                if frame.f_code.co_filename == record.pathname:
                    if frame.f_lineno == record.lineno:
                        best_match_frame = frame
                        break
                    elif frame.f_code.co_name == record.funcName and best_match_frame is None:
                        best_match_frame = frame
                frame = frame.f_back

            if best_match_frame is not None:
                self_obj = best_match_frame.f_locals.get("self")
                if self_obj is not None:
                    class_name_str = self_obj.__class__.__name__
                else:
                    cls_obj = best_match_frame.f_locals.get("cls")
                    if cls_obj is not None and hasattr(cls_obj, "__name__"):
                        class_name_str = cls_obj.__name__
        except Exception:
            pass

        # 스택에서 미발견 시 fallback 활용
        if not class_name_str:
            if hasattr(record, "className") and record.className:
                class_name_str = str(record.className)
            elif hasattr(record, "fallback_class_name") and record.fallback_class_name:
                class_name_str = str(record.fallback_class_name)

        record.className = class_name_str
        record.caller = f"{class_name_str}.{record.funcName}()" if class_name_str else f"{record.funcName}()"

        # 2. 예외(Traceback) 발생 원천 지점 정보([Origin: filename:Llineno in funcName()]) 추출
        origin_prefix = ""
        if record.exc_info and len(record.exc_info) >= 3 and record.exc_info[2]:
            try:
                import traceback
                tb_list = traceback.extract_tb(record.exc_info[2])
                if tb_list:
                    last_frame = tb_list[-1]
                    origin_file = Path(last_frame.filename).name
                    origin_prefix = f"[Origin: {origin_file}:L{last_frame.lineno} in {last_frame.name}()] "
            except Exception:
                pass

        # 3. 부모 클래스의 기본 포맷팅 수행 (다중 행 로그 및 Traceback 원형 보존)
        s = super().format(record)

        # 4. Origin 원천 지점 정보가 있으면 메인 로그 메시지 서두/줄말에 결합
        if origin_prefix:
            if "\nTraceback" in s:
                head, tail = s.split("\nTraceback", 1)
                s = f"{head} {origin_prefix}\nTraceback{tail}"
            elif "\n" in s:
                head, tail = s.split("\n", 1)
                s = f"{head} {origin_prefix}\n{tail}"
            else:
                s = f"{s} {origin_prefix}"

        return s


class ProjectLogger:
    """앱과 스크립트의 로깅 설정을 표준화하고 예외 및 템플릿 로그를 기록하는 프로젝트 로거 클래스.

    디자인 패턴: 파이썬 표준 logging.Logger를 감싸는 어댑터(Adapter Pattern) 역할을 수행하며,
    기존 info/warning/error 메서드는 물론 log_msg(level, code, **kwargs) 등의 메서드를 직접 지원합니다.
    """

    # 중복 basicConfig 호출로 handler가 겹치지 않도록 로깅 초기화 여부를 기억합니다.
    _configured = False
    _app_name_str: str | None = None
    # 클래스 전역 결과 건수 및 에러/제외 집계
    _success_count_int: int = 0
    _failure_count_int: int = 0
    _excluded_count_int: int = 0
    _error_counts_dict: dict[str, int] = {}
    _excluded_counts_dict: dict[str, int] = {}

    def __init__(self, name: str | logging.Logger | None = None, config_dir: str | Path | None = None):
        self._config_loader: ConfigLoader | None = None
        self.success_count_int: int = 0
        self.failure_count_int: int = 0
        self.excluded_count_int: int = 0
        self.error_counts_dict: dict[str, int] = {}
        self.excluded_counts_dict: dict[str, int] = {}
        if config_dir:
            self.config_loader.config_dir_set(config_dir)

        if isinstance(name, logging.Logger):
            self.logger: logging.Logger = name
            self._assigned_name_str: str = getattr(name, "name", "")
        else:
            self._assigned_name_str: str = name or ""
            eff_logger_name_str: str = (
                ProjectLogger._app_name_str
                if ProjectLogger._app_name_str
                else (self._assigned_name_str if self._assigned_name_str else "app")
            )
            if not ProjectLogger._configured:
                logging.basicConfig(level=logging.INFO)
                ProjectLogger._configured = True
            self.logger: logging.Logger = logging.getLogger(eff_logger_name_str)

    def _inject_fallback_extra(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """스택 추적 실패 시 보완을 위해 인스턴스 생성 시 전달된 클래스명을 extra에 안전하게 주입합니다."""
        if self._assigned_name_str:
            extra_val = kwargs.get("extra")
            if isinstance(extra_val, dict):
                if "fallback_class_name" not in extra_val:
                    extra_val["fallback_class_name"] = self._assigned_name_str
            else:
                kwargs["extra"] = {"fallback_class_name": self._assigned_name_str}
        return kwargs

    @property
    def config_loader(self) -> ConfigLoader:
        """ConfigLoader 객체를 반환하며, 미초기화 시 지연 로딩(Lazy Initialization)하여 무한 루프를 방지합니다."""
        if self._config_loader is None:
            from agent_common.config_loader import ConfigLoader
            self._config_loader = ConfigLoader()
        return self._config_loader

    @classmethod
    def configure(
        cls,
        config_dir: str | Path | None = None,
        default_log_file_str: str = "logs/app.log",
        app_name_str: str | None = None,
        file_logging_bool: bool | None = None,
    ) -> None:
        """설정 파일(logging.yml, config.yml 등)을 기반으로 전체 로깅 환경을 일괄 초기화합니다.

        :param config_dir: 커스텀 설정 디렉토리 경로 (선택)
        :param default_log_file_str: 기본 로그 파일 경로 (선택, 기본값: 'logs/app.log')
        :param app_name_str: 애플리케이션 명칭 (로그 파일명 {app_name} 치환용)
        :param file_logging_bool: 로그 파일 생성 활성화 여부 (True: 파일 저장, False: 콘솔만 출력, None: config.yml logging.file_logging 설정 준용)
        """
        import sys
        from agent_common.config_loader import ConfigLoader

        if not app_name_str:
            app_name_str = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else "app"

        cls._app_name_str = app_name_str

        loader = ConfigLoader(config_dir=config_dir)
        level_dict: dict[str, str] | None = loader.setting("logging.level_dict")
        if level_dict:
            app_key_str: str = f"{app_name_str}_str"
            log_level_str: str = level_dict.get(app_key_str) or level_dict.get(app_name_str) or level_dict.get("default", "INFO")
        else:
            log_level_str = loader.setting("logging.level_str") or "INFO"

        log_format_str: str = loader.setting("logging.format_str")
        datefmt_str: str = loader.setting("logging.datefmt_str")

        level = getattr(logging, log_level_str.upper(), logging.INFO)

        formatter = SingleLineFlattenFormatter(log_format_str, datefmt=datefmt_str)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers: list[logging.Handler] = [console_handler]

        # 로그 파일 생성 활성화 여부 결정 (CLI 파라미터 우선 -> config.yml logging.file_logging_bool)
        cfg_file_logging_bool: bool | None = loader.setting("logging.file_logging_bool")
        final_file_logging_bool: bool = (
            file_logging_bool
            if file_logging_bool is not None
            else (cfg_file_logging_bool if cfg_file_logging_bool is not None else True)
        )

        level_name_str: str = logging.getLevelName(level).lower()

        # 로그 파일 저장 경로 템플릿 결정 (단일 표준 log_file_str 우선 -> 미설정 시 기본값)
        target_log_file_path_str: str = loader.setting("logging.log_file_str") or default_log_file_str

        if final_file_logging_bool and target_log_file_path_str:
            from datetime import datetime

            today_dt: datetime = datetime.now()
            target_log_template_str: str = target_log_file_path_str
            # {app_name}, {log_level} (소문자), {LOG_LEVEL} (대문자) 동적 치환
            target_log_formatted_str: str = target_log_template_str.format(
                app_name=app_name_str,
                log_level=level_name_str,
                LOG_LEVEL=level_name_str.upper(),
            )
            dynamic_log_file_path: Path = Path(today_dt.strftime(target_log_formatted_str))
            log_file_path: Path = loader.project_path(dynamic_log_file_path)
            try:
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler_obj = logging.FileHandler(log_file_path, encoding="utf-8")
                file_handler_obj.setFormatter(formatter)
                handlers.append(file_handler_obj)
            except PermissionError as perm_err:
                sys.stderr.write(
                    f"[경고] 로그 파일 저장 디렉터리({log_file_path.parent})에 대한 접근/생성 권한이 없어 "
                    f"파일 로깅을 비활성화하고 콘솔 출력만 유지합니다: {perm_err}\n"
                )
            except OSError as os_err:
                sys.stderr.write(
                    f"[경고] 로그 파일 경로({log_file_path}) 생성 중 OS 오류가 발생하여 "
                    f"파일 로깅을 비활성화하고 콘솔 출력만 유지합니다: {os_err}\n"
                )
            except Exception as unk_err:
                sys.stderr.write(
                    f"[경고] 로그 핸들러 초기화 중 예기치 않은 오류가 발생하여 "
                    f"파일 로깅을 비활성화하고 콘솔 출력만 유지합니다: {unk_err}\n"
                )

        logging.basicConfig(
            level=level,
            format=log_format_str,
            handlers=handlers,
            force=True,
        )
        logging.getLogger("metricflow").setLevel(logging.WARNING)
        logging.getLogger("metricflow_semantics").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        ProjectLogger._configured = True

    @classmethod
    def set_language(cls, lang_str: str) -> None:
        """전역 로그 메시지 언어를 'KO' 또는 'EN'으로 설정합니다.

        :param lang_str: 설정할 언어 코드 ('KO' 또는 'EN', 대소문자 무관)
        """
        from agent_common.config_loader import ConfigLoader
        ConfigLoader.set_language(lang_str)

    def language_set(self, lang_str: str) -> None:
        """로그 메시지 언어를 'KO' 또는 'EN'으로 설정합니다 (Setter).

        :param lang_str: 설정할 언어 코드 ('KO' 또는 'EN', 대소문자 무관)
        """
        self.set_language(lang_str)

    @property
    def language(self) -> str:
        """현재 적용 중인 로그 메시지 언어 코드를 반환합니다 (Getter)."""
        return self.config_loader.language

    def _search_template_in_level(self, target_lvl_str: str, target_code_str: str) -> str | None:
        """
        지정된 로그 레벨 섹션 또는 하위 카테고리에서 메시지 코드 템플릿을 탐색합니다.

        :param target_lvl_str: 탐색 대상 로그 레벨 문자열 (INFO, WARNING, ERROR 등)
        :param target_code_str: 탐색할 메시지 식별 코드 문자열
        :return: 발견된 메시지 템플릿 문자열 (미발견 시 None)
        """
        direct_template_str: Any = self.config_loader.setting(f"logging_messages.{target_lvl_str}.{target_code_str}")
        if direct_template_str and isinstance(direct_template_str, str):
            return direct_template_str
        lvl_dict: Any = self.config_loader.setting(f"logging_messages.{target_lvl_str}")
        if isinstance(lvl_dict, dict):
            for _, sub_val in lvl_dict.items():
                if isinstance(sub_val, dict) and target_code_str in sub_val:
                    candidate_str: Any = sub_val[target_code_str]
                    if isinstance(candidate_str, str):
                        return candidate_str
        return None

    def get_log_msg(self, level_str: str, msg_code_str: str, default_str: str = "", **kwargs: Any) -> str:
        """logging_messages_ko.yml 또는 logging_messages_en.yml에 정의된 로그 레벨(level_str)과 메시지 코드(msg_code_str) 템플릿을 포매팅하여 반환합니다.

        :param level_str: 로그 레벨 문자열 (INFO, WARNING, ERROR 등)
        :param msg_code_str: 메시지 식별 코드
        :param default_str: 템플릿 미존재 시 사용할 기본 문자열
        :param kwargs: 템플릿 포매팅용 키워드 인자
        :return: 포매팅 완료된 로그 메시지 문자열
        """
        target_level_str: str = str(level_str).strip().upper()
        target_code_str: str = str(msg_code_str).strip()

        template_str: str | None = self._search_template_in_level(target_level_str, target_code_str)

        if not template_str:
            all_msgs_dict: Any = self.config_loader.setting("logging_messages")
            if isinstance(all_msgs_dict, dict):
                for other_lvl_str in all_msgs_dict.keys():
                    if str(other_lvl_str).upper() != target_level_str:
                        cand_str: str | None = self._search_template_in_level(str(other_lvl_str).upper(), target_code_str)
                        if cand_str:
                            template_str = cand_str
                            break

        if not template_str or not isinstance(template_str, str):
            template_str = default_str or target_code_str
        if kwargs:
            try:
                safe_kwargs_dict: dict[str, Any] = {
                    k: str(v).replace("{", "{{").replace("}", "}}") if isinstance(v, str) else v
                    for k, v in kwargs.items()
                }
                return template_str.format(**safe_kwargs_dict)
            except Exception:
                kwargs_detail_str: str = " ".join(f"{k}={v}" for k, v in kwargs.items())
                return f"{template_str} [{kwargs_detail_str}]" if template_str != target_code_str else f"[FATAL][Fail-Fast] {target_code_str}: {kwargs_detail_str}"
        return str(template_str)

    def record_error(self, error_type_str: str, count_int: int = 1) -> None:
        """
        발생한 예외 또는 에러 식별자(로그 ID)의 발생 건수를 누적 기록합니다.

        :param error_type_str: 에러 식별 코드 또는 예외 클래스명
        :param count_int: 누적할 발생 건수 (기본값: 1)
        """
        if not error_type_str:
            error_type_str = "UnknownError"
        clean_code_str: str = str(error_type_str).strip()
        self.error_counts_dict[clean_code_str] = self.error_counts_dict.get(clean_code_str, 0) + max(1, count_int)
        ProjectLogger._error_counts_dict[clean_code_str] = ProjectLogger._error_counts_dict.get(clean_code_str, 0) + max(1, count_int)

    def record_exclusion(self, exclusion_type_str: str, count_int: int = 1) -> None:
        """
        발생한 제외 사유 또는 제외 식별자(로그 ID)의 발생 건수를 누적 기록합니다.

        :param exclusion_type_str: 제외 식별 코드(로그 ID) 또는 사유 문자열
        :param count_int: 누적할 발생 건수 (기본값: 1)
        """
        if not exclusion_type_str:
            exclusion_type_str = "UnknownExclusion"
        clean_code_str: str = str(exclusion_type_str).strip()
        self.excluded_counts_dict[clean_code_str] = self.excluded_counts_dict.get(clean_code_str, 0) + max(1, count_int)
        ProjectLogger._excluded_counts_dict[clean_code_str] = ProjectLogger._excluded_counts_dict.get(clean_code_str, 0) + max(1, count_int)

    def get_error_counts(self) -> dict[str, int]:
        """
        누적된 에러 유형/로그 ID별 발생 건수 딕셔너리를 반환합니다.
        클래스 전역 집계가 존재할 경우 이를 우선 반환하여 모듈 간 집계를 통합합니다.

        :return: 에러 코드별 발생 건수 딕셔너리
        """
        if ProjectLogger._error_counts_dict:
            return dict(ProjectLogger._error_counts_dict)
        return dict(self.error_counts_dict)

    def reset_error_counts(self) -> None:
        """현재 인스턴스 및 클래스 전역 에러 건수 집계를 초기화합니다."""
        self.error_counts_dict.clear()
        ProjectLogger._error_counts_dict.clear()

    @classmethod
    def get_global_error_counts(cls) -> dict[str, int]:
        """클래스 전역으로 누적된 모든 에러 건수 딕셔너리를 반환합니다."""
        return dict(cls._error_counts_dict)

    @classmethod
    def reset_global_error_counts(cls) -> None:
        """클래스 전역 에러 건수 집계를 초기화합니다."""
        cls._error_counts_dict.clear()

    def get_excluded_counts(self) -> dict[str, int]:
        """
        누적된 제외 사유/로그 ID별 발생 건수 딕셔너리를 반환합니다.
        클래스 전역 집계가 존재할 경우 이를 우선 반환하여 모듈 간 집계를 통합합니다.

        :return: 제외 코드별 발생 건수 딕셔너리
        """
        if ProjectLogger._excluded_counts_dict:
            return dict(ProjectLogger._excluded_counts_dict)
        return dict(self.excluded_counts_dict)

    def reset_excluded_counts(self) -> None:
        """현재 인스턴스 및 클래스 전역 제외 건수 집계를 초기화합니다."""
        self.excluded_counts_dict.clear()
        ProjectLogger._excluded_counts_dict.clear()

    @classmethod
    def get_global_excluded_counts(cls) -> dict[str, int]:
        """클래스 전역으로 누적된 모든 제외 건수 딕셔너리를 반환합니다."""
        return dict(cls._excluded_counts_dict)

    @classmethod
    def reset_global_excluded_counts(cls) -> None:
        """클래스 전역 제외 건수 집계를 초기화합니다."""
        cls._excluded_counts_dict.clear()

    def update(
        self,
        success_bool: bool = True,
        excluded_bool: bool = False,
        count_int: int = 1,
        log_id_str: str = "",
    ) -> None:
        """
        작업 진행 건수의 결과 유형(성공/실패/제외)을 분류하여 누적 기록합니다.

        :param success_bool: 성공 여부
        :param excluded_bool: 제외 대상 여부 (예: 자산상태코드 09, 중복 PK 등)
        :param count_int: 누적할 건수 (기본값: 1)
        :param log_id_str: 실패 또는 제외 발생 시 연계할 로그 ID 식별 코드 (선택)
        """
        inc_int: int = max(1, count_int)
        if excluded_bool:
            self.excluded_count_int += inc_int
            ProjectLogger._excluded_count_int += inc_int
            if log_id_str:
                self.record_exclusion(log_id_str, count_int=inc_int)
        elif success_bool:
            self.success_count_int += inc_int
            ProjectLogger._success_count_int += inc_int
        else:
            self.failure_count_int += inc_int
            ProjectLogger._failure_count_int += inc_int
            if log_id_str:
                self.record_error(log_id_str, count_int=inc_int)

    def record_result(
        self,
        success_bool: bool = True,
        excluded_bool: bool = False,
        count_int: int = 1,
        log_id_str: str = "",
    ) -> None:
        """진행 건수 분류 기록의 명시적 별칭 메서드입니다."""
        self.update(success_bool=success_bool, excluded_bool=excluded_bool, count_int=count_int, log_id_str=log_id_str)

    def record_success(self, count_int: int = 1) -> None:
        """성공 건수를 누적 기록합니다."""
        self.update(success_bool=True, excluded_bool=False, count_int=count_int)

    def record_failure(self, count_int: int = 1, log_id_str: str = "") -> None:
        """실패 건수를 누적 기록합니다."""
        self.update(success_bool=False, excluded_bool=False, count_int=count_int, log_id_str=log_id_str)

    def record_excluded(self, log_id_or_count: str | int = "", count_int: int = 1) -> None:
        """
        제외 건수 및 제외 식별자(로그 ID)를 누적 기록합니다.

        :param log_id_or_count: 제외 식별 코드(로그 ID) 또는 기존 호환용 누적 건수
        :param count_int: 누적할 건수 (기본값: 1, 첫 번째 인자가 정수일 경우 무시)
        """
        if isinstance(log_id_or_count, int):
            eff_count_int: int = log_id_or_count
            eff_code_str: str = ""
        else:
            eff_count_int = count_int
            eff_code_str = str(log_id_or_count).strip()
        self.update(success_bool=False, excluded_bool=True, count_int=eff_count_int, log_id_str=eff_code_str)

    def get_result_counts(self) -> dict[str, int]:
        """성공, 실패, 제외 건수 딕셔너리를 반환합니다."""
        has_instance_counts_bool: bool = bool(self.success_count_int or self.failure_count_int or self.excluded_count_int)
        return {
            "success": self.success_count_int if has_instance_counts_bool else ProjectLogger._success_count_int,
            "failure": self.failure_count_int if has_instance_counts_bool else ProjectLogger._failure_count_int,
            "excluded": self.excluded_count_int if has_instance_counts_bool else ProjectLogger._excluded_count_int,
        }

    def reset_result_counts(self) -> None:
        """진행 건수 분류 통계 및 에러/제외 집계를 초기화합니다."""
        self.success_count_int = 0
        self.failure_count_int = 0
        self.excluded_count_int = 0
        ProjectLogger._success_count_int = 0
        ProjectLogger._failure_count_int = 0
        ProjectLogger._excluded_count_int = 0
        self.reset_error_counts()
        self.reset_excluded_counts()

    def get_log_id_description(self, log_id_str: str) -> str:
        """
        로그 ID(메시지 코드)에 대응하는 직관적인 설명 문자열을 logging_messages 설정(KO/EN)으로부터 동적으로 조회하고 정제하여 반환합니다.

        :param log_id_str: 로그 메시지 식별 코드
        :return: 정제된 설명 문자열 (미매핑 시 빈 문자열)
        """
        if not log_id_str:
            return ""

        target_code_str: str = str(log_id_str).strip()
        template_val: str | None = self._search_template_in_level("ERROR", target_code_str)

        if not template_val:
            all_msgs_dict = self.config_loader.setting("logging_messages")
            if isinstance(all_msgs_dict, dict):
                for lvl_str in all_msgs_dict.keys():
                    cand_str: str | None = self._search_template_in_level(str(lvl_str).upper(), target_code_str)
                    if cand_str:
                        template_val = cand_str
                        break

        if not template_val or not isinstance(template_val, str) or template_val == target_code_str:
            return ""

        # 상세 파라미터 구분자(:, [ 등) 이전의 핵심 요약문 추출
        import re
        title_str: str = template_val.split(":")[0].strip()
        if "[" in title_str:
            if title_str.startswith("[") and "]" in title_str:
                closing_bracket_idx_int: int = title_str.find("]")
                after_tag_str: str = title_str[closing_bracket_idx_int + 1:]
                if "[" in after_tag_str:
                    title_str = title_str[:closing_bracket_idx_int + 1] + after_tag_str.split("[")[0]
            else:
                title_str = title_str.split("[")[0].strip()

        # 기본 서비스/스토리지 컨텍스트 치환 (설정 파일 기반 감지)
        try:
            settings_dict = self.config_loader.get_settings()
            if "bigquery" in settings_dict and settings_dict.get("bigquery"):
                title_str = title_str.replace("{service_name}", "BigQuery").replace("{client_name}", "BigQuery")
            elif "db" in settings_dict and settings_dict.get("db"):
                title_str = title_str.replace("{service_name}", "데이터베이스").replace("{client_name}", "데이터베이스")

            if "gcs" in settings_dict and settings_dict.get("gcs"):
                title_str = title_str.replace("{storage_type}", "GCS")
            elif "ecs" in settings_dict and settings_dict.get("ecs"):
                title_str = title_str.replace("{storage_type}", "ECS")
        except Exception:
            pass

        # 미치환 템플릿 변수({stage}, {ecs_key} 등) 제거
        cleaned_str: str = re.sub(r"\{[^}]*\}", "", title_str)

        # 괄호, 따옴표, 잉여 특수문자 및 연속 공백 정제
        cleaned_str = re.sub(r"[\(\)\[\]\'\"]", "", cleaned_str)
        cleaned_str = re.sub(r"\s+", " ", cleaned_str).strip(" -:,")

        return cleaned_str

    def log_msg(
        self,
        level_str: str,
        msg_code_str: str,
        default_str: str = "",
        **kwargs: Any,
    ) -> str:
        """코드 기반 메시지를 로거에 즉시 기록하고 완성된 메시지를 반환합니다.

        :param level_str: 로그 레벨 문자열
        :param msg_code_str: 메시지 식별 코드
        :param default_str: 기본 문자열
        :param kwargs: 추가 포매팅 인자
        :return: 기록된 완성 메시지 문자열
        """
        lvl_name_str: str = str(level_str).strip().upper()
        if lvl_name_str in ("ERROR", "CRITICAL"):
            self.record_error(msg_code_str)
        stacklevel_int: int = kwargs.pop("stacklevel", 2)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        msg_str: str = self.get_log_msg(level_str, msg_code_str, default_str=default_str, **kwargs)
        lvl_num_int: int = getattr(logging, lvl_name_str, logging.INFO)
        self.logger.log(lvl_num_int, msg_str, stacklevel=stacklevel_int, extra=extra_dict)
        return msg_str

    def info(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """INFO 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("INFO", msg_or_code, default=default, **kwargs)
            self.logger.info(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.logger.info(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def warning(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """WARNING 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("WARNING", msg_or_code, default=default, **kwargs)
            self.logger.warning(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.logger.warning(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def error(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """ERROR 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        self.record_failure(1)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            self.record_error(msg_or_code)
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.error(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.record_error(msg_or_code.__class__.__name__ if hasattr(msg_or_code, "__class__") else "UnknownError")
        self.logger.error(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def critical(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """CRITICAL 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        self.record_failure(1)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            self.record_error(msg_or_code)
            msg = self.get_log_msg("CRITICAL", msg_or_code, default=default, **kwargs)
            self.logger.critical(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.record_error(msg_or_code.__class__.__name__ if hasattr(msg_or_code, "__class__") else "UnknownError")
        self.logger.critical(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def debug(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """DEBUG 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("DEBUG", msg_or_code, default=default, **kwargs)
            self.logger.debug(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.logger.debug(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def exception(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """예외 Traceback 정보와 함께 ERROR 레벨로 로그를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        self.record_failure(1)
        kwargs = self._inject_fallback_extra(kwargs)
        extra_dict = kwargs.pop("extra", None)
        if isinstance(msg_or_code, str):
            self.record_error(msg_or_code)
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.exception(msg, *args, stacklevel=stacklevel, extra=extra_dict)
            return msg
        self.record_error(msg_or_code.__class__.__name__ if hasattr(msg_or_code, "__class__") else "UnknownError")
        self.logger.exception(msg_or_code, *args, stacklevel=stacklevel, extra=extra_dict, **kwargs)
        return str(msg_or_code)

    def log_summary(
        self,
        task_name_str: str = "작업",
        total_items_int: int = 0,
        success_count_int: int = 0,
        failure_count_int: int = 0,
        excluded_count_int: int = 0,
        start_time_float: float | None = None,
        start_datetime_str: str | None = None,
        total_bytes_int: int = 0,
        error_counts_dict: dict[str, int] | None = None,
        excluded_counts_dict: dict[str, int] | None = None,
        extra_lines_list: list[str] | None = None,
        tracker_obj: Any = None,
    ) -> None:
        """
        작업 실행 메트릭 또는 ProgressTracker 객체를 기반으로 최종 결과 요약 리포트(Summary Report)를 생성하여 WARNING 레벨로 로깅합니다.

        :param task_name_str: 작업 명칭 (요약 리포트 제목용)
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
        :param tracker_obj: 메트릭을 추출할 ProgressTracker 인스턴스 (지정 시 다른 메트릭 인자 자동 추출)
        """
        if tracker_obj is not None:
            task_name_str = getattr(tracker_obj, "task_name_str", task_name_str)
            total_items_int = getattr(tracker_obj, "total_items_int", total_items_int)
            start_time_float = getattr(tracker_obj, "start_time_float", start_time_float)
            start_datetime_str = getattr(tracker_obj, "start_datetime_str", start_datetime_str)
            total_bytes_int = getattr(tracker_obj, "total_bytes_int", total_bytes_int)

        counts_dict: dict[str, int] = self.get_result_counts()
        eff_success_count_int: int = success_count_int or counts_dict["success"]
        eff_failure_count_int: int = failure_count_int or counts_dict["failure"]
        eff_excluded_count_int: int = excluded_count_int or counts_dict["excluded"]

        import time
        from agent_common.tool.date.date_time_utils import DateTimeUtils

        effective_start_time_float: float = start_time_float if start_time_float is not None else time.time()
        effective_start_datetime_str: str = start_datetime_str or DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ_STR)
        elapsed_float: float = time.time() - effective_start_time_float
        end_datetime_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ_STR)

        mins_int: int = int(elapsed_float // 60)
        secs_float: float = elapsed_float % 60
        time_display_str: str = f"{mins_int}분 {secs_float:.1f}초 ({elapsed_float:.2f}초)" if mins_int > 0 else f"{elapsed_float:.2f}초"

        lines_list: list[str] = [
            "=" * 80,
            f"                    [{task_name_str} 작업 결과 요약]",
            "=" * 80,
            f"- 작업 시작 / 종료 시간 : {effective_start_datetime_str} ~ {end_datetime_str}",
            f"- 총 소요 시간          : {time_display_str}",
            "-" * 80,
            f"- 총 처리 대상 건수     : {total_items_int:,} 건",
            f"- 처리 성공 / 실패      : {eff_success_count_int:,} 건 / {eff_failure_count_int:,} 건",
            f"- 처리 제외 (Skip)      : {eff_excluded_count_int:,} 건",
        ]

        # 에러 통계 조회: 인자로 전달된 error_counts_dict 우선, 없으면 로거의 get_error_counts() 사용
        errors_map_dict: dict[str, int] = error_counts_dict if error_counts_dict is not None else self.get_error_counts()

        if errors_map_dict:
            total_errors_int: int = sum(errors_map_dict.values())
            lines_list.append(f"- 예외/오류 발생 세부 내역 (총 {total_errors_int:,}건):")
            for err_log_id_str, err_cnt_int in sorted(errors_map_dict.items(), key=lambda x: (-x[1], x[0])):
                desc_str: str = self.get_log_id_description(err_log_id_str)
                if desc_str:
                    lines_list.append(f"  * {err_log_id_str} ({desc_str}): {err_cnt_int:,} 건")
                else:
                    lines_list.append(f"  * {err_log_id_str}: {err_cnt_int:,} 건")
        elif eff_failure_count_int > 0:
            lines_list.append(f"- 예외/오류 발생 세부 내역 (총 {eff_failure_count_int:,}건):")
            lines_list.append(f"  * 기타 미분류 실패: {eff_failure_count_int:,} 건")

        # 제외 통계 조회: 인자로 전달된 excluded_counts_dict 우선, 없으면 로거의 get_excluded_counts() 사용
        excluded_map: dict[str, int] = excluded_counts_dict if excluded_counts_dict is not None else self.get_excluded_counts()

        if excluded_map:
            total_excluded_items_int: int = sum(excluded_map.values())
            lines_list.append(f"- 처리 제외 세부 내역 (총 {total_excluded_items_int:,}건):")
            for excl_log_id_str, excl_cnt_int in sorted(excluded_map.items(), key=lambda x: (-x[1], x[0])):
                desc_str: str = self.get_log_id_description(excl_log_id_str)
                if desc_str:
                    lines_list.append(f"  * {excl_log_id_str} ({desc_str}): {excl_cnt_int:,} 건")
                else:
                    lines_list.append(f"  * {excl_log_id_str}: {excl_cnt_int:,} 건")
        elif eff_excluded_count_int > 0:
            lines_list.append(f"- 처리 제외 세부 내역 (총 {eff_excluded_count_int:,}건):")
            lines_list.append(f"  * 기타 미분류 제외: {eff_excluded_count_int:,} 건")

        if total_bytes_int > 0:
            mb_val_float: float = total_bytes_int / (1024 * 1024)
            mb_rate_float: float = mb_val_float / max(0.001, elapsed_float)
            lines_list.append(f"- 총 전송 데이터 용량   : {mb_val_float:.2f} MB (평균 {mb_rate_float:.2f} MB/s)")

        total_processed_int: int = eff_success_count_int + eff_failure_count_int + eff_excluded_count_int
        rate_float: float = total_processed_int / max(0.001, elapsed_float)
        lines_list.append(f"- 평균 처리 속도        : {rate_float:.2f} items/sec")

        if extra_lines_list:
            lines_list.append("-" * 80)
            for line_str in extra_lines_list:
                lines_list.append(f"- {line_str}" if not line_str.startswith("-") else line_str)

        lines_list.append("=" * 80)

        summary_block_str: str = "\n" + "\n".join(lines_list)
        self.warning("execution_summary_report", summary=summary_block_str)

    @staticmethod
    def log_request_result(
        logger: ProjectLogger | logging.Logger,
        method: str,
        path: str,
        start_time: float,
        status_code: int | None = None,
        exc: Exception | None = None,
    ) -> None:
        """HTTP 요청 처리 시간과 성공/실패 여부를 포맷하여 로그에 기록합니다."""
        from time import perf_counter

        elapsed_ms = (perf_counter() - start_time) * 1000
        if exc is not None:
            logger.exception(
                "request_error method=%s path=%s elapsed_ms=%.2f",
                method,
                path,
                elapsed_ms,
                stacklevel=2,
            )
        else:
            logger.info(
                "request_end method=%s path=%s status_code=%s elapsed_ms=%.2f",
                method,
                path,
                status_code,
                elapsed_ms,
                stacklevel=2,
            )


# 하위 호환성을 위한 별칭 함수
get_log_msg = ProjectLogger.get_log_msg
