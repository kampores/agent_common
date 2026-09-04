# 1.6. 모든 상수의 설정 파일화 및 템플릿 보정 (`ensure_config_file`)

> **소속 모듈**: `agent_common.config_loader.ConfigLoader`  
> **핵심 메서드**: `ConfigLoader.ensure_config_file()`, `ConfigLoader.register_schema()`  
> **연계 원칙**: `AGENTS.md` 제1.1조 (No Hardcoding & 설정 분리 원칙)

---

## 1. 핵심 설계 철학: 왜 이 기능이 필요한가?

> **"‘자가 치유(Self-healing)’는 동작 방식일 뿐, 본질이자 주 목적은 ‘코드 내 모든 상수의 설정 파일화(외부화)와 가시화’입니다."**

많은 프로그램에서 개발자들은 소스 코드 곳곳에 기본 상수값(타임아웃, 배치 크기, 재시도 횟수, 워커 수 등)을 하드코딩해 두고, 설정 파일에 값이 없으면 코드 내부의 기본값(fallback)을 조용히 꺼내 쓰는 방식을 취하곤 합니다.  
하지만 이러한 방식은 심각한 문제를 야기합니다:

- **설정 항목의 블랙박스화**: 소스 코드를 직접 열어 분석하지 않는 한, 개발자나 이용자는 **"이 프로그램에 어떤 튜닝 가능한 상수가 존재하는지"**, **"기본값으로 몇 초, 몇 개가 지정되어 있는지"** 알 방법이 없습니다.
- **하드코딩 분리 원칙 위배**: `AGENTS.md` 제1.1조(No Hardcoding)에 명시된 대로 시스템의 동작을 제어하는 모든 상수와 파라미터는 설정 파일로 완전히 외부화되어야 합니다.

### 본 기능의 주 목적과 실현 원리

1. **모든 상수의 설정 파일화 (주 목적)**:
   - 코드 내부에 숨어 있는 모든 상수값을 설정 파일(`config.yml`)로 강제 외부화하여 운영자와 개발자에게 100% 투명하게 공개합니다.
2. **코드 맨 처음 / 최초 실행단 스키마 선언**:
   - 모든 상수를 config화하기 위해, **코드의 맨 처음과 최초 실행단(Entry Point)**에서 시스템에 필요한 모든 상수와 초기 기본값을 담은 **설정 스키마(`default_schema`)**를 선언합니다.
3. **상수값 강제 주입 (말이 '자가 치유'이지 실질은 '상수 강제 주입')**:
   - 설정 파일에 특정 설정이 누락되어 있다면, 코드 내부에서 조용히 기본값으로 땜질(Silent Fallback)하는 대신 **설정 파일에 누락된 상수의 기본값을 물리적으로 강제 주입(기록)**합니다.
   - 이렇게 강제로 상수값을 파일에 밀어 넣어 줌으로써, 개발자나 이용자가 생성/보정된 설정 파일만 열어보면 **"어떤 상수가 존재하며 현재 무슨 값으로 설정되어 있는지"** 즉시 파악하고 직관적으로 수정할 수 있게 됩니다.

> [!CAUTION]
> ### ⚠️ 중요 철칙: 상수를 따로 정의하거나 코드 중간에 만들면 본 기능은 완전히 무의미해집니다!
> `ensure_config_file()`의 존재 이유는 **"코드 내 모든 상수를 최초 실행단 스키마로 모아 설정 파일에 강제로 꺼내놓는 것"**입니다.  
> 만약 이 기능을 사용하더라도 다음과 같은 방식으로 코딩한다면 **이 기능의 가치와 목적은 완전히 상실**됩니다:
> 
> - **코드 중간(함수나 클래스 내부)에서 독자적인 상수를 하드코딩해 쓰는 경우**
> - **`default_schema`에 등록하지 않고 별도의 모듈/파일에 상수를 따로 정의하여 쓰는 경우**
> 
> 스키마에 등록되지 않은 상수는 `ensure_config_file()`이 감지할 수 없어 `config.yml`에 자동 주입되지 않으므로, **여전히 소스 코드 속에 파묻힌 '블랙박스 상수'로 남게 됩니다**.  
> 따라서 **"모든 상수는 반드시 최초 실행단의 `default_schema` 단 한 곳에 선언하고, 비즈니스 로직 코드 내부에서는 오직 전역 `config` 객체로만 참조한다"**는 단일 창구화(Single Source of Truth) 원칙을 철저히 준수해야 합니다.

