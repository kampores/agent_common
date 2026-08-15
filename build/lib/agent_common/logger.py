# 작성일: 2026-08-08
# 설계자: 김유상
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
    ) -> None:
        """설정 파일(logging.yml 등)을 기반으로 전체 로깅 환경을 일괄 초기화합니다."""
        import sys
        from agent_common.config_loader import ConfigLoader

        if not app_name:
            app_name = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else "app"

        loader = ConfigLoader(config_dir=config_dir)
        log_level_str = loader.setting("logging.level", "INFO")
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

        if target_log_file:
            from datetime import datetime

            today = datetime.now()
            target_log_str = str(target_log_file)
            if "{app_name}" in target_log_str:
                target_log_str = target_log_str.format(app_name=app_name)
            dynamic_log_path = Path(today.strftime(target_log_str))
            log_path = loader.project_path(dynamic_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

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

    def get_log_msg(self, level: str, code: str, default: str = "", **kwargs: Any) -> str:
        """logging_messages.yml 파일에 정의된 로그 레벨(level)과 메시지 코드(code) 템플릿을 포매팅하여 반환합니다."""
        level_str = str(level).strip().upper()

        def _search_in_level(target_lvl: str) -> str | None:
            direct = self.config_loader.setting(f"logging_messages.{target_lvl}.{code}")
            if direct and isinstance(direct, str):
                return direct
            lvl_dict = self.config_loader.setting(f"logging_messages.{target_lvl}")
            if isinstance(lvl_dict, dict):
                for _, sub_val in lvl_dict.items():
                    if isinstance(sub_val, dict) and code in sub_val:
                        candidate = sub_val[code]
                        if isinstance(candidate, str):
                            return candidate
            return None

        template = _search_in_level(level_str)

        if not template:
            all_msgs = self.config_loader.setting("logging_messages")
            if isinstance(all_msgs, dict):
                for other_lvl in all_msgs.keys():
                    if str(other_lvl).upper() != level_str:
                        cand = _search_in_level(str(other_lvl).upper())
                        if cand:
                            template = cand
                            break

        if not template or not isinstance(template, str):
            template = default or code
        if kwargs:
            try:
                safe_kwargs = {
                    k: str(v).replace("{", "{{").replace("}", "}}") if isinstance(v, str) else v
                    for k, v in kwargs.items()
                }
                return template.format(**safe_kwargs)
            except Exception:
                kwargs_detail = " ".join(f"{k}={v}" for k, v in kwargs.items())
                return f"{template} [{kwargs_detail}]" if template != code else f"[FATAL][Fail-Fast] {code}: {kwargs_detail}"
        return str(template)

    def log_msg(
        self,
        level: str,
        code: str,
        default: str = "",
        **kwargs: Any,
    ) -> str:
        """코드 기반 메시지를 로거에 즉시 기록하고 완성된 메시지를 반환합니다."""
        msg = self.get_log_msg(level, code, default=default, **kwargs)
        lvl_name = str(level).strip().upper()
        if lvl_name == "DEBUG":
            self.debug(msg)
        elif lvl_name == "WARNING":
            self.warning(msg)
        elif lvl_name == "ERROR":
            self.error(msg)
        elif lvl_name == "CRITICAL":
            self.critical(msg)
        else:
            self.info(msg)
        return msg

    def info(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """INFO 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("INFO", msg_or_code, default=default, **kwargs)
            self.logger.info(msg, *args)
            return msg
        self.logger.info(msg_or_code, *args, **kwargs)
        return str(msg_or_code)

    def warning(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """WARNING 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("WARNING", msg_or_code, default=default, **kwargs)
            self.logger.warning(msg, *args)
            return msg
        self.logger.warning(msg_or_code, *args, **kwargs)
        return str(msg_or_code)

    def error(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """ERROR 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.error(msg, *args)
            return msg
        self.logger.error(msg_or_code, *args, **kwargs)
        return str(msg_or_code)

    def critical(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """CRITICAL 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("CRITICAL", msg_or_code, default=default, **kwargs)
            self.logger.critical(msg, *args)
            return msg
        self.logger.critical(msg_or_code, *args, **kwargs)
        return str(msg_or_code)

    def debug(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """DEBUG 레벨로 로그 및 일반 메시지를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("DEBUG", msg_or_code, default=default, **kwargs)
            self.logger.debug(msg, *args)
            return msg
        self.logger.debug(msg_or_code, *args, **kwargs)
        return str(msg_or_code)

    def exception(self, msg_or_code: Any, *args: Any, default: str = "", **kwargs: Any) -> str:
        """예외 Traceback 정보와 함께 ERROR 레벨로 로그를 기록하고, 포매팅된 메시지를 반환합니다."""
        if isinstance(msg_or_code, str):
            msg = self.get_log_msg("ERROR", msg_or_code, default=default, **kwargs)
            self.logger.exception(msg, *args)
            return msg
        self.logger.exception(msg_or_code, *args, **kwargs)
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
            )
        else:
            logger.info(
                "request_end method=%s path=%s status_code=%s elapsed_ms=%.2f",
                method,
                path,
                status_code,
                elapsed_ms,
            )


# 하위 호환성을 위한 별칭 함수
get_log_msg = ProjectLogger.get_log_msg
