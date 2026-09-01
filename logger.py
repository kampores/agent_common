# 작성일: 2026-08-08
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""앱과 스크립트의 표준 로깅 및 포매팅 기능을 제공하는 공용 로깅 모듈입니다."""

from __future__ import annotations

import logging
from logging import Logger
from collections.abc import Callable
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_common.config_loader import ConfigLoader

__all__ = ["SingleLineFlattenFormatter", "ProjectLogger", "Logger", "get_log_msg"]


class SingleLineFlattenFormatter(logging.Formatter):
    """
    로그 레코드 및 예외 추적(Traceback) 데이터를 포맷팅하는 공용 커스텀 로깅 포매터 클래스.
    (여러 줄 읽기를 지원하는 로그 수집기 환경에 맞춰 멀티라인 포맷팅을 지원합니다.)
    """

    def flatten_to_single_line(self, text: str) -> str:
        """텍스트 내부의 개행 문자(\n, \r)를 공백으로 변환합니다 (하위 호환성 유지용)."""
        return text.replace("\n", " ").replace("\r", " ")

    def format(self, record: logging.LogRecord) -> str:
        # 0. 예외(Traceback) 발생 원천 지점 정보([Origin: filename:Llineno in funcName()]) 추출
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

        # 1. 부모 클래스의 기본 포맷팅 수행 (다중 행 로그 및 Traceback 원형 보존)
        s = super().format(record)

        # 2. Origin 원천 지점 정보가 있으면 메인 로그 메시지 서두/줄말에 결합
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

    def __init__(self, name: str | logging.Logger, config_dir: str | Path | None = None):
        self._config_loader: ConfigLoader | None = None
        if config_dir:
            self.config_loader.config_dir_set(config_dir)

        if isinstance(name, logging.Logger):
            self.logger: logging.Logger = name
        else:
            if not ProjectLogger._configured:
                logging.basicConfig(level=logging.INFO)
                ProjectLogger._configured = True
            self.logger: logging.Logger = logging.getLogger(name)

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
        default_log_file: str = "logs/app.log",
        app_name: str | None = None,
        file_logging: bool | None = None,
    ) -> None:
        """설정 파일(logging.yml, config.yml 등)을 기반으로 전체 로깅 환경을 일괄 초기화합니다.

        :param config_dir: 커스텀 설정 디렉토리 경로 (선택)
        :param default_log_file: 기본 로그 파일 경로 (선택)
        :param app_name: 애플리케이션 명칭 (로그 파일명 {app_name} 치환용)
        :param file_logging: 로그 파일 생성 활성화 여부 (True: 파일 저장, False: 콘솔만 출력, None: config.yml logging.file_logging 설정 준용)
        """
        import sys
        from agent_common.config_loader import ConfigLoader

        if not app_name:
            app_name = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else "app"

        loader = ConfigLoader(config_dir=config_dir)
        log_level_setting: Any = loader.setting("logging.level", "INFO")

        # logging.level이 dict/ReadOnlyConfig (프로그램별 레벨 설정)인 경우 app_name 매칭
        log_level_str: str = "INFO"
        if isinstance(log_level_setting, dict) or hasattr(log_level_setting, "items") or hasattr(log_level_setting, "get"):
            lvl_dict: dict[str, Any] = (
                dict(log_level_setting)
                if not isinstance(log_level_setting, dict)
                else log_level_setting
            )
            cand_keys_list: list[str] = [
                str(app_name).strip().lower().replace("-", "_"),
            ]
            if sys.argv and sys.argv[0]:
                cand_keys_list.append(Path(sys.argv[0]).stem.lower().replace("-", "_"))

            found_lvl_any: Any = None
            for cand_key_str in cand_keys_list:
                for k_any, v_any in lvl_dict.items():
                    if str(k_any).strip().lower().replace("-", "_") == cand_key_str:
                        found_lvl_any = v_any
                        break
                if found_lvl_any is not None:
                    break

            if found_lvl_any is None:
                found_lvl_any = lvl_dict.get("default", "INFO")
            log_level_str = str(found_lvl_any)
        else:
            log_level_str = str(log_level_setting)

        log_format = loader.setting(
            "logging.format",
            "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d %(funcName)s()] %(message)s",
        )
        datefmt = loader.setting("logging.datefmt", "%Y-%m-%d %H:%M:%S")

        level = getattr(logging, str(log_level_str).upper(), logging.INFO)

        formatter = SingleLineFlattenFormatter(log_format, datefmt=datefmt)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers: list[logging.Handler] = [console_handler]

        # 로그 파일 생성 활성화 여부 결정 (CLI 파라미터 우선 -> config.yml logging.file_logging -> 기본값 True)
        file_logging_enabled: bool = (
            file_logging
            if file_logging is not None
            else bool(loader.setting("logging.file_logging", True))
        )

        log_file = loader.setting("logging.file", default_log_file)
        out_file = loader.setting("logging.out_file")
        debug_file = loader.setting("logging.debug_file")

        # 설정된 logging.level 기반 파일 저장 경로 결정
        # logging.level이 ERROR 이상(ERROR, CRITICAL)인 경우 out_file 경로 사용
        # logging.level이 WARNING 이하(DEBUG, INFO, WARNING)인 경우 debug_file 경로 사용
        target_log_file: str | None = None
        if level >= logging.ERROR and out_file:
            target_log_file = out_file
        elif level <= logging.WARNING and debug_file:
            target_log_file = debug_file
        elif log_file:
            target_log_file = log_file

        if file_logging_enabled and target_log_file:
            from datetime import datetime

            today_dt: datetime = datetime.now()
            target_log_str: str = str(target_log_file)
            if "{app_name}" in target_log_str:
                target_log_str = target_log_str.format(app_name=app_name)
            dynamic_log_path: Path = Path(today_dt.strftime(target_log_str))
            log_file_path: Path = loader.project_path(dynamic_log_path)
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
            format=log_format,
            handlers=handlers,
            force=True,
        )
        logging.getLogger("metricflow").setLevel(logging.WARNING)
        logging.getLogger("metricflow_semantics").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        ProjectLogger._configured = True

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
        """logging_messages.yml 파일에 정의된 로그 레벨(level_str)과 메시지 코드(msg_code_str) 템플릿을 포매팅하여 반환합니다.

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
        stacklevel_int: int = kwargs.pop("stacklevel", 2)
        msg_str: str = self.get_log_msg(level_str, msg_code_str, default_str=default_str, **kwargs)
        lvl_name_str: str = str(level_str).strip().upper()
        lvl_num_int: int = getattr(logging, lvl_name_str, logging.INFO)
        self.logger.log(lvl_num_int, msg_str, stacklevel=stacklevel_int)
        return msg_str

    def info(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """INFO 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("INFO", msg_or_code, default=default, **kwargs)
            self.logger.info(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.info(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

    def warning(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """WARNING 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("WARNING", msg_or_code, default=default, **kwargs)
            self.logger.warning(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.warning(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

    def error(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """ERROR 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.error(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.error(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

    def critical(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """CRITICAL 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("CRITICAL", msg_or_code, default=default, **kwargs)
            self.logger.critical(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.critical(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

    def debug(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """DEBUG 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("DEBUG", msg_or_code, default=default, **kwargs)
            self.logger.debug(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.debug(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

    def exception(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """예외 Traceback 정보와 함께 ERROR 레벨로 로그를 기록하고, 포매팅된 메시지를 반환합니다."""
        stacklevel = kwargs.pop("stacklevel", 2)
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.exception(msg, *args, stacklevel=stacklevel)
            return msg
        self.logger.exception(msg_or_code, *args, stacklevel=stacklevel, **kwargs)
        return str(msg_or_code)

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