---

## 2. 메서드 시그니처 및 파라미터

```python
def ensure_config_file(
    self, 
    config_file_name: str = "config.yml", 
    default_schema: Optional[dict[str, Any]] = None
) -> Path:
```

- **`config_file_name` (str)**: 검증 및 상수를 주입·보정할 대상 설정 파일명 (기본값: `"config.yml"`)
- **`default_schema` (dict | None)**: 코드 최초 실행단에 정의된 기본 상수 딕셔너리 스키마. (미지정 시 `register_schema`로 등록된 스키마 사용)
- **반환값 (`Path`)**: 모든 상수가 파일화되어 보정 완료된 설정 파일의 절대 경로 `Path` 객체

---

## 3. 상수 강제 주입 및 파일 보정 흐름

```mermaid
flowchart TD
    Start[코드 맨 처음 / 최초 실행단:<br/>모든 상수를 담은 default_schema 정의] --> Call[ensure_config_file 호출]
    Call --> CheckExist{config.yml 파일이<br/>존재하는가?}
    
    CheckExist -- 아니오 (신규 환경) --> CreateNew[1. 전체 상수를 담은 config.yml 파일 신규 생성<br/>헤더 안내 주석 자동 부착]
    CreateNew --> LogCreate[logger.info: config_file_auto_created]
    
    CheckExist -- 예 (기존 파일 존재) --> CompareSchema[2. 기존 설정 내용과 스키마 내 상수 비교]
    CompareSchema --> MissingCheck{파일에 누락된<br/>상수가 있는가?}
    MissingCheck -- 없음 (모든 상수 반영됨) --> Done[완료: 캐시 갱신 및 정상 진행]
    MissingCheck -- 있음 (일부 상수 누락) --> ForceInject[3. 누락된 상수 기본값을 파일에 강제 주입<br/># 자동 추가: YYYY-MM-DD... 인라인 주석 병합]
    ForceInject --> LogRepair[logger.info: config_file_auto_repaired]
    LogRepair --> Done
```

### 3.1. Case 1: 파일이 아예 없을 때 (신규 자동 생성 및 전체 상수 주입)
- `config/` 디렉터리가 없으면 자동 생성합니다.
- 스키마에 정의된 모든 상수와 가이드 헤더 주석을 포함하여 `config.yml` 파일을 즉시 생성합니다.
- 사용자는 이 파일을 열어 시스템에 존재하는 모든 상수를 한눈에 확인하고 바로 값을 커스터마이징할 수 있습니다.

### 3.2. Case 2: 파일은 있으나 새로운 상수가 없을 때 (상수 강제 주입 및 인라인 주석)
- 기존 사용자가 설정해 둔 값과 주석을 100% 보존합니다.
- 파일에 아직 반영되지 않은 누락된 상수를 찾아 기본값을 파일 끝 또는 해당 블록에 **강제로 기록**합니다.
- 추가된 라인 끝에 `# [자동 추가: 2026-09-04 14:30:00+09:00]`와 같은 **타임스탬프 인라인 주석**을 붙여, 운영자가 어떤 상수가 파일에 새로 주입되었는지 즉시 인지할 수 있도록 합니다.

---

## 4. 실전 활용 예시

### 4.1. 애플리케이션 최초 기동단(Entry Point) 작성 패턴

