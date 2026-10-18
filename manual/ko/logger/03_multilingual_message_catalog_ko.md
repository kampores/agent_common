# 2.3. 다국어 로그 메시지 템플릿 사전 및 코드 기반 로깅 (`logging_messages_*.yml`, `log_msg`)

> **소속 모듈**: `agent_common.logger.ProjectLogger`  
> **관련 함수/메서드**: `ProjectLogger.get_log_msg()`, `ProjectLogger.log_msg()`, `ProjectLogger.get_log_id_description()`, `get_log_msg()`  
> **메시지 사전 파일**: `agent_common/src/agent_common/localize/{ko,en,zh,ja}/logging_messages_{lang}.yml`

---

## 1. 개요 및 엔터프라이즈 배경

엔터프라이즈 서비스 개발 시 코드 내부에 하드코딩된 한글/영어 로그 메시지는 다음과 같은 중대한 문제를 발생시킵니다:

1. **규정 위반 및 유지보수 비용 증대**: AGENTS.md 제1원칙(하드코딩 금지) 위반으로, 메시지 문구 수정 시 소스 코드를 다시 빌드하고 배포해야 하는 비효율성 발생
2. **글로벌 운영 지원 한계**: 해외 운영 센터(NOC)나 외국인 엔지니어 협업 시 한글 로그 메시지로 인한 장애 대응 지연
3. **로그 분석 및 메트릭 표준화 부재**: 로그 메시지가 비정형 텍스트로 자유롭게 작성되어 동일한 유형의 장애를 통계화하거나 알람 룰로 정의하기 극히 어려움

`ProjectLogger`는 이러한 문제를 원천 해결하기 위해 **메시지 코드 기반의 외부 사전 템플릿 연동 시스템**과 **런타임 동적 다국어 전환(KO ⇄ EN ⇄ JA ⇄ ZH)** 기능을 완벽하게 지원합니다.

---

## 2. 핵심 아키텍처 및 템플릿 해석 파이프라인

```mermaid
flowchart TD
    A["logger.info('task_start', task_name='이관') 호출"] --> B{"언어 판별"}
    B -->|"KO / EN / ZH / JA"| C["localize/{lang}/logging_messages_{lang}.yml"]
    
    C --> E["_search_template_in_level(레벨, 코드)"]
    E --> F{"해당 레벨에서 발견?"}
    F -->|"예"| G["템플릿 획득"]
    F -->|"아니오"| H{"타 레벨 섹션 순회 탐색"}
    H -->|"발견"| G
    H -->|"미발견"| I["default_str 또는 코드 문자열 자체를 템플릿으로 사용"]
    
    G --> J["safe_kwargs_dict 처리 (중괄호 이스케이프 보호)"]
    I --> J
    J --> K["template.format(**safe_kwargs) 수행"]
    K --> L["포매팅 완료된 메시지 문자열 생성"]
    L --> M["stacklevel=2를 적용하여 호출 원천 라인으로 로깅 기록"]
```

---

## 3. 메시지 사전 YAML 구조

다국어 메시지 파일은 컴포넌트별로 모듈화되어 `agent_common/src/agent_common/localize/{lang}/` 하위에 위치합니다.

### 3.1. 한국어 사전 (`agent_common/src/agent_common/localize/ko/logging_messages_ko.yml`)

```yaml
logging_messages:
  INFO:
    task_start: "🚀 [{task_name}] 작업이 시작되었습니다. (대상: {target_count:,}건)"
    task_completed: "✅ [{task_name}] 작업이 성공적으로 완료되었습니다."
    data_transfer_progress: "[{task_name}] 처리 진행 중: {processed_count:,}/{total_count:,}건 ({percent:.1f}%)"
  
  WARNING:
    record_skipped: "⚠️ [{task_name}] 제외 조건에 의해 데이터 처리를 건너뜁니다: {reason}"
    retry_attempt: "⚠️ 일시적 연결 실패로 재시도합니다. (시도 횟수: {attempt_count}/{max_retries})"
  
  ERROR:
    connection_failed: "❌ {service_name} 서비스 연결에 실패하였습니다. (사유: {error_msg})"
    schema_validation_failed: "❌ 필수 필드 누락 또는 스키마 검증 실패: {detail}"
```

### 3.2. 영문 사전 (`agent_common/src/agent_common/localize/en/logging_messages_en.yml`)

