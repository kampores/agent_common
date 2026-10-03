# agent_common (한국어)

**[📦 PyPI 패키지](https://pypi.org/project/agent-common/) · [💻 GitHub 소스 및 매뉴얼](https://github.com/kampores/agent_common)**

> [ 🇰🇷 한국어 (README_KR.md) ](README_KR.md) | [ 🇺🇸 English (README_EN.md) ](README_EN.md) | [ 🇨🇳 中文 (README_ZH.md) ](README_ZH.md) | [ 🇯🇵 日本語 (README_JP.md) ](README_JP.md)

---

## 🇰🇷 agent_common 패키지 개요

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트, 동적 도구(Tool) 파서 및 에러 처리 라이브러리 패키지입니다.

---

### 📌 주요 제공 기능

#### 1. 설정 로더 및 불변 설정 객체 (`agent_common.config_loader`)
- **1.1. [계층적 YAML 설정 해석 및 병합 (Deep Merge)](manual/kr/config_loader/01_hierarchical_yaml_merge_kr.md)**: 패키지 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정(`config/*.yml`) 동적 병합.
- **1.2. [불변 점 표기법 조회 (`ReadOnlyConfig`)](manual/kr/config_loader/02_readonly_dot_notation_kr.md)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 형태로 직관적 속성 접근 및 런타임 변조 방지.
- **1.3. [타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion)](manual/kr/config_loader/03_type_coercion_and_guarantee_kr.md)**:
  - `_int`: `int` 정수형 자동 형 변환 및 보증
  - `_float`: `float` 실수형 자동 형 변환 및 보증
  - `_bool`: `bool` 불리언형 자동 변환 및 타입 보증 (파이썬 `bool` 또는 대소문자 무관 `"true"`, `"false"` 지원, `0`, `1` 등 비지원 값 유입 시 Fail-Fast 차단)
  - `_str`: `str` 문자열 변환 및 `.strip()` 공백 자동 정제
  - `_list` / `_dict`: 리스트 / 불변 딕셔너리(`ReadOnlyConfig`) 래핑 보증
  - 범용 함수 `coerce_type_by_key_suffix` 및 중첩 딕셔너리 일괄 변환 `coerce_dict_by_key_suffix` 제공으로 임의의 외부 설정 파일(`rule.yml`, `mapping.yml` 등) 및 데이터 파이프라인 완벽 지원
  - 타입 불일치 시 침묵하지 않고 상세 안내와 함께 즉시 조기 실패(Fail-Fast, `ValueError`/`TypeError`) 발생 보증