```python
from agent_common.config_loader import ConfigLoader

loader = ConfigLoader()

# ==============================================================================
# [핵심 원칙] 코드 맨 처음 / 최초 실행단에 시스템의 모든 상수를 스키마로 정의
# 소스 코드 내부의 하드코딩을 배제하고, 설정 파일로 투명하게 노출할 모든 상수를 선언합니다.
# ==============================================================================
APP_DEFAULT_SCHEMA = {
    "transfer": {
        "max_workers_int": 4,          # 동시 전송 워커 수 상수
        "batch_size_int": 500,         # 1회 배치 처리 행 수 상수
        "timeout_seconds_int": 30,     # 네트워크 타임아웃(초) 상수
        "enable_metrics_bool": True    # 메트릭 수집 활성화 여부
    },
    "logging": {
        "level_str": "INFO",           # 기본 로그 레벨 상수
        "language": "KO"               # 로그 출력 언어
    }
}

# 1. 스키마 등록 (런타임 기본 뼈대로 상시 유지)
loader.register_schema(APP_DEFAULT_SCHEMA)

# 2. 모든 상수의 설정 파일화 실행 (누락된 상수가 있다면 config.yml에 강제 주입)
config_path = loader.ensure_config_file("config.yml", default_schema=APP_DEFAULT_SCHEMA)
print(f"모든 상수가 파일화되어 보정 완료된 경로: {config_path}")
```

### 4.2. 다중 프로그램 환경에서의 설정값(상수) 공유 및 스키마 합성 패턴 (`app_schema.py`)

실무 프로젝트(데이터 파이프라인, 마이크로서비스 등)는 단일 프로그램이 아니라 **동일한 데이터베이스나 스토리지 인프라를 공유하는 여러 개의 독립 실행 프로그램(API 서버, 배치 워커, 스트리밍 컨슈머 등)**으로 구성되는 경우가 많습니다.

> **일반적인 다중 서비스 구성 예시**:
> 1. `api_server.py`: 클라이언트 요청을 수신하여 처리하는 실시간 웹 API 서비스
> 2. `batch_worker.py`: 주기적으로 대량의 데이터를 수집·가공하는 백그라운드 배치 프로그램
> 3. `stream_consumer.py`: 메시지 브로커(Kafka 등)의 이벤트를 구독하여 저장소에 동기화하는 스트리밍 컨슈머

이때 데이터베이스 접속 정보(`database`), 저장소 경로(`storage`), 공통 로깅(`logging`)과 같은 시스템 상수는 **모든 프로그램이 동일하게 공유**해야 하지만, 포트 번호(`port_int`), 1회 배치 처리량(`batch_size_int`), 버퍼 크기(`buffer_size_int`) 등은 **프로그램마다 고유한 값**을 가집니다.