```yaml
logging_messages:
  INFO:
    task_start: "🚀 [{task_name}] task has started. (Targets: {target_count:,} items)"
    task_completed: "✅ [{task_name}] task has completed successfully."
    data_transfer_progress: "[{task_name}] Transfer progress: {processed_count:,}/{total_count:,} items ({percent:.1f}%)"
  
  WARNING:
    record_skipped: "⚠️ [{task_name}] Record skipped due to exclusion policy: {reason}"
    retry_attempt: "⚠️ Temporary connection failure. Retrying (Attempt: {attempt_count}/{max_retries})"
  
  ERROR:
    connection_failed: "❌ Failed to connect to {service_name}. (Reason: {error_msg})"
    schema_validation_failed: "❌ Required fields missing or schema validation failed: {detail}"
```

---

## 4. 주요 기능 및 구현 특징

### 4.1. 안전한 인자 치환 (`safe_kwargs_dict`)
로그 파라미터로 전달된 문자열에 중괄호(`{`, `}`)가 포함되어 있더라도(예: JSON 문자열, 정규식 등) `format()` 파싱 시 `KeyError`나 `ValueError`가 발생하지 않도록 이스케이프(`{{`, `}}`)를 안전하게 처리합니다.

```python
safe_kwargs_dict = {
    k: str(v).replace("{", "{{").replace("}", "}}") if isinstance(v, str) else v
    for k, v in kwargs.items()
}
```

### 4.2. 정확한 호출자 추적 (`stacklevel=2`)
`logger.info()`, `logger.error()` 등의 편의 래퍼 메서드를 경유하더라도 로깅 프레임워크가 래퍼 내부가 아닌 **실제 이 메서드를 호출한 비즈니스 코드의 파일명과 라인 번호**를 로그 헤더에 정확히 기록하도록 `stacklevel=2`를 적용합니다.

### 4.3. 런타임 동적 언어 전환
프로세스를 재시작하지 않고도 글로벌 설정 또는 `ConfigLoader`를 통해 즉시 출력 언어를 변경할 수 있습니다:

- 전역 설정: `Localizer.set_global_language("EN")`
- 설정 로더 프로퍼티(Setter): `config_loader.language_str = "EN"`
- 현재 언어 확인(Getter): `config_loader.language_str` (➔ `"EN"`, `"KO"`, `"JA"`, `"ZH"`)

지원하는 언어 코드는 `KO`, `EN`, `ZH`, `JA`이며, 로그 언어는 다음 우선순위로 결정됩니다:

1. `ConfigLoader.language_str` 또는 `Localizer.set_global_language()`로 지정한 값
2. 환경변수 `AGENT_LOG_LANGUAGE`, `LOGGING_LANGUAGE`, `AGENT_LANGUAGE`, `APP_LANGUAGE`, `LANG` 중 앞에서부터 처음으로 값이 있는 것 (BCP 47 표준 하이픈 로케일 자동 정규화)
3. `config.yml`의 `logging.language_str`
4. 기본 언어 `KO`

언어 코드 정규화 규칙과 언어별 파일 탐색 방식은 [8.1. 언어 코드 정규화 및 언어별 리소스 파일 탐색 (`Localizer`)](../localizer/01_language_codes_and_resource_lookup_ko.md)을 참고하세요.

### 4.4. `service_name_str` 바인딩을 통한 서비스 문맥 자동 주입
`ProjectLogger(name_str, service_name_str="")` 인스턴스 생성 시 선택적 파라미터 `service_name_str`을 넘겨주면 로거 인스턴스에 영속적으로 바인딩됩니다.
이후 `get_log_msg()`나 `get_log_id_description()` 호출 시 매번 `service_name="BigQuery"`를 반복 전달하지 않아도 템플릿의 `{service_name}` 및 `{service_name_str}` 변수에 바인딩된 서비스명이 자동으로 주입됩니다:

```python
logger = ProjectLogger("BqPipeline", service_name_str="BigQuery")
logger.error("connection_failed", error_msg="Timeout")
# ➔ "❌ BigQuery 서비스 연결에 실패하였습니다. (사유: Timeout)"
```

---

## 5. 실전 사용 코드

### 5.1. 코드 기반 메시지 로깅

```python
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MigrationService", service_name_str="Cloud_Storage")

# 1. 메시지 코드 및 키워드 인자를 사용한 로깅
logger.info("task_start", task_name="Cloud_Data_Sync", target_count=50000)

# 2. 진행률 로깅
logger.info(
    "data_transfer_progress",
    task_name="Cloud_Data_Sync",
    processed_count=25000,
    total_count=50000,
    percent=50.0,
)

# 3. 에러 발생 시 코드 기반 로깅 (service_name 자동 치환)
try:
    raise ConnectionTimeoutError("Connection timed out after 30s")
except Exception as e:
    logger.exception("connection_failed", error_msg=str(e))
```

