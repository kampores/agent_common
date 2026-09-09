# 작성일: 2026-06-19
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""외부 LLM API 및 로컬 GGUF 모델을 통합 제어하여 범용 텍스트 생성을 수행하는 공용 LLM 클라이언트 모듈입니다."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_common.config_loader import ConfigLoader, ReadOnlyConfig, config
from agent_common.logger import ProjectLogger

# ==============================================================================
# LLM 클라이언트 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "llm": {
        "router_model_str": "groq_gpt_oss",
        "sql_generator_model_str": "openai_gpt4o",
        "system_prompt_str": "You are a helpful AI assistant.",
        "default_purpose_str": "sql_generator",
    },
    "llm_pool": {},
}

# 로컬 GGUF 모델들의 캐시 딕셔너리. 파일 경로를 키로 하고 Llama 객체를 값으로 갖는다.
_LOCAL_LLMS_DICT: dict[str, Any] = {}

# 전역 설정 객체(config)에 LLM 모듈 기본 스키마 자동 등록
if hasattr(config, "_source") and isinstance(config._source, ConfigLoader):
    config._source.register_schema(APP_DEFAULT_SCHEMA_DICT)


class LlmInferenceError(Exception):
    """LLM 추론 또는 호출 과정 중 예외 상황이 발생했을 때 나타내는 예외 클래스입니다.

    도메인 의미: API 키 미설정, 타임아웃, 모델 로드 실패, 서버 측 HTTP 오류 등
    LLM 추론 실패 전반에 적용됩니다.
    """
    pass


