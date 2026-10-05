# agent_common

**[📦 PyPI 패키지](https://pypi.org/project/agent-common/) · [💻 GitHub 소스 및 매뉴얼](https://github.com/kampores/agent_common)**

> [ KO 한국어 ](#agent_common-패키지-한국어) | [ EN English ](#agent_common-package-english) | [ ZH 中文 ](#agent_common-软件包-中文) | [ JA 日本語 ](#agent_common-パッケージ-日本語)

---

## agent_common 패키지 (한국어)

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트, 동적 도구(Tool) 파서 및 에러 처리 라이브러리 패키지입니다.

---

### 📌 주요 제공 기능

#### 1. 설정 로더 및 불변 설정 객체 (`agent_common.config_loader`)
- **1.1. [계층적 YAML 설정 해석 및 병합 (Deep Merge)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/01_hierarchical_yaml_merge_ko.md)**: 패키지 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정(`config/*.yml`) 동적 병합.
- **1.2. [불변 점 표기법 조회 (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/02_readonly_dot_notation_ko.md)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 형태로 직관적 속성 접근 및 런타임 변조 방지.
- **1.3. [타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/03_type_coercion_and_guarantee_ko.md)**:
  - `_int`: `int` 정수형 자동 형 변환 및 보증
  - `_float`: `float` 실수형 자동 형 변환 및 보증
  - `_bool`: `bool` 불리언형 자동 변환 및 타입 보증 (파이썬 `bool` 또는 대소문자 무관 `"true"`, `"false"` 지원, `0`, `1` 등 비지원 값 유입 시 Fail-Fast 차단)
  - `_str`: `str` 문자열 변환 및 `.strip()` 공백 자동 정제
  - `_list` / `_dict`: 리스트 / 불변 딕셔너리(`ReadOnlyConfig`) 래핑 보증
  - 범용 함수 `coerce_type_by_key_suffix` 및 중첩 딕셔너리 일괄 변환 `coerce_dict_by_key_suffix` 제공으로 임의의 외부 설정 파일(`rule.yml`, `mapping.yml` 등) 및 데이터 파이프라인 완벽 지원
  - 타입 불일치 시 침묵하지 않고 상세 안내와 함께 즉시 조기 실패(Fail-Fast, `ValueError`/`TypeError`) 발생 보증
- **1.4. [Fail-Fast 필수 설정 검증 (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/04_fail_fast_require_setting_ko.md)**: 프로그램 시작 시 필수 설정값 누락 시 상세 원인 출력 후 프로세스 즉시 종료.
- **1.5. [네트워크 프록시 제어 (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/05_network_proxy_control_ko.md)**: `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영.
- **1.6. [모든 상수의 설정 파일화 및 템플릿 보정 (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/06_ensure_config_self_healing_ko.md)**: 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정. `agent_common` 클래스의 기본 설정은 `config_loader.config_file_auto_repair_dict`에서 `true`로 켠 클래스만 기록.

#### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- **2.1. [단일 행 평탄화 포매터 및 예외 원천 추적 (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/01_single_line_flatten_formatter_ko.md)**: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화 및 `[Origin: ...]` 원천 위치 추출, 로거 팩토리 기반 호출자/클래스명(`%(caller_str)s`, `%(class_name_str)s`) 자동 결합 및 프로그램 로거 이름(`%(name)s`) 통일 지원.
- **2.2. [로깅 환경 일괄 구성 및 핸들러 제어 (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/02_project_logger_configure_ko.md)**: 콘솔 및 파일 로그 핸들러 동적 생성, 일자별 폴더 분리, 실행 로그 레벨별 디렉터리 자동 분기(`{log_level_str}` 기반 `log_file_str` 단일화).
- **2.3. [다국어 로그 메시지 템플릿 사전 및 코드 기반 로깅 (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/03_multilingual_message_catalog_ko.md)**: `config.yml`의 `logging.language_str` (`KO`, `EN`, `ZH`, `JA`) 설정에 따라 다국어 메시지 사전 자동 연동, 런타임 동적 언어 전환 및 안전한 템플릿 치환.
- **2.4. [작업 진행 통계 및 예외/제외 사유별 실시간 집계 (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/04_execution_result_and_error_tracking_ko.md)**: 성공, 실패, 제외(Skip) 3단계 상태 분류 및 인스턴스/클래스 전역 멀티스레드 에러 집계.
- **2.5. [작업 결과 요약 리포트 자동 생성 (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/05_summary_report_generation_ko.md)**: '전체 = 성공 + 실패 + 제외' 정합성 보장, `TableFormatter` 기반 세로줄 자동 맞춤, 소요 시간, 처리 속도, 전송량이 포함된 표준 마크다운 표(Table) 자동 출력.

#### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- **3.1. [AWS S3 및 Dell ECS 오브젝트 스토리지 클라이언트 (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/01_s3_ecs_storage_client_ko.md)**: AWS S3 및 Dell ECS(S3 호환) 저장소 접속, 초기화 즉시 `head_bucket` Fail-Fast 검증, 대용량 페이징 제너레이터(`list_objects`), 메타데이터 빠른 조회(`get_object_size`), 메모리 스트리밍 획득(`get_object_stream`), GCS 실시간 파일 전송 및 동일 파일 스마트 스킵(`transfer_to_gcs`).
- **3.2. [Google Cloud Storage 스트리밍 클라이언트 및 멀티 계층 인증 (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/02_gcs_cloud_storage_client_ko.md)**: 4단계 GCP 인증 우선순위(`GOOGLE_APPLICATION_CREDENTIALS_JSON` 인메모리 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 파일 -> `credentials_path_str` -> Google ADC) 지원, 연결 및 버킷 권한 조기 검증, 블롭 메타데이터 및 크기 조회(`get_blob_size`), 메모리 낭비 없는 청크 단위 스트림 직접 업로드(`upload_stream`).
- **3.3. [BigQuery 배치 및 스트리밍 적재 클라이언트 (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/03_bigquery_batch_and_streaming_load_ko.md)**: 연결 및 테이블 스키마 사전 캐싱(`get_table`), JSON 배치 로드 Job(`load_table_from_json_data`) 및 중첩 에러(`errors`, `location`, `reason`) 상세 분해, 실시간 스트리밍 인서트(`insert_rows_json_data`), 범용 동기 SQL 쿼리(`query`), 중복 전송 방지용 기존 키 집합 추출(`get_existing_keys`), 기존 레코드 메타데이터 일괄 조회(`get_existing_records_metadata`).
- **3.4. [BigQuery 고성능 인라인 MERGE (Upsert) 쿼리 엔진 (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/04_bigquery_inline_merge_upsert_ko.md)**: 스테이징 임시 테이블 생성 없이 직접 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 기반 인라인 MERGE INTO 수행, 기본키(PK) 기준 자동 UPDATE/INSERT 분기, 생성일시 등 최초 값 보존(`preserve_columns_list`), 컬럼 데이터 타입 자동 추론 및 명시적 캐스팅(`column_types_dict`), 한글/특수문자/예약어 백틱(`` ` ``) 완벽 보호, HTTP 413 페이로드 초과 방지 기본 100건 청크 자동 분할.
- **3.5. [BigQuery TIMESTAMP·DATETIME 일시 문자열 변환 (`convert_to_bigquery_timestamp`, `convert_to_bigquery_datetime`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/05_bigquery_timestamp_and_datetime_conversion_ko.md)**: ISO 8601, 공백 구분, 14자리/8자리 숫자 등 다양한 원천 날짜 문자열을 `TIMESTAMP` 컬럼용(타임존 오프셋 포함, 우선순위 `timezone_offset_str`)과 `DATETIME` 컬럼용(오프셋 없는 벽시계 시각 `YYYY-MM-DD HH:MM:SS`) 표준 문자열로 정규화.
- **3.6. [GCP 서비스 계정 인증 해석기 (`GcpCredentialResolver`)](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/06_gcp_credential_resolver_ko.md)**: 4단계 우선순위(환경변수 JSON → 환경변수 파일 경로 → 설정 파일 경로 → ADC)에 따른 GCP 인증 해석을 전담하는 독립 클래스. `GcsClient`·`BigQueryClient`가 합성(Composition)으로 사용하며, 그 외 GCP 서비스에서도 단독으로 재사용 가능.

#### 4. 동적 도구 로더 및 템플릿 평가기 (`agent_common.tool_parser`) & 내장 도구 (`agent_common.tool`)
- **4.1. [이원화된 Tool 디렉터리 계층 탐색 및 동적 로딩 (`ToolParser.load_tool_function`)](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/01_dual_tool_hierarchy_discovery_ko.md)**:
  - **1순위 (내장 도구)**: `agent_common/tool/` 하위 모듈 (전사 표준 내장 도구)
  - **2순위 (프로젝트 도구)**: `config.yml`의 `transfer.tool_dir_str`에 지정된 로컬 경로 (예: `medallion/tool/`)
- **4.2. [선언적 템플릿 치환 및 표현식 평가 (`ToolParser.eval`)](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/02_declarative_template_eval_ko.md)**:
  - 변수 네임스페이스 바인딩: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - 동적 도구 함수 호출: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - 파이프(`|`) 우선순위 폴백 및 기본값: `"{meta.title|json.title|'기본제목'}"`
- **4.3. [안전한 네임스페이스 탐색 (`_SafeNamespace`)](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/03_safe_namespace_navigation_ko.md)**: 점(`.`) 및 인덱스 통합 접근, 대소문자 무관 탐색, 누락 필드 `""` 반환, 중첩 딕셔너리/리스트 안전 재귀 래핑.
- **4.4. [내장 공통 일시 도구 (`DateTimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/04_builtin_datetime_utils_ko.md)**: 테이블 규칙 및 템플릿 평가 전용 날짜/시간 도구, 코어 타임존 해석은 `TimeUtils`에 위임하여 역할 분담.

#### 5. 진행률 트래커, 테이블 포매터 및 시간 유틸리티 (`agent_common.progress_tracker`, `agent_common.table_formatter`, `agent_common.time_utils`)
- **5.1. [호스트 시스템 타임존 감지, 전 세계 표준시 해석 및 일시 정규화 (`TimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/01_time_utils_and_timezone_resolution_ko.md)**: 호스트 시스템 타임존 동적 자동 감지, 전 세계 30여 개 주요 표준 타임존 해석, ISO 8601 오프셋 계산, 일시 객체/문자열을 timezone-aware datetime으로 정규화하는 `parse_datetime`.
- **5.2. [멀티스레드 실시간 진행률 추적 및 마일스톤 경고 (`ProgressTracker`)](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/02_progress_tracker_and_milestones_ko.md)**: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간(ETA) 예측, 일반 진행 `INFO` vs 10% 단위 마일스톤 `WARNING` 승격 로깅.
- **5.3. [유니코드 전각 문자 폭 계산 및 마크다운/콘솔 테이블 칼맞춤 포매터 (`TableFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/03_unicode_table_formatter_ko.md)**: 유니코드 동아시아 문자 폭(`unicodedata.east_asian_width`) 정밀 계산 기반 한글/한자(2칸) vs 영문(1칸) 모노스페이스 콘솔 및 마크다운 테이블 세로줄 자동 맞춤 포매터.

#### 6. 공용 에러 및 예외 핸들러 (`agent_common.error_handler`)
- 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공.

#### 7. 통합 LLM 클라이언트 및 추론 엔진 (`agent_common.llm`)
- **7.1. [모델 프로필 관리 및 텍스트 생성](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/01_model_profiles_and_generation_ko.md)**
- **7.2. [외부 채팅 API 및 Fabrix 연동](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/02_external_api_and_fabrix_ko.md)**
- **7.3. [로컬 GGUF 추론 및 모델 캐싱](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/03_local_gguf_inference_ko.md)**
- **7.4. [실행 모드 및 조건부 로컬 전환](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/04_provider_and_local_fallback_ko.md)**
- **7.5. [추론 결과 및 예외 처리](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/05_inference_results_and_errors_ko.md)**
- **7.6. [Groq 감독관 AI 및 Antigravity Stop 훅](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/06_groq_supervisor_and_stop_hook_ko.md)**

#### 8. 언어 로컬라이저 (`agent_common.localizer`)
- **8.1. [언어 코드 정규화 및 언어별 리소스 파일 탐색 (`Localizer`)](https://github.com/kampores/agent_common/blob/main/manual/ko/localizer/01_language_codes_and_resource_lookup_ko.md)**: ISO 639-1 언어 코드(`KO`, `EN`, `ZH`, `JA`) 정규화, 명시 인자·전역 설정·환경변수 기반 언어 결정, `{접두사}_{언어}.yml` 형태의 언어별 리소스 파일 탐색. 로깅과 분리되어 라벨·안내문 등 임의의 다국어 리소스에 재사용 가능.

---

### 🛠️ 사용 예시 (Usage Examples)

#### 1. 전역 `config` 점 표기법 및 타입 보증 활용
```python
from agent_common.config_loader import config

# 1) 타입 접미사에 따른 자동 형 변환 보증
max_workers: int = config.transfer.max_workers_int       # int 타입 보증
host: str = config.database.host_str                     # str 타입 및 .strip() 정제 보증
is_active: bool = config.transfer.is_active_bool         # bool 타입 보증

# 2) 계층적 속성 접근
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. ToolParser를 통한 동적 룰 평가
```python
from agent_common.tool_parser import ToolParser

tool_parser = ToolParser()

context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) 도구 함수 호출 템플릿 평가
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)

# 2) 네임스페이스 및 내장 일시 템플릿 평가
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. ProgressTracker 실시간 진행률 추적
```python
from agent_common import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="파일")

for file_info in file_list:
    try:
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

tracker.log_summary()
```

#### 4. LlmClient를 통한 통합 텍스트/SQL 생성
```python
from agent_common.llm import LlmClient

llm_client = LlmClient(purpose_str="sql_generator")
response_str = llm_client.generate(
    prompt_str="사용자 요청: 2026년 8월 일일 가입자 수 통계 쿼리를 작성해줘.",
    system_prompt_str="당신은 BigQuery 전문 SQL 생성 AI입니다."
)
print(f"생성된 결과 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. 스토리지 및 BigQuery 클라이언트 활용
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS 스마트 전송
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery 인라인 MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "홍길동", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

#### 6. GcpCredentialResolver로 다른 GCP 서비스 인증하기
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

# 환경변수 JSON → 환경변수 파일 경로 → 지정 경로 순으로 해석하고, 모두 없으면 None(ADC)을 반환
credentials = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
).resolve()

# GCS·BigQuery 외의 GCP 클라이언트에도 그대로 전달
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

---

### 📖 상세 기능 매뉴얼 (User Manuals)

| 번호 | 모듈 / 주제 | 상세 매뉴얼 링크 | 주요 내용 요약 |
| :---: | :--- | :---: | :--- |
| **1.1** | **계층적 YAML 해석 & 딥 머지** | [01_hierarchical_yaml_merge_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/01_hierarchical_yaml_merge_ko.md) | 5단계 계층 병합 순서, `_deep_merge` 재귀 알고리즘, 루트 디렉터리 자동 탐색 |
| **1.2** | **불변 점 표기법 조회 (`ReadOnlyConfig`)** | [02_readonly_dot_notation_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/02_readonly_dot_notation_ko.md) | 점 표기법 속성 접근, 런타임 변조 원천 차단(Read-Only), 불변 객체 설계 |
| **1.3** | **타입 접미사 자동 형 변환 & 타입 보증** | [03_type_coercion_and_guarantee_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/03_type_coercion_and_guarantee_ko.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 런타임 자동 캐스팅 및 타입 안전성 보증 |
| **1.4** | **Fail-Fast 필수 설정 검증** | [04_fail_fast_require_setting_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/04_fail_fast_require_setting_ko.md) | 기동 초기 필수 설정 누락 감지, 상세 진단 로그 및 프로세스 안전 조기 종료 |
| **1.5** | **네트워크 프록시 제어** | [05_network_proxy_control_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/05_network_proxy_control_ko.md) | `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영 및 내부 통신 프록시 우회 |
| **1.6** | **모든 상수의 설정 파일화 및 템플릿 보정** | [06_ensure_config_self_healing_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/config_loader/06_ensure_config_self_healing_ko.md) | 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정 |
| **2.1** | **단일 행 평탄화 포매터 & 원천 추적** | [01_single_line_flatten_formatter_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/01_single_line_flatten_formatter_ko.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` 프레임 추출, 중앙 로그 수집기 연동 최적화 |
| **2.2** | **로깅 환경 일괄 구성 & 핸들러 제어** | [02_project_logger_configure_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/02_project_logger_configure_ko.md) | `ProjectLogger.configure()`, 콘솔/파일 핸들러 분기, 레벨별 파일 분리, 단일 표준 경로 템플릿 |
| **2.3** | **다국어 메시지 사전 & 코드 기반 로깅** | [03_multilingual_message_catalog_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/03_multilingual_message_catalog_ko.md) | `logging_messages_*.yml`, 런타임 언어 전환, `safe_kwargs` 템플릿 치환 |
| **2.4** | **작업 통계 & 에러/제외 실시간 집계** | [04_execution_result_and_error_tracking_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/04_execution_result_and_error_tracking_ko.md) | 성공/실패/제외(Skip) 3단계 상태 분류, 인스턴스 및 클래스 전역 멀티스레드 집계 |
| **2.5** | **작업 결과 요약 리포트 자동 생성** | [05_summary_report_generation_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/logger/05_summary_report_generation_ko.md) | `ProjectLogger.log_summary()`, 80열 표준 요약 블록, 처리 속도/전송률, 에러 상세 해석 |
| **3.1** | **AWS S3 & Dell ECS 스토리지 연동** | [01_s3_ecs_storage_client_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/01_s3_ecs_storage_client_ko.md) | S3/ECS 연결, Fail-Fast 검증, 페이징 목록 조회, GCS 스트리밍 전송 및 동일 파일 스킵 |
| **3.2** | **GCS 스트리밍 업로드 & 4단계 인증** | [02_gcs_cloud_storage_client_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/02_gcs_cloud_storage_client_ko.md) | 4단계 서비스 계정 인증 우선순위, 연결 검증, 메타데이터 조회, 메모리 파이프라인 업로드 |
| **3.3** | **BigQuery 배치 적재 & 스트리밍 인서트** | [03_bigquery_batch_and_streaming_load_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/03_bigquery_batch_and_streaming_load_ko.md) | JSON 배치 로드 Job vs 스트리밍 API, 중첩 에러 상세 분해, 중복 방지 키 집합 조회 |
| **3.4** | **BigQuery 인라인 MERGE (Upsert) 엔진** | [04_bigquery_inline_merge_upsert_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/04_bigquery_inline_merge_upsert_ko.md) | 임시 테이블 없는 인라인 MERGE, UNNEST 파라미터 바인딩, 동적 타입 캐스팅, 100건 청크 분할 |
| **3.5** | **BigQuery TIMESTAMP·DATETIME 변환** | [05_bigquery_timestamp_and_datetime_conversion_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/05_bigquery_timestamp_and_datetime_conversion_ko.md) | ISO/압축 일시 정규화, 타임존 오프셋 결정 우선순위, 컬럼 타입별 메서드 선택 기준 |
| **3.6** | **GCP 서비스 계정 인증 해석기** | [06_gcp_credential_resolver_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/clients/06_gcp_credential_resolver_ko.md) | `GcpCredentialResolver`, 4단계 인증 우선순위, 다른 GCP 서비스에서의 단독 재사용, 합성(Composition) 구조 |
| **4.1** | **이원화된 Tool 디렉터리 계층 탐색 & 동적 로딩** | [01_dual_tool_hierarchy_discovery_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/01_dual_tool_hierarchy_discovery_ko.md) | 내장(1순위) vs 로컬(2순위) 탐색 계층, 3단계 함수 탐색, `_tool_cache`, 사전 검증 |
| **4.2** | **선언적 템플릿 치환 & 표현식 평가** | [02_declarative_template_eval_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/02_declarative_template_eval_ko.md) | `ToolParser.eval()`, 도구 함수 직통 호출, 점(.) 네임스페이스 바인딩, 파이프(`\|`) 폴백 |
| **4.3** | **안전한 네임스페이스 탐색 (`_SafeNamespace`)** | [03_safe_namespace_navigation_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/03_safe_namespace_navigation_ko.md) | 점(.)/인덱스 통합 접근, 대소문자 무관 탐색, 누락 필드 `""` 반환, 중첩 래핑 |
| **4.4** | **내장 공통 일시 도구 (`DateTimeUtils`)** | [04_builtin_datetime_utils_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/tool_parser/04_builtin_datetime_utils_ko.md) | 테이블 룰/템플릿 전용 날짜 도구, `YYYYMMDD`, ISO 타임스탬프, 압축 일시 생성 |
| **5.1** | **호스트 타임존 감지 & 세계 표준시 해석** | [01_time_utils_and_timezone_resolution_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/01_time_utils_and_timezone_resolution_ko.md) | `TimeUtils`, OS/컨테이너 타임존 감지, 전 세계 30여 개 표준시 해석, datetime 정규화 |
| **5.2** | **멀티스레드 실시간 진행률 추적 & 마일스톤** | [02_progress_tracker_and_milestones_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/02_progress_tracker_and_milestones_ko.md) | `ProgressTracker`, 실시간 진행률(`%`), 처리 속도, ETA 계산, `WARNING` 승격 로깅 |
| **5.3** | **유니코드 전각 폭 계산 & 마크다운 표 칼맞춤** | [03_unicode_table_formatter_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/utils/03_unicode_table_formatter_ko.md) | `TableFormatter`, 동아시아 문자 폭(`east_asian_width`) 정밀 계산, 마크다운 표 정렬 |
| **7.1** | **모델 프로필 관리 및 텍스트 생성** | [01_model_profiles_and_generation_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/01_model_profiles_and_generation_ko.md) | `agent_common.llm` |
| **7.2** | **외부 채팅 API 및 Fabrix 연동** | [02_external_api_and_fabrix_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/02_external_api_and_fabrix_ko.md) | `agent_common.llm` |
| **7.3** | **로컬 GGUF 추론 및 모델 캐싱** | [03_local_gguf_inference_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/03_local_gguf_inference_ko.md) | `agent_common.llm` |
| **7.4** | **실행 모드 및 조건부 로컬 전환** | [04_provider_and_local_fallback_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/04_provider_and_local_fallback_ko.md) | `agent_common.llm` |
| **7.5** | **추론 결과 및 예외 처리** | [05_inference_results_and_errors_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/05_inference_results_and_errors_ko.md) | `agent_common.llm` |
| **7.6** | **Groq 감독관 AI 및 Antigravity Stop 훅** | [06_groq_supervisor_and_stop_hook_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/llm/06_groq_supervisor_and_stop_hook_ko.md) | `agent_common.llm` |
| **8.1** | **언어 코드 정규화 & 언어별 리소스 탐색** | [01_language_codes_and_resource_lookup_ko.md](https://github.com/kampores/agent_common/blob/main/manual/ko/localizer/01_language_codes_and_resource_lookup_ko.md) | `Localizer`, 지원 언어 코드와 별칭, 언어 결정 우선순위, 언어별 파일 탐색 및 기본 언어 대체 규칙 |

---

### 🚀 설치 및 빌드 가이드 (Installation and Build Guide)

#### 📦 Wheel 패키지 빌드 (.whl)
새로운 버전으로 패키징하여 `.whl` 파일을 빌드할 경우 `scripts/build_agent_common_whl.py` 또는 `agent_common` 디렉터리 내에서 아래 명령을 실행합니다.

##### 1. 사내 폐쇄망 환경 (인터넷 차단, 완전히 오프라인 빌드)
```bash
# 루트 디렉터리에서 자동 빌드 스크립트 실행 (권장)
python scripts/build_agent_common_whl.py

# 또는 pip wheel 직접 실행
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

##### 2. 인터넷 연동망 환경 (온라인 빌드)
```bash
# pip wheel 이용
pip wheel ./agent_common --no-deps -w whls/

# 또는 build 모듈 이용
python -m build agent_common --wheel -o whls/
```

#### Wheel 패키지 설치
```bash
# 개발 환경 (Editable 모드 - 기본 경량 설치)
pip install -e agent_common

# 개발 환경 (클라우드 클라이언트 extras 포함)
pip install -e "agent_common[clients]"

# 배포 환경 (Wheel 패키지 설치)
pip install dist/agent_common-0.4.98-py3-none-any.whl
```

#### 🌐 PyPI 공식 배포 (관리자 전용)
```bash
# 1. 빌드 도구 최신화
pip install build twine

# 2. 패키지 빌드 (sdist 및 wheel 동시 생성)
python -m build

# 3. 배포 아카이브 검증
python -m twine check dist/*

# 4. PyPI 업로드
python -m twine upload dist/agent_common-0.4.98*
```

---

### 📋 버전 변경 이력 (Changelog)

전체 상세 버전 변경 이력은 [CHANGELOG_KO.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_KO.md) 파일을 참고하세요.

---

## agent_common Package (English)

A comprehensive Python common library providing unified logging, hierarchical configuration loaders, cloud and database infrastructure clients, dynamic tool parsers, and centralized error handling for enterprise agent services and data migration pipelines.

---

### 📌 Key Features

#### 1. Configuration Loader & Immutable Config Object (`agent_common.config_loader`)
- **1.1. [Hierarchical YAML Parsing & Deep Merge](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/01_hierarchical_yaml_merge_en.md)**: Dynamically merges base package configurations (`agent_common/config/*.yml`) with project-specific configurations (`config/*.yml`).
- **1.2. [Immutable Dot-Notation Access (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/02_readonly_dot_notation_en.md)**: Intuitive attribute-based lookup (`config.ecs.endpoint_url`, `config.transfer.max_workers_int`) while preventing unintended runtime mutations.
- **1.3. [Type Guarantee & Automatic Coercion via Type Suffixes](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/03_type_coercion_and_guarantee_en.md)**:
  - `_int`: Automatic integer conversion and type guarantee.
  - `_float`: Automatic floating-point conversion and type guarantee.
  - `_bool`: Strict boolean conversion and type guarantee (Python `bool` or case-insensitive `"true"`, `"false"`; unsupported values like `0`, `1` fail fast).
  - `_str`: Automatic string conversion and `.strip()` whitespace trimming.
  - `_list` / `_dict`: Guaranteed list / immutable dictionary (`ReadOnlyConfig`) wrapping.
  - Standalone functions `coerce_type_by_key_suffix` and recursive batch coercion `coerce_dict_by_key_suffix` for arbitrary external configuration files (`rule.yml`, `mapping.yml`) and data mappings.
  - Strict Fail-Fast guarantee: type-suffix mismatches immediately raise diagnostic exceptions (`ValueError`/`TypeError`) instead of silently falling back to raw values.
- **1.4. [Fail-Fast Required Setting Validation (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/04_fail_fast_require_setting_en.md)**: Immediate process termination with diagnostic output if required settings are missing during startup.
- **1.5. [Network Proxy Control (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/05_network_proxy_control_en.md)**: Automatic synchronization of `NO_PROXY` environment variable from `proxy.no_proxy` configuration.
- **1.6. [Externalizing All Constants & Self-Healing Templates (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/06_ensure_config_self_healing_en.md)**: Materializing all in-code constants to configuration files, automatic scaffolding, and in-place missing key injection. Defaults of `agent_common` classes are written only for classes set to `true` in `config_loader.config_file_auto_repair_dict`.

#### 2. Single-Line Log Formatter & Project Logger (`agent_common.logger`)
- **2.1. [Single-Line Flatten Formatter & Origin Tracking (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/01_single_line_flatten_formatter_en.md)**: Flattens log records, extracts `[Origin: ...]` caller frames, and optimizes for centralized log aggregators (Logstash, Fluentd, CloudWatch).
- **2.2. [Batch Logging Configuration & Handler Control (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/02_project_logger_configure_en.md)**: Dynamic console/file handler initialization, date-based directories, and level-based directory creation (`log_file_str` with `{log_level_str}`).
- **2.3. [Multilingual Message Catalog & Code-Based Logging (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/03_multilingual_message_catalog_en.md)**: Dynamic multilingual dictionary loading (`KO`, `EN`, `ZH`, `JA`), runtime language switching, and safe template parameter substitution.
- **2.4. [Real-Time Metric Tracking & Error/Exclusion Classification (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/04_execution_result_and_error_tracking_en.md)**: Three-tier outcome model (Success, Failure, Excluded/Skip) and dual instance/class-global multithreaded telemetry.
- **2.5. [Automatic Summary Report Generation (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/05_summary_report_generation_en.md)**: Emits structured 80-column execution summary reports with duration, throughput (items/s), transfer rate (MB/s), and decoded error diagnostics.

#### 3. Storage and Database Infrastructure Clients (`agent_common.clients`)
- **3.1. [AWS S3 & Dell ECS Object Storage Client (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/01_s3_ecs_storage_client_en.md)**: Connects to AWS S3 and Dell ECS (S3-compatible) storage, early `head_bucket` Fail-Fast verification, high-throughput paginated iterator (`list_objects`), fast header metadata lookup (`get_object_size`), in-memory streaming body extraction (`get_object_stream`), real-time streaming pipeline upload to GCS with smart duplicate skipping (`transfer_to_gcs`).
- **3.2. [Google Cloud Storage Streaming Client & Multi-Tier Auth (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/02_gcs_cloud_storage_client_en.md)**: Four-tier GCP credential resolution hierarchy (`GOOGLE_APPLICATION_CREDENTIALS_JSON` in-memory JSON -> `GOOGLE_APPLICATION_CREDENTIALS` file -> `credentials_path_str` -> Google ADC), instant bucket reachability validation, blob metadata lookup (`get_blob_size`), zero-disk chunked streaming uploads (`upload_stream`).
- **3.3. [BigQuery Batch Loading & Streaming Ingestion (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/03_bigquery_batch_and_streaming_load_en.md)**: Fail-fast schema caching (`get_table`), JSON batch load jobs (`load_table_from_json_data`) with unpacked nested error diagnostics, real-time streaming ingestion (`insert_rows_json_data`), general SQL query execution (`query`), unique key deduplication set lookup (`get_existing_keys`).
- **3.4. [BigQuery High-Performance Inline MERGE (Upsert) Engine (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/04_bigquery_inline_merge_upsert_en.md)**: Executes direct inline MERGE INTO via `UNNEST(JSON_QUERY_ARRAY(@json_payload))` without temporary staging tables, automatic primary key routing, original column preservation (`preserve_columns_list`), schema type inference and casting (`column_types_dict`), reserved keyword and Unicode column backtick escaping, HTTP 413 payload limit protection via default 100-row chunking.
- **3.5. [BigQuery TIMESTAMP and DATETIME String Conversion (`convert_to_bigquery_timestamp`, `convert_to_bigquery_datetime`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/05_bigquery_timestamp_and_datetime_conversion_en.md)**: Normalizes ISO 8601, whitespace-separated, and 14-digit/8-digit date strings into standard strings for `TIMESTAMP` columns (with a time zone offset, precedence via `timezone_offset_str`) and for `DATETIME` columns (wall-clock `YYYY-MM-DD HH:MM:SS` without an offset).
- **3.6. [GCP Service Account Credential Resolver (`GcpCredentialResolver`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/06_gcp_credential_resolver_en.md)**: Standalone class dedicated to resolving GCP credentials by a four-tier precedence (environment JSON → environment file path → configured file path → ADC). Used by `GcsClient` and `BigQueryClient` through composition, and reusable on its own for other GCP services.

#### 4. Dynamic Tool Loader & Template Evaluator (`agent_common.tool_parser`) & Built-in Tools (`agent_common.tool`)
- **4.1. [Dual Tool Hierarchy Discovery & Dynamic Loading (`ToolParser.load_tool_function`)](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/01_dual_tool_hierarchy_discovery_en.md)**:
  - **Priority 1 (Built-in Tools)**: Modules under `agent_common/tool/` (standard enterprise tools).
  - **Priority 2 (Project Tools)**: Local path configured in `config.yml` under `transfer.tool_dir_str` (e.g., `medallion/tool/`).
- **4.2. [Declarative Template Evaluation & Expression Resolution (`ToolParser.eval`)](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/02_declarative_template_eval_en.md)**:
  - Variable namespace binding: `{ecs.key}`, `{sys.today}`, `{json.title}`.
  - Dynamic tool function invocation: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - Pipe (`|`) fallback chains and default values: `"{meta.title|json.title|'Default Title'}"`.
- **4.3. [Safe Namespace Lookup & Case-Insensitive Access (`_SafeNamespace`)](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/03_safe_namespace_navigation_en.md)**: Unified dot-notation and bracket indexing, resilient case-insensitive key resolution, empty string (`""`) fallback on missing keys, recursive nested collection wrapping.
- **4.4. [Built-in DateTime Tool (`DateTimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/04_builtin_datetime_utils_en.md)**: Business rule and template formatting tool delegating core timezone calculations to `TimeUtils`.

#### 5. Progress Tracker & Common Utilities (`agent_common.progress_tracker`, `agent_common.table_formatter`, `agent_common.time_utils`)
- **5.1. [System Timezone Detection, Global Timezone Resolution & Datetime Normalization (`TimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/en/utils/01_time_utils_and_timezone_resolution_en.md)**: Dynamic host OS system timezone detection, 30+ world timezone parsing, ISO 8601 offset calculation, and `parse_datetime` normalization core utility.
- **5.2. [Multithreaded Progress Tracking & Milestone Telemetry (`ProgressTracker`)](https://github.com/kampores/agent_common/blob/main/manual/en/utils/02_progress_tracker_and_milestones_en.md)**: Real-time multithreaded progress tracking (`[N/Total] (P%)`), throughput/ETA calculation, and tiered logging (standard `INFO` vs 10% milestone `WARNING` level elevation).
- **5.3. [Unicode East Asian Width Alignment & Table Formatter (`TableFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/en/utils/03_unicode_table_formatter_en.md)**: Precision terminal and Markdown table column width alignment utility calculating Unicode East Asian character display widths (`unicodedata.east_asian_width`).

#### 6. Common Error & Exception Handler (`agent_common.error_handler`)
- Consistent exception logging and handling for network failures, configuration errors, and runtime exceptions.

#### 7. Unified LLM Client & Inference Engine (`agent_common.llm`)
- **7.1. [Model Profiles and Text Generation](https://github.com/kampores/agent_common/blob/main/manual/en/llm/01_model_profiles_and_generation_en.md)**
- **7.2. [External Chat APIs and Fabrix](https://github.com/kampores/agent_common/blob/main/manual/en/llm/02_external_api_and_fabrix_en.md)**
- **7.3. [Local GGUF Inference and Model Caching](https://github.com/kampores/agent_common/blob/main/manual/en/llm/03_local_gguf_inference_en.md)**
- **7.4. [Provider Selection and Conditional Local Fallback](https://github.com/kampores/agent_common/blob/main/manual/en/llm/04_provider_and_local_fallback_en.md)**
- **7.5. [Inference Results and Error Handling](https://github.com/kampores/agent_common/blob/main/manual/en/llm/05_inference_results_and_errors_en.md)**
- **7.6. [Groq Supervisor and Antigravity Stop Hook](https://github.com/kampores/agent_common/blob/main/manual/en/llm/06_groq_supervisor_and_stop_hook_en.md)**

#### 8. Language Localizer (`agent_common.localizer`)
- **8.1. [Language Code Normalization & Localized Resource Lookup (`Localizer`)](https://github.com/kampores/agent_common/blob/main/manual/en/localizer/01_language_codes_and_resource_lookup_en.md)**: Normalizes ISO 639-1 language codes (`KO`, `EN`, `ZH`, `JA`), decides the language from an explicit argument, the global setting, and environment variables, and finds per-language resource files named `{prefix}_{language}.yml`. Separate from logging, so it can be reused for any multilingual resource such as labels and notices.

---

### 🛠️ Usage Examples

#### 1. Dot-Notation Global `config` & Type Guarantees
```python
from agent_common.config_loader import config

# 1) Guaranteed type coercion via type suffixes
max_workers: int = config.transfer.max_workers_int       # Guaranteed int
host: str = config.database.host_str                     # Guaranteed str with .strip()
is_active: bool = config.transfer.is_active_bool         # Guaranteed bool

# 2) Hierarchical attribute access
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. Dynamic Rule Evaluation via ToolParser
```python
from agent_common.tool_parser import ToolParser

tool_parser = ToolParser()

context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. Real-time Progress Tracking with ProgressTracker
```python
from agent_common import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="file")

for file_info in file_list:
    try:
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

tracker.log_summary()
```

#### 4. Unified Text/SQL Generation with LlmClient
```python
from agent_common.llm import LlmClient

llm_client = LlmClient(purpose_str="sql_generator")
prompt_str = "User request: Generate daily subscriber statistics SQL for August 2026."
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="You are an expert AI for BigQuery SQL generation."
)
print(f"Generated result ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. Storage and BigQuery Client Usage
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS Smart Transfer
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery Inline MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "John Doe", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

#### 6. Authenticating Other GCP Services with GcpCredentialResolver
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

# Resolves environment JSON -> environment file path -> given path, and returns None (ADC) when none apply
credentials = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
).resolve()

# Pass it straight to GCP clients other than GCS and BigQuery
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

---

### 📖 Detailed Feature Manuals

| # | Module / Topic | User Manual Link | Key Highlights |
| :---: | :--- | :---: | :--- |
| **1.1** | **Hierarchical YAML Parsing & Deep Merge** | [01_hierarchical_yaml_merge_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/01_hierarchical_yaml_merge_en.md) | 5-stage merge order, recursive `_deep_merge` algorithm, auto project root discovery |
| **1.2** | **Immutable Dot-Notation Access (`ReadOnlyConfig`)** | [02_readonly_dot_notation_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/02_readonly_dot_notation_en.md) | Dot-notation attribute lookup, strict runtime mutation prevention (Read-Only) |
| **1.3** | **Type Guarantee & Automatic Coercion** | [03_type_coercion_and_guarantee_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/03_type_coercion_and_guarantee_en.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` runtime casting and type safety |
| **1.4** | **Fail-Fast Required Setting Validation** | [04_fail_fast_require_setting_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/04_fail_fast_require_setting_en.md) | Startup phase mandatory validation, diagnostic output, and fail-fast termination |
| **1.5** | **Network Proxy Control** | [05_network_proxy_control_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/05_network_proxy_control_en.md) | Automatic synchronization of `NO_PROXY` from `proxy.no_proxy` configuration |
| **1.6** | **Constant Externalization & Self-Healing Templates** | [06_ensure_config_self_healing_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/06_ensure_config_self_healing_en.md) | Materializing all in-code constants, automatic scaffolding, and in-place missing key injection |
| **2.1** | **Single-Line Formatter & Origin Tracking** | [01_single_line_flatten_formatter_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/01_single_line_flatten_formatter_en.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` frame extraction, centralized log collector optimization |
| **2.2** | **Batch Logging Setup & Handler Control** | [02_project_logger_configure_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/02_project_logger_configure_en.md) | `ProjectLogger.configure()`, console/file handler routing, level-based paths, unified path template |
| **2.3** | **Multilingual Catalog & Code-Based Logging** | [03_multilingual_message_catalog_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/03_multilingual_message_catalog_en.md) | `logging_messages_*.yml`, runtime language switching, safe template variable formatting |
| **2.4** | **Result Telemetry & Error Classification** | [04_execution_result_and_error_tracking_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/04_execution_result_and_error_tracking_en.md) | Success/Failure/Exclusion 3-tier classification, instance & class-global multithreaded counters |
| **2.5** | **Automatic Summary Report Generation** | [05_summary_report_generation_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/05_summary_report_generation_en.md) | `ProjectLogger.log_summary()`, 80-column summary block, throughput/bandwidth, decoded error explanations |
| **3.1** | **AWS S3 & Dell ECS Storage Integration** | [01_s3_ecs_storage_client_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/01_s3_ecs_storage_client_en.md) | S3/ECS connection, Fail-Fast verification, paginated listing, direct GCS streaming and duplicate skip |
| **3.2** | **GCS Streaming Upload & 4-Tier Auth** | [02_gcs_cloud_storage_client_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/02_gcs_cloud_storage_client_en.md) | 4-tier GCP credential precedence, connection validation, metadata retrieval, in-memory stream upload |
| **3.3** | **BigQuery Batch Loading & Streaming Ingestion** | [03_bigquery_batch_and_streaming_load_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/03_bigquery_batch_and_streaming_load_en.md) | JSON batch load jobs vs streaming API, nested error diagnostics unpacking, deduplication key lookup |
| **3.4** | **BigQuery Inline MERGE (Upsert) Engine** | [04_bigquery_inline_merge_upsert_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/04_bigquery_inline_merge_upsert_en.md) | Pure inline MERGE without staging tables, UNNEST parameter binding, dynamic type casting, 100-row chunks |
| **3.5** | **BigQuery TIMESTAMP & DATETIME Conversion** | [05_bigquery_timestamp_and_datetime_conversion_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/05_bigquery_timestamp_and_datetime_conversion_en.md) | ISO/compact datetime normalization, time zone offset precedence, choosing a method by column type |
| **3.6** | **GCP Service Account Credential Resolver** | [06_gcp_credential_resolver_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/06_gcp_credential_resolver_en.md) | `GcpCredentialResolver`, 4-tier credential precedence, standalone reuse for other GCP services, composition design |
| **4.1** | **Dual Tool Hierarchy Discovery & Dynamic Loading** | [01_dual_tool_hierarchy_discovery_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/01_dual_tool_hierarchy_discovery_en.md) | Built-in (Priority 1) vs Local (Priority 2) discovery, 3-step function introspection, `_tool_cache`, `scan_rules_for_tool_functions` pre-flight validation |
| **4.2** | **Declarative Template Evaluation & Expression Resolution** | [02_declarative_template_eval_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/02_declarative_template_eval_en.md) | `ToolParser.eval()`, direct tool calls, dot-notation namespaces, pipe (`\|`) fallbacks, signature-aware parameter binding, and automatic context injection |
| **4.3** | **Safe Namespace Lookup & Case-Insensitive Access** | [03_safe_namespace_navigation_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/03_safe_namespace_navigation_en.md) | `_SafeNamespace`, case-insensitive lookups, silent empty-string (`""`) fallback on missing keys, recursive nested collection wrapping |
| **4.4** | **Built-in DateTime Tool (`DateTimeUtils`)** | [04_builtin_datetime_utils_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/tool_parser/04_builtin_datetime_utils_en.md) | Business template formatting tool, `TimeUtils` delegation architecture, `YYYYMMDD`, BigQuery ISO timestamps, and compact datetime strings |
| **5.1** | **System Timezone Detection & Global Timezone Resolution** | [01_time_utils_and_timezone_resolution_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/utils/01_time_utils_and_timezone_resolution_en.md) | `TimeUtils`, dynamic host OS/container timezone detection, 30+ global timezone abbreviation parser, timezone-aware datetime normalization |
| **5.2** | **Multithreaded Progress Tracking & Milestone Telemetry** | [02_progress_tracker_and_milestones_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/utils/02_progress_tracker_and_milestones_en.md) | `ProgressTracker`, real-time percentage (`%`), throughput, ETA, standard `INFO` vs 10% milestone `WARNING` level elevation |
| **5.3** | **Unicode East Asian Width Alignment & Table Formatter** | [03_unicode_table_formatter_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/utils/03_unicode_table_formatter_en.md) | `TableFormatter`, precise East Asian character display width calculation, monospace and Markdown table vertical border alignment |
| **7.1** | **Model Profiles and Text Generation** | [01_model_profiles_and_generation_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/01_model_profiles_and_generation_en.md) | `agent_common.llm` |
| **7.2** | **External Chat APIs and Fabrix** | [02_external_api_and_fabrix_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/02_external_api_and_fabrix_en.md) | `agent_common.llm` |
| **7.3** | **Local GGUF Inference and Model Caching** | [03_local_gguf_inference_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/03_local_gguf_inference_en.md) | `agent_common.llm` |
| **7.4** | **Provider Selection and Conditional Local Fallback** | [04_provider_and_local_fallback_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/04_provider_and_local_fallback_en.md) | `agent_common.llm` |
| **7.5** | **Inference Results and Error Handling** | [05_inference_results_and_errors_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/05_inference_results_and_errors_en.md) | `agent_common.llm` |
| **7.6** | **Groq Supervisor and Antigravity Stop Hook** | [06_groq_supervisor_and_stop_hook_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/llm/06_groq_supervisor_and_stop_hook_en.md) | `agent_common.llm` |
| **8.1** | **Language Code Normalization & Localized Resource Lookup** | [01_language_codes_and_resource_lookup_en.md](https://github.com/kampores/agent_common/blob/main/manual/en/localizer/01_language_codes_and_resource_lookup_en.md) | `Localizer`, supported language codes and aliases, language precedence, per-language file lookup with default-language fallback |

---

### 🚀 Installation and Build Guide

#### 📦 Wheel Package Build (.whl)
```bash
# Offline environment
python scripts/build_agent_common_whl.py

# Online environment
python -m build agent_common --wheel -o whls/
```

#### Installing the Wheel Package
```bash
# Development (Editable mode - lightweight core)
pip install -e agent_common

# Development (With cloud client extras)
pip install -e "agent_common[clients]"

# Production (Wheel package)
pip install dist/agent_common-0.4.98-py3-none-any.whl
```

#### 🌐 Official PyPI Distribution (Maintainers Only)
```bash
# 1. Update build tools
pip install build twine

# 2. Build distributions (sdist & wheel)
python -m build

# 3. Validate distribution archives
python -m twine check dist/*

# 4. Upload to PyPI
python -m twine upload dist/agent_common-0.4.98*
```

---

### 📋 Version History (Changelog)

For detailed version history, please refer to [CHANGELOG_EN.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_EN.md).

---

## agent_common 软件包 (中文)

面向企业级智能体（Agent）服务与数据迁移/生成管道的通用 Python 核心库，提供统一日志记录、分层配置加载、云端与数据库基础设施客户端、动态工具解析器及集中异常处理。

---

### 📌 核心功能

#### 1. 配置加载器与不可变配置对象 (`agent_common.config_loader`)
- **1.1. [分层 YAML 解析与深度合并 (Deep Merge)](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/01_hierarchical_yaml_merge_zh.md)**: 动态合并包内置默认配置 (`agent_common/config/*.yml`) 与各独立项目配置 (`config/*.yml`)。
- **1.2. [不可变点属性访问 (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/02_readonly_dot_notation_zh.md)**: 直观的点操作符属性访问 (`config.ecs.endpoint_url`, `config.transfer.max_workers_int`)，彻底杜绝运行时配置意外篡改。
- **1.3. [基于类型后缀的自动类型转换与类型保证](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/03_type_coercion_and_guarantee_zh.md)**:
  - `_int`: 自动整型转换与类型保证。
  - `_float`: 自动浮点型转换与类型保证。
  - `_bool`: 严格布尔型转换与类型保证（支持 Python `bool` 或不区分大小写的 `"true"`/`"false"`，传入 `0`、`1` 等非布尔值时快速失败拦截）。
  - `_str`: 自动字符串转换与 `.strip()` 空格清理。
  - `_list` / `_dict`: 保证列表 / 不可变字典 (`ReadOnlyConfig`) 包装。
  - 提供独立函数 `coerce_type_by_key_suffix` 与嵌套字典批量转换 `coerce_dict_by_key_suffix`，全面支持任意外部配置文件 (`rule.yml`, `mapping.yml`) 和数据流。
  - 严格快速失败 (Fail-Fast) 保证：类型不匹配时立即抛出详细诊断异常 (`ValueError`/`TypeError`)，绝不静默降级为原始值。
- **1.4. [快速失败必需配置验证 (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/04_fail_fast_require_setting_zh.md)**: 程序启动阶段若缺少必要配置项，立即输出详细诊断日志并安全终止进程。
- **1.5. [网络代理控制 (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/05_network_proxy_control_zh.md)**: 自动将 `proxy.no_proxy` 配置同步至 `NO_PROXY` 环境变量，绕过内部通信代理。
- **1.6. [常量外部化与自愈模板校正 (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/06_ensure_config_self_healing_zh.md)**: 将代码中所有常量外部化为配置文件，自动生成 `config.yml` 并强制注入/补齐缺失的配置键。`agent_common` 各类的默认配置仅写入在 `config_loader.config_file_auto_repair_dict` 中设为 `true` 的类。

#### 2. 单行日志格式化器与项目日志器 (`agent_common.logger`)
- **2.1. [单行扁平化格式化器与源头位置追踪 (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/01_single_line_flatten_formatter_zh.md)**: 扁平化多行日志与 Traceback 异常，提取 `[Origin: ...]` 根源调用栈，针对集中式日志收集器（Logstash、Fluentd、CloudWatch）优化。
- **2.2. [批量日志环境配置与处理器控制 (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/02_project_logger_configure_zh.md)**: 控制台与文件日志处理器动态创建，按日期分目录归档，按执行日志级别自动分流 (`{log_level_str}` 统一日志路径)。
- **2.3. [多语言日志消息字典与基于代码的日志记录 (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/03_multilingual_message_catalog_zh.md)**: 依据配置自动联动中文/英文/韩文/日文消息字典，支持运行时动态语言切换与安全的模板占位符替换。
- **2.4. [任务进度统计与异常/跳过分类实时汇总 (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/04_execution_result_and_error_tracking_zh.md)**: 成功、失败、跳过 (Skip) 三级状态分类，支持实例级与类全局多线程遥测。
- **2.5. [自动生成任务执行总结报告 (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/05_summary_report_generation_zh.md)**: 确保“总计 = 成功 + 失败 + 跳过”严格一致，自动生成对齐的标准 Markdown 表格，包含耗时、处理吞吐量、传输速率与错误诊断。

#### 3. 存储与数据库基础设施客户端 (`agent_common.clients`)
- **3.1. [AWS S3 与 Dell ECS 对象存储客户端 (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/01_s3_ecs_storage_client_zh.md)**: 连接 AWS S3 及 Dell ECS（S3 兼容）存储，初始化即执行 `head_bucket` 快速失败校验，海量对象分页迭代器 (`list_objects`)，元数据快速查询 (`get_object_size`)，流式读取 (`get_object_stream`)，GCS 实时流式传输与相同文件智能跳过 (`transfer_to_gcs`)。
- **3.2. [Google Cloud Storage 流式客户端与多层级认证 (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/02_gcs_cloud_storage_client_zh.md)**: 4 级 GCP 认证回退体系 (`GOOGLE_APPLICATION_CREDENTIALS_JSON` 内存 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 文件 -> `credentials_path_str` -> Google ADC)，存储桶连通性早验，分块流式上传零临时文件占用 (`upload_stream`)。
- **3.3. [BigQuery 批量加载与流式插入客户端 (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/03_bigquery_batch_and_streaming_load_zh.md)**: 快速失败架构与表元数据缓存 (`get_table`)，JSON 批量加载作业 (`load_table_from_json_data`) 深度展开嵌套错误，实时流式写入 (`insert_rows_json_data`)，同步 SQL 查询 (`query`)，防重唯一键集合提取 (`get_existing_keys`)。
- **3.4. [BigQuery 高性能内联 MERGE (Upsert) 引擎 (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/04_bigquery_inline_merge_upsert_zh.md)**: 无需临时暂存表，基于 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 执行内联 MERGE INTO，主键自动更新/插入，保留初始列值 (`preserve_columns_list`)，列类型推断与显式转换，防 HTTP 413 载荷超限默认 100 行自动切片。
- **3.5. [BigQuery TIMESTAMP 与 DATETIME 日期时间字符串转换 (`convert_to_bigquery_timestamp`, `convert_to_bigquery_datetime`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/05_bigquery_timestamp_and_datetime_conversion_zh.md)**: 将 ISO 8601、空格分隔、14 位/8 位数字等各类源日期字符串规范化为 `TIMESTAMP` 列用（带时区偏移量，优先级 `timezone_offset_str`）与 `DATETIME` 列用（不带偏移量的钟表时刻 `YYYY-MM-DD HH:MM:SS`）的标准字符串。
- **3.6. [GCP 服务账号认证解析器 (`GcpCredentialResolver`)](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/06_gcp_credential_resolver_zh.md)**: 按 4 级优先级（环境变量 JSON → 环境变量文件路径 → 配置文件路径 → ADC）专门负责 GCP 认证解析的独立类。`GcsClient`、`BigQueryClient` 通过组合 (Composition) 使用，也可在其他 GCP 服务中单独复用。

#### 4. 动态工具加载器与模板评估器 (`agent_common.tool_parser`) & 内置工具 (`agent_common.tool`)
- **4.1. [双层 Tool 目录层级发现与动态加载 (`ToolParser.load_tool_function`)](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/01_dual_tool_hierarchy_discovery_zh.md)**:
  - **优先级 1 (内置工具)**: `agent_common/tool/` 下属模块（企业标准内置工具）。
  - **优先级 2 (项目工具)**: `config.yml` 中 `transfer.tool_dir_str` 指定的本地路径（如 `medallion/tool/`）。
- **4.2. [声明式模板替换与表达式评估 (`ToolParser.eval`)](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/02_declarative_template_eval_zh.md)**:
  - 变量命名空间绑定: `{ecs.key}`, `{sys.today}`, `{json.title}`。
  - 动态工具函数调用: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - 管道符 (`|`) 链式降级与默认值: `"{meta.title|json.title|'默认标题'}"`.
- **4.3. [安全命名空间导航 (`_SafeNamespace`)](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/03_safe_namespace_navigation_zh.md)**: 点 (.) 与中括号索引统一访问，不区分大小写，缺失键返回 `""` 避免 `KeyError`，嵌套集合安全递归包装。
- **4.4. [内置通用日期时间工具 (`DateTimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/04_builtin_datetime_utils_zh.md)**: 表规则与模板评估专用日期工具，时区核心运算委托给 `TimeUtils` 协同分工。

#### 5. 进度跟踪器、表格格式化器与时间工具 (`agent_common.progress_tracker`, `agent_common.table_formatter`, `agent_common.time_utils`)
- **5.1. [主机系统时区探测、全球标准时区解析与日期规范化 (`TimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/01_time_utils_and_timezone_resolution_zh.md)**: 动态自动探测主机系统时区，解析全球 30+ 常见标准时区缩写，计算 ISO 8601 偏移量，提供时区感知转换核心 `parse_datetime`。
- **5.2. [多线程实时进度跟踪与里程碑警报 (`ProgressTracker`)](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/02_progress_tracker_and_milestones_zh.md)**: 多线程实时进度跟踪 (`[N/Total] (P%)`)，处理吞吐量与预计剩余时间 (ETA) 计算，常规 `INFO` 与 10% 整数倍里程碑 `WARNING` 升级记录。
- **5.3. [Unicode 全角字符宽度计算与 Markdown/控制台表格对齐格式化器 (`TableFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/03_unicode_table_formatter_zh.md)**: 基于东亚字符宽度 (`unicodedata.east_asian_width`) 精确计算，实现汉字/全角(2格)与英文(1格)在控制台与 Markdown 表格中的对齐。

#### 6. 通用错误与异常处理器 (`agent_common.error_handler`)
- 提供网络中断、配置缺失及运行时异常的一致日志记录与规范处理。

#### 7. 统一 LLM 客户端与推理引擎 (`agent_common.llm`)
- **7.1. [模型配置文件管理与文本生成](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/01_model_profiles_and_generation_zh.md)**
- **7.2. [外部聊天 API 与 Fabrix 集成](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/02_external_api_and_fabrix_zh.md)**
- **7.3. [本地 GGUF 推理与模型缓存](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/03_local_gguf_inference_zh.md)**
- **7.4. [执行模式与条件化本地切换](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/04_provider_and_local_fallback_zh.md)**
- **7.5. [推理结果与异常处理](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/05_inference_results_and_errors_zh.md)**
- **7.6. [Groq 监督员 AI 与 Antigravity Stop 钩子](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/06_groq_supervisor_and_stop_hook_zh.md)**

#### 8. 语言本地化器 (`agent_common.localizer`)
- **8.1. [语言代码规范化与多语言资源文件查找 (`Localizer`)](https://github.com/kampores/agent_common/blob/main/manual/zh/localizer/01_language_codes_and_resource_lookup_zh.md)**: 规范化 ISO 639-1 语言代码 (`KO`, `EN`, `ZH`, `JA`)，基于显式参数、全局设置与环境变量决定语言，并查找 `{前缀}_{语言}.yml` 形式的多语言资源文件。与日志功能相互独立，可复用于标签、提示文案等任意多语言资源。

---

### 🛠️ 使用示例 (Usage Examples)

#### 1. 点属性访问全局 `config` 与类型保证
```python
from agent_common.config_loader import config

# 1) 基于类型后缀自动强制转换保证
max_workers: int = config.transfer.max_workers_int       # 保证 int 类型
host: str = config.database.host_str                     # 保证 str 类型并自动执行 .strip()
is_active: bool = config.transfer.is_active_bool         # 保证 bool 类型

# 2) 分层属性点访问
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. 通过 ToolParser 动态评估规则
```python
from agent_common.tool_parser import ToolParser

tool_parser = ToolParser()

context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. 使用 ProgressTracker 实时追踪进度
```python
from agent_common import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="文件")

for file_info in file_list:
    try:
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

tracker.log_summary()
```

#### 4. 使用 LlmClient 进行统一文本/SQL生成
```python
from agent_common.llm import LlmClient

llm_client = LlmClient(purpose_str="sql_generator")
prompt_str = "用户需求: 请编写统计 2026 年 8 月每日新增订阅用户数的 SQL 查询。"
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="你是一名精通 BigQuery SQL 编写的专业 AI 助手。"
)
print(f"生成结果 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. 存储与 BigQuery 客户端操作示例
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS 智能流式传输
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery 高性能内联 MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "张三", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

#### 6. 使用 GcpCredentialResolver 为其他 GCP 服务认证
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

# 按 环境变量 JSON → 环境变量文件路径 → 指定路径 的顺序解析，均不存在时返回 None (ADC)
credentials = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
).resolve()

# 可直接传给 GCS、BigQuery 以外的 GCP 客户端
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

---

### 📖 详细功能用户手册 (User Manuals)

| 编号 | 模块 / 主题 | 详细手册链接 | 核心要点说明 |
| :---: | :--- | :---: | :--- |
| **1.1** | **分层 YAML 解析 & 深度合并** | [01_hierarchical_yaml_merge_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/01_hierarchical_yaml_merge_zh.md) | 5 阶段配置加载合并顺序，递归 `_deep_merge` 算法，项目根目录自动探测 |
| **1.2** | **不可变点属性访问 (`ReadOnlyConfig`)** | [02_readonly_dot_notation_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/02_readonly_dot_notation_zh.md) | 点属性操作符访问，严格杜绝运行时篡改 (Read-Only)，不可变结构设计 |
| **1.3** | **类型后缀自动转换 & 类型安全保证** | [03_type_coercion_and_guarantee_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/03_type_coercion_and_guarantee_zh.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 运行时自动类型转换及安全保证 |
| **1.4** | **快速失败必需配置验证** | [04_fail_fast_require_setting_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/04_fail_fast_require_setting_zh.md) | 启动阶段检测缺失配置，输出清晰诊断日志并即时中止进程 |
| **1.5** | **网络代理控制** | [05_network_proxy_control_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/05_network_proxy_control_zh.md) | 自动将 `proxy.no_proxy` 配置同步至 `NO_PROXY` 环境变量并绕过代理 |
| **1.6** | **常量外部化与自愈模板校正** | [06_ensure_config_self_healing_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/config_loader/06_ensure_config_self_healing_zh.md) | 代码中所有常量配置化（外部化），自动生成 `config.yml` 并强制注入缺失配置项 |
| **2.1** | **单行扁平化格式化器 & 根源追踪** | [01_single_line_flatten_formatter_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/01_single_line_flatten_formatter_zh.md) | `SingleLineFlattenFormatter`，`[Origin: ...]` 堆栈调用帧提取，适配日志收集器 |
| **2.2** | **批量日志配置 & 处理器控制** | [02_project_logger_configure_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/02_project_logger_configure_zh.md) | `ProjectLogger.configure()`，控制台/文件处理器动态分配，按日志级别路径归档 |
| **2.3** | **多语言消息字典 & 基于代码的日志** | [03_multilingual_message_catalog_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/03_multilingual_message_catalog_zh.md) | `logging_messages_*.yml`，运行时语言平滑切换，`safe_kwargs` 安全模板占位符 |
| **2.4** | **执行结果统计 & 错误分类实时汇总** | [04_execution_result_and_error_tracking_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/04_execution_result_and_error_tracking_zh.md) | 成功/失败/跳过 (Skip) 三级状态分类，实例与类全局多线程统计指标汇总 |
| **2.5** | **任务执行总结报告自动生成** | [05_summary_report_generation_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/logger/05_summary_report_generation_zh.md) | `ProjectLogger.log_summary()`，80 列标准对齐摘要块，吞吐量/带宽，错误归因解析 |
| **3.1** | **AWS S3 & Dell ECS 存储集成** | [01_s3_ecs_storage_client_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/01_s3_ecs_storage_client_zh.md) | S3/ECS 连接连通性早验，海量对象分页遍历，流式直传 GCS 与相同文件跳过 |
| **3.2** | **GCS 流式上传 & 4 级认证体系** | [02_gcs_cloud_storage_client_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/02_gcs_cloud_storage_client_zh.md) | 4 级服务账号凭证优先级，连接验证，元数据获取，零磁盘暂存分块流式上传 |
| **3.3** | **BigQuery 批量加载 & 流式插入** | [03_bigquery_batch_and_streaming_load_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/03_bigquery_batch_and_streaming_load_zh.md) | JSON 批量加载 vs 流式 API，嵌套错误解包，防重已有唯一键集合提取 |
| **3.4** | **BigQuery 内联 MERGE (Upsert) 引擎** | [04_bigquery_inline_merge_upsert_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/04_bigquery_inline_merge_upsert_zh.md) | 无需中间临时表的内联 MERGE，UNNEST 参数化绑定，动态类型转换，100 条分片 |
| **3.5** | **BigQuery TIMESTAMP 与 DATETIME 转换** | [05_bigquery_timestamp_and_datetime_conversion_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/05_bigquery_timestamp_and_datetime_conversion_zh.md) | ISO 与压缩日期时间规范化，时区偏移量决定优先级，按列类型选择方法 |
| **3.6** | **GCP 服务账号认证解析器** | [06_gcp_credential_resolver_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/clients/06_gcp_credential_resolver_zh.md) | `GcpCredentialResolver`、4 级认证优先级、在其他 GCP 服务中单独复用、组合 (Composition) 结构 |
| **4.1** | **双层 Tool 目录结构发现 & 动态加载** | [01_dual_tool_hierarchy_discovery_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/01_dual_tool_hierarchy_discovery_zh.md) | 内置 (优先 1) 与项目本地 (优先 2) 发现机制，3 阶段函数内省，`_tool_cache` 预校验 |
| **4.2** | **声明式模板替换 & 表达式评估** | [02_declarative_template_eval_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/02_declarative_template_eval_zh.md) | `ToolParser.eval()`，工具函数直调，点号命名空间绑定，管道符 (`\|`) 兜底降级 |
| **4.3** | **安全命名空间导航 (`_SafeNamespace`)** | [03_safe_namespace_navigation_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/03_safe_namespace_navigation_zh.md) | 点/中括号通用解析，不区分大小写，缺字段静默返回 `""`，递归封装嵌套容器 |
| **4.4** | **内置通用日期时间工具 (`DateTimeUtils`)** | [04_builtin_datetime_utils_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/tool_parser/04_builtin_datetime_utils_zh.md) | 规则与模板专用日期工具，时区底层计算委托 `TimeUtils`，生成 ISO 与紧凑日期 |
| **5.1** | **主机时区探测 & 全球标准时区解析** | [01_time_utils_and_timezone_resolution_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/01_time_utils_and_timezone_resolution_zh.md) | `TimeUtils`，动态探测系统/容器时区，解析全球 30+ 标准时区，datetime 规范化 |
| **5.2** | **多线程实时进度跟踪 & 里程碑记录** | [02_progress_tracker_and_milestones_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/02_progress_tracker_and_milestones_zh.md) | `ProgressTracker`，实时百分比 (`%`)、吞吐率、预计剩余时间，`WARNING` 里程碑 |
| **5.3** | **Unicode 全角字符宽度计算与表格对齐** | [03_unicode_table_formatter_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/utils/03_unicode_table_formatter_zh.md) | `TableFormatter`，基于 `east_asian_width` 计算，汉字全角(2格)与英文(1格)对齐 |
| **7.1** | **模型配置文件管理与文本生成** | [01_model_profiles_and_generation_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/01_model_profiles_and_generation_zh.md) | `agent_common.llm` |
| **7.2** | **外部聊天 API 与 Fabrix 集成** | [02_external_api_and_fabrix_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/02_external_api_and_fabrix_zh.md) | `agent_common.llm` |
| **7.3** | **本地 GGUF 推理与模型缓存** | [03_local_gguf_inference_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/03_local_gguf_inference_zh.md) | `agent_common.llm` |
| **7.4** | **执行模式与条件化本地切换** | [04_provider_and_local_fallback_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/04_provider_and_local_fallback_zh.md) | `agent_common.llm` |
| **7.5** | **推理结果与异常处理** | [05_inference_results_and_errors_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/05_inference_results_and_errors_zh.md) | `agent_common.llm` |
| **7.6** | **Groq 监督员 AI 与 Antigravity Stop 钩子** | [06_groq_supervisor_and_stop_hook_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/llm/06_groq_supervisor_and_stop_hook_zh.md) | `agent_common.llm` |
| **8.1** | **语言代码规范化 & 多语言资源查找** | [01_language_codes_and_resource_lookup_zh.md](https://github.com/kampores/agent_common/blob/main/manual/zh/localizer/01_language_codes_and_resource_lookup_zh.md) | `Localizer`、支持的语言代码与别名、语言决定优先级、多语言文件查找及默认语言回退规则 |

---

### 🚀 安装与构建指南 (Installation and Build Guide)

#### 📦 构建 Wheel 安装包 (.whl)
```bash
# 离线环境
python scripts/build_agent_common_whl.py

# 联网环境
python -m build agent_common --wheel -o whls/
```

#### 安装 Wheel 软件包
```bash
# 开发环境 (Editable 可编辑模式 - 核心轻量安装)
pip install -e agent_common

# 开发环境 (包含云端客户端 extras)
pip install -e "agent_common[clients]"

# 生产环境 (安装 Wheel 包)
pip install dist/agent_common-0.4.98-py3-none-any.whl
```

#### 🌐 官方 PyPI 镜像分发（仅限维护者）
```bash
# 1. 更新构建工具
pip install build twine

# 2. 构建分发包 (同时生成 sdist 与 wheel)
python -m build

# 3. 校验分发归档完整性
python -m twine check dist/*

# 4. 上传至 PyPI
python -m twine upload dist/agent_common-0.4.98*
```

---

### 📋 版本变更历史 (Changelog)

详细版本变更历史请参阅 [CHANGELOG_ZH.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_ZH.md) 文件。

---

## agent_common パッケージ (日本語)

エンタープライズ AI エージェントサービスおよびデータ移行・生成パイプラインのための共通 Python コアライブラリです。統合ロギング、階層型設定ローダー、クラウドおよびデータベースインフラクライアント、動的ツールパーサー、集中エラー処理を提供します。

---

### 📌 主な機能

#### 1. 設定ローダーおよび不変設定オブジェクト (`agent_common.config_loader`)
- **1.1. [階層型 YAML 解析およびディープマージ (Deep Merge)](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/01_hierarchical_yaml_merge_ja.md)**: パッケージ組み込みデフォルト設定 (`agent_common/config/*.yml`) とプロジェクト固有設定 (`config/*.yml`) を動的にマージ。
- **1.2. [不変ドット記法アクセス (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/02_readonly_dot_notation_ja.md)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 形式の直感的な属性アクセスとランタイム改ざん防止。
- **1.3. [型サフィックス自動型変換および型保証](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/03_type_coercion_and_guarantee_ja.md)**:
  - `_int`: 自動整数変換および型保証。
  - `_float`: 自動浮動小数点数変換および型保証。
  - `_bool`: 厳格なブール型変換および型保証（Python `bool` または大文字小文字不問の `"true"`, `"false"` をサポートし、`0`, `1` など非ブール値流入時は Fail-Fast 遮断）。
  - `_str`: 自動文字列変換および `.strip()` 空白トリミング。
  - `_list` / `_dict`: リスト / 不変辞書 (`ReadOnlyConfig`) ラッピング保証。
  - 汎用関数 `coerce_type_by_key_suffix` およびネスト辞書一括変換 `coerce_dict_by_key_suffix` により、外部設定ファイル (`rule.yml`, `mapping.yml`) やデータパイプラインを完全サポート。
  - 厳格な Fail-Fast 保証: 型不一致時は詳細な診断例外 (`ValueError`/`TypeError`) を即座に発生。
- **1.4. [Fail-Fast 必須設定検証 (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/04_fail_fast_require_setting_ja.md)**: プログラム起動時に必須設定値が欠落している場合、詳細原因を出力してプロセスを即座に終了。
- **1.5. [ネットワークプロキシ制御 (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/05_network_proxy_control_ja.md)**: `proxy.no_proxy` 設定を `NO_PROXY` 環境変数に自動反映し、内部通信プロキシをバイパス。
- **1.6. [全定数の設定ファイル外部化および自己修復テンプレート補正 (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/06_ensure_config_self_healing_ja.md)**: コード内の全定数を設定ファイル化、`config.yml` の自動生成および欠落キーの強制補正。`agent_common` クラスの既定設定は `config_loader.config_file_auto_repair_dict` で `true` にしたクラスのみ書き込む。

#### 2. 単一行ログフォーマッターおよびロガー (`agent_common.logger`)
- **2.1. [単一行フラット化フォーマッターおよび例外発生源追跡 (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/01_single_line_flatten_formatter_ja.md)**: 全ログおよびトレースバックを1行にフラット化し、`[Origin: ...]` 発生源位置を抽出。集中ログ収集基盤（Logstash, Fluentd, CloudWatch）に最適化。
- **2.2. [一括ロギング構成およびハンドラー制御 (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/02_project_logger_configure_ja.md)**: コンソールおよびファイルハンドラーを動的構成、日付別ディレクトリ分離、ログレベル別ディレクトリ自動振り分け。
- **2.3. [多言語メッセージカタログおよびコードベースロギング (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/03_multilingual_message_catalog_ja.md)**: 設定に基づき日本語/英語/韓国語/中国語メッセージ辞書を自動連動、動的言語切り替えおよび安全なテンプレート変数置換。
- **2.4. [タスク進捗統計およびエラー/除外リアルタイム集計 (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/04_execution_result_and_error_tracking_ja.md)**: 成功、失敗、除外 (Skip) の3段階分類とマルチスレッド集計。
- **2.5. [タスク結果要約レポート自動生成 (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/05_summary_report_generation_ja.md)**: 「全体 = 成功 + 失敗 + 除外」整合性保証、処理スループット、転送速度、エラー診断を含む標準 Markdown 表を出力。

#### 3. ストレージおよびデータベースクライアント (`agent_common.clients`)
- **3.1. [AWS S3 および Dell ECS オブジェクトストレージクライアント (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/01_s3_ecs_storage_client_ja.md)**: AWS S3 および Dell ECS (S3互換) 接続、起動時 `head_bucket` 検証、ページネーション一覧取得 (`list_objects`)、メタデータ高速取得 (`get_object_size`)、ストリーミング読み込み (`get_object_stream`)、GCS リアルタイム転送と重複スキップ (`transfer_to_gcs`)。
- **3.2. [Google Cloud Storage ストリーミングクライアントおよび多層認証 (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/02_gcs_cloud_storage_client_ja.md)**: 4段階 GCP 認証階層 (`GOOGLE_APPLICATION_CREDENTIALS_JSON` メモリ JSON -> `GOOGLE_APPLICATION_CREDENTIALS` ファイル -> `credentials_path_str` -> Google ADC)、バケット疎通検証、チャンク単位ストリーム直接アップロード (`upload_stream`)。
- **3.3. [BigQuery バッチロードおよびストリーミング挿入クライアント (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/03_bigquery_batch_and_streaming_load_ja.md)**: テーブルメタデータキャッシュ (`get_table`)、JSON バッチロード Job (`load_table_from_json_data`)、リアルタイムストリーミング挿入 (`insert_rows_json_data`)、同期 SQL クエリ (`query`)、重複防止キー抽出 (`get_existing_keys`)。
- **3.4. [BigQuery 高性能インライン MERGE (Upsert) エンジン (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/04_bigquery_inline_merge_upsert_ja.md)**: 一時テーブル不要で `UNNEST(JSON_QUERY_ARRAY(@json_payload))` によるインライン MERGE INTO 実行、主キー基準の自動 UPDATE/INSERT、作成日時等の初期値保護 (`preserve_columns_list`)、100件チャンク自動分割。
- **3.5. [BigQuery TIMESTAMP・DATETIME 日時文字列変換 (`convert_to_bigquery_timestamp`, `convert_to_bigquery_datetime`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/05_bigquery_timestamp_and_datetime_conversion_ja.md)**: ISO 8601、空白区切り、14桁/8桁の数字など多様な日時文字列を、`TIMESTAMP` 列向け（タイムゾーンオフセット付き、優先順位 `timezone_offset_str`）および `DATETIME` 列向け（オフセットなしの壁時計時刻 `YYYY-MM-DD HH:MM:SS`）の標準文字列へ正規化。
- **3.6. [GCP サービスアカウント認証リゾルバー (`GcpCredentialResolver`)](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/06_gcp_credential_resolver_ja.md)**: 4段階の優先順位（環境変数 JSON → 環境変数のファイルパス → 設定ファイルのパス → ADC）による GCP 認証解決を専任する独立クラス。`GcsClient`・`BigQueryClient` がコンポジションで利用し、その他の GCP サービスでも単独で再利用可能。

#### 4. 動的ツールローダーおよびテンプレート評価器 (`agent_common.tool_parser`) & 組み込みツール (`agent_common.tool`)
- **4.1. [二元化 Tool ディレクトリ階層探索および動的ロード (`ToolParser.load_tool_function`)](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/01_dual_tool_hierarchy_discovery_ja.md)**:
  - **優先度 1 (組み込みツール)**: `agent_common/tool/` 配下モジュール（標準組み込みツール）。
  - **優先度 2 (プロジェクトツール)**: `config.yml` 内の `transfer.tool_dir_str` 指定パス（例: `medallion/tool/`）。
- **4.2. [宣言的テンプレート置換および式評価 (`ToolParser.eval`)](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/02_declarative_template_eval_ja.md)**:
  - 名前空間バインディング: `{ecs.key}`, `{sys.today}`, `{json.title}`。
  - 動的ツール関数呼び出し: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - パイプ (`|`) フォールバック連鎖とデフォルト値: `"{meta.title|json.title|'デフォルトタイトル'}"`.
- **4.3. [安全な名前空間探索 (`_SafeNamespace`)](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/03_safe_namespace_navigation_ja.md)**: ドットおよびブラケットアクセス統合、大文字小文字不問探索、欠落キー `""` 返却、ネスト辞書/リストの安全ラッピング。
- **4.4. [組み込み共通日時ツール (`DateTimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/04_builtin_datetime_utils_ja.md)**: テーブルルールおよびテンプレート専用日時ツール。タイムゾーン中核計算は `TimeUtils` に委譲。

#### 5. 進捗トラッカー、テーブルフォーマッターおよび時間ユーティリティ (`agent_common.progress_tracker`, `agent_common.table_formatter`, `agent_common.time_utils`)
- **5.1. [ホストシステムタイムゾーン検出、世界標準時解決および日時正規化 (`TimeUtils`)](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/01_time_utils_and_timezone_resolution_ja.md)**: ホストシステムタイムゾーン自動検出、世界30以上の標準時解決、ISO 8601 オフセット計算、`parse_datetime` による正規化。
- **5.2. [マルチスレッドリアルタイム進捗追跡およびマイルストーン警告 (`ProgressTracker`)](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/02_progress_tracker_and_milestones_ja.md)**: リアルタイム進捗率表示 (`[N/Total] (P%)`)、スループットおよび予測残り時間 (ETA) 計算、通常 `INFO` と10%単位マイルストーン `WARNING` 昇格ログ。
- **5.3. [Unicode 全角文字幅計算およびテーブル位置合わせフォーマッター (`TableFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/03_unicode_table_formatter_ja.md)**: 東アジア文字幅 (`unicodedata.east_asian_width`) 計算による全角・半角混在時の Markdown / コンソール表縦罫線位置合わせ。

#### 6. 共通エラーおよび例外ハンドラー (`agent_common.error_handler`)
- ネットワーク障害、設定エラー、実行時例外の一貫したログ記録と標準処理を提供。

#### 7. 統合 LLM クライアントおよび推論エンジン (`agent_common.llm`)
- **7.1. [モデルプロファイル管理およびテキスト生成](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/01_model_profiles_and_generation_ja.md)**
- **7.2. [外部チャット API および Fabrix 連携](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/02_external_api_and_fabrix_ja.md)**
- **7.3. [ローカル GGUF 推論およびモデルキャッシュ](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/03_local_gguf_inference_ja.md)**
- **7.4. [実行モードおよび条件付きローカル切り替え](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/04_provider_and_local_fallback_ja.md)**
- **7.5. [推論結果および例外処理](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/05_inference_results_and_errors_ja.md)**
- **7.6. [Groq 監督官 AI および Antigravity Stop フック](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/06_groq_supervisor_and_stop_hook_ja.md)**

#### 8. 言語ローカライザー (`agent_common.localizer`)
- **8.1. [言語コードの正規化と言語別リソースファイル探索 (`Localizer`)](https://github.com/kampores/agent_common/blob/main/manual/ja/localizer/01_language_codes_and_resource_lookup_ja.md)**: ISO 639-1 言語コード (`KO`, `EN`, `ZH`, `JA`) の正規化、明示引数・グローバル設定・環境変数に基づく言語決定、`{接頭辞}_{言語}.yml` 形式の言語別リソースファイル探索。ロギングから分離されており、ラベルや案内文など任意の多言語リソースに再利用可能。

---

### 🛠️ 使用例 (Usage Examples)

#### 1. グローバル `config` ドットアクセスおよび型保証
```python
from agent_common.config_loader import config

# 1) 型サフィックスによる自動キャスト保証
max_workers: int = config.transfer.max_workers_int       # int 型保証
host: str = config.database.host_str                     # str 型および .strip() 保証
is_active: bool = config.transfer.is_active_bool         # bool 型保証

# 2) 階層的プロパティアクセス
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. ToolParser による動的ルール評価
```python
from agent_common.tool_parser import ToolParser

tool_parser = ToolParser()

context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. ProgressTracker リアルタイム進捗追跡
```python
from agent_common import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="ファイル")

for file_info in file_list:
    try:
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

tracker.log_summary()
```

#### 4. LlmClient による統合テキスト/SQL生成
```python
from agent_common.llm import LlmClient

llm_client = LlmClient(purpose_str="sql_generator")
prompt_str = "ユーザー要求: 2026年8月の日次新規加入者統計クエリを作成してください。"
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="あなたは BigQuery SQL 専門の生成 AI です。"
)
print(f"生成結果 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. ストレージおよび BigQuery クライアント使用例
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS スマート転送 (同一ファイルスキップ)
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery インライン MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "山田太郎", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

#### 6. GcpCredentialResolver で他の GCP サービスを認証する
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

# 環境変数 JSON → 環境変数のファイルパス → 指定パス の順に解決し、いずれもなければ None (ADC) を返却
credentials = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
).resolve()

# GCS・BigQuery 以外の GCP クライアントにもそのまま渡せます
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

---

### 📖 詳細機能マニュアル (User Manuals)

| 番号 | モジュール / テーマ | マニュアルリンク | 主な内容要約 |
| :---: | :--- | :---: | :--- |
| **1.1** | **階層型 YAML 解析 & ディープマージ** | [01_hierarchical_yaml_merge_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/01_hierarchical_yaml_merge_ja.md) | 5段階マージ順序、再帰 `_deep_merge` アルゴリズム、ルート自動探索 |
| **1.2** | **不変ドット記法アクセス (`ReadOnlyConfig`)** | [02_readonly_dot_notation_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/02_readonly_dot_notation_ja.md) | ドット記法アクセス、ランタイム改ざん防止 (Read-Only)、不変オブジェクト設計 |
| **1.3** | **型サフィックス自動型変換 & 型保証** | [03_type_coercion_and_guarantee_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/03_type_coercion_and_guarantee_ja.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 自動キャストおよび安全性保証 |
| **1.4** | **Fail-Fast 必須設定検証** | [04_fail_fast_require_setting_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/04_fail_fast_require_setting_ja.md) | 起動時必須設定の欠落検知、診断ログおよびプロセスの安全な早期終了 |
| **1.5** | **ネットワークプロキシ制御** | [05_network_proxy_control_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/05_network_proxy_control_ja.md) | `proxy.no_proxy` 設定の `NO_PROXY` 環境変数自動反映とプロキシバイパス |
| **1.6** | **全定数の設定ファイル外部化とテンプレート補正** | [06_ensure_config_self_healing_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/config_loader/06_ensure_config_self_healing_ja.md) | コード内全定数の外部化、`config.yml` 自動生成および欠落設定の強制補正 |
| **2.1** | **単一行フラット化フォーマッター & 発生源追跡** | [01_single_line_flatten_formatter_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/01_single_line_flatten_formatter_ja.md) | `SingleLineFlattenFormatter`、`[Origin: ...]` 抽出、集中ログ収集最適化 |
| **2.2** | **一括ロギング構成 & ハンドラー制御** | [02_project_logger_configure_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/02_project_logger_configure_ja.md) | `ProjectLogger.configure()`、コンソール/ファイル振り分け、レベル別ディレクトリ分離 |
| **2.3** | **多言語メッセージカタログ & コードベースロギング** | [03_multilingual_message_catalog_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/03_multilingual_message_catalog_ja.md) | `logging_messages_*.yml`、ランタイム言語切り替え、安全な変数置換 |
| **2.4** | **タスク統計 & エラー/除外リアルタイム集計** | [04_execution_result_and_error_tracking_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/04_execution_result_and_error_tracking_ja.md) | 成功/失敗/除外の3段階分類、マルチスレッド環境での指標集計 |
| **2.5** | **タスク結果要約レポート自動生成** | [05_summary_report_generation_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/logger/05_summary_report_generation_ja.md) | `ProjectLogger.log_summary()`、80列整形要約ブロック、スループットとエラー診断 |
| **3.1** | **AWS S3 & Dell ECS ストレージ連携** | [01_s3_ecs_storage_client_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/01_s3_ecs_storage_client_ja.md) | S3/ECS 接続検証、ページネーション一覧取得、GCS ストリーミング転送と重複スキップ |
| **3.2** | **GCS ストリーミングアップロード & 4段階認証** | [02_gcs_cloud_storage_client_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/02_gcs_cloud_storage_client_ja.md) | 4段階認証優先順位、バケット検証、メモリパイプラインによるゼロディスク転送 |
| **3.3** | **BigQuery バッチロード & ストリーミング挿入** | [03_bigquery_batch_and_streaming_load_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/03_bigquery_batch_and_streaming_load_ja.md) | JSON バッチロード vs ストリーミング API、ネストエラー展開、既存キー重複防止 |
| **3.4** | **BigQuery インライン MERGE (Upsert) エンジン** | [04_bigquery_inline_merge_upsert_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/04_bigquery_inline_merge_upsert_ja.md) | 一時テーブル不要のインライン MERGE、UNNEST パラメータバインディング、100件分割 |
| **3.5** | **BigQuery TIMESTAMP・DATETIME 変換** | [05_bigquery_timestamp_and_datetime_conversion_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/05_bigquery_timestamp_and_datetime_conversion_ja.md) | ISO/圧縮日時の正規化、タイムゾーンオフセットの決定優先順位、列の型ごとのメソッド選択基準 |
| **3.6** | **GCP サービスアカウント認証リゾルバー** | [06_gcp_credential_resolver_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/clients/06_gcp_credential_resolver_ja.md) | `GcpCredentialResolver`、4段階の認証優先順位、他の GCP サービスでの単独再利用、コンポジション構造 |
| **4.1** | **二元化 Tool ディレクトリ探索 & 動的ロード** | [01_dual_tool_hierarchy_discovery_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/01_dual_tool_hierarchy_discovery_ja.md) | 組み込み(優先1) vs ローカル(優先2) 探索、3段階関数内省、キャッシュ機構 |
| **4.2** | **宣言的テンプレート置換 & 式評価** | [02_declarative_template_eval_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/02_declarative_template_eval_ja.md) | `ToolParser.eval()`、関数直接呼び出し、名前空間バインド、パイプ (`\|`) フォールバック |
| **4.3** | **安全な名前空間探索 (`_SafeNamespace`)** | [03_safe_namespace_navigation_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/03_safe_namespace_navigation_ja.md) | ドット/インデックス統一、大文字小文字不問、欠落時 `""` 返却、再帰ラッピング |
| **4.4** | **組み込み共通日時ツール (`DateTimeUtils`)** | [04_builtin_datetime_utils_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/tool_parser/04_builtin_datetime_utils_ja.md) | ルール/テンプレート専用日時ツール、`TimeUtils` 連携、ISO タイムスタンプ生成 |
| **5.1** | **ホストタイムゾーン検出 & 世界標準時解決** | [01_time_utils_and_timezone_resolution_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/01_time_utils_and_timezone_resolution_ja.md) | `TimeUtils`、OS/コンテナタイムゾーン検出、30+標準時解析、datetime 正規化 |
| **5.2** | **マルチスレッド進捗追跡 & マイルストーン** | [02_progress_tracker_and_milestones_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/02_progress_tracker_and_milestones_ja.md) | `ProgressTracker`、進捗率 (`%`)、スループット、ETA 計算、`WARNING` 昇格ログ |
| **5.3** | **Unicode 全角幅計算 & テーブル縦線整列** | [03_unicode_table_formatter_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/utils/03_unicode_table_formatter_ja.md) | `TableFormatter`、`east_asian_width` に基づく全角(2幅)・半角(1幅)整列 |
| **7.1** | **モデルプロファイル管理およびテキスト生成** | [01_model_profiles_and_generation_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/01_model_profiles_and_generation_ja.md) | `agent_common.llm` |
| **7.2** | **外部チャット API および Fabrix 連携** | [02_external_api_and_fabrix_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/02_external_api_and_fabrix_ja.md) | `agent_common.llm` |
| **7.3** | **ローカル GGUF 推論およびモデルキャッシュ** | [03_local_gguf_inference_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/03_local_gguf_inference_ja.md) | `agent_common.llm` |
| **7.4** | **実行モードおよび条件付きローカル切り替え** | [04_provider_and_local_fallback_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/04_provider_and_local_fallback_ja.md) | `agent_common.llm` |
| **7.5** | **推論結果および例外処理** | [05_inference_results_and_errors_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/05_inference_results_and_errors_ja.md) | `agent_common.llm` |
| **7.6** | **Groq 監督官 AI および Antigravity Stop フック** | [06_groq_supervisor_and_stop_hook_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/llm/06_groq_supervisor_and_stop_hook_ja.md) | `agent_common.llm` |
| **8.1** | **言語コード正規化 & 言語別リソース探索** | [01_language_codes_and_resource_lookup_ja.md](https://github.com/kampores/agent_common/blob/main/manual/ja/localizer/01_language_codes_and_resource_lookup_ja.md) | `Localizer`、対応言語コードと別名、言語決定の優先順位、言語別ファイル探索とデフォルト言語への代替ルール |

---

### 🚀 インストールおよびビルドガイド (Installation and Build Guide)

#### 📦 Wheel パッケージビルド (.whl)
```bash
# クローズドネットワーク環境
python scripts/build_agent_common_whl.py

# インターネット接続環境
python -m build agent_common --wheel -o whls/
```

#### Wheel パッケージのインストール
```bash
# 開発環境（Editable モード - 軽量コアインストール）
pip install -e agent_common

# 開発環境（クラウドクライアント extras 含む）
pip install -e "agent_common[clients]"

# 本番環境（Wheel パッケージのインストール）
pip install dist/agent_common-0.4.98-py3-none-any.whl
```

#### 🌐 公式 PyPI 配布（管理者専用）
```bash
# 1. ビルドツールの更新
pip install build twine

# 2. パッケージビルド（sdist および wheel 同時作成）
python -m build

# 3. 配布アーカイブの検証
python -m twine check dist/*

# 4. PyPI アップロード
python -m twine upload dist/agent_common-0.4.98*
```

---

### 📋 バージョン変更履歴 (Changelog)

詳細なバージョン変更履歴は [CHANGELOG_JA.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_JA.md) をご参照ください。