### 5.2. 런타임 다국어 동적 전환 실전 예시

```python
from agent_common.logger import ProjectLogger
from agent_common import Localizer

logger = ProjectLogger("InternationalBatch")

# 기본 언어(KO) 출력
logger.info("task_start", task_name="SyncJob", target_count=100)
# ➔ [INFO] 🚀 [SyncJob] 작업이 시작되었습니다. (대상: 100건)

# 영문 모드로 전환
Localizer.set_global_language("EN")

logger.info("task_start", task_name="SyncJob", target_count=100)
# ➔ [INFO] 🚀 [SyncJob] task has started. (Targets: 100 items)
```

### 5.3. 하위 호환 및 문자열 템플릿 포매팅 전용 함수 (`get_log_msg`)

로그를 직접 남기지 않고 포매팅된 메시지 텍스트만 가져와 알림(Slack, Email 등)에 사용해야 할 때는 `get_log_msg()`를 활용합니다:

```python
from agent_common.logger import get_log_msg

alert_text = get_log_msg("ERROR", "connection_failed", service_name="Kafka", error_msg="Broker unreachable")
print(alert_text)
# ➔ "❌ Kafka 서비스 연결에 실패하였습니다. (사유: Broker unreachable)"
```

---

## 6. 운영 베스트 프랙티스

### 6.1. 프로젝트별 메시지 사전 확장 실전 예시

`agent_common` 패키지가 기본 제공하는 표준 사전 외에, 개별 프로젝트 고유의 비즈니스 메시지나 도메인 에러 코드가 필요한 경우 프로젝트 루트의 `config/logging_messages_ko.yml`에 작성합니다.

`ConfigLoader`는 **5단계 계층 병합(Deep Merge)**을 통해 패키지 기본 사전을 유지하면서 프로젝트 사전을 덮어쓰거나 새로운 키를 안전하게 병합합니다.

#### 1) 프로젝트 고유 메시지 파일 작성 (`<프로젝트_루트>/config/logging_messages_ko.yml`)
```yaml
logging_messages:
  INFO:
    # 기존 패키지 기본 메시지를 프로젝트 맞춤형 문구로 재정의 (Override)
    task_start: "🔥 [파이프라인 시작] {task_name} 배치가 가동되었습니다. (예정 대상: {target_count:,}건)"
    
    # 프로젝트 고유의 신규 비즈니스 메시지 코드 추가
    medallion_step_completed: "🏅 [{stage_name}] 단계 정제 및 변환 완료: 성공 {success_count:,}건, 제외 {excluded_count:,}건"

  ERROR:
    # 프로젝트 전용 외부 API 에러 코드 추가
    auth_token_expired: "🚫 인증 서버({auth_url}) 토큰 만료 또는 갱신 실패 (HTTP 상태코드: {status_code})"
```

#### 2) 파이썬 코드에서 호출 및 동작 검증
```python
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MedallionPipeline")

# 1. 재정의(Override)된 메시지 코드 호출
logger.info("task_start", task_name="SilverToGold", target_count=10000)
# ➔ [INFO] 🔥 [파이프라인 시작] SilverToGold 배치가 가동되었습니다. (예정 대상: 10,000건)

# 2. 신규 추가된 프로젝트 고유 메시지 코드 호출
logger.info(
    "medallion_step_completed",
    stage_name="Gold_Mart",
    success_count=9950,
    excluded_count=50,
)
# ➔ [INFO] 🏅 [Gold_Mart] 단계 정제 및 변환 완료: 성공 9,950건, 제외 50건

# 3. 신규 에러 메시지 코드 호출 (자동으로 failure 및 에러 카운트 누적)
try:
    raise PermissionError("Token expired")
except Exception as e:
    logger.exception(
        "auth_token_expired",
        auth_url="https://auth.internal.example.com",
        status_code=401,
    )

# 4. 패키지 기본 사전에만 정의된 기존 메시지(오버라이드하지 않은 키)도 그대로 호출 가능
logger.info("task_completed", task_name="SilverToGold")
# ➔ [INFO] ✅ [SilverToGold] 작업이 성공적으로 완료되었습니다.
```

### 6.2. 에러 코드 명명 규칙
- 메시지 코드는 스네이크 케이스(`snake_case`)로 일관성 있게 작성하며, 목적과 주체를 명확히 부여하십시오 (예: `db_query_failed`, `file_not_found`, `invalid_payload`).

