# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""공통 예외 처리 및 에러 변환을 수행하는 모듈입니다."""

from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("agent_common.error_handler")


class ErrorHandler:
    """공통 예외 처리 및 로깅을 담당하는 클래스.

    도메인 의미: 애플리케이션 전반에서 발생하는 비즈니스/시스템 예외를 중앙 집중적으로 핸들링하며,
    FastAPI의 전역 에러 응답 변환과 SQL 가공 및 네트워크 통신 예외 로깅을 통일되게 수행함.
    """

    @staticmethod
    def handle_sql_error(exc: Exception, sql: str, context: str) -> str:
        """SQL 구문 해석 및 변환 중 발생한 예외를 로깅하고 원본 SQL을 안전하게 반환한다.

        Args:
            exc: 발생한 구문 오류 또는 파싱 예외 객체
            sql: 가공 및 최적화 대상이었던 원본 SQL 문자열
            context: 어떤 작업(예: 한글화, 평탄화) 중 실패했는지 식별할 수 있는 문맥 설명

        Returns:
            str: 오류 발생 시 가용한 최후의 보루인 원본 SQL 문자열을 그대로 반환
        """
        logger.warning(
            "%s 중 예외가 발생하여 원본 SQL을 폴백 반환합니다. 오류 내용: %s. 원본 SQL:\n%s",
            context,
            exc,
            sql,
        )
        return sql

    @staticmethod
    def handle_network_error(exc: Exception, context: str) -> None:
        """LLM 통신 및 외부 API 연동 중 발생한 예외에 대해 경고 로그를 기록한다.

        Args:
            exc: 네트워크, 타임아웃 또는 JSON 디코딩 실패 예외 객체
            context: 예외가 발생한 구체적인 비즈니스 호출 맥락 정보
        """
        logger.warning("%s 호출 중 예외가 발생했습니다. 오류 메시지: %s", context, exc)

    @staticmethod
    def handle_db_connection_error(exc: Exception, db_path: Any, custom_logger: logging.Logger | None = None) -> None:
        """데이터베이스 연결 실패 시 파일 잠금(Lock) 가능성 등의 도메인 원인을 식별하여 한글로 로깅한다.

        Args:
            exc: 발생한 데이터베이스 연결/IO 관련 예외 객체
            db_path: 연결을 시도한 데이터베이스 파일 경로
            custom_logger: 호출한 프로그램의 로거 인스턴스 (없으면 기본 에러 핸들러 로거 사용)
        """
        active_logger = custom_logger if custom_logger is not None else logger
        active_logger.error(
            "데이터베이스 연결에 실패했습니다 (경로: %s). "
            "FastAPI 서버(Uvicorn)나 타 프로세스에서 해당 데이터베이스 파일을 잠금(Lock)하고 있을 수 있습니다. "
            "관련 세션 및 프로세스를 종료한 뒤 재시도 바랍니다. 상세 오류: %s",
            db_path,
            exc,
        )

    @staticmethod
    def handle_config_warning(key: str) -> None:
        """설정 파일에 필수 설정 항목이 누락되었을 때 경고 로그를 기록한다.

        Args:
            key: 누락된 설정 키 이름
        """
        logger.warning("설정(key: '%s') 항목이 존재하지 않습니다. 시스템 기본값으로 대체하여 기동합니다.", key)

    @classmethod
    def register_fastapi_handlers(cls, app: FastAPI) -> None:
        """FastAPI 애플리케이션에 대한 비즈니스 전역 예외 핸들러들을 일괄 등록한다.

        도메인 의미: 개별 API 라우터 함수 내에 존재하던 try-except 로직을 일괄 대체하여
        FastAPI가 예외 발생 시 자동으로 HTTP 상태 코드 및 정형화된 JSONResponse를 생성하게 함.
        (순환 참조 방지를 위해 대상 커스텀 예외 클래스들은 런타임에 동적으로 임포트함.)

        Args:
            app: 등록 대상인 FastAPI 애플리케이션 인스턴스
        """
        try:
            from app.exceptions import SqlGenerationError, MetricFlowError
        except ImportError:
            # test_main_agent 프로젝트에는 해당 커스텀 예외 클래스들이 없을 수 있으므로 핸들러 등록을 스킵합니다.
            return

        # 1. SQL 생성 실패 예외 핸들링 (유효성 검증 위반 등)
        @app.exception_handler(SqlGenerationError)
        async def sql_generation_error_handler(request: Request, exc: SqlGenerationError):
            err_msg = str(exc)
            # 모델을 전혀 읽지 못했을 때의 심각한 서버 에러
            if "No dbt models were loaded" in err_msg:
                logger.error("generate_sql_no_models - 서버 내부 오류 발생: %s", err_msg)
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Server Configuration Error: {err_msg}"},
                )
            
            # 일반적인 쿼리 생성 실패는 유효성 및 문법 경고로 처리 (HTTP 422)
            logger.warning("generate_sql_failed - SQL 생성 실패 경고: %s", err_msg)
            return JSONResponse(
                status_code=422,
                content={"detail": err_msg},
            )

        # 2. MetricFlow 처리 실패 예외 핸들링
        @app.exception_handler(MetricFlowError)
        async def metricflow_error_handler(request: Request, exc: MetricFlowError):
            err_msg = str(exc)
            logger.warning("metricflow_operation_failed - MetricFlow 처리 중 에러 발생: %s", err_msg)
            return JSONResponse(
                status_code=422,
                content={"detail": err_msg},
            )

        # 3. 입력값 형식 위반 및 잘못된 출력 디렉토리 예외 핸들링
        @app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            err_msg = str(exc)
            # 잘못된 디렉토리 쓰기 시도인 경우를 포함한 잘못된 인자 입력 (HTTP 400)
            logger.warning("invalid_argument_error - 입력값 형식 오류 발생: %s", err_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": err_msg},
            )
