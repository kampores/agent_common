# 1.3. Type Guarantee & Automatic Coercion via Type Suffixes

> **Module**: `agent_common.config_loader` (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`, `ReadOnlyConfig`, `ConfigLoader`)  
> **Introduced In**: `v0.4.14` (Generalized Public Functions & Multi-Config Support: `v0.4.32`)  
> **Key Functions/Methods**:  
> - `coerce_type_by_key_suffix(key_str, val_any)` (Standalone key-value type coercion)  
> - `coerce_dict_by_key_suffix(data_dict)` (Recursive nested dictionary batch coercion)  
> - `ReadOnlyConfig(data, source_name_str="config.yml")` (Immutable dot-notation wrapper)

---

## 1. Overview & Problem Statement

In YAML configurations and environment variable injections, type ambiguity frequently causes subtle runtime bugs:
- Quoted numbers (e.g. `timeout: "30"`) causing `TypeError: can only concatenate str to str`.
- Quoted boolean values (e.g. `is_enabled: "false"`) evaluating to `True` in Python truthiness checks (`bool("false") == True`).

`agent_common` integrates with the strict AGENTS.md **type-suffix naming convention** (`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`), automatically coercing and guaranteeing exact Python standard types at runtime.

Starting from `v0.4.32`, these capabilities are promoted to **first-class public functions** (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`) so that any configuration file (`rule.yml`, `mapping.yml`, `db.yml`) or arbitrary in-memory dictionaries can be coerced cleanly without being tied strictly to `config.yml`.

---

## 2. Supported Suffixes & Coercion Rules

| Configuration Key Suffix | Guaranteed Return Type | Coercion Logic & Normalization | Failure Behavior (Fail-Fast) | Example Input & Result |
| :--- | :---: | :--- | :--- | :--- |
| `_int` | `int` | Automatically converted via `int(val)` | **Raises `ValueError` (Fail-Fast)**<br/>Diagnostic integer guidance | `"100"` ➔ `100`<br/>`"abc"` ➔ `ValueError` |
| `_float` | `float` | Automatically converted via `float(val)` | **Raises `ValueError` (Fail-Fast)**<br/>Diagnostic float guidance | `"3.14"` ➔ `3.14`<br/>`"xyz"` ➔ `ValueError` |
| `_bool` | `bool` | Explicit boolean conversion<br/>(`"true"`, `"1"`, `"yes"`, `"y"`, `"on"` ➔ `True`<br/>`"false"`, `"0"`, `"no"`, `"n"`, `"off"` ➔ `False`) | **Raises `ValueError` (Fail-Fast)**<br/>Diagnostic boolean guidance | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`"hello"` ➔ `ValueError` |
| `_str` | `str` | Automatically converted to `str(val)` with whitespace stripped (`.strip()`) | - | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | Ensures tuples, sets, or single items are returned as a `list` | - | `("a", "b")` ➔ `["a", "b"]`<br/>`"single"` ➔ `["single"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | Guarantees dictionary mapping structure and wraps in `ReadOnlyConfig` | **Raises `TypeError` (Fail-Fast)**<br/>Diagnostic dictionary guidance | `{}` ➔ `ReadOnlyConfig({})`<br/>`123` ➔ `TypeError` |

> ⚠️ **Note**: If the raw value is `None`, type coercion is skipped and `None` is returned safely.

---

## 3. Core Coercion Implementation

### 3.1. Single Key-Value Coercion (`coerce_type_by_key_suffix`)

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

### 3.2. Recursive Batch Coercion for Nested Mappings (`coerce_dict_by_key_suffix`)

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

## 4. Scope of Application

Type coercion is universally applied across both standard and custom configuration workflows:

1. **Dot-notation attribute access (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ returns guaranteed `int`
2. **Single path query (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ returns guaranteed `int`
3. **Fail-Fast required query (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ returns guaranteed `int`
4. **Standalone Coercion for Arbitrary Configurations**:  
   Direct execution via `coerce_type_by_key_suffix` and `coerce_dict_by_key_suffix` on any parsed dictionary
5. **Custom Configuration File Dot-Notation Wrapper**:  
   `ReadOnlyConfig(custom_dict, source_name_str="rule.yml")` providing dot-notation, immutability, and accurate attribute error messages

---

## 5. Practical Examples

### 5.1. Default `config/config.yml` Access

```python
from agent_common.config_loader import config

# 1) _int guarantee: Ready for arithmetic operations without casting
batch_size: int = config.transfer.max_workers_int
total_capacity = batch_size * 10  # 160 (No TypeError)

# 2) _bool guarantee: Completely eliminates string evaluation bugs
if config.transfer.is_active_bool:
    print("Service is active.")

# 3) _str guarantee: Clean comparisons without manual .strip()
if config.transfer.environment_str == "staging":
    print("Running in staging environment.")

# 4) _list guarantee: Safe for iteration
for tag in config.transfer.target_tags_list:
    print(f"Tag: {tag}")
```

### 5.2. Generalized Usage on Custom Configuration Files (`rule.yml`, `mapping.yml`)

#### A. Recursive Batch Dictionary Coercion (`coerce_dict_by_key_suffix`)

```python
import yaml
from agent_common import coerce_dict_by_key_suffix

with open("config/rule.yml", "r", encoding="utf-8") as f:
    raw_rules = yaml.safe_load(f)

# Deep nested coercion applied in a single step
clean_rules = coerce_dict_by_key_suffix(raw_rules)

assert isinstance(clean_rules["retry"]["max_attempts_int"], int)
assert isinstance(clean_rules["features"]["enable_cache_bool"], bool)
```

#### B. Custom File Dot-Notation Access (`ReadOnlyConfig`)

```python
import yaml
from agent_common import ReadOnlyConfig

with open("config/mapping.yml", "r", encoding="utf-8") as f:
    mapping_data = yaml.safe_load(f)

# Wrap custom configuration with accurate source name tracking
mapping_cfg = ReadOnlyConfig(mapping_data, source_name_str="mapping.yml")

timeout_sec = mapping_cfg.timeout_float
print(f"Timeout: {timeout_sec}")

# Missing key produces exact diagnostic error:
# AttributeError: mapping.yml에 정의되지 않은 설정 항목입니다: 'undefined_key'
```

#### C. Standalone Key-Value Coercion (`coerce_type_by_key_suffix`)

```python
from agent_common import coerce_type_by_key_suffix

port = coerce_type_by_key_suffix("server_port_int", "8080")  # 8080 (int)
debug = coerce_type_by_key_suffix("is_debug_bool", "yes")     # True (bool)
```