class LlmClient:
    """외부 OpenAI 호환 API, Fabrix API 및 로컬 GGUF 모델을 지원하는 공용 LLM 클라이언트 클래스입니다.

    llmpool.yml 설정 풀로부터 지정된 모델 속성을 읽어와 설정 상태를 바인딩하고 추론을 처리합니다.
    """

    # 마지막 추론 생성에 실제로 사용된 LLM 경로 종류 ("external_llm" 또는 "local_llm")
    last_generated_by_str: str | None

    # 이 인스턴스가 담당하는 LLM의 작동 목적을 의미한다. ("sql_generator" 또는 "router" 등)
    purpose_str: str

    # config/llmpool.yml에 정의된 풀(Pool) 내의 고유한 LLM 프로필 모델 명칭이다.
    model_name_str: str

    def __init__(
        self,
        model_name_str: str | None = None,
        purpose_str: str | None = None,
        config_dir_path: str | Path | None = None,
    ) -> None:
        """설정 풀로부터 특정 모델명 또는 용도에 맞는 LLM 세부 사양을 로드하여 인스턴스를 초기화합니다.

        :param model_name_str: llmpool.yml 설정 풀에 정의된 고유한 LLM 프로필 모델 명칭.
        :param purpose_str: LLM 사용 용도 구분자 ("sql_generator", "router" 등).
        :param config_dir_path: 설정 파일들이 위치한 디렉토리 경로 (옵션).
        """
        self.last_generated_by_str = None
        self.purpose_str: str = purpose_str or config.llm.default_purpose_str
        self.logger: ProjectLogger = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # self 객체 내에 독립적인 ConfigLoader 인스턴스를 바인딩하고 스키마 등록
        self.config_loader: ConfigLoader = ConfigLoader(config_dir=config_dir_path)
        self.config_loader.register_schema(APP_DEFAULT_SCHEMA_DICT)

        if model_name_str:
            self.model_name_str = model_name_str
        else:
            if self.purpose_str == "router":
                self.model_name_str = config.llm.router_model_str
            else:
                self.model_name_str = config.llm.sql_generator_model_str

        # llmpool.yml 내 모델 설정 존재 여부 확인 (Fail-Fast)
        pool_config_any = self.config_loader.setting(f"llm_pool.{self.model_name_str}")
        if not pool_config_any and self.model_name_str not in config.llm_pool:
            raise LlmInferenceError(self.logger.error("config_load_failed", error=f"llmpool.yml 내 '{self.model_name_str}' 모델 설정이 누락되었습니다."))

    @property
    def model_config(self) -> ReadOnlyConfig:
        """현재 인스턴스가 참조하는 모델의 읽기 전용 설정을 반환합니다.

        :return: 해당 LLM 모델의 ReadOnlyConfig 설정 객체
        """
        pool_config_any = self.config_loader.setting(f"llm_pool.{self.model_name_str}")
        if isinstance(pool_config_any, dict):
            return ReadOnlyConfig(pool_config_any, source_name_str="llmpool.yml")
        if isinstance(pool_config_any, ReadOnlyConfig):
            return pool_config_any
        return config.llm_pool[self.model_name_str]

    def generate(
        self,
        prompt_str: str = "",
        system_prompt_str: str | None = None,
    ) -> str | None:
        """설정된 provider 우선순위에 따라 외부 또는 로컬 LLM에 텍스트 생성을 요청합니다.

        :param prompt_str: LLM에 전달할 사용자 프롬프트 문자열
        :param system_prompt_str: 시스템 지침 프롬프트 (미지정 시 설정 기본값 적용)
        :return: 생성된 텍스트 응답 문자열 (실패 시 None)
        :raises LlmInferenceError: 지원되지 않는 provider 설정이거나 API 통신 장애 발생 시
        """
        self.last_generated_by_str = None

        provider_env_str: str | None = os.getenv("LLM_PROVIDER")
        provider_str: str = (provider_env_str or self.model_config.provider_str).lower()
        if provider_str not in {"auto", "external", "local"}:
            raise LlmInferenceError(self.logger.error("config_load_failed", error=f"지원하지 않는 LLM_PROVIDER 설정입니다: {provider_str}"))

        # 시스템 프롬프트가 제공되지 않은 경우 설정 파일에서 기본 시스템 지침을 로드한다.
        resolved_system_prompt_str: str = system_prompt_str if system_prompt_str is not None else config.llm.system_prompt_str

        if provider_str in {"auto", "external"}:
            external_res_str = self._generate_external(prompt_str, resolved_system_prompt_str)
            if external_res_str is not None:
                self.last_generated_by_str = "external_llm"
                return external_res_str
            if provider_str == "external":
                return None

        if provider_str in {"auto", "local"}:
            local_res_str = self._generate_local(prompt_str, resolved_system_prompt_str)
            if local_res_str is not None:
                self.last_generated_by_str = "local_llm"
                return local_res_str

        return None

    def _generate_external(self, prompt_str: str, system_prompt_str: str | None = None) -> str | None:
        """OpenAI 호환 chat/completions API로 텍스트 생성을 요청합니다.

        :param prompt_str: LLM에 전달할 사용자 프롬프트 문자열
        :param system_prompt_str: 시스템 지침 프롬프트
        :return: 생성된 텍스트 응답 문자열 (실패 시 None)
        :raises LlmInferenceError: HTTP 오류, 네트워크 장애 또는 응답 파싱 실패 시 발생
        """
        enabled_bool: bool = self._external_llm_enabled()
        api_key_str: str | None = self._external_api_key()

        self.logger.info(
            "api_call_started",
            service_name="외부 LLM API",
            purpose=self.purpose_str,
            model_name=self.model_name_str,
        )

        if not enabled_bool:
            self.logger.warning("api_disabled", service_name="외부 LLM API")
            return None
        if not api_key_str:
            self.logger.warning("api_key_missing", service_name="외부 LLM API", api_key_env=self.model_config.api_key_env_str)
            return None

        resolved_system_prompt_str: str = system_prompt_str if system_prompt_str is not None else config.llm.system_prompt_str

        # Fabrix 전용 API 형식 처리
        if getattr(self.model_config, "api_format_str", "standard") == "fabrix_api":
            return self._generate_fabrix(prompt_str, resolved_system_prompt_str)

        # 표준 OpenAI 호환 API 형식 처리
        base_url_str: str = os.getenv("EXTERNAL_LLM_BASE_URL", self.model_config.base_url_str).rstrip("/")
        endpoint_str: str = os.getenv("EXTERNAL_LLM_CHAT_COMPLETIONS_PATH", self.model_config.chat_completions_path_str)
        url_str: str = f"{base_url_str}{endpoint_str if endpoint_str.startswith('/') else '/' + endpoint_str}"

        max_tokens_env_str: str | None = os.getenv("EXTERNAL_LLM_MAX_TOKENS")
        max_tokens_int: int = int(max_tokens_env_str) if max_tokens_env_str is not None else self.model_config.max_tokens_int

        temperature_env_str: str | None = os.getenv("EXTERNAL_LLM_TEMPERATURE")
        temperature_float: float = float(temperature_env_str) if temperature_env_str is not None else self.model_config.temperature_float

        payload_dict: dict[str, Any] = {
            "model": os.getenv("EXTERNAL_LLM_MODEL", self.model_config.model_str),
            "messages": [
                {
                    "role": "system",
                    "content": resolved_system_prompt_str,
                },
                {"role": "user", "content": prompt_str},
            ],
            "max_tokens": max_tokens_int,
            "temperature": temperature_float,
        }
        request_obj = Request(
            url_str,
            data=json.dumps(payload_dict, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key_str}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )
        timeout_env_str: str | None = os.getenv("EXTERNAL_LLM_TIMEOUT_SECONDS")
        timeout_seconds_int: int = int(timeout_env_str) if timeout_env_str is not None else self.model_config.timeout_seconds_int
        try:
            with urlopen(request_obj, timeout=timeout_seconds_int) as response:
                data_dict = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body_str = exc.read().decode("utf-8", errors="replace").replace("\n", " ").replace("\r", " ")
            raise LlmInferenceError(self.logger.error("api_http_error", service_name="외부 LLM API", code=exc.code, detail=body_str)) from exc
        except URLError as exc:
            raise LlmInferenceError(self.logger.error("api_connection_error", service_name="외부 LLM API", detail=str(exc.reason))) from exc

        try:
            content_str = data_dict["choices"][0]["message"]["content"]
            content_flat_str = str(content_str).replace("\n", " ").replace("\r", "")
            self.logger.info("api_call_success", service_name="외부 LLM API", detail=content_flat_str)
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmInferenceError(self.logger.error("api_missing_field", service_name="외부 LLM API", field_name="choices[0].message.content")) from exc

        return str(content_str)

    def _generate_fabrix(self, prompt_str: str, system_prompt_str: str | None = None) -> str | None:
        """Fabrix GenAI 허브 전용 API로 텍스트 생성을 요청합니다.

        :param prompt_str: LLM에 전달할 사용자 프롬프트 문자열
        :param system_prompt_str: 시스템 지침 프롬프트
        :return: 생성된 텍스트 응답 문자열 (실패 시 None)
        :raises LlmInferenceError: HTTP 오류, 네트워크 장애 또는 필드 누락 시 발생
        """
        enabled_bool: bool = self._external_llm_enabled()
        # 외부 API 키 조회 (x-openapi-token)
        api_key_str: str | None = self._external_api_key()
        url_str: str = self.model_config.base_url_str.rstrip("/")

        llm_id_env_str: str | None = os.getenv("FABRIX_LLM_ID")
        llm_id_int: int = int(llm_id_env_str) if llm_id_env_str is not None else self.model_config.llm_id_int

        client_env_key_str: str = getattr(self.model_config, "client_env_str", "")
        user_env_key_str: str = getattr(self.model_config, "user_env_str", "")
        client_key_str: str = os.getenv(client_env_key_str, "") if client_env_key_str else ""
        user_email_str: str = os.getenv(user_env_key_str, "") if user_env_key_str else ""

        self.logger.info(
            "api_call_started",
            service_name="Fabrix API",
            purpose=self.purpose_str,
            model_name=self.model_name_str,
        )

        if not enabled_bool:
            self.logger.warning("api_disabled", service_name="Fabrix API")
            return None
        if not api_key_str:
            self.logger.warning("api_key_missing", service_name="Fabrix API", api_key_env=self.model_config.api_key_env_str)
            return None

        resolved_system_prompt_str: str = system_prompt_str if system_prompt_str is not None else config.llm.system_prompt_str

        # Fabrix API는 contents 배열에 메시지를 전달한다.
        default_system_prompt_str = config.llm.system_prompt_str
        if resolved_system_prompt_str and resolved_system_prompt_str != default_system_prompt_str:
            contents_list = [f"{resolved_system_prompt_str}\n\n{prompt_str}"]
        else:
            contents_list = [prompt_str]

        payload_dict: dict[str, Any] = {
            "llmId": llm_id_int,
            "contents": contents_list,
            "isStream": "False",
        }

        request_obj = Request(
            url_str,
            data=json.dumps(payload_dict, ensure_ascii=False).encode("utf-8"),
            headers={
                "x-openapi-token": api_key_str,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        # 추가 인증 헤더 (client_key, user_email이 설정된 경우)
        if client_key_str:
            request_obj.add_header("x-generative-ai-client", client_key_str)
        if user_email_str:
            request_obj.add_header("x-client-user", user_email_str)

        timeout_env_str: str | None = os.getenv("FABRIX_TIMEOUT_SECONDS")
        timeout_seconds_int: int = int(timeout_env_str) if timeout_env_str is not None else self.model_config.timeout_seconds_int
        try:
            with urlopen(request_obj, timeout=timeout_seconds_int) as response:
                data_dict = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body_str = exc.read().decode("utf-8", errors="replace").replace("\n", " ").replace("\r", " ")
            raise LlmInferenceError(self.logger.error("api_http_error", service_name="Fabrix API", code=exc.code, detail=body_str)) from exc
        except URLError as exc:
            raise LlmInferenceError(self.logger.error("api_connection_error", service_name="Fabrix API", detail=str(exc.reason))) from exc

        # Fabrix API 응답 형식: 최상위 content 필드
        try:
            content_str = data_dict["content"]
            content_flat_str = str(content_str).replace("\n", " ").replace("\r", "")
            self.logger.info("api_call_success", service_name="Fabrix API", detail=content_flat_str)
        except (KeyError, TypeError) as exc:
            raise LlmInferenceError(self.logger.error("api_missing_field", service_name="Fabrix API", field_name="content")) from exc

        return str(content_str)

    def _generate_local(self, prompt_str: str, system_prompt_str: str | None = None) -> str | None:
        """설정된 GGUF 모델이 있으면 llama-cpp-python으로 텍스트 생성을 요청합니다.

        :param prompt_str: LLM에 전달할 사용자 프롬프트 문자열
        :param system_prompt_str: 시스템 지침 프롬프트
        :return: 생성된 텍스트 응답 문자열 (모델 미발견 시 None)
        """
        model_path_str: str = os.getenv("LOCAL_LLM_MODEL_PATH", self.model_config.model_path_str)
        resolved_model_path = self.config_loader.project_path(model_path_str)
        if not resolved_model_path.exists():
            return None

        resolved_system_prompt_str: str = system_prompt_str if system_prompt_str is not None else config.llm.system_prompt_str

        n_ctx_env_str: str | None = os.getenv("LOCAL_LLM_N_CTX")
        n_ctx_int: int = int(n_ctx_env_str) if n_ctx_env_str is not None else self.model_config.n_ctx_int

        n_threads_env_str: str | None = os.getenv("LOCAL_LLM_N_THREADS")
        n_threads_int: int = int(n_threads_env_str) if n_threads_env_str is not None else self.model_config.n_threads_int

        n_batch_env_str: str | None = os.getenv("LOCAL_LLM_N_BATCH")
        n_batch_int: int = int(n_batch_env_str) if n_batch_env_str is not None else self.model_config.n_batch_int

        n_gpu_layers_env_str: str | None = os.getenv("LOCAL_LLM_N_GPU_LAYERS")
        n_gpu_layers_int: int = int(n_gpu_layers_env_str) if n_gpu_layers_env_str is not None else self.model_config.n_gpu_layers_int

        verbose_env_str: str | None = os.getenv("LOCAL_LLM_VERBOSE")
        verbose_bool: bool = (verbose_env_str.lower() == "true") if verbose_env_str is not None else self.model_config.verbose_bool

        llm_obj = _get_local_llm(
            model_path_str=str(resolved_model_path),
            n_ctx_int=n_ctx_int,
            n_threads_int=n_threads_int,
            n_batch_int=n_batch_int,
            n_gpu_layers_int=n_gpu_layers_int,
            verbose_bool=verbose_bool,
        )
        max_tokens_env_str: str | None = os.getenv("LOCAL_LLM_MAX_TOKENS")
        max_tokens_int: int = int(max_tokens_env_str) if max_tokens_env_str is not None else self.model_config.max_tokens_int

        temperature_env_str: str | None = os.getenv("LOCAL_LLM_TEMPERATURE")
        temperature_float: float = float(temperature_env_str) if temperature_env_str is not None else self.model_config.temperature_float

        output_dict = llm_obj.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": resolved_system_prompt_str,
                },
                {"role": "user", "content": prompt_str},
            ],
            max_tokens=max_tokens_int,
            temperature=temperature_float,
            stop=["\n\nQuestion:", "\n\nModel:"],
        )
        content_str = output_dict["choices"][0]["message"]["content"]

        return str(content_str)

    def _external_llm_enabled(self) -> bool:
        """설정과 환경변수를 기준으로 외부 LLM 사용 여부를 판단합니다.

        :return: 외부 LLM 활성화 여부 불리언 값
        """
        enabled_str = os.getenv("EXTERNAL_LLM_ENABLED")
        if enabled_str is not None:
            return enabled_str.lower() in {"1", "true", "yes", "on"}
        return self.model_config.enabled_bool

    def _external_api_key(self) -> str | None:
        """외부 LLM API key를 설정된 환경변수 이름에서 읽어옵니다.

        :return: 환경변수에 설정된 API 키 문자열 또는 None
        """
        return os.getenv(self.model_config.api_key_env_str) or os.getenv("EXTERNAL_LLM_API_KEY")


