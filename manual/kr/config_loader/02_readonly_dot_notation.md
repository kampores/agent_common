# 02. 불변 점 표기법 조회 (`ReadOnlyConfig`)

> **소속 모듈**: `agent_common.config_loader.ReadOnlyConfig`  
> **관련 전역 인스턴스**: `from agent_common.config_loader import config`

---

## 1. 개요 및 설계 의도

기존 파이썬 딕셔너리 기반 설정 조회(`config['ecs']['endpoint_url']`)는 다음과 같은 심각한 유지보수 및 안정성 문제를 야기합니다:
1. **키 오타에 취약**: 문자열 키 오타 시 컴파일 타임 및 정적 분석에서 감지 불가
2. **코드 가독성 저하**: 중첩 대괄호와 따옴표로 인한 시각적 피로도 증가
3. **런타임 변조 위험**: 임의의 모듈이나 스레드에서 `config['key'] = new_val` 형태로 공유 설정을 수정하여 다른 컴포넌트의 동작을 훼손할 가능성

`ReadOnlyConfig`는 이러한 문제를 원천 차단하기 위해 **점 표기법(Dot-notation, 속성 접근)과 엄격한 불변성(Immutability)**을 결합한 고성능 설정 래퍼 클래스입니다.

---

## 2. 주요 기능 및 특징

### 2.1. 직관적인 점 표기법(Dot-Notation) 탐색
`config.ecs.endpoint_url`, `config.transfer.max_workers_int`처럼 객체 속성에 접근하듯 간결하게 설정값을 읽어들일 수 있습니다.

- 중첩된 하위 딕셔너리(`dict`)는 읽기 시점에 자동으로 또 다른 `ReadOnlyConfig` 객체로 재귀 래핑됩니다.
- 중첩 리스트(`list`) 내의 딕셔너리 항목 또한 자동으로 `ReadOnlyConfig`로 래핑되어 일관된 속성 조회를 보장합니다.

### 2.2. 엄격한 불변성 (Read-Only 보장)
설정 객체의 무결성을 보장하기 위해 모든 변경 및 삭제 연산을 원천 차단합니다:

```python
def __setattr__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __setitem__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __delattr__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

def __delitem__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")
```

### 2.3. 기존 딕셔너리 인터페이스와의 완벽한 호환성
점 표기법뿐만 아니라 기존 파이썬 문법과의 상호 운용성을 완벽히 지원합니다:

- **인덱싱 조회**: `config['ecs']['endpoint_url']` (점 표기법과 동일 결과)
- **멤버십 검사 (`in` 연산자)**: `'ecs' in config`, `'endpoint_url' in config.ecs`
- **순수 딕셔너리 변환**: `config.to_dict()`를 통해 외부 라이브러리(Boto3, BigQuery Client 등)에 원본 딕셔너리 전달 가능

---

## 3. 실전 코드 예시

### 3.1. 정상 조회 패턴

```python
from agent_common.config_loader import config

# 1. 점 표기법 계층 접근
endpoint_str: str = config.ecs.endpoint_url
bucket_str: str = config.gcs.bucket_name_str

# 2. 존재 여부 확인 (in 연산자)
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id

# 3. 외부 API 호출을 위한 딕셔너리 추출
ecs_kwargs = config.ecs.to_dict()
```

### 3.2. 변조 시도 시 예외 발생 (방어적 동작)

```python
from agent_common.config_loader import config

try:
    # 런타임 변조 시도
    config.ecs.endpoint_url = "http://malicious-url:9020"
except TypeError as e:
    print(f"변조 방어 성공: {e}")
    # 출력: 변조 방어 성공: config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).

try:
    # 딕셔너리 인덱싱 변경 시도
    config['ecs']['endpoint_url'] = "http://malicious-url:9020"
except TypeError as e:
    print(f"변조 방어 성공: {e}")
```

### 3.3. 미정의 속성 접근 시 Fail-Fast 에러 안내

```python
from agent_common.config_loader import config

try:
    non_existent = config.ecs.unknown_property
except AttributeError as e:
    print(f"속성 오류: {e}")
    # 출력: 속성 오류: config.yml에 정의되지 않은 설정 항목입니다: 'unknown_property'
```

---

## 4. 모범 아키텍처 규칙 (AGENTS.md 연계)

- **규칙 1.4.2 (Direct Immutable Config Access)**:  
  정적이고 불변인 전역 설정값을 클래스 내부 `self` 인스턴스 변수로 중복 복사(Clone)하지 마십시오.  
  반드시 `config.ecs.endpoint_url` 형태로 전역 `config` 객체를 직접 참조하여 단일 진실 공급원(Single Source of Truth)을 유지하십시오.
