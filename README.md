# agent_common

> [ 🇰🇷 한국어 설명 ](#-agent_common-패키지-한국어) | [ 🇺🇸 English Description ](#-agent_common-package-english) | [ 📖 매뉴얼 (Manuals) ](#-상세-기능-매뉴얼-user-manuals)

---

## 🇰🇷 agent_common 패키지 (한국어)

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트, 동적 도구(Tool) 파서 및 에러 처리 라이브러리 패키지입니다.

---

### 📌 주요 제공 기능

#### 1. 설정 로더 및 불변 설정 객체 (`agent_common.config_loader`)
- **1.1. [계층적 YAML 설정 해석 및 병합 (Deep Merge)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/01_hierarchical_yaml_merge.md)**: 패키지 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정(`config/*.yml`) 동적 병합.
- **1.2. [불변 점 표기법 조회 (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/02_readonly_dot_notation.md)**: `config.ecs.endpoint_url`, `config.transfer.max_workers_int` 형태로 직관적 속성 접근 및 런타임 변조 방지.
- **1.3. [타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion - v0.4.14 / 범용화 v0.4.32)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/03_type_coercion_and_guarantee.md)**:
  - `_int`: `int` 정수형 자동 형 변환 및 보증
  - `_float`: `float` 실수형 자동 형 변환 및 보증
  - `_bool`: `bool` 불리언형 자동 변환 (`"true"`, `"false"`, `1`, `0` 등 완벽 대응)
  - `_str`: `str` 문자열 변환 및 `.strip()` 공백 자동 정제
  - `_list` / `_dict`: 리스트 / 불변 딕셔너리(`ReadOnlyConfig`) 래핑 보증
  - 범용 함수 `coerce_type_by_key_suffix` 및 중첩 딕셔너리 일괄 변환 `coerce_dict_by_key_suffix` 제공으로 임의의 외부 설정 파일(`rule.yml`, `mapping.yml` 등) 및 데이터 파이프라인 완벽 지원
  - 타입 불일치 시 침묵하지 않고 상세 안내와 함께 즉시 조기 실패(Fail-Fast, `ValueError`/`TypeError`) 발생 보증
- **1.4. [Fail-Fast 필수 설정 검증 (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/04_fail_fast_require_setting.md)**: 프로그램 시작 시 필수 설정값 누락 시 상세 원인 출력 후 프로세스 즉시 종료.
- **1.5. [네트워크 프록시 제어 (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/05_network_proxy_control.md)**: `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영.
- **1.6. [모든 상수의 설정 파일화 및 템플릿 보정 (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/06_ensure_config_self_healing.md)**: 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정.
- **1.7. [환경변수 템플릿 치환 (`_interpolate_env_vars`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/01_hierarchical_yaml_merge.md)**: YAML 파일 및 설정 딕셔너리 내 `${VAR_NAME:-default}` 구문 자동 치환을 통한 선언적 환경변수 바인딩 지원 (v0.4.55).

#### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- **2.1. [단일 행 평탄화 포매터 및 예외 원천 추적 (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/01_single_line_flatten_formatter.md)**: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화 및 `[Origin: ...]` 원천 위치 추출, 호출 스택 기반 호출자/클래스명(`%(caller)s`, `%(className)s`) 자동 분리 추출 및 프로그램 로거 이름(`%(name)s`) 통일 지원 (v0.4.36)
- **2.2. [로깅 환경 일괄 구성 및 핸들러 제어 (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/02_project_logger_configure.md)**: 콘솔 및 파일 로그 핸들러 동적 생성, 일자별 폴더 분리, 실행 로그 레벨별 디렉터리 자동 분기(`{log_level}` 기반 `log_file` 단일화) 및 서드파티 노이즈 억제
- **2.3. [다국어 로그 메시지 템플릿 사전 및 코드 기반 로깅 (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/03_multilingual_message_catalog.md)**: `config.yml`의 `logging.language` (`KO` 또는 `EN`) 설정에 따라 한국어/영문 메시지 사전 자동 연동, 런타임 동적 언어 전환 및 안전한 템플릿 치환, `default_str` 표준 매개변수 기반 기본 템플릿 치환 보증 (v0.4.73)
- **2.4. [작업 진행 통계 및 예외/제외 사유별 실시간 집계 (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/04_execution_result_and_error_tracking.md)**: 성공, 실패, 제외(Skip) 3단계 상태 분류 및 인스턴스/클래스 전역 멀티스레드 에러 집계
- **2.5. [작업 결과 요약 리포트 자동 생성 (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/05_summary_report_generation.md)**: '전체 = 성공 + 실패 + 제외' 정합성 보장, `TableFormatter` 기반 세로줄 자동 맞춤, 소요 시간, 처리 속도, 전송량이 포함된 표준 마크다운 표(Table) 자동 출력 (v0.4.63)

#### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- **3.1. [AWS S3 및 Dell ECS 오브젝트 스토리지 클라이언트 (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/01_s3_ecs_storage_client.md)**: AWS S3 및 Dell ECS(S3 호환) 저장소 접속, 초기화 즉시 `head_bucket` Fail-Fast 검증, 대용량 페이징 제너레이터(`list_objects`), 메타데이터 빠른 조회(`get_object_size`), 메모리 스트리밍 획득(`get_object_stream`), GCS 실시간 파일 전송 및 동일 파일 스마트 스킵(`transfer_to_gcs` - `"UPLOADED"`, `"SKIPPED"`, `"FAILED"` 반환 및 구간별 정밀 레이턴시 로깅 지원 - v0.4.72)
- **3.2. [Google Cloud Storage 스트리밍 클라이언트 및 멀티 계층 인증 (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/02_gcs_cloud_storage_client.md)**: 4단계 GCP 인증 우선순위(`GOOGLE_APPLICATION_CREDENTIALS_JSON` 인메모리 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 파일 -> `credentials_path_str` -> Google ADC) 지원, 연결 및 버킷 권한 조기 검증, 블롭 메타데이터 및 크기 조회(`get_blob_size`), 메모리 낭비 없는 청크 단위 스트림 직접 업로드(`upload_stream` - v0.4.56)
- **3.3. [BigQuery 배치 및 스트리밍 적재 클라이언트 (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/03_bigquery_batch_and_streaming_load.md)**: 연결 및 테이블 스키마 사전 캐싱(`get_table`), JSON 배치 로드 Job(`load_table_from_json_data`) 및 중첩 에러(`errors`, `location`, `reason`) 상세 분해, 실시간 스트리밍 인서트(`insert_rows_json_data`), 범용 동기 SQL 쿼리(`query`), 중복 전송 방지용 기존 키 집합 추출(`get_existing_keys`)
- **3.4. [BigQuery 고성능 인라인 MERGE (Upsert) 쿼리 엔진 (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/04_bigquery_inline_merge_upsert.md)**: 스테이징 임시 테이블 생성 없이 직접 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 기반 인라인 MERGE INTO 수행, 기본키(PK) 기준 자동 UPDATE/INSERT 분기, 생성일시 등 최초 값 보존(`preserve_columns_list`), 컬럼 데이터 타입 자동 추론 및 명시적 캐스팅(`column_types_dict`), 한글/특수문자/예약어 백틱(`` ` ``) 완벽 보호, HTTP 413 페이로드 초과 방지 기본 100건 청크 자동 분할, 후속 연쇄 쿼리(`post_queries_list`) 지원
- **3.5. [BigQuery 타임존 오프셋 변환 및 테이블 타임존 모드 검증·동기화 (`convert_to_bigquery_timestamp`)](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/05_bigquery_timestamp_and_tz_sync.md)**: ISO 8601, 공백 구분, 14자리/8자리 숫자 등 다양한 원천 날짜 문자열의 BigQuery 표준 타임스탬프 정규화, 타임존 오프셋 우선순위(`timezone_offset_str` - v0.4.71), 한국 시각 숫자 보존 모드(`kst_as_utc_timestamp_bool`), 테이블 메타데이터(라벨 `timestamp_mode`, 테이블 및 컬럼 Description) 자동 동기화 및 기존 데이터 존재 시 불일치 차단(Fail-Fast)

#### 4. 동적 도구 로더 및 템플릿 평가기 (`agent_common.tool_parser`) & 내장 도구 (`agent_common.tool`)
- **이원화된 Tool 디렉터리 계층 탐색**:
  - **1순위 (내장 도구)**: `agent_common/tool/` 하위 모듈 (전사 표준 내장 도구)
  - **2순위 (프로젝트 도구)**: `config.yml`의 `transfer.tool_dir_str`에 지정된 로컬 경로 (예: `medallion/tool/`)
- **선언적 템플릿 치환 및 표현식 평가 (`ToolParser.eval`)**:
  - 변수 네임스페이스 바인딩: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - 동적 도구 함수 호출: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - 문자열 슬라이싱/메서드: `"{raw_key.lstrip('/')}"`, `"{raw_size|0}"`
- **안전한 네임스페이스 탐색 (`_SafeNamespace`)**:
  - 대소문자 무관 탐색 및 누락된 필드에 대해 KeyError 없이 안전하게 빈 문자열(`""`) 반환
- **내장 공통 도구 (`agent_common.tool.date.DateTimeUtils`)**:
  - 테이블 규칙 및 템플릿 평가 전용 날짜/시간 도구 (v0.4.69 / v0.4.74)
  - `parse_datetime(dt_input_any, default_tz_obj)`: 다양한 형식(datetime, ISO 문자열)의 일시를 timezone-aware datetime으로 정규화 변환 (v0.4.74)
  - `get_now_timestamp(tz_obj)`: ISO 8601 표준 타임스탬프(`YYYY-MM-DD HH:MM:SS+09:00` 또는 `+00:00`) 반환 (BigQuery 적재 및 규칙 파일 표준)
  - `get_now_no_tz(tz_obj)`: 타임존 없는 일시 문자열(`YYYY-MM-DD HH:MM:SS`) 반환 (로그 및 요약표 전용)
  - `get_now_compact(tz_obj)`: `YYYYMMDDHHMMSS` 형식 14자리 압축 일시 반환 (예: `20260824110500`)
  - `get_today_yyyymmdd(tz_obj)`: `YYYYMMDD` 형식 8자리 일자 반환 (새벽 배치 날짜 역전 방지, 예: `20260824`)

#### 5. 진행률 트래커 및 공용 유틸리티 (`agent_common.utils`)
- `TimeUtils`: 호스트 시스템(배치 KST vs 파드 UTC) 타임존 동적 자동 감지, 전 세계 주요 표준 타임존(UTC, KST, JST, EST, CET 등) 해석, ISO 8601 오프셋 계산, 일시 객체/문자열을 timezone-aware datetime으로 정규화하는 `parse_datetime` 지원 코어 시간 인프라 유틸리티 (v0.4.69 / v0.4.74)
- `ProgressTracker`: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간 예측, 마일스톤 경고 승격 로깅
- `TableFormatter`: 유니코드 동아시아 문자 폭(Display Width) 정밀 계산 기반 모노스페이스 콘솔 및 마크다운 테이블 세로줄 자동 맞춤 포매터 (v0.4.63)

#### 6. 공용 에러 및 예외 핸들러 (`agent_common.error_handler`)
- 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

#### 7. 통합 LLM 클라이언트 및 추론 엔진 (`agent_common.llm`)
- **다중 프로바이더 통합 지원 (`LlmClient`)**:
  - **외부 LLM API**: OpenAI 호환 표준 API (`/chat/completions`) 및 Fabrix 전용 API 형식 지원
  - **로컬 GGUF 모델**: `llama-cpp-python` 기반 로컬 CPU/GPU 가속 추론 및 인메모리 모델 캐싱(`_LOCAL_LLMS`)
- **설정 풀(Pool) 기반 모델 프로필 관리**:
  - `llmpool.yml` 및 `config.yml`을 통해 모델명, 토큰 수(`max_tokens`), 온도(`temperature`), 타임아웃, 컨텍스트 크기(`n_ctx`), 스레드 수(`n_threads`), GPU 레이어(`n_gpu_layers`) 등 동적 구성
- **자동 장애 복구 (Auto Failover)**:
  - `provider: auto` 설정 시 외부 LLM API 호출 실패 시 로컬 GGUF 모델로 무중단 자동 전환
- **추론 예외 통일 관리 (`LlmInferenceError`)**:
  - API 키 누락, 타임아웃, 모델 로드 실패 등에 대한 통합 예외 처리

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

# ToolParser 인스턴스 생성 (설정 파일 기반으로 내장/로컬 Tool 자동 탐색)
tool_parser = ToolParser()

# 컨텍스트 데이터 준비
context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) 도구 함수 호출 템플릿 평가
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
# -> "20260824"

# 2) 네임스페이스 및 내장 일시 템플릿 평가
today_val = tool_parser.eval("{sys.today}", context_dict)
# -> "20260824"
```

#### 3. ProgressTracker 실시간 진행률 추적
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="파일")

for file_info in file_list:
    try:
        # 처리 로직 수행
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# 최종 결과 요약 리포트 출력
tracker.log_summary()
```

#### 4. LlmClient를 통한 통합 텍스트/SQL 생성
```python
from agent_common.llm import LlmClient

# 1) 설정 풀에 정의된 모델명 또는 용도로 클라이언트 초기화
llm_client = LlmClient(purpose_str="sql_generator")

# 2) 프롬프트 기반 텍스트 생성 (외부 API -> 로컬 GGUF 자동 폴백)
prompt_str = "사용자 요청: 2026년 8월 일일 가입자 수 통계 쿼리를 작성해줘."
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="당신은 BigQuery 전문 SQL 생성 AI입니다."
)

print(f"생성된 결과 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. 스토리지 및 BigQuery 클라이언트 활용

##### S3/ECS 파일 순회 및 GCS 실시간 파이프라인 전송 (동일 파일 스마트 스킵)
```python
from agent_common.clients import S3Client, GcsClient

# S3/ECS 및 GCS 클라이언트 초기화 (버킷 접근 권한 Fail-Fast 자동 검증)
s3_client = S3Client(
    endpoint_url_str="https://ecs.mycorp.internal:9021",
    access_key_str="MY_ACCESS_KEY",
    secret_key_str="MY_SECRET_KEY",
    bucket_name_str="source-lake",
)
gcs_client = GcsClient(bucket_name_str="target-lake")

# 대용량 객체 제너레이터 순회 및 실시간 스트리밍 전송
for obj_dict in s3_client.list_objects(prefix_str="raw/events/20260824/"):
    s3_key_str: str = obj_dict["Key"]
    size_int: int = obj_dict["Size"]
    gcs_blob_str: str = f"lake/{s3_key_str.lstrip('/')}"
    
    # 동일 파일 존재 시 스킵("SKIPPED"), 신규 전송 시 "UPLOADED"
    status_str = s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=s3_key_str,
        gcs_blob_name_str=gcs_blob_str,
        size_int=size_int,
    )
    print(f"[{status_str}] {s3_key_str} -> {gcs_blob_str} ({size_int:,} bytes)")