---

### 6.3. 예외 발생 시 메시지 처리 베스트 프랙티스: 다국어화(Localize) 및 이중 로깅(Double Logging) 방지

데이터 검증, 컨텍스트 빌더, 도메인 변환기 등 하위 레이어에서 잘못된 파라미터나 비정상 데이터가 유입되어 예외(`ValueError`, `TypeError` 등)를 발생시켜야 할 때, 코드 내에 직접 문자열을 하드코딩하거나 성급하게 로거를 직접 호출하면 심각한 부작용이 발생합니다.

#### 1) 발생 가능한 문제점
* **하드코딩 문제**: `raise ValueError(f"에러 발생: {key_str}")` 형태로 문자열을 소스에 직접 작성하면 **AGENTS.md 제1원칙(하드코딩 금지)** 위배 및 다국어(Localization) 지원이 불가능해집니다.
* **이중 로깅(Double Logging) 문제**: 하위 함수에서 `logger.error(...)`를 직접 호출하고 `raise ValueError(...)`를 던지면, 상위 실행기(예: `PipelineThreadRunner`의 워커 스레드)가 `except Exception:`으로 포착하여 `logger.exception(...)`을 다시 출력하므로 **동일 에러 1건에 대해 로그가 2회 중복 출력**되어 로그 분석과 모니터링이 왜곡됩니다.

#### 2) 권장 해결 패턴: "Log or Throw, Never Both" & `get_log_msg()` 활용
하위 함수에서는 로그 출력을 하지 않고, `logger.get_log_msg()`를 통해 메시지 사전으로부터 다국어화된 에러 텍스트만 렌더링하여 예외 객체에 주입합니다. 실제 로그 출력과 트레이스백 보존은 예외를 최종 포착하는 상위 실행기(Runner)가 전담합니다.

```python
# 1. 메시지 사전 등록 (config/logging_messages_ko.yml 또는 logging_messages.yml)
logging_messages:
  ERROR:
    extract_job_base_date_failed_error: "ECS 객체 키에서 8자리 작업기준일(YYYYMMDD)을 추출할 수 없습니다: [ECS_Key={ecs_key_str}]"

# 2. 하위 도메인/빌더 클래스에서의 예외 발생 (화면/파일 출력 없이 포매팅 문자열만 획득)
class RuleContextBuilder:
    def __init__(self):
        self.logger = ProjectLogger(self.__class__.__name__)

    def build_context(self, ecs_key_str: str) -> dict[str, Any]:
        extracted_date_str = StoragePathBuilder.extract_date_from_key(ecs_key_str)
        if not extracted_date_str:
            # get_log_msg()는 콘솔/파일 출력을 하지 않고 다국어 템플릿에서 포매팅된 문자열만 반환합니다.
            error_msg_str: str = self.logger.get_log_msg(
                "ERROR",
                "extract_job_base_date_failed_error",
                ecs_key_str=ecs_key_str,
            )
            raise ValueError(error_msg_str)
        ...

# 3. 상위 실행기(Runner)에서의 단일 일괄 로깅 및 예외 격리
try:
    context_dict = context_builder.build_context(ecs_key_str)
except Exception as err_obj:
    # 상위에서 트레이스백과 함께 정확히 1회만 로깅 (이중 로깅 원천 차단 + 다국어 메시지 보존)
    self.logger.exception(
        "pipeline_worker_exception",
        target_item_str=ecs_key_str,
        error_str=f"[{type(err_obj).__name__}] {err_obj}",
    )
```

#### 3) 이 패턴의 3대 핵심 이점
1. **이중 로깅 0% (Duplicate Logging 방지)**: `get_log_msg()`는 화면/파일 핸들러 출력을 전혀 하지 않고 포맷팅된 문자열만 반환하므로 하위 단계에서 중복 로그가 남지 않습니다.
2. **다국어화 100% (Localization 완벽 대응)**: 소스 코드에 한글/영어 문자열이 전혀 하드코딩되지 않으며, `logging_messages_*.yml` 사전을 통해 프로세스 언어 설정(KO/EN/JA/ZH)에 따라 동적으로 메시지가 변환됩니다.
3. **상위 일괄 집계 및 트레이스백 보존**: 상위 Runner가 `logger.exception()`으로 단 1회 기록하므로 스택 트레이스와 함께 에러 카운트 집계가 누락이나 왜곡 없이 완벽히 유지됩니다.
