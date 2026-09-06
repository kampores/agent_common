# 1.3. 타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion)

> **소속 모듈**: `agent_common.config_loader` (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`, `ReadOnlyConfig`, `ConfigLoader`)  
> **도입 버전**: `v0.4.14` (범용 함수 승격 및 다중 설정 지원: `v0.4.32`)  
> **핵심 함수/메서드**:  
> - `coerce_type_by_key_suffix(key_str, val_any)` (단일 키-값 범용 변환 함수)  
> - `coerce_dict_by_key_suffix(data_dict)` (중첩 딕셔너리/리스트 일괄 재귀 변환 함수)  
> - `ReadOnlyConfig(data, source_name_str="config.yml")` (불변 점 표기법 래퍼)

---

## 1. 개요 및 배경

YAML 파일 작성 시 따옴표 누락(`timeout: 30` vs `timeout: "30"`)이나 환경변수 주입 시 모든 값이 문자열(`"true"`, `"100"`)로 주입되는 현상으로 인해 파이썬 런타임에서 다음과 같은 버그가 빈번히 발생합니다:

- `"30" + 10` 연산 시 `TypeError: can only concatenate str to str`
- `"false"` 문자열이 `if config.is_enabled:` 조건문에서 `True`로 평가되는 치명적 오작동

`agent_common`은 AGENTS.md 표준의 **명시적 타입 접미사 명명 규칙**과 연계하여, 설정 키의 끝자리 접미사에 따라 파이썬 표준 데이터 타입으로 **런타임에 자동 형 변환 및 타입을 엄격히 보증(Coercion & Guarantee)**합니다.

`v0.4.32`부터는 `config.yml` 뿐만 아니라 **임의의 외부 설정 파일(`rule.yml`, `mapping.yml`, `db.yml` 등)**과 임의의 인메모리 딕셔너리(JSON, Dict)에서도 단독 함수로 즉시 import하여 활용할 수 있도록 **범용 공개 함수(`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`)**로 제공됩니다.

---

## 2. 지원 접미사 및 자동 형 변환 규칙

| 설정 키 접미사 | 반환 보증 타입 | 형 변환 및 정제 동작 | 실패 시 동작 (Fail-Fast) | 입력 예시 및 변환 결과 |
| :--- | :---: | :--- | :--- | :--- |
| `_int` | `int` | `int(val)` 자동 변환 | **`ValueError` 발생 (Fast-Fail)**<br/>올바른 정수형 입력 안내 | `"100"` ➔ `100`<br/>`"abc"` ➔ `ValueError` |
| `_float` | `float` | `float(val)` 자동 변환 | **`ValueError` 발생 (Fast-Fail)**<br/>올바른 숫자형 입력 안내 | `"3.14"` ➔ `3.14`<br/>`"xyz"` ➔ `ValueError` |
| `_bool` | `bool` | 명시적 진위형 판정<br/>(`"true"`, `"1"`, `"yes"`, `"y"`, `"on"` ➔ `True`<br/>`"false"`, `"0"`, `"no"`, `"n"`, `"off"` ➔ `False`) | **`ValueError` 발생 (Fast-Fail)**<br/>불리언 규격 입력 안내 | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`"hello"` ➔ `ValueError` |
| `_str` | `str` | `str(val).strip()`으로 양끝 공백 자동 제거 | - | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | 튜플, 세트, 단일 원소를 `list`로 보증 | - | `("a", "b")` ➔ `["a", "b"]`<br/>`"only_one"` ➔ `["only_one"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | 딕셔너리 구조 보증 및 `ReadOnlyConfig` 래핑 | **`TypeError` 발생 (Fast-Fail)**<br/>딕셔너리 매핑 입력 안내 | `{}` ➔ `ReadOnlyConfig({})`<br/>`123` ➔ `TypeError` |

> ⚠️ **참고**: 원본 값이 `None`인 경우에는 타입 변환을 시도하지 않고 안전하게 `None`을 그대로 반환합니다.

---

## 3. 핵심 변환 알고리즘

### 3.1. 단일 키-값 변환 (`coerce_type_by_key_suffix`)

```python
from agent_common.error_handler import ErrorHandler


def coerce_type_by_key_suffix(key_str: str, val_any: Any) -> Any:
    if val_any is None:
        return None

    if key_str.endswith("_int"):
        try:
            return int(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="정수형(int)",
                guide_msg_str="정수형 값으로 입력해 주십시오.",
                cause_exc=err,
            )

    if key_str.endswith("_float"):
        try:
            return float(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="실수형(float)",
                guide_msg_str="올바른 숫자형 값으로 입력해 주십시오.",
                cause_exc=err,
            )

    if key_str.endswith("_bool"):
        if isinstance(val_any, bool):
            return val_any
        if isinstance(val_any, str):
            clean_str = val_any.strip().lower()
            if clean_str == "true":
                return True
            if clean_str == "false":
                return False
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="불리언(bool)",
                guide_msg_str="True 또는 False 값으로 입력해 주십시오.",
                exc_cls=ValueError,
            )
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="불리언(bool)",
            guide_msg_str="True 또는 False 값으로 입력해 주십시오.",
            exc_cls=TypeError,
        )

    if key_str.endswith("_str"):
        return str(val_any).strip()

    if key_str.endswith("_list"):
        if isinstance(val_any, list):
            return val_any
        if isinstance(val_any, (tuple, set)):
            return list(val_any)
        return [val_any]

    if key_str.endswith("_dict"):
        if isinstance(val_any, dict):
            return val_any
        if hasattr(val_any, "to_dict") and callable(val_any.to_dict):
            return val_any.to_dict()
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="딕셔너리(dict)",
            guide_msg_str="딕셔너리 매핑 구조로 입력해 주십시오.",
            exc_cls=TypeError,
        )

    return val_any
```

### 3.2. 중첩 딕셔너리 일괄 재귀 변환 (`coerce_dict_by_key_suffix`)

```python
def coerce_dict_by_key_suffix(data_dict: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data_dict, dict):
        return data_dict

    result_dict: dict[str, Any] = {}
    for key_str, val_any in data_dict.items():
        if isinstance(val_any, dict):
            result_dict[key_str] = coerce_dict_by_key_suffix(val_any)
        elif isinstance(val_any, list):
            result_dict[key_str] = [
                coerce_dict_by_key_suffix(item_any) if isinstance(item_any, dict) else item_any
                for item_any in val_any
            ]
        else:
            result_dict[key_str] = coerce_type_by_key_suffix(key_str, val_any)
    return result_dict
```

---

## 4. 적용 영역

타입 보증은 `agent_common` 전반의 설정 로더 및 임의의 외부 설정 파일에 일관되게 적용됩니다:

1. **점 표기법 (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ `int` 반환
2. **단일 경로 조회 (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ `int` 반환
3. **Fail-Fast 필수 조회 (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ `int` 반환
4. **다른 설정 파일 및 딕셔너리 직접 변환 (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`)**:  
   외부 YAML/JSON 설정 파싱 후 단일 값 또는 딕셔너리 전체에 즉시 적용 가능
5. **임의의 설정 파일 `ReadOnlyConfig` 래핑**:  
   `ReadOnlyConfig(custom_dict, source_name_str="rule.yml")` 형태로 점 표기법 + 불변성 + 파일 맞춤형 진단 예외 제공

---

## 5. 실전 활용 예시

### 5.1. 기본 `config/config.yml` 점 표기법 활용

```python
from agent_common.config_loader import config

# 1) _int 보증: 즉시 산술 연산 가능
batch_size: int = config.transfer.max_workers_int
total_capacity = batch_size * 10  # 160 (정수 연산 성공)

# 2) _bool 보증: 문자열 불리언 판정 오류 완전 차단
if config.transfer.is_active_bool:
    print("서비스 활성화 상태입니다.")

# 3) _str 보증: 공백 오염 없는 정확한 문자열 비교
if config.transfer.environment_str == "staging":
    print("스테이징 환경입니다.")

# 4) _list 보증: for-in 순회 가능
for tag in config.transfer.target_tags_list:
    print(f"태그: {tag}")
```

### 5.2. 다른 설정 파일(`rule.yml`, `mapping.yml` 등)에 범용 적용

#### A. 중첩 딕셔너리 일괄 정제 (`coerce_dict_by_key_suffix`)

```python
import yaml
from agent_common import coerce_dict_by_key_suffix

with open("config/rule.yml", "r", encoding="utf-8") as f:
    raw_rules = yaml.safe_load(f)

# 중첩된 모든 키(_int, _bool, _str 등)의 값이 일괄 타입 변환된 깨끗한 dict 획득
clean_rules = coerce_dict_by_key_suffix(raw_rules)

assert isinstance(clean_rules["retry"]["max_attempts_int"], int)
assert isinstance(clean_rules["features"]["enable_cache_bool"], bool)
```

#### B. 임의의 설정 파일 불변 점 표기법 래핑 (`ReadOnlyConfig`)

```python
import yaml
from agent_common import ReadOnlyConfig

with open("config/mapping.yml", "r", encoding="utf-8") as f:
    mapping_data = yaml.safe_load(f)

# 파일명을 지정하여 불변 점 표기법 객체 생성
mapping_cfg = ReadOnlyConfig(mapping_data, source_name_str="mapping.yml")

# 점 표기법 및 타입 보증 동시 지원
timeout_sec = mapping_cfg.timeout_float
print(f"타임아웃: {timeout_sec}")

# 정의되지 않은 키 접근 시 정확한 파일명과 함께 AttributeError 발생
# AttributeError: mapping.yml에 정의되지 않은 설정 항목입니다: 'undefined_key'
```

#### C. 단일 키-값 변환 (`coerce_type_by_key_suffix`)

```python
from agent_common import coerce_type_by_key_suffix

# 환경 변수나 CLI 인자, 외부 API 응답값 단건 변환
port = coerce_type_by_key_suffix("server_port_int", "8080")  # 8080 (int)
debug = coerce_type_by_key_suffix("is_debug_bool", "yes")     # True (bool)
```

이 규칙을 통해 개발자는 `int()`, `float()`, `.strip()`과 같은 불필요한 방어 코드를 비즈니스 로직에서 완전히 제거할 수 있습니다.
