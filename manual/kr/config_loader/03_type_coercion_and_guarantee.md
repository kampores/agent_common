# 03. 타입 접미사 자동 형 변환 및 타입 보증 (Type Guarantee & Coercion)

> **소속 모듈**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **도입 버전**: `v0.4.14`  
> **핵심 메서드**: `ReadOnlyConfig._coerce_type_by_key_suffix(key, val)`

---

## 1. 개요 및 배경

YAML 파일 작성 시 따옴표 누락(`timeout: 30` vs `timeout: "30"`)이나 환경변수 주입 시 모든 값이 문자열(`"true"`, `"100"`)로 주입되는 현상으로 인해 파이썬 런타임에서 다음과 같은 버그가 빈번히 발생합니다:

- `"30" + 10` 연산 시 `TypeError: can only concatenate str to str`
- `"false"` 문자열이 `if config.is_enabled:` 조건문에서 `True`로 평가되는 치명적 오작동

`agent_common`은 AGENTS.md 표준의 **명시적 타입 접미사 명명 규칙**과 연계하여, 설정 키의 끝자리 접미사에 따라 파이썬 표준 데이터 타입으로 **런타임에 자동 형 변환 및 타입을 엄격히 보증(Coercion & Guarantee)**합니다.

---

## 2. 지원 접미사 및 자동 형 변환 규칙

| 설정 키 접미사 | 반환 보증 타입 | 형 변환 및 정제 동작 | 입력 예시 및 변환 결과 |
| :--- | :---: | :--- | :--- |
| `_int` | `int` | `int(val)` 자동 변환 (변환 실패 시 원본 반환) | `"100"` ➔ `100`<br/>`100.0` ➔ `100` |
| `_float` | `float` | `float(val)` 자동 변환 | `"3.14"` ➔ `3.14`<br/>`3` ➔ `3.0` |
| `_bool` | `bool` | 대소문자 무관 진위형 판정<br/>(`"true"`, `"1"`, `"yes"`, `"y"`, `"on"` ➔ `True`<br/>그 외 ➔ `False`) | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`"0"` ➔ `False`<br/>`"yes"` ➔ `True` |
| `_str` | `str` | `str(val).strip()`으로 양끝 공백 자동 제거 | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | 튜플, 세트, 단일 원소를 `list`로 보증 | `("a", "b")` ➔ `["a", "b"]`<br/>`"only_one"` ➔ `["only_one"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | 딕셔너리 구조 보증 및 `ReadOnlyConfig` 래핑 | `{}` ➔ `ReadOnlyConfig({})` |

> ⚠️ **참고**: 원본 값이 `None`인 경우에는 타입 변환을 시도하지 않고 안전하게 `None`을 그대로 반환합니다.

---

## 3. 핵심 변환 알고리즘 (`_coerce_type_by_key_suffix`)

```python
@staticmethod
def _coerce_type_by_key_suffix(key: str, val: Any) -> Any:
    if val is None:
        return val
    if key.endswith("_int"):
        try:
            return int(val)
        except (ValueError, TypeError):
            return val
    if key.endswith("_float"):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    if key.endswith("_bool"):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.strip().lower() in ("true", "1", "yes", "y", "on")
        return bool(val)
    if key.endswith("_str"):
        return str(val).strip()
    if key.endswith("_list") and not isinstance(val, list):
        if isinstance(val, (tuple, set)):
            return list(val)
        return [val]
    if key.endswith("_dict") and not isinstance(val, dict):
        return dict(val) if hasattr(val, "to_dict") or hasattr(val, "items") else val
    return val
```

---

## 4. 적용 영역

타입 보증은 `agent_common.config_loader`의 모든 조회 경로에 일관되게 적용됩니다:

1. **점 표기법 (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ `int` 반환
2. **단일 경로 조회 (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ `int` 반환
3. **Fail-Fast 필수 조회 (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ `int` 반환

---

## 5. 실전 활용 예시

### 5.1. YAML 설정 작성 (`config/config.yml`)

```yaml
transfer:
  max_workers_int: "16"          # 문자열로 잘못 입력되어도 int(16) 보증
  timeout_seconds_float: "45.5"  # float(45.5) 보증
  is_active_bool: "yes"          # bool(True) 보증
  environment_str: "  staging  " # 공백이 자동 제거되어 "staging" 보증
  target_tags_list: "production" # 리스트가 아니어도 ["production"]으로 자동 래핑
```

### 5.2. 파이썬 비즈니스 로직

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

이 규칙을 통해 개발자는 `int()`, `float()`, `.strip()`과 같은 불필요한 방어 코드를 비즈니스 로직에서 완전히 제거할 수 있습니다.
