# 03. Type Guarantee & Automatic Coercion via Type Suffixes

> **Module**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **Introduced In**: `v0.4.14`  
> **Key Method**: `ReadOnlyConfig._coerce_type_by_key_suffix(key, val)`

---

## 1. Overview & Problem Statement

In YAML configurations and environment variable injections, type ambiguity frequently causes subtle runtime bugs:
- Quoted numbers (e.g. `timeout: "30"`) causing `TypeError: can only concatenate str to str`.
- Quoted boolean values (e.g. `is_enabled: "false"`) evaluating to `True` in Python truthiness checks (`bool("false") == True`).

`agent_common` integrates with the strict AGENTS.md **type-suffix naming convention** (`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`), automatically coercing and guaranteeing exact Python standard types at runtime.

---

## 2. Supported Suffixes & Coercion Rules

| Configuration Key Suffix | Guaranteed Return Type | Coercion Logic & Normalization | Example Input & Result |
| :--- | :---: | :--- | :--- |
| `_int` | `int` | Automatically converted via `int(val)` (retains original on conversion failure) | `"100"` ➔ `100`<br/>`100.0` ➔ `100` |
| `_float` | `float` | Automatically converted via `float(val)` | `"3.14"` ➔ `3.14`<br/>`3` ➔ `3.0` |
| `_bool` | `bool` | Case-insensitive boolean evaluation<br/>(`"true"`, `"1"`, `"yes"`, `"y"`, `"on"` ➔ `True`<br/>Otherwise ➔ `False`) | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`"0"` ➔ `False`<br/>`"yes"` ➔ `True` |
| `_str` | `str` | Automatically converted to `str(val)` with whitespace stripped (`.strip()`) | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | Ensures tuples, sets, or single items are returned as a `list` | `("a", "b")` ➔ `["a", "b"]`<br/>`"single"` ➔ `["single"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | Guarantees dictionary mapping structure and wraps in `ReadOnlyConfig` | `{}` ➔ `ReadOnlyConfig({})` |

> ⚠️ **Note**: If the raw value is `None`, type coercion is skipped and `None` is returned safely.

---

## 3. Core Coercion Implementation (`_coerce_type_by_key_suffix`)

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

## 4. Scope of Application

Type coercion is universally applied across all access paths in `agent_common.config_loader`:

1. **Dot-notation attribute access (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ returns guaranteed `int`
2. **Single path query (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ returns guaranteed `int`
3. **Fail-Fast required query (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ returns guaranteed `int`

---

## 5. Practical Example

### 5.1. YAML Configuration (`config/config.yml`)

```yaml
transfer:
  max_workers_int: "16"          # Guaranteed int(16) even if entered as a string
  timeout_seconds_float: "45.5"  # Guaranteed float(45.5)
  is_active_bool: "yes"          # Guaranteed bool(True)
  environment_str: "  staging  " # Whitespace automatically trimmed to "staging"
  target_tags_list: "production" # Wrapped into ["production"]
```

### 5.2. Python Code Consumption

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
