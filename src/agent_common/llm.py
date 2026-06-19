# 작성일: 2026-06-19
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""외부 LLM API 및 로컬 GGUF 모델을 통합 제어하여 범용 텍스트 생성을 수행하는 공용 LLM 클라이언트 모듈입니다."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_common.config_loader import project_path, setting

# 로컬 GGUF 모델들의 캐시 딕셔너리. 파일 경로를 키로 하고 Llama 객체를 값으로 갖는다.
_LOCAL_LLMS: dict[str, Any] = {}

# 로깅 객체 생성
logger = logging.getLogger("agent_common.llm")


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
    last_generated_by: str | None

    # 이 인스턴스가 담당하는 LLM의 작동 목적을 의미한다. ("sql_generator" 또는 "router" 등)
    purpose: str

    # config/llmpool.yml에 정의된 풀(Pool) 내의 고유한 LLM 프로필 모델 명칭이다.
    model_name: str

    # LLM 모델을 제공하는 방식이다. ("local" 또는 "external")
    provider: str

    # 외부 LLM API 활성화 여부를 나타낸다. (True인 경우에만 외부 API 전송 허용)
    enabled: bool

    # 외부 API 호출 시 활용할 환경변수 기반 인증 키 이름이다. (예: "GROQ_API_KEY")
    api_key_env: str

    # 외부 LLM API 요청을 보낼 기본 접속 도메인 및 base 경로이다.
    base_url: str

    # 외부 LLM API의 세부 채팅 엔드포인트 리소스 경로이다. (기본값: "/chat/completions")
    chat_completions_path: str

    # API 요청 형식이다. ("standard": OpenAI 호환, "fabrix_api": Fabrix 전용 형식)
    api_format: str

    # 호출 대상 외부 LLM 모델의 식별 명칭이다. (예: "openai/gpt-oss-120b")
    model: str

    # Fabrix API 전용 LLM 식별자 (integer, standard API에서는 미사용)
    llm_id: int

    # Fabrix API 전용 인증 환경변수 이름 (x-generative-ai-client)
    client_env: str

    # Fabrix API 전용 인증 환경변수 이름 (x-client-user)
    user_env: str
    
    # 외부 API 서버 응답 지연을 방지하기 위한 최대 커넥션 타임아웃 제한 시간(초)이다. (범위: 1 ~ 300)
    timeout_seconds: int

    # LLM 추론 시 생성할 출력 텍스트의 최대 토큰 수이다. (범위: 1 ~ 4096)
    max_tokens: int

    # LLM 답변의 다양성 및 창의성 수준을 결정하는 값이다.
    temperature: float

    # 로컬 CPU/GPU 추론 엔진 작동 시 참조할 GGUF 모델 파일의 프로젝트 내 상대 경로이다.
    model_path: str

    # 로컬 추론 시 입력 프롬프트와 생성 답변을 포괄하는 최대 컨텍스트 윈도우 토큰 용량이다.
    n_ctx: int

    # 로컬 CPU 추론 속도 최적화를 위해 점유할 멀티스레딩 개수이다. (실제 CPU 코어 수에 준해 조절)
    n_threads: int

    # 로컬 LLM 프롬프트 토큰 분석 시의 처리 배치 크기이다. (범위: 1 ~ 512)
    n_batch: int

    # 로컬 GPU 연산 가속을 위해 VRAM에 올릴 모델 가중치 레이어 개수이다. (0은 CPU 단독 실행)
    n_gpu_layers: int

    # llama.cpp의 디버그용 및 최적화 분석용 텍스트 상세 로그 출력 여부이다.
    verbose: bool

    def __init__(self, model_name: str | None = None, purpose: str | None = None) -> None:
        """설정 풀로부터 특정 모델명 또는 용도에 맞는 LLM 세부 사양을 로드하여 인스턴스를 초기화한다.

        Args:
            model_name: llmpool.yml 설정 풀에 정의된 고유한 LLM 프로필 모델 명칭.
            purpose: LLM 사용 용도 구분자 ("sql_generator", "router" 등).
                     model_name이 주어지지 않고 purpose가 주어지면, 설정의 llm.router_model 혹은 llm.sql_generator_model에서 model_name을 결정합니다.
        """
        self.last_generated_by = None
        self.purpose = purpose or "sql_generator"

        if model_name:
            self.model_name = model_name
        else:
            if self.purpose == "router":
                self.model_name = str(setting("llm.router_model", "groq_gpt_oss"))
            else:
                self.model_name = str(setting("llm.sql_generator_model", "openai_gpt4o"))

        # llmpool.yml의 상세 설정을 로드한다.
        pool_config = setting(f"llm_pool.{self.model_name}", {})
        if not pool_config:
            raise LlmInferenceError(f"LLM pool model '{self.model_name}' is not defined in llmpool.yml.")

        # 설정 항목들을 객체 변수로 바인딩한다.
        self.provider = str(pool_config.get("provider", "external")).lower()
        self.enabled = bool(pool_config.get("enabled", True))
        self.api_key_env = str(pool_config.get("api_key_env", "EXTERNAL_LLM_API_KEY"))
        self.base_url = str(pool_config.get("base_url", ""))
        self.chat_completions_path = str(pool_config.get("chat_completions_path", "/chat/completions"))
        self.api_format = str(pool_config.get("api_format", "standard")).lower()
        self.model = str(pool_config.get("model", ""))
        self.llm_id = int(pool_config.get("llm_id", 0))
        self.client_env = str(pool_config.get("client_env", ""))
        self.user_env = str(pool_config.get("user_env", ""))
        self.timeout_seconds = int(pool_config.get("timeout_seconds", 60))
        self.max_tokens = int(pool_config.get("max_tokens", 512))
        self.temperature = float(pool_config.get("temperature", 0))
        self.model_path = str(pool_config.get("model_path", ""))
        self.n_ctx = int(pool_config.get("n_ctx", 4096))
        self.n_threads = int(pool_config.get("n_threads", 12))
        self.n_batch = int(pool_config.get("n_batch", 512))
        self.n_gpu_layers = int(pool_config.get("n_gpu_layers", 0))
        self.verbose = bool(pool_config.get("verbose", False))

    def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """설정된 provider 우선순위에 따라 외부 또는 로컬 LLM에 텍스트 생성을 요청한다.

        system_prompt가 주어지면 기본 시스템 지침 대신 해당 지침을 사용한다.
        """
        self.last_generated_by = None
        provider = os.getenv("LLM_PROVIDER", self.provider).lower()
        if provider not in {"auto", "external", "local"}:
            raise LlmInferenceError(f"Unsupported LLM_PROVIDER: {provider}")

        # 시스템 프롬프트가 제공되지 않은 경우 설정 파일에서 적절한 기본 시스템 지침을 로드한다.
        if system_prompt is None:
            if self.purpose == "router":
                system_prompt = str(setting("prompts.routing_system_prompt") or setting("llm.routing_system_prompt"))
            else:
                system_prompt = str(setting("prompts.system_prompt") or setting("llm.system_prompt"))

        if provider in {"auto", "external"}:
            external_res = self._generate_external(prompt, system_prompt)
            if external_res is not None:
                self.last_generated_by = "external_llm"
                return external_res
            if provider == "external":
                return None

        if provider in {"auto", "local"}:
            local_res = self._generate_local(prompt, system_prompt)
            if local_res is not None:
                self.last_generated_by = "local_llm"
                return local_res

        return None

    def _generate_external(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """OpenAI 호환 chat/completions API로 텍스트 생성을 요청한다."""
        enabled = self._external_llm_enabled()
        api_key = self._external_api_key()

        logger.info(
            "[LlmClient] _generate_external 호출됨. purpose=%s, model_name=%s, enabled=%s, has_api_key=%s",
            self.purpose,
            self.model_name,
            enabled,
            bool(api_key),
        )

        if not enabled:
            logger.warning("[LlmClient] 외부 LLM 사용이 비활성화 상태입니다. (enabled=False)")
            return None
        if not api_key:
            logger.warning("[LlmClient] 외부 LLM API Key가 설정되어 있지 않습니다. api_key_env=%s", self.api_key_env)
            return None

        # system_prompt는 generate 메서드 단계에서 미리 보장되므로, 만약에 대비해 fallback만 둔다.
        if system_prompt is None:
            if self.purpose == "router":
                system_prompt = str(setting("prompts.routing_system_prompt") or setting("llm.routing_system_prompt"))
            else:
                system_prompt = str(setting("prompts.system_prompt") or setting("llm.system_prompt"))

        # Fabrix 전용 API 형식 처리
        if self.api_format == "fabrix_api":
            return self._generate_fabrix(prompt, system_prompt)

        # 표준 OpenAI 호환 API 형식 처리
        base_url = os.getenv("EXTERNAL_LLM_BASE_URL", self.base_url).rstrip("/")
        endpoint = os.getenv("EXTERNAL_LLM_CHAT_COMPLETIONS_PATH", self.chat_completions_path)
        url = f"{base_url}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
        payload = {
            "model": os.getenv("EXTERNAL_LLM_MODEL", self.model),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": int(os.getenv("EXTERNAL_LLM_MAX_TOKENS", str(self.max_tokens))),
            "temperature": float(os.getenv("EXTERNAL_LLM_TEMPERATURE", str(self.temperature))),
        }
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )
        timeout = int(os.getenv("EXTERNAL_LLM_TIMEOUT_SECONDS", str(self.timeout_seconds)))
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LlmInferenceError(f"External LLM request failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise LlmInferenceError(f"External LLM request failed: {exc.reason}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            logger.info("[LlmClient] External LLM API 응답 수집 성공. content: %s", content)
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmInferenceError(f"External LLM response did not contain choices[0].message.content: {data}") from exc

        return str(content)

    def _generate_fabrix(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """Fabrix(kbonecloud) GenAI 허브 전용 API로 텍스트 생성을 요청한다."""
        enabled = self._external_llm_enabled()
        # 외부 API 키 조회 (x-openapi-token)
        api_key = self._external_api_key()
        url = self.base_url.rstrip("/")
        llm_id = int(os.getenv("FABRIX_LLM_ID", str(self.llm_id)))
        client_key = os.getenv(self.client_env, "") if self.client_env else ""
        user_email = os.getenv(self.user_env, "") if self.user_env else ""
        
        logger.info(
            "[LlmClient] _generate_fabrix 호출됨. purpose=%s, model_name=%s, enabled=%s, has_api_key=%s",
            self.purpose,
            self.model_name,
            enabled,
            bool(api_key),
        )

        if not enabled:
            logger.warning("[LlmClient] 외부 LLM 사용이 비활성화 상태입니다. (enabled=False)")
            return None
        if not api_key:
            logger.warning("[LlmClient] 외부 LLM API Key가 설정되어 있지 않습니다. api_key_env=%s", self.api_key_env)
            return None

        # system_prompt는 generate 메서드 단계에서 미리 보장되므로, 만약에 대비해 fallback만 둔다.
        if system_prompt is None:
            if self.purpose == "router":
                system_prompt = str(setting("prompts.routing_system_prompt") or setting("llm.routing_system_prompt"))
            else:
                system_prompt = str(setting("prompts.system_prompt") or setting("llm.system_prompt"))

        # Fabrix API는 contents 배열에 메시지를 전달한다.
        default_system_prompt = str(setting("prompts.system_prompt") or setting("llm.system_prompt"))
        if system_prompt and system_prompt != default_system_prompt:
            contents = [f"{system_prompt}\n\n{prompt}"]
        else:
            contents = [prompt]

        payload = {
            "llmId": llm_id,
            "contents": contents,
            "isStream": "False",
        }

        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "x-openapi-token": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        # 추가 인증 헤더 (client_key, user_email이 설정된 경우)
        if client_key:
            request.add_header("x-generative-ai-client", client_key)
        if user_email:
            request.add_header("x-client-user", user_email)

        timeout = int(os.getenv("FABRIX_TIMEOUT_SECONDS", str(self.timeout_seconds)))
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LlmInferenceError(f"Fabrix API request failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise LlmInferenceError(f"Fabrix API response failed: {exc.reason}") from exc

        # Fabrix API 응답 형식: 최상위 content 필드
        try:
            content = data["content"]
            logger.info("[LlmClient] Fabrix API 응답 수집 성공. content: %s", content)
        except (KeyError, TypeError) as exc:
            raise LlmInferenceError(f"Fabrix API 응답에 'content' 필드가 없습니다. : {data}") from exc

        return str(content)

    def _generate_local(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """설정된 GGUF 모델이 있으면 llama-cpp-python으로 텍스트 생성을 요청한다."""
        model_path = os.getenv("LOCAL_LLM_MODEL_PATH", self.model_path)
        resolved_model_path = project_path(model_path)
        if not resolved_model_path.exists():
            return None

        # system_prompt는 generate 메서드 단계에서 미리 보장되므로, 만약에 대비해 fallback만 둔다.
        if system_prompt is None:
            if self.purpose == "router":
                system_prompt = str(setting("prompts.routing_system_prompt") or setting("llm.routing_system_prompt"))
            else:
                system_prompt = str(setting("prompts.system_prompt") or setting("llm.system_prompt"))

        n_ctx = int(os.getenv("LOCAL_LLM_N_CTX", str(self.n_ctx)))
        n_threads = int(os.getenv("LOCAL_LLM_N_THREADS", str(self.n_threads)))
        n_batch = int(os.getenv("LOCAL_LLM_N_BATCH", str(self.n_batch)))
        n_gpu_layers = int(os.getenv("LOCAL_LLM_N_GPU_LAYERS", str(self.n_gpu_layers)))
        verbose = os.getenv("LOCAL_LLM_VERBOSE", str(self.verbose)).lower() == "true"

        llm = _get_local_llm(
            model_path=str(resolved_model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
        )
        output = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=int(os.getenv("LOCAL_LLM_MAX_TOKENS", str(self.max_tokens))),
            temperature=float(os.getenv("LOCAL_LLM_TEMPERATURE", str(self.temperature))),
            stop=["\n\nQuestion:", "\n\nModel:"],
        )
        content = output["choices"][0]["message"]["content"]

        return str(content)

    def _external_llm_enabled(self) -> bool:
        """설정과 환경변수를 기준으로 외부 LLM 사용 여부를 판단한다."""
        enabled = os.getenv("EXTERNAL_LLM_ENABLED", str(self.enabled)).lower()
        return enabled in {"1", "true", "yes", "on"}

    def _external_api_key(self) -> str | None:
        """외부 LLM API key를 설정된 환경변수 이름에서 읽어온다."""
        return os.getenv(self.api_key_env) or os.getenv("EXTERNAL_LLM_API_KEY")


def _get_local_llm(
    model_path: str,
    n_ctx: int,
    n_threads: int,
    n_batch: int,
    n_gpu_layers: int,
    verbose: bool
) -> Any:
    """GGUF 모델을 lazy-load하고 프로세스 안에서 재사용한다."""
    global _LOCAL_LLMS
    if model_path in _LOCAL_LLMS:
        return _LOCAL_LLMS[model_path]

    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise LlmInferenceError(
            "LOCAL_LLM_MODEL_PATH is set, but llama-cpp-python is not installed."
        ) from exc

    if not os.path.exists(model_path):
        raise LlmInferenceError(f"Local LLM model file does not exist: {model_path}")

    _LOCAL_LLMS[model_path] = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_batch=n_batch,
        n_gpu_layers=n_gpu_layers,
        verbose=verbose,
    )
    return _LOCAL_LLMS[model_path]
