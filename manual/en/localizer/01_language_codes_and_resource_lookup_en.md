# 8.1. Language Code Normalization & Localized Resource Lookup (`Localizer`)

> **Module**: `agent_common.localizer.Localizer` (`from agent_common import Localizer`)  
> **Key Methods**: `normalize_language()`, `resolve_language()`, `set_global_language()`, `resolve_localized_file()`, `resolve_localized_path_from_list()`  
> **Dependencies**: None (standard library only)

---

## 1. Overview

`Localizer` is the class dedicated to deciding which language to use and where that language's file is. It is separate from logging, so it works for any resource that is split by language, such as UI labels, notices, and prompts, not only log messages.

It does three things.

- Normalizes a language string into a standard language code
- Decides the final language from an explicit argument, the global setting, and environment variables
- Finds per-language resource files named `{prefix}_{language}.yml`

Every method is a class method, so you call them without creating an instance.

---

## 2. Supported Language Codes

Language codes follow ISO 639-1.

| Standard code | Language | Also accepted | File suffix |
| :---: | :--- | :--- | :---: |
| `KO` | Korean (default language) | `KOR`, `KOREAN` | `_ko` |
| `EN` | English | `ENG`, `ENGLISH` | `_en` |
| `ZH` | Chinese | `CHI`, `CHINESE` | `_zh` |
| `JA` | Japanese | `JPN`, `JAPANESE` | `_ja` |

- Letter case and surrounding whitespace are ignored (`" Korean "` → `KO`).
- An unrecognized or empty value falls back to the default language `KO` without raising an error.
- Country codes (`KR`, `JP`, `CN`, `US`) are not language codes and are not recognized. For example, `JP` resolves to the default language `KO`, not `JA`.

---

## 3. Language Precedence (`resolve_language`)

`resolve_language()` uses the first value that applies, in this order.

1. The `explicit_lang_str` argument
2. The process-wide language set with `set_global_language()`
3. The first of the environment variables `AGENT_LANGUAGE`, `APP_LANGUAGE`, `LANGUAGE`, `LANG` that has a value
4. The `default_lang_str` argument (default `KO`)

Environment variables may be in locale form. Only the part before `.` and `_` is used, so `ja_JP.UTF-8` resolves to `JA`.

The log message language is decided by `ConfigLoader` with its own precedence, which includes logging-specific environment variables and the `logging.language_str` setting. See [2.3. Multilingual Message Catalog](../logger/03_multilingual_message_catalog_en.md) for details.

---

## 4. Localized Resource File Lookup Rules

`resolve_localized_file()` and `resolve_localized_path_from_list()` choose a file in the same order.

1. The target language file: `{prefix}_{language}.yml` (for example `labels_en.yml`)
2. The default language file: `{prefix}_ko.yml`
3. The file with no suffix: `{prefix}.yml`
4. `None` when none of these exist

`resolve_localized_file()` searches a directory and checks the extensions `.yml` and `.yaml` in turn. `resolve_localized_path_from_list()` compares against file names without their extension, from a list of files you already have.

---

## 5. Method Reference

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

- `extensions_list`: The extensions to search. Defaults to `[".yml", ".yaml"]`.
- `resolve_catalog_file()` and `resolve_project_catalog_file()` call the two methods above with the prefix fixed to `logging_messages`.

---

## 6. Usage Examples

### 6.1. Normalizing Language Codes
```python
from agent_common import Localizer

Localizer.normalize_language("ko")        # "KO"
Localizer.normalize_language(" Korean ")  # "KO"
Localizer.normalize_language("JPN")       # "JA"
Localizer.normalize_language("fr")        # "KO" (unsupported languages fall back to the default)
```

### 6.2. Deciding the Final Language
```python
import os

from agent_common import Localizer

Localizer.resolve_language()                         # "KO" (nothing configured)
Localizer.resolve_language(default_lang_str="EN")    # "EN"

os.environ["LANG"] = "ja_JP.UTF-8"
Localizer.resolve_language()                         # "JA"

Localizer.set_global_language("english")
Localizer.resolve_language()                         # "EN" (the global setting beats environment variables)
Localizer.resolve_language("ja")                     # "JA" (an explicit argument wins)

Localizer.clear_global_language()
```

### 6.3. Finding Your Project's Own Per-Language Resource Files
This example assumes `config/` contains `labels_ko.yml`, `labels_en.yml`, and `notice.yml`.
```python
from pathlib import Path

from agent_common import Localizer

config_dir_path = Path("config")
language_str = Localizer.resolve_language()

# Returns the English file when it exists -> config/labels_en.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "EN")

# Falls back to the default language file when there is no Japanese file -> config/labels_ko.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "JA")

# Uses the file with no suffix when there are no per-language files -> config/notice.yml
Localizer.resolve_localized_file(config_dir_path, "notice", language_str)

# Returns None when no matching file exists
Localizer.resolve_localized_file(config_dir_path, "other", "EN")
```