만약 각 프로그램마다 스키마를 제각각 따로 작성하면 동일한 상수가 여러 파일에 중복 정의되어 `DRY`(Don't Repeat Yourself) 원칙을 위배하게 되고, 상수 수정 시 모든 스크립트를 찾아 고쳐야 하는 위험이 발생합니다.

이를 깔끔하게 해결하는 표준 설계 패턴이 바로 **전용 스키마 모듈(`app/app_schema.py`)을 통한 스키마 합성(Composition) 패턴**입니다.

#### 1) 전용 스키마 모듈 정의 (`app/app_schema.py`)

공통 섹션별 기본 상수를 베이스 딕셔너리로 분리 정의한 뒤, 파이썬 딕셔너리 언패킹(`**`)을 통해 프로그램별 차이점만 간결하게 오버라이드하여 합성합니다:

```python
# app/app_schema.py
"""
애플리케이션 공통 및 프로그램별 기본 설정 스키마 정의 모듈.
"""

from typing import Any, Dict


# ==============================================================================
# 1. 공통 섹션별 베이스 스키마 정의 (DRY 원칙 준수)
# ==============================================================================
_BASE_DATABASE_SCHEMA: Dict[str, Any] = {
    "host_str": "127.0.0.1",
    "port_int": 5432,
    "pool_size_int": 10,
    "timeout_seconds_int": 30,
    "auto_reconnect_bool": True,
}

_BASE_STORAGE_SCHEMA: Dict[str, Any] = {
    "base_path_str": "/var/data/app",
    "temp_dir_str": "temp",
    "chunk_size_int": 1048576,  # 1MB
    "max_retries_int": 3,
}

_BASE_LOGGING_SCHEMA: Dict[str, Any] = {
    "language": "KO",
    "file_logging": False,
    "level": {
        "api": "INFO",
        "batch": "WARNING",
        "consumer": "INFO",
    },
}


# ==============================================================================
# 2. 프로그램별 전용 스키마 (공통 베이스 상속 + 고유 옵션 오버라이드)
# ==============================================================================

# 프로그램 1: 웹 API 백엔드 서비스
API_SERVER_SCHEMA: Dict[str, Any] = {
    "database": _BASE_DATABASE_SCHEMA,
    "server": {
        "port_int": 8080,
        "max_connections_int": 500,
        "enable_cors_bool": True,
    },
    "logging": _BASE_LOGGING_SCHEMA,
}

# 프로그램 2: 백그라운드 배치 처리 워커
BATCH_WORKER_SCHEMA: Dict[str, Any] = {
    "database": _BASE_DATABASE_SCHEMA,
    "storage": _BASE_STORAGE_SCHEMA,
    "batch": {
        "batch_size_int": 500,
        "max_workers_int": 4,
        "cron_schedule_str": "0 2 * * *",
    },
    "logging": _BASE_LOGGING_SCHEMA,
}

# 프로그램 3: 메시지 스트림 컨슈머
STREAM_CONSUMER_SCHEMA: Dict[str, Any] = {
    "database": _BASE_DATABASE_SCHEMA,
    "storage": _BASE_STORAGE_SCHEMA,
    "consumer": {
        "group_id_str": "events-consumer-group",
        "buffer_limit_int": 100,
        "flush_interval_seconds_int": 5,
    },
    "logging": _BASE_LOGGING_SCHEMA,
}
```

#### 2) 개별 프로그램 엔트리포인트에서의 활용

각 실행 프로그램(CLI 진입점)에서는 중앙 `app_schema.py`로부터 자신의 전용 스키마를 가져와 `ensure_config_file`에 전달합니다:

```python
# bin/run_api_server.py (API 서버 진입점)
from agent_common.config_loader import ConfigLoader, config
from app.app_schema import API_SERVER_SCHEMA

loader = ConfigLoader()
loader.register_schema(API_SERVER_SCHEMA)
loader.ensure_config_file("config.yml", default_schema=API_SERVER_SCHEMA)

# 전역 config 객체로 타입 보증된 상수 참조
port = config.server.port_int
db_host = config.database.host_str
```

```python
# bin/run_batch_worker.py (배치 워커 진입점)
from agent_common.config_loader import ConfigLoader, config
from app.app_schema import BATCH_WORKER_SCHEMA

loader = ConfigLoader()
loader.register_schema(BATCH_WORKER_SCHEMA)
loader.ensure_config_file("config.yml", default_schema=BATCH_WORKER_SCHEMA)

# 전역 config 객체로 타입 보증된 상수 참조
batch_size = config.batch.batch_size_int
max_workers = config.batch.max_workers_int
```

#### 3) 다중 프로그램 스키마 공유의 핵심 이점
- **점진적 무손실 자가 치유 (Progressive Reconciliation)**:
  `run_api_server.py`가 먼저 기동되면 공통 `database` 설정과 `server` 관련 상수가 `config.yml`에 생성되고, 이후 `run_batch_worker.py`가 기동되면 기존 설정은 그대로 유지한 채 `storage` 및 `batch` 관련 누락 상수 키들만 인라인 주석과 함께 파일에 **추가로 자동 보정(주입)**됩니다.
- **상수 중복의 원천 배제 (DRY)**: 공통 데이터베이스 접속 포트, 타임아웃, 스토리지 버퍼 크기 등의 상수가 `app_schema.py` 한 곳에만 존재하므로, 기본값을 튜닝할 때 여러 소스 파일을 뒤져가며 수정할 필요가 없습니다.
- **단일 설정 파일(`config.yml`) 내 조화로운 공존**: `logging.level.api`, `logging.level.batch`, `logging.level.consumer`처럼 각 서비스별 고유 설정이 단 하나의 `config.yml` 안에서 충돌 없이 깔끔하게 공존하고 중앙 제어됩니다.

---

### 4.3. 보정 결과 파일 예시 (`config/config.yml`)

기존에 사용자가 `max_workers_int: 8`만 수동으로 적어두고 나머지 상수는 몰랐던 상태라면, 실행 직후 다음과 같이 모든 상수가 파일에 **강제 주입**됩니다:

```yaml
transfer:
  max_workers_int: 8
  batch_size_int: 500  # [자동 추가: 2026-09-04 14:35:10+09:00]
  timeout_seconds_int: 30  # [자동 추가: 2026-09-04 14:35:10+09:00]
  enable_metrics_bool: true  # [자동 추가: 2026-09-04 14:35:10+09:00]
logging:
  level_str: "INFO"  # [자동 추가: 2026-09-04 14:35:10+09:00]
  language: "KO"  # [자동 추가: 2026-09-04 14:35:10+09:00]
```

- 사용자가 정의한 기존 커스텀 값(`max_workers_int: 8`)은 안전하게 보존됩니다.
- 미처 몰랐거나 새로 추가된 모든 상수값들이 파일에 기록되어, 사용자가 메모장이나 편집기로 열었을 때 **"아, 이런 상수가 있었구나!"** 하고 즉시 파악할 수 있게 됩니다.

### 4.4. ⚠️ 안티패턴 비교: 코드 중간에서 독자 상수를 만들어 쓰는 경우 (기능 무의미화)

```python
# ==============================================================================
# ❌ [치명적인 안티패턴] ensure_config_file을 쓰면서도 코드 중간에 상수를 따로 두는 경우
# ==============================================================================
def process_batches():
    # 스키마에 선언하지 않고 함수 내부나 코드 중간에 독자적인 상수를 정의하면,
    # config.yml에 강제 주입되지 않아 이용자/운영자가 이 상수의 존재를 알 수 없습니다.
    DEFAULT_TIMEOUT_SECONDS = 60    # ❌ 여전히 코드 속에 은닉된 블랙박스 상수!
    MAX_BATCH_ROWS = 1000           # ❌ 운영자가 설정 파일(config.yml)을 열어도 튜닝 불가!
    ...


# ==============================================================================
# ⭕ [올바른 패턴] 모든 상수를 엔트리포인트 스키마에 모으고, 런타임에는 config로만 접근
# ==============================================================================
# 1) 최초 실행단(app_schema.py 등)의 default_schema에 모든 상수를 등록
APP_DEFAULT_SCHEMA = {
    "transfer": {
        "timeout_seconds_int": 60,  # ⭕ 최초 1회 선언
        "batch_rows_int": 1000,     # ⭕ 파일 누락 시 config.yml에 자동 강제 주입
    }
}
loader.ensure_config_file("config.yml", default_schema=APP_DEFAULT_SCHEMA)

# 2) 비즈니스 로직(함수/클래스)에서는 오직 config 속성으로만 참조
def process_batches():
    timeout = config.transfer.timeout_seconds_int  # ⭕ config.yml과 완벽히 동기화
    batch_rows = config.transfer.batch_rows_int    # ⭕ 코드 수정 없이 설정 파일만으로 즉시 튜닝 가능
    ...
```

---

## 5. 기대 효과 및 아키텍처적 의의

1. **모든 상수의 완전한 설정 파일화 (하드코딩 배제)**:
   - 코드 곳곳에 흩어져 숨어 있는 매직 넘버를 완전히 제거하고, 설정 파일이라는 단일 창구로 상수를 일원화합니다.
2. **개발자 및 이용자의 설정 가시성(Visibility) 극대화**:
   - 소스 코드를 뒤져보지 않아도 `config.yml` 파일만 열면 프로그램에 존재하는 모든 제어 상수와 기본값을 한눈에 확인할 수 있습니다.
3. **침묵하는 기본값(Silent Fallback) 방지**:
   - 설정이 없다고 해서 코드 내부에서 조용히 기본값으로 땜질하는 것이 아니라, 설정 파일에 명시적으로 상수값을 강제 기록하여 설정과 런타임 동작의 일치성을 보증합니다.
4. **배포 안정성 및 버전 마이그레이션 자동화**:
   - 신규 버전 배포 시 새롭게 추가된 설정 상수가 기존 환경의 `config.yml`에 자동 반영되므로 배포 사고 및 수동 마이그레이션 부담이 해소됩니다.
5. **상수 정의의 단일 창구화 (Single Source of Truth)**:
   - 코드 곳곳에 파편화되어 숨어 있던 상수를 최초 실행단 스키마와 `config.yml`로 완전히 일원화하여, 코드 중간의 임의 상수 생성을 원천 차단합니다.