- **1.4. [Fail-Fast 필수 설정 검증 (`require_setting()`)](manual/kr/config_loader/04_fail_fast_require_setting_kr.md)**: 프로그램 시작 시 필수 설정값 누락 시 상세 원인 출력 후 프로세스 즉시 종료.
- **1.5. [네트워크 프록시 제어 (`_apply_no_proxy`)](manual/kr/config_loader/05_network_proxy_control_kr.md)**: `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영.
- **1.6. [모든 상수의 설정 파일화 및 템플릿 보정 (`ensure_config_file()`)](manual/kr/config_loader/06_ensure_config_self_healing_kr.md)**: 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정.

#### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- **2.1. [단일 행 평탄화 포매터 및 예외 원천 추적 (`SingleLineFlattenFormatter`)](manual/kr/logger/01_single_line_flatten_formatter_kr.md)**: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화 및 `[Origin: ...]` 원천 위치 추출, 로거 팩토리 기반 호출자/클래스명(`%(caller)s`, `%(className)s`) 자동 결합 및 프로그램 로거 이름(`%(name)s`) 통일 지원
- **2.2. [로깅 환경 일괄 구성 및 핸들러 제어 (`ProjectLogger.configure`)](manual/kr/logger/02_project_logger_configure_kr.md)**: 콘솔 및 파일 로그 핸들러 동적 생성, 일자별 폴더 분리, 실행 로그 레벨별 디렉터리 자동 분기(`{log_level_str}` 기반 `log_file_str` 단일화)
- **2.3. [다국어 로그 메시지 템플릿 사전 및 코드 기반 로깅 (`logging_messages_*.yml`)](manual/kr/logger/03_multilingual_message_catalog_kr.md)**: `config.yml`의 `logging.language` (`KO` 또는 `EN`) 설정에 따라 한국어/영문 메시지 사전 자동 연동, 런타임 동적 언어 전환 및 안전한 템플릿 치환
- **2.4. [작업 진행 통계 및 예외/제외 사유별 실시간 집계 (`record_result`)](manual/kr/logger/04_execution_result_and_error_tracking_kr.md)**: 성공, 실패, 제외(Skip) 3단계 상태 분류 및 인스턴스/클래스 전역 멀티스레드 에러 집계
- **2.5. [작업 결과 요약 리포트 자동 생성 (`log_summary`)](manual/kr/logger/05_summary_report_generation_kr.md)**: '전체 = 성공 + 실패 + 제외' 정합성 보장, `TableFormatter` 기반 세로줄 자동 맞춤, 소요 시간, 처리 속도, 전송량이 포함된 표준 마크다운 표(Table) 자동 출력

#### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- **3.1. [AWS S3 및 Dell ECS 오브젝트 스토리지 클라이언트 (`S3Client`)](manual/kr/clients/01_s3_ecs_storage_client_kr.md)**: AWS S3 및 Dell ECS(S3 호환) 저장소 접속, 초기화 즉시 `head_bucket` Fail-Fast 검증, 대용량 페이징 제너레이터(`list_objects`), 메타데이터 빠른 조회(`get_object_size`), 메모리 스트리밍 획득(`get_object_stream`), GCS 실시간 파일 전송 및 동일 파일 스마트 스킵(`transfer_to_gcs`)
- **3.2. [Google Cloud Storage 스트리밍 클라이언트 및 멀티 계층 인증 (`GcsClient`)](manual/kr/clients/02_gcs_cloud_storage_client_kr.md)**: 4단계 GCP 인증 우선순위(`GOOGLE_APPLICATION_CREDENTIALS_JSON` 인메모리 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 파일 -> `credentials_path_str` -> Google ADC) 지원, 연결 및 버킷 권한 조기 검증, 블롭 메타데이터 및 크기 조회(`get_blob_size`), 메모리 낭비 없는 청크 단위 스트림 직접 업로드(`upload_stream`)
- **3.3. [BigQuery 배치 및 스트리밍 적재 클라이언트 (`BigQueryClient`)](manual/kr/clients/03_bigquery_batch_and_streaming_load_kr.md)**: 연결 및 테이블 스키마 사전 캐싱(`get_table`), JSON 배치 로드 Job(`load_table_from_json_data`) 및 중첩 에러(`errors`, `location`, `reason`) 상세 분해, 실시간 스트리밍 인서트(`insert_rows_json_data`), 범용 동기 SQL 쿼리(`query`), 중복 전송 방지용 기존 키 집합 추출(`get_existing_keys`)
- **3.4. [BigQuery 고성능 인라인 MERGE (Upsert) 쿼리 엔진 (`merge_table_from_json_data`)](manual/kr/clients/04_bigquery_inline_merge_upsert_kr.md)**: 스테이징 임시 테이블 생성 없이 직접 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 기반 인라인 MERGE INTO 수행, 기본키(PK) 기준 자동 UPDATE/INSERT 분기, 생성일시 등 최초 값 보존(`preserve_columns_list`), 컬럼 데이터 타입 자동 추론 및 명시적 캐스팅(`column_types_dict`), 한글/특수문자/예약어 백틱(`` ` ``) 완벽 보호, HTTP 413 페이로드 초과 방지 기본 100건 청크 자동 분할
- **3.5. [BigQuery 타임존 오프셋 변환 및 테이블 타임존 모드 검증·동기화 (`convert_to_bigquery_timestamp`)](manual/kr/clients/05_bigquery_timestamp_and_tz_sync_kr.md)**: ISO 8601, 공백 구분, 14자리/8자리 숫자 등 다양한 원천 날짜 문자열의 BigQuery 표준 타임스탬프 정규화, 타임존 오프셋 우선순위(`timezone_offset_str`), 한국 시각 숫자 보존 모드(`kst_as_utc_timestamp_bool`), 테이블 메타데이터 자동 동기화 및 기존 데이터 존재 시 불일치 차단(Fail-Fast)

#### 4. 동적 도구 로더 및 템플릿 평가기 (`agent_common.tool_parser`) & 내장 도구 (`agent_common.tool`)
- **4.1. [이원화된 Tool 디렉터리 계층 탐색 및 동적 로딩 (`ToolParser.load_tool_function`)](manual/kr/tool_parser/01_dual_tool_hierarchy_discovery_kr.md)**:
  - **1순위 (내장 도구)**: `agent_common/tool/` 하위 모듈 (전사 표준 내장 도구)
  - **2순위 (프로젝트 도구)**: `config.yml`의 `transfer.tool_dir_str`에 지정된 로컬 경로 (예: `medallion/tool/`)