def _get_local_llm(
    model_path_str: str,
    n_ctx_int: int,
    n_threads_int: int,
    n_batch_int: int,
    n_gpu_layers_int: int,
    verbose_bool: bool
) -> Any:
    """GGUF 모델을 lazy-load하고 프로세스 안에서 재사용합니다.

    :param model_path_str: GGUF 모델 파일 경로 문자열
    :param n_ctx_int: 최대 컨텍스트 토큰 크기
    :param n_threads_int: CPU 멀티스레딩 스레드 수
    :param n_batch_int: 배치 토큰 크기
    :param n_gpu_layers_int: GPU 가속 레이어 수
    :param verbose_bool: 상세 디버그 로깅 활성화 여부
    :return: 초기화된 Llama 모델 인스턴스
    :raises LlmInferenceError: llama_cpp 모듈 미설치 또는 모델 파일 미존재 시 발생
    """
    global _LOCAL_LLMS_DICT
    if model_path_str in _LOCAL_LLMS_DICT:
        return _LOCAL_LLMS_DICT[model_path_str]

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        msg_str = ProjectLogger.get_log_msg("ERROR", "config_load_failed", error="llama-cpp-python 패키지가 설치되어 있지 않습니다.")
        raise LlmInferenceError(msg_str) from exc

    if not os.path.exists(model_path_str):
        msg_str = ProjectLogger.get_log_msg("ERROR", "config_file_not_found", path=model_path_str)
        raise LlmInferenceError(msg_str)

    _LOCAL_LLMS_DICT[model_path_str] = Llama(
        model_path=model_path_str,
        n_ctx=n_ctx_int,
        n_threads=n_threads_int,
        n_batch=n_batch_int,
        n_gpu_layers=n_gpu_layers_int,
        verbose=verbose_bool,
    )
    return _LOCAL_LLMS_DICT[model_path_str]
