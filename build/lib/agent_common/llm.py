# 작성일: 2026-06-22
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""llm_api 독립 서비스로 텍스트 생성을 위임하는 Proxy 역할의 공용 LLM 클라이언트 모듈입니다.

도메인 의미: 기존 LlmClient의 인터페이스 명세를 완전히 보존하면서, 
실제 LLM 추론 연산은 별도로 구동되는 llm_api 도커 컨테이너 서버에 HTTP 통신으로 요청하여 응답을 가져옵니다.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_common.config_loader import setting

# 로깅 설정
logger = logging.getLogger("agent_common.llm")


class LlmInferenceError(Exception):
    """LLM API 요청 처리 또는 연동 네트워크 상태 장애를 가리키는 예외 클래스입니다.

    도메인 의미: API 서버 미작동, HTTP 500 오류 응답, 네트워크 연결 지연 타임아웃 등의 예외 상황을 반영합니다.
    """
    pass


class LlmClient:
    """llm_api 컨테이너 서버를 향해 추론 요청을 프록시 전송하는 공용 LLM 클라이언트 클래스입니다.

    기존 클래스 명세(model_name, purpose, last_generated_by 등)를 유지하여
    기타 에이전트 서비스들이 코드 수정 없이 그대로 외부 서비스와 연동될 수 있도록 합니다.
    """

    # 마지막 추론 시 실제 사용된 LLM 리소스 명칭 (local_llm 또는 external_llm)
    last_generated_by: str | None

    # 이 인스턴스가 담당하는 LLM의 작동 목적 (sql_generator, router 등)
    purpose: str

    # config/llmpool.yml 설정 풀에 정의된 고유한 LLM 프로필 모델 명칭
    model_name: str

    # 호출할 llm_api 컨테이너의 텍스트 생성 엔드포인트 URL
    api_url: str

    # 호출 대상인 LLM API 서비스 식별 명칭 (도메인 의미: 에러 메시지 템플릿에 주입되는 서비스 이름)
    service_name: str = "llm_api"

    # 용도별 config 키 매핑 (model_name=None일 때 설정 파일에서 자동 로드)
    _PURPOSE_TO_CONFIG_MAP: dict[str, str] = {
        "router": "llm.router_model",
        "sql_generator": "llm.sql_generator_model",
    }

    def __init__(self, model_name: str | None = None, purpose: str | None = None) -> None:
        """설정 상태와 환경변수를 바탕으로 LLM 프록시 클라이언트를 초기화한다.

        Args:
            model_name: llmpool.yml에 정의된 고유 모델 명칭.
            purpose: LLM 추론 목적 구분자 ("sql_generator", "router" 등).
        """
        self.last_generated_by = None
        self.purpose = purpose or "sql_generator"

        # model_name이 명시되지 않은 경우, 용도에 맞게 설정 파일에서 자동 로드
        if not model_name:
            config_key = self._PURPOSE_TO_CONFIG_MAP.get(self.purpose)
            if config_key:
                model_name = setting(config_key)
        self.model_name = model_name or ""
        
        # llm_api 서버 엔드포인트 설정 (도커 브릿지 및 로컬 테스트 호환성 기본값 제공)
        self.api_url = os.getenv("LLM_API_URL") or setting("llm.llm_api_url") or "http://llm-api:5000/generate"
        logger.info(
            "[Proxy-LlmClient] 초기화 완료. model_name=%s, purpose=%s, api_url=%s",
            self.model_name,
            self.purpose,
            self.api_url
        )

    def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """독립된 llm_api 도커 서버로 HTTP POST 요청을 전송하여 생성 결과 텍스트를 수집한다.

        Args:
            prompt: 사용자 입력 프롬프트.
            system_prompt: 기존 시스템 지침을 대체할 사용자 정의 시스템 지침.

        Returns:
            LLM이 생성한 응답 텍스트 문자열.
        """
        self.last_generated_by = None
        
        # HTTP 전송 페이로드 구성
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model_name": self.model_name if self.model_name else None,
            "purpose": self.purpose
        }
        
        logger.info(
            "[Proxy-LlmClient] llm_api 서버로 텍스트 생성 요청 전송 중. api_url=%s, purpose=%s",
            self.api_url,
            self.purpose
        )
        
        request = Request(
            self.api_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        # 타임아웃 기본값 120초 지정 (GGUF 모델 로컬 연산 시간 반영)
        timeout = int(os.getenv("LLM_API_TIMEOUT", "120"))
        
        try:
            with urlopen(request, timeout=timeout) as response:
                resp_bytes = response.read()
                data = json.loads(resp_bytes.decode("utf-8"))
                
                # 결과 파싱
                content = data.get("result")
                self.last_generated_by = data.get("generated_by", "unknown")
                
                if content is None:
                     msg_tmpl = setting("errors.llm.missing_result") or "{service_name} 응답 내 'result' field가 누락되어 있습니다."
                     raise LlmInferenceError(msg_tmpl.format(service_name=self.service_name))
                     
                content_flat = str(content).replace("\n", " ").replace("\r", "")
                logger.info(
                    "[Proxy-LlmClient] %s 응답 수집 성공. generated_by=%s, content: %s",
                    self.service_name,
                    self.last_generated_by,
                    content_flat
                )
                return str(content)
                
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            msg_tmpl = setting("errors.llm.http_error") or "{service_name} 서버 오류 HTTP {code}: {detail}"
            error_msg = msg_tmpl.format(service_name=self.service_name, code=exc.code, detail=body)
            logger.error("[Proxy-LlmClient] HTTPError 발생: %s", error_msg)
            raise LlmInferenceError(error_msg) from exc
            
        except URLError as exc:
            msg_tmpl = setting("errors.llm.connection_error") or "{service_name} 연결 실패 (서버 미동작 또는 네트워크 장애): {detail}"
            error_msg = msg_tmpl.format(service_name=self.service_name, detail=str(exc.reason))
            logger.error("[Proxy-LlmClient] URLError 발생: %s", error_msg)
            raise LlmInferenceError(error_msg) from exc
            
        except Exception as exc:
            msg_tmpl = setting("errors.llm.unexpected_error") or "{service_name} 연동 중 예기치 않은 오류 발생: {detail}"
            error_msg = msg_tmpl.format(service_name=self.service_name, detail=str(exc))
            logger.error("[Proxy-LlmClient] 예외 발생: %s", error_msg)
            raise LlmInferenceError(error_msg) from exc
