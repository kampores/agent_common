# 1.3. 键类型后缀自动类型转换与类型保障 (Type Guarantee & Coercion)

> **所属模块**: `agent_common.config_loader` (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`, `ReadOnlyConfig`, `ConfigLoader`)  
> **引入版本**: `v0.4.14`（通用化升级及多配置文件支持: `v0.4.32`）  
> **核心函数/方法**:  
> - `coerce_type_by_key_suffix(key_str, val_any)` (单键值对通用转换函数)  
> - `coerce_dict_by_key_suffix(data_dict)` (嵌套字典/列表批量递归转换函数)  
> - `ReadOnlyConfig(data, source_name_str="config.yml")` (不可变点记法包装器)

---

## 1. 概述与背景

在编写 YAML 配置文件或通过环境变量注入参数时，由于引号遗漏（`timeout: 30` vs `timeout: "30"`）或环境变量始终以字符串形式（`"true"`, `"100"`）传入，往往在 Python 运行时引发典型 Bug：

- 算术运算时报错：`"30" + 10` ➔ `TypeError: can only concatenate str to str`
- 字符串布尔误判：`"false"` 在 `if config.is_enabled:` 条件判断中被判定为 `True`，造成严重业务逻辑异常。

`agent_common` 严格结合 AGENTS.md 规范中的**显式类型后缀命名原则**，依据配置键末尾的类型后缀，在运行时自动将配置值**强制转换为 Python 标准数据类型并执行严格保障（Coercion & Guarantee）**。

自 `v0.4.32` 起，该机制不仅适用于 `config.yml`，还以**通用公共函数（`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`）**的形式开放，可直接导入并应用于任意外部配置文件（如 `rule.yml`, `mapping.yml`, `db.yml`）或内存字典/JSON 数据。

---

## 2. 支持的后缀与自动转换规则

| 配置键后缀 | 返回保障类型 | 转换与规范化处理 | 失败时行为 (Fail-Fast) | 输入示例与转换结果 |
| :--- | :---: | :--- | :--- | :--- |
| `_int` | `int` | 自动转为 `int(val)` | **抛出 `ValueError` (Fail-Fast)**<br/>提示应输入标准整数 | `"100"` ➔ `100`<br/>`"abc"` ➔ `ValueError` |
| `_float` | `float` | 自动转为 `float(val)` | **抛出 `ValueError` (Fail-Fast)**<br/>提示应输入标准浮点数/数值 | `"3.14"` ➔ `3.14`<br/>`"xyz"` ➔ `ValueError` |
| `_bool` | `bool` | 显式布尔值判定<br/>(原生 `bool` 或不区分大小写的 `"true"` ➔ `True`, `"false"` ➔ `False`<br/>※ 不支持数字 `0`/`1` 及任意字符串) | **抛出 `ValueError` / `TypeError` (Fail-Fast)**<br/>提示必须为规范的 True 或 False | `"True"` ➔ `True`<br/>`"false"` ➔ `False`<br/>`1`, `"0"`, `"hello"` ➔ 抛出异常 (Fail-Fast) |
| `_str` | `str` | 自动调用 `str(val).strip()` 清除首尾空白 | - | `"  prod  "` ➔ `"prod"`<br/>`1234` ➔ `"1234"` |
| `_list` | `list` | 保证为 `list`（元组、集合、单元素自动包装为列表） | - | `("a", "b")` ➔ `["a", "b"]`<br/>`"only_one"` ➔ `["only_one"]` |
| `_dict` | `dict` / `ReadOnlyConfig` | 保证为字典结构并由 `ReadOnlyConfig` 包装 | **抛出 `TypeError` (Fail-Fast)**<br/>提示必须为字典映射结构 | `{}` ➔ `ReadOnlyConfig({})`<br/>`123` ➔ `TypeError` |

> ⚠️ **注意**: 若原始输入值为 `None`，则不进行强制类型转换，直接安全返回 `None`。

---

## 3. 核心转换算法

### 3.1. 单键值对类型转换 (`coerce_type_by_key_suffix`)

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
                expected_type_str="整数型(int)",
                guide_msg_str="请输入合法的整数值。",
                cause_exc=err,
            )

    if key_str.endswith("_float"):
        try:
            return float(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="浮点型(float)",
                guide_msg_str="请输入合法的数值。",
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
                expected_type_str="布尔型(bool)",
                guide_msg_str="请输入 True 或 False。",
                exc_cls=ValueError,
            )
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="布尔型(bool)",
            guide_msg_str="请输入 True 或 False。",
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
            expected_type_str="字典型(dict)",
            guide_msg_str="请输入符合映射结构的字典对象。",
            exc_cls=TypeError,
        )

    return val_any
```

### 3.2. 嵌套字典批量递归转换 (`coerce_dict_by_key_suffix`)

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

## 4. 应用场景

类型保障机制在 `agent_common` 的各个配置访问层级及外部配置解析中保持严格统一：

1. **点记法属性访问 (`ReadOnlyConfig.__getattr__`)**:  
   `config.transfer.max_workers_int` ➔ 返回 `int`
2. **单路径键查询 (`ConfigLoader.setting()`)**:  
   `loader.setting("transfer.max_workers_int")` ➔ 返回 `int`
3. **快速失败必选查询 (`ConfigLoader.require_setting()`)**:  
   `loader.require_setting("transfer.max_workers_int")` ➔ 返回 `int`
4. **外部文件/字典直接转换 (`coerce_type_by_key_suffix`, `coerce_dict_by_key_suffix`)**:  
   解析外部 YAML/JSON 后，可直接对单值或整树字典进行批量类型转换
5. **任意配置文件的只读包装**:  
   `ReadOnlyConfig(custom_dict, source_name_str="rule.yml")` 提供点记法、不可变性以及精准的文件名报错诊断

---

## 5. 实战应用示例

### 5.1. 基础 `config/config.yml` 点记法读取

```python
from agent_common.config_loader import config

# 1) _int 保障: 可直接进行算术运算
batch_size: int = config.transfer.max_workers_int
total_capacity = batch_size * 10  # 160 (整数算术运算成功)

# 2) _bool 保障: 彻底杜绝字符串布尔判断陷阱
if config.transfer.is_active_bool:
    print("服务处于启用状态。")

# 3) _str 保障: 消除前后空格污染，保证字符串精确匹配
if config.transfer.environment_str == "staging":
    print("当前为 Staging 测试环境。")

# 4) _list 保障: 可安全用于 for-in 遍历
for tag in config.transfer.target_tags_list:
    print(f"处理标签: {tag}")
```

### 5.2. 通用应用于其它配置文件（如 `rule.yml`, `mapping.yml`）

#### A. 嵌套字典批量规整 (`coerce_dict_by_key_suffix`)

```python
import yaml
from agent_common import coerce_dict_by_key_suffix

with open("config/rule.yml", "r", encoding="utf-8") as f:
    raw_rules = yaml.safe_load(f)

# 所有嵌套键（_int, _bool, _str 等）的值均完成批量类型转换
clean_rules = coerce_dict_by_key_suffix(raw_rules)

assert isinstance(clean_rules["retry"]["max_attempts_int"], int)
assert isinstance(clean_rules["features"]["enable_cache_bool"], bool)
```

#### B. 任意配置文件的不可变点记法包装 (`ReadOnlyConfig`)

```python
import yaml
from agent_common import ReadOnlyConfig

with open("config/mapping.yml", "r", encoding="utf-8") as f:
    mapping_data = yaml.safe_load(f)

# 指定来源文件名创建不可变配置对象
mapping_cfg = ReadOnlyConfig(mapping_data, source_name_str="mapping.yml")

# 享有属性点记法与类型保障
timeout_sec = mapping_cfg.timeout_float
print(f"超时时间: {timeout_sec}")

# 访问不存在的键时，准确提示文件名与错误项
# AttributeError: mapping.yml 中未定义该配置项: 'undefined_key'
```

#### C. 单键值对快速转换 (`coerce_type_by_key_suffix`)

```python
from agent_common import coerce_type_by_key_suffix

# 转换环境变量、CLI 参数或外部 API 响应单值
port = coerce_type_by_key_suffix("server_port_int", "8080")  # 8080 (int)
debug = coerce_type_by_key_suffix("is_debug_bool", "true")   # True (bool)
```

通过这一规范，开发者可以在业务逻辑中彻底抛弃多余的防御性类型转换代码（如 `int(...)`, `float(...)`, `.strip()`）。
