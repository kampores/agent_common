# 8.1. 言語コードの正規化と言語別リソースファイル探索 (`Localizer`)

> **所属モジュール**: `agent_common.localizer.Localizer` (`from agent_common import Localizer`)  
> **中核メソッド**: `normalize_language()`, `resolve_language()`, `set_global_language()`, `resolve_localized_file()`, `resolve_localized_path_from_list()`  
> **依存パッケージ**: なし（標準ライブラリのみ使用）

---

## 1. 概要

`Localizer` は、「どの言語を使うか」と「その言語のファイルがどこにあるか」の決定を専任するクラスです。ロギングから分離されているため、ログメッセージだけでなく、画面ラベル、案内文、プロンプトなど、言語ごとに分かれるあらゆるリソースに利用できます。

担当するのは次の 3 つです。

- 入力された言語文字列を標準の言語コードへ正規化
- 明示引数、グローバル設定、環境変数から最終的な言語を決定
- `{接頭辞}_{言語}.yml` 形式の言語別リソースファイルを探索

すべてのメソッドはクラスメソッドのため、インスタンスを生成せずに呼び出します。

---

## 2. 対応言語コード

言語コードは ISO 639-1 の言語コードを基準とします。

| 標準コード | 言語 | あわせて認識する入力 | ファイル接尾辞 |
| :---: | :--- | :--- | :---: |
| `KO` | 韓国語（デフォルト言語） | `KOR`, `KOREAN` | `_ko` |
| `EN` | 英語 | `ENG`, `ENGLISH` | `_en` |
| `ZH` | 中国語 | `CHI`, `CHINESE` | `_zh` |
| `JA` | 日本語 | `JPN`, `JAPANESE` | `_ja` |

- 大文字・小文字と前後の空白は無視します（`" Korean "` → `KO`）。
- 認識できない値や空の値は、エラーにならずデフォルト言語 `KO` として扱われます。
- 国コード（`KR`、`JP`、`CN`、`US`）は言語コードではないため認識しません。たとえば `JP` を指定すると、`JA` ではなくデフォルト言語 `KO` になります。

---

## 3. 言語決定の優先順位 (`resolve_language`)

`resolve_language()` は以下の順序で、最初に該当した値を使用します。

1. 引数 `explicit_lang_str`
2. `set_global_language()` で指定したプロセス全体の言語
3. 環境変数 `AGENT_LANGUAGE`、`APP_LANGUAGE`、`LANGUAGE`、`LANG` のうち、先頭から最初に値があるもの
4. 引数 `default_lang_str`（デフォルト値 `KO`）

環境変数はロケール形式でもかまいません。`.` と `_` より前の部分だけを使用するため、`ja_JP.UTF-8` は `JA` と解釈されます。

ログメッセージの言語は、`ConfigLoader` がロギング専用の環境変数と `logging.language_str` 設定を含む別の優先順位で決定します。詳しくは [2.3. 多言語ログメッセージテンプレート辞書](../logger/03_multilingual_message_catalog_ja.md) を参照してください。

---

## 4. 言語別リソースファイルの探索ルール

`resolve_localized_file()` と `resolve_localized_path_from_list()` は、同じ順序でファイルを選びます。

1. 対象言語のファイル: `{接頭辞}_{言語}.yml`（例: `labels_en.yml`）
2. デフォルト言語のファイル: `{接頭辞}_ko.yml`
3. 接尾辞なしのファイル: `{接頭辞}.yml`
4. いずれもなければ `None`

`resolve_localized_file()` はディレクトリを直接探索し、拡張子 `.yml`、`.yaml` を順に確認します。`resolve_localized_path_from_list()` は、すでに持っているファイル一覧の中から、拡張子を除いたファイル名で比較します。

---

## 5. メソッド仕様

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

- `extensions_list`: 探索する拡張子の一覧。指定しない場合は `[".yml", ".yaml"]` です。
- `resolve_catalog_file()`、`resolve_project_catalog_file()` は、接頭辞を `logging_messages` に固定して上記 2 つのメソッドを呼び出すメソッドです。

---

## 6. 使用例

### 6.1. 言語コードの正規化
```python
from agent_common import Localizer

Localizer.normalize_language("ko")        # "KO"
Localizer.normalize_language(" Korean ")  # "KO"
Localizer.normalize_language("JPN")       # "JA"
Localizer.normalize_language("fr")        # "KO"（未対応の言語はデフォルト言語）
```

### 6.2. 最終的な言語の決定
```python
import os

from agent_common import Localizer

Localizer.resolve_language()                         # "KO"（何も設定がない場合）
Localizer.resolve_language(default_lang_str="EN")    # "EN"

os.environ["LANG"] = "ja_JP.UTF-8"
Localizer.resolve_language()                         # "JA"

Localizer.set_global_language("english")
Localizer.resolve_language()                         # "EN"（グローバル設定が環境変数より優先）
Localizer.resolve_language("ja")                     # "JA"（明示引数が最優先）

Localizer.clear_global_language()
```

### 6.3. プロジェクト独自の言語別リソースファイルを探す
`config/` 配下に `labels_ko.yml`、`labels_en.yml`、`notice.yml` がある場合の例です。
```python
from pathlib import Path

from agent_common import Localizer

config_dir_path = Path("config")
language_str = Localizer.resolve_language()

# 英語ファイルがあればそのファイルを返却 -> config/labels_en.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "EN")

# 日本語ファイルがなければデフォルト言語のファイルで代替 -> config/labels_ko.yml
Localizer.resolve_localized_file(config_dir_path, "labels", "JA")

# 言語別ファイルがなければ接尾辞なしのファイル -> config/notice.yml
Localizer.resolve_localized_file(config_dir_path, "notice", language_str)

# 該当するファイルがまったくなければ None
Localizer.resolve_localized_file(config_dir_path, "other", "EN")
```