- **4.2. [선언적 템플릿 치환 및 표현식 평가 (`ToolParser.eval`)](manual/kr/tool_parser/02_declarative_template_eval_kr.md)**:
  - 변수 네임스페이스 바인딩: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - 동적 도구 함수 호출: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - 파이프(`|`) 우선순위 폴백 및 기본값: `"{meta.title|json.title|'기본제목'}"`
- **4.3. [안전한 네임스페이스 탐색 (`_SafeNamespace`)](manual/kr/tool_parser/03_safe_namespace_navigation_kr.md)**:
  - 점(`.`) 및 인덱스 통합 접근, 대소문자 무관 탐색, 누락 필드 `""` 반환, 중첩 딕셔너리/리스트 안전 재귀 래핑
- **4.4. [내장 공통 일시 도구 (`DateTimeUtils`)](manual/kr/tool_parser/04_builtin_datetime_utils_kr.md)**:
  - 테이블 규칙 및 템플릿 평가 전용 날짜/시간 도구, 코어 타임존 해석은 `TimeUtils`에 위임하여 역할 분담

#### 5. 진행률 트래커, 테이블 포매터 및 시간 유틸리티 (`agent_common.utils`)
- **5.1. [호스트 시스템 타임존 감지, 전 세계 표준시 해석 및 일시 정규화 (`TimeUtils`)](manual/kr/utils/01_time_utils_and_timezone_resolution_kr.md)**: 호스트 시스템 타임존 동적 자동 감지, 전 세계 30여 개 주요 표준 타임존 해석, ISO 8601 오프셋 계산, 일시 객체/문자열을 timezone-aware datetime으로 정규화하는 `parse_datetime`
- **5.2. [멀티스레드 실시간 진행률 추적 및 마일스톤 경고 (`ProgressTracker`)](manual/kr/utils/02_progress_tracker_and_milestones_kr.md)**: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간(ETA) 예측, 일반 진행 `INFO` vs 10% 단위 마일스톤 `WARNING` 승격 로깅
- **5.3. [유니코드 전각 문자 폭 계산 및 마크다운/콘솔 테이블 칼맞춤 포매터 (`TableFormatter`)](manual/kr/utils/03_unicode_table_formatter_kr.md)**: 유니코드 동아시아 문자 폭(`unicodedata.east_asian_width`) 정밀 계산 기반 한글/한자(2칸) vs 영문(1칸) 모노스페이스 콘솔 및 마크다운 테이블 세로줄 자동 맞춤 포매터

#### 6. 공용 에러 및 예외 핸들러 (`agent_common.error_handler`)
- 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

#### 7. 통합 LLM 클라이언트 및 추론 엔진 (`agent_common.llm`)
- **7.1. [모델 프로필 관리 및 텍스트 생성](manual/kr/llm/01_model_profiles_and_generation_kr.md)**
- **7.2. [외부 채팅 API 및 Fabrix 연동](manual/kr/llm/02_external_api_and_fabrix_kr.md)**
- **7.3. [로컬 GGUF 추론 및 모델 캐싱](manual/kr/llm/03_local_gguf_inference_kr.md)**
- **7.4. [실행 모드 및 조건부 로컬 전환](manual/kr/llm/04_provider_and_local_fallback_kr.md)**
- **7.5. [추론 결과 및 예외 처리](manual/kr/llm/05_inference_results_and_errors_kr.md)**
- **7.6. [Groq 감독관 AI 및 Antigravity Stop 훅](manual/kr/llm/06_groq_supervisor_and_stop_hook_kr.md)**

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
from agent_common.utils import ProgressTracker
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

---

### 📖 상세 기능 매뉴얼 (User Manuals)

