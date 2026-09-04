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
- **1.3. [타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion - v0.4.14)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/03_type_coercion_and_guarantee.md)**:
  - `_int`: `int` 정수형 자동 형 변환 및 보증
  - `_float`: `float` 실수형 자동 형 변환 및 보증
  - `_bool`: `bool` 불리언형 자동 변환 (`"true"`, `"false"`, `1`, `0` 등 완벽 대응)
  - `_str`: `str` 문자열 변환 및 `.strip()` 공백 자동 정제
  - `_list` / `_dict`: 리스트 / 불변 딕셔너리(`ReadOnlyConfig`) 래핑 보증
- **1.4. [Fail-Fast 필수 설정 검증 (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/04_fail_fast_require_setting.md)**: 프로그램 시작 시 필수 설정값 누락 시 상세 원인 출력 후 프로세스 즉시 종료.
- **1.5. [네트워크 프록시 제어 (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/05_network_proxy_control.md)**: `proxy.no_proxy` 설정의 `NO_PROXY` 환경변수 자동 반영.
- **1.6. [모든 상수의 설정 파일화 및 템플릿 보정 (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/kr/config_loader/06_ensure_config_self_healing.md)**: 코드 내 모든 상수의 설정 파일화(외부화), `config.yml` 자동 생성 및 누락 상수 강제 주입·보정.

#### 2. 단일 행 로깅 포매터 및 로거 (`agent_common.logger`)
- **2.1. [단일 행 평탄화 포매터 및 예외 원천 추적 (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/01_single_line_flatten_formatter.md)**: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화 및 `[Origin: ...]` 원천 위치 추출로 중앙 로그 수집(Logstash, Fluentd 등)에 최적화
- **2.2. [로깅 환경 일괄 구성 및 핸들러 제어 (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/02_project_logger_configure.md)**: 콘솔 및 파일 로그 핸들러 동적 생성, 일자별 폴더 분리, 레벨별 파일 분기(`out_file`, `debug_file`) 및 서드파티 노이즈 억제
- **2.3. [다국어 로그 메시지 템플릿 사전 및 코드 기반 로깅 (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/03_multilingual_message_catalog.md)**: `config.yml`의 `logging.language` (`KO` 또는 `EN`) 설정에 따라 한국어/영문 메시지 사전 자동 연동, 런타임 동적 언어 전환 및 안전한 템플릿 치환
- **2.4. [작업 진행 통계 및 예외/제외 사유별 실시간 집계 (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/04_execution_result_and_error_tracking.md)**: 성공, 실패, 제외(Skip) 3단계 상태 분류 및 인스턴스/클래스 전역 멀티스레드 에러 집계
- **2.5. [작업 결과 요약 리포트 자동 생성 (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/kr/logger/05_summary_report_generation.md)**: 소요 시간, 처리 속도, 전송량 및 에러/제외 사유별 상세 내역(`get_log_id_description`)이 포함된 표준 요약 블록 자동 출력

#### 3. 스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)
- `EcsClient`: Dell ECS S3 저장소 접속, 목록 조회, 메타데이터 해석 및 파일 메모리 스트리밍 획득
- `GcsClient`: Google Cloud Storage 연결, 파일 존재 검증 및 대용량 멀티스레드 스트리밍 업로드
- `BigQueryClient`: Google Cloud BigQuery 연결, JSON 데이터 스트리밍 입력(`insert_rows_json`), 배치 로드(`load_table_from_json_data`), 인라인 MERGE(`merge_table_from_json_data` - 한글/특수문자/예약어 컬럼 백틱 지원 및 413 방지 기본 청크 100건 분할), 범용 SQL 쿼리(`query`)

#### 4. 동적 도구 로더 및 템플릿 평가기 (`agent_common.tool_parser`) & 내장 도구 (`agent_common.tool`)
- **이원화된 Tool 디렉터리 계층 탐색**:
  - **1순위 (내장 도구)**: `agent_common/tool/` 하위 모듈 (전사 표준 내장 도구)
  - **2순위 (프로젝트 도구)**: `config.yml`의 `transfer.tool_dir`에 지정된 로컬 경로 (예: `medallion/tool/`)
- **선언적 템플릿 치환 및 표현식 평가 (`ToolParser.eval`)**:
  - 변수 네임스페이스 바인딩: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - 동적 도구 함수 호출: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - 문자열 슬라이싱/메서드: `"{raw_key.lstrip('/')}"`, `"{raw_size|0}"`
- **안전한 네임스페이스 탐색 (`_SafeNamespace`)**:
  - 대소문자 무관 탐색 및 누락된 필드에 대해 KeyError 없이 안전하게 빈 문자열(`""`) 반환
- **내장 공통 도구 (`agent_common.tool.date.DateTimeUtils`)**:
  - `get_today_yyyymmdd()`: `YYYYMMDD` 형식 8자리 일자 반환 (예: `20260824`)
  - `get_now_compact()`: `YYYYMMDDHHMMSS` 형식 14자리 압축 일시 반환 (예: `20260824110500`)
  - `get_now_formatted(fmt)`: `YYYY-MM-DD HH:MM:SS+09:00` 표준 KST 포맷 일시 반환
- **시스템 컨텍스트 스키마 (`agent_common.schemas.sys.json`)**:
  - `{sys.today}`, `{sys.now_compact}`, `{sys.timestamp_compact}`, `{sys.env}` 등 기본 자동 제공

#### 5. 진행률 트래커 및 공용 유틸리티 (`agent_common.utils`)
- `ProgressTracker`: 멀티스레드 실시간 진행률 추적(`[N/Total] (P%)`), 처리 속도 및 남은 시간 예측, 마일스톤 경고 승격 로깅, 최종 요약 리포트(Summary Report) 생성
- `DateTimeUtils`: 전역 일시 헬퍼 함수군

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
llm_client = LlmClient(purpose="sql_generator")

# 2) 프롬프트 기반 텍스트 생성 (외부 API -> 로컬 GGUF 자동 폴백)
prompt_str = "사용자 요청: 2026년 8월 일일 가입자 수 통계 쿼리를 작성해줘."
response_str = llm_client.generate(
    prompt=prompt_str,
    system_prompt="당신은 BigQuery 전문 SQL 생성 AI입니다."
)

print(f"생성된 결과 ({llm_client.last_generated_by}):\n{response_str}")
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
# 개발 환경 (Editable 모드)
pip install -e agent_common

# 배포 환경 (Wheel 패키지 설치)
pip install dist/agent_common-0.4.30-py3-none-any.whl
```

#### PyPI 공공 배포 가이드
본 패키지는 표준 `src/` 레이아웃으로 구성되어 소스 배포판(`sdist`) 및 휠(`wheel`) 파일 용량이 약 50KB 수준으로 최소화되어 있습니다.

```bash
# 1. 빌드 도구 설치
pip install build twine

# 2. 패키지 빌드 (sdist 및 wheel 동시 생성)
python -m build

# 3. 배포 아카이브 검증
python -m twine check dist/*

# 4. PyPI 업로드
python -m twine upload dist/agent_common-0.4.30*
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
- **1.3. [Type Guarantee & Automatic Coercion via Type Suffixes (v0.4.14)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/03_type_coercion_and_guarantee.md)**:
  - `_int`: Automatic integer conversion and type guarantee.
  - `_float`: Automatic floating-point conversion and type guarantee.
  - `_bool`: Automatic boolean conversion (`"true"`, `"false"`, `1`, `0`, etc.).
  - `_str`: Automatic string conversion and `.strip()` whitespace trimming.
  - `_list` / `_dict`: Guaranteed list / immutable dictionary (`ReadOnlyConfig`) wrapping.
- **1.4. [Fail-Fast Required Setting Validation (`require_setting()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/04_fail_fast_require_setting.md)**: Immediate process termination with diagnostic output if required settings are missing during startup.
- **1.5. [Network Proxy Control (`_apply_no_proxy`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/05_network_proxy_control.md)**: Automatic synchronization of `NO_PROXY` environment variable from `proxy.no_proxy` configuration.
- **1.6. [Externalizing All Constants & Self-Healing Templates (`ensure_config_file()`)](https://github.com/kampores/agent_common/blob/main/manual/en/config_loader/06_ensure_config_self_healing.md)**: Materializing all in-code constants to configuration files, automatic scaffolding, and in-place missing key injection.

#### 2. Single-Line Log Formatter & Project Logger (`agent_common.logger`)
- **2.1. [Single-Line Flatten Formatter & Origin Tracking (`SingleLineFlattenFormatter`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/01_single_line_flatten_formatter.md)**: Flattens log records, extracts `[Origin: ...]` caller frames, and optimizes for centralized log aggregators (Logstash, Fluentd, CloudWatch).
- **2.2. [Batch Logging Configuration & Handler Control (`ProjectLogger.configure`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/02_project_logger_configure.md)**: Dynamic console/file handler initialization, date-based directories, level-based file routing (`out_file`, `debug_file`), and third-party noise suppression.
- **2.3. [Multilingual Message Catalog & Code-Based Logging (`logging_messages_*.yml`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/03_multilingual_message_catalog.md)**: Dynamic bilingual dictionary loading (`KO`/`EN`), runtime language switching, and safe template parameter substitution.
- **2.4. [Real-Time Metric Tracking & Error/Exclusion Classification (`record_result`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/04_execution_result_and_error_tracking.md)**: Three-tier outcome model (Success, Failure, Excluded/Skip) and dual instance/class-global multithreaded telemetry.
- **2.5. [Automatic Summary Report Generation (`log_summary`)](https://github.com/kampores/agent_common/blob/main/manual/en/logger/05_summary_report_generation.md)**: Emits structured 80-column execution summary reports with duration, throughput (items/s), transfer rate (MB/s), and decoded error diagnostics.

#### 3. Storage and Database Infrastructure Clients (`agent_common.clients`)
- `EcsClient`: Dell ECS S3 storage connection, object listing, metadata extraction, and in-memory streaming retrieval.
- `GcsClient`: Google Cloud Storage connection, blob existence verification, and high-throughput multithreaded streaming uploads.
- `BigQueryClient`: Google Cloud BigQuery client supporting streaming ingestion (`insert_rows_json`), batch loading (`load_table_from_json_data`), inline MERGE (`merge_table_from_json_data` with backtick escaping and 100-record chunking to prevent HTTP 413), and general SQL execution (`query`).

#### 4. Dynamic Tool Loader & Template Evaluator (`agent_common.tool_parser`) & Built-in Tools (`agent_common.tool`)
- **Dual Tool Hierarchy Discovery**:
  - **Priority 1 (Built-in Tools)**: Modules under `agent_common/tool/` (standard enterprise tools).
  - **Priority 2 (Project Tools)**: Local path configured in `config.yml` under `transfer.tool_dir` (e.g., `medallion/tool/`).
- **Declarative Template Replacement & Expression Evaluation (`ToolParser.eval`)**:
  - Variable namespace binding: `{ecs.key}`, `{sys.today}`, `{json.title}`
  - Dynamic tool function invocation: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`
  - String slicing & fallback methods: `"{raw_key.lstrip('/')}"`, `"{raw_size|0}"`
- **Safe Namespace Lookup (`_SafeNamespace`)**:
  - Case-insensitive lookups returning empty strings (`""`) without raising `KeyError` on missing keys.
- **Built-in Common Utilities (`agent_common.tool.date.DateTimeUtils`)**:
  - `get_today_yyyymmdd()`: Returns 8-digit date string (e.g., `20260824`).
  - `get_now_compact()`: Returns 14-digit timestamp string (e.g., `20260824110500`).
  - `get_now_formatted(fmt)`: Returns standard KST formatted datetime string (`YYYY-MM-DD HH:MM:SS+09:00`).
- **Standard System Context Schema (`agent_common.schemas.sys.json`)**:
  - Automatically provides `{sys.today}`, `{sys.now_compact}`, `{sys.timestamp_compact}`, `{sys.env}`, etc.

#### 5. Progress Tracker & Common Utilities (`agent_common.utils`)
- `ProgressTracker`: Real-time multithreaded progress tracking (`[N/Total] (P%)`), throughput/ETA calculation, milestone log level elevation, and summary report generation.
- `DateTimeUtils`: Global date/time helper functions.

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
llm_client = LlmClient(purpose="sql_generator")

# 2) Prompt-based generation (External API with auto fallback to local GGUF)
prompt_str = "User request: Generate daily subscriber statistics SQL for August 2026."
response_str = llm_client.generate(
    prompt=prompt_str,
    system_prompt="You are an expert AI for BigQuery SQL generation."
)

print(f"Generated result ({llm_client.last_generated_by}):\n{response_str}")
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
# Development (Editable mode)
pip install -e agent_common

# Production (Wheel package)
pip install dist/agent_common-0.4.30-py3-none-any.whl
```

#### PyPI Public Distribution Guide
This package adopts the standard `src/` layout, minimizing distribution archives (`sdist` and `wheel`) to approximately 50KB.

```bash
# 1. Install build tools
pip install build twine

# 2. Build distribution archives (sdist and wheel)
python -m build

# 3. Check distribution archives
python -m twine check dist/*

# 4. Upload to PyPI
python -m twine upload dist/agent_common-0.4.30*
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

---

### 📋 Version History (Changelog)

For detailed version history, please refer to [GitHub CHANGELOG_EN.md](https://github.com/kampores/agent_common/blob/main/CHANGELOG_EN.md).