```

##### BigQuery 고성능 인라인 MERGE (Upsert) 실행
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-gcp-project",
    dataset_id_str="analytics_dw",
    table_id_str="tb_member_profile",
)

members_list = [
    {
        "member_id": "M001",
        "name": "홍길동",
        "login_count": 42,
        "is_vip": True,
        "created_at": "2026-01-01 00:00:00+09:00",
        "last_login_at": "2026-08-24 15:30:00+09:00",
    }
]

# 임시 테이블 없이 단일 SQL 쿼리로 직접 MERGE 수행 (created_at 최초값 보존)
bq_client.merge_table_from_json_data(
    json_data_any=members_list,
    pk_key_str="member_id",
    preserve_columns_list=["created_at"],
    chunk_size_int=100,
)
```

---

### 🚀 설치 및 빌드 방법

#### 📦 Wheel 패키지 빌드 (.whl 생성)

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
pip install dist/agent_common-0.4.76-py3-none-any.whl
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
python -m twine upload dist/agent_common-0.4.76*
```

---

### 📖 상세 기능 매뉴얼 (User Manuals)

모듈별 상세 아키텍처 및 실전 코드 예시는 아래 상세 매뉴얼 문서를 참고하세요:

| 번호 | 모듈 / 주제 | 상세 매뉴얼 링크 | 주요 내용 요약 |
| :---: | :--- | :---: | :--- |
| **1.1** | **계층적 YAML 해석 & 딥 머지** | [01_hierarchical_yaml_merge.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/01_hierarchical_yaml_merge.md) | 5단계 계층 병합 순서, `_deep_merge` 재귀 알고리즘, 루트 디렉터리 자동 탐색 |
| **1.2** | **불변 점 표기법 조회 (`ReadOnlyConfig`)** | [02_readonly_dot_notation.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/02_readonly_dot_notation.md) | 점 표기법 속성 접근, 런타임 변조 원천 차단(Read-Only), 불변 객체 설계 |
| **1.3** | **타입 접미사 자동 형 변환 & 타입 보증** | [03_type_coercion_and_guarantee.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/03_type_coercion_and_guarantee.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 런타임 자동 캐스팅 및 타입 안전성 보증 |
| **1.4** | **Fail-Fast 필수 설정 검증** | [04_fail_fast_require_setting.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/04_fail_fast_require_setting.md) | 기동 초기 필수 설정 누락 감지, 상세 진단 로그 및 프로세스 안전 조기 종료 |
| **1.5** | **네트워크 프록시 제어** | [05_network_proxy_control.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/05_network_proxy_control.md) | `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영 및 내부 통신 프록시 우회 |
| **1.6** | **모든 상수의 설정 파일화 및 템플릿 보정** | [06_ensure_config_self_healing.md](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/06_ensure_config_self_healing.md) | 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정 |
| **2.1** | **단일 행 평탄화 포매터 & 원천 추적** | [01_single_line_flatten_formatter.md](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/01_single_line_flatten_formatter.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` 프레임 추출, 중앙 로그 수집기 연동 최적화 |
| **2.2** | **로깅 환경 일괄 구성 & 핸들러 제어** | [02_project_logger_configure.md](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/02_project_logger_configure.md) | `ProjectLogger.configure()`, 콘솔/파일 핸들러 분기, 레벨별 파일 분리, 서드파티 노이즈 억제 |
| **2.3** | **다국어 메시지 사전 & 코드 기반 로깅** | [03_multilingual_message_catalog.md](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/03_multilingual_message_catalog.md) | `logging_messages_ko.yml`/`en.yml`, 런타임 언어 전환, `safe_kwargs` 템플릿 치환 |
| **2.4** | **작업 통계 & 에러/제외 실시간 집계** | [04_execution_result_and_error_tracking.md](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/04_execution_result_and_error_tracking.md) | 성공/실패/제외(Skip) 3단계 상태 분류, 인스턴스 및 클래스 전역 멀티스레드 집계 |
| **2.5** | **작업 결과 요약 리포트 자동 생성** | [05_summary_report_generation.md](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/05_summary_report_generation.md) | `ProjectLogger.log_summary()`, 80열 표준 요약 블록, 처리 속도/전송률, 에러 상세 해석 |
| **3.1** | **AWS S3 & Dell ECS 스토리지 연동** | [01_s3_ecs_storage_client.md](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/01_s3_ecs_storage_client.md) | S3/ECS 연결, Fail-Fast 검증, 페이징 목록 조회, GCS 스트리밍 전송 및 동일 파일 스킵 |
| **3.2** | **GCS 스트리밍 업로드 & 4단계 인증** | [02_gcs_cloud_storage_client.md](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/02_gcs_cloud_storage_client.md) | 4단계 서비스 계정 인증 우선순위, 연결 검증, 메타데이터 조회, 메모리 파이프라인 업로드 |
| **3.3** | **BigQuery 배치 적재 & 스트리밍 인서트** | [03_bigquery_batch_and_streaming_load.md](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/03_bigquery_batch_and_streaming_load.md) | JSON 배치 로드 Job vs 스트리밍 API, 중첩 에러 상세 분해, 중복 방지 키 집합 조회 |
| **3.4** | **BigQuery 인라인 MERGE (Upsert) 엔진** | [04_bigquery_inline_merge_upsert.md](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/04_bigquery_inline_merge_upsert.md) | 임시 테이블 없는 인라인 MERGE, UNNEST 파라미터 바인딩, 동적 타입 캐스팅, 100건 청크 분할 |
| **3.5** | **BigQuery 타임존 변환 & 모드 검증·동기화** | [05_bigquery_timestamp_and_tz_sync.md](https://github.com/kampores/agent_common/blob/main/manual/kr/clients/05_bigquery_timestamp_and_tz_sync.md) | ISO/압축 일시 정규화, Standard-UTC vs KST-as-UTC 모드, 테이블 메타데이터 동기화 및 Fail-Fast |

---

### 📋 버전 변경 이력 (Changelog)

자세한 버전 변경 이력은 [GitHub CHANGELOG.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG.md) 파일을 참고하세요.

---

## 🇺🇸 agent_common Package (English)

A comprehensive Python common library providing unified logging, hierarchical configuration loaders, cloud and database infrastructure clients, dynamic tool parsers, and centralized error handling for enterprise agent services and data migration pipelines.

---

### 📌 Key Features

#### 1. Configuration Loader & Immutable Config Object (`agent_common.config_loader`)
- **1.1. [Hierarchical YAML Parsing & Deep Merge](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/01_hierarchical_yaml_merge.md)**: Dynamically merges base package configurations (`agent_common/config/*.yml`) with project-specific configurations (`config/*.yml`).
- **1.2. [Immutable Dot-Notation Access (`ReadOnlyConfig`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/02_readonly_dot_notation.md)**: Intuitive attribute-based lookup (`config.ecs.endpoint_url`, `config.transfer.max_workers_int`) while preventing unintended runtime mutations.
- **1.3. [Type Guarantee & Automatic Coercion via Type Suffixes (v0.4.14 / Generalized v0.4.32)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/03_type_coercion_and_guarantee.md)**:
  - `_int`: Automatic integer conversion and type guarantee.
  - `_float`: Automatic floating-point conversion and type guarantee.
  - `_bool`: Automatic boolean conversion (`"true"`, `"false"`, `1`, `0`, etc.).
  - `_str`: Automatic string conversion and `.strip()` whitespace trimming.
  - `_list` / `_dict`: Guaranteed list / immutable dictionary (`ReadOnlyConfig`) wrapping.
  - Standalone functions `coerce_type_by_key_suffix` and recursive batch coercion `coerce_dict_by_key_suffix` for arbitrary external configuration files (`rule.yml`, `mapping.yml`) and data mappings.
  - Strict Fail-Fast guarantee: type-suffix mismatches immediately raise diagnostic exceptions (`ValueError`/`TypeError`) instead of silently falling back to raw values.
- **1.4. [Fail-Fast Required Setting Validation (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/04_fail_fast_require_setting.md)**: Immediate process termination with diagnostic output if required settings are missing during startup.
- **1.5. [Network Proxy Control (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/05_network_proxy_control.md)**: Automatic synchronization of `NO_PROXY` environment variable from `proxy.no_proxy` configuration.
- **1.6. [Externalizing All Constants & Self-Healing Templates (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/06_ensure_config_self_healing.md)**: Materializing all in-code constants to configuration files, automatic scaffolding, and in-place missing key injection.

#### 2. Single-Line Log Formatter & Project Logger (`agent_common.logger`)
- **2.1. [Single-Line Flatten Formatter & Origin Tracking (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/01_single_line_flatten_formatter.md)**: Flattens log records, extracts `[Origin: ...]` caller frames, and optimizes for centralized log aggregators (Logstash, Fluentd, CloudWatch).
- **2.2. [Batch Logging Configuration & Handler Control (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/02_project_logger_configure.md)**: Dynamic console/file handler initialization, date-based directories, level-based directory creation (`log_file` with `{log_level}`), and third-party noise suppression.
- **2.3. [Multilingual Message Catalog & Code-Based Logging (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/03_multilingual_message_catalog.md)**: Dynamic bilingual dictionary loading (`KO`/`EN`), runtime language switching, and safe template parameter substitution.
- **2.4. [Real-Time Metric Tracking & Error/Exclusion Classification (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/04_execution_result_and_error_tracking.md)**: Three-tier outcome model (Success, Failure, Excluded/Skip) and dual instance/class-global multithreaded telemetry.
- **2.5. [Automatic Summary Report Generation (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/05_summary_report_generation.md)**: Emits structured 80-column execution summary reports with duration, throughput (items/s), transfer rate (MB/s), and decoded error diagnostics.

#### 3. Storage and Database Infrastructure Clients (`agent_common.clients`)
- **3.1. [AWS S3 & Dell ECS Object Storage Client (`S3Client`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/01_s3_ecs_storage_client.md)**: Connects to AWS S3 and Dell ECS (S3-compatible) storage, early `head_bucket` Fail-Fast verification, high-throughput paginated iterator (`list_objects`), fast header metadata lookup (`get_object_size`), in-memory streaming body extraction (`get_object_stream`), real-time streaming pipeline upload to GCS with smart duplicate skipping (`transfer_to_gcs` - returning `"UPLOADED"`, `"SKIPPED"`, or `"FAILED"` with sub-stage latency telemetry - v0.4.72).
- **3.2. [Google Cloud Storage Streaming Client & Multi-Tier Auth (`GcsClient`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/02_gcs_cloud_storage_client.md)**: Four-tier GCP credential resolution hierarchy (`GOOGLE_APPLICATION_CREDENTIALS_JSON` in-memory JSON -> `GOOGLE_APPLICATION_CREDENTIALS` file -> `credentials_path_str` -> Google ADC), instant bucket reachability validation, blob metadata lookup (`get_blob_size`), zero-disk chunked streaming uploads (`upload_stream` - v0.4.56).
- **3.3. [BigQuery Batch Loading & Streaming Ingestion (`BigQueryClient`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/03_bigquery_batch_and_streaming_load.md)**: Fail-fast schema caching (`get_table`), JSON batch load jobs (`load_table_from_json_data`) with unpacked nested error diagnostics (`errors`, `location`, `reason`), real-time streaming ingestion (`insert_rows_json_data`), general SQL query execution (`query`), unique key deduplication set lookup (`get_existing_keys`).
- **3.4. [BigQuery High-Performance Inline MERGE (Upsert) Engine (`merge_table_from_json_data`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/04_bigquery_inline_merge_upsert.md)**: Executes direct inline MERGE INTO via `UNNEST(JSON_QUERY_ARRAY(@json_payload))` without temporary staging tables, automatic primary key routing, original column preservation (`preserve_columns_list`), schema type inference and casting (`column_types_dict`), reserved keyword and Unicode column backtick escaping, HTTP 413 payload limit protection via default 100-row chunking, post-processing query execution (`post_queries_list`).
- **3.5. [BigQuery Timestamp Conversion & Timezone Mode Synchronization (`convert_to_bigquery_timestamp`)](https://github.com/kampores/agent_common/blob/main/manual/en/clients/05_bigquery_timestamp_and_tz_sync.md)**: Normalizes ISO 8601, whitespace, and 14-digit/8-digit timestamps to standard BigQuery formats, timezone offset precedence (`timezone_offset_str` - v0.4.71), display convenience mode (`kst_as_utc_timestamp_bool`), automated table metadata synchronization (labels, table/column descriptions) with fail-fast mismatch blocking.

#### 4. Dynamic Tool Loader & Template Evaluator (`agent_common.tool_parser`) & Built-in Tools (`agent_common.tool`)
- **Dual Tool Hierarchy Discovery**:
  - **Priority 1 (Built-in Tools)**: Modules under `agent_common/tool/` (standard enterprise tools).
  - **Priority 2 (Project Tools)**: Local path configured in `config.yml` under `transfer.tool_dir_str` (e.g., `medallion/tool/`).
- **Declarative Template Replacement & Expression Evaluation (`ToolParser.eval`)**:
  - Variable namespace binding: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - Dynamic tool function invocation: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - String slicing & fallback methods: `"{raw_key.lstrip('/')}"`, `"{raw_size|0}"`
- **Safe Namespace Lookup (`_SafeNamespace`)**:
  - Case-insensitive lookups returning empty strings (`""`) without raising `KeyError` on missing keys.
- **Built-in Common Utilities (`agent_common.tool.date.DateTimeUtils`)**:
  - `get_now_timestamp(tz_obj)`: Returns standard ISO 8601 timestamp string (`YYYY-MM-DD HH:MM:SS+09:00` or `+00:00`).
  - `get_now_no_tz(tz_obj)`: Returns datetime string without timezone (`YYYY-MM-DD HH:MM:SS`).
  - `get_now_compact(tz_obj)`: Returns 14-digit timestamp string (e.g., `20260824110500`).
  - `get_today_yyyymmdd(tz_obj)`: Returns 8-digit date string (e.g., `20260824`).

#### 5. Progress Tracker & Common Utilities (`agent_common.utils`)
- `TimeUtils`: Dynamic host OS system timezone detection, world timezone parsing, and ISO 8601 offset calculation core utility (v0.4.69).
- `ProgressTracker`: Real-time multithreaded progress tracking (`[N/Total] (P%)`), throughput/ETA calculation, and milestone log level elevation.
- `TableFormatter`: Precision terminal and markdown table column width alignment utility (v0.4.63).

#### 6. Common Error & Exception Handler (`agent_common.error_handler`)
- Consistent exception logging and handling for network failures, configuration errors, and runtime exceptions.

#### 7. Unified LLM Client & Inference Engine (`agent_common.llm`)
- **Multi-Provider Support (`LlmClient`)**:
  - **External LLM APIs**: Standard OpenAI-compatible API (`/chat/completions`) and Fabrix API format.
  - **Local GGUF Models**: Local CPU/GPU accelerated inference via `llama-cpp-python` with in-memory caching (`_LOCAL_LLMS`).
- **Pool-based Model Profile Management**: Dynamic configuration via `llmpool.yml` and `config.yml`.
- **Auto Failover**: Seamless automatic fallback to local GGUF models if external API calls fail (`provider: auto`).
- **Unified Inference Error Handling (`LlmInferenceError`)**: Centralized exception handling for API key errors, timeouts, and model load failures.

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

# Initialize ToolParser (auto-discovers built-in and project tools)
tool_parser = ToolParser()

# Prepare context dictionary
context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) Evaluate tool function call template
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
# -> "20260824"

# 2) Evaluate system namespace & date templates
today_val = tool_parser.eval("{sys.today}", context_dict)
# -> "20260824"
```

#### 3. Real-time Progress Tracking with ProgressTracker
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="file")

for file_info in file_list:
    try:
        # Processing logic
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# Output final execution summary report
tracker.log_summary()
```

#### 4. Unified Text/SQL Generation with LlmClient
```python
from agent_common.llm import LlmClient

# 1) Initialize client with configured purpose or model name
llm_client = LlmClient(purpose_str="sql_generator")

# 2) Prompt-based generation (External API with auto fallback to local GGUF)
prompt_str = "User request: Generate daily subscriber statistics SQL for August 2026."
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="You are an expert AI for BigQuery SQL generation."
)

print(f"Generated result ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. Storage and BigQuery Client Usage

##### S3/ECS Object Traversal & Direct GCS Streaming (Smart Skipping)
```python
from agent_common.clients import S3Client, GcsClient

# Initialize S3/ECS and GCS clients (fail-fast bucket validation)
s3_client = S3Client(
    endpoint_url_str="https://ecs.mycorp.internal:9021",
    access_key_str="MY_ACCESS_KEY",
    secret_key_str="MY_SECRET_KEY",
    bucket_name_str="source-lake",
)
gcs_client = GcsClient(bucket_name_str="target-lake")

# Iterate over large object prefixes and stream into GCS directly
for obj_dict in s3_client.list_objects(prefix_str="raw/events/20260824/"):
    s3_key_str: str = obj_dict["Key"]
    size_int: int = obj_dict["Size"]
    gcs_blob_str: str = f"lake/{s3_key_str.lstrip('/')}"
    
    # "SKIPPED" if identical file exists, "UPLOADED" on successful stream
    status_str = s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=s3_key_str,
        gcs_blob_name_str=gcs_blob_str,
        size_int=size_int,
    )
    print(f"[{status_str}] {s3_key_str} -> {gcs_blob_str} ({size_int:,} bytes)")
```

##### BigQuery High-Performance Inline MERGE (Upsert)
```python
from agent_common.clients import BigQueryClient

bq_client = BigQueryClient(
    project_id_str="my-gcp-project",
    dataset_id_str="analytics_dw",
    table_id_str="tb_member_profile",
)

members_list = [
    {
        "member_id": "M001",
        "name": "Alex",
        "login_count": 42,
        "is_vip": True,
        "created_at": "2026-01-01 00:00:00+09:00",
        "last_login_at": "2026-08-24 15:30:00+09:00",
    }
]

# Direct parameterized MERGE without staging tables (preserves created_at)
bq_client.merge_table_from_json_data(
    json_data_any=members_list,
    pk_key_str="member_id",
    preserve_columns_list=["created_at"],
    chunk_size_int=100,
)
```

---

### 🚀 Installation and Build Guide

#### 📦 Wheel Package Build (.whl)
Run the following commands within the `agent_common` directory or using `scripts/build_agent_common_whl.py`:

##### 1. Air-gapped / Offline Environment
Use `--no-index`, `--no-build-isolation`, and `--no-deps` to build offline without external PyPI access:
```bash
# Recommended: Run build script from root
python scripts/build_agent_common_whl.py

# Or build wheel directly
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

##### 2. Online Environment
```bash
# Using pip wheel
pip wheel ./agent_common --no-deps -w whls/

# Or using build module
python -m build agent_common --wheel -o whls/
```

#### Installing the Wheel Package
```bash
# Development (Editable mode - lightweight core)
pip install -e agent_common

# Development (With cloud client extras)
pip install -e "agent_common[clients]"

# Production (Wheel package)
pip install dist/agent_common-0.4.76-py3-none-any.whl
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
python -m twine upload dist/agent_common-0.4.76*
```

---

### 📖 Detailed Feature Manuals

For comprehensive architecture details and practical code examples for each module:

| # | Module / Topic | User Manual Link | Key Highlights |
| :---: | :--- | :---: | :--- |
| **1.1** | **Hierarchical YAML Parsing & Deep Merge** | [01_hierarchical_yaml_merge.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/01_hierarchical_yaml_merge.md) | 5-stage merge order, recursive `_deep_merge` algorithm, auto project root discovery |
| **1.2** | **Immutable Dot-Notation Access (`ReadOnlyConfig`)** | [02_readonly_dot_notation.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/02_readonly_dot_notation.md) | Dot-notation attribute lookup, strict runtime mutation prevention (Read-Only) |
| **1.3** | **Type Guarantee & Automatic Coercion** | [03_type_coercion_and_guarantee.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/03_type_coercion_and_guarantee.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` runtime casting and type safety |
| **1.4** | **Fail-Fast Required Setting Validation** | [04_fail_fast_require_setting.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/04_fail_fast_require_setting.md) | Startup phase mandatory validation, diagnostic output, and fail-fast termination |
| **1.5** | **Network Proxy Control** | [05_network_proxy_control.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/05_network_proxy_control.md) | Automatic synchronization of `NO_PROXY` from `proxy.no_proxy` configuration |
| **1.6** | **Constant Externalization & Self-Healing Templates** | [06_ensure_config_self_healing.md](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/06_ensure_config_self_healing.md) | Materializing all in-code constants, automatic scaffolding, and in-place missing key injection |
| **2.1** | **Single-Line Formatter & Origin Tracking** | [01_single_line_flatten_formatter.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/01_single_line_flatten_formatter.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` frame extraction, centralized log collector optimization |
| **2.2** | **Batch Logging Setup & Handler Control** | [02_project_logger_configure.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/02_project_logger_configure.md) | `ProjectLogger.configure()`, console/file handler routing, level-based paths, third-party noise suppression |
| **2.3** | **Multilingual Catalog & Code-Based Logging** | [03_multilingual_message_catalog.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/03_multilingual_message_catalog.md) | `logging_messages_ko.yml`/`en.yml`, runtime language switching, safe template variable formatting |
| **2.4** | **Result Telemetry & Error Classification** | [04_execution_result_and_error_tracking.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/04_execution_result_and_error_tracking.md) | Success/Failure/Exclusion 3-tier classification, instance & class-global multithreaded counters |
| **2.5** | **Automatic Summary Report Generation** | [05_summary_report_generation.md](https://github.com/kampores/agent_common/blob/main/manual/en/logger/05_summary_report_generation.md) | `ProjectLogger.log_summary()`, 80-column summary block, throughput/bandwidth, decoded error explanations |
| **3.1** | **AWS S3 & Dell ECS Storage Integration** | [01_s3_ecs_storage_client.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/01_s3_ecs_storage_client.md) | S3/ECS connection, Fail-Fast verification, paginated listing, direct GCS streaming and duplicate skip |
| **3.2** | **GCS Streaming Upload & 4-Tier Auth** | [02_gcs_cloud_storage_client.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/02_gcs_cloud_storage_client.md) | 4-tier GCP credential precedence, connection validation, metadata retrieval, in-memory stream upload |
| **3.3** | **BigQuery Batch Loading & Streaming Ingestion** | [03_bigquery_batch_and_streaming_load.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/03_bigquery_batch_and_streaming_load.md) | JSON batch load jobs vs streaming API, nested error diagnostics unpacking, deduplication key lookup |
| **3.4** | **BigQuery Inline MERGE (Upsert) Engine** | [04_bigquery_inline_merge_upsert.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/04_bigquery_inline_merge_upsert.md) | Pure inline MERGE without staging tables, UNNEST parameter binding, dynamic type casting, 100-row chunks |
| **3.5** | **BigQuery Timestamp Conversion & TZ Sync** | [05_bigquery_timestamp_and_tz_sync.md](https://github.com/kampores/agent_common/blob/main/manual/en/clients/05_bigquery_timestamp_and_tz_sync.md) | ISO/compact timestamp normalization, Standard-UTC vs KST-as-UTC modes, table metadata auto-sync & Fail-Fast |

---

### 📋 Version History (Changelog)

For detailed version history, please refer to [GitHub CHANGELOG_EN.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_EN.md).