| 번호 | 모듈 / 주제 | 상세 매뉴얼 링크 | 주요 내용 요약 |
| :---: | :--- | :---: | :--- |
| **1.1** | **계층적 YAML 해석 & 딥 머지** | [01_hierarchical_yaml_merge_kr.md](manual/kr/config_loader/01_hierarchical_yaml_merge_kr.md) | 5단계 계층 병합 순서, `_deep_merge` 재귀 알고리즘, 루트 디렉터리 자동 탐색 |
| **1.2** | **불변 점 표기법 조회 (`ReadOnlyConfig`)** | [02_readonly_dot_notation_kr.md](manual/kr/config_loader/02_readonly_dot_notation_kr.md) | 점 표기법 속성 접근, 런타임 변조 원천 차단(Read-Only), 불변 객체 설계 |
| **1.3** | **타입 접미사 자동 형 변환 & 타입 보증** | [03_type_coercion_and_guarantee_kr.md](manual/kr/config_loader/03_type_coercion_and_guarantee_kr.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 런타임 자동 캐스팅 및 타입 안전성 보증 |
| **1.4** | **Fail-Fast 필수 설정 검증** | [04_fail_fast_require_setting_kr.md](manual/kr/config_loader/04_fail_fast_require_setting_kr.md) | 기동 초기 필수 설정 누락 감지, 상세 진단 로그 및 프로세스 안전 조기 종료 |
| **1.5** | **네트워크 프록시 제어** | [05_network_proxy_control_kr.md](manual/kr/config_loader/05_network_proxy_control_kr.md) | `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영 및 내부 통신 프록시 우회 |
| **1.6** | **모든 상수의 설정 파일화 및 템플릿 보정** | [06_ensure_config_self_healing_kr.md](manual/kr/config_loader/06_ensure_config_self_healing_kr.md) | 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정 |
| **2.1** | **단일 행 평탄화 포매터 & 원천 추적** | [01_single_line_flatten_formatter_kr.md](manual/kr/logger/01_single_line_flatten_formatter_kr.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` 프레임 추출, 중앙 로그 수집기 연동 최적화 |
| **2.2** | **로깅 환경 일괄 구성 & 핸들러 제어** | [02_project_logger_configure_kr.md](manual/kr/logger/02_project_logger_configure_kr.md) | `ProjectLogger.configure()`, 콘솔/파일 핸들러 분기, 레벨별 파일 분리, 단일 표준 경로 템플릿 |
| **2.3** | **다국어 메시지 사전 & 코드 기반 로깅** | [03_multilingual_message_catalog_kr.md](manual/kr/logger/03_multilingual_message_catalog_kr.md) | `logging_messages_ko.yml`/`en.yml`, 런타임 언어 전환, `safe_kwargs` 템플릿 치환 |
| **2.4** | **작업 통계 & 에러/제외 실시간 집계** | [04_execution_result_and_error_tracking_kr.md](manual/kr/logger/04_execution_result_and_error_tracking_kr.md) | 성공/실패/제외(Skip) 3단계 상태 분류, 인스턴스 및 클래스 전역 멀티스레드 집계 |
| **2.5** | **작업 결과 요약 리포트 자동 생성** | [05_summary_report_generation_kr.md](manual/kr/logger/05_summary_report_generation_kr.md) | `ProjectLogger.log_summary()`, 80열 표준 요약 블록, 처리 속도/전송률, 에러 상세 해석 |
| **3.1** | **AWS S3 & Dell ECS 스토리지 연동** | [01_s3_ecs_storage_client_kr.md](manual/kr/clients/01_s3_ecs_storage_client_kr.md) | S3/ECS 연결, Fail-Fast 검증, 페이징 목록 조회, GCS 스트리밍 전송 및 동일 파일 스킵 |
| **3.2** | **GCS 스트리밍 업로드 & 4단계 인증** | [02_gcs_cloud_storage_client_kr.md](manual/kr/clients/02_gcs_cloud_storage_client_kr.md) | 4단계 서비스 계정 인증 우선순위, 연결 검증, 메타데이터 조회, 메모리 파이프라인 업로드 |
| **3.3** | **BigQuery 배치 적재 & 스트리밍 인서트** | [03_bigquery_batch_and_streaming_load_kr.md](manual/kr/clients/03_bigquery_batch_and_streaming_load_kr.md) | JSON 배치 로드 Job vs 스트리밍 API, 중첩 에러 상세 분해, 중복 방지 키 집합 조회 |
| **3.4** | **BigQuery 인라인 MERGE (Upsert) 엔진** | [04_bigquery_inline_merge_upsert_kr.md](manual/kr/clients/04_bigquery_inline_merge_upsert_kr.md) | 임시 테이블 없는 인라인 MERGE, UNNEST 파라미터 바인딩, 동적 타입 캐스팅, 100건 청크 분할 |
| **3.5** | **BigQuery 타임존 변환 & 모드 검증·동기화** | [05_bigquery_timestamp_and_tz_sync_kr.md](manual/kr/clients/05_bigquery_timestamp_and_tz_sync_kr.md) | ISO/압축 일시 정규화, Standard-UTC vs KST-as-UTC 모드, 테이블 메타데이터 동기화 및 Fail-Fast |
| **4.1** | **이원화된 Tool 디렉터리 계층 탐색 & 동적 로딩** | [01_dual_tool_hierarchy_discovery_kr.md](manual/kr/tool_parser/01_dual_tool_hierarchy_discovery_kr.md) | 내장(1순위) vs 로컬(2순위) 탐색 계층, 3단계 함수 탐색, `_tool_cache`, 사전 검증 |
| **4.2** | **선언적 템플릿 치환 & 표현식 평가** | [02_declarative_template_eval_kr.md](manual/kr/tool_parser/02_declarative_template_eval_kr.md) | `ToolParser.eval()`, 도구 함수 직통 호출, 점(.) 네임스페이스 바인딩, 파이프(`\|`) 폴백 |
| **4.3** | **안전한 네임스페이스 탐색 (`_SafeNamespace`)** | [03_safe_namespace_navigation_kr.md](manual/kr/tool_parser/03_safe_namespace_navigation_kr.md) | 점(.)/인덱스 통합 접근, 대소문자 무관 탐색, 누락 필드 `""` 반환, 중첩 래핑 |
| **4.4** | **내장 공통 일시 도구 (`DateTimeUtils`)** | [04_builtin_datetime_utils_kr.md](manual/kr/tool_parser/04_builtin_datetime_utils_kr.md) | 테이블 룰/템플릿 전용 날짜 도구, `YYYYMMDD`, ISO 타임스탬프, 압축 일시 생성 |
| **5.1** | **호스트 타임존 감지 & 세계 표준시 해석** | [01_time_utils_and_timezone_resolution_kr.md](manual/kr/utils/01_time_utils_and_timezone_resolution_kr.md) | `TimeUtils`, OS/컨테이너 타임존 감지, 전 세계 30여 개 표준시 해석, datetime 정규화 |
| **5.2** | **멀티스레드 실시간 진행률 추적 & 마일스톤** | [02_progress_tracker_and_milestones_kr.md](manual/kr/utils/02_progress_tracker_and_milestones_kr.md) | `ProgressTracker`, 실시간 진행률(`%`), 처리 속도, ETA 계산, `WARNING` 승격 로깅 |
| **5.3** | **유니코드 전각 폭 계산 & 마크다운 표 칼맞춤** | [03_unicode_table_formatter_kr.md](manual/kr/utils/03_unicode_table_formatter_kr.md) | `TableFormatter`, 동아시아 문자 폭(`east_asian_width`) 정밀 계산, 마크다운 표 정렬 |
| **7.1** | **모델 프로필 관리 및 텍스트 생성** | [01_model_profiles_and_generation_kr.md](manual/kr/llm/01_model_profiles_and_generation_kr.md) | `agent_common.llm` |
| **7.2** | **외부 채팅 API 및 Fabrix 연동** | [02_external_api_and_fabrix_kr.md](manual/kr/llm/02_external_api_and_fabrix_kr.md) | `agent_common.llm` |
| **7.3** | **로컬 GGUF 추론 및 모델 캐싱** | [03_local_gguf_inference_kr.md](manual/kr/llm/03_local_gguf_inference_kr.md) | `agent_common.llm` |
| **7.4** | **실행 모드 및 조건부 로컬 전환** | [04_provider_and_local_fallback_kr.md](manual/kr/llm/04_provider_and_local_fallback_kr.md) | `agent_common.llm` |
| **7.5** | **추론 결과 및 예외 처리** | [05_inference_results_and_errors_kr.md](manual/kr/llm/05_inference_results_and_errors_kr.md) | `agent_common.llm` |
| **7.6** | **Groq 감독관 AI 및 Antigravity Stop 훅** | [06_groq_supervisor_and_stop_hook_kr.md](manual/kr/llm/06_groq_supervisor_and_stop_hook_kr.md) | `agent_common.llm` |

---

### 🚀 설치 및 빌드 가이드 (Installation and Build Guide)

#### 📦 Wheel 패키지 빌드 (.whl)
새로운 버전으로 패키징하여 `.whl` 파일을 빌드할 경우 `scripts/build_agent_common_whl.py` 또는 `agent_common` 디렉터리 내에서 아래 명령을 실행합니다.

##### 1. 사내 폐쇄망 환경 (인터넷 차단, 완전히 오프라인 빌드)
외부 PyPI 접속을 완전히 차단하기 위해 `--no-index`, `--no-build-isolation`, `--no-deps` 옵션을 지정합니다.

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
pip install dist/agent_common-0.4.78-py3-none-any.whl
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
python -m twine upload dist/agent_common-0.4.92*
```

---

### 📋 버전 변경 이력 (Changelog)

전체 상세 버전 변경 이력은 [CHANGELOG_KR.md](CHANGELOG_KR.md) 파일을 참고하세요.


