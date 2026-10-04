# 8.1. 语言代码规范化与多语言资源文件查找 (`Localizer`)

> **所属模块**: `agent_common.localizer.Localizer` (`from agent_common import Localizer`)  
> **核心方法**: `normalize_language()`, `resolve_language()`, `set_global_language()`, `resolve_localized_file()`, `resolve_localized_path_from_list()`  
> **依赖组件**: 无（仅使用标准库）

---

## 1. 概述

`Localizer` 是专门负责决定“使用哪种语言”以及“该语言的文件在哪里”的类。它与日志功能相互独立，因此不仅可用于日志消息，也可用于界面标签、提示文案、提示词等所有按语言拆分的资源。

它负责三件事。

- 将输入的语言字符串规范化为标准语言代码
- 综合显式参数、全局设置和环境变量，决定最终语言
- 查找 `{前缀}_{语言}.yml` 形式的多语言资源文件

所有方法都是类方法，无需创建实例即可调用。

---

## 2. 支持的语言代码

语言代码以 ISO 639-1 语言代码为准。

| 标准代码 | 语言 | 同时识别的输入 | 文件后缀 |
| :---: | :--- | :--- | :---: |
| `KO` | 韩语（默认语言） | `KOR`, `KOREAN` | `_ko` |
| `EN` | 英语 | `ENG`, `ENGLISH` | `_en` |
| `ZH` | 中文 | `CHI`, `CHINESE` | `_zh` |
| `JA` | 日语 | `JPN`, `JAPANESE` | `_ja` |

- 忽略大小写和首尾空格（`" Korean "` → `KO`）。
- 无法识别的值或空值不会报错，按默认语言 `KO` 处理。
- 国家代码（`KR`、`JP`、`CN`、`US`）不是语言代码，不予识别。例如输入 `JP` 得到的是默认语言 `KO`，而不是 `JA`。

---

## 3. 语言决定优先级 (`resolve_language`)

`resolve_language()` 按以下顺序采用最先满足条件的值。

1. 参数 `explicit_lang_str`
2. 通过 `set_global_language()` 指定的进程全局语言
3. 环境变量 `AGENT_LANGUAGE`、`APP_LANGUAGE`、`LANGUAGE`、`LANG` 中按顺序第一个有值的
4. 参数 `default_lang_str`（默认值 `KO`）

环境变量可以是 locale 形式。只取 `.` 和 `_` 之前的部分，因此 `ja_JP.UTF-8` 会被解析为 `JA`。

日志消息的语言由 `ConfigLoader` 按另一套优先级决定，其中包含日志专用环境变量和 `logging.language_str` 配置。详情请参阅 [2.3. 多语言日志消息模板字典](../logger/03_multilingual_message_catalog_zh.md)。

---

## 4. 多语言资源文件查找规则

`resolve_localized_file()` 与 `resolve_localized_path_from_list()` 按相同的顺序选择文件。

1. 目标语言文件: `{前缀}_{语言}.yml`（例如 `labels_en.yml`）
2. 默认语言文件: `{前缀}_ko.yml`
3. 不带后缀的文件: `{前缀}.yml`
4. 均不存在时返回 `None`

`resolve_localized_file()` 直接搜索目录，依次检查扩展名 `.yml`、`.yaml`。`resolve_localized_path_from_list()` 则在已有的文件列表中，按去掉扩展名后的文件名进行比较。

---

## 5. 方法规格

```python
@classmethod
def normalize_language(cls, language_str: str) -> str

@classmethod
def resolve_language(cls, explicit_lang_str: Optional[str] = None, default_lang_str: str = "KO") -> str

@classmethod
def set_global_language(cls, language_str: str) -> None

@classmethod
def get_global_language(cls) -> Optional[str]

@classmethod
def clear_global_language(cls) -> None

@classmethod
def resolve_localized_file(
    cls,
    dir_path: Path,
    prefix_str: str,
    language_str: str,
    extensions_list: Optional[list[str]] = None,
) -> Optional[Path]

@classmethod
def resolve_localized_path_from_list(
    cls,
    file_paths_list: list[Path],
    prefix_str: str,
    language_str: str,
) -> Optional[Path]
```

- `extensions_list`: 要查找的扩展名列表。未指定时为 `[".yml", ".yaml"]`。
- `resolve_catalog_file()`、`resolve_project_catalog_file()` 是将前缀固定为 `logging_messages` 后调用上述两个方法的方法。

---

## 6. 使用示例

### 6.1. 语言代码规范化
```python
from agent_common import Localizer

Localizer.normalize_language("ko")        # "KO"
Localizer.normalize_language(" Korean ")  # "KO"
Localizer.normalize_language("JPN")       # "JA"
Localizer.normalize_language("fr")        # "KO"（不支持的语言按默认语言处理）
```

### 6.2. 决定最终语言
```python
import os

from agent_common import Localizer

Localizer.resolve_language()                         # "KO"（没有任何设置时）
Localizer.resolve_language(default_lang_str="EN")    # "EN"

os.environ["LANG"] = "ja_JP.UTF-8"
Localizer.resolve_language()                         # "JA"

Localizer.set_global_language("english")
Localizer.resolve_language()                         # "EN"（全局设置优先于环境变量）
Localizer.resolve_language("ja")                     # "JA"（显式参数优先级最高）

Localizer.clear_global_language()
```

### 6.3. 查找项目自有的多语言资源文件
假设 `config/` 下有 `labels_ko.yml`、`labels_en.yml`、`notice.yml`。
```python
from pathlib import Path

from agent_common import Localizer

config_dir_path = Path("config")
language_str = Localizer.resolve_language()

# 存在英语文件时返回该文件 -> config/labels_en.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "EN")

# 没有日语文件时以默认语言文件代替 -> config/labels_ko.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "JA")

# 没有按语言区分的文件时使用不带后缀的文件 -> config/notice.yml
Localizer.resolve_localized_file(config_dir_path, "notice", language_str)

# 完全没有匹配的文件时返回 None
Localizer.resolve_localized_file(config_dir_path, "other", "EN")
```
