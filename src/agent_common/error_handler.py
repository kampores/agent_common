# 작성일: 2026-06-18
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""공통 예외 처리 및 에러 변환을 수행하는 모듈입니다."""

from __future__ import annotations

from typing import Any, Callable, Optional

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
except ImportError:
    FastAPI = Any  # type: ignore
    Request = Any  # type: ignore
    JSONResponse = None  # type: ignore

from agent_common.logger import ProjectLogger


class _HybridMethod:
    """인스턴스 호출(instance.method())과 클래스 직접 호출(Class.method())을 모두 투명하게 지원하는 디스크립터."""

    def __init__(self, func: Callable) -> None:
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __get__(self, instance: Any, owner: type) -> Any:
        if instance is None:
            if getattr(owner, "_default_instance", None) is None:
                owner._default_instance = owner()
            return self.func.__get__(owner._default_instance, owner)
        return self.func.__get__(instance, owner)


class ErrorHandler:
    """공통 예외 처리 및 로깅을 담당하는 클래스.

    도메인 의미: 애플리케이션 전반에서 발생하는 비즈니스/시스템 예외를 중앙 집중적으로 핸들링하며,
    FastAPI의 전역 에러 응답 변환과 네트워크 통신 예외 로깅 및 설정 타입 보증 예외 처리를 통일되게 수행함.
    인스턴스 생성(self.logger 바인딩) 및 클래스 직접 호출(하위 호환)을 모두 지원합니다.
    """

    _default_instance: Optional[ErrorHandler] = None

    def __init__(self, logger: Optional[ProjectLogger] = None) -> None:
        """ErrorHandler 인스턴스를 초기화하며 self.logger를 바인딩합니다.

        :param logger: 커스텀 ProjectLogger 인스턴스 (선택, 기본값: 'agent_common.ErrorHandler' 로거 생성)
        """
        self.logger: ProjectLogger = (
            logger if logger is not None else ProjectLogger(f"agent_common.{self.__class__.__name__}")
        )




    @_HybridMethod
    def raise_coercion_error(
        self,
        key_str: str,
        val_any: Any,
        expected_type_str: str,
        guide_msg_str: str = "",
        cause_exc: Optional[Exception] = None,
        exc_cls: Optional[type[Exception]] = None,
    ) -> None:
        """설정값 타입 보증 실패 시 self.logger.exception()을 호출하여 로그를 기록하고 적합한 예외를 발생시킵니다 (Fail-Fast).

        원인 예외(cause_exc)의 종류(ValueError, TypeError 등)를 스마트하게 판별하여 동일한 예외 타입으로 승계하거나,
        명시적 exc_cls를 우선 발생시킵니다. 둘 다 없는 경우 최상위 Exception으로 발생시킵니다.

        :param key_str: 설정 키 문자열
        :param val_any: 변환에 실패한 원본 값
        :param expected_type_str: 기대된 타입 명칭 (예: '정수형(int)', '실수형(float)')
        :param guide_msg_str: 올바른 값 입력을 위한 사용자 안내 문구 (선택)
        :param cause_exc: 원인 예외 객체 (선택). 명시적 exc_cls가 없을 때 원인 예외의 타입을 자동 승계
        :param exc_cls: 명시적으로 발생시킬 예외 클래스 타입 (선택, 기본값: cause_exc 타입 또는 Exception)
        :raises Exception: 결정된 예외 인스턴스 발생
        """
        target_exc_cls: type[Exception]
        if exc_cls is not None:
            target_exc_cls = exc_cls
        elif cause_exc is not None:
            target_exc_cls = type(cause_exc)
        else:
            target_exc_cls = Exception

        current_type_str: str = type(val_any).__name__
        val_repr_str: str = repr(val_any)
        err_msg_str: str = self.logger.exception(
            "config_type_coercion_failed",
            key_str=key_str,
            expected_type=expected_type_str,
            guide_msg=guide_msg_str,
            val_any=val_repr_str,
            current_type=current_type_str,
        )
        if cause_exc:
            raise target_exc_cls(err_msg_str) from cause_exc
        raise target_exc_cls(err_msg_str)

    @_HybridMethod
    def register_fastapi_handlers(self, app: FastAPI) -> None:
        """FastAPI 애플리케이션에 대한 비즈니스 전역 예외 핸들러들을 일괄 등록한다.

        도메인 의미: 개별 API 라우터 함수 내에 존재하던 try-except 로직을 일괄 대체하여
        FastAPI가 예외 발생 시 자동으로 HTTP 상태 코드 및 정형화된 JSONResponse를 생성하게 함.
        (순환 참조 방지를 위해 대상 커스텀 예외 클래스들은 런타임에 동적으로 임포트함.)

        :param app: 등록 대상인 FastAPI 애플리케이션 인스턴스
        """
        if JSONResponse is None:
            self.logger.warning("fastapi 패키지가 설치되어 있지 않아 FastAPI 예외 핸들러를 등록할 수 없습니다.")
            return

        try:
            from app.exceptions import SqlGenerationError, MetricFlowError
        except ImportError:
            # test_main_agent 프로젝트에는 해당 커스텀 예외 클래스들이 없을 수 있으므로 핸들러 등록을 스킵합니다.
            return

        # 1. SQL 생성 실패 예외 핸들링 (유효성 검증 위반 등)
        @app.exception_handler(SqlGenerationError)
        async def sql_generation_error_handler(request: Request, exc: SqlGenerationError):
            err_msg = str(exc)
            # DBT모델을 전혀 읽지 못했을 때의 심각한 서버 에러
            if "No dbt models were loaded" in err_msg:
                self.logger.error("generate_sql_no_models - 서버 내부 오류 발생: %s", err_msg)
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Server Configuration Error: {err_msg}"},
                )
            
            # 일반적인 쿼리 생성 실패는 유효성 및 문법 경고로 처리 (HTTP 422)
            self.logger.warning("generate_sql_failed - SQL 생성 실패 경고: %s", err_msg)
            return JSONResponse(
                status_code=422,
                content={"detail": err_msg},
            )

        # 2. MetricFlow 처리 실패 예외 핸들링
        @app.exception_handler(MetricFlowError)
        async def metricflow_error_handler(request: Request, exc: MetricFlowError):
            err_msg = str(exc)
            self.logger.warning("metricflow_operation_failed - MetricFlow 처리 중 에러 발생: %s", err_msg)
            return JSONResponse(
                status_code=422,
                content={"detail": err_msg},
            )

        # 3. 입력값 형식 위반 및 잘못된 출력 디렉토리 예외 핸들링
        @app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            err_msg = str(exc)
            # 잘못된 디렉토리 쓰기 시도인 경우를 포함한 잘못된 인자 입력 (HTTP 400)
            self.logger.warning("invalid_argument_error - 입력값 형식 오류 발생: %s", err_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": err_msg},
            )


error_handler: ErrorHandler = ErrorHandler()
raise_coercion_error = error_handler.raise_coercion_error

__all__ = ["ErrorHandler", "error_handler", "raise_coercion_error"]
