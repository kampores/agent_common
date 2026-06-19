# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""앱과 스크립트의 로깅 설정을 표준화하는 프로젝트 로깅 모듈입니다."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any


class ProjectLogger:
    """앱과 스크립트의 로깅 설정을 표준화하는 프로젝트 로깅 클래스.

    도메인 의미: 콘솔 및 디스크 파일 로그 핸들러를 정의하고,
    일자별로 격리되는 로그 디렉토리 생성 및 basicConfig 설정을 담당함.
    """

    # 중복 basicConfig 호출로 handler가 겹치지 않도록 로깅 초기화 여부를 기억한다.
    _configured = False

    @classmethod
    def configure(
        cls,
        setting: Callable[[str, Any], Any],
        project_path: Callable[[str | Path], Path],
        default_log_file: str | None = None,
    ) -> None:
        """설정 값을 기준으로 콘솔과 파일 로깅을 초기화한다.

        도메인 의미: 프로그램별 설정 또는 기본 파일 경로(default_log_file)를 바탕으로
        동적인 일자별 로그 파일 경로를 할당하여 로그 꼬임(섞임) 현상을 방지함.
        """
        level_name = str(setting("logging.level", "INFO")).upper()
        level = getattr(logging, level_name, logging.INFO)
        log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

        handlers: list[logging.Handler] = [logging.StreamHandler()]
        log_file = setting("logging.file", default_log_file)
        if log_file:
            from datetime import datetime

            # 설정 값에 포함된 날짜 포맷팅 지시자(예: %Y, %m, %d)를 오늘 날짜로 포맷팅하여 동적 경로를 구성한다.
            # 도메인 의미: 설정 파일의 표기 형식과 런타임에 실제 생성되는 파일 구조 간의 논리적 일치성을 보장
            today = datetime.now()
            dynamic_log_path = Path(today.strftime(str(log_file)))
            log_path = project_path(dynamic_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=handlers,
            force=True,
        )
        # 외부 서드파티 디버그성 로그가 과도하게 노출되는 것을 방지하기 위해 로거 레벨 조정
        logging.getLogger("metricflow").setLevel(logging.WARNING)
        logging.getLogger("metricflow_semantics").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """지정한 이름의 logger를 반환하고 필요하면 기본 로깅을 초기화한다."""
        if not cls._configured:
            logging.basicConfig(level=logging.INFO)
            cls._configured = True
        return logging.getLogger(name)

    @staticmethod
    def log_request_result(
        logger: logging.Logger,
        method: str,
        path: str,
        start_time: float,
        status_code: int | None = None,
        exc: Exception | None = None,
    ) -> None:
        """HTTP 요청 처리 시간과 성공/실패 여부를 일관된 포맷으로 로그에 남긴다.

        도메인 의미: 인라인 중복되던 요청 소요 시간 계산 및 로그 포맷을 일괄 수행하여 로깅의 일관성 보장.
        """
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
