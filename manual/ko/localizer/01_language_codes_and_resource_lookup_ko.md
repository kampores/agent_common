# 8.1. 언어 코드 정규화 및 언어별 리소스 파일 탐색 (`Localizer`)

> **소속 모듈**: `agent_common.localizer.Localizer` (`from agent_common import Localizer`)  
> **핵심 메서드**: `normalize_language()`, `resolve_language()`, `set_global_language()`, `resolve_localized_file()`, `resolve_localized_path_from_list()`  
> **의존 패키지**: 없음 (표준 라이브러리만 사용)

---

## 1. 개요

`Localizer`는 "어떤 언어를 쓸지"와 "그 언어의 파일이 어디 있는지"를 결정하는 일을 전담하는 클래스입니다. 로깅과 분리되어 있어서, 로그 메시지뿐 아니라 화면 라벨, 안내문, 프롬프트처럼 언어별로 나뉘는 모든 리소스에 쓸 수 있습니다.

담당하는 일은 세 가지입니다.

- 입력된 언어 문자열을 표준 언어 코드로 정규화
- 명시 인자, 전역 설정, 환경변수를 따져 최종 언어 결정
- `{접두사}_{언어}.yml` 형태의 언어별 리소스 파일 탐색

모든 메서드는 클래스 메서드라서 인스턴스를 만들지 않고 호출합니다.

---

## 2. 지원 언어 코드

언어 코드는 ISO 639-1 언어 코드를 기준으로 합니다.

| 표준 코드 | 언어 | 함께 인식하는 입력 | 파일 접미사 |
| :---: | :--- | :--- | :---: |
| `KO` | 한국어 (기본 언어) | `KOR`, `KOREAN` | `_ko` |
| `EN` | 영어 | `ENG`, `ENGLISH` | `_en` |
| `ZH` | 중국어 | `CHI`, `CHINESE` | `_zh` |
| `JA` | 일본어 | `JPN`, `JAPANESE` | `_ja` |

- 대소문자와 앞뒤 공백은 무시합니다 (`" Korean "` → `KO`).
- 인식하지 못한 값이나 빈 값은 오류 없이 기본 언어 `KO`로 처리됩니다.
- 국가 코드(`KR`, `JP`, `CN`, `US`)는 언어 코드가 아니므로 인식하지 않습니다. 예를 들어 `JP`를 넣으면 `JA`가 아니라 기본 언어 `KO`가 됩니다.

---

## 3. 언어 결정 우선순위 (`resolve_language`)

`resolve_language()`는 아래 순서로 먼저 해당하는 값을 사용합니다.

1. 인자 `explicit_lang_str`
2. `set_global_language()`로 지정한 프로세스 전역 언어
3. 환경변수 `AGENT_LANGUAGE`, `APP_LANGUAGE`, `LANGUAGE`, `LANG` 중 앞에서부터 처음으로 값이 있는 것
4. 인자 `default_lang_str` (기본값 `KO`)

환경변수는 로캘 형식이어도 됩니다. `.`과 `_` 앞부분만 사용하므로 `ja_JP.UTF-8`은 `JA`로 해석됩니다.

로그 메시지 언어는 `ConfigLoader`가 로깅 전용 환경변수와 `logging.language_str` 설정을 포함한 별도 우선순위로 결정합니다. 자세한 내용은 [2.3. 다국어 로그 메시지 템플릿 사전](../logger/03_multilingual_message_catalog_ko.md)을 참고하세요.

---

## 4. 언어별 리소스 파일 탐색 규칙

`resolve_localized_file()`과 `resolve_localized_path_from_list()`는 같은 순서로 파일을 고릅니다.

1. 대상 언어 파일: `{접두사}_{언어}.yml` (예: `labels_en.yml`)
2. 기본 언어 파일: `{접두사}_ko.yml`
3. 접미사 없는 파일: `{접두사}.yml`
4. 모두 없으면 `None`

`resolve_localized_file()`은 디렉토리를 직접 탐색하며 확장자 `.yml`, `.yaml`을 차례로 확인합니다. `resolve_localized_path_from_list()`는 이미 가지고 있는 파일 목록에서 확장자를 뺀 파일명으로 비교합니다.

---

## 5. 메서드 규격

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

- `extensions_list`: 탐색할 확장자 목록. 지정하지 않으면 `[".yml", ".yaml"]`입니다.
- `resolve_catalog_file()`, `resolve_project_catalog_file()`은 접두사를 `logging_messages`로 고정해 위 두 메서드를 호출하는 메서드입니다.

---

## 6. 사용 예시

### 6.1. 언어 코드 정규화
```python
from agent_common import Localizer

Localizer.normalize_language("ko")        # "KO"
Localizer.normalize_language(" Korean ")  # "KO"
Localizer.normalize_language("JPN")       # "JA"
Localizer.normalize_language("fr")        # "KO" (지원하지 않는 언어는 기본 언어)
```

### 6.2. 최종 언어 결정
```python
import os

from agent_common import Localizer

Localizer.resolve_language()                         # "KO" (아무 설정도 없을 때)
Localizer.resolve_language(default_lang_str="EN")    # "EN"

os.environ["LANG"] = "ja_JP.UTF-8"
Localizer.resolve_language()                         # "JA"

Localizer.set_global_language("english")
Localizer.resolve_language()                         # "EN" (전역 설정이 환경변수보다 우선)
Localizer.resolve_language("ja")                     # "JA" (명시 인자가 최우선)

Localizer.clear_global_language()
```

### 6.3. 프로젝트 고유의 언어별 리소스 파일 찾기
`config/` 아래에 `labels_ko.yml`, `labels_en.yml`, `notice.yml`이 있는 경우입니다.
```python
from pathlib import Path

from agent_common import Localizer

config_dir_path = Path("config")
language_str = Localizer.resolve_language()

# 영어 파일이 있으면 그 파일을 반환 -> config/labels_en.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "EN")

# 일본어 파일이 없으면 기본 언어 파일로 대체 -> config/labels_ko.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "JA")

# 언어별 파일이 없으면 접미사 없는 파일 -> config/notice.yml
Localizer.resolve_localized_file(config_dir_path, "notice", language_str)

# 해당하는 파일이 전혀 없으면 None
Localizer.resolve_localized_file(config_dir_path, "other", "EN")
```
